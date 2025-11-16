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




<details markdown="1">
<summary>open_session(*, run_id: str | None = None, graph_id: str = "adhoc", node_id: str = "adhoc", **rt_overrides)</summary>

**Description:** pen a temporary, fully wired `NodeContext` for ad‑hoc use.

**Inputs:**

* `run_id: str`
* `run_id: str`
* `node_id: str`
* `rt_overrides` — runtime overrides. See graph runner doc for details.

**Returns:**

* `None`

**Note:** Handles setup and implicit cleanup at exit.

</details>

<details markdown="1">
<summary>build_adhoc_context(*, run_id: str | None = None, graph_id: str = "adhoc", node_id: str = "adhoc", **rt_overrides)</summary>

**Inputs:**

* `run_id: str`
* `run_id: str`
* `node_id: str`
* `rt_overrides` — runtime overrides. See graph runner doc for details.

**Returns:** 

* `NodeContext` (caller manages any cleanup).

</details>


---

## Notes & gotchas

* `open_session()` gives you a **real** `NodeContext` bound to a throwaway run/graph/node. Treat it like a normal node.
* If you rely on external adapters (Slack/Telegram/Web UI) or resumable waits, ensure the **sidecar server is running**.
* For long‑lived scripting, prefer `open_session()`; reach for `build_adhoc_context()` only when you need total control.
* Services which are not configured (e.g., RAG, MCP) will raise a clear `RuntimeError`. Wire them via your runtime config or server startup.
