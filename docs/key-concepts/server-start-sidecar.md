# Server (Sidecar) Overview

The **AetherGraph sidecar** is a lightweight process that boots your runtime services and exposes a tiny HTTP/WebSocket surface for **adapters** (Slack, Web, Telegram, …) and **continuations** (event‑driven waits). You can run `@graph_fn` in pure Python without it (console only), but start the sidecar when you need:

* **Real interactions**: `ask_text/approval/files` from Slack/Web/Telegram and resume the run
* **Centralized service wiring**: artifacts, memory, kv, llm, rag, mcp, logger
* **A shared control plane**: health, upload hooks, progress streams, basic inspect

> **In short:** keep your agents plain Python; start the sidecar for **I/O, resumability, and shared services**.

---

## Quick Start

```python
from aethergraph.server import start, stop

url = start(host="127.0.0.1", port=0)  # FastAPI + Uvicorn in a background thread
print("sidecar:", url)

# ... run @graph_fn / @graphify normally ...

stop()  # optional (handy in tests/CI)
```

**Tips**

* Use `port=0` to pick a free port automatically. 
* Start it once per process; reuse the base URL across adapters/UI.

---

## What `start()` Does

1. **Load config & workspace** — resolve paths, secrets, and profiles; make the workspace if needed.
2. **Build & register services** — channels, artifacts (store/index), memory (hotlog/persistence/indices), kv, llm, rag, mcp, logger.
3. **Expose endpoints** —

    * **Continuations**: resume callbacks for `ask_text / ask_approval / ask_files`
    * **Adapters**: chat/events, uploads, progress streams

4. **Launch Uvicorn** — run the app in a background thread and return the **base URL**.

---

## Minimal API

`start(host="127.0.0.1", port=0, workspace=None, log_level="info") -> str`

Starts the sidecar **in‑process** and returns the base URL.

`start_async(...) -> str`

Async‑friendly variant (still hosts the server in a thread), convenient inside async apps/tests.

`stop() -> None`

Stops the background server. Useful for teardown in tests/CI.

---

## When to Use the Sidecar

* **Event‑driven waits** from non‑console adapters (Slack/Web/Telegram)
* **File uploads & artifact routing** from a browser/UI
* **Progress/streaming** to external UIs
* **Shared settings & service wiring** across multiple agents

You **don’t** need it for: simple console demos, unit tests without external I/O, or pure compute.

---

## Common Issues & Fixes

* **No reply after `ask_text()`** → The adapter isn’t posting **resume** events to the sidecar. Verify the sidecar base URL and token in the adapter config.
* **CORS blocked** in web UI → Allow your UI origin in sidecar settings (CORS `allow_origins`).
* **Port busy** → Use `port=0` or pick an open port.
* **Service not available** (e.g., LLM/RAG) → Ensure your `create_app()` wires those services or provide the required credentials.

---

## Notes on Architecture

* The sidecar runs its **own event loop/thread**; your agents/tools run on the **main loop**. They communicate via the ChannelBus/HTTP hooks.
* External context services you register as **instances** run on the **main loop**, so `asyncio` locks work as expected.

---

## Takeaways

* The sidecar is your **local control plane**: services + continuations + adapters.
* Start it with `start()` when you need **interactions, persistence, or shared wiring**.
* Your agent code stays **plain Python** either way; the sidecar simply adds I/O and resumability.
