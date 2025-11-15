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
* **Per‑node awareness** — access to built-in services through `self.ctx()` for provenance or multi‑tenancy.

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

class Trainer(Service):
    async def submit(self, spec: dict) -> str:
        # Submit a training job to your HPC/cluster
        ... 
        return job_id

    async def inspect_job(self, job_id: str) -> dict:
        # Inspect the job status
        ...
        return {"job_id": job_id, "status": status}
```

### Register at startup (pass an **instance**)

```python
from aethergraph.runtime import register_context_service
from aethergraph import start_server()

# register after server is started 
start_server() 
register_context_service("trainer",  Trainer())
```

> After this, `context.trainer()` is available everywhere in the runtime.

---

## 4. Usage Patterns

### A) Submit training & link artifacts

```python
@graph_fn(name="train_model", outputs=["job_id", "ckpt_uri"]) 
async def train_model(spec: dict, *, context):
    #  Submit to your cluster via the custom service
    job_id = await context.trainer().submit(spec)
    return {"job_id": job_id, "ckpt_uri": ckpt.uri}
```

### B) Inspect status in another node/tool

```python
@tool(name="wait_for_training", outputs=["ready"]) 
async def wait_for_training(job_id: str, *, context) -> dict:
    # Inspect you job through your service
    info = await context.trainer().inspect_job(job_id)
    return {"ready": info["status"] == "COMPLETED"}
```

---

## 5. Concurrency & Lifecycle

If you expect your services are accessed by multiple agents concurrently, consider the designs: 

* **Lifecycle hooks:** `start()` / `close()` are optional; call them from your app/server bootstrap.
* **Shared access:** use `self.critical()` to protect mutable shared state. Design your own mutex when scaling up. 
* **Per‑node context:** call `self.ctx()` whenever you need `{run_id, graph_id, node_id}`.
* **Async native:** expose async APIs; if integrating queues, consider `asyncio.Queue`.


---

## 6. Common Service Patterns (Examples)

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


## Summary

* **External services** add named capabilities to `context` without changing agent code.
* Built‑ins remain stable; extend via **new names** (no in‑place swaps).
* Register **instances**, not factories; services run on the **main event loop**.
* Use `self.ctx()` to fetch per‑node provenance on demand; protect shared state with `critical()` or your own lock design.
