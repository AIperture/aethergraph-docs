# Server (Sidecar) Overview

The **AetherGraph server** is a lightweight **sidecar** that boots your runtime services and exposes a tiny HTTP/WebSocket surface for adapters and continuations. You can run `@graph_fn` without it (pure Python, console I/O), but the sidecar is required for:

* **Event‑driven waits** (`ask_*` via Slack/Telegram/Web UI beyong Console → resume your run)
* **Centralized service wiring** (artifacts, memory, kv, rag, llm, mcp)
* **Global scheduling** for `@graphify` pipelines

> In short: start the sidecar when you need real interactions, resumability, or a shared control plane.

---

## Quick Start

```python
from aethergraph.server import start, stop

url = start(host="127.0.0.1", port=0)  # launches FastAPI+Uvicorn in a background thread
print("sidecar:", url)

# ... run @graph_fn / @graphify normally ...

stop()  # optional (useful for tests/CI)
```

---

## What `start()` actually does

1. **Load config & workspace** (paths, secrets, profiles) and install them as current settings.
2. **Build services** and register them (channels, artifacts, memory hotlog/persistence/indices, kv, llm, rag, mcp, logger).
3. **Expose endpoints** for:
    * **Continuations** (resume callbacks for `ask_text/approval/files`),
    * **Adapters** (chat/events, uploads, progress),
    * **Health/inspect** (minimal status routes).

4. **Launch Uvicorn** in a background thread and return the **base URL**.

---

## Minimal API

### `start(...) -> str`

Starts the sidecar in‑process and returns the base URL.

* `workspace`: root dir for artifacts/logs/corpora (auto‑created)
* `host`, `port`: bind address; `port=0` picks a free port
* `log_level`: Uvicorn verbosity

### `start_async(...) -> str`

Async‑friendly variant (still runs the server in a thread).

### `stop() -> None`

Stops the background server (useful in tests/CI).

---

## When do I *not* need it?

* Pure `@graph_fn` runs that only print to **console** and don’t use `ask_*`, external channels, or global scheduling. Those run directly in Python’s event loop. 

## When do I *need* it?

* Any **interactive** or **resumable** flow (cooperative or dual‑stage waits).
* Using **Slack/Telegram/Web** channels or file uploads.
* Running **static DAGs** built with `@graphify` under the **global scheduler**.

If you don't know whether to use it, start the server anyway. 

---

## Security & Networking (short)

* Default bind: `127.0.0.1` (local only). Use `0.0.0.0` only on trusted networks.
* Put auth on WS/HTTP if exposed beyond localhost. Never log plaintext API keys.

---

## Troubleshooting (quick)

* **No reply after `ask_text()`** → adapter isn’t posting resumes to the sidecar URL/token.
* **CORS error from web UI** → allow the UI origin in sidecar settings.
* **Port busy** → pass `port=0` or another free port.
* **Services unavailable** → ensure your `create_app()` wires llm/rag/kv/etc., or use defaults.

---

## Takeaways

* The sidecar is your **local control plane**: services + continuations + adapters + global scheduling.
* Start it once with `start()`; keep your agents **plain Python**.
* Use it whenever you need **interactions, persistence, or scale**.
