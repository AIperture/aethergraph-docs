# Other Services Overview

AetherGraph’s **context** exposes a set of lightweight, composable runtime services that complement **Channels**, **Artifacts**, and **Memory**. Use them when your agent needs coordination, observability, or intelligent reasoning — while keeping your core logic pure Python.

> **Philosophy:** keep code idiomatic; reach for `context.<service>()` only when you need I/O, coordination, or intelligence.

---

## 1. KV — Ephemeral Coordination

A minimal key–value store for transient state, synchronization, and quick signals between nodes/agents.

```python
@graph_fn(name="kv_demo", outputs=["ok"])
async def kv_demo(*, context):
    kv = context.kv()
    await kv.set("stage", "preflight", ttl_s=300)
    stage = await kv.get("stage")  # → "preflight"
    return {"ok": stage == "preflight"}
```

**Why/When:** feature flags, locks/counters, short-lived coordination.

**Default backend:** in-memory KV.

**Deep dive:** KV Service →

---

## 2. Logger — Structured Logs with Provenance

Structured logging with `{run_id, graph_id, node_id}` automatically injected.

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

**Why/When:** lifecycle traces, metrics, error reporting.

**Default backend:** Python `logging`.

**Deep dive:** Logging →

---

## 3. LLM — Unified Chat & Embeddings *(optional)*

Provider-agnostic interface for chat/completions and embeddings. Requires configuration (API keys, profile).

```python
@graph_fn(name="llm_demo", outputs=["reply"])
async def llm_demo(prompt: str, *, context):
    llm = context.llm(profile="default")
    msg = await llm.chat([{"role": "user", "content": prompt}])
    return {"reply": msg["content"]}
```

**Why/When:** summarization, drafting, tool-use planning, embeddings.

**Backends:** OpenAI, Anthropic, local, etc.

**Deep dive:** LLM Service →

---

## 4. RAG — Long‑Term Semantic Recall *(optional)*

Build searchable corpora from events/docs; retrieve or answer with citations. Requires an LLM for answering.

```python
@graph_fn(name="rag_demo", outputs=["answer"])
async def rag_demo(q: str, *, context):
    mem = context.memory()
    corpus = await mem.rag_bind(scope="project")
    await mem.rag_promote_events(corpus_id=corpus)
    ans = await mem.rag_answer(corpus_id=corpus, question=q)
    return {"answer": ans["answer"]}
```

**Why/When:** semantic search, project recall, retrieval‑augmented QA.

**Default backend:** FAISS (local).

**Deep dive:** RAG → · External Context →

---

## 5. MCP — External Tool Bridges *(optional)*

Connect to external tool servers over stdio/WebSocket/HTTP via **Model Context Protocol (MCP)**.

```python
@graph_fn(name="mcp_demo", outputs=["hits"])
async def mcp_demo(*, context):
    ws = context.mcp("ws")  # adapter name
    res = await ws.call("search", {"q": "tolerance analysis", "k": 3})
    return {"hits": res.get("items", [])}
```

**Why/When:** integrate non-Python tools or remote services with structured contracts.

**Deep dive:** MCP →

---

## Takeaways

* Access everything through `context.<service>()` — no globals or custom wiring.
* KV and Logger work out of the box; LLM/RAG/MCP are optional and enabled by config.
* Backends are pluggable; you can move from local to managed services without changing agent code.

**Next:** Explore [Channels & Interaction →] or [Artifacts & Memory →]
