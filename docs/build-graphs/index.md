# Build Graphs in AetherGraph

Welcome! This section is the fastest way to grok how to build and run graphs with Python-first ergonomics.

We introduce things in the order you will actually use them:

1. **`@graph_fn`** — the on-ramp. Wrap a regular Python function so it runs as a single graph node, with full `context.*` access. Great for demos, services, notebooks.
2. **`@tool`** — make any function a graph node. Use it inside `graph_fn` for per-step visibility, metrics, artifacts, and reuse.
3. **`@graphify`** — build an explicit DAG for fan-out/fan-in, ordering via `_after`, subgraphs, and reuse.

Tip: Start with `@graph_fn` (plus a couple of `@tool` calls). Move to `@graphify` when you want explicit topology, parallel map/reduce, barriers, or long-lived pipelines.

---

## What is a "graph" here?

- AetherGraph executes TaskGraphs — directed acyclic graphs of nodes.
- A node can be:
  - a graph function (`@graph_fn`) — runs immediately and can call context services.
  - a tool node (`@tool`) — a typed, reusable operation with visible inputs/outputs.
- The Context (`context.*`) gives every node uniform access to runtime services:
  `channel()`, `artifacts()`, `memory()`, `kv()`, `llm()`, `rag()`, `mcp()`, `logger()`.

---

## Quickstart (30 lines)

```python
from aethergraph import graph_fn, tool

@tool(outputs=["y"])
def square(x: int):
    return {"y": x * x}

@graph_fn(name="demo", outputs=["y"])
async def demo(x: int, *, context):
    await context.channel().send_text(f"Computing square of {x}…")
    h = square(x=x)              # creates a node you can inspect later
    await context.channel().send_text("Done.")
    return {"y": h.y}            # expose tool output
```

Why this design?
- You get instant run semantics (like a normal async function), but steps you mark with `@tool` become visible graph nodes with metrics/artifacts.
- When your flow grows and needs explicit fan-out/fan-in or ordering, switch to `@graphify`.

---

### Next steps

- `graph_fn` (on-ramp) -> [graph_fn.md](./graph_fn.md)
- `@tool` reference -> [tool.md](./tool.md)
- `@graphify` (explicit DAG + fan-in/out) -> [graphify.md](./graphify.md)
- Choosing the right approach -> [choosing.md](./choosing.md)
