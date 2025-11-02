# AetherGraph — Server (Sidecar) Overview

The **AetherGraph server** is a lightweight **sidecar** that wires up all runtime services (channels, memory, artifacts, KV, LLM, RAG, MCP, logging, etc.) and exposes a small HTTP/WebSocket surface for adapters and tools. You can run AetherGraph without the server, but the sidecar makes it easy to:

- Use GUI/chat adapters (Slack/Telegram/Console UI) that push events back to your runs
- Host continuation callbacks for `ask_text()` / `ask_approval()`
- Centralize service wiring (secrets, paths, corpora, registries)
- Inspect/trace runs, artifacts, and health in one place

> Think of it as your **local control plane** so your graph functions can stay plain Python.

---

## Quick Start
```python
from aethergraph.server import start, stop

# 1) Start the sidecar (in a background thread) and get its base URL
url = start(host="127.0.0.1", port=0)   # port=0 → auto-pick a free port
print("AetherGraph sidecar:", url)

# 2) Run your graph functions as usual
from aethergraph import graph_fn

@graph_fn(name="hello")
async def hello(name: str, *, context):
    await context.channel().send_text(f"Hi {name}")
    return {"greeting": f"Hello, {name}"}

# ... elsewhere ...
# res = await hello(name="ZC")

# 3) (Optional) Stop when done (tests/CLI)
stop()
```

---

## API — `start()` / `start_async()` / `stop()`

### start
```
start(*, workspace: str = "./aeg_workspace", session_id: str | None = None,
      host: str = "127.0.0.1", port: int = 0, log_level: str = "warning") -> str
```
Start the sidecar in a **background thread**. Safe to call at the top of scripts or notebook cells.

**Parameters**

- **workspace** (*str*) – Root directory for runtime state (artifacts, logs, corpora, temp files). Auto‑created.

- **session_id** (*str, optional*) – Override the logical session. If `None`, the runtime will create one.

- **host** (*str*) – Bind address (defaults to loopback).

- **port** (*int*) – `0` picks a free port automatically; otherwise bind an explicit port.

- **log_level** (*str*) – Uvicorn log level (e.g., `"info"`, `"warning"`).

**Returns**  
*str* – Base URL, e.g., `"http://127.0.0.1:54321"`.

### start_async
```
start_async(**kwargs) -> str
```
Async‑friendly wrapper that still runs the server in a thread to avoid clashing with your event loop.

### stop
```
stop() -> None
```
Signal the background server to shut down and join its thread (useful in tests/CI or ephemeral scripts).

---

## Why a sidecar?
- **Continuations**: `context.channel().ask_*` creates a continuation token and waits for a resume callback; the server receives user replies (Slack/Telegram/HTTP) and wakes your run.
- **Adapters**: chat/file/progress adapters connect over HTTP/WS to publish events (`agent.message`, `agent.progress.*`, uploads) into your run.
- **Central config**: one place to load settings, secrets, workspace paths, and register services (LLM, RAG, MCP, artifact store, memory backends).
- **Inspection**: optional health and tracing endpoints (depending on your app factory) to debug runs locally.

---

## What `start()` actually does
1. Loads app settings (`load_settings()`), installs them as current (`set_current_settings(...)`).
2. Builds a FastAPI app via `create_app(workspace=..., cfg=...)` — this registers services and routes.
3. Picks a free port if `port=0` and **launches Uvicorn** in a background thread (non‑blocking).
4. Returns the base URL so other components (e.g., WS/HTTP MCP clients) can connect.

---

## Typical usage patterns

### Notebooks & quick scripts
```python
url = start(port=0)
# … run several cells that use context.channel()/continuations
# restart kernel or call stop() when done
```

### Long‑running dev server
- Call `start(host="0.0.0.0", port=8787, log_level="info")` once at process start.
- Point Slack/Telegram adapters or local tools at `http://localhost:8787`.

### Tests/CI
```python
url = start(port=0)
try:
    # run test suite that uses continuations/artifacts
    ...
finally:
    stop()
```
<!-- 
---

## Configuration & environment
Settings are loaded via `load_settings()` and used in `create_app(...)`. Common knobs include:
- **Paths**: workspace root, artifact/log dirs
- **Services**: which LLM/RAG/MCP/KV backends to enable and with what credentials
- **Security**: allowed origins, tokens/secrets for inbound adapters

> For portable demos, you can also imperatively construct individual services and register them into the runtime; the server just gives you a consistent place to do so. -->

---

## Interop with context services
Once the sidecar is up, graph functions can rely on bound services:

- `context.channel()` – routes via the server to your chat adapters

- `context.artifacts()` – saves to the workspace CAS under the sidecar

- `context.memory()` – hotlog/persistence live alongside the server’s config

- `context.rag()` – corpora root under workspace; embedders/indices wired here

- `context.mcp(...)` – WS/HTTP MCP clients often target sidecar endpoints

---

## Security notes
- Default bind is `127.0.0.1` (local only). Use `0.0.0.0` only in trusted networks.
- Protect WS/HTTP endpoints behind auth headers/tokens if exposing beyond localhost.
- Never log plaintext API keys; prefer a Secrets store.

---

## Troubleshooting
- **Port already in use**: pass `port=0` or another free port.
- **Nothing happens after ask_text()**: ensure the chat adapter posts replies to the sidecar (correct base URL / token).
- **No LLM/kv/rag configured**: your `create_app()` must wire these services (or the accessors will raise "… not available").
- **Jupyter hangs on restart**: call `stop()` before restarting the kernel, or rely on kernel shutdown to terminate the thread.

---

## Minimal adapter sketch (optional)
```python
# Example: WebSocket adapter connecting to sidecar URL
a_sync_ws_client.connect(f"{url.replace('http','ws')}/events", headers={"Authorization": "Bearer demo"})
# publish OutEvent / listen for Continuation notifications
```

---

## Summary
Run the **sidecar server** to centralize runtime services, handle continuations/adapters, and keep your graph functions clean. Use `start()` to launch in‑process, `start_async()` in async apps, and `stop()` for tests/CI. Configure paths and services once; build everything else in plain Python.