# External Context Services (Revised)

> Make reusable, lifecycle‑aware helpers available as `context.<name>` inside any `@graph_fn`.

This page explains what an **external context service** is, why you might use one, how it looks at a high level, and the APIs you’ll use to define and register services. It also clarifies lifecycle behavior **today** vs. **after** you add a server/sidecar, and shows how services can access the active `NodeContext`.

---

## 1) What is an external context service?

An **external context service** is a Python object managed by AetherGraph’s runtime and exposed to your graph functions through the `NodeContext`. Once registered, you can access it as `context.svc("name")` or simply `context.<name>`.

Key ideas:

* **Dependency injection**: Centralize clients, caches, and policies in one place and inject them wherever needed.
* **Lifecycle‑ready**: Services can implement `start()` and `close()` for setup/teardown (e.g., open a pool, kick off a background task). *Today these hooks are optional and not auto‑invoked unless you wire them (see §4.1).*
* **Concurrency controls**: Built‑in mutex and read/write helpers to safely share state across concurrent nodes.
* **Per‑run binding**: Each call is bound to a `NodeContext` so the service can access run_id, logger, artifacts, memory, etc.
* **Uniform surface**: The same service works in local scripts today and can be proxied or hosted later without changing call sites.

Use services when logic benefits from a **long‑lived instance**, **shared state**, or **orchestration**—not for tiny, pure functions (plain imports are fine there).

---

## 2) High‑level usage sketch

Below is a **conceptual** outline (intentionally abstract) of how you would define and call a service.

### Define (high‑level)

```python
class MyService(Service):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._cache = {}

    async def start(self):
        # optional: warm up connections, threads, or caches
        ...

    async def close(self):
        # optional: flush or close resources
        ...

    async def do_something(self, key: str) -> str:
        # example: consult cache, maybe call out to an API, return a value
        ...
```

### Register (at app startup)

```python
register_context_service("myservice", MyService(config={"mode": "dev"}))
```

### Use in a graph function

```python
@graph_fn(name="demo")
async def demo(*, context: NodeContext):
    value = await context.myservice.do_something("foo")
    return {"value": value}
```

That’s it: once registered, your service is reachable from any node via `context`.

---

## 3) Why use external context? (Benefits + use cases)

### Benefits

* **Replaceable implementations**: Swap local vs. remote, mock vs. real, dev vs. prod—without editing call sites.
* **Centralized auth & config**: Put tokens, endpoints, retry/timeout policy, telemetry in one place.
* **Lifecycle & performance**: Reuse clients, connection pools, thread pools; warm caches once.
* **Concurrency safety**: Use the provided `critical()` mutex or `AsyncRWLock` to protect shared state.
* **Per‑run awareness**: Access `self.ctx()` to reach logger, artifacts, memory, continuations, etc.
* **Future‑proof**: The same surface can later be proxied (sidecar/hosted) while keeping your graph code unchanged.

### Itemized scenarios (no code)

* **Model/Tool Clients**: Wrap an LLM, embedding service, vector DB, or a simulation engine with retry, rate limit, and consistent API.
* **Job Orchestration**: Submit long‑running jobs to a queue/cluster and expose `submit/status/wait` for nodes.
* **Caching/Indexing**: Provide a shared in‑memory or on‑disk cache with strict read (R/W lock) semantics.
* **Policy Enforcement**: Centralize tenant limits, quotas, audit logging, and redaction.
* **Data Access Facades**: Read domain data (materials table, experiment registry) with local cache + background refresh.
* **Adapters**: Present a unified interface over heterogeneous backends (e.g., multiple vendor APIs behind one broker).

---

## 4) APIs: defining, registering, and binding services

AetherGraph provides small primitives for service registration and a base class with helpful utilities.

### 4.1 Lifecycle (today vs. server/sidecar)

* **Today (no server yet):** `start()`/`close()` exist but are **not auto‑invoked**. You can omit them or leave them as no‑ops.
* **When you add a server/sidecar:** wire lifecycle once at boot/shutdown (pseudo‑code):

```python
# After install_services(...) and registrations
await start_all_services()
# ... run your app/sidecar ...
await close_all_services()
```

> Until those hooks are added, services work fine without lifecycle calls.

### 4.2 Registry functions (runtime‑level)

* `install_services(container)` – Set the process‑wide service container at startup.
* `ensure_services_installed(factory)` – Lazily create/install the container if missing.
* `register_context_service(name, instance)` – Add a concrete service instance under `name`.
* `get_context_service(name)` – Retrieve a registered instance.
* `list_context_services()` – List the names currently registered.

### 4.3 Base class: `Service` (aka `BaseContextService`)

The base class gives you batteries‑included ergonomics:

* **Lifecycle**

  * `async def start(self) -> None` – Optional setup hook.
  * `async def close(self) -> None` – Optional teardown hook.

* **Binding**

  * `def bind(self, *, context: NodeContext) -> Service` – Called by the runtime so `self.ctx()` works.
  * `def ctx(self) -> NodeContext` – Access the current node context (logger, memory, artifacts, etc.).

* **Concurrency**

  * `self._lock` – An async mutex available for your own critical sections.
  * `def critical()(fn)` – Decorator that serializes an **async** method (easy mutual exclusion).
  * `class AsyncRWLock` – Many‑readers/one‑writer lock for shared tables and caches.

* **Offloading**

  * `async def run_blocking(self, fn, *a, **kw)` – Run CPU or blocking I/O on a worker thread (keeps the event loop responsive).

### 4.4 Accessing services from nodes

* **Dynamic attribute**: `context.<name>` resolves to the registered service (e.g., `context.myservice`).
* **Explicit lookup**: `context.svc("name")` (equivalent to the dynamic attribute).

### 4.5 Accessing `NodeContext` from *inside* a service (essential)

Services frequently need run‑scoped utilities (logger, memory, artifacts, kv, llm, rag, etc.). Enable **per‑call binding** so `self.ctx()` returns the right `NodeContext`.


**Use `self.ctx()` in the service**:

```python
class MyService(Service):
    async def do_work(self, x: int) -> int:
        ctx = self.ctx()  # NodeContext bound for this call
        ctx.logger().info("working", extra={"x": x})
        await ctx.memory().record(kind="note", data={"x": x})
        uri = ctx.artifacts().put_text("result.txt", f"value={x}")
        return x + 1
```

### 4.6 Event loop & locking model

* External services run on the **main event loop** used by the executing node.
* Locks (`_lock`, `AsyncRWLock`) coordinate on that loop; use `run_blocking()` for CPU/IO work.

---

## 5) Summary

External context services provide a clean way to share long‑lived capabilities across nodes while keeping graph code small and portable:

* **Inject** reusable helpers via `context.<name>` (or `context.svc(name)`).
* **Manage** concurrency and performance in one place; offload blocking work with `run_blocking()`.
* **Abstract** environments (mock/local/dev/prod) without touching business logic.
* **Bind** to `NodeContext` automatically so services can use logger, memory, artifacts, kv, llm/rag, etc.
* **Lifecycle now vs later**: Today you can skip `start()`/`close()`; add startup/shutdown hooks when you introduce a server/sidecar.

Use services for shared state, orchestration, specialized clients, or cross‑cutting policies. Use plain imports for tiny, stateless helpers.

---
