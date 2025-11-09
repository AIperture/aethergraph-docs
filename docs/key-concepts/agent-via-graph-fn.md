# Agents via `@graph_fn`

This chapter introduces **agents** in AetherGraph through the `@graph_fn` decorator. You’ll learn how `@tool` functions become **nodes** on the fly, when and why to use **async** functions, and how to chain or nest them to form structured yet reactive agentic workflows.

---

## 1. What is a `graph_fn`?

A `graph_fn` turns a plain Python function into an **agent** with access to rich **context services**—channel, memory, artifacts, logger, and more. It runs in the **normal Python runtime** by default; no DAG is captured automatically when you invoke it. For most interactive or agentic workflows, this lightweight mode is ideal: you get an ergonomic async function with context utilities for I/O, persistence, and orchestration without committing to graph capture.

### Function shape

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="example")
async def example(x: int, *, context: NodeContext):
    # Access runtime services from the context
    await context.channel().send_text(f"x={x}")
    return {"y": x + 1}
```

* Define your own API through standard parameters.
* Include `*, context` to access the `NodeContext`; if omitted, nothing is injected.

Minimal example:

```python
@graph_fn(name="hello_agent")
async def hello_agent(name: str = "world", *, context: NodeContext):
    await context.channel().send_text(f"👋 Hello, {name}!")
    context.memory().record(kind="usr_data", data={"name": name})
    context.logger().info("Greeted user", extra={"name": name})
    return {"message": f"Hello, {name}"}
```

> **Key idea:** `@graph_fn` provides a **reactive agent interface**—async execution with contextual power—while keeping runtime overhead minimal. Nodes are only added when you explicitly use `@tool` or call other graphs.

---

## 2. Tools: nodes on the fly

The `@tool` decorator marks a Python function as a **tool node**. When called inside a `graph_fn`, the runtime creates a **node on the fly** and records its inputs/outputs for provenance, inspection, or future resumptions.

> **Rule of thumb:** for exploratory, reactive development, call regular Python functions freely. Reach for `@tool` when you need **traceable state**, **durability**, or **resume checkpoints**.

### Example: a simple sum tool

```python
from typing import List
from aethergraph import tool

@tool(name="sum_vec", outputs=["total"])
def sum_vec(xs: List[float]) -> dict:
    return {"total": float(sum(xs))}
```

Use inside a `graph_fn`:

```python
@graph_fn(name="tool_demo", outputs=["total"])
async def tool_demo(values: list[float], *, context: NodeContext):
    stats = {"n": len(values)}             # executed inline
    out = sum_vec(values)                  # ← captured as a node
    await context.channel().send_text(f"n={stats['n']}, sum={out['total']}")
    return {"total": out["total"]}
```

You can mix normal Python code and `@tool` calls seamlessly. Only `@tool` calls create nodes.

### Example: lightweight HTTP fetch tool

```python
from aethergraph import tool
import json, urllib.request

@tool(name="fetch_json", outputs=["data"])
def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as r:
        return {"data": json.load(r)}
```

Then call it inside a `graph_fn`:

```python
@graph_fn(name="use_fetch", outputs=["data"])
async def use_fetch(url: str, *, context: NodeContext):
    res = fetch_json(url)                   # node created dynamically
    context.logger().info("fetched", extra={"url": url})
    return {"data": res["data"]}
```

To inspect the implicit graph created during execution, call `graph_fn.last_graph()` — it returns the captured `TaskGraph` for visualization or reuse.

---

## 3. Async-first: chaining, nesting, and concurrency

AetherGraph adopts **async-first design** because agents often:

* Wait for **user input** (`ask_text`, `ask_approval`)
* Perform **I/O** (HTTP, file writes, DB queries)
* Launch **parallel sub-tasks**

### Chaining and nesting `graph_fn`s

You can call one `graph_fn` from another. Each call creates a **child subgraph node**:

```python
@graph_fn(name="step1", outputs=["y"])
async def step1(x: int, *, context: NodeContext) -> dict:
    return {"y": x + 1}

@graph_fn(name="step2", outputs=["z"])
async def step2(y: int, *, context: NodeContext) -> dict:
    return {"z": y * 2}

@graph_fn(name="pipeline", outputs=["z"])
async def pipeline(x: int, *, context: NodeContext) -> dict:
    a = await step1(x)       # → child node
    b = await step2(a["y"]) # → child node
    return {"z": b["z"]}
```

### Fan-out concurrency

Launch multiple subgraphs concurrently with `asyncio.gather`:

```python
import asyncio

@graph_fn(name="concurrent_steps", outputs=["r1", "r2"])
async def concurrent_steps(a: int, b: int, *, context: NodeContext) -> dict:
    r1, r2 = await asyncio.gather(step1(a), step2(b))
    return {"r1": r1["y"], "r2": r2["z"]}
```

This pattern enables natural fan-out/fan-in parallelism within a single reactive agent.

---

## 4. Running a `graph_fn`

You can execute a `graph_fn` directly from async code or through the provided runners.

### Option A – Direct await

```python
# In an async function
result = await pipeline(3)
```

### Option B – Synchronous helper

```python
from aethergraph.runner import run
final = run(pipeline(3))
```

### Option C – Explicit async runner

```python
from aethergraph.runner import run_async
# In an async function
result = await run_async(pipeline)
```

The `run_*` helpers drive the event loop and normalize execution for both reactive and static graphs.

---

## 5. Summary

* `@graph_fn` wraps a Python function into an **async agent** with an injected `NodeContext` exposing rich runtime services.
* Execution stays in normal Python until you invoke `@tool` or another `graph_fn`—only those create nodes.
* `@tool` functions let you capture intermediate steps for provenance and durability.
* Agents are composable: call one `graph_fn` from another or fan out with `asyncio.gather`.
* Use `run()` or `run_async()` for simple orchestration; prefer plain calls + context for lightweight workflows.

> AetherGraph’s agent model combines Pythonic simplicity with event-driven introspection—reactive first, deterministic when needed.