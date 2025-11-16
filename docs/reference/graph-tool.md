# `@tool` – Dual‑mode Tool Decorator

The `@tool` decorator turns a plain Python callable into an AetherGraph **tool**:

* **Immediate mode** (no active graph): calling the decorated function executes it directly and returns a **dict of outputs** (or an awaitable for async tools).
* **Graph mode** (inside `@graph_fn` / `@graphify`): calling the decorated function **builds a node** and returns a **`NodeHandle`**; nothing is executed yet.
* **Registry integration**: when a registry is active, the implementation is automatically registered under the `tool` namespace.
* **Context injection**: if the tool signature includes a `context` parameter, a **`NodeContext`** is injected automatically at run time when the tool runs as a node in a graph.

---

## Signature

```python
@tool(
    outputs: list[str],
    inputs: list[str] | None = None,
    *,
    name: str | None = None,
    version: str = "0.1.0",
)
```

### Required vs optional

| Parameter | Type                         | Required? | Description                                                                                                                          |
| --------- | ---------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `outputs` | `list[str]`                  | **Yes**   | Declares the **named outputs** produced by the tool. Every call must return a dict containing exactly these keys.                    |
| `inputs`  | `list[str] \| None`          | No        | Optional **explicit input names**. If `None`, they are inferred from the implementation’s signature (excluding `*args`, `**kwargs`). |
| `name`    | `str \| None` (keyword‑only) | No        | Optional **registry / UI name**. Defaults to the underlying implementation’s `__name__`.                                             |
| `version` | `str` (keyword‑only)         | No        | Semantic version used for registry and provenance. Defaults to `"0.1.0"`.                                                            |

**Notes**

* `outputs` is **always required** and defines the contract enforced at runtime.
* `inputs` is usually **optional** – in most cases, you can let AetherGraph infer it from the function’s parameters.
* `name` and `version` matter when you later want to **look up** tools in a registry or inspect runs.

---

## Behavior Overview

* **Sync vs async**

  * If the implementation is synchronous, the decorated function returns a **dict** in immediate mode.
  * If the implementation is async, the decorated function returns an **awaitable** in immediate mode.

* **Graph vs immediate mode**

  * When a graph builder is active (`current_builder() is not None`), calling the tool returns a **`NodeHandle`** (graph node), not data.
  * When no builder is active, calling the tool executes the implementation and returns results.

* **Context injection**

  * If the tool’s signature includes a parameter named `context`, it is treated as a **reserved injectable** rather than a normal data input.
  * You **do not** list `"context"` in the `inputs` list; `inputs` is for data‑flow arguments only.
  * When the tool runs as a node in a graph (via `@graph_fn` or `graphify`), AetherGraph automatically injects a `NodeContext` instance for that node. Callers do not pass it manually when running the graph.

---

## Runtime Contracts

The decorator enforces a **strict I/O contract** for every tool call:

* The implementation must return either:

  * a `dict` with exactly the declared `outputs` keys, or
  * a value that `_normalize_result` can convert into such a dict.

* `_check_contract(outputs, out, impl)` validates that:

  * all `outputs` keys are present,
  * no unexpected keys are produced (where applicable).

On violation, the runtime raises a clear error pointing at the original implementation.

---

## Context‑aware Tools

To use runtime services inside a tool (channel, memory, artifacts, logger, etc.), add a `context` parameter:

```python
from aethergraph import tool, NodeContext

@tool(outputs=["y"], inputs=["x"])
async def double_with_log(x: int, *, context: NodeContext) -> dict:
    # `context` is injected automatically when this tool runs as a graph node
    context.logger().info("doubling", extra={"x": x})
    return {"y": x * 2}
```

**Contracts:**

* `context` is not part of the data‑flow; it never becomes an edge in the graph.
* In graph mode, callers simply write `double_with_log(x=42)` in a `@graph_fn` / `graphify` body; the runner injects `NodeContext` when executing the node.
* In immediate mode (outside any graph), you can optionally pass a `context` argument manually if you want to test the tool with a synthetic context, but typical usage is inside graphs.

---

## Usage Patterns

Below are common ways to define and call tools. These examples focus on **shape and contracts**; see the main Graph docs for deeper patterns.

<details markdown="1">
<summary>1. Simple synchronous tool</summary>

```python
from aethergraph import tool

@tool(outputs=["y"])
def double(x: int) -> dict:
    return {"y": x * 2}

# Immediate mode (no active graph)
result = double(x=21)
assert result == {"y": 42}
```

**Key points**

* `outputs=["y"]` is **required**.
* `inputs` is omitted → inferred as `["x"]` from the function signature.
* In immediate mode, `double(...)` runs immediately and returns a dict.

</details>

<details markdown="1">
<summary>2. Async tool</summary>

```python
from aethergraph import tool

@tool(outputs=["text"])
async def fetch_text(url: str) -> dict:
    data = await some_async_http_get(url)
    return {"text": data}

# Immediate mode
result = await fetch_text(url="https://example.com")
print(result["text"])
```

**Key points**

* Implementation is async → in immediate mode, calling `fetch_text(...)` returns an **awaitable**.
* `inputs` again inferred from the signature (`["url"]`).

</details>

<details markdown="1">
<summary>3. Explicit inputs (with non‑data params)</summary>

```python
from aethergraph import tool, NodeContext

@tool(outputs=["out"], inputs=["a", "b"])
async def add(a: int, b: int = 0, *, scale: int = 1, context: NodeContext | None = None) -> dict:
    # `a`, `b` are data inputs; `scale` and `context` are not graph edges
    if context is not None:
        context.logger().info("adding", extra={"a": a, "b": b, "scale": scale})
    return {"out": (a + b) * scale}
```

**Key points**

* `inputs=["a", "b"]` means **only** `a` and `b` are considered data‑inputs from upstream nodes.
* `scale` and `context` are **non‑data** parameters:

  * `context` is a reserved injectable (runtime will supply it in graph mode).
  * `scale` can be passed as a literal or configured inside the graph; it does not appear as an edge unless you model it explicitly.

</details>

<details markdown="1">
<summary>4. Graph mode – building nodes</summary>

```python
from aethergraph import graph_fn, tool, NodeContext

@tool(outputs=["y"])
def double(x: int):
    return {"y": x * 2}

@tool(outputs=["y"], inputs=["x"])
async def double_with_log(x: int, *, context: NodeContext) -> dict:
    context.logger().info("doubling", extra={"x": x})
    return {"y": x * 2}

@graph_fn(name="pipeline", outputs=["z"])
async def pipeline(*, context: NodeContext):
    # Inside a graph_fn, calling tools builds nodes
    n1 = double(x=21)                 # NodeHandle, not the numeric 42
    n2 = double_with_log(x=n1.y)      # NodeHandle with NodeContext injection at run time
    return {"z": n2.y}
```

**Key points**

* Inside `@graph_fn`, both `double(...)` and `double_with_log(...)` **do not run** immediately.
* Instead, `NodeHandle`s are returned and the builder records tool nodes and their dependencies.
* When the graph is executed:

  * The runtime calls the underlying implementation with concrete values for data inputs.
  * If a `context` parameter is present, a `NodeContext` instance is injected automatically for that node.

</details>

---

## Registry Behavior (Advanced)

When a registry is active (`current_registry() is not None`), the decorator automatically registers the underlying implementation:

```python
registry.register(
    nspace="tool",
    name=name or impl.__name__,
    version=version,
    obj=impl,
)
```

This enables:

* **Discovery** – listing available tools by `(name, version)`.
* **Provenance** – runs can record which version of which tool was used.
* **Hot reload / development** – registries can swap implementations without changing graph code.

If no registry is active, the decorator still works normally; registration is simply skipped.

---

## Summary

* Use `@tool(outputs=[...])` on any function to make it part of the graph runtime.
* **Required:** `outputs` – define the contract.
* **Optional:** `inputs`, `name`, `version` – control graph wiring and registry metadata.
* Immediate calls return concrete data (or awaitables); calls inside graphs create nodes and wire dependencies.
* To use runtime services inside a tool, add a `context` parameter:

  * It is automatically injected as `NodeContext` when the tool runs as a node in a graph.
  * Callers **never** pass `context` manually when running `@graph_fn` or `graphify` graphs; the runner does it for them.
