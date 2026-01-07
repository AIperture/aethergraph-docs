# Tutorial 4: Store & Recall — Artifacts and Memory

This tutorial focus on the how Aethergraph can memorize what happened before. Learn how to **save outputs**, **log results/events**, and **recall them later** using AetherGraph’s two persistence pillars:

* **Artifacts** — durable assets (files/dirs/JSON/text) stored by **content address (CAS URI)** with labels & metrics for ranking and search.
* **Memory** — a structured **event & result log** with fast “what’s the latest?” simple recent‑history queries.

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
art = await arts.save_file(
    path="/tmp/report.pdf",
    kind="report",                 # a short noun; you’ll filter/rank by this
    labels={"exp": "A"},           # 1–3 filters you actually plan to query
    # metrics={"bleu": 31.2},      # optional if you’ll rank later
)

# When you need a real path again:
path = await arts.as_local_file(art)
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
await mem.record_tool_result(
    tool="train.step",
    outputs=[
        {"name": "val_acc",  "kind": "number", "value": 0.912},
        {"name": "ckpt_uri", "kind": "uri",    "value": uri},
    ],
)

recent = await mem.recent_tool_results(tool="train.step", limit=10) # retrieve the last tool result events
```

### B. Log arbitrary events (structured but lightweight)

```python
await mem.record(
    kind="train_log",
    data={"epoch": 1, "loss": 0.25, "acc": 0.91},
)

recent = await mem.recent(kinds=["train_log"], limit=3) # recent is an Event
```

You will need to load the data from seriazalized `recent.text` (`channel.memory()` [docs](../reference/context-memory.md))

Need only the decoded payloads?

```python
logs = await mem.recent_data(kinds=["train_log"], limit=3) # this returns the `data` saved in memory, not Event
```

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
    best_path = await arts.as_local_file(best)
```

> Attach `metrics={"val_acc": ...}` when saving to enable ranking later.

---

## 4. Practical recipes

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

## 5. Minimal reference (schemas & helpers)

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

## 6. When to use what

| Need                             | Use                                      | Why                        |
| -------------------------------- | ---------------------------------------- | -------------------------- |
| Keep a file/dir for later        | `artifacts.save_file(...)` / `writer(...)`    | Durable, deduped, indexed  |
| Store small JSON/Text            | `artifacts.save_json/text`               | Convenience, still indexed |
| Log structured progress/events   | `memory.record` → `recent`/`recent_data` | Lightweight trace          |
| Pick the best checkpoint/report  | `artifacts.best(kind, metric, mode)`     | Built‑in ranking           |
| List everything from current run | `artifacts.list(scope="run")`            | One‑liner browse           |

