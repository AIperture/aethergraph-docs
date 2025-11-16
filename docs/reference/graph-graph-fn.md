# `@graph_fn` – Graph Function API

`@graph_fn` turns a plain Python function into a **GraphFunction** object – a named, versioned graph entry that still feels like a normal Python callable.

* You write a regular function (usually `async`) with whatever parameters you want.
* If the function’s signature includes a `context` parameter, a **`NodeContext`** is injected automatically.
* Inside the body, calls to `@tool` functions are recorded as **nodes**, while plain Python calls just run inline.

This section focuses on the **API surface and contracts**, not on execution details or schedulers.

---

## 1. GraphFunction Overview

The decorator builds a `GraphFunction` instance:

```python
class GraphFunction:
    def __init__(
        self,
        name: str,
        fn: Callable,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        version: str = "0.1.0",
    ):
        self.graph_id = name
        self.name = name
        self.fn = fn
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.version = version
        self.registry_key: str | None = None
        self.last_graph = None
        self.last_context = None
        self.last_memory_snapshot = None
```

### Key attributes

| Attribute              | Type                | Meaning / contract                                                                                       |
| ---------------------- | ------------------- | -------------------------------------------------------------------------------------------------------- |
| `graph_id`             | `str`               | Stable identifier for the graph, usually equal to `name`. Used for specs, visualization, and provenance. |
| `name`                 | `str`               | Human‑readable name of the graph function. Shows up in logs/registry.                                    |
| `fn`                   | `Callable`          | The original Python function body you wrote. Used to build the graph and evaluate return values.         |
| `inputs`               | `list[str]`         | Declared **graph input names**. Optional; can be empty.                                                  |
| `outputs`              | `list[str]`         | Declared **graph output names**. Optional; used for output normalization/validation.                     |
| `version`              | `str`               | Version tag for this graph. Included in registry entries and provenance.                                 |
| `registry_key`         | `str \| None`       | Internal hook for registry bookkeeping. Not part of the public contract.                                 |
| `last_graph`           | `TaskGraph \| None` | Last built graph (for inspection and debugging). May be `None` if not built yet.                         |
| `last_context`         | `Any`               | Reserved for runtime use (not a stable API).                                                             |
| `last_memory_snapshot` | `Any`               | Reserved for runtime use (not a stable API).                                                             |

> Treat `graph_id`, `name`, `inputs`, `outputs`, `version`, and `last_graph` as the **main public surface**; the other fields are implementation details that can change.

---

## 2. `@graph_fn` Decorator – Definition

```python
def graph_fn(
    name: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    version: str = "0.1.0",
    agent: str | None = None,
) -> Callable[[Callable], GraphFunction]:
    ...
```

### Parameters

| Parameter | Type                | Required? | Description                                                                                                                               |
| --------- | ------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `name`    | `str`               | **Yes**   | Logical ID for the graph. Also used as the `graphfn` registry name.                                                                       |
| `inputs`  | `list[str] \| None` | No        | Optional list of **named graph inputs**. If omitted, the graph can still accept `**inputs`, but there is no typed input list in the spec. |
| `outputs` | `list[str] \| None` | No        | Optional list of **declared graph outputs**. Used to normalize and validate the function’s return value.                                  |
| `version` | `str`               | No        | Semantic version for this graph. Defaults to `"0.1.0"`.                                                                                   |
| `agent`   | `str \| None`       | No        | If provided, additionally registers this `GraphFunction` in the registry under the `agent` namespace with the given name.                 |

### What the decorator returns

Using `@graph_fn` on a function returns a **`GraphFunction` instance**, not the raw function:

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="example", inputs=["x"], outputs=["y"])
async def example(x: int, *, context: NodeContext):
    ...

# `example` is now a GraphFunction
assert isinstance(example, GraphFunction)
```

Internally, the decorator:

1. Constructs `GraphFunction(name, fn, inputs, outputs, version)`.
2. Looks up the **current registry** via `current_registry()`.
3. If a registry is available, registers the object as:

     * `nspace="graphfn"`, `name=name`, `version=version`, `obj=gf`.

4. If `agent` is provided, also registers:

     * `nspace="agent"`, `name=agent`, `version=version`, `obj=gf`.

The `agent` registration currently serves as metadata for higher‑level agent frameworks; it does **not** change how the graph function runs.

---

## 3. Function Shape & Context Injection

A `graph_fn` is written like a normal Python function. The only special convention is the optional `context` parameter:

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="example")
async def example(x: int, *, context: NodeContext):
    # `context` is injected automatically
    await context.channel().send_text(f"x={x}")
    return {"y": x + 1}
```

**Rules:**

* You can define any positional/keyword parameters you want (`x`, `y`, `options`, etc.).
* If the function signature contains a parameter named `context`, the runtime **injects a `NodeContext`** instance when building/executing the graph.
* If `context` is **not** present in the signature, nothing special is injected.

> The injected `NodeContext` gives you access to runtime services like `channel()`, `memory()`, `artifacts()`, `logger()`, etc. This is the main way `graph_fn`s interact with the outside world.

---

## 4. Tools vs Plain Callables Inside a `graph_fn`

Inside a graph function body, you can freely mix:

1. **Plain Python code and callables** – executed immediately as normal Python.
2. **`@tool` functions** – these create graph nodes and tracked edges when invoked.

### Plain callables

Regular functions or methods (not decorated with `@tool`) behave exactly as in standard Python:

```python
def local_scale(x: int, factor: int = 2) -> int:
    return x * factor

@graph_fn(name="mixed_body")
async def mixed_body(x: int, *, context: NodeContext):
    y = local_scale(x)          # plain Python call, no node created
    context.logger().info("scaled", extra={"y": y})
    return {"y": y}
```

### `@tool` functions – nodes on the fly

When you call a `@tool` inside a `graph_fn`, the decorator’s proxy detects that a graph builder is active, execute the `@tool`, and return the `NodeHandler`. You can access the output of the tool as regular `@tool`. 

Conceptually:

```python
from aethergraph import tool

@tool(outputs=["total"])
def sum_vec(xs: list[float]) -> dict:
    return {"total": sum(xs)}

@graph_fn(name="tool_usage")
async def tool_usage(xs: list[float], *, context: NodeContext):
    stats = {"n": len(xs)}           # plain Python
    out = sum_vec(xs=xs)             # becomes a node (NodeHandle)
    await context.channel().send_text(
        f"n={stats['n']}, total={out['total']}"
    )
    return {"total": out["total"]}
```

**API contract:**

* Plain callables inside a `graph_fn` execute immediately and are **not** tracked as graph nodes.
* `@tool` calls inside a `graph_fn` become **tracked nodes** with inputs/outputs wired into the `TaskGraph`.
* You can still treat the `@tool` call’s result like a dict in your function body; the NodeHandle provides field‑like accessors that match the tool outputs.

---

## 5. Output Contract (High Level)

The `outputs` list given to `@graph_fn` defines the **expected graph outputs**. After your function body returns, the runtime normalizes the return value and enforces this contract.

Supported return shapes (high‑level):

* A `dict[str, Any]` – keys may map to literals, `NodeHandle`s, or internal `Ref` objects.
* A single `NodeHandle` – its outputs will be exposed as graph outputs.
* A single literal / `Ref` – only valid when exactly one output is declared.

If `outputs` is not `None`:

* The normalized result is restricted to exactly those keys (in order).
* Missing keys cause a `ValueError`.

---

## 6. Registry and `agent` Metadata

When a registry is active (`current_registry() is not None`), `@graph_fn` registers the created `GraphFunction` automatically:

```python
registry.register(
    nspace="graphfn",
    name=name,
    version=version,
    obj=gf,
)
```

If you pass `agent="my_agent"`, the same object is additionally registered as:

```python
registry.register(
    nspace="agent",
    name=agent,
    version=version,
    obj=gf,
)
```

**Current usage:**

* `graphfn` entries: used to discover graphs by name/version and to attach specs/visualizations.
* `agent` entries: reserved for higher‑level agent orchestration (e.g., routing, multi‑agent systems). At present, it is a **metadata hook** only; the core `GraphFunction` API does not change.

---

## 7. Summary

* `@graph_fn` wraps a Python function into a **GraphFunction**: a named, versioned graph entry with optional inputs/outputs.
* The function signature is normal Python; an optional `context` parameter triggers 
**`NodeContext` injection**. 
* Inside the body:

    * Plain Python calls execute inline.
    * `@tool` calls become **nodes on the fly**, tracked in the underlying `TaskGraph`.

* Declared `outputs` define the expected graph outputs and are enforced by the runtime’s normalization logic.

* When a registry is active, each `graph_fn` is registered under `graphfn`, and optionally under `agent` when `agent="..."` is provided.

