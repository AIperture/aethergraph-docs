# Context Services Overview

**Context** is the lightweight runtime handle that every **agent** and **tool** receives during execution. It represents the active **run**, **graph**, and **node** scope and exposes AetherGraph’s built-in **runtime services**—channels, memory, artifacts, logs, and more—through a clean, Pythonic interface.

> **In short:** Context is what makes an AetherGraph program “alive.” It bridges your pure Python logic with interactive I/O, persistence, orchestration, and AI-powered capabilities—without introducing a new DSL or framework-specific syntax.

---

## 1. Why Context Matters

AetherGraph’s guiding principle is **Python-first orchestration**. The context system makes that possible by providing a unified way to connect logic and infrastructure.

**Core benefits:**

* **Decoupled logic:** Agents and tools can call `context.<service>()` without worrying about back-end details or deployment environment.
* **Automatic provenance:** Each call carries its `run_id`, `graph_id`, and `node_id`, ensuring full traceability.
* **Zero-friction orchestration:** Handles message passing, persistence, and coordination transparently.
* **Optional intelligence:** Attach LLMs, RAG corpora, or MCP servers only when needed—no dependencies until configured.

In practice, `NodeContext` turns plain async functions into **interactive, stateful agents** that can communicate, remember, reason, and orchestrate—all from Python.

---

## 2. Quick Start

```python
from aethergraph import graph_fn

@graph_fn(name="hello_context")
async def hello_context(*, context):
    await context.channel().send_text("Hello from AetherGraph!")
    await context.memory().record(
        kind="chat_data",
        data={"message": "Hello from AetherGraph!"},  
    ) # remember key events
    context.logger().info("finished", extra={"stage": "done"})
    return {"ok": True}
```

> Each call operates within a specific node scope. The runtime automatically provides `run_id`, `graph_id`, and `node_id` to maintain context and provenance.

---

## 3. Context Structure

Each `NodeContext` carries stable identifiers and bound service references.

```python
@dataclass
class NodeContext:
    run_id: str
    graph_id: str
    node_id: str
    services: NodeServices  # all bound runtime services
```

**Identifiers**

* **run_id** — unique per execution run.
* **graph_id** — identifies which graph the node belongs to.
* **node_id** — unique ID for the node invocation.

---

## 4. Context Services

AetherGraph organizes its context services into **core**, **optional**, and **utility** layers.

### Core Services

| Method                    | Purpose                                                                                     |                                                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `context.channel()`       | Message and interaction bus — send/receive text/approval/files, show progress, or streaming events. |
| `context.memory()`        | Memory façade — record events, write typed results, query history, or manage RAG-ready logs.      |                                                                                                                            |
| `context.artifacts()`     | Artifact store façade — save/retrieve files, track outputs, and query files by labels/metrics artifacts. |                                                                                                                            |
| `context.kv()`            | Lightweight key–value store for ephemeral coordination and small caches.                    |                                                                                                                            |
| `context.logger()`        | Structured logger with `{run_id, graph_id, node_id}` metadata automatically included.       |                                                                                                                            |

### Optional Services (config-dependent)

Optional services require API keys or runtime configuration. They are injected dynamically when available.

| Method                           | Purpose                                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `context.llm()` | Access an LLM client for chat, embeddings, or raw apis access (OpenAI, Anthropic, Google, or local backends, etc.).                  |
| `context.rag()`                  | Retrieval-augmented generation façade — build corpora, upsert documents, search, and answer queries. |
| `context.mcp()`              | Connect to external MCP tool servers via stdio, WebSocket, or HTTP.                                  |

### Utility Helpers

| Method                    | Purpose                                                                                       |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| `context.clock()`         | Clock utilities for timestamps, delays, and scheduling.                                       |
| `context.continuations()` | Access continuation store; used internally for dual-stage waits (`ask_text`, `ask_approval`). |

> If a service is unavailable, its accessor raises a clear runtime error (e.g., `LLMService not available`). Configure them globally or per-environment to enable.

---

## 5. Typical Patterns

### 1 Ask → Wait → Resume

```python
text = await context.channel().ask_text("Provide a dataset path") 
# wait for external input and resume when done
await context.channel().send(f"you provided the dataset path {text}")
```


### 2 Artifacts + Memory

```python
# save and return an artifact 
art = await context.artifacts().save(path="/tmp/report.pdf", kind="report", labels={"exp": "A"}) 
# save and return an event  
evt = await context.memory().record(kind="checkpoint", data={"info": "experiment A saved"}) 

# In later stage or other agent:
# list all previous saved art with kind == "report"
arts = await context.artifacts().search(kind="report")      
# list past 100 memory with kinds include "checkpoint" 
evts = await context.memory().recent(kinds=["checkpoint"], limit=100)    
```

### 4 RAG + LLM Answers

```python
# ingest data into vector DB
corpus_id = "notes"
_ = await context.rag().upsert_docs(corpus_id, docs)  # your documentations in a list 

# later search/answer
hits = await context.rag().search(corpus_id, query="Tool used in experiment #A2?", k=5)
ans = await context.rag().answer(corpus_id, question="What is the best iteration and what is the loss?", style="concise")
await context.channel().send_text(ans["answer"])
```

### 5 External Tools via MCP

```python
res = await context.mcp("ws").call("search", {"q": "tolerance analysis", "k": 5})
```

---

## 6. Custom Context Services

The context system is **fully extensible**. You can define your own service and expose it via `context.<name>()` using `register_context_service()`.

**Use cases:**

* Add domain-specific APIs (e.g., simulation, materials DB, experiment tracking).
* Provide custom persistence or distributed coordination layers.
* Implement bridges between external systems (e.g., job schedulers, cloud storage, or lab devices).

See *External Context Services* for API details and examples.

---

## 7. Design Philosophy

* **Python-first:** use direct calls, not DSL syntax.
* **Minimal surface:** each service follows a small, composable API.
* **Composable orchestration:** mix local and remote services freely.
* **Swappable backends:** replace LLM, KV, or artifact backends without touching agent logic.

---

## See Also

* [`context.channel()`] — cooperative waits, streaming, progress updates
* [`context.memory()`] — event log, typed results, summaries, and RAG helpers
* [`context.artifacts()`] — content-addressable storage and retrieval
* [`context.llm()`] — chat, completion, and embeddings
* [`context.rag()`] — corpus creation and QA retrieval
* [`context.mcp()`] — bridges to external tool servers
* [`context.kv()`] — transient coordination and state passing
* [`context.logger()`] — structured
