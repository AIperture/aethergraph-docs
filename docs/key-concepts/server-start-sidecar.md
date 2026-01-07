# Server (Sidecar) Overview

The **AetherGraph sidecar** is a lightweight process that boots your runtime services and exposes a tiny HTTP/WebSocket surface for **adapters** (Slack, Web, Telegram, …) and **continuations** (event‑driven waits). With the server, you can: 

* **Real interactions**: `ask_text/approval/files` from Slack/Web/Telegram and resume the run
* **Centralized service wiring**: artifacts, memory, kv, llm, rag, mcp, logger
* **A shared control plane**: health, upload hooks, progress streams, basic inspect

> **In short:** keep your agents plain Python; start the sidecar for **I/O, resumability, and shared services**.
> Always start the server before registering services and running agents

---

## Quick Start

```python
from aethergraph import start_server, stop_server

url = start_server()  # FastAPI + Uvicorn in a background thread
print("sidecar:", url)  # Default to 127.0.0.1:8745

# ... run @graph_fn / @graphify normally ...

stop_server()  # optional (handy in tests/CI)
```

**Tips**

* If using Aethergraph UI, keep the same port everytime to retrieve the history and persist data. 
* Start it once per process; reuse the base URL across adapters/UI.

---

## What `start_server()` Does

1. **Load config & workspace** — resolve paths, secrets, and profiles; make the workspace if needed.
2. **Build & register services** — channels, artifacts (store/index), memory (hotlog/persistence/indices), kv, llm, rag, mcp, logger.
3. **Expose endpoints** —

    * **Continuations**: resume callbacks for `ask_text / ask_approval / ask_files`
    * **Adapters**: chat/events, uploads, progress streams

4. **Launch Uvicorn** — run the app in a background thread and return the **base URL**.
5. **Launch UI** -- start the UI when possible for inspection of graph and agent runs. 

> It is safe to use `start_server()` in Jupyter notebook
> When using UI, use CLI to serve the project with `--reload` for best DX.

---

## Minimal API

`start_server() -> str`

Starts the sidecar **in‑process** and returns the base URL.

`stop_server() -> None`

Stops the background server. Useful for teardown in tests/CI.

Full API for server management is listed [here](../reference/runtime-server.md)
