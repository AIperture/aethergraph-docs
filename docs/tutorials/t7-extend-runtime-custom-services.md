# Extend the Runtime — Custom Services

Sometimes your agents need to talk to the *rest* of your world: clusters, databases, storage systems, internal APIs, you name it. Instead of wiring all that logic directly into every `graph_fn`, AetherGraph lets you hang **custom services** off the `context` object:

```python
# Later inside a graph or tool
await context.trainer().submit(spec)
await context.storage().put("/tmp/report.pdf")
status = await context.tracker().job_status(job_id)
```

This tutorial shows how to:

1. Define a small service class (just Python).
2. Register it so it appears as `context.<name>()`.
3. Use it from `graph_fn` / `@tool` code.
4. Apply a few practical patterns (HPC jobs, storage, external APIs).

The goal: **keep your agent logic clean**, and move integration glue into reusable, testable services.

---

## 1. What is a Custom Service, Really?

A *custom service* is just a long‑lived Python object that the runtime injects into every `NodeContext` under a chosen name.

Once registered, this works anywhere inside AetherGraph:

```python
@graph_fn(name="demo_trainer")
async def demo_trainer(*, context):
    job_id = await context.trainer().submit({"epochs": 10})
    return {"job_id": job_id}
```

Key properties:

* **Named entrypoint** — you pick the accessor name (e.g., `trainer`, `storage`, `models`).
* **Shared instance** — the same service object is reused across nodes/runs (unless you decide otherwise).
* **Context-aware** — it can see the *current* `NodeContext` (`run_id`, `graph_id`, `node_id`) when needed.
* **Async-first** — it plays nicely with the event loop (`await` everywhere).

Use a service when you have **state or connectivity** that should be shared and configured once (clients, caches, pools, background workers, etc.). For pure math helpers, regular modules are fine.

---

## 2. Minimal Service: from Zero to `context.trainer()`

### Step 1: Define a service class

Most custom services inherit from `Service` (aka `BaseContextService`). That gives you a few niceties: access to the current context, a mutex, and helpers for running blocking code.

```python
from aethergraph.services.runtime.base import Service

class Trainer(Service):
    async def submit(self, spec: dict) -> str:
        """Submit a training job to your cluster / scheduler."""
        # 1) Inspect current run/node if you like
        ctx = self.ctx()  # NodeContext bound at call time
        ctx.logger().info("trainer.submit", extra={"spec": spec})

        # 2) Call your real backend (pseudo-code)
        job_id = await self._submit_to_cluster(spec)

        # 3) Optionally record to memory for later inspection
        await ctx.memory().write_result(
            topic="trainer.submit",
            outputs=[{"name": "job_id", "kind": "text", "value": job_id}],
        )
        return job_id

    async def inspect_job(self, job_id: str) -> dict:
        """Check job status from the same backend."""
        status = await self._query_cluster(job_id)
        return {"job_id": job_id, "status": status}

    # You implement these however you like
    async def _submit_to_cluster(self, spec: dict) -> str: ...
    async def _query_cluster(self, job_id: str) -> str: ...
```

Important bits:

* `self.ctx()` gives you the **current** `NodeContext` when the method is called — so logs, memory, artifacts, etc. are automatically run‑scoped.
* The service itself is free to keep **internal state** (connection pools, caches, in‑memory maps) across calls.

### Step 2: Register the service

At startup (e.g., in your sidecar/server init), register an *instance* of the service under a name:

```python
from aethergraph.services.runtime.registry import register_context_service

trainer_service = Trainer()
register_context_service("trainer", trainer_service)
```

From now on, **inside any node** you can write:

```python
job_id = await context.trainer().submit(spec)
```

> The pattern is: **register once → call anywhere**.

---

## 3. Using Services Inside `graph_fn` and `@tool`

Once registered, services behave just like built‑ins on `context`.

### Example A — Submit and track a job

```python
from aethergraph import graph_fn, tool

@graph_fn(name="train_and_wait", outputs=["job_id", "done"])
async def train_and_wait(spec: dict, *, context):
    # 1) Kick off work via the custom service
    job_id = await context.trainer().submit(spec)

    # 2) Poll in a small @tool (keeps the graph explicit)
    ready = await wait_for_training(job_id=job_id, context=context)
    return {"job_id": job_id, "done": ready["ready"]}

@tool(name="wait_for_training", outputs=["ready"])
async def wait_for_training(job_id: str, *, context) -> dict:
    info = await context.trainer().inspect_job(job_id)
    return {"ready": info["status"] == "COMPLETED"}
```

Why this is nice:

* Your **cluster logic lives in one place** (`Trainer`), not sprinkled across graphs.
* Tests can swap in a fake `Trainer` that just returns canned statuses.

### Example B — Custom storage wrapper

```python
class Storage(Service):
    async def put(self, local_path: str, key: str) -> str:
        # upload to S3/GCS/MinIO/etc. and return a URI
        uri = await self._upload(local_path, key)
        self.ctx().logger().info("storage.put", extra={"uri": uri})
        return uri

    async def get(self, uri: str, dest: str) -> None:
        await self._download(uri, dest)

# Register once
register_context_service("storage", Storage())

# Use anywhere
@graph_fn(name="upload_report", outputs=["uri"])
async def upload_report(*, context):
    uri = await context.storage().put("/tmp/report.pdf", key="reports/2025-01-01.pdf")
    return {"uri": uri}
```

Here you’re free to mix `context.storage()` with core features like `artifacts()` and `memory()` — for example, storing the CAS URI next to an external bucket URI.

---

## 4. Concurrency & Shared State

Because a service instance is shared, you might need coordination when multiple nodes hit it at once.

The base `Service` gives you two main tools:

### A. Critical sections (simple mutex)

```python
class RateLimitedAPI(Service):
    def __init__(self):
        super().__init__()
        self._remaining = 100

    @Service.critical(self)  # or use self.critical() as a decorator factory
    async def call(self, payload: dict) -> dict:
        # This body runs under a mutex
        if self._remaining <= 0:
            raise RuntimeError("rate limit exceeded")
        self._remaining -= 1
        return await self._do_http_call(payload)
```

A more typical pattern is:

```python
class RateLimitedAPI(Service):
    def __init__(self):
        super().__init__()
        self._remaining = 100

    def critical(self):  # inherited helper already exists; used like this:
        return super().critical()

    @critical
    async def call(self, payload: dict) -> dict:
        ...
```

Either way, the idea is: **protect shared mutable state** in the service, not in every caller.

### B. Run blocking code off the event loop

```python
class Heavy(Service):
    async def compute(self, x: int) -> int:
        # Offload CPU-heavy work to a background thread
        return await self.run_blocking(self._slow_cpu_fn, x)

    def _slow_cpu_fn(self, x: int) -> int:
        ...  # pure Python CPU work
```

This keeps your agents responsive even when a service needs to do something slow and synchronous.

---

## 5. Service Lifecycle (start/close)

Some integrations need setup/teardown — e.g., opening a DB connection pool, warming a model, or starting a local daemon.

You can implement optional `start()` and `close()` hooks on your service:

```python
class Tracker(Service):
    async def start(self):
        # e.g., open DB pool or HTTP client
        self._client = ...

    async def close(self):
        # tidy up
        if getattr(self, "_client", None):
            await self._client.aclose()
```

Then call these from your process bootstrap / shutdown logic (sidecar, web server, CLI tool). The runtime doesn’t force a pattern here — you choose how you host services.

---

## 6. Testing & Swapping Implementations

Because services are registered by name, they’re easy to replace in tests.

```python
class FakeTrainer(Service):
    async def submit(self, spec: dict) -> str:
        return "job-test-123"

    async def inspect_job(self, job_id: str) -> dict:
        return {"job_id": job_id, "status": "COMPLETED"}

# In your test setup
register_context_service("trainer", FakeTrainer())

# All graph/tool code using context.trainer() now talks to the fake.
```

This is especially useful when your real service hits Slurm, K8s, or external APIs that you don’t want in unit tests.

---

## 7. Design Tips & Common Patterns

A few patterns that tend to work well in real projects:

* **One concept → one service**
  Example: `context.trainer()` for orchestration, `context.storage()` for object store, `context.lineage_store()` for pushing run metadata to a warehouse.

* **Keep names explicit**
  Prefer `context.k8s_jobs()` or `context.minio()` over something vague like `context.utils()`.

* **Use services for anything stateful**
  HTTP clients, ORM sessions, caches, in‑memory registries, queues — all good fits.

* **Don’t replace built‑ins**
  Leave `context.memory()`, `context.artifacts()`, `context.channel()` as‑is. If you mirror to another system, register a new service that knows how to consume those.

Example service ideas:

| Scenario                          | Accessor              | What it wraps                         |
| --------------------------------- | --------------------- | ------------------------------------- |
| HPC / Training cluster            | `context.trainer()`   | Slurm, K8s jobs, Ray, internal queue  |
| External object storage           | `context.storage()`   | S3/GCS/MinIO, signed URLs             |
| Internal REST / GraphQL API       | `context.apiclient()` | HTTP client with auth & retries       |
| Domain registry (materials, etc.) | `context.registry()`  | Your domain-specific DB + cache       |
| Lineage export                    | `context.lineage()`   | Push run/graph/node metadata to BI/DB |

---

## 8. Optional: Callable Services

If you like very compact call sites, you can make the service itself callable by defining `__call__`. The `NodeContext` will happily forward through the handle:

```python
class Predictor(Service):
    async def __call__(self, prompt: str) -> str:
        # convenience wrapper
        return await self.generate(prompt)

    async def generate(self, prompt: str) -> str:
        ...

# After registration as "predictor":
text = await context.predictor("hello")        # calls __call__
text = await context.predictor().generate("hello")  # same thing, more explicit
```

This is optional sugar; for team readability, explicit methods like `submit`, `inspect_job`, `upload`, `generate` are often clearer.

---

## 9. How This Fits with MCP and Other Integrations

In the previous section, you saw how **MCP** lets you treat external processes (HTTP, WebSocket, stdio) as tools the agent can call. Custom services are the **other half of the story**:

* **MCP**: great when the external system already speaks the MCP protocol and you want tools/resources auto‑described.
* **Custom services**: great when you just want a **plain Python wrapper** around some internal system — no server to run, no protocol to implement.

In practice, projects often mix both:

* use an MCP server for things like filesystem, SQL, or web search tools;
* use services like `context.trainer()` or `context.storage()` for tightly‑coupled, org‑specific infrastructure.

With this pattern in place, you can keep adding capabilities to your agents by **teaching the runtime new services**, while keeping the agent code itself small, readabl
