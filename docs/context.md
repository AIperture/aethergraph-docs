# Context Overview

**Context** is the lightweight runtime handle your tools/agents receive at execution time. It encapsulates the current **run/graph/node scope** and provides access to built‑in **services** (channels, memory, artifacts, kv, LLM, RAG, MCP, logger, continuations, clock, etc.) via concise helper methods.

> In short: **do your work with plain Python**, and when you need IO, state, or orchestration, call `context.<service>()`.

---

## Quick start
```python
from aethergraph import graph_fn

@graph_fn(name="hello_context")
async def hello_context(*, context):
    await context.channel().send_text("Hello from AetherGraph!")
    await context.memory().write_result(
        topic="hello",
        outputs=[{"name":"msg","kind":"text","value":"hello"}],
        tags=["demo"],
    )
    log = context.logger()
    log.info("done", extra={"stage": "finish"})
```

---

## What the Context contains
Each `NodeContext` carries stable identifiers and bound services for the current execution scope.

```python
@dataclass
class NodeContext:
    run_id: str
    graph_id: str
    node_id: str
    services: NodeServices  # wiring for all built‑ins
```

**IDs**
- **run_id** — unique per execution run
- **graph_id** — which graph this node belongs to
- **node_id** — unique node invocation id

---

## Core methods (one‑liners)
| Method | Purpose |
|---|---|
| `context.channel(key: str | None = None)` | Message & interaction bus (text, buttons, files, streaming, progress). Defaults to configured channel; pass a key to target another (e.g., `"slack:#lab"`). |
| `context.memory()` | Session/run memory façade (record events, write typed results, query recent/indices, rolling & episode summaries, optional RAG helpers). |
| `context.artifacts()` | Artifact store/index façade (stage/save/write files/dirs, search/best, pin). |
| `context.kv()` | Small, transient key–value store for coordination and short‑lived caches. |
| `context.llm(profile="default")` | LLM client for `chat()` and `embed()`; switch keys via `context.llm_set_key(...)`. |
| `context.rag()` | RAG façade: create corpora, upsert docs, search/retrieve, answer with citations. |
| `context.mcp(name)` | MCP client to call external tool servers (stdio/ws/http), list/read resources. |
| `context.logger()` | Scoped Python logger with `{run_id, graph_id, node_id}` auto‑injected. |
| `context.continuations()` | Access to continuation store (usually used indirectly via `channel().ask_*`). |
| `context.clock()` | Clock/time helpers (scheduling, timestamps) if bound. |

> If a service is not configured in your runtime, its accessor raises a clear error (e.g., `LLMService not available`).

---

## Typical patterns

### 1) Ask → Wait → Continue
```python
text = await context.channel().ask_text("Provide a dataset path")
# runtime yields, persists a continuation; resumes with user input
```

### 2) Stream + progress
```python
async with context.channel().stream() as s:
    await s.delta("Parsing… ")
    await s.delta("OK. ")
async with context.channel().progress(title="Training", total=100) as p:
    for i in range(0, 101, 5):
        await p.update(current=i)
```

### 3) Artifacts + memory
```python
art = await context.artifacts().save(path="/tmp/report.pdf", kind="report", labels={"exp":"A"})
await context.memory().write_result(
    topic="report",
    outputs=[{"name":"uri","kind":"uri","value": art.uri}],
)
```

### 4) RAG answer using LLM
```python
hits = await context.rag().search("notes", query="What is MTF?", k=5)
ans = await context.rag().answer("notes", question="What is MTF?", style="concise")
await context.channel().send_text(ans["answer"]) 
```

### 5) External tools via MCP
```python
res = await context.mcp("ws").call("search", {"q": "tolerance analysis", "k": 5})
```

---

## Choosing a channel
- By default, `context.channel()` resolves to the runtime’s configured default (e.g., console).
- Pass a **channel key** to target a specific adapter:
  - `"console:stdin"`
  - `"slack:#research"` or `"slack:@alice"`
  - `"telegram:chat:<id>"`
- You can override per call: `context.channel("slack:#lab").send_text("hi")` or `context.channel().send_text("hi", channel="slack:#lab")`.

---

## Error handling & logging
- Service calls raise `RuntimeError` if the service is missing; wire them at server startup.
- Use `context.logger().exception("...")` inside `except` blocks to capture tracebacks.
- Prefer logging artifact URIs and metrics over large payloads.

---

## Server wiring (very short)
Make services available before running graphs/tools.
```python
# Pseudo-bootstrap
services = build_runtime_services(
    logger=StdLoggerService.build(),
    llm=make_llm_service(),
    memory=make_memory_facade_factory(),
    artifacts=make_artifact_facade(),
    kv=EphemeralKV(prefix="ag:"),
    rag=make_rag_facade(),
    mcp=make_mcp_service(),
)
start_server(services)
```

---

## Philosophy
- **Python‑first**: context calls are **helpers**, not a DSL. Keep your logic in plain Python.
- **Minimal surface**: each service exposes a small, composable API.
- **Swappable backends**: you can replace services (e.g., LLM provider, KV backend) without changing your tools.

---

## See also
- `context.channel()` — cooperative waits, streaming, progress
- `context.memory()` — event log, typed results, summaries, RAG helpers
- `context.artifacts()` — CAS storage + search
- `context.llm()` — chat & embeddings
- `context.rag()` — corpora & QA
- `context.mcp()` — external tool bridges
- `context.kv()` — transient coordination
- `context.logger()` — structured logs