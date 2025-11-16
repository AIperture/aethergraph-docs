# Sidecar Server – `start_server` and `stop_server`

The **sidecar server** is a lightweight FastAPI+Uvicorn process that:

* Boots the **services container** (channels, LLM, RAG, artifacts, state store, etc.).
* Exposes a small HTTP/WebSocket API for adapters, web UI, and continuations.
* Installs a **web channel** so you can talk to agents via a browser.

For most applications you:

1. Call `start_server(...)` once at startup (or in a notebook cell).
2. Use `@graph_fn`, `run_async`, and `context.*` as usual.
3. Optionally call `stop_server()` in tests or when shutting down.

---

## 1. `start_server` – sync sidecar starter

```python
def start_server(
    *,
    workspace: str = "./aethergraph_data",
    host: str = "127.0.0.1",
    port: int = 8000,      # 0 = auto free port
    log_level: str = "warning",
    unvicorn_log_level: str = "warning",
    return_container: bool = False,
) -> str | tuple[str, Any]:
    """Start the AetherGraph sidecar server in a background thread."""
```

**Description:**

Start the sidecar server in a **background thread** and install runtime services. This is safe to call at the top of any script or notebook cell; if the server is already running, it simply returns the previously computed URL.

### Parameters

* `workspace: str = "./aethergraph_data"`

    * Filesystem **root directory** for AetherGraph data:

        * artifact storage
        * RAG indexes
        * logs
        * snapshots/state store
        * any other on-disk runtime data
    * Use an absolute or project‑relative path; it will be created if missing.

* `host: str = "127.0.0.1"`

    * Host interface for the HTTP server (e.g., `"0.0.0.0"` to expose externally).

* `port: int = 8000`

    * Desired port.
    * If `port == 0`, a free port is chosen automatically.

* `log_level: str = "warning"`

    * Application log level (used by `create_app`, e.g., `"info"`, `"debug"`, `"warning"`).

* `unvicorn_log_level: str = "warning"`

     * Log level passed to Uvicorn’s `Config` (note: parameter name uses the existing spelling in code).

* `return_container: bool = False`

    * If `False` (default): return only the **base URL** as `str`.
    * If `True`: return a tuple `(url, container)` where `container` is the installed services container (`app.state.container`).

### Returns

* `str` – Base URL of the sidecar server (e.g., `"http://127.0.0.1:8001"`).
* or `(str, container)` when `return_container=True`.

### Behavior & notes

* **Idempotent:** If called multiple times in the same process, only the first call actually starts the server; later calls return the same `_url`.
* Runs uvicorn in a separate thread (`"aethergraph-sidecar"`) with its own event loop.
* Installs the services container for the process, so `current_services()`, `context.llm()`, `context.channel()`, etc. all work.
<!-- * Registers the **web UI channel** via `install_web_channel(app)` so you can connect from a browser. -->

---

## 2. `start_server_async` – async-friendly wrapper

```python
async def start_server_async(**kw) -> str:
    """Async-friendly wrapper; still uses a thread to avoid clashing with caller loop."""
```

**Description:**

Async wrapper around `start_server(...)`. It still starts Uvicorn in a **thread**, but exposes an `async` signature so you can `await` it from async code.

### Parameters

* `**kw` – Same keyword arguments as `start_server(...)` (`workspace`, `host`, `port`, etc.).

### Returns

* `str` – Base URL of the sidecar server.

**Notes:**

* Useful in async applications where you want to start the sidecar without blocking the existing event loop.

---

## 3. `stop_server` – optional shutdown helper

```python
def stop_server() -> None:
    """Optional: stop the background server (useful in tests)."""
```

**Description:**

Request a clean shutdown of the background Uvicorn thread and reset internal globals.

### Parameters

* —

### Returns

* `None`

### Behavior & notes

* If the server was **never started**, this is a no-op.
* Sets an internal `_shutdown_flag`, which the background loop polls; once set, the server’s `should_exit` flag is toggled and the main serve task finishes.
* Joins the server thread (up to 5 seconds) and clears `_started`, `_server_thread`, `_url`, and `_shutdown_flag`.
* Particularly useful for:

  * **Unit tests / integration tests** where you need to bring up and tear down the sidecar.
  * Long‑running notebooks where you want to restart with a fresh workspace or settings.

---

## 4. When to use the sidecar

You should start the sidecar server when you need:

* **External channels** beyond the console (Slack, web UI, etc.).
* **Resumable runs** and centralized state store / snapshots.
* A shared services container for multiple processes or adapters.

For purely local, one‑off experiments that only use `run_async` and `context` from a single process, you *can* rely on the default container (via `ensure_services_installed`). But for anything interactive or multi‑channel, `start_server(...)` is the recommended entrypoint.
