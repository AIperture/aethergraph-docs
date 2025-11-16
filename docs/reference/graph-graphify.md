# `graphify` – Static Graph Builder Decorator

`graphify` turns a plain Python function into a **static graph factory**: a callable that, when invoked, builds and returns a `TaskGraph` using the **graph builder** context.

Key ideas:

* The decorated function is evaluated **at build time**, not at run time.
* Inputs are injected as **graph refs** (via `arg("<name>")`), not real values.
* Calls to `@tool` inside the function body become **tool nodes** in the `TaskGraph`.
* The function’s return value defines which refs / literals are **exposed as graph outputs**.
* There is **no `NodeContext` injection** in `graphify`; if you need context services, put that logic **inside a `@tool`** and call the tool from the graphified function.

This section focuses on the **API and contracts** of `graphify`. Details of `TaskGraph` structure and the runner live on dedicated pages.

---

## 1. Decorator Signature

```python
def graphify(
    *,
    name: str,
    outputs: list[str],
    inputs = (),
    version: str = "0.1.0",
    agent: str | None = None,
):
    ...
```

### Parameters

| Parameter | Type                                    | Required?                      | Description                                                                                                                 |
| --------- | --------------------------------------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `name`    | `str`                                   | Yes  | Graph ID / name for the built `TaskGraph`. Used in specs, logs, and registry.                                               |
| `inputs`  | `Iterable[str]` **or** `dict[str, Any]` | No (default `()` )             | Graph **input declaration**. Can be a list/tuple of required input names, or a dict of optional inputs with default values. |
| `outputs` | `list[str] \| None`                     | Yes                             |  List of **declared graph output names**.                     |
| `version` | `str`                                   | No                             | Version tag for this graph. Included in registry entries and provenance.                                                    |
| `agent`   | `str \| None`                           | No                             | If provided, also registers this graph under the `agent` namespace in the registry.                                         |

**Inputs semantics**

* If `inputs` is a **sequence** (e.g. `("x", "y")`):

    * All listed names are treated as **required** inputs.

* If `inputs` is a **dict** (e.g. `{ "x": 0.0, "y": 1.0 }`):

    * All keys are treated as **optional** inputs, and the dict values can be used as default metadata.

The function parameters determine which inputs are injected (see below); `inputs` defines the **graph-level** input signature (required/optional) via `g.declare_inputs(...)`.

---

## 2. What `graphify` Returns

Applying `graphify` to a function wraps it into a **builder function**:

```python
@graphify(name="my_graph", inputs=["x"], outputs=["y"])
def my_graph(x):
    ...
```

The decorated object (e.g. `my_graph`) is **not** the original function anymore. Instead, it is a zero-argument callable that builds a new `TaskGraph` each time you call it:

```python
g = my_graph()     # builds and returns a TaskGraph
```

For convenience, the builder also exposes a few attributes:

| Attribute             | Type                  | Meaning                                                          |
| --------------------- | --------------------- | ---------------------------------------------------------------- |
| `my_graph()`          | `() -> TaskGraph`     | Calling the object builds a fresh `TaskGraph`.                   |
| `my_graph.build`      | `() -> TaskGraph`     | Alias to the same build function.                                |
| `my_graph.graph_name` | `str`                 | Graph name used when constructing the `TaskGraph` (from `name`). |
| `my_graph.version`    | `str`                 | Version tag passed via `version`.                                |
| `my_graph.spec()`     | `() -> TaskGraphSpec` | Builds a graph and returns **only the spec** (`g.spec`).         |
| `my_graph.io()`       | `() -> dict`          | Builds a graph and returns `g.io_signature()`.                   |

> In other words: `graphify` gives you a **graph factory** with lightweight helpers to inspect the spec and I/O signature. The original function body is used only to describe how the graph should be built.

---

## 3. Function Shape & Input Injection

The function you decorate with `graphify` is written like a regular synchronous function. Always return a **dictionary of outputs** specified in the decorator. 

```python
from aethergraph import graphify

@graphify(name="sum_graph", inputs=["xs"], outputs=["total"])
def sum_graph(xs):
    # body uses NodeHandles / refs
    ...
    return {"total": some_handle}
```

### Parameter matching

**Contract:**

* Only parameters whose name appears in `inputs` are **injected**.
* Injected values are **`arg("<name>")` refs**, not concrete Python values.
* Extra parameters in the function signature that are not listed in `inputs` are **not** passed by `graphify`.
* There is **no `context` parameter** here – if you need `NodeContext` services (channel, memory, artifacts, logger, etc.), move that logic into a `@tool` and call the tool from the graphified function.

This means:

* Use `inputs` to define which parameters are part of the **graph I/O**.
* Inside the function body, treat injected parameters as **graph references** – suitable for passing into `@tool` calls and other graph APIs.

---

## 4. Tools vs Plain Code Inside a `graphify` Body

When the builder runs your function inside `with graph(name=...) as g`, the **graph builder** is active (`current_builder()` is not `None`). This affects how `@tool` calls behave.

### Plain Python code

Non-tool code runs normally and is not recorded as a node:

```python
def local_scale(xs, factor=2):
    return [x * factor for x in xs]

@graphify(name="scaled_sum", inputs=["xs"], outputs=["total"])
def scaled_sum(xs):
    ys = local_scale(xs)   # plain Python; not a node
    ...
```

### `@tool` calls → nodes

When you call a `@tool` inside a `graphify` body, the `tool` proxy uses `call_tool(...)`:

* It detects the active `GraphBuilder` via `current_builder()`.
* It creates a **tool node** via `builder.add_tool_node(...)`.
* It returns a **NodeHandle** (static build-mode handle) with `node_id` and `output_keys`.

Example shape:

```python
from aethergraph import tool

@tool(outputs=["total"])
def sum_vec(xs: list[float]) -> dict:
    return {"total": sum(xs)}

@graphify(name="sum_graph", inputs=["xs"], outputs=["total"])
def sum_graph(xs):
    node = sum_vec(xs=xs)     # ← NodeHandle, not a concrete result
    return {"total": node}   # expose this node’s outputs
```

**Contract:**

* Plain Python functions: execute at build time, do not affect the graph structure (unless they call graph APIs themselves).
* `@tool` calls: always become **nodes** in the resulting `TaskGraph` when used inside a `graphify` body.

### Control kwargs for node ordering & IDs

Calling tools inside a `@graphify` also supports a small set of **control-plane** keyword arguments that do not become data inputs but affect node metadata and ordering. 

You can pass them when calling a `@tool` inside a `graphify` body:

* `_after`: one node or a list of nodes/IDs this node should run **after**.
* `_name`: human-readable display name for the node (stored in metadata as `display_name`).
* `_alias`: short, unique alias for the node; can be used for later lookup via `find_by_alias`.
* `_id`: hard override for the underlying `node_id` (must be unique within the graph).
* `_labels`: one or more string labels (as a str or list[str]) to tag the node; used for later lookup and grouping via `find_by_label`.

Example:

```python
n1 = sum_vec(xs=xs, _alias="sum1")
n2 = sum_vec(xs=n1.total, _after=[n1], _name="sum_again", _id="sum_again_node")
```

These control fields are **optional** and are taken out of `kwargs` before computing tool inputs, so they never appear as data edges.


## 5. Registry

At decoration time, `graphify` checks the current registry:

**Behavior:**

* If a registry is active:

    * A `TaskGraph` instance is registered under `nspace="graph"` with the given `name` and `version`.
    * If `agent` is provided, another `TaskGraph` instance is registered under `nspace="agent"` with that name.

* If no registry is active:

    * The builder still works; registration is simply skipped.

> Current implementation registers a **concrete `TaskGraph` instance**, not the factory itself.

---

## 6. Summary

* `graphify` decorates a synchronous function and turns it into a **TaskGraph factory**: calling the decorated object builds a fresh `TaskGraph`.
* `inputs` defines graph-level input names (required vs optional) and determines which parameters are injected as `arg("<name>")` refs.
* Inside the body:

    * Plain Python code runs at build time and is not recorded as nodes.
    * `@tool` calls become **tool nodes** via the active `GraphBuilder` (`current_builder()`), with optional control-plane kwargs (`_after`, `_name`, `_alias`, `_id`) for ordering and IDs.

* There is **no `NodeContext`** in `graphify`; use a `@tool` when you need context services and call that tool from the graphified function.
* When a registry is active, `graphify` registers a built `TaskGraph` under `graph` and optionally under `agent` when `agent="..."` is provided.
* When executed, `graphify` graphs automatically take advantage of **concurrent execution** under a configurable concurrency cap for nodes that are ready at the same level.
