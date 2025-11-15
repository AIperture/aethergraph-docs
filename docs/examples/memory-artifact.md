# Memory & Artifact Mini Examples

These snippets assume you’re inside an async function where you already have:

```python
mem: MemoryFacade = context.memory()
arts: ArtifactFacade = context.artifacts()
```

They’re meant as **supplementary examples**, not main docs.

---

## 1. Events 101 – what is saved and how to read it

### 1.1 Recording a simple event

```python
# Record a simple user message as an event.
evt = await mem.record(
    kind="user_msg",
    data={"role": "user", "text": "How do I use AetherGraph?"},
    tags=["chat", "demo"],
    severity=2,
    stage="observe",
)

print("Event ID:", evt.event_id)
print("Kind:", evt.kind)
print("Text payload (JSON string):", evt.text)
```

**What happens**:

* `record(...)` JSON-serializes `data` and stores it in `evt.text`.
* Adds scope fields like `session_id`, `run_id`, `graph_id`, `node_id`, `agent_id`.
* Appends the `Event` to **HotLog** (recent buffer) and **Persistence** (JSONL).

Conceptually, an **Event** is:

> “Something happened (tool call, chat turn, metric, etc.), scoped to this session/run.”

---

### 1.2 Reading raw events vs decoded data

```python
# Raw events (Event objects)
from aethergraph.contracts.services.memory import Event

events: list[Event] = await mem.recent(kinds=["user_msg"], limit=10)
for e in events:
    print("Raw event kind:", e.kind, "text:", e.text)

# Decoded data (whatever you passed as data=...)
data_items = await mem.recent_data(kinds=["user_msg"], limit=10)
for d in data_items:
    print("Decoded data:", d)   # dict: {"role": "...", "text": "..."}
```

* `recent(...)` → `list[Event]` (full event objects).
* `recent_data(...)` → `list[Any]` using the JSON-in-`text` convention of `record()`.

Users who just want “the thing I logged” should use **`recent_data`**.

---

## 2. `write_result` & indices – structured tool/agent outputs

`write_result` is a convenience for logging structured outputs from a tool/agent
and updating indices so you can ask things like:

* “What was the last value named `result`?”
* “What are the latest outputs for `tool.calculator`?”

### 2.1 Recording a tool result

```python
# Imagine a tiny calculator tool
inputs = [
    {"name": "expression", "kind": "text", "value": "1 + 2 * 3"},
]
outputs = [
    {"name": "result", "kind": "number", "value": 7},
]

evt = await mem.write_result(
    topic="tool.calculator",      # identifier for this tool/agent
    inputs=inputs,
    outputs=outputs,
    tags=["tool", "calculator"],
    metrics={"latency_ms": 12.3},
    message="Evaluated 1 + 2 * 3",
)

print("tool_result event_id:", evt.event_id)
print("Kind:", evt.kind)   # "tool_result"
print("Tool:", evt.tool)   # "tool.calculator"
```

### 2.2 Reading via indices

```python
# 1) Last output value by name (fast)
last_result = await mem.get_last_value("result")
print("get_last_value('result') ->", last_result)
# e.g. {"name":"result","kind":"number","value":7}

# 2) Latest reference outputs by kind (e.g. "number", "json", "uri")
number_refs = await mem.get_latest_values_by_kind("number", limit=5)
print("get_latest_values_by_kind('number'):", number_refs)
# e.g. [{"name":"result","kind":"number","value":7}, ...]

# 3) Last outputs for a given topic (tool/agent)
calc_outputs = await mem.get_last_outputs_for_topic("tool.calculator")
print("get_last_outputs_for_topic('tool.calculator'):", calc_outputs)
# e.g. {"result": 7, "latency_ms": 12.3, ...} (depends on index impl)
```

**Purpose of `write_result`**:

* Normalizes tool/agent outputs into a `tool_result` event.
* Keeps HotLog + Persistence in sync.
* Updates indices so other code can quickly answer questions about *latest* outputs.

---

## 3. Artifacts 101 – save, list, search, best

An **Artifact** is an immutable asset:

* Models, reports, checkpoints, metrics files, directories, etc.
* Stored via an `AsyncArtifactStore` and indexed via `AsyncArtifactIndex`.

In agents, you normally access them through **ArtifactFacade** via `context.artifacts()`.

### 3.1 Save small text & JSON artifacts

```python
# Save a plain-text log
log_art = await arts.save_text(
    "This is a tiny experiment log.",
    suggested_uri="./logs/experiment_001.txt",
)
print("Log artifact URI:", log_art.uri)

# Save structured metrics as JSON
metrics_art = await arts.save_json(
    {"epoch": 3, "train_loss": 0.42, "val_loss": 0.55},
    suggested_uri="./metrics/exp001_epoch3.json",
)
print("Metrics artifact URI:", metrics_art.uri)
```

### 3.2 Save a file with kind/labels/metrics

```python
checkpoint_path = "./checkpoints/exp001_step100.pt"

ckpt_art = await arts.save(
    checkpoint_path,
    kind="model_checkpoint",
    labels={"experiment": "exp001", "step": "100"},
    metrics={"val_loss": 0.55},
    suggested_uri="./checkpoints/exp001_step100.pt",
    pin=True,   # mark as important/keep
)

print("Checkpoint id:", ckpt_art.id)
print("Checkpoint kind:", ckpt_art.kind)
print("Checkpoint labels:", ckpt_art.labels)
print("Checkpoint metrics:", ckpt_art.metrics)
```

---

## 4. Listing & searching artifacts (scope, labels, metrics)

### 4.1 List all artifacts for this run

```python
arts_in_run = await arts.list(scope="run")
print("Artifacts in this run:", [a.uri for a in arts_in_run])
```

### 4.2 Search by kind + label

```python
exp_ckpts = await arts.search(
    kind="model_checkpoint",
    labels={"experiment": "exp001"},
    scope="run",
)
print("Exp001 checkpoints:", [a.uri for a in exp_ckpts])
```

* `kind` narrows by artifact type.
* `labels` filters by label key/value.
* `scope` controls implicit filters:

  * `"run"` = current run only (default).
  * `"graph"` / `"node"` = more specific.
  * `"project"` / `"all"` = wider.

### 4.3 Selecting the "best" artifact by metric

```python
best_ckpt = await arts.best(
    kind="model_checkpoint",
    metric="val_loss",
    mode="min",                # minimize validation loss
    scope="run",
    filters={"experiment": "exp001"},
)

if best_ckpt:
    print("Best checkpoint (by val_loss):", best_ckpt.uri, best_ckpt.metrics)
else:
    print("No checkpoint found.")
```

Here, `best(...)` asks the index to:

* Filter by `kind` + `filters` (labels).
* Select the artifact with **min or max** on the given `metric`.

---

## 5. Loading artifacts and turning URIs into paths

### 5.1 Load payload back from the store

```python
# If the artifact payload is JSON
metrics = await arts.load_artifact(metrics_art.uri)
print("Loaded metrics json:", metrics)

# If it's bytes (e.g., a binary checkpoint)
ckpt_bytes = await arts.load_artifact_bytes(ckpt_art.uri)
print("Loaded checkpoint size:", len(ckpt_bytes))
```

### 5.2 Convert artifact URI to local filesystem path

```python
# Turn an artifact URI into a local file path (for external libs)
local_ckpt_path = arts.to_local_file(ckpt_art)
print("Local checkpoint path:", local_ckpt_path)

# Same idea for directories:
# local_dir = arts.to_local_dir(dir_artifact)
```

These helpers are handy when your artifacts are tracked as `file://...` URIs
but some library expects a plain `str` path.

---

## 6. Combining memory + artifacts

Typical pattern:

1. Agent runs a job.
2. Saves results as artifacts.
3. Logs a `tool_result` event with artifact URIs in outputs.
4. Later, uses memory indices + artifact search/load to inspect results.

```python
# 1) Save metrics as an artifact
metrics_art = await arts.save_json(
    {"epoch": 10, "train_loss": 0.21, "val_loss": 0.24},
    suggested_uri="./metrics/exp002_epoch10.json",
)

# 2) Log a structured result referencing the artifact
await mem.write_result(
    topic="trainer.exp002",
    outputs=[
        {"name": "final_val_loss", "kind": "number", "value": 0.24},
        {"name": "metrics_uri", "kind": "uri", "value": metrics_art.uri},
    ],
    tags=["training", "exp002"],
    message="Training finished for exp002",
    metrics={"epoch": 10},
)

# 3) Later: quickly get last trainer outputs via indices
trainer_outs = await mem.get_last_outputs_for_topic("trainer.exp002")
print("Trainer last outputs:", trainer_outs)
# e.g. {"final_val_loss": 0.24, "metrics_uri": "file://.../metrics/exp002_epoch10.json"}

# 4) Load the metrics artifact via the recorded URI
loaded_metrics = await arts.load_artifact(trainer_outs["metrics_uri"])
print("Loaded metrics from artifact:", loaded_metrics)
```

This example shows how **memory** (events + indices) and **artifacts** work together:

* Memory tells you *what happened last* and *which artifact URIs matter*.
* ArtifactFacade lets you search, rank, and then actually load those files.

---

## 7. RAG + Memory – turning events into searchable knowledge

RAG (Retrieval-Augmented Generation) here is wired through **MemoryFacade** to let you:

1. Create or bind to a **corpus** (a logical collection of documents/chunks).
2. **Promote events** (e.g., tool results, chat summaries) into that corpus.
3. Search / answer questions over it using an LLM.
4. Optionally snapshot or compact the corpus over time.

These examples assume `mem: MemoryFacade` is configured with a `RAGFacade`.

### 7.1 Binding to a corpus (project/session/run)

```python
# Common pattern: bind to a project-level corpus.
corpus_id = await mem.rag_bind(scope="project")
print("Using corpus:", corpus_id)

# Or a session-specific corpus
session_corpus = await mem.rag_bind(scope="session")
print("Session corpus:", session_corpus)

# Or an explicitly named key (stable across runs if you reuse it)
team_corpus = await mem.rag_bind(scope="project", key="team-alpha-notes")
print("Team corpus:", team_corpus)
```

* `scope` controls how the corpus is keyed:

  * `"project"` → tied to workspace/project.
  * `"session"` → tied to session_id.
  * `"run"` → tied to particular run (more ephemeral).
* You can override with `corpus_id=` directly if you already know the ID.

---

### 7.2 Promoting events into RAG (event → doc)

You can convert existing memory events into RAG documents with
`rag_promote_events()`.

```python
corpus_id = await mem.rag_bind(scope="project")

# Promote recent high-signal tool_result events into the corpus
stats = await mem.rag_promote_events(
    corpus_id=corpus_id,
    where={
        "kinds": ["tool_result"],   # filter by Event.kind
        "limit": 200,
    },
    policy={
        "min_signal": 0.3,           # ignore low-signal noise
        "chunk": {"size": 800, "overlap": 120},  # (if your RAG index supports chunking)
    },
)

print("Promoted events stats:", stats)
# e.g. {"added": 12, "chunks": 48, "index": "SomeIndexImpl"}
```

What happens:

* `rag_promote_events` pulls events (via `recent` or your provided `events` list).
* For each event, it builds a document:

  * `text` from `Event.text` (or a JSON of inputs/outputs/metrics).
  * `title` + `labels` derived from kind/tool/stage/tags.
* Upserts docs into the RAG index.
* Logs a `tool_result` under topic `rag.promote.<corpus_id>` for traceability.

You can also pass `events=` yourself if you already filtered them manually.

---

### 7.3 Direct upsert of custom docs (bypassing events)

If you just have ad-hoc docs (e.g., notes, specs), you can call `rag_upsert`:

```python
corpus_id = await mem.rag_bind(scope="project")

docs = [
    {
        "text": "AetherGraph is a framework for building agentic graphs.",
        "title": "AG overview",
        "labels": {"topic": "overview", "source": "docs"},
    },
    {
        "text": "MemoryFacade coordinates HotLog, Persistence, Indices, and optional RAG.",
        "title": "MemoryFacade design",
        "labels": {"topic": "memory", "source": "notes"},
    },
]

upsert_stats = await mem.rag_upsert(corpus_id=corpus_id, docs=docs)
print("RAG upsert stats:", upsert_stats)
```

This bypasses events entirely and goes straight to documents.

---

### 7.4 Searching the corpus

Once docs are in the corpus, you can run semantic/hybrid search:

```python
corpus_id = await mem.rag_bind(scope="project")

hits = await mem.rag_search(
    corpus_id=corpus_id,
    query="How does the memory system work?",
    k=5,
    filters={"topic": "memory"},  # optional label filter
    mode="hybrid",                 # or "dense"
)

for h in hits:
    print("Score:", h["score"])
    print("Title:", h["meta"].get("title"))
    print("Text snippet:", h["text"][:120], "...")
    print("Labels:", h["meta"].get("labels"))
    print("---")
```

`rag_search` returns a list of serializable dicts:

* `text`  – chunk text.
* `meta`  – metadata (labels, title, etc.).
* `score` – similarity/relevance score.

---

### 7.5 RAG answer – retrieval + LLM + citations

For “ask a question over everything in the corpus” you use `rag_answer`:

```python
corpus_id = await mem.rag_bind(scope="project")

answer = await mem.rag_answer(
    corpus_id=corpus_id,
    question="Summarize how MemoryFacade and ArtifactFacade work together.",
    style="concise",          # or "detailed"
    with_citations=True,
    k=6,
)

print("Answer:\n", answer.get("answer"))
print("Citations:")
for c in answer.get("resolved_citations", []):
    print("- From doc:", c.get("doc_id"), "score=", c.get("score"))
```

`rag_answer` will:

1. Run retrieval over the corpus.
2. Call the LLM with retrieved chunks.
3. Return an `answer` plus `resolved_citations`.
4. Log a `tool_result` under topic `rag.answer.<corpus_id>` with outputs
   and usage metrics (via `write_result`).

---

<!-- ### 7.6 Snapshot & compact – housekeeping

Once your corpus grows, you might want to snapshot or compact it.

```python
corpus_id = await mem.rag_bind(scope="project")

# Snapshot: export corpus into an artifact bundle (e.g., a tar/zip or directory)
snap = await mem.rag_snapshot(
    corpus_id=corpus_id,
    title="Project-wide RAG snapshot",
    labels={"project": "demo"},
)
print("Snapshot bundle URI:", snap.get("uri"))

# Compact: re-embed or prune (policy is currently simple)
compact_stats = await mem.rag_compact(
    corpus_id=corpus_id,
    policy={"reembed_model": "my-new-embedding-model"},
)
print("Compaction stats:", compact_stats)
``` -->

These helpers are optional, but they show how the RAG integration fits the
same pattern as memory + artifacts:

* **Memory**: events + indices for “what happened and when?”.
* **Artifacts**: big immutable assets (files, bundles) with labels/metrics.
* **RAG**: a semantic index over the *content* of your events/docs, used by
  your agents via standard tools (`rag_search`, `rag_answer`, etc.).
