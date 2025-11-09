# Static Graphs with `@graphify`

`@graphify` transforms a plain Python function into a **graph builder**. Instead of running immediately (like `@graph_fn`), it **constructs a TaskGraph** from `@tool` calls — a reusable, explicit DAG that you can run later.

**In short:**
> * `@graph_fn` → executes now (reactive, dynamic)
> * `@graphify` → builds first, runs later (deterministic DAG)

---

## 1. What Is a Static Graph?

A **static graph** is a declarative DAG of tool nodes and dependencies. Each node is a `@tool` call; edges represent data flow or forced ordering. You build it once, then you can inspect, persist, visualize, and run it repeatedly.

**Why static?** Repeatability, inspectability, and clear fan‑in/fan‑out. Static graphs shine for pipelines and reproducible experiments where determinism and analysis matter.

---

## 2. `@graphify` vs `@graph_fn`

| Aspect         | `@graph_fn` (Reactive)                             | `@graphify` (Static)                                                       |
| -------------- | -------------------------------------------------- | -------------------------------------------------------------------------- |
| Execution      | Runs immediately when called                       | Builds a DAG first; run later                                              |
| Composition    | Mix plain Python + `@tool` (implicit nodes)        | Only `@tool` nodes are valid steps                                         |
| Context usage  | Rich `context.*` available inline                  | Need to wrap `context.*` in a tool to access it |
| Inspectability | Inspect implicit graph via `graph_fn.last_graph()` | Full spec via `.io()`, `.spec()`, `TaskGraph.pretty()`                     |
| Best for       | Interactive agents, quick iteration                | Pipelines, reproducible runs, analytics                                    |

> **Note:** Nested static‑graph calls are **not supported** at the moment (no calling one `@graphify` from another as a node). Compose via tools or run graphs separately.

---

## 3. Define and Build a Graph

```python
from aethergraph import graphify, tool

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
    raw  = load_csv(path=csv_path)
    tidy = clean(rows=raw.rows)
    mod  = train(data=tidy.clean)
    rep  = report(model=mod.model)
    return {"uri": rep.uri}

G = etl_train_report.build()     # → TaskGraph
```

### Control ordering without data edges

Use `_after` to enforce sequence when there’s no data dependency:

```python
@tool(outputs=["ok"])    
def fetch(): ...

@tool(outputs=["done"])  
def train(): ...

@graphify(name="seq", inputs=[], outputs=["done"]) 
def seq():
    a = fetch()
    b = train(_after=a)        # run `train` after `fetch`
    return {"done": b.done}
```

### Referencing Tool Outputs (dot vs. key) 

Each `@tool` must declare its outputs. AetherGraph wraps the call in a handle whose fields mirror those names, so you can access them either as **attributes** or **dict keys** — both are equivalent.

```python
@tool(outputs=["rows"])
def load_csv(path: str):
# must return a dict matching declared outputs
return {"rows": parse_csv(path)}


@tool(outputs=["clean"])
def clean(rows):
return {"clean": tidy(rows)}


@graphify(name="etl", inputs=["csv_path"], outputs=["clean"])
def etl(csv_path):
raw = load_csv(path=csv_path)
# Access either way; these are equivalent
tidy1 = clean(rows=raw.rows) # dot access
tidy2 = clean(rows=raw["rows"]) # key access
return {"clean": tidy1.clean}
```

> Consistency matters: declared output names (e.g.,`outputs=["rows"]`) must match the keys you return from the tool (e.g., `{"rows": ...}`). Mismatches raise clear build/runtime errors.

**Multiple outputs**
```python 
@tool(outputs=["mean", "std"])
def stats(xs: list[float]):
return {"mean": avg(xs), "std": stdev(xs)}


@graphify(name="use_stats", inputs=["xs"], outputs=["m"])
def use_stats(xs):
s = stats(xs=xs)
return {"m": s.mean} # or s["mean"]
```
> Think of tool calls as **typed nodes** whose declared outputs become fields on the node handle.

---

## 4. Fan‑in / Fan‑out Patterns

```python
@tool(outputs=["v"]) 
def step(x: int): ...

@tool(outputs=["z"]) 
def join(a, b): ...

@graphify(name="fan", inputs=["x1", "x2"], outputs=["z"]) 
def fan(x1, x2):
    a = step(x=arg("x1"))  # fan‑out 1
    b = step(x=arg("x2"))  # fan‑out 2
    j = join(a=a.v, b=b.v)  # fan‑in
    return {"z": j.z}
```

> Tips: you can use for loop to create fan-in and fan-out

---

## 5. Run a Built Graph

Run the materialized DAG with the runner (sync or async):

```python
from aethergraph.runner import run, run_async

result = run(G, inputs={"csv_path": "data/train.csv"})
# → {"uri": "file://..."}

# Async form (e.g., inside another async function)
final = await run_async(G, inputs={"csv_path": "data/train.csv"})
```

---

## 6. Inspect and Explore

`@graphify` builders expose helpers for IO/signature and full spec:

```python
sig  = etl_train_report.io()     # inputs/outputs signature
spec = etl_train_report.spec()   # GraphSpec (nodes, edges, metadata)
```

**Runtime helpers on `TaskGraph`:**

```python
print(G.pretty())                # human‑friendly table
print(G.ascii_overview())        # compact overview

# Select / find nodes
ids     = G.list_nodes()                         # visible node_ids
first_c = G.find_by_logic("clean", first=True)  # by tool/logic name
some    = G.find_by_label("train")              # by label
sel     = G.select("@my_alias")                 # mini‑DSL (@alias, #label, logic:, name:, id:, /regex/)

# Topology & subgraphs
order   = G.topological_order()                  # raises if cycles
up      = G.get_upstream_nodes(first_c)          # dependency closure
sub     = G.get_subgraph_nodes(first_c)          # downstream closure
```

**Export / visualize**

```python
dot = G.to_dot()                 # Graphviz DOT
# G.visualize()                  # if enabled: render to file/viewer
```

---

## 7. Recall: Use `@tool` inside `@graph_fn`

While `@graph_fn` executes immediately, **you can embed `@tool` calls** to create explicit nodes for tracing or parallelism within a reactive agent:

```python
from aethergraph import graph_fn, tool

@tool(outputs=["y"]) 
def square(x: int):
    return {"y": x*x}

@graph_fn(name="mix") 
async def mix(x: int, *, context):
    h = square(x=x)                 # schedules a tool node in the implicit graph
    await context.channel().send_text("running square…")
    return {"y": h.y}
```

> Prefer `@graphify` for full, reproducible pipelines; prefer `@graph_fn` for interactive/reactive agents that lean on `context.*`.

If you executed a `@graph_fn` and want to inspect the **implicit** graph of tool nodes it created:

```python
G_last = graph_fn.last_graph()    # TaskGraph of the most recent run (if available)
print(G_last.pretty())
```

---

## 8. Key Points

* `@graphify` **builds** a DAG from `@tool` calls; you **run it later**.
* Use `arg("name")` to reference declared inputs inside the builder.
* Use `_after` to force ordering without data edges.
* Fan‑out/fan‑in is natural with multiple `@tool` calls and a later join.
* Inspect via `.io()`, `.spec()`, `TaskGraph.pretty()`, `ascii_overview()`, `to_dot()`.
* **No nested static graphs** currently (don’t call one `@graphify` from another as a node).
* For reactive agents, stick with `@graph_fn`; for pipelines, prefer `@graphify`.
