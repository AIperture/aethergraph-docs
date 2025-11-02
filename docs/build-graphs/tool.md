# `@tool` — Turn any function into a graph node

Make a plain function a typed, reusable node with explicit inputs/outputs. Works in both `@graph_fn` (immediate run with visible steps) and `@graphify` (graph build).

## Decorator
```
@tool(outputs: list[str], inputs: list[str] | None = None, *, name: str | None = None, version: str = "0.1.0")
def fn(...): ...
```

- **outputs** (list[str]) — Output field names this tool produces.
- **inputs** (list[str], optional) — Input names; inferred from signature if omitted.
- **name** (str, optional) — Registry name (defaults to function name).
- **version** (str) — SemVer for registry/lineage.

## Return normalization
- `None` -> `{}`
- `dict` -> as-is
- `tuple` -> `{ "out0": v0, "out1": v1, ... }`
- single value -> `{ "result": value }`

Contract check: Declared `outputs` must be present in the normalized return, otherwise a `ValueError` is raised.

## Two modes (same decorator)

| Where called from        | Behavior                                   |
|--------------------------|---------------------------------------------|
| Outside any graph        | Runs immediately and returns a dict.        |
| Inside `@graph_fn`       | Creates a node handle you can expose.       |
| Inside `@graphify`       | Adds a node to the DAG (honors control kw). |

Control kwargs (graph build only):
- `_after` (NodeHandle | list) — add control-edge dependency.
- `_alias` / `_id` — override node id / alias.
- `_labels` (list[str]) — annotate node for UI/search.
- `_name` — display name hint.

## Minimal example
```python
from aethergraph import tool

@tool(outputs=["y"])
def square(x:int) -> dict:
    return {"y": x*x}
```

Use in `graph_fn` or `@graphify` as shown in their pages.
