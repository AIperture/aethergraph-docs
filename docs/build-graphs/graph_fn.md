# `@graph_fn` — Python-first on-ramp

Wrap a normal (async) Python function so it runs as a single graph node with full access to `context.*` services. Return values are exposed as graph outputs.

## Signature
```
@graph_fn(name: str, *, inputs: list[str] | None = None, outputs: list[str] | None = None, version: str = "0.1.0", agent: str | None = None)
def|async def fn(..., *, context: NodeContext) -> dict | value | NodeHandle
```

- **name** (str) — Graph identifier.
- **inputs** (list[str], optional) — Declared input keys (used for IO spec; optional for quickstart).
- **outputs** (list[str], optional) — Declared output keys (enables single-value return).
- **version** (str) — SemVer for registry/lineage.
- **agent** (str, optional) — If set, register this graph function as an agent (advanced).

## Return normalization
- dict -> keys become outputs; NodeHandles/Refs are exposed.
- single value -> allowed only if exactly one `outputs` key is declared (collapsed to that name).
- NodeHandle -> its outputs are exposed (single output collapses).

## Using `@tool` inside `graph_fn`

You can call `@tool` functions to create visible/inspectable nodes while keeping immediate Python control flow:

```python
from aethergraph import graph_fn, tool

@tool(outputs=["y"])
def square(x: int): return {"y": x*x}

@graph_fn(name="demo", outputs=["y"])
async def demo(x: int, *, context):
    h = square(x=x)          # creates a node
    await context.channel().send_text("computed")
    return {"y": h.y}
```

Important: Control kwargs like `_after`, `_alias`, `_labels` are only honored in graph build contexts (e.g., `@graphify`). Inside `graph_fn`, execution order follows normal Python semantics. If you need control edges without passing data, use `@graphify`.

## When to use `@graph_fn`

- Quick demos, notebooks, service-style tasks.
- One to a few steps, mostly sequential.
- You want full `context.*` access and instant execution, with optional visibility via `@tool` calls.

See also: [tool.md](./tool.md), [graphify.md](./graphify.md).
