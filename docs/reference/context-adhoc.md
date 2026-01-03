# Using `context` outside a graph (Ad‑hoc sessions)

Sometimes you want a fully‑featured `NodeContext` **without** constructing a graph—e.g., quick scripts, notebooks, data prep, or admin tasks. AetherGraph exposes an async helper you can import from `aethergraph.runtime`:

* `open_session(...)` – **async context manager** that yields a temporary, fully wired `NodeContext` and cleans up afterward.

> These sessions are “single‑node” and aren’t scheduled like a graph run, but they provide the same services: `context.llm()`, `context.artifacts()`, `context.memory()`, `context.kv()`, `context.logger()`, `context.rag`, `context.mcp()`, and any **custom services** you’ve registered.

---

## Quick Start

```python
from aethergraph.runtime import open_session

# Recommended: context manager form (handles cleanup)
async with open_session(run_id="adhoc-demo", graph_id="adhoc", node_id="adhoc") as context:
    context.logger().info("hello from adhoc")
    txt, _ = await context.llm().chat([
        {"role": "user", "content": "Give me a haiku about photons."}
    ])
    print(txt)
```

### Common parameters

* `run_id: str | None` — logical session/run identifier (default: auto‑generated)
* `graph_id: str` — namespace label for this session (default: `"adhoc"`)
* `node_id: str` — node label within the session (default: `"adhoc"`)
* `**rt_overrides` — advanced runtime knobs you can pass through (e.g., `max_concurrency`, service injections)

> **Tip:** Start your sidecar server (`start_server(...)`) first if you plan to use external channels, resumable waits, or any service that relies on the sidecar’s wiring.

---

## API Reference

???+ quote "open_session(run_id, graph_id, node_id, **rt_overrides)"
    ::: aethergraph.core.runtime.ad_hoc_context.open_session
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "build_adhoc_context(run_id, graph_id, node_id, **rt_overrides)"
    ::: aethergraph.core.runtime.ad_hoc_context.build_adhoc_context
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

---

## Notes & gotchas

* `open_session()` gives you a **real** `NodeContext` bound to a throwaway run/graph/node. Treat it like a normal node.
* If you rely on external adapters (Slack/Telegram/Web UI) or resumable waits, ensure the **sidecar server is running**.
* For long‑lived scripting, prefer `open_session()`; reach for `build_adhoc_context()` only when you need total control.
* Services which are not configured (e.g., RAG, MCP) will raise a clear `RuntimeError`. Wire them via your runtime config or server startup.
