# Concurrency, Fan‑In/Fan‑Out & Graph‑Level Orchestration

AetherGraph provides **Python‑first concurrency** that scales from small reactive agents to globally scheduled DAGs. You can orchestrate parallelism naturally in Python, while the runtime enforces safe scheduling and per‑run concurrency caps.

---

## 1. `@graph_fn` — Pythonic Concurrency for Reactive Agents

`@graph_fn` functions execute through normal Python async semantics. **Plain Python awaits run directly on the event loop**, while **any `@tool` calls inside a `@graph_fn` become implicit nodes** managed by the agent’s internal scheduler.

**Example: bounded fan‑out using a semaphore**

```python
import asyncio
from aethergraph import graph_fn

sem = asyncio.Semaphore(4)  # cap concurrent jobs (user-managed)

async def run_capped(fn, **kw):
    async with sem:
        return await fn(**kw)

@graph_fn(name="batch_agent")
async def batch_agent(items: list[str], *, context):
    async def one(x):
        await context.channel().send_text(f"processing {x}")
        return {"y": x.upper()}

    # fan‑out with manual cap
    tasks = [run_capped(one, x=v) for v in items]
    results = await asyncio.gather(*tasks)

    # fan‑in
    return {"ys": [r["y"] for r in results]}
```

**Notes:**

* Plain Python steps execute immediately — **not capped** by the scheduler.
* `@tool` calls are scheduled and counted toward the agent’s concurrency cap through `max_concurrency` (default = **4**).
* You can override per‑run limits by passing `max_concurrency=<int>` to `run()` or `run_async()` or use `graph_fn(.., max_concurrency=<int>)`.
* For nested or composed agents, effective concurrency multiplies; use semaphores or pools to control load.
* Ideal for reactive, exploratory agents or mixed I/O + compute logic.

---

## 2. `@graphify` — Scheduler‑Controlled Static DAGs

In static DAGs built with `@graphify`, every `@tool` call becomes a node in a **TaskGraph**. Concurrency is automatically managed by the runtime scheduler, respecting per‑run limits.

**Minimal fan‑in/fan‑out example:**

```python
from aethergraph import graphify, tool

@tool(outputs=["out"])
async def work(x: int):
    return {"out": x * 2}

@tool(outputs=["sum"])
async def reduce_sum(xs: list[int]):
    return {"sum": sum(xs)}

@graphify(name="map_reduce", inputs=["vals"], outputs=["sum"])
def map_reduce(vals):
    outs = [work(x=v) for v in vals]       # fan‑out
    total = reduce_sum(xs=[o.out for o in outs])  # fan‑in
    return {"sum": total.sum}
```

**Key points:**

* The scheduler enforces `max_concurrency` automatically (default = **4**).
* You can override per‑run limits by passing `max_concurrency=<int>` to `run()`, or `run_async()`.
* Static DAG concurrency is global and consistent across all tool nodes.
* Each node runs once dependencies resolve; no explicit `await` is required.

---

## 3. Graph‑Level Orchestration Patterns

All orchestration in AetherGraph is **just Python**. You can run sequentially or concurrently using standard async primitives.

### A) Sequential orchestration (plain Python)

```python
res1 = await graph_fn1(a=1)
res2 = await graph_fn2(b=2)
```

### B) Concurrent `graph_fn` runs (async‑friendly)

```python
res1, res2 = await asyncio.gather(
    graph_fn1(a=1),
    graph_fn2(b=2),
)
```

### C) Concurrent graph runner (works for both `graph_fn` and `graphify`)

```python
from aethergraph.runner import run_async

res1, res2 = await asyncio.gather(
    run_async(graph1, inputs={"a": 1}, max_concurrency=8),
    run_async(graph2, inputs={"b": 2}, max_concurrency=2),
)
```

> Default concurrency for **each** graph is **4**, but you can override it per call with `max_concurrency` in either `run()` or `run_async()`.
> Becareful of global concurrency limit. Use semaphores or pools to control load. 

---

## 4. Nested and Multi‑Graph Execution

**Nested `@graph_fn`** — supported. Each agent has its own scheduler; nested agents may multiply total concurrency. Use global semaphores or resource pools to cap total parallelism.

**Nested `@graphify`** — not supported yet. Static graphs cannot call other static graphs as nodes; compose them at the orchestration layer instead.

---

## 5. Concurrency Comparison

| Aspect                  | `@graph_fn` (Reactive)                    | `@graphify` (Static)                          |
| ----------------------- | ----------------------------------------- | --------------------------------------------- |
| Concurrency Control     | Automatic via scheduler (`max_concurrency`) | Automatic via scheduler (`max_concurrency`)   |
| Default Limit           | Default 4 per run, multiply with nested calls                  | Default 4 per run                             |
| Plain Python Awaitables | Run immediately, outside scheduler        | Not applicable (only tool nodes)              |
| Nested Calls            | Supported                                 | Not yet supported                             |
| Failure Behavior        | Caught at runtime; user decides           | Scheduler stops on first error (configurable) |
| Use Case                | Agents, exploration, hybrid control       | Pipelines, batch workflows, reproducible DAGs |

---

## Takeaways

* **Reactive vs Deterministic:** `graph_fn` for interactive exploration; `graphify` for reproducible pipelines.
* **Fan‑In/Fan‑Out:** Async patterns in `graph_fn`; data edges in `graphify`.
* **Concurrency Control:** Default cap = 4; override per run with `max_concurrency`.
* **Scalability:** Local schedulers per agent; a global scheduler orchestrates multiple runs.
* **Everything is Python:** The runtime extends standard async execution into persistent, inspectable DAG scheduling.
