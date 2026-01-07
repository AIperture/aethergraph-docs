# Tutorial 7: Plug In Your World — Custom Services

Sometimes your agents need to talk to the *rest* of your world—clusters, databases, storage systems, internal APIs. Instead of wiring that logic into every `graph_fn`, AetherGraph lets you attach **custom services** to the `context` object:

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
4. Apply practical patterns (HPC jobs, storage, external APIs).

**Goal:** keep agent logic clean and move integration glue into reusable, testable services.

---

## 1. What is a Custom Service, Really?

A *custom service* is a long‑lived Python object the runtime injects into every `NodeContext` under a chosen name.

Once registered, it works anywhere:

```python
@graph_fn(name="demo_trainer")
async def demo_trainer(*, context):
    job_id = await context.trainer().submit({"epochs": 10})
    return {"job_id": job_id}
```

**Key properties**

* **Named entrypoint** — you choose the accessor (e.g., `trainer`, `storage`, `models`).
* **Shared instance** — one instance reused across nodes/runs (unless you design otherwise).
* **Context‑aware** — methods can access the *current* `NodeContext` (`run_id`, `graph_id`, `node_id`).
* **Async‑first** — works naturally with `await` and the event loop.

Use a service when you have **state or connectivity** to share: clients, pools, caches, queues, background workers. For pure functions, a regular module is fine.

---

## 2. Minimal Service: from Zero to `context.trainer()`

### Step 1: Define a service class

Most custom services inherit from `Service` (aka `BaseContextService`) to get handy utilities: access to the current context, a service‑wide mutex, and helpers to run blocking code.

```python
from aethergraph.services.runtime.base import Service

class Trainer(Service):
    async def submit(self, spec: dict) -> str:
        """Submit a training job to your cluster/scheduler."""
        job_id = await self._submit_to_cluster(spec)  # implement backend call
        return job_id

    async def inspect_job(self, job_id: str) -> dict:
        status = await self._query_cluster(job_id)    # implement backend call
        return {"job_id": job_id, "status": status}
```

**Notes**

* `self.ctx()` gives you the **current** `NodeContext` at call time—so logs, memory, and artifacts are run‑scoped automatically.
* The service can hold **internal state** (connection pools, caches) across calls.

### Step 2: Register the service

Register an *instance* at startup (e.g., when your sidecar/server boots):

```python
from aethergraph import start_server
from aethergraph.services.runtime.registry import register_context_service

start_server()  # start sidecar so services can be wired

trainer_service = Trainer()
register_context_service("trainer", trainer_service)
```

From now on, inside any node:

```python
job_id = await context.trainer().submit(spec)
```

Pattern: **register once → call anywhere**.

---

## 3. Using Services Inside `graph_fn` and `@tool`

Services behave like built‑ins on `context`.

### Example A — Submit and track a job

```python
from aethergraph import graph_fn, tool

@graph_fn(name="train_and_wait", outputs=["job_id", "done"])
async def train_and_wait(spec: dict, *, context):
    job_id = await context.trainer().submit(spec)
    ready = await wait_for_training(job_id=job_id, context=context)
    return {"job_id": job_id, "done": ready["ready"]}

@tool(name="wait_for_training", outputs=["ready"])
async def wait_for_training(job_id: str, *, context) -> dict:
    info = await context.trainer().inspect_job(job_id)
    return {"ready": info["status"] == "COMPLETED"}
```

Why this is nice:

* **Cluster logic in one place** (`Trainer`), not scattered across graphs.
* Tests can swap in a fake `Trainer` that returns canned statuses.

### Example B — Custom storage wrapper

```python
class Storage(Service):
    async def put(self, local_path: str, key: str) -> str:
        uri = await self._upload(local_path, key)  # implement upload
        self.ctx().logger().info("storage.put", extra={"uri": uri})
        return uri

    async def get(self, uri: str, dest: str) -> None:
        await self._download(uri, dest)

@graph_fn(name="upload_report", outputs=["uri"])
async def upload_report(*, context):
    uri = await context.storage().put("/tmp/report.pdf", key="reports/2025-01-01.pdf")
    return {"uri": uri}
```

You can mix `context.storage()` with core features like `artifacts()` and `memory()`—for example, storing the CAS URI next to an external bucket URI.

---

## 4. Concurrency & Shared State

Because a service instance is shared, multiple nodes (or graphs) may hit it concurrently. If you expect concurrent accesses to a service, protect shared state inside the **service**, not at every call site.

### A) Service‑wide mutex (recommended pattern)

Use the built‑in `critical()` helper to guard a method. The pattern below **binds** the mutex to an instance method immediately after `__init__`, ensuring `self` exists:

```python
import asyncio
from aethergraph.services.runtime.base import Service

class CounterService(Service):
    def __init__(self):
        super().__init__()
        self._value = 0
        # Decorate incr with the bound service-wide mutex
        # The entire method runs under a critical section
        self.incr = self.critical()(self.incr)  # type: ignore

    async def incr(self, n: int = 1) -> int:
        self._value += n
        await asyncio.sleep(0)  # yield to event loop
        return self._value
```

> If you need finer‑grained control (e.g., per‑key locks, rate windows), design your own locking scheme inside the service. The point is to centralize concurrency policy in one place.

### B) Offload blocking work

```python
class Heavy(Service):
    async def compute(self, x: int) -> int:
        return await self.run_blocking(self._slow_cpu_fn, x)  # threadpool offload

    def _slow_cpu_fn(self, x: int) -> int:
        ...  # pure CPU work
```

This keeps agents responsive even when a service must do something synchronous or CPU‑heavy (e.g. heavy local simulation, training etc.).

---

## 5. Service Lifecycle (start/close)

Some integrations need setup/teardown—opening DB pools, authenticating SDKs, or warming models. Implement optional hooks on your service:

```python
class Tracker(Service):
    async def start(self):
        self._client = ...  # open DB/HTTP client

    async def close(self):
        if getattr(self, "_client", None):
            await self._client.aclose()
```

Call these from your process bootstrap/shutdown (sidecar, web server, CLI). The runtime doesn’t force a pattern—choose how you host services.

---

## 6. Testing & Swapping Implementations

Because services are registered by name, they’re easy to replace in tests:

```python
class FakeTrainer(Service):
    async def submit(self, spec: dict) -> str:
        return "job-test-123"

    async def inspect_job(self, job_id: str) -> dict:
        return {"job_id": job_id, "status": "COMPLETED"}

# Test setup
register_context_service("trainer", FakeTrainer())
# All code using context.trainer() now talks to the fake.
```

---

## 7. Design Tips & Common Patterns

A few patterns that work well in real projects:

* **One concept → one service**
  `context.trainer()` for orchestration, `context.storage()` for object stores, `context.materials()` for domain registries, etc.

* **Keep names explicit**
  Prefer `context.k8s_jobs()` or `context.minio()` over vague `context.utils()`.

* **Use services for anything stateful**
  HTTP clients, ORM sessions, caches, in‑memory registries, queues, schedulers.

* **Don’t replace built‑ins**
  Leave `context.memory()`, `context.artifacts()`, `context.channel()` alone. If you mirror to another system, create a separate service that consumes those.

**More handy service ideas**

| Scenario                              | Accessor                | What it wraps / does                           |
| ------------------------------------- | ----------------------- | ---------------------------------------------- |
| HPC / Training cluster                | `context.trainer()`     | Slurm/K8s jobs, Ray, internal queue            |
| External object storage               | `context.storage()`     | S3/GCS/MinIO, signed URLs, lifecycle/pinning   |
| Job/run tracking                      | `context.tracker()`     | DB for job metadata, status dashboards         |
| Feature or embedding store            | `context.vectorstore()` | Vector DB client, batch upserts, hybrid search |
| Materials/parts registry              | `context.materials()`   | Domain DB + caching (e.g., refractive indices) |
| Metrics/telemetry export              | `context.metrics()`     | Push to Prometheus/OTel/Grafana                |
| Lineage/BI export                     | `context.lineage()`     | Push run/graph/node metadata to warehouse      |
| PDF/Doc processing                    | `context.docs()`        | OCR, parsing, chunking utilities               |
| Secure secrets broker                 | `context.secrets()`     | Rotation, envelope decryption                  |
| Payment/billing                       | `context.billing()`     | Client to your billing/ledger microservice     |
| License/Entitlements                  | `context.license()`     | Gate features per user/org                     |
| Remote execution (HPC/VM functions)   | `context.runner()`      | Dispatch Python/CLI jobs to remote workers     |
| Caching layer for expensive API calls | `context.cache()`       | Memoization + TTL + invalidation               |
| Model hosting / inference gateway     | `context.predict()`     | Internal inference service with model registry |

---

## 8. Optional: Callable Services

If you like compact call sites, implement `__call__`:

```python
class Predictor(Service):
    async def __call__(self, prompt: str) -> str:
        return await self.generate(prompt)

    async def generate(self, prompt: str) -> str:
        ...

# After registration as "predictor":
text = await context.predictor("hello")               # calls __call__
text = await context.predictor().generate("hello")    # explicit method
```

Sugar only; explicit method names (`submit`, `inspect_job`, `upload`, `generate`) are often clearer for teams.

---

## 9. How This Fits with MCP and Other Integrations

In the previous section, **MCP** treated external processes (HTTP/WebSocket/stdio) as tools your agent can call. Custom services are the **other half**:

* **MCP**: great when the external system already speaks MCP and you want tools/resources auto‑described.
* **Custom services**: great when you want a **plain Python wrapper** around internal systems—no extra server, no protocol.

Projects often mix both:

* Use an MCP server for generic capabilities (filesystem, SQL, web search).
* Use services like `context.trainer()` and `context.storage()` for tightly‑coupled, org‑specific infrastructure.

With this pattern in place, you can keep adding capabilities by **teaching the runtime new services**, while keeping agent code small, readable, and testable.