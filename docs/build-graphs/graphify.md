# `@graphify` — Build an explicit DAG (fan-out, fan-in, ordering)

Use `@graphify` when you need clear topology: map/fan-out, reduce/fan-in, barriers via `_after`, subgraphs, or reusable pipelines.

## Signature
```
@graphify(*, name="default_graph", inputs=(), outputs=None, version="0.1.0", agent: str | None = None)
def body(...):
    # Use tool calls to add nodes and return NodeHandles/Refs
    return {...}
```
- The decorated function returns a builder: call `.build()` to get a `TaskGraph` instance; `.spec()` for a serializable spec; `.io()` for IO signature.

## Control edges and labels (graph build only)
`@tool` control kwargs are honored here:
- `_after`, `_alias`, `_labels`, `_id`, `_name`

## Patterns

### Fan-out (map over inputs)
```python
from aethergraph import tool, graphify

@tool(outputs=["vec"])
def embed(text: str): ...

@graphify(name="fanout_demo", inputs=["texts"], outputs=["vecs"])
def fanout_demo(texts):
    handles = [embed(text=t) for t in texts]          # fan-out
    return {"vecs": [h.vec for h in handles]}         # expose list of outputs
```

### Fan-in (reduce)
```python
@tool(outputs=["score"])
def dot(a, b): ...

@graphify(name="fanin_demo", inputs=["query", "vecs"], outputs=["scores"])
def fanin_demo(query, vecs):
    q = embed(text=query)
    scores = [dot(a=v, b=q.vec) for v in vecs]        # fan-in through q
    return {"scores": [s.score for s in scores]}
```

### Control edge without data
```python
@tool(outputs=["ok"])   def init(): ...
@tool(outputs=["done"]) def train(): ...

@graphify(name="order", outputs=["done"])
def order():
    a = init()
    b = train(_after=a)            # sequence a -> b
    return {"done": b.done}
```

### Subgraph reuse (optional)
You can register graphs and call them as nodes (advanced). For most cases, compose `@tool`s directly inside `@graphify`.

## When to use `@graphify`
- You need parallelism (map) or aggregation (reduce).
- You need ordering without data flow (`_after`/barriers).
- You want a reusable / inspectable DAG (e.g., schedule in a UI).

See also: [graph_fn.md](./graph_fn.md), [tool.md](./tool.md), [choosing.md](./choosing.md).
