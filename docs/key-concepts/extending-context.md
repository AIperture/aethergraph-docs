# Extending Context Services

AetherGraph lets you **extend the runtime** by adding your own `context.<name>` methods. These *external context services* are reusable, lifecycle-aware helpers that live alongside the built-ins (`channel`, `memory`, `artifacts`, etc.) and can hold shared state, wrap APIs, or orchestrate external systems — all without changing your agent code.

---

## What Is an External Context Service?

A **context service** is a registered Python object that AetherGraph injects into every node’s `NodeContext`. Once registered, it’s available anywhere inside a graph:

```python
@graph_fn(name="demo")
async def demo(*, context):
    val = await context.myservice.do_something("foo")
    return {"val": val}
```

### Why Use It

* **Reusable helpers** – share clients, caches, or models across nodes.
* **Shared state** – coordinate progress or reuse expensive objects.
* **Centralized config** – keep API keys, timeouts, or policies in one place.
* **Lifecycle control** – optional `start()`/`close()` for setup or teardown.
* **Per-run binding** – each call knows its `run_id`, `graph_id`, and `node_id`.

Use a service when you need a *long-lived instance* or *cross-node coordination*. For small, stateless helpers, plain imports are simpler.

---

## Minimal Example

### Define a Service

```python
from aethergraph.v3.core.runtime.base_service import Service

class MyService(Service):
    async def do_something(self, key: str) -> str:
        ctx = self.ctx()  # current NodeContext
        ctx.logger().info(f"working on {key}")
        return f"done:{key}"
```

### Register at Startup

```python
from aethergraph.v3.core.runtime.runtime_services import register_context_service
register_context_service("myservice", MyService())
```

Now `context.myservice` is available to all nodes in that runtime.

---

## When to Use Custom Services

| Scenario                | Example                                           |
| ----------------------- | ------------------------------------------------- |
| **Model/Tool Wrappers** | unify access to LLMs, simulation engines, or APIs |
| **Shared Caches**       | memoize expensive lookups or material tables      |
| **Job Orchestration**   | submit/track remote compute jobs                  |
| **Policy / Governance** | enforce tenant limits, logging, or auditing       |
| **Adapters / Brokers**  | expose multiple vendor APIs under one interface   |

---

## Lifecycle & Concurrency

* Services can optionally implement `start()` / `close()`; these are manual today but can be auto-wired when running under a server/sidecar.
* Use `self.critical()` or `AsyncRWLock` for safe shared access.
* `self.run_blocking(fn)` helps offload CPU or blocking I/O.

---

## Takeaways

* External services make AetherGraph modular and composable.
* They behave like built-in context methods — bound automatically per node.
* Use them to manage clients, caches, orchestration, or background work.
* Configure once; your `@graph_fn` and `@tool` logic remains unchanged.

> See also: [External Context Deep Dive →](../external_context.md) for advanced registration, lifecycle management, and hosted modes.
