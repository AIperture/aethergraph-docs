# AetherGraph — `@tool` Decorator (Reference & How‑to)

`@tool` turns a plain Python function into a **tool node** that can be executed immediately *or* added to a graph
during build time. You write ordinary Python, declare outputs, and AetherGraph handles result normalization and
graph node creation.

---

## What is a Tool?

A **tool** is a reusable, IO‑typed operation that can be executed on its own or orchestrated inside a graph.
Tools are perfect for things like “load CSV”, “train model”, “plot chart”, “send_slack”, etc.

- **Immediate mode** (no graph builder active): calling the tool runs the Python function right away and returns a **dict** of outputs.
- **Graph mode** (inside a `with graph(...):` block or a `@graphify` body): calling the tool **adds a node** to the graph and returns a `NodeHandle` you can wire to other nodes (fan‑in/fan‑out).
- Tools automatically register in the runtime registry (`nspace="tool"`) when a registry is active.

> This page covers the simple function form. (The advanced *waitable* class form is documented separately.)

---

## Decorator Signature

```python
from aethergraph import tool

@tool(outputs: list[str], *, inputs: list[str] | None = None,
      name: str | None = None, version: str = "0.1.0")
def your_function(...): ...
```

**Parameters**

- **outputs** (*list[str], required*) — Declares the output keys your tool will produce.
- **inputs** (*list[str], optional*) — Explicit input names. Omit to infer from function signature (excluding `*args`/`**kwargs`).  
- **name** (*str, optional*) — Registry/display name. Defaults to the function’s `__name__`.  
- **version** (*str, optional*) — Semantic version recorded in the registry (default: `"0.1.0"`).

**Return value (call‑site dependent)**

- **Immediate mode**: returns a **`dict`** of outputs.  
- **Graph mode**: returns a **`NodeHandle`** (or an awaitable handle under an interpreter) to be wired/exposed by the builder.

---

## Return Normalization

The wrapped function can return different shapes; the decorator normalizes into a dict that must include every declared output:

- `None` → `{}`
- `dict` → used as‑is
- `tuple` → `{"out0": v0, "out1": v1, ...}`
- single value → `{"result": value}`

> If any declared `outputs` are missing from the normalized dict, a `ValueError` is raised.

---

## Control Keywords (graph mode)

When calling a tool *while building a graph* (e.g., inside a `with graph(...):` or `@graphify` body), you may pass these special kwargs to influence scheduling/metadata:

- **`_after`** (*NodeHandle | list[NodeHandle | node_id]*): explicit dependency edges (fan‑in).  
- **`_name`** (*str*): display name for UI/spec.  
- **`_id`** (*str*): hard override of the node ID (must be unique in the graph).  
- **`_alias`** (*str*): optional alias for reverse lookups.  
- **`_labels`** (*Iterable[str]*): lightweight tags for search/grouping.

Example:

```python
res = my_tool(a=arg_a, b=arg_b, _after=[prev1, prev2], _name="preprocess", _labels=["data","prep"])
```

> These control keys are stripped before calling your function and only affect graph construction.

---

## Simple Examples

### 1) Immediate execution (no graph builder active)

```python
from aethergraph import tool

@tool(outputs=["sum", "mean"])  # outputs you promise to return
def stats(xs: list[float]):
    s = sum(xs)
    return {"sum": s, "mean": s / len(xs)}

out = stats([1,2,3,4])   # → {"sum": 10, "mean": 2.5}
```

### 2) Graph construction (inside a builder)

```python
from aethergraph import tool
from aethergraph import graphify
from aethergraph.graph import arg  # or from aethergraph.graph.graph_refs import arg

@tool(outputs=["y"])
def add(x: int, z: int): return {"y": x + z}

@tool(outputs=["z"])
def mul(x: int, k: int): return {"z": x * k}

@graphify(name="pipeline", inputs=["x"], outputs=["y"])
def pipeline(x):
    a = mul(x=arg("x"), k=2)          # NodeHandle("mul_...")
    b = add(x=arg("x"), z=a.z)        # depends on `a` automatically via data edge
    return {"y": b.y}

G = pipeline.build()                    # TaskGraph
spec = pipeline.spec()                  # graph spec for inspection/registry
io = pipeline.io()                      # IO signature
```

### 3) Forcing an order with `_after` (no data edge)

```python
@tool(outputs=["ok"])
def init(): return {"ok": True}

@tool(outputs=["ready"])
def warmup(): return {"ready": True}

@graphify(name="order_demo", inputs=[], outputs=["ready"])
def order_demo():
    n1 = init()
    n2 = warmup(_after=n1)   # enforce sequencing without passing data
    return {"ready": n2.ready}
```

---

## Registration (Optional)

If a runtime registry is active (via `current_registry()`), the decorator auto‑registers your tool under the `tool` namespace
with its `name` and `version` so it can be listed and referenced later.

You can also call tools by **dotted path** via `call_tool("pkg.module:function", arg1=..., ...)` to avoid importing
at build sites, but the recommended ergonomic flow is to `import` the tool and call it directly.

---

## Best Practices

- Keep tools focused and side‑effect aware (e.g., write artifacts via `context.artifacts()` inside `@graph_fn` wrappers).
- Always declare `outputs` and make your function return those keys.
- Use `_after` for control dependencies when no data edge exists.
- Prefer composing tools via `@graphify` for explicit fan‑in/fan‑out graphs.
- Inside `@graph_fn`, you *can* call tools to create explicit nodes, but `@graph_fn` is for immediate orchestration.