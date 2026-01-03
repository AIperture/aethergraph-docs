# Runner API – `run_async` & `run`

The runner serves as the **unified entry point** for executing:

* a **`GraphFunction`** (created with `@graph_fn`), or
* a **static `TaskGraph`** (constructed via `graphify`, builder, or storage).

Internally, it initializes a `RuntimeEnv`, configures services, and manages a `ForwardScheduler` with customizable **retry** and **concurrency** options.

---

## Runner APIs

Use these APIs to start new runs. For nested execution of graphs or agents, refer to the [Context Run API](context-runner.md).

???+ quote "run_async(target, inputs, identity, **rt_overrides)"
    ::: aethergraph.core.runtime.graph_runner.run_async
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

???+ quote "run(target, inputs, identity, **rt_overrides)"
    ::: aethergraph.core.runtime.graph_runner.run
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false