# AetherGraph — `context.memory()` Reference

This page documents the **MemoryFacade** returned by `context.memory()` in a concise format: signature, brief description, parameters, returns, and practical examples. The facade coordinates three core components — **HotLog** (recent, transient), **Persistence** (durable JSONL/appends), and **Indices** (fast derived views) — with optional **ArtifactStore**, **RAG**, and **LLM** services.

---

## Overview
`context.memory()` is bound to your current runtime scope (`session_id`, `run_id`, `graph_id`, `node_id`, `agent_id`). Typical operations:

1. **Record** events (raw or typed results)

2. **Query** recent/last/by‑kind outputs via indices/hotlog

3. **Distill** (rolling summaries, episode summaries)

4. **RAG** (optional): upsert, search, answer using a configured RAG + LLM

---

## memory.record_raw
```
record_raw(*, base: dict, text: str | None = None, metrics: dict | None = None, sources: list[str] | None = None) -> Event
```
Append a **normalized** event to HotLog (fast) and Persistence (durable). Computes a stable `event_id` and a lightweight `signal` if absent.

**Parameters**

- **base** (*dict*) – Canonical fields describing the event (e.g., `kind`, `stage`, `severity`, `tool`, `tags`, `entities`, `inputs`, `outputs`, …). Missing scope keys are filled from the bound context.

- **text** (*str, optional*) – Human‑readable message/body.

- **metrics** (*dict, optional*) – Numeric metrics (latency, token counts, costs, etc.).

- **sources** (*list[str], optional*) – Event IDs this event summarizes/derives from.

**Returns**  
*Event* – The appended event.

**Notes**  
Does **not** update `indices` automatically. Use `write_result()` when you want indices updated for typed outputs.

---

## memory.record
```
record(kind, data, tags=None, entities=None, severity=2, stage=None, inputs_ref=None, outputs_ref=None, metrics=None, sources=None, signal=None) -> Event
```
Convenience wrapper around `record_raw()` for common fields; stringifies `data` if needed.

**Parameters**

- **kind** (*str*) – Event kind (e.g., `"user_msg"`, `"tool_call"`).

- **data** (*Any*) – JSON‑serializable payload; will be stringified for `text`.

- **tags** (*list[str], optional*) – Tag list.

- **entities** (*list[str], optional*) – Entity IDs.

- **severity** (*int*) – 1–5 scale (default 2).

- **stage** (*str, optional*) – Phase label (e.g., `"observe"`, `"act"`).

- **inputs_ref** (*list[dict], optional*) – Typed input references (Value[]).

- **outputs_ref** (*list[dict], optional*) – Typed output references (Value[]).

- **metrics** (*dict, optional*) – Numeric metrics.

- **sources** (*list[str], optional*) – Upstream event IDs.

- **signal** (*float, optional*) – 0.0–1.0; if omitted, computed heuristically.

**Returns**  
*Event* – The appended event.

---

## memory.write_result
```
write_result(*, topic: str, inputs: list[dict] | None = None, outputs: list[dict] | None = None, tags: list[str] | None = None, metrics: dict | None = None, message: str | None = None, severity: int = 3) -> Event
```
Record a **typed result** (tool/agent/flow) and update indices for quick retrieval.

**Parameters**

- **topic** (*str*) – Tool/agent/flow identifier (used by `indices.last_outputs_by_topic`).

- **inputs** (*list[dict], optional*) – Typed inputs (Value[]).

- **outputs** (*list[dict], optional*) – Typed outputs (Value[]). **Indices derive from these.**

- **tags** (*list[str], optional*) – Tag list.

- **metrics** (*dict, optional*) – Numeric metrics.

- **message** (*str, optional*) – Human‑readable summary.

- **severity** (*int*) – Default 3.

**Returns**  
*Event* – The normalized `tool_result` event.

**Effect**  
Auto‑appends to HotLog & Persistence **and** calls `indices.update(session_id, evt)`.

---

## memory.recent
```
recent(*, kinds: list[str] | None = None, limit: int = 50) -> list[Event]
```
Return recent events from HotLog (most recent last), optionally filtering by `kinds`.

**Parameters**

- **kinds** (*list[str], optional*) – Filter kinds.

- **limit** (*int*) – Max events (default 50).

**Returns**  
*list[Event]* – Recent events.

---

## memory.last_by_name
```
last_by_name(name: str)
```
Return the last **output value** by `name` from Indices (fast path).

**Parameters**

- **name** (*str*) – Output name.

**Returns**  
*Any* – The stored value for that name (adapter‑dependent) or `None`.

---

## memory.latest_refs_by_kind
```
latest_refs_by_kind(kind: str, *, limit: int = 50)
```
Return latest **ref outputs** by `ref.kind` (fast path, KV‑backed) from Indices.

**Parameters**

- **kind** (*str*) – Reference kind.

- **limit** (*int*) – Max items (default 50).

**Returns**  
*list[Any]* – Recent references.

---

## memory.last_outputs_by_topic
```
last_outputs_by_topic(topic: str)
```
Return the last **output map** for a given topic (tool/flow/agent) from Indices.

**Parameters**

- **topic** (*str*) – Topic identifier.

**Returns**  
*dict | None* – Latest outputs or `None` if absent.

---

## memory.distill_rolling_chat
```
distill_rolling_chat(*, max_turns: int = 20, min_signal: float | None = None) -> dict
```
Build a **rolling chat summary** from recent user/assistant turns (reads HotLog; typically writes a JSON summary via Persistence).

**Parameters**

- **max_turns** (*int*) – Window of turns to include (default 20).

- **min_signal** (*float, optional*) – Signal threshold; uses facade default if omitted.

**Returns**  
*dict* – Descriptor (e.g., `{ "uri": ..., "sources": [...] }`).

---

## memory.distill_episode
```
distill_episode(*, tool: str, run_id: str, include_metrics: bool = True) -> dict
```
Summarize a **tool/agent episode** (all events for a given `run_id` + `tool`). Reads HotLog/Persistence; writes back a summary JSON (and optionally CAS bundle).

**Parameters**

- **tool** (*str*) – Tool/agent identifier.

- **run_id** (*str*) – Run to summarize.

- **include_metrics** (*bool*) – Include metrics in the summary (default True).

**Returns**  
*dict* – Descriptor (e.g., `{ "uri": ..., "sources": [...], "metrics": {...} }`).

---

## RAG helpers (optional)

### memory.rag_upsert
```
rag_upsert(*, corpus_id: str, docs: Sequence[dict], topic: str | None = None) -> dict
```
Upsert documents into a RAG corpus via the configured RAG facade.

**Parameters**

- **corpus_id** (*str*) – Target corpus identifier.

- **docs** (*Sequence[dict]*) – Documents/chunks with text and metadata.

- **topic** (*str, optional*) – Optional topic name to attribute the upsert.

**Returns**  
*dict* – Upsert stats (shape adapter‑specific).

**Raises**  
`RuntimeError` – if RAG facade is not configured.

---

### memory.rag_search
```
rag_search(*, corpus_id: str, query: str, k: int = 8) -> list[dict]
```
Retrieve best‑matching chunks for a query.

**Parameters**

- **corpus_id** (*str*) – Target corpus identifier.

- **query** (*str*) – Natural language query.

- **k** (*int*) – Max results (default 8), reranked.

**Returns**  
*list[dict]* – Ranked hits.

**Raises**  
`RuntimeError` – if RAG facade is not configured.

---

### memory.rag_answer
```
rag_answer(*, corpus_id: str, question: str, style: str = "concise", k: int = 6, llm_profile: str = "default") -> dict
```
Answer a question using RAG + LLM (both must be configured).

**Parameters**

- **corpus_id** (*str*) – Target corpus identifier.

- **question** (*str*) – User question.

- **style** (*str*) – Answering style (e.g., `"concise"`).

- **k** (*int*) – Max retrieved chunks (default 6).

- **llm_profile** (*str*) – Profile name to select an LLM client.

**Returns**  
*dict* – Answer payload (adapter‑specific).

**Raises**  
`RuntimeError` – if RAG or LLM is not configured.

---

<!-- ## memory.resolve
```
resolve(params: dict) -> dict
```
Synchronous helper to resolve parameter templates against memory context (uses the resolver service under the hood).

**Parameters**

- **params** (*dict*) – Parameters with placeholders.

**Returns**  
*dict* – Resolved parameters.

--- -->

## Practical examples

**1) Record + recent**
```python
from aethergraph import graph_fn

@graph_fn(name="mem_record_recent")
async def mem_record_recent(*, context):
    evt = await context.memory().record(
        kind="user_msg",
        data={"text":"hello world","lang":"en"},
        tags=["demo","quickstart"],
        severity=2,
    )
    recent = await context.memory().recent(kinds=["user_msg"], limit=5)
    await context.channel().send_text(f"recent user_msg count={len(recent)}")
    return {"event_id": evt.event_id, "recent_count": len(recent)}
```

**2) Write a typed result and fetch last outputs**
```python
@graph_fn(name="mem_write_result")
async def mem_write_result(*, context):
    await context.memory().write_result(
        topic="eval.step",
        outputs=[{"name":"acc","kind":"number","value":0.912}],
        metrics={"latency_ms": 120},
        message="evaluation complete",
    )
    last = await context.memory().last_outputs_by_topic("eval.step")
    await context.channel().send_text(f"last acc={last['acc']:.3f}")
```

**3) Rolling chat summary**
```python
@graph_fn(name="mem_rolling")
async def mem_rolling(*, context):
    summary = await context.memory().distill_rolling_chat(max_turns=16)
    await context.channel().send_text(f"rolling summary uri: {summary.get('uri','<none>')}")
```

**4) Episode summary**
```python
@graph_fn(name="mem_episode")
async def mem_episode(*, context, run_id: str, tool: str):
    desc = await context.memory().distill_episode(tool=tool, run_id=run_id)
    await context.channel().send_text(f"episode summary: {desc.get('uri','<none>')}")
```

**5) RAG (if configured)**
```python
@graph_fn(name="mem_rag")
async def mem_rag(*, context):
    # Upsert a few docs
    await context.memory().rag_upsert(
        corpus_id="notes",
        docs=[{"id":"1","text":"Optics basics: Snell's law"}],
    )
    # Search
    hits = await context.memory().rag_search(corpus_id="notes", query="Snell")
    # Answer
    ans = await context.memory().rag_answer(corpus_id="notes", question="What is Snell's law?", style="concise")
    await context.channel().send_text(ans.get("answer","<no answer>"))
```

---

## Notes & behaviors
- **Signal heuristic**: if not provided, `record(_raw)` computes a 0.0–1.0 `signal` from severity + presence/length of text + metrics.

- **Durability**: every `record_raw` & `write_result` appends to **Persistence**; `recent()` reads from **HotLog**.

- **Indices**: `write_result()` updates fast views used by `last_by_name`, `latest_refs_by_kind`, `last_outputs_by_topic`.

- **Artifacts**: distillers may produce CAS artifacts when an `ArtifactStore` is provided.

- **Performance**: methods are async; backends should avoid blocking the event loop (use `asyncio.to_thread` for heavy IO).

