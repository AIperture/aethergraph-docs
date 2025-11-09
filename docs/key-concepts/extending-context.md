# Extending Context Services

AetherGraph lets you **extend the runtime** by adding your own `context.<name>` methods. These *external context services* live **alongside** built‑ins like `channel`, `memory`, and `artifacts`, and provide reusable, lifecycle‑aware helpers for clients, caches, orchestration, or domain APIs — **without changing your agent code**.

> **Key idea:** keep agent logic pure‑Python; move integration glue and shared state into **services** that the runtime injects per node.

---

## 1. What is an External Context Service?

A **context service** is a registered Python object bound into every `NodeContext`. After registration, you can use it anywhere inside a graph or tool:

```python
@graph_fn(name="demo")
async def demo(*, context):
    info = await context.trainer().inspect_job(job_id="abc123")
    return {"status": info["status"]}
```

### Why/When to Use

* **Reusable helpers** — share clients (e.g., HPC, S3, DB, solver), connection pools, or token buckets.
* **Shared state** — memoize expensive lookups; coordinate across nodes within a run.
* **Centralized config** — keep API keys, timeouts, routing, or policies in one place.
* **Lifecycle control** — optional `start()/close()` hooks for setup/teardown.
* **Per‑node awareness** — access `run_id/graph_id/node_id` for provenance or multi‑tenancy.

> Use a service for *long‑lived instances* or *cross‑node coordination*. For tiny stateless helpers, plain imports are fine.

---

## 2. Naming & Boundaries (Important)

Built‑ins (`context.artifacts()`, `context.memory()`, etc.) are **not swappable** in OSS. To extend the system, register **new services with new names** (e.g., `context.trainer()`, `context.datasets()`, `context.lineage_store()`).

* Keep agent code explicit about which storage or API it’s using.
* If mirroring/exporting, record links (artifact URIs, memory event IDs) inside your external system for provenance.

---

## 3. Minimal Service (Instance‑based)

### Define a service and use `self.ctx()`

```python
from aethergraph import Service

class RunAware(Service):
    async def tag_current(self) -> str:
        # Access the *current* NodeContext lazily
        ctx = self.ctx()
        return f"run={ctx.run_id} node={ctx.node_id}"

class Trainer(Service):
    async def submit(self, spec: dict) -> str:
        # Submit a training job to your HPC/cluster
        job_id = await self._submit_to_cluster(spec)
        # Log provenance to the *current* node
        self.ctx().logger().info("trainer.submit", extra={"job_id": job_id})
        return job_id

    async def inspect_job(self, job_id: str) -> dict:
        status = await self._query_cluster(job_id)
        return {"job_id": job_id, "status": status}
```

### Register at startup (pass an **instance**)

```python
from aethergraph.runtime import register_context_service

register_context_service("runaware", RunAware())
register_context_service("trainer",  Trainer())
```

> After this, `context.runaware()` and `context.trainer()` are available everywhere in the runtime.

---

## 4. Usage Patterns

### A) Submit training & link artifacts

```python
@graph_fn(name="train_model", outputs=["job_id", "ckpt_uri"]) 
async def train_model(spec: dict, *, context):
    # 1) Submit to your cluster via the custom service
    job_id = await context.trainer().submit(spec)
    # other waiting or inspection logic ...

    # 2) Imagine your trainer writes a checkpoint to /tmp/ckpt.bin 
    # (NOTE: you need to ensure the job finishes, this is a simplification)
    ckpt = await context.artifacts().save("/tmp/ckpt.bin", kind="checkpoint", labels={"job": job_id})
    return {"job_id": job_id, "ckpt_uri": ckpt.uri}
```

### B) Inspect status in another node/tool

```python
@tool(name="wait_for_training", outputs=["ready"]) 
async def wait_for_training(job_id: str, *, context) -> dict:
    info = await context.trainer().inspect_job(job_id)
    return {"ready": info["status"] == "COMPLETED"}
```

### C) Background/Blocking helpers

```python
class Heavy(Service):
    async def compute(self, x: int) -> int:
        # Offload CPU/binding operations without blocking the event loop
        return await self.run_blocking(lambda: slow_cpu_fn(x))
```

---

## 5. Concurrency & Lifecycle

* **Lifecycle hooks:** `start()` / `close()` are optional; call them from your app/server bootstrap.
* **Shared access:** use `self.critical()` or an `AsyncRWLock` to protect mutable shared state.
* **Per‑node context:** call `self.ctx()` whenever you need `{run_id, graph_id, node_id}`.
* **Backpressure:** expose async APIs; if integrating queues, consider `asyncio.Queue` or your platform’s client backpressure.

---

## 6. Testing & Mocking

* Provide a **fake implementation** with the same interface for unit tests.
* Register your fake with the same name (e.g., `"trainer"`) in the test harness.
* Use in‑memory structures (dicts, temp dirs) for deterministic tests.

---

## 7. Error Handling & Observability

* Emit structured logs via `context.logger()` with operation names and durations.
* Normalize exceptions from vendor SDKs into your own error types.
* Consider retry/backoff wrappers in the service (centralized, consistent).

---

## 8. Common Service Patterns (Examples)

| Scenario                           | Suggested accessor        | What it abstracts                      | Typical operations                                   |
| ---------------------------------- | ------------------------- | -------------------------------------- | ---------------------------------------------------- |
| **HPC / Training orchestration**   | `context.trainer()`       | Submit/track jobs on Slurm/K8s/Ray     | `submit(spec)`, `inspect_job(id)`, `cancel(id)`      |
| **External object storage**        | `context.storage()`       | S3/GCS/MinIO buckets & signed URLs     | `put(path)`, `get(uri)`, `sign(uri)`, `list(prefix)` |
| **Vendor API client**              | `context.apiclient()`     | Rate‑limited, retried HTTP SDK         | `get/put/post`, `batch()`, `retry/backoff`           |
| **In‑house AI models**             | `context.models()`        | Local inference endpoints              | `embed(texts)`, `generate(prompt)`                   |
| **Materials DB / domain registry** | `context.materials()`     | Domain lookups & cached tables         | `get_index(name)`, `search(filters)`                 |
| **Lineage export**                 | `context.lineage_store()` | Mirror core provenance to BI/warehouse | `export_run(run_id)`, `push(events)`                 |

> Pick names that are **explicit** in your org (e.g., `context.k8s_jobs()`, `context.minio()`). Avoid names that shadow built‑ins.

---

## 9. Optional callable services

You may define `__call__` on a service to allow a compact form like `await context.trainer(spec)` in addition to `await context.trainer().submit(spec)`. This can be handy when switching model profiles or submitting a quick spec inline. It's supported, but for clarity we generally **recommend explicit method calls**.

```python
class Trainer(Service):
    async def __call__(self, spec: dict) -> str:
        return await self.submit(spec)

    async def submit(self, spec: dict) -> str:
        ...

# Both are valid
job_id = await context.trainer(spec)
job_id = await context.trainer().submit(spec)
```

## 10. Recap

* **External services** add named capabilities to `context` without changing agent code.
* Built‑ins remain stable; extend via **new names** (no in‑place swaps).
* Register **instances**, not factories; services run on the **main event loop**.
* `ServiceHandle` supports both `context.svc()` (instance) and optional callable forwarding if your service implements `__call__`.
* Use `self.ctx()` to fetch per‑node provenance on demand; protect shared state with `AsyncRWLock` or `critical()`.

**See also:** External Context Deep Dive → · Channels & Interaction → · Artifacts & Memory →
