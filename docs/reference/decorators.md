# Decorator API — `@graph_fn`, `@graphify`, `@tool`

A single reference page for the three core decorators you’ll use to build with AetherGraph.

---

## Quick chooser

| Use this when…                                                                                                      | Pick            | Why                                                                                          |
| ------------------------------------------------------------------------------------------------------------------- | --------------- | -------------------------------------------------------------------------------------------- |
| You want the quickest way to make a Python function runnable as a graph entrypoint and get a `context` for services | **`@graph_fn`** | Small, ergonomic, ideal for tutorials, notebooks, single‑entry tools/agents                  |
| You need to expose reusable steps with typed I/O that can run **standalone** *or* as **graph nodes**                | **`@tool`**     | Dual‑mode decorator; gives you fine control of inputs/outputs; portable and composable       |
| Your function body is mostly **tool wiring** (fan‑in/fan‑out) and you want a static graph spec from Python syntax   | **`@graphify`** | Author graphs declaratively; returns a `TaskGraph` factory; great for orchestration patterns |

---

## `@graph_fn`

Wrap a normal async function into a runnable graph with optional `context` injection.

### Signature

```
@graph_fn(name: str, *, inputs: list[str] | None = None, outputs: list[str] | None = None, version: str = "0.1.0", agent: str | None = None)
async def my_fn(..., *, context: NodeContext): ...
```

### Description

* Builds a fresh `TaskGraph` under the hood and executes it immediately.
* If your function signature includes `context: NodeContext`, AetherGraph injects a `NodeContext` so you can call `context.channel()`, `context.memory()`, `context.artifacts()`, `context.llm()`, etc.
* Ideal for single‑file demos, CLI/notebook usage, and simple agents.

### Parameters

* **name** (*str, required*) — Graph ID and human‑readable name.
* **inputs** (*list[str], optional*) — Declared input keys. Purely declarative; your function still gets normal Python args.
* **outputs** (*list[str], optional*) — Declared output keys. If you return a single literal, declare exactly one.
* **version** (*str, optional*) — Semantic version for registry.
* **agent** (*str, optional*) — If provided, registers this graph function as an agent under the given name.

### Returns

* The decorator returns a **`GraphFunction`** object. Calling/awaiting it executes the graph and returns a **`dict`** of outputs keyed by `outputs`.

### Minimal example

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="hello.world", inputs=["name"], outputs=["greeting"], version="0.1.0")
async def hello_world(name: str, *, context: NodeContext):
    await context.channel().send_text(f"👋 Hello {name}")
    return {"greeting": f"Hello, {name}!"}

# Run (async)
res = await hello_world(name="Aether")
print(res["greeting"])  # → "Hello, Aether!"
```

### Tips

* Return a `dict` where keys match `outputs`. If you return a single literal, declare one output.
* You can call `@tool` functions **inside** a `@graph_fn` (they’ll run immediately, not build nodes). Use this for small, fast helper steps.
* For complex orchestration (fan‑in/fan‑out), prefer `@graphify` so `@tool` calls become nodes.

---

## `@tool`

Dual‑mode decorator for reusable steps with explicit inputs/outputs.

### Signature

```
@tool(outputs: list[str], *, inputs: list[str] | None = None, name: str | None = None, version: str = "0.1.0")
def/async def my_tool(...): ...
```

### Description

* **Immediate mode (no builder/interpreter active):** calling the function executes it **now** and returns a `dict` of outputs.
* **Graph mode (inside a `graph(...)` / `@graphify` body or during `@graph_fn` build):** calling the proxy **adds a node** to the current graph and returns a `NodeHandle` with typed outputs.
* Registers the underlying implementation in the runtime registry for portability.

### Parameters

* **outputs** (*list[str], required*) — Names of output values (e.g., `["result"]`, `["image", "stats"]`).
* **inputs** (*list[str], optional*) — Input names (auto‑inferred from signature if omitted).
* **name** (*str, optional*) — Registry/display name; defaults to function name.
* **version** (*str, optional*) — Semantic version for registry.

### Returns

* In immediate mode: **`dict`** of outputs.
* In graph mode: **`NodeHandle`** with `.out_key` attributes (e.g., `node.result`).

### Example — reusable step

```python
from aethergraph import tool

@tool(outputs=["sum", "count"])
def aggregate(xs: list[int]):
    return {"sum": sum(xs), "count": len(xs)}

# Immediate mode
print(aggregate([1,2,3]))  # {"sum": 6, "count": 3}
```

### Example — using `@tool` inside `@graph_fn` (immediate execution)

```python
from aethergraph import graph_fn, tool, NodeContext

@tool(outputs=["sum"])  
def add(x: int, y: int):
    return {"sum": x + y}

@graph_fn(name="calc.pipeline", inputs=["a","b"], outputs=["total"])
async def calc(a: int, b: int, *, context: NodeContext):
    out = add(a, b)                 # immediate mode here
    await context.channel().send_text(f"sum = {out['sum']}")
    return {"total": out["sum"]}
```

### Tips

* Use `@tool` to make steps portable and inspectable (typed I/O makes graphs predictable).
* In **`@graph_fn`** the `@tool` call executes immediately; in **`@graphify`** the same call becomes a graph node.
* Control‑flow knobs like `_after`, `_id`, `_alias` apply **only in graph‑building contexts** (e.g., `@graphify`), not in `@graph_fn` bodies.

---

## `@graphify`

Author a **static TaskGraph** by writing normal Python that *calls `@tool`s*. The function body executes during build to register nodes and edges; returned node handles/literals define graph outputs.

### Signature

```
@graphify(*, name: str = "default_graph", inputs: Iterable[str] | dict = (), outputs: list[str] | None = None, version: str = "0.1.0", agent: str | None = None)
def my_graph(...):
    ...  # body calls @tool proxies (graph mode)
    return {...}  # NodeHandle(s) and/or literal refs
```

### Description

* The decorated function becomes a **factory**: calling `my_graph.build()` returns a `TaskGraph` spec.
* When the body runs under the builder, calls to `@tool` proxies **add nodes** to the graph and return `NodeHandle`s.
* Perfect for **fan‑out** (parallel branches) and **fan‑in** (join/aggregate) patterns.

### Parameters

* **name** (*str*) — Graph identifier.
* **inputs** (*iterable[str]* or *dict*) — Required/optional input names. If dict, keys are optional names with defaults in the body.
* **outputs** (*list[str], optional*) — Names of exposed boundary outputs. If body returns a single literal, declare exactly one.
* **version** (*str*) — Semantic version.
* **agent** (*str, optional*) — Register this graph as an agent (factory registered).

### Returns

* The decorator returns a **builder function** with:

  * `.build() -> TaskGraph`
  * `.spec() -> TaskGraphSpec`
  * `.io() -> IO signature`

### Example — fan‑out + fan‑in

```python
from aethergraph import graphify, tool

@tool(outputs=["y"])
def f(x: int):
    return {"y": x * x}

@tool(outputs=["z"])
def g(x: int):
    return {"z": x + 1}

@tool(outputs=["sum"])  
def add(a: int, b: int):
    return {"sum": a + b}

@graphify(name="fan_in_out", inputs=["x"], outputs=["total"]) 
def pipe(x):
    a = f(x=x)          # node A (graph mode)  ┐
    b = g(x=x)          # node B (graph mode)  ┘  ← fan‑out
    c = add(a=a.y, b=b.z)   # node C depends on A,B ← fan‑in
    return {"total": c.sum}

G = pipe.build()
```

### Example — ordering with `_after` and aliasing

```python
@tool(outputs=["out"]) 
def step(name: str):
    return {"out": name}

@graphify(name="ordered", inputs=[]) 
def ordered():
    a = step(name="A", _alias="first")
    b = step(name="B", _after=a)
    c = step(name="C", _after=[a, b], _id="third")
    return {"final": c.out}

G = ordered.build()
```

### Using `@tool` inside `@graph_fn` vs `@graphify`

* **Inside `@graph_fn`**: `@tool` calls **execute immediately** (no `_after`/alias). Great for quick helpers.
* **Inside `@graphify`**: `@tool` calls **define nodes** (support `_after`, `_alias`, `_id`, `_labels`). Ideal for orchestration.

---

## Interop & best practices

1. **Start simple with `@graph_fn`** — it’s the easiest way to get `context` and ship a working demo.
2. **Extract reusable steps with `@tool`** — typed I/O makes debugging, tracing, and promotion to graphs trivial.
3. **Promote to `@graphify`** when you need:

   * Parallel branches (fan‑out), joins (fan‑in)
   * Explicit ordering with `_after`
   * Reuse via `NodeHandle` composition and aliasing
4. **Context access**:

   * `@graph_fn` gives you `context: NodeContext` directly.
   * In `@graphify`, nodes don’t get `context`; tools *run with context at execution time* when the graph is interpreted. Use `@tool` implementations to call `context.*`.
5. **Outputs discipline** — keep outputs small and typed (e.g., `{ "image": ref, "metrics": {…} }`).
6. **Registry** — all three decorators register artifacts (graph fn as runnable, tool impls, graph factories) so you can call by name later.

---

## See also

* **Quick Start**: install, start server, first `@graph_fn`.
* **Contex
