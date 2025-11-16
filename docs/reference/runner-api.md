# Runner API – `run_async` & `run`

The runner is the **unified entry point** to execute either:

* a **`GraphFunction`** (from `@graph_fn`), or
* a **static `TaskGraph`** (built via `graphify` / builder / storage).

Under the hood it builds a `RuntimeEnv`, wires services, and drives a `ForwardScheduler` with configurable **retry** and **concurrency**.

---

## 1. Function Shapes

### `run_async`

```python
async def run_async(
    target,
    inputs: dict[str, Any] | None = None,
    **rt_overrides,
):
    """
    Generic async runner for TaskGraph or GraphFunction.
    - GraphFunction → delegates to gf.run(env=..., **inputs)
    - TaskGraph/builder → schedules and resolves graph-level outputs
    """
```

**Accepted `target` types**

* `GraphFunction` instance (`@graph_fn` result)
* `TaskGraph` instance 
* **Builder** with `.build()` returning a `TaskGraph`
* **Callable** returning a `TaskGraph` when called with no args

**Inputs**

* `inputs: dict[str, Any] | None`
  Graph-level inputs (must match the graph’s declared `required` / `optional` IO). Defaults to `{}`.

* `**rt_overrides` – runtime overrides (see [Runtime overrides](#3-runtime-overrides-rt_overrides)).

**Returns**

* For a **`GraphFunction` target**: `dict` matching its declared or inferred `outputs` list.
* For a **TaskGraph target**:

    * If the graph exposes **exactly one** output → that value directly.
    * Otherwise → `dict[name, value]` for all exposed outputs. (In `@graphify` it is the declared `outputs` list)
    
* May raise `GraphHasPendingWaits` if the run quiesces with unresolved waits and outputs cannot yet be resolved.

---

### `run` (sync adapter)

```python
def run(
    target,
    inputs: dict[str, Any] | None = None,
    **rt_overrides,
):
    ...
```

* Thin synchronous wrapper around `run_async`, using a background event loop thread.
* Same `target`, `inputs`, and `rt_overrides` semantics.
* Returns the **same result shape** as `run_async(...)` but **blocks** the current thread.

> Use `run(...)` in **scripts / notebooks** where you don’t want to manage an event loop yourself. Prefer `run_async(...)` in async applications or services.

---

## 2. GraphFunction Convenience – `await my_graph_fn(...)`

For `@graph_fn` agents, you **don’t have to call the runner directly**.

`GraphFunction` implements `__call__`:

```python
class GraphFunction:
    ...

    async def __call__(self, **inputs):
        """Async call to run the graph function.
        Usage:
           result = await my_graph_fn(input1=value1, input2=value2)
        """
        from ..runtime.graph_runner import run_async
        return await run_async(self, inputs)
```

So you can simply:

```python
# my_graph_fn is created via @graph_fn(...)
result = await my_graph_fn(x=1, y=2)
```

Behind the scenes this:

* Builds a `RuntimeEnv` and `ForwardScheduler` via `run_async`.
* Creates a **fresh TaskGraph** for this call.
* Injects `NodeContext` if the function signature includes `context`.

> Use `await my_graph_fn(...)` for **day-to-day agent usage**; reach for `run_async(...)` when you need **fine-grained control** over runtime overrides or when running **static TaskGraphs**.

---

## 3. Runtime overrides (`**rt_overrides`)

The `run_async` / `run` API accepts **extra keyword arguments** to customize the runtime. These are passed to `_build_env(...)`, which:

1. Creates a default container via `build_default_container()`.
2. Applies overrides onto the container and env.

### Core overrides

These are the most important knobs:

* `run_id: str`
  Explicit run identifier (otherwise a random `run-<hex>` is generated). Used for **persistence**, **resume**, and **continuations**.

* `retry: RetryPolicy`
  Custom retry behavior for node execution. Defaults to a new `RetryPolicy()` when not provided.

* `max_concurrency: int`
  Upper bound on **parallel node execution** used by the scheduler. Defaults to `getattr(owner, "max_concurrency", 4)` – where `owner` is the `GraphFunction` or `TaskGraph`.

In addition, any override where the **name matches a container attribute** is applied directly:

```python
container = _get_container()
for k, v in rt_overrides.items():
    if v is not None and hasattr(container, k):
        setattr(container, k, v)
```

Typical examples include (depending on your container):

* `state_store=...` – custom state store for snapshots / resume.
* `artifacts=...` – custom artifact store.
* `llm=...`, `memory=...`, `rag=...`, `kv=...` – swapped service instances.
* `continuation_store=...` – custom continuation backend.

> **Rule of thumb:**
> Use explicit overrides (`run_id`, `retry`, `max_concurrency`) most often; use container attribute overrides when you need to plug in **custom services** for a particular run.

---

## 4. Scheduler Behavior (Execution Model)

> Currently, Scheduler API is not exposed. Here we list the function shape for completeness 

`run_async` builds a `ForwardScheduler`:

```python
sched = ForwardScheduler(
    graph,
    env,
    retry_policy=retry,
    max_concurrency=max_conc,
    skip_dep_on_failure=True,
    stop_on_first_error=True,
    logger=logger,
)
```

**Key parameters**

* `max_concurrency: int` – how many **ready** nodes can run concurrently.
* `stop_on_first_error: bool` – whether to stop scheduling when the first node fails (`True` in the default runner).
* `skip_dep_on_failure: bool` – whether to skip downstream nodes whose dependencies failed (`True` by default).

**Execution semantics (high level)**

* The scheduler maintains a queue of **ready nodes** (all dependencies completed).
* It launches nodes in **parallel** up to `max_concurrency`.
* If a node **waits** (e.g., external continuation), it may park and allow other ready nodes to proceed.
* At the end of the run, the runner resolves graph-level outputs via `io_signature` bindings; if some outputs are unresolved due to waits, it raises `GraphHasPendingWaits`.

> More advanced scheduling / resume controls are exposed via the Scheduler and Recovery APIs; this section only covers the knobs surfaced through `run_async`.

---

## 5. Run vs Resume (async)

There is also a helper:

```python
async def run_or_resume_async(
    target,
    inputs: dict[str, Any],
    *,
    run_id: str | None = None,
    **rt_overrides,
):
    """
    If state exists for run_id → cold resume, else fresh run.
    Exactly the same signature as run_async plus optional run_id.
    """
```

* If a `state_store` is configured and snapshots exist for the given `run_id`, the graph is **recovered** and resumed.
* If not, it behaves like a fresh `run_async(...)` call (with the given `run_id` if provided).

Use this when you:

* Know the `run_id` you want to continue, but
* Don’t want to manually check whether state exists.

---

## 6. Summary

* `run_async(target, inputs, **rt_overrides)` is the **core runner** for both `GraphFunction` agents and static `TaskGraph`s.
* `run(...)` is a **sync adapter** around `run_async` for scripts / notebooks.
* `GraphFunction` supports direct `await my_graph_fn(...)`, which simply delegates to `run_async(self, inputs)`.
* You can control runtime behavior via:

  * `run_id`, `retry`, `max_concurrency`,
  * and container-level overrides (e.g., `state_store`, `artifacts`, `llm`, `memory`).
* Execution is handled by a `ForwardScheduler` that runs ready nodes concurrently up to `max_concurrency`, stopping on first error and skipping dependents of failed nodes by default.
