# Artifacts and Memory

This section explains two foundational components of AetherGraph’s runtime: **Artifacts** and **Memory**. Together, they form the system’s provenance backbone — ensuring every result, file, and intermediate step can be saved, indexed, and revisited.

---

## 1. Artifacts — Persistent Assets

**Artifacts** are immutable, content-addressed assets produced or consumed by agents and tools. They may be files, directories, JSON payloads, or serialized objects.

### Why Artifacts Matter

* **Reproducibility:** Everything an agent produces can be saved and reloaded later by URI.
* **Traceability:** Each artifact is stamped with `{run_id, graph_id, node_id, tool_name, tool_version}`.
* **Discoverability:** Artifacts are indexed by kind, labels, and metrics, making it easy to search or rank results (e.g., best model checkpoint by validation score).

### Artifacts Architecture
```
[ Your Agent / Tool ]
          │   (context)
          ▼
[ NodeContext ]
          │
          ▼
[ context.artifacts()  — Artifact Facade ]
     ├───────────────┬────────────────┐
     │               │                │
     │ save / writer │ stage/ingest   │ list/search/best/pin
     ▼               ▼                ▼
[ Artifact Store ]  [ Staging Area ]  [ Artifact Index ]
   (CAS/FS)             (tmp)            (SQLite/kv)
```

`context.artifacts()` saves immutable outputs (CAS URIs) and allows you to query them later. Typical flow: save/writer → (Store) → upsert → (Index) → search/best. 

### Core Features

| Method                                      | Purpose                                                      |
| ------------------------------------------- | ------------------------------------------------------------ |
| `stage()` / `stage_dir()`                   | Reserve a temporary path for producing files or directories. |
| `save(path, kind, labels, metrics, pin)`    | Save an existing file and index it.                          |
| `save_text(content)` / `save_json(payload)` | Quickly store small artifacts.                               |
| `writer(kind, planned_ext)`                 | Context manager to stream-write binary content safely.       |
| `list(scope)` / `search(...)` / `best(...)` | Query artifacts by scope, kind, label, or metric.            |
| `pin(artifact_id)`                          | Mark an artifact as retained.                                |
| `to_local_path(uri)`                        | Resolve file URIs for local access.                          |

### Examples 

#### Save a File

```python
@graph_fn(name="produce_artifact", outputs=["report_uri"])
async def produce_artifact(*, context):
    # assume the file has been exported to tmp path "/tmp/report.pdf"
    art = await context.artifacts().save(
        path="/tmp/report.pdf", kind="report", labels={"exp": "A"}
    )
    return {"report_uri": art.uri}
```

#### Search After Save

```python
@graph_fn(name="search_reports", outputs=["top_uri"]) 
async def search_reports(*, context):
    # Find the best report by a metric (if indexed) within current run
    top = await context.artifacts().best(
        kind="report", metric="val_score", mode="max", scope="run"
    )
    if top:
        return {"top_uri": top.uri}
    # Or general search by labels/kind
    reports = await context.artifacts().search(kind="report", labels={"exp": "A"})
    return {"top_uri": reports[0].uri if reports else None}
```

---

## 2. Memory — Structured Event & Result Log

**Memory** provides a unified façade for recording, persisting, and querying events during an agent’s lifetime. It keeps **raw logs**, **typed results**, and **derived indices** in sync.

### Why Memory Matters

* **Provenance:** Tracks everything your graph or agent does — messages, results, metrics.
* **Contextual recall:** Enables reactive behavior by letting agents recall previous states.
* **Analytics:** Supports summaries, distillation, and RAG promotion for long-term memory.

### Core Methods

| Method                                 | Purpose                                           |
| -------------------------------------- | ------------------------------------------------- |
| `record_raw(base, text, metrics)`      | Append a low-level event to logs and persistence. |
| `record(kind, data, tags, ...)`        | Convenience for structured logging.               |
| `write_result(topic, inputs, outputs)` | Log a typed output event; updates indices.        |
| `recent(kinds, limit)`                 | Fetch recent events from the hot log.             |
| `last_by_name(name)`                   | Fetch the last output value by name.              |
| `latest_refs_by_kind(kind)`            | Retrieve last references of a given kind.         |

### Memory Architecture
```
[ Your Agent / Tool ]
          │   (context)
          ▼
[ NodeContext ]
          │
          ▼
[ context.memory()  — Memory Facade ]
        ├───────────────┬──────────────────┬───────────────┐
        │               │                  │               │
        ▼               ▼                  ▼               ▼
   [ HotLog ]      [ Persistence ]     [ Indices ]     [ RAG (FAISS) ]
 (ephemeral KV)   (JSONL append-only)   (SQLite)      (vector index)
        │               │                  │               │
   recent()/tail   replay/export      last_by_name     search/answer*
                                      last_outputs     promote_events
```

### Examples

#### Use in a graph_fn

```python
@graph_fn(name="remember_output", outputs=["y"])
async def remember_output(x: int, *, context):
    y = x + 1
    await context.memory().write_result(
        topic="calc",
        outputs=[{"name": "y", "kind": "number", "value": y}]
    )
    return {"y": y}
```

---



#### Using Memory Facets

```python
# Retrieve recent events
recent = await context.memory().recent(limit=10)

# Get last stored output
last_y = await context.memory().last_by_name("y")

# Summarize conversation or run
summary = await context.memory().distill_rolling_chat(max_turns=20)
```

#### Combining with RAG

Memory can promote important events into a RAG corpus for question‑answering and retrieval. **RAG requires an LLM configuration** (`context.llm()`), and the default vector index is **FAISS**.

```python
# Bind or create a RAG corpus for the "project" scope and get its id
corpus = await context.memory().rag_bind(scope="project")

# Promote recent events into the bound corpus so they become retrievable
await context.memory().rag_promote_events(corpus_id=corpus)

# Query the RAG corpus to answer a question (returns the retrieved/LLM answer)
ans = await context.memory().rag_answer(corpus_id=corpus, question="What was the best run?")
```

---

## Takeaways

* **Artifacts** ensure files and datasets are traceable, reproducible, and searchable.
* **Memory** provides structured logging and retrieval of all runtime events.
* **RAG** is available out‑of‑the‑box via FAISS (LLM required) and can be swapped via external services.
* If you have your own memory system, **External Context Services** let you add custom memory with advanced capability (e.g., FAISS → managed vector DB, FS CAS → S3/GCS) without changing the main agent code.

---

**See also:**

* `context.artifacts()` — artifact storage façade
* `context.memory()` — session memory façade
* `context.rag()` — retrieval‑augmented interface (requires LLM)
* *External Context* — extend/replace local services for scale or compliance
