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

**Artifacts** are immutable, content‑addressed assets produced or consumed by agents/tools: files, directories, JSON payloads, or serialized objects.

### Why Artifacts (vs. manual files)?

* **Content‑addressed**: the URI reflects the content (CAS) — no silent overwrites.
* **Typed + labeled**: add `kind`, `labels`, and `metrics` to organize results.
* **Indexed**: query by scope or rank by metric (e.g., best checkpoint by `val_acc`).
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
| `save(path, kind, labels=None, metrics=None, pin=False)`          | Save an existing path and index it. Returns an artifact with `uri`.          |
| `save_text(content, *, kind="text", labels=None)`                 | Store small text payloads.                                                   |
| `save_json(obj, *, kind="json", labels=None)`                     | Store a JSON payload.                                                        |
| `writer(kind, planned_ext)`                                       | Context manager to stream‑write binary content; atomically indexes on close. |
| `list(scope)` / `search(...)` / `best(kind, metric, mode, scope)` | Query and rank artifacts by descriptors or metrics.                          |
| `pin(artifact_id)`                                                | Mark as retained (skip cleanup policies).                                    |
| `to_local_path(uri)`                                              | Resolve a CAS URI to a local filesystem path.                                |

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

**Rank by metric or search**

```python
@graph_fn(name="search_reports", outputs=["top_uri"])
async def search_reports(*, context):
    top = await context.artifacts().best(
        kind="checkpoint", metric="val_acc", mode="max", scope="run"
    )
    if top:
        return {"top_uri": top.uri}
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
* **Summarization**: distill long conversations or runs into compact context.
* **RAG‑ready**: promote events to a vector index for retrieval‑augmented answers.
* **Analytics**: compute “last by name,” track trends, or export for BI.

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
| `record_raw(base, text=None, metrics=None)`                       | Append a low‑level event.                           |
| `record(kind, data, tags=None, **extra)`                          | Convenience structured logging.                     |
| `write_result(topic, inputs=None, outputs=None, tags=None)`       | Log a typed output; updates indices.                |
| `recent(kinds=None, limit=50)`                                    | Fetch most recent events.                           |
| `last_by_name(name)`                                              | Get the latest output value by name.                |
| `latest_refs_by_kind(kind)`                                       | Retrieve latest artifact/message refs of a kind.    |
| `distill_rolling_chat(max_turns=20)`                              | Generate a compact chat/run summary (LLM‑assisted). |
| `rag_bind(scope)` / `rag_promote_events(...)` / `rag_answer(...)` | RAG lifecycle helpers (requires LLM).               |

### Examples

**Log a typed result**

```python
@graph_fn(name="remember_output", outputs=["y"])
async def remember_output(x: int, *, context):
    y = x + 1
    await context.memory().write_result(
        topic="calc",
        outputs=[{"name": "y", "kind": "number", "value": y}],
        tags=["demo"],
    )
    return {"y": y}
```

**Recall + summarization**

```python
recent = await context.memory().recent(limit=10)
last_y = await context.memory().last_by_name("y")
summary = await context.memory().distill_rolling_chat(max_turns=20)
```

**Promote to RAG**

```python
corpus = await context.memory().rag_bind(scope="project")
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

AetherGraph’s built‑ins for **Artifacts** and **Memory** are part of the OSS core runtime and are not swappable in place. That is intentional: we rely on their stable semantics for provenance, lineage, and tooling.

> **Important:** You **cannot** replace `context.artifacts()` or `context.memory()` with custom implementations. Instead, add **new services with new names** and keep agent code explicit about which storage it is using.

### Recommended Extension Pattern

* **Register new services** under distinct names, e.g. `context.datasets()`, `context.vault()`, `context.lineage_store()`, `context.vector_db()` or `context.external_artifacts()`.
* **Keep provenance links** by storing artifact URIs or memory event IDs alongside your external records when appropriate.
* **Export/mirror** selectively: you can mirror core artifacts/memory events to external systems for BI/compliance without changing the core stores.

See *Extending Context Services* for `Service` APIs.



---

## 6. Design Principles

* **Python‑first**: simple, composable APIs; no DSL required.
* **Immutable by default**: artifacts are write‑once; updates create new versions.
* **Typed results**: names/kinds/values make analytics and recall precise.
* **Provenance everywhere**: run/graph/node IDs are attached automatically.
* **Separation of concerns**: artifacts hold assets; memory holds events/results; they reference each other for lineage.

---

## Summary

* **Artifacts** make outputs durable, searchable, and reproducible with CAS URIs and rich indexing.
* **Memory** records the event stream and typed results for contextual recall, analytics, and RAG.
* Together they provide end‑to‑end provenance and effortless “time travel” across runs.
* The façades are **extensible**: swap in enterprise stores/indices without changing agent code.

**See also:** `context.artifacts()` · `context.memory()` · `context.rag()` · *External Context Services*
