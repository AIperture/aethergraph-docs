# Core Services at a Glance

AetherGraph’s **context** provides a unified interface to access runtime services — from lightweight coordination to AI-powered reasoning. This page offers a concise overview of these services with minimal examples, showing what’s available beyond **Channels, Artifacts, and Memory**.

> **Goal:** Keep your logic pure-Python and call `context.<service>()` only when you need I/O, coordination, or intelligence.

---

## 1. KV — Ephemeral Coordination

A lightweight key–value store for transient synchronization, small caches, and locks.

```python
@graph_fn(name="kv_demo", outputs=["ok"])
async def kv_demo(*, context):
    kv = context.kv()
    await kv.set("stage", "preflight", ttl_s=300)
    stage = await kv.get("stage")  # "preflight"
    return {"ok": stage == "preflight"}
```

**Default backend:** ephemeral in-memory KV.
**Use for:** feature flags, shared state, short coordination.
**See:** KV Service Deep Dive →

---

## 2. Logger — Structured Logs with Provenance

Structured Python logger that automatically includes `{run_id, graph_id, node_id}` in every record.

```python
@graph_fn(name="log_demo", outputs=["done"])
async def log_demo(*, context):
    log = context.logger()
    log.info("starting", extra={"component": "ingest"})
    try:
        ...
        log.info("finished", extra={"component": "ingest"})
        return {"done": True}
    except Exception:
        log.exception("ingest failed")
        return {"done": False}
```

**Default backend:** standard Python logging.
**Use for:** lifecycle traces, metrics, structured error reports.
**See:** Logging Deep Dive →

---

## 3. LLM — Unified Chat & Embeddings *(optional)*

An abstraction over multiple model providers. Requires configuration (API keys, profile).

```python
@graph_fn(name="llm_demo", outputs=["reply"])
async def llm_demo(prompt: str, *, context):
    llm = context.llm(profile="default")
    msg = await llm.chat([{"role": "user", "content": prompt}])
    return {"reply": msg["content"]}
```

**Use for:** chat completions, summarization, embeddings.
**Backend:** pluggable clients (OpenAI, Anthropic, local).
**See:** LLM Service Deep Dive →

---

## 4. RAG — Long-Term Semantic Recall *(optional)*

Build searchable corpora from events or docs, then retrieve or answer with citations. Requires an LLM for answering.

```python
@graph_fn(name="rag_demo", outputs=["answer"])
async def rag_demo(q: str, *, context):
    mem = context.memory()
    corpus = await mem.rag_bind(scope="project")
    await mem.rag_promote_events(corpus_id=corpus)
    ans = await mem.rag_answer(corpus_id=corpus, question=q)
    return {"answer": ans["answer"]}
```

**Default backend:** FAISS (local).
**Use for:** semantic search and retrieval-augmented QA.
**See:** RAG Deep Dive → · External Context →

---

## 5. MCP — External Tool Bridges

Connect to external tool servers over stdio, WebSocket, or HTTP using the **Model Context Protocol (MCP)**.

```python
@graph_fn(name="mcp_demo", outputs=["hits"])
async def mcp_demo(*, context):
    ws = context.mcp("ws")  # adapter name
    res = await ws.call("search", {"q": "tolerance analysis", "k": 3})
    return {"hits": res.get("items", [])}
```

**Use for:** safe integration with non-Python tools and structured external APIs.
**See:** MCP Deep Dive →

---

## Takeaways

* All services are accessible through `context.<service>()` — no imports or globals.
* Core defaults (KV, Logger) work locally out of the box.
* LLM, RAG, and MCP are optional; enable them via environment or external context configuration.
* Backends are swappable — you can move from local to managed services without changing agent code.

**Next:** Explore [Channels & Interaction →](../channels.md) or [Artifacts & Memory →](../artifacts_memory.md)
