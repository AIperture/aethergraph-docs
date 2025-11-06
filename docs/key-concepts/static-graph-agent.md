# Static Graphs with `@graphify`

`@graphify` turns a plain Python function into a **graph builder**. Instead of executing immediately (like `@graph_fn`), it **constructs a TaskGraph** from `@tool` calls, which you build once and run later.

> **In short:** `@graph_fn` = execute now (implicit, reactive).
> `@graphify` = build first, then run (explicit DAG).

---

## 1 What is a Static Graph?

A **static graph** is an explicit DAG of tool nodes and dependencies. All internal steps must be `@tool` calls; the builder wires nodes and returns exposed outputs. You can then:

* inspect the spec / IO signature
* persist or visualize the graph
* run it under the **global scheduler**

**Why static?** Repeatability, inspectability, and clear fan‑in/fan‑out. Ideal for pipelines and reproducible experiments.

**How it differs from `@graph_fn`:**

* `@graph_fn` executes immediately with a per‑function scheduler and rich `context.*` calls.
* `@graphify` **builds** a DAG; you run it later (typically using the global scheduler).

> When to use it: `@graphify` asks for a bit more code up front (declared inputs, explicit `@tool` nodes, `_after` for ordering), but you get stability, efficiency, and inspectability in return—deterministic runs, clearer fan-in/out, easier caching/retries, and better debugging/analytics. For reactive exploration, stick with `@graph_fn` until your flow settles; switch to `@graphify` when the pipeline is stabilized or when product environments demand determinism and performance.

---

## 2 Define and Build a Graph

```python
from aethergraph import graphify, tool
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

G = etl_train_report.build()     # → TaskGraph
```

### Control ordering without data edges

Use `_after` to enforce sequence when you don’t pass outputs:

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

---

## 3 Run a Built Graph

Static graphs typically run under the **global scheduler** (centralized control over node scheduling). You can only run a static graph using runner function. 

```python
# Pseudocode — exact runner API depends on your hosting layer
from aethergraph.runner import run

result = run(G, inputs={"csv_path": "data/train.csv"})
# `result` contains graph-level outputs, e.g., {"uri": "file://..."}
```

> **Note:** `@graph_fn` uses its own lightweight scheduler for immediate execution, while `@graphify` graphs are designed to be scheduled by the **global** scheduler for observability, resumability, and concurrency control.

---

## 4 Inspect and Explore a Graph

`@graphify` builders expose helpers:

```python
sig = etl_train_report.io()      # inputs/outputs signature
spec = etl_train_report.spec()   # GraphSpec (nodes, edges, metadata)
```

**Runtime helpers on `TaskGraph`:**

```python
print(G.pretty())                # human-friendly table
print(G.ascii_overview())        # compact ASCII view

# Select / find nodes
ids     = G.list_nodes()                         # all non-internal node_ids
first_c = G.find_by_logic("clean", first=True)  # by tool/logic name
some    = G.find_by_label("train")              # by label
sel     = G.select("@my_alias")                  # mini-DSL (@alias, #label, logic:, name:, id:, /regex/)

# Topology & subgraphs
order   = G.topological_order()                  # raise if cycles
up      = G.get_upstream_nodes(first_c)          # closure of dependencies
sub     = G.get_subgraph_nodes(first_c)          # downstream dependents
```

**Export / visualize**

```python
dot = G.to_dot()                 # Graphviz DOT
# G.visualize()                  # if enabled: render to file/viewer
```

---

## 5 Recall: Use `@tool` inside `@graph_fn`

While `@graph_fn` executes immediately, you **can** embed `@tool` calls to create explicit nodes for tracing or parallelism within a reactive agent:

```python
from aethergraph import graph_fn, tool

@tool(outputs=["y"]) 
def square(x: int): return {"y": x*x}

@graph_fn(name="mix")
async def mix(x: int, *, context):
    h = square(x=x)                 # schedules a tool node in the implicit graph
    await context.channel().send_text("running square…")
    return {"y": h.y}
```

> Prefer `@graphify` for full pipelines and reproducible DAGs; prefer `@graph_fn` for interactive/reactive agents that lean on `context.*`.

---

If you executed a `@graph_fn` and want to inspect the **implicit** graph of tool nodes it created:

```python
from aethergraph import graph_fn
G_last = graph_fn.last_graph()    # TaskGraph of the most recent run (if available)
print(G_last.pretty())
```

---

## 6 Key Points

* `@graphify` **builds** a DAG from `@tool` calls; you **run it later** (usually with the global scheduler).
* Use `arg("name")` inside the builder to reference declared inputs.
* Use `_after` to force ordering without data edges.
* Inspect via `.io()`, `.spec()`, `TaskGraph.pretty()`, `ascii_overview()`, `to_dot()`.
* For reactive agents, stick with `@graph_fn`; for pipelines, prefer `@graphify`.
