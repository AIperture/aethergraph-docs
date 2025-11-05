# Context Overview

**Context** is the lightweight runtime handle that your **agents** and **tools** receive at execution time. It represents the current **run**, **graph**, and **node** scope, and provides access to the runtime’s built‑in **services** (like channels, memory, artifacts, etc.) through a clean, composable Python interface.

> **In essence:** Context is what lets AetherGraph “come alive.” It connects your pure Python logic to external I/O, state, orchestration, and AI‑augmented services — without introducing a new DSL.

---

## Why Context Matters

AetherGraph’s design principle is *Python‑first orchestration*. The context system enables this by:

* **Decoupling logic from infrastructure** – you can build tools and agents that call `context.<service>()` without caring about the backend implementation.
* **Maintaining provenance and state** – each call is aware of its `run_id`, `graph_id`, and `node_id`, so results and events are recorded with full traceability.
* **Enabling orchestration without overhead** – context manages message passing, persistence, and coordination automatically.
* **Integrating optional intelligence** – attach LLMs, RAG corpora, or external MCP tool servers only when needed.

Ultimately, `NodeContext` is what transforms plain async functions into **interactive, stateful agents** — giving you the ability to talk, remember, reason, and orchestrate in one consistent runtime.

---

## Quick Start

```python
from aethergraph import graph_fn

@graph_fn(name="hello_context")
async def hello_context(*, context):
    await context.channel().send_text("Hello from AetherGraph!")
    await context.memory().write_result(
        topic="hello",
        outputs=[{"name": "msg", "kind": "text", "value": "hello"}],
        tags=["demo"],
    )
    context.logger().info("done", extra={"stage": "finish"})
```

---

## What the Context Contains

Each `NodeContext` carries stable identifiers and bound services for the current execution scope.

```python
@dataclass
class NodeContext:
    run_id: str
    graph_id: str
    node_id: str
    services: NodeServices  # wiring for all built‑ins
```

**Identifiers**

* **run_id** — unique per execution run
* **graph_id** — which graph this node belongs to
* **node_id** — unique node invocation id

---

## Context Methods

AetherGraph divides context services into **core**, **optional**, and **utility** groups.

### Core Services

| Method                    | Purpose                                                                                     |                                                                                                        |
| ------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `context.channel(key: str | None = None)`                                                                               | Message & interaction bus (text, buttons, files, streaming, progress). Defaults to configured channel. |
| `context.memory()`        | Session/run memory façade — record events, write results, query history, build RAG indices. |                                                                                                        |
| `context.artifacts()`     | Artifact store/index façade — save or retrieve files, manage experiment outputs.            |                                                                                                        |
| `context.kv()`            | Transient key–value store for coordination, small caches, and ephemeral synchronization.    |                                                                                                        |
| `context.logger()`        | Structured Python logger with `{run_id, graph_id, node_id}` automatically injected.         |                                                                                                        |

### Optional Services (require extra configuration)

These depend on environment/API keys and are only available if configured at runtime.

| Method                           | Purpose                                                                                                |
| -------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `context.llm(profile="default")` | LLM client for `chat()` or `embed()` operations; plug in OpenAI, Anthropic, or local models.           |
| `context.rag()`                  | Retrieval‑augmented generation façade; create corpora, upsert docs, search, and answer with citations. |
| `context.mcp(name)`              | MCP client to connect to external tool servers via stdio/websocket/HTTP.                               |

### Utility Helpers

| Method                    | Purpose                                                                      |
| ------------------------- | ---------------------------------------------------------------------------- |
| `context.clock()`         | Clock/time helpers for timestamps, scheduling, and delays.                   |
| `context.continuations()` | Access to continuation store (usually used indirectly by `channel().ask_*`). |

> If a service is unavailable, its accessor raises a clear error (e.g., `LLMService not available`). Configure them at startup or through the environment.

---

## Typical Patterns

### 1) Ask → Wait → Continue

```python
text = await context.channel().ask_text("Provide a dataset path")
# runtime yields, persists a continuation, resumes with user input
```

### 2) Stream + Progress

```python
async with context.channel().stream() as s:
    await s.delta("Parsing… ")
    await s.delta("OK. ")

async with context.channel().progress(title="Training", total=100) as p:
    for i in range(0, 101, 5):
        await p.update(current=i)
```

### 3) Artifacts + Memory

```python
art = await context.artifacts().save(path="/tmp/report.pdf", kind="report", labels={"exp":"A"})
await context.memory().write_result(
    topic="report",
    outputs=[{"name": "uri", "kind": "uri", "value": art.uri}],
)
```

### 4) RAG Answer using LLM

```python
hits = await context.rag().search("notes", query="What is MTF?", k=5)
ans = await context.rag().answer("notes", question="What is MTF?", style="concise")
await context.channel().send_text(ans["answer"])
```

### 5) External Tools via MCP

```python
res = await context.mcp("ws").call("search", {"q": "tolerance analysis", "k": 5})
```

---

## Custom Context Services

AetherGraph’s context system is **extensible**. You can register your own service and make it available as `context.<your_service>()`. This allows you to:

* Extend the runtime with **custom persistence layers**, schedulers, or storage models.
* Encapsulate **domain‑specific APIs** (e.g., simulation, materials database, experiment tracker).
* Implement **persistent stages** that survive restarts or act as bridges between distributed components.

Custom contexts are defined and registered via `register_context_service()` (see the *External Context* section for details and benefits).

---

## Philosophy

* **Python‑first**: context calls are helpers, not a DSL. Keep logic in plain Python.
* **Minimal surface**: each service has a small, composable API.
* **Composable orchestration**: mix local and remote services freely.
* **Swappable backends**: replace services (e.g., LLM provider, KV backend) without changing agent code.

---

## See Also

* `context.channel()` — cooperative waits, streaming, progress
* `context.memory()` — event log, typed results, summaries, RAG helpers
* `context.artifacts()` — CAS storage + search
* `context.llm()` — chat & embeddings
* `context.rag()` — corpora & QA
* `context.mcp()` — external tool bridges
* `context.kv()` — transient coordination
* `context.logger()` — structured logs
