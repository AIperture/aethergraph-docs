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

???+ quote "start_server(*, workspace, host, port, log_level, ...)"
    ::: aethergraph.server.start.start_server
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

---

## 2. start server via CLI
???+ quote "CLI start server"
    ::: aethergraph.__main__.main
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  
