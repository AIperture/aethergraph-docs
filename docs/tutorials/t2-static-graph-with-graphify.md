# Tutorial 2: Static Graphs with `@graphify`

`@graphify` turns a plain Python function into a **graph builder**. Instead of executing immediately (like `@graph_fn`), it **builds a deterministic TaskGraph** from `@tool` calls — a DAG you can inspect, persist, and run later.

---

## 🧭 Mental Model

> **`@graph_fn`** → executes now (reactive, context‑rich)
>
> **`@graphify`** → builds first, runs later (deterministic DAG)

* Each `@tool` call becomes a **node** in the DAG.
* Edges are formed by **data flow** and optional ordering via `_after=[…]`.
* You get reproducibility, inspectability, and clean fan‑in/fan‑out.

> **Note:** Access runtime services (`channel`, `llm`, `memory`) **through tools** in static graphs. If you need direct `context.*` calls inline, use `@graph_fn`.

---

## 1) Key Rules (short)

* **Only `@tool` calls are allowed as steps** in a `@graphify` builder. Use plain Python **only to wire values or format the graph** (no side‑effects); such code will **not** appear as nodes.
* **Build ≠ Run.** Calling a `@graphify` function **returns a TaskGraph**. Use a runner to execute it.
* **Async supported.** Tools can be sync or async; the runner provides both sync and async entry points.
* **Resumption requires stable IDs.** Give important nodes a fixed `*_id` and **reuse the same `run_id`** when resuming.
* **Outputs:** Return a **dict of JSON‑serializable values**. Large/binary data → save via `artifacts()` and return a reference. (Full rules live in the API page.)

> **Related:** `@graph_fn` can also emit an **implicit graph** when you call `@tool`s inside it. Use `_after` to enforce ordering there too, and inspect the last run’s captured graph with `graph_fn.last_graph()`.

---

## 2) Shapes (tools & graphify)

### `@tool` shape (suggested)

```python
from aethergraph import tool

@tool(name="load_csv", outputs=["rows"])            # names become handle fields
def load_csv(path: str) -> dict:                      # return dict matching outputs
    # ... load and parse ...
    return {"rows": rows}
```

* Declare `outputs=[...]`. Returned dict **must** contain those keys.
* Use `_after=...` to force ordering when no data edge exists.

### `@graphify` shape (suggested)

```python
from aethergraph import graphify

@graphify(name="etl", inputs=["csv_path"], outputs=["nrows"])  # declarative I/O
def etl(csv_path: str):
    raw = load_csv(path=csv_path)         # node
    # ... add more tool calls ...
    return {"nrows": len(raw.rows)}      # JSON-serializable outputs
```

* Calling `etl()` **builds** a `TaskGraph`; it does not run.
* Run using `run(...)` / `run_async(...)` with `inputs={...}`.

---

## 3) Minimal Example — Build → Run

```python
from aethergraph import graphify, tool
from aethergraph.core.runtime.graph_runner import run  # sync helper

@tool(outputs=["doubled"])  
def double(x: int) -> dict:
    return {"doubled": x * 2}

@tool(outputs=["shifted"])  
def add_ten(x: int) -> dict:
    return {"shifted": x + 10}

@graphify(name="tiny_pipeline", inputs=["x"], outputs=["y"])
def tiny_pipeline(x: int):
    a = double(x=x)                   # node A
    b = add_ten(x=a.doubled)         # node B depends on A via data edge
    return {"y": b.shifted}

# Build (no execution yet)
G = tiny_pipeline()                   # → TaskGraph

# Run (sync)
result = run(G, inputs={"x": 7})
print(result)  # {'y': 24}
```

> Try `max_concurrency=1` vs `>1` in the runner if your tools are async and parallelizable.

---

## 4) Ordering Without Data Edges — `_after`

```python
@tool(outputs=["ok"])  
def fetch() -> dict: ...

@tool(outputs=["done"])
def train() -> dict: ...

@graphify(name="seq", inputs=[], outputs=["done"])
def seq():
    a = fetch()
    b = train(_after=a)               # force run-after without wiring data
    return {"done": b.done}
```

* Use a single node or a list `_after=[a, b]`.

---

## 5) Resume a Run — Stable `_id` + `run_id`

Resumption lets you continue a partially-completed graph **without redoing finished nodes**. This is useful for flaky I/O or long pipelines.

* Assign deterministic IDs to nodes with `_id="..."` in your tools.
* Reuse the same `run_id` when invoking the runner again.
* **Indefinite waits** (e.g., human input) are supported via dedicated wait tools and are covered in the **Channels & Wait Models** tutorial—this section uses a **non‑channel** example.

```python
from aethergraph import graphify, tool
from aethergraph.core.runtime.graph_runner import run_async
import random

@tool(outputs=["ok"])  
def prepare() -> dict:
    # Pretend to set up workspace/artifacts
    return {"ok": True}

@tool(outputs=["value"])  
def flaky_compute(x: int) -> dict:
    # Simulate a transient failure half the time
    if random.random() < 0.5:
        raise RuntimeError("transient error — try resuming")
    return {"value": x * 2}

@tool(outputs=["ok"])  
def finalize(v: int) -> dict:
    # Commit final result (e.g., write an artifact)
    return {"ok": True}

@graphify(name="resumable_pipeline", inputs=["x"], outputs=["y"]) 
def resumable_pipeline(x: int):
    s1 = prepare(_id="prepare_1")
    s2 = flaky_compute(x=x, _after=s1, _id="flaky_2")  # may fail on first run
    s3 = finalize(v=s2.value, _after=s2, _id="finalize_3")
    return {"y": s2.value}

# First run may fail while computing 'flaky_2'...
# await run_async(resumable_pipeline(), inputs={"x": 21}, run_id="run-abc")

# Re-run with the SAME run_id to resume from the failed node (prepare_1 is skipped):
# await run_async(resumable_pipeline(), inputs={"x": 21}, run_id="run-abc")
```

> Keep `_id`s stable to allow the engine to match nodes. If a node fails or is interrupted, resuming with the same `run_id` will continue from the last successful checkpoint.

> Use json-serializable output in `@tool` so that Aethergraph can reload previous outputs; otherwise resumption may fail.

---

## 6) Inspect Before/After Running

Once you have a `TaskGraph` (e.g., `G = tiny_pipeline()`), you can:

```python
print(G.pretty())           # readable node table
print(G.ascii_overview())   # compact topology
print(G.topological_order())

# Graph metadata
sig  = tiny_pipeline.io()   # declared inputs/outputs
spec = tiny_pipeline.spec() # full GraphSpec (nodes, edges, metadata)

# Export (if enabled)
dot = G.to_dot()            # Graphviz DOT text
# G.visualize()             # render to image if your env supports it
```

---

## 7) Practical Tips

* **Keep nodes small and typed**: expose clear outputs (e.g., `outputs=["clean"]`).
* **Use JSON‑serializable returns**; store big/binary as artifacts.
* **Prefer `_after` for control edges** instead of fake data plumb‑through.
* **No nested static graphs** (don’t call one `@graphify` from another). Use tools or run graphs separately.
* **Async tools + `max_concurrency`** unlock parallel speedups.

---

## 8) Summary

* `@graphify` **materializes** a static DAG from `@tool` calls.
* **Build** with the function call; **run** with the runner (sync or async).
* For resumption, use **stable `_id`** per node and **replay with the same `run_id`**.
* Inspect graphs via `pretty()`, `ascii_overview()`, `.io()`, `.spec()`, and `to_dot()`.

> Use `@graphify` for pipelines and reproducible experiments; stick with `@graph_fn` for interactive, context‑heavy agents.
