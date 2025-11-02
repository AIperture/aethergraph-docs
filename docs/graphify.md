# AetherGraph — `@graphify` (Builder Decorator)

`@graphify` lets you write a plain Python function whose body *builds* a `TaskGraph` using tool calls.
Instead of executing immediately, the function becomes a **graph factory**: call `.build()` to get a concrete graph,
`.spec()` to inspect, and `.io()` to see its input/output signature.

---

## Why `graphify` vs `graph_fn`?

| Aspect            | `graph_fn`                                 | `graphify`                                          |
|-------------------|--------------------------------------------|-----------------------------------------------------|
| Primary purpose   | **Execute now** as a single graph node     | **Build a graph** (explicit fan‑in/fan‑out wiring)  |
| Return at call    | Dict of outputs (or awaitable)             | A **builder** you later `.build()` into a graph     |
| Control‑flow      | Pythonic, implicit graph behind the scenes | Explicit nodes & edges via tool calls (`NodeHandle`) |
| Best for          | Orchestration + `context.*` services       | Pipelines, DAGs, reusable subgraphs                 |

Use **`graphify`** when you want:

- Multiple tool calls as separate nodes
- Explicit dependencies (`_after`) and fan‑in/fan‑out
- To inspect/serialize the graph spec for registry/UI
- To reuse the same pipeline with different inputs

Use **`graph_fn`** when you want:

- A simple function that runs immediately and returns values
- Access to `context.channel()/memory()/artifacts()/llm()` services
- Minimal ceremony (one decorator and go)

---

## Decorator Signature

```python
from aethergraph import graphify

@graphify(*, name="default_graph", inputs=(), outputs=None, version="0.1.0", agent: str | None = None)
def build_fn(...):
    ...  # tool calls returning NodeHandles
    return {"y": handle.y}
```

**Parameters**

- **name** (*str*) — Graph identifier.
- **inputs** (*Iterable[str] or dict*) — Declare required/optional inputs.  
  - If `list/tuple`: treated as **required** input names.  
  - If `dict`: `{required_name: ..., ...}` for optional mapping; builder will declare required/optional accordingly.
- **outputs** (*list[str] \| None*) — Names to expose. If you return a single literal, you must declare exactly one.
- **version** (*str*) — Semantic version for registry/spec metadata.
- **agent** (*str \| None*) — Optionally register the built graph under `agent` namespace.

**Return value**

The decorated symbol becomes a **builder function** with helpers:

  - `.build() -> TaskGraph`
  - `.spec() -> GraphSpec`
  - `.io() -> IOSignature`
  - Attributes: `.graph_name`, `.version`

---

## Writing a `@graphify` Body

Inside the function:

1. **Use `arg("name")`** to reference declared inputs.
2. **Call `@tool` functions** (or `call_tool("pkg.mod:fn", ...)`) — each returns a `NodeHandle` in build mode.
3. **Return outputs** as:
   - A dict mapping names → `NodeHandle` outputs or refs/literals, or
   - A single `NodeHandle` (its outputs will be exposed), or
   - A single literal *only if* `outputs` has length 1.

```python
from aethergraph import graphify, tool
from aethergraph.graph import arg

@tool(outputs=["embedded"])
def embed(text: str): ...

@tool(outputs=["score"])
def score(vec, query_vec): ...

@graphify(name="ranker", inputs=["texts","query"], outputs=["scores"])
def ranker(texts, query):
    q = embed(text=query)
    # fan‑out: call `embed` for each text
    vecs = [embed(text=t) for t in texts]  # list[NodeHandle]
    # fan‑in: score each against query vec
    scs = [score(vec=v.embedded, query_vec=q.embedded) for v in vecs]
    return {"scores": [s.score for s in scs]}

G = ranker.build()
```

### Control Dependencies without Data Edges

Use `_after` when you must enforce order but don’t pass outputs:
```python
@tool(outputs=["ok"])
def fetch(): return {"ok": True}

@tool(outputs=["done"])
def train(): return {"done": True}

@graphify(name="seq", inputs=[], outputs=["done"])
def seq():
    a = fetch()
    b = train(_after=a)   # run b after a
    return {"done": b.done}
```

---

## Registration

If a registry is active, `@graphify` registers the **built graph** under `nspace="graph"` with `name`/`version` so it can be listed or launched elsewhere. You can also register it as an `agent` via the `agent=` parameter.

---

## Example: End‑to‑End Pipeline

```python
from aethergraph import tool, graphify
from aethergraph.graph import arg

@tool(outputs=["rows"])
def load_csv(path: str): ...

@tool(outputs=["clean"])
def clean(rows): ...

@tool(outputs=["model"])
def train(data): ...

@tool(outputs=["uri"])
def report(model): ...

@graphify(name="etl_train_report", inputs=["csv_path"], outputs=["uri"])
def etl_train_report(csv_path):
    raw  = load_csv(path=arg("csv_path"))
    tidy = clean(rows=raw.rows)
    mod  = train(data=tidy.clean)
    rep  = report(model=mod.model)
    return {"uri": rep.uri}

G = etl_train_report.build()
```

---

## Using `@tool` Inside `@graph_fn` (Brief)

While `@graph_fn` is for immediate execution, you *can* drop explicit tool nodes inside a `graph_fn` when you want finer‑grained tracing or parallelism:

```python
from aethergraph import graph_fn, tool

@tool(outputs=["y"])
def square(x: int): return {"y": x*x}

@graph_fn(name="mix")
async def mix(x: int, *, context):
    h = square(x=x)                 # schedules a tool node in the implicit graph
    await context.channel().send_text("running square…")
    return {"y": h.y}               # exposes tool output as graph_fn output
```

> Prefer `@graphify` for full pipeline construction; use `@graph_fn` when you want to orchestrate services (`context.*`) and run quickly.