# Custom Context Services – API Guide (using `Service` alias)

AetherGraph lets you attach **your own runtime helpers** onto `context.*` as first‑class services (e.g., `context.trainer()`, `context.materials()`).

> Use **`Service`** (alias of the underlying `BaseContextService`) for all subclasses:
>
> ```python
> from aethergraph import Service  # alias of BaseContextService
> ```

Register your service **after the sidecar starts**, then access it anywhere via the context: `context.<name>()`.

---


## Minimal Flow

```python
from aethergraph import start_server, Service
from aethergraph.runtime import register_context_service

class MyCache(Service):
    def __init__(self):
        super().__init__()
        self._data = {}

    def get(self, k, default=None):
        return self._data.get(k, default)

    def set(self, k, v):
        self._data[k] = v

# 1) Start sidecar
start_server(port=0)

# 2) Register a **singleton** instance for all contexts
register_context_service("cache", MyCache())

# 3) Use inside a graph/tool
async def do_work(*, context):
    cache = context.cache()        # no‑arg call ⇒ bound service instance
    cache.set("foo", 42)
    return cache.get("foo")
```

**Why it works:**

* `context.__getattr__("cache")` resolves the registered service and binds the active `NodeContext` via `Service.bind(...)`.
* The returned `_ServiceHandle` forwards attribute access and calls. A **no‑arg call** returns the underlying service instance for convenience.

---

## API Reference
### 1. Register External Services
??? quote "register_context_service(name, service)"
    ::: aethergraph.core.runtime.runtime_services.register_context_service
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "get_ext_context_service(name)"
    ::: aethergraph.core.runtime.runtime_services.get_ext_context_service
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "list_ext_context_services()"
    ::: aethergraph.core.runtime.runtime_services.list_ext_context_services
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 


### 2. Access External Services

??? quote "context.<service_name\>(*args)"
    ::: aethergraph.core.runtime.node_context.NodeContext.__getattr__
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 


??? quote "context.svc(name)"
    ::: aethergraph.core.runtime.node_context.NodeContext.svc
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

---

## Patterns

### 1) Context‑Aware Logging & Artifacts

```python
from aethergraph import Service

class Reporter(Service):
    def log_metric(self, name: str, value: float):
        self.ctx().logger().info("metric", extra={"name": name, "value": value})

    async def save_text(self, text: str) -> str:
        art = await self.ctx().artifacts().save_text(text)
        return art.uri
```

### 2) Thread‑safe Mutations

```python
from aethergraph import Service

class Counter(Service):
    def __init__(self):
        super().__init__()
        self._n = 0
        self.inc = self.critical()(self.inc)

    def inc(self, k: int = 1) -> int:
        self._n += k
        return self._n
```

### 3) Wrapping External Clients

```python
from aethergraph import Service
import httpx

class Weather(Service):
    def __init__(self, base: str):
        super().__init__()
        self._base = base
        self._http = httpx.Client(timeout=10)

    async def close(self):
        await self.run_blocking(self._http.close)

    def get_temp_c(self, city: str) -> float:
        r = self._http.get(f"{self._base}/temp", params={"city": city})
        r.raise_for_status()
        return float(r.json()["c"])  # noqa
```

### 4) Using in Graphs/Tools

```python
from aethergraph import Service
from aethergraph.runtime import register_context_service

class Greeter(Service):
    def greet(self, name: str) -> str:
        return f"Hello, {name}! (run={self.ctx().run_id})"

register_context_service("greeter", Greeter())

# Inside a node
async def hello(*, context):
    g = context.greeter()               # bound service
    return {"msg": g.greet("World")}
```

---

## FAQ

**Q: Where should I create the service instance?**
Usually at process boot, **after** `start_server(...)`. Register exactly once (singleton). If you need per‑tenant services, implement your own map inside the service keyed by tenant.

**Q: How do I access other context services from my service?**
Use `self.ctx().<other_service>()`, e.g., `self.ctx().artifacts()` or `self.ctx().logger()`.

**Q: Can a service be async?**
Yes—methods can be `async` and you may leverage `run_blocking(...)` for sync IO.

**Q: How do I store configuration/keys?**
Provide them to your service constructor, or pull from env. For dynamic secrets, wire a secrets service and read from it inside your custom service.

---

## Gotchas & Tips

* **Name collisions:** Avoid names of built‑ins (`channel`, `memory`, `artifacts`, etc.).
* **No context at import time:** `Service.ctx()` works **after** binding; do not call it in `__init__`.
* **Thread safety:** Use `@Service.critical` for shared state.
* **Long‑running IO:** Prefer `await self.run_blocking(...)` for blocking clients.
* **Testing:** You can construct a `Service` and call `bind(context=FakeContext(...))` directly in unit tests.
