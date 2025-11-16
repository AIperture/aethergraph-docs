# `TaskGraph` – Runtime Graph Representation

`TaskGraph` is the **runtime representation** of a graph in AetherGraph. It combines:

* A **structural spec** (`TaskGraphSpec`) – nodes, dependencies, metadata.
* A **mutable state** (`TaskGraphState`) – node statuses, outputs, patches.
* Ephemeral **runtime nodes** (`TaskNodeRuntime`) – convenience wrappers used by the scheduler and tools.

This page documents the **most commonly used APIs** on `TaskGraph`. 

> You typically will not directly use `TaskGraph` method except for inspection. Using `@graph_fn` and `graphify` to create graph is preferred.

---

## 1. Construction & Core Attributes

### Classmethods

```python
TaskGraph.new_run(spec: TaskGraphSpec, *, run_id: str | None = None, **kwargs) -> TaskGraph
TaskGraph.from_spec(spec: TaskGraphSpec, *, state: TaskGraphState | None = None) -> TaskGraph
```

* `new_run(...)` – convenience to create a **fresh run** with a new `run_id` and an empty `TaskGraphState` (all nodes start in `PENDING` except the inputs node, which is set to `DONE`).
* `from_spec(...)` – construct a `TaskGraph` from an existing spec and optional state (used for **resuming** or inspecting previous runs).

**Key attributes**

* `graph.spec: TaskGraphSpec` – structural definition.
* `graph.state: TaskGraphState` – statuses, outputs, patches, bound inputs.
* `graph.graph_id: str` – alias for `spec.graph_id`.
* `graph.nodes: list[TaskNodeRuntime]` – list of runtime node wrappers.
* `graph._runtime_nodes: dict[str, TaskNodeRuntime]` – internal node table (id → runtime node).

<details markdown="1">
<summary>Typical construction: new run vs resume</summary>

```python
# New run from a spec
spec = ...  # TaskGraphSpec from graphify / storage
G = TaskGraph.new_run(spec)

# Resume with existing state
state = ...  # TaskGraphState loaded from storage
G_resumed = TaskGraph.from_spec(spec, state=state)
```

You rarely instantiate `TaskGraph` directly; use `new_run` or `from_spec` (or runner helpers) instead.

</details>

---

## 2. Node Access & Selection

### Direct access

```python
node(self, node_id: str) -> TaskNodeRuntime
@property
nodes(self) -> list[TaskNodeRuntime]

node_ids(self) -> list[str]
get_by_id(self, node_id: str) -> str
```

* `node(node_id)` – get the **runtime node** (raises if not found).
* `nodes` – list of all runtime nodes.
* `node_ids()` – list of node IDs.
* `get_by_id()` – returns the same ID or raises if missing (useful when normalizing selectors).

### Indexed finders

```python
get_by_alias(alias: str) -> str
find_by_label(label: str) -> list[str]
find_by_logic(logic_prefix: str, *, first: bool = False) -> list[str] | str | None
find_by_display(name_prefix: str, *, first: bool = False) -> list[str] | str | None
```

These use metadata created at build time (e.g., via `call_tool(..., _alias=..., _labels=[...], _name=...)`).

* `get_by_alias("sum1")` → node id for alias `sum1` or `KeyError`.
* `find_by_label("critical")` → all node ids tagged with that label.
* `find_by_logic("tool_name")` → nodes whose logic name equals or starts with `tool_name`.
* `find_by_display("My Step")` → nodes whose display name equals or starts with `"My Step"`.

### Unified selector DSL

```python
select(selector: str, *, first: bool = False) -> str | list[str] | None
pick_one(selector: str) -> str
pick_all(selector: str) -> list[str]
```

Selector mini‑DSL:

* `"@alias"` → by alias.
* `"#label"` → by label (may return many).
* `"id:<id>"` → exact id.
* `"logic:<prefix>"` → logic name prefix.
* `"name:<prefix>"` → display name prefix.
* `"/regex/"` → regex on `node_id`.
* anything else → prefix match on `node_id`.

<details markdown="1">
<summary>Selector examples</summary>

```python
# Single node by alias
target_id = graph.pick_one("@sum1")

# All nodes with a label
critical_ids = graph.pick_all("#critical")

# First node whose logic name starts with "normalize_"
nid = graph.select("logic:normalize_", first=True)

# Regex on node id
debug_nodes = graph.pick_all("/debug_.*/")
```

Use selectors when building **debug tooling**, partial resets, or visualization filters.

</details>

---

## 3. Read‑only Views

```python
view(self) -> GraphView
list_nodes(self, exclude_internal: bool = True) -> list[str]
```

* `view()` – returns a `GraphView` with:

  * `graph_id`,
  * `nodes` (specs),
  * `node_status` (derived map: node id → `NodeStatus`),
  * `metadata`.
* `list_nodes(exclude_internal=True)` – list node ids, optionally excluding internal nodes (ids starting with `_`).

<details markdown="1">
<summary>Inspecting a graph view</summary>

```python
v = graph.view()
print(v.graph_id)
print(v.node_status)  # {"node_1": NodeStatus.DONE, ...}
```

`GraphView` is a snapshot for inspection / APIs; it does not expose mutation methods.

</details>

---

## 4. Graph Mutation (Patches)

Dynamic graph edits are represented as **patches** in `TaskGraphState`.

```python
patch_add_or_replace_node(node_spec: dict[str, Any]) -> None
patch_remove_node(node_id: str) -> None
patch_add_dependency(node_id: str, dependency_id: str) -> None
```

* `patch_add_or_replace_node` – add a new node or replace an existing one (payload is a plain dict convertible to `TaskNodeSpec`).
* `patch_remove_node` – remove a node by id.
* `patch_add_dependency` – add a new dependency edge.

Each method:

* appends a `GraphPatch` entry to `state.patches` and increments `state.rev`,
* notifies observers via `on_patch_applied`,
* rebuilds `_runtime_nodes` for the effective view.

> These APIs are intended for **advanced dynamic graph editing** and patch flows; many users won’t need them directly.

---

## 5. Topology & Subgraphs

```python
dependents(node_id: str) -> list[str]
topological_order() -> list[str]
get_subgraph_nodes(start_node_id: str) -> list[str]
get_upstream_nodes(start_node_id: str) -> list[str]
```

* `dependents(nid)` – all nodes that list `nid` as a dependency.
* `topological_order()` – a topological sort of all nodes (raises on cycles).
* `get_subgraph_nodes(start)` – `start` plus all nodes **reachable downstream** (dependents).
* `get_upstream_nodes(start)` – `start` plus all nodes it **depends on** (upstream).

<details markdown="1">
<summary>Working with subgraphs</summary>

```python
# All nodes that can be affected if you change `node_a`
forward = graph.get_subgraph_nodes("node_a")

# All nodes that must run before `node_b`
upstream = graph.get_upstream_nodes("node_b")
```

These helpers are typically used for **partial reset**, **impact analysis**, or **visualization filters**.

</details>

---

## 6. State Mutation & Reset

```python
async def set_node_status(self, node_id: str, status: NodeStatus) -> None
async def set_node_outputs(self, node_id: str, outputs: dict[str, Any]) -> None

async def reset_node(self, node_id: str, *, preserve_outputs: bool = False)
async def reset(
    self,
    node_ids: list[str] | None = None,
    *,
    recursive: bool = True,
    direction: str = "forward",
    preserve_outputs: bool = False,
) -> dict[str, Any]
```

* `set_node_status` – update a node’s status and notify observers (`on_node_status_change`).
* `set_node_outputs` – update a node’s outputs and notify observers (`on_node_output_change`).
* `reset_node` – reset a single node to `PENDING`, optionally keeping outputs.
* `reset` – reset all or part of the graph:

  * `node_ids=None` → reset all nodes (except the synthetic inputs node).
  * `recursive=True, direction="forward"` → also reset all dependents.
  * `recursive=True, direction="backward"` → reset upstream dependencies.

<details markdown="1">
<summary>Partial reset patterns</summary>

```python
# Reset a node and everything that depends on it
await graph.reset(node_ids=["step_3"], recursive=True, direction="forward")

# Reset only a single node, keeping its outputs
await graph.reset(node_ids=["step_3"], recursive=False, preserve_outputs=True)

# Reset entire graph (except inputs)
await graph.reset(node_ids=None)
```

These methods are used by runners / UIs to implement **retry**, **rerun from here**, and **what-if** operations.

</details>

---

## 7. IO Definition & Binding

### IO APIs

```python
declare_inputs(
    *,
    required: Iterable[str] | None = None,
    optional: dict[str, Any] | None = None,
) -> None

expose(name: str, value: Ref | Any) -> None
require_outputs(*names: str) -> None

io_signature(include_values: bool = False) -> dict[str, Any]
```

* `declare_inputs(...)` – declares graph-level inputs:

  * `required` – names that **must** be provided when binding inputs.
  * `optional` – names with default values (modeled via `ParamSpec`).
* `expose(name, value)` – declare a graph output:

  * `value` can be a **Ref** (to node outputs or inputs) or a literal.
* `require_outputs(...)` – sanity check for required outputs (uses internal `_io_outputs`).
* `io_signature(include_values=False)` – summarized IO description:

  * `inputs.required` / `inputs.optional` (names and defaults).
  * `outputs.keys` – names of exposed outputs.
  * `outputs.bindings` – raw bindings (Refs or literals).
  * `outputs.values` – optional resolved values (when `include_values=True`).

> Binding of actual input values happens via the runner, which calls the internal `_validate_and_bind_inputs(...)` helper.

<details markdown="1">
<summary>Inspect IO signature</summary>

```python
sig = graph.io_signature()
print(sig["inputs"]["required"])
print(sig["outputs"]["keys"])

# After a run, you can inspect resolved output values
full = graph.io_signature(include_values=True)
print(full["outputs"]["values"])
```

The IO signature is useful for **APIs**, **UIs**, and tooling that needs to describe how to call a graph without inspecting internals.

</details>

---

## 8. Observers & Notifications

```python
add_observer(observer: Any) -> None
```

Observers are objects that can implement any of the following methods:

* `on_node_status_change(runtime_node)`
* `on_node_output_change(runtime_node)`
* `on_inputs_bound(graph)`
* `on_patch_applied(graph, patch)`

They are invoked whenever the corresponding events occur.

<details markdown="1">
<summary>Lightweight observer usage</summary>

```python
class PrintObserver:
    def on_node_status_change(self, node):
        print("status", node.node_id, node.state.status)

graph.add_observer(PrintObserver())
```

Observers are the main extension point for **logging**, **metrics**, and **live UI updates**.

</details>

---

## 9. Diff & Persistence Helpers

### Diffing

```python
diff(other: TaskGraph) -> dict[str, Any]
```

* Compare two graphs with the **same `graph_id`**.
* Returns a dict with:

  * `"added"`: list of node ids present only in `other`.
  * `"removed"`: list of node ids present only in `self`.
  * `"modified"`: node ids whose dependencies or metadata differ.

<details markdown="1">
<summary>Basic diff usage</summary>

```python
d = graph_v2.diff(graph_v1)
print("added", d["added"])
print("modified", d["modified"])
```

Useful for **visualizing evolution**, **reviewing patches**, or **migration tooling**.

</details>

### Spec serialization

```python
spec_json(self) -> dict[str, Any]
```

* Returns a JSON‑safe representation of the spec (`TaskGraphSpec`) using `_dataclass_to_plain`.
* Storage/layout is left to callers (file, DB, etc.).

---

## 10. Debug & Visualization

### Human‑readable summary

```python
pretty(self, *, max_nodes: int = 20, max_width: int = 100) -> str
__str__(self) -> str
```

* `pretty(...)` – a compact, human‑friendly summary including:

  * graph id, node count, observer count;
  * IO signature summary;
  * state summary;
  * a small table of nodes with id, type, status, dependencies count, and logic.
* `__str__` – uses `pretty(max_nodes=12, max_width=96)` for `print(graph)`.

<details markdown="1">
<summary>Quick debug print</summary>

```python
print(graph)          # uses __str__
print(graph.pretty()) # full summary
```

This is the fastest way to get an overview of a graph in a REPL or log.

</details>

### Visualization helpers

At the bottom of the module, these are attached as methods:

```python
TaskGraph.to_dot = to_dot
TaskGraph.visualize = visualize
TaskGraph.ascii_overview = ascii_overview
```

* `graph.to_dot(...)` – export a DOT representation.
* `graph.visualize(...)` – high‑level helper for rich visualizations (see Visualization docs).
* `graph.ascii_overview(...)` – ASCII summary for terminals / logs.

<details markdown="1">
<summary>High‑level usage (shape only)</summary>

```python
dot_str = graph.to_dot()
print(graph.ascii_overview())
# graph.visualize(...)  # see visualization docs for options
```

Exact options and rendering backends are described on the **Visualization** page.

</details>

---

## 11. Summary

* `TaskGraph` ties together **spec**, **state**, and **runtime node table**.
* Use `new_run` / `from_spec` to construct graphs; use selectors (`pick_one`, `pick_all`) to locate nodes.
* IO is declared via `declare_inputs` / `expose` and inspected via `io_signature`.
* Topology helpers (`dependents`, `get_subgraph_nodes`, `get_upstream_nodes`) support partial reset and analysis.
* State mutation APIs (`set_node_status`, `set_node_outputs`, `reset`) underpin runners and interactive tooling.
* Patches, diff, observers, and visualization helpers are advanced tools for dynamic graphs, UIs, and diagnostics.
