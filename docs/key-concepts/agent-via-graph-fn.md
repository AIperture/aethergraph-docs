# Agents via `@graph_fn`

This page introduces **agents** in AetherGraph through the `@graph_fn` decorator, shows how `@tool` functions become **nodes** on the fly, and explains why/when to write **async** functions and how to chain/nest them.

---

## What is a `graph_fn`?

A `graph_fn` turns a plain Python function into an **agent** with access to rich **context services** (channel, memory, artifacts, logger, etc.). **By default, it runs in normal Python runtime**—no DAG is constructed just because you called the function. For most agentic workflows, this is **sufficient and preferred**: you get an ergonomic async function with `context` methods for interaction, memory, and side effects, without forcing a graph capture.

### Decorator signature

```python
@graph_fn(
    name: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    version: str = "0.1.0",
    agent: str | None = None,  # optional: also register as an agent name
)
```

**Required**

* **name** (str) – Unique identifier for this graph function.

**Optional**

* **inputs** (list[str]) – Declares input names for docs/registry (not enforced at call time).
* **outputs** (list[str]) – Declares output names/order; enables single‑literal returns. Required if you do not return a `dict`
* **version** (str) – Semantic version for registry/discovery.
* **agent** (str) – Also register in the `agent` namespace (advanced).

### Function shape

```python
@graph_fn(name="example")
async def example(x: int, *, context: NodeContext):
    # use services via context: channel/memory/artifacts/kv/llm/rag/mcp/logger
    await context.channel().send_text(f"x={x}")
    return {"y": x + 1}
```

* Positional/keyword parameters are **your** API.
* Include `*, context` to receive the `NodeContext`. If you don’t declare it, nothing is injected.

Minimal example:

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="hello_agent")
async def hello_agent(name: str = "world", *, context: NodeContext):
    # Uses standard Python execution; no nodes are created just by running this.
    await context.channel().send_text(f"👋 Hello, {name}!")
    context.memory().write_result(name="greet", value={"who": name})
    context.logger().info("Greeted user", extra={"name": name})
    return {"message": f"Hello, {name}"}
```

> **Key idea:** `@graph_fn` gives you an **agent surface** (context + async) while keeping execution **lightweight and reactive**. The runtime will only add nodes when you explicitly opt in (see §2).

---

## Quick intro to `@tool` — nodes on the fly

`@tool` marks a regular Python function as a **tool node**. **When a `graph_fn` calls a tool, the runtime creates a node on the fly** and can optionally capture its inputs/outputs for **inspection, provenance, and later features like persisted waits** (introduced later). This is useful when you want **traceable state** or need to **persist / resume** around boundaries.

> **Pragmatic guidance:** for exploratory, reactive research flows, you often **don’t need** tools—just call normal Python and use `context` for I/O, memory, and messaging. Reach for `@tool` when you want **graph/state capture** or durability guarantees.

### Decorator signature

```python
@tool(
    outputs: list[str],
    inputs: list[str] | None = None,
    *,
    name: str | None = None,
    version: str = "0.1.0",
)
``` 

**Required**

* **outputs** (str) – List of output keys

**Optional**

* **inputs** (list[str]) – Declares input names for docs/registry (not enforced at call time).
* **name** (str) – optional name of a tool.
* **version** (str) – Semantic version for registry/discovery.


Works on any plain Python function.

**Execution mode:**

  * **Graph mode:** inside a `graph_fn`, calling the tool **builds a node** (returns a handle under the hood).
  * **Immediate mode:** outside a graph, executes immediately (sync returns `dict`; async returns awaitable).


You can **mix** regular Python and `@tool` calls inside a `graph_fn`; only the `@tool` calls create nodes.

```python
from typing import List
from aethergraph import tool

@tool(name="sum_vec", outputs=["total"])  # declare outgoing fields
def sum_vec(xs: List[float]) -> dict:
    return {"total": float(sum(xs))}
```

Use inside a `graph_fn`:

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="tool_demo", outputs=["total"])
async def tool_demo(values: list[float], *, context: NodeContext):
    # regular Python is just executed; @tool creates a node and is captured
    stats = {"n": len(values)}                 # no node
    out = sum_vec(values)                       # ← node is captured
    await context.channel().send_text(f"n={stats['n']}, sum={out['total']}")
    return {"total": out["total"]}
```

A slightly richer tool (e.g., lightweight HTTP fetch):

```python
from aethergraph import tool
import json, urllib.request

@tool(name="fetch_json", outputs=["data"])
def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as r:
        return {"data": json.load(r)}
```

Then, in a `graph_fn`:

```python
@graph_fn(name="use_fetch", outputs=["data"]) 
async def use_fetch(url: str, *, context: NodeContext):
    res = fetch_json(url)                        # node is created on call
    context.logger().info("fetched", extra={"url": url})
    return {"data": res["data"]}
```

---

## Async functions: chaining, nesting, and running

AetherGraph is **async-first** because agents often:

* Wait for **user input** (`ask_text`, `ask_approval`),
* Perform **I/O** (HTTP, file ops),
* Launch **parallel** sub-steps.

### Chaining and nesting `graph_fn`s

You can call one `graph_fn` from another; each call becomes a child subgraph node.

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="step1", outputs=["y"])
async def step1(x: int, *, context: NodeContext) -> dict:
    return {"y": x + 1}

@graph_fn(name="step2", outputs=["z"])
async def step2(y: int, *, context: NodeContext) -> dict:
    return {"z": y * 2}

@graph_fn(name="pipeline", outputs=["z"]) 
async def pipeline(x: int, *, context: NodeContext) -> dict:
    a = await step1(x)              # child graph node
    b = await step2(a["y"])        # child graph node
    return {"z": b["z"]}          # => (x + 1) * 2
```

### Fan-out / concurrency

Launch independent awaits concurrently with `asyncio.gather`:

```python
import asyncio

@graph_fn(name="concurrent_steps", outputs=["r1","r2"]) 
async def concurrent_steps(a: int, b: int, *, context: NodeContext) -> dict:
    r1, r2 = await asyncio.gather(step1(a), step2(b))
    return {"r1": r1["y"], "r2": r2["z"]}
```

### Running a `graph_fn` like any async function

In scripts/tests you can `await` a `graph_fn` directly from an async context, or use the helper runner:

```python
# Option A: inside another graph_fn or an async test
result = await pipeline(3)

# Option B: top-level runner (e.g., in __main__)
from aethergraph import run

if __name__ == "__main__":
    final = run(pipeline(3))        # drives the event loop
    print(final)                    # {"z": 8}
```

> The `run(...)` helper drives the event loop and returns the final result, while the runtime records the graph only around `@tool`/child graph calls.

--- 

## Summary 

- `graph_fn` wraps a Python function into an async "agent" with an injected `NodeContext` (channel, memory, artifacts, logger, etc.) while executing in normal Python runtime—no graph nodes are created unless you opt in.
- Use `@tool` to mark functions as tool nodes; calling a tool inside a `graph_fn` creates a node on the fly and can capture inputs/outputs for provenance or persistence.
- You can call one `graph_fn` from another—each call becomes a child subgraph node—so compose agents naturally.
- The system is async-first for waiting on user input, performing I/O, and running concurrent work (use asyncio.gather for fan-out).
- For scripts/tests you can await `graph_fn`s directly or use `run(...)` to drive the event loop; prefer plain calls + context for lightweight, reactive workflows and use tools when you need traceability/durability.
