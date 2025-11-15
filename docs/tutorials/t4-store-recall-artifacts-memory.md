# Tutorial 4: Store & Recall — Artifacts and Memory

This tutorial focus on the how Aethergraph can memorize what happened before. Learn how to **save outputs**, **log results/events**, and **recall them later** using AetherGraph’s two persistence pillars:

* **Artifacts** — durable assets (files/dirs/JSON/text) stored by **content address (CAS URI)** with labels & metrics for ranking and search.
* **Memory** — a structured **event & result log** with fast “what’s the latest?” recall (e.g., `last_by_name`), plus simple recent‑history queries.

We’ll build this up step‑by‑step with short, copy‑ready snippets.

---

## 0. What you’ll use

```python
# Access services from your NodeContext
arts = context.artifacts()   # artifact store
mem  = context.memory()      # event & result log
```

> Mental model: **Artifacts** hold large, immutable outputs. **Memory** records *what happened* and the small named values you need to recall quickly.

---

## 1. Save something → get a URI → open it later

### A. Ingest an existing file

```python
art = await arts.save(
    path="/tmp/report.pdf",
    kind="report",                 # a short noun; you’ll filter/rank by this
    labels={"exp": "A"},          # 1–3 filters you actually plan to query
    # metrics={"bleu": 31.2},      # optional if you’ll rank later
)
uri = art.uri                       # stable CAS URI

# When you need a real path again:
path = arts.to_local_path(uri)
```

**Why CAS?** It prevents accidental overwrites and gives you a stable handle you can pass around (in Memory, dashboards, etc.).

### B. Stream‑write (no temp file), atomically

```python
async with arts.writer(kind="plot", planned_ext=".png") as w:
    w.write(png_bytes)
# on exit → the artifact is committed and indexed
```

> Tip: Prefer `writer(...)` for programmatically produced bytes.

---

## 2. Record results you’ll want to recall fast

Use **Memory** for structured results and lightweight logs.

### A. Record a typed result (fast recall by name)

```python
await mem.write_result(
    topic="train.step",
    outputs=[
        {"name": "val_acc",  "kind": "number", "value": 0.912},
        {"name": "ckpt_uri", "kind": "uri",    "value": uri},
    ],
)

last_acc = await mem.last_by_name("val_acc")
```

`write_result` indexes named values so `last_by_name("val_acc")` is O(1) to fetch the latest.

### B. Log arbitrary events (structured but lightweight)

```python
await mem.record(
    kind="train_log",
    data={"epoch": 1, "loss": 0.25, "acc": 0.91},
)

recent = await mem.recent(kinds=["train_log"], limit=3)
```

Need only the decoded payloads?

```python
logs = await mem.recent_data(kinds=["train_log"], limit=3)
```

> Use `record` for progress/trace breadcrumbs. Use `write_result` for small named values you’ll query later.

---

## 3. Search, filter, and rank artifacts

### A. Search by labels you saved earlier

```python
hits = await arts.search(
    kind="report",
    labels={"exp": "A"},    # exact‑match filter across indexed labels
)
```

### B. Pick “best so far” by a metric

```python
best = await arts.best(
    kind="checkpoint",
    metric="val_acc",   # must exist in artifact.metrics
    mode="max",         # or "min"
    scope="run",        # limit to current run | graph | node
)
if best:
    best_path = arts.to_local_path(best.uri)
```

> Attach `metrics={"val_acc": ...}` when saving to enable ranking later.

---

## 4. End‑to‑end: save, log, and recall

```python
@graph_fn(name="train_epoch", outputs=["ckpt_uri"])
async def train_epoch(epoch: int, *, context):
    arts = context.artifacts()
    mem  = context.memory()

    # 1) Export a checkpoint to a temp path you control
    tmp_path = "/tmp/ckpt.bin"

    # 2) Ingest it as an Artifact
    ckpt = await arts.save(
        path=tmp_path,
        kind="checkpoint",
        labels={"epoch": epoch},
        # metrics={"val_acc": val_acc},
    )

    # 3) Record the important values for quick recall
    await mem.write_result(
        topic="train.epoch",
        outputs=[
            {"name": "epoch",    "kind": "number", "value": epoch},
            {"name": "ckpt_uri", "kind": "uri",    "value": ckpt.uri},
        ],
    )

    return {"ckpt_uri": ckpt.uri}
```

Now, any later node can do:

```python
latest_uri = await context.memory().last_by_name("ckpt_uri")
path = context.artifacts().to_local_path(latest_uri)
```

---

## 5. Practical recipes

### A. Save small JSON/Text directly

```python
cfg_art = await arts.save_json({"lr": 1e-3, "batch": 64})
log_art = await arts.save_text("training finished ok")
```

### B. Browse everything produced in this run

```python
all_run_outputs = await arts.list(scope="run")
```

### C. Pin something to keep forever

```python
await arts.pin(artifact_id=cfg_art.artifact_id)
```

### D. Keep Memory lean but persistent

* Memory acts like a **fixed‑length hot queue** for fast recall (`last_by_name`, `recent`).
* **All events are persisted** for later inspection, but only a rolling window stays hot in KV for speed.

---

## 6. Minimal reference (schemas & helpers)

You rarely need all fields. Here are the **useful bits** to recognize in code and logs.

```python
@dataclass
class Artifact:
    artifact_id: str
    uri: str           # CAS URI
    kind: str          # short noun (e.g., "checkpoint", "report")
    labels: dict[str, Any]
    metrics: dict[str, Any]
    preview_uri: str | None = None
    pinned: bool = False
```

```python
@dataclass
class Event:
    event_id: str
    ts: str
    kind: str          # e.g., "tool_result", "train_log"
    topic: str | None = None
    inputs: list[Value] | None = None
    outputs: list[Value] | None = None
    metrics: dict[str, float] | None = None
    text: str | None = None   # JSON string or message text
    version: int = 1
```

Helper (already built‑in) that returns decoded payloads from `recent`:

```python
async def recent_data(*, kinds: list[str], limit: int = 50) -> list[Any]
```

---

## 7. When to use what

| Need                             | Use                                      | Why                        |
| -------------------------------- | ---------------------------------------- | -------------------------- |
| Keep a file/dir for later        | `artifacts.save(...)` / `writer(...)`    | Durable, deduped, indexed  |
| Store small JSON/Text            | `artifacts.save_json/text`               | Convenience, still indexed |
| Quick recall of named values     | `memory.write_result` → `last_by_name`   | O(1) latest lookups        |
| Log structured progress/events   | `memory.record` → `recent`/`recent_data` | Lightweight trace          |
| Pick the best checkpoint/report  | `artifacts.best(kind, metric, mode)`     | Built‑in ranking           |
| List everything from current run | `artifacts.list(scope="run")`            | One‑liner browse           |

---

## 8. RAG: turning history into answers (optional)

Memory ships with a **RAG facade** so you can promote events/results into a searchable corpus.

```python
@graph_fn(name="make_rag_corpus", outputs=["answer"])
async def make_rag_corpus(question: str, *, context):
    mem = context.memory()

    corpus = await mem.rag_bind(scope="project")
    await mem.rag_promote_events(
        corpus_id=corpus,
        where={"kinds": ["tool_result"], "limit": 200},
    )
    ans = await mem.rag_answer(corpus_id=corpus, question=question)
    snap = await mem.rag_snapshot(corpus_id=corpus, title="Weekly knowledge snapshot")
    return {"answer": ans.get("answer", ""), "snapshot_uri": snap.get("uri")}
```

Use this if you want citations and cross‑run Q&A on top of your logs.

---

## 9. Troubleshooting & tips

* **I saved without labels/metrics — can I still search?** Yes. You can list by scope and filter in Python. Add labels/metrics next time for richer queries.
* **URIs vs paths?** Always store/share **URIs**. Resolve to a path only when you need to read the bytes: `arts.to_local_path(uri)`.
* **Performance:** Keep Memory results tiny and focused (a few named values). Put large blobs in Artifacts.
* **Naming:** Re‑use a small stable set of `kind` values (e.g., `checkpoint`, `report`, `plot`). It pays off in search and dashboards.

---

## Summary

* **Artifacts**: durable results with CAS URIs, plus **labels/metrics** for search & ranking.
* **Memory**: structured **results & events** for instant recall (`last_by_name`, `recent`).
* Use them together: save outputs as Artifacts, then record the important URIs and numbers with `write_result` for fast retrieval.
* Optional: promote Memory into **RAG** to get searchable, cited answers across runs.

**See also:** `context.artifacts()` · `context.memory()` · RAG helpers (`rag_bind`, `rag_promote_events`, `rag_answer`, `rag_snapshot`)
