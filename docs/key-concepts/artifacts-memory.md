# Artifacts and Memory

This chapter covers two foundational pillars of AetherGraph’s runtime: **Artifacts** and **Memory**. Together, they form the **provenance backbone** — making every result, file, and intermediate step traceable, reproducible, and retrievable long after execution.

> **Mental model:** Artifacts capture *what* was produced; Memory captures *what happened* (events, results, metrics) and *why* (context, summaries, links).

---

## 1. Why Artifacts & Memory Exist

Most Python workflows scatter outputs across temp folders and logs with no consistent linkage. AetherGraph fixes this by binding everything to the active **run/graph/node** and exposing consistent, high‑level APIs for saving and recalling state.

| Concern         | Manual management                    | With AetherGraph                                                        |
| --------------- | ------------------------------------ | ----------------------------------------------------------------------- |
| Provenance      | Files & logs scattered; hard to link | Every record stamped with `{run_id, graph_id, node_id}` + tool metadata |
| Reproducibility | Filenames drift; env unknown         | Content‑addressed + typed records → deterministic recall                |
| Discoverability | Grep and guess                       | Query by `kind`, `labels`, `metrics`, scope; ask “best by metric”       |
| Durability      | Ad‑hoc paths; stale temp dirs        | CAS store + index; pins; export/replay                                  |
| Collaboration   | Tribal conventions                   | Shared schema (URIs/records) + searchable index                         |

**Takeaway:** Use artifacts for durable assets; use memory for structured, queryable history. Both are scoped to your execution so you can reconstruct the *story* of a run.

---

## 2. Artifacts — Persistent Assets

**Artifacts** are immutable, content‑addressed assets (CAS) produced or consumed by agents/tools: files, directories, JSON payloads, or serialized objects.

### Why Artifacts (vs. manual files)?

* **Content‑addressed**: the URI reflects the content (CAS) — no silent overwrites, no need for manual naming.
* **Typed + labeled**: add `kind`, `labels`, and `metrics` to organize results.
* **Indexed**: query by scope/labels or rank by metric. 
* **Provenance‑stamped**: `{run_id, graph_id, node_id, tool_name, tool_version}` baked in.
* **Portable**: `to_local_path(uri)` resolves for local or remote stores.

### Architecture

```
[ Your Agent / Tool ]
          │   (context)
          ▼
[ NodeContext ]
          │
          ▼
[ context.artifacts() — Artifact Facade ]
     ├───────────────┬────────────────┬─────────────────┐
     │               │                │                 │
     │ save / writer │ stage / ingest │ list / search   │ best / pin
     ▼               ▼                ▼                 ▼
[ Artifact Store ]  [ Staging Area ]  [ Artifact Index ]  [ Retention ]
     (CAS/FS)          (tmp)             (SQLite/KV)        (pins)
```

### Core API

| Method                                                            | Purpose                                                                      |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `stage()` / `stage_dir()`                                         | Reserve a temp path for producing files/dirs safely.                         |
| `save()`          | Save an existing path and index it. Returns an artifact with `uri`.          |
| `save_text()`                 | Store small text payloads.                                                   |
| `save_json()`                     | Store a JSON payload.                                                        |
| `writer()`                                       | Context manager to stream‑write binary content; atomically indexes on close. |
| `list()` / `search()` / `best()` | Query and rank artifacts by descriptors or metrics.                          |
| `pin()`                                                | Mark as retained (skip cleanup policies).                                    |
| `to_local_path()`                                              | Resolve a CAS URI to a local filesystem path.                                |

### Examples

**Save a file**

```python
@graph_fn(name="produce_artifact", outputs=["report_uri"])
async def produce_artifact(*, context):
    art = await context.artifacts().save(
        path="/tmp/report.pdf", kind="report", labels={"exp": "A"}
    )
    return {"report_uri": art.uri}
```

**Search a past artfiact**

```python
@graph_fn(name="search_reports", outputs=["top_uri"])
async def search_reports(*, context):
    results = await context.artifacts().search(
        kind="report", labels={"exp": "A"}
    )
    return {"top_uri": results[0].uri if results else None}
```

---

## 3. Memory — Structured Event & Result Log

**Memory** is a unified façade for recording, persisting, and querying **events** during an agent’s lifetime: raw logs, typed results, metrics, and their relationships with artifacts. 

### Why Memory (design intent)

* **Contextual recall**: agents can react based on recent or historical state.
* **Typed outputs**: `write_result` records semantic outputs with names/kinds/values.
* **RAG‑ready**: promote events to a vector index for retrieval‑augmented answers.
* **Analytics**: retrieve last actions for logical connection, track trends, or export for traceability.

### Architecture

```
[ Your Agent / Tool ]
          │   (context)
          ▼
[ NodeContext ]
          │
          ▼
[ context.memory() — Memory Facade ]
        ├───────────────┬──────────────────┬───────────────┬──────────────┐
        │               │                  │               │              │
        ▼               ▼                  ▼               ▼              ▼
   [ HotLog ]      [ Persistence ]     [ Indices ]     [ Summaries ]  [ RAG ]
 (ephemeral KV)   (JSONL append-only)   (SQLite/KV)     (LLM-based)   (FAISS)
        │               │                  │               │              │
   recent()/tail   replay/export      last_by_name     distill_*      search/answer
                                      last_outputs                     promote_events
```

### Core API

| Method                                                            | Purpose                                             |
| ----------------------------------------------------------------- | --------------------------------------------------- |
| `record_raw()`                       | Append a low‑level event.                           |
| `record()`                          | Convenience structured logging.                     |
| `write_result()`       | Log a typed output; updates indices.                |
| `recent()` / `recent_data()`                                    | Fetch most recent events / event data                       |
| `last_by_name()`                                              | Get the latest output value by name.                |
| `rag_bind()` / `rag_promote_events()` / `rag_answer()` | RAG lifecycle helpers (requires LLM).               |

### Examples

**Record an event**

```python
@graph_fn(name="remember_output", outputs=["y"])
async def remember_output(x: int, *, context):
    y = x + 1
    await context.memory().record(kind="cal.result", data={"y": y})
    return {"y": y}
```

**Recall + summarization**

```python
recent = await context.memory().recent(limit=10) # return list of events
```

**Promote to RAG**

```python
corpus = await context.memory().rag_bind()
await context.memory().rag_promote_events(corpus_id=corpus)
ans = await context.memory().rag_answer(corpus_id=corpus, question="What was the best run?")
```

---

## 4. Artifacts × Memory — Better Together

Artifacts and Memory reference each other: results and metrics point to artifact URIs; artifact metadata references the node that produced them. This **bi‑directional linking** enables:

* Reconstructing the full story of a result (inputs → tools → outputs → files).
* Ranking/searching results across runs/experiments.
* Efficient clean‑up strategies (e.g., keep pinned/best; GC the rest).

---

## 5. Extensibility & External Systems

AetherGraph’s built‑ins for **Artifacts** and **Memory** are part of the OSS core runtime and are not swappable in place. That is intentional: we rely on their stable semantics for provenance, lineage, and tooling. If you need custom memory or storage systems (local or cloud), see *Extending Context Services* for `Service` APIs.

---


## Summary

* **Artifacts** make outputs durable, searchable, and reproducible with CAS URIs and rich indexing.
* **Memory** records the event stream and typed results for contextual recall, analytics, and RAG.
* Together they provide end‑to‑end provenance and effortless “time travel” across runs.

**See also:** `context.artifacts()` · `context.memory()` · `context.rag()` · *External Context Services*
