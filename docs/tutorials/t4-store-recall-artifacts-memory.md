# Tutorial 4: Store & Recall — Artifacts and Memory

This tutorial shows practical, copy-ready patterns for **saving outputs** (Artifacts) and **logging results/events** (Memory) — the pair that gives your work provenance, searchability, and recall.

> **Mental model**
>
> * **Artifacts** = durable assets (files/dirs/JSON blobs) with **CAS URIs**.
> * **Memory** = structured event/result log you can **query** later.

---

## 1) Quick Patterns

We’ll introduce each concept right where you use it — so you always know **why** a field exists and **how** to fill it.

### A. Save a produced file → get a URI → later resolve to path

```python
# produce a file first, then ingest it as an artifact
art = await context.artifacts().save(
    path="/tmp/report.pdf",           # file you created
    kind="report",                    # short noun; you’ll search/rank by this later
    labels={"exp": "A"},             # 1–3 useful filters you actually query later
)
uri = art.uri                          # content-addressed, stable (CAS URI)

# when you need to open the file locally again
p = context.artifacts().to_local_path(uri)
```

* `save(...)` ingests your file into the managed store under `workspace/artifacts/...` using content‑addressed storage (CAS). This avoids accidental overwrites and gives you a stable identifier.
* If you pass a `suggested_uri`, that hint will also appear in the managed path so it’s easier to find in your file explorer (still CAS‑backed under the hood).
* The return value is a **URI**. Use `to_local_path(uri)` when you actually need a filesystem path.

### B. Stream-write bytes safely (atomically) and index

```python
async with context.artifacts().writer(kind="plot", planned_ext=".png") as w:
    w.write(png_bytes)
# on exit: artifact is saved + indexed
```

The writer ensures atomic creation and indexing in one step.

### C. Record a typed result for fast recall

```python
await context.memory().write_result(
    topic="train.step",               # small identifier of the step/agent/tool
    outputs=[                          # named values you’ll query later
        {"name": "val_acc", "kind": "number", "value": 0.912},
        {"name": "ckpt_uri", "kind": "uri", "value": uri},
    ],
)
```

* **Memory results** are easy to query with `last_by_name("val_acc")`.
* Use just a few named outputs you care about.

### D. Record arbitrary event logs and recall them

```python
await context.memory().record(
    kind="train_log",
    data={"epoch": 1, "loss": 0.25, "acc": 0.91},
)
recent_logs = await context.memory().recent(limit=3)
```

Use `record()` for lightweight structured logging of intermediate data or progress. Later, `recent()` lets you fetch the most recent N events for debugging, reporting, or summarization.

### E. Find the “best so far” or search by label (after you’ve saved)

```python
# Ranking: requires that artifacts were saved with a relevant metric
best = await context.artifacts().best(
    kind="checkpoint",      # the noun you used on save
    metric="val_acc",       # metric name present on saved artifacts
    mode="max",             # pick highest value
    scope="run"             # limit to current run (common default)
)

# Flexible filtering by labels you used on save
hits = await context.artifacts().search(
    kind="report",
    labels={"exp": "A"},   # must match labels you saved earlier
)
```

* `best(...)` selects by a numeric `metric` you attached **when saving** (e.g., `metrics={"val_acc": 0.912}`).
* You don’t need `memory.write_result(...)` for `best(...)`, but recording the same metric and the artifact URI via `write_result(...)` is recommended for quick recall (`last_by_name`) and dashboards.
* Keep `scope` tight (e.g., current run) for speed.

### F. Grab the latest value by name

```python
last_acc = await context.memory().last_by_name("val_acc")
```

Retrieve the latest recorded value by its name; indices are updated by `write_result(...)`.

---

## 2) Minimal End-to-End Examples

### 2.1 Save, log, and recall (common training loop)

```python
@graph_fn(name="train_epoch", outputs=["ckpt_uri"])
async def train_epoch(epoch: int, *, context):
    # 1) write a checkpoint to a temp path you control
    tmp_path = "/tmp/ckpt.bin"   # your code exports it here
    # 2) ingest as artifact + index
    ckpt = await context.artifacts().save(path=tmp_path, kind="checkpoint", labels={"epoch": epoch})
    # 3) record metrics & refs to artifacts
    await context.memory().write_result(
        topic="train.epoch",
        outputs=[
            {"name": "epoch", "kind": "number", "value": epoch},
            {"name": "ckpt_uri", "kind": "uri", "value": ckpt.uri},
        ],
    )
    return {"ckpt_uri": ckpt.uri}
```

**Why this matters**

* Artifact is durable and discoverable.
* Memory entry lets you query the last checkpoint quickly or build summaries later.

### 2.2 Rank by metric (pick the best)

```python
best = await context.artifacts().best(
    kind="checkpoint", metric="val_acc", mode="max", scope="run"
)
if best:
    path = context.artifacts().to_local_path(best.uri)
```

### 2.3 Save small JSON/Text directly

```python
cfg = await context.artifacts().save_json({"lr": 1e-3, "batch": 64})
log = await context.artifacts().save_text("training finished ok")
```

---

## 3) What to Record — Without Overdoing It

* **Artifacts:**

  * `kind` (required): a short noun (`"checkpoint"`, `"report"`, `"plot"`).
  * `labels` (optional): 1–3 filters you will actually search by (e.g., `{“exp”: “A”, “epoch”: 12}`).
  * `metrics` (optional): only if you’ll **rank** later (e.g., `{“val_acc”: 0.912}`).
* **Memory results:**

  * `topic`: small identifier for the step (`"train.epoch"`, `"eval.run"`).
  * `outputs`: a few **named** values you want to query (`val_acc`, `ckpt_uri`).

> Keep it lean. You can always add more labels/metrics in later runs.

---

## 4) FAQs & Concepts (for new users)

* **“Save” doesn’t edit in place:** It **ingests** a file/dir into the store, returns a URI, and indexes it. This is safer than writing into arbitrary folders.
* **CAS URI:** A content-addressed location that won’t change if you rename your experiment; it changes only when the content changes.
* **Index:** A searchable catalog of artifacts; it also tracks occurrences so you can filter by run/graph/node.
* **Suggested URI:** A hint for human-friendly paths; storage may fold this into the final URI while preserving CAS.
* **Distill memory:** Create compact summaries from verbose logs — useful before promoting to RAG.
* **Tool episode:** A prebuilt summarizer that collects all events for a tool or run, producing a concise JSON or artifact summary.
* **RAG:** Retrieval-Augmented Generation — turns your events/logs into a search corpus to answer questions later.

---

## 5) When to Use What

| Need                         | Use                                              | Rationale                          |
| ---------------------------- | ------------------------------------------------ | ---------------------------------- |
| Keep a file/dir for later    | `artifacts.save(...)` or `writer(...)`           | Durable, CAS, indexed.             |
| Store small JSON/Text        | `artifacts.save_json/text`                       | Convenience; still indexed.        |
| Quick metric/URI recall      | `memory.write_result(...)` → `last_by_name(...)` | Fast path via indices.             |
| Log structured data/events   | `memory.record(...)` → `recent(...)`             | Lightweight structured trace.      |
| Pick the best run/checkpoint | `artifacts.best(kind, metric, mode)`             | Ranking built into index.          |
| Browse all outputs from run  | `artifacts.list(scope="run")`                    | One-liner listing.                 |
| Summarize/answer across runs | `memory.distill_*` + `memory.rag_*`              | From logs to searchable knowledge. |

---

## 6) RAG — Memory × Artifacts (paired example)

> **Heads-up:** The Memory system ships with a **RAG facade**. You can use it via `context.memory().rag_*` helpers, **or** call the unified `context.rag()` service directly — they share the same backend.

```python
@graph_fn(name="make_rag_corpus", outputs=["answer"]) 
async def make_rag_corpus(question: str, *, context):
    # 1) Bind or create a project-level corpus (via Memory's RAG facade)
    corpus = await context.memory().rag_bind(scope="project")

    # 2) Promote informative events (e.g., tool_result) to the corpus
    await context.memory().rag_promote_events(
        corpus_id=corpus,
        where={"kinds": ["tool_result"], "limit": 200},  # pulls events from memory of this kind
    )

    # The method above fetches previously logged `tool_result` events —
    # those written through `memory.write_result(...)` — and turns them
    # into searchable text chunks inside the RAG corpus.

    # 3) Ask a question with citations (either path works)
    ans = await context.memory().rag_answer(corpus_id=corpus, question=question)

    # 4) Optionally snapshot the corpus as an artifact bundle
    snap = await context.memory().rag_snapshot(corpus_id=corpus, title="Weekly knowledge snapshot")

    return {"answer": ans.get("answer", ""), "snapshot_uri": snap.get("uri")}
```

**What’s happening**

* Event/results become a **searchable corpus**; answers include citations.
* `rag_promote_events()` converts stored `tool_result` memory entries (from your runs) into documents.
* Memory’s RAG helpers are convenience wrappers; `context.rag()` provides the same backend if you prefer working directly.

---

## 7) Small but Useful Extras

* **Pins:** `await context.artifacts().pin(artifact_id)` to mark artifacts as “keep forever”.
* **Scopes:** many list/search helpers accept `scope="run"|"graph"|"node"` for quick filtering.
* **Local access:** `to_local_path(uri)` is your bridge from URI → file path; it validates existence.
* **Distill summaries:** `await context.memory().distill_rolling_chat()` or `distill_episode()` to compress long logs into structured summaries.
* **Tool episodes:** use `distill_episode(tool="your_tool", run_id=run_id)` to summarize an entire tool’s activity.

---

## Summary

* Use **Artifacts** to durably store outputs and make them discoverable.
* Use **Memory** to log **named results** and recent events for instant recall.
* Combine **record()**, **write_result()**, and **recent()** for flexible tracking.
* Keep inputs minimal: a **kind**, a couple of **labels**, and a crucial **metric** if you’ll rank.
* Combine Memory distillation with RAG to turn past runs into searchable knowledge — with artifacts as cited evidence.

**See also:** `context.artifacts()` · `context.memory()` · RAG helpers (`rag_bind`, `rag_promote_events`, `rag_answer`, `rag_snapshot`)
