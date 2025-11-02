# AetherGraph — `context.artifacts()` Reference

This page documents the **ArtifactFacade** methods returned by `context.artifacts()` in a concise format: signature, brief description, parameters, and returns — plus examples for `writer()` and scoped search.

---

## Overview
`context.artifacts()` returns an **ArtifactFacade** bound to the current `run_id`, `graph_id`, and `node_id`. It wraps an `AsyncArtifactStore` for persistence and an `AsyncArtifactIndex` for search/pinning/metrics. Most mutating ops auto‑index and record an occurrence.

**Typical flow**

1. Stage (optional) → write → ingest

2. Or directly save an existing file path

3. Or use the built‑in `writer()` context manager to stream bytes and auto‑index

---

## artifacts.stage
```
stage(ext: str = "") -> str
```
Plan a staging file path (temporary path) with an optional extension.

**Parameters**

- **ext** (*str, optional*) – Suggested extension (e.g., ".png", ".csv").

**Returns**  
*str* – Staging file path.

---

## artifacts.ingest
```
ingest(staged_path: str, *, kind: str, labels=None, metrics=None, suggested_uri: str | None = None, pin: bool = False) -> Artifact
```
Ingest a previously staged file into the store, attach metadata, and auto‑index.

**Parameters**

- **staged_path** (*str*) – Path returned by `stage()` or `stage_dir()`.

- **kind** (*str*) – Logical artifact kind (e.g., "image", "table", "model").

- **labels** (*dict, optional*) – Arbitrary labels; merged into index filters.

- **metrics** (*dict, optional*) – Numeric metrics used for `best()` queries.

- **suggested_uri** (*str, optional*) – Hint for final URI; store may ignore.

- **pin** (*bool*) – Mark artifact as pinned in the index.

**Returns**  
*Artifact* – Indexed artifact record.

---

## artifacts.save
```
save(path: str, *, kind: str, labels=None, metrics=None, suggested_uri: str | None = None, pin: bool = False) -> Artifact
```
Save an existing on‑disk file to the store with metadata; auto‑index and record occurrence. Sets `last_artifact`.

**Parameters**

- **path** (*str*) – Existing file path to persist.

- **kind** (*str*) – Logical artifact kind.

- **labels** (*dict, optional*) – Arbitrary labels.

- **metrics** (*dict, optional*) – Numeric metrics.

- **suggested_uri** (*str, optional*) – Hint for final URI; store may ignore.

- **pin** (*bool*) – Mark artifact as pinned.

**Returns**  
*Artifact* – Indexed artifact record.

---

## artifacts.writer
```
writer(*, kind: str, planned_ext: str | None = None, pin: bool = False) -> AsyncContextManager[Writer]
```
Open a binary writer context that persists bytes as an artifact; auto‑indexes on exit. Sets `last_artifact`.

**Parameters**

- **kind** (*str*) – Logical artifact kind.

- **planned_ext** (*str, optional*) – Extension hint for underlying temp file.

- **pin** (*bool*) – Mark resulting artifact as pinned.

**Yields**  
*Writer* – File‑like object; write bytes and close by exiting the context.

**Example**
```python
from aethergraph import graph_fn

@graph_fn(name="make_png")
async def make_png(*, context):
    import PIL.Image as Image
    img = Image.new("RGB", (128, 128), (255, 122, 26))
    async with context.artifacts().writer(kind="image", planned_ext=".png") as w:
        # writer exposes a real file handle underneath
        img.save(w, format="PNG")
    art = context.artifacts().last_artifact
    await context.channel().send_image(url=art.uri, title="Generated PNG")
    return {"uri": art.uri}
```

---

## artifacts.stage_dir
```
stage_dir(suffix: str = "") -> str
```
Plan a staging **directory** for multi‑file artifacts.

**Parameters**

- **suffix** (*str, optional*) – Optional directory suffix.

**Returns**  
*str* – Staging directory path.

---

## artifacts.ingest_dir
```
ingest_dir(staged_dir: str, **kw) -> Artifact
```
Ingest a directory of files as a single logical artifact; forwards extra keyword args to the store.

**Parameters**

- **staged_dir** (*str*) – Directory created by `stage_dir()`.

- **kw** – Store‑specific options (e.g., kind/labels/metrics/pin).

**Returns**  
*Artifact* – Indexed artifact record.

---

## artifacts.tmp_path
```
tmp_path(suffix: str = "") -> str
```
Alias of `stage()` for convenience.

**Parameters**

- **suffix** (*str, optional*) – Extension or suffix.

**Returns**  
*str* – Staging file path.

---

## artifacts.load_artifact
```
load_artifact(uri: str) -> Any
```
Load a previously saved artifact by URI, using the store’s type‑specific loader.

**Parameters**

- **uri** (*str*) – Artifact URI.

**Returns**  
*Any* – Decoded object (depends on store & artifact type).

---

## artifacts.load_artifact_bytes
```
load_artifact_bytes(uri: str) -> bytes
```
Load raw bytes for a previously saved artifact by URI.

**Parameters**

- **uri** (*str*) – Artifact URI.

**Returns**  
*bytes* – Artifact content.

---

## artifacts.list
```
list(*, scope: Literal["node","run","graph","project","all"] = "run") -> list[Artifact]
```
Quick listing with **implicit scoping** (defaults to the current run). Under the hood, this uses the index with reasonable filters for the given scope.

**Parameters**

- **scope** (*str*) – One of:

  - **"node"** – filter by *(run_id, graph_id, node_id)*  

  - **"graph"** – filter by *(run_id, graph_id)*  

  - **"run"** – filter by *(run_id)* **(default)**  

  - **"project"** – filter by project/org if tracked in labels  

  - **"all"** – no implicit filters (use sparingly)

**Returns**  
*list[Artifact]* – Matching artifacts.

---

## artifacts.search
```
search(*, kind: str | None = None, labels: dict | None = None, metric: str | None = None, mode: Literal["max","min"] | None = None, scope: Scope = "run", extra_scope_labels: dict | None = None) -> list[Artifact]
```
Index search with **automatic scoping**. Merges your `labels` with scope‑derived labels.

**Parameters**

- **kind** (*str, optional*) – Filter by artifact kind.

- **labels** (*dict, optional*) – Arbitrary label filters.

- **metric** (*str, optional*) – Metric name for ranking.

- **mode** (*{"max","min"}, optional*) – Ranking direction.

- **scope** (*Scope*) – Implicit scope (default: "run").

- **extra_scope_labels** (*dict, optional*) – Additional scope labels to merge.

**Returns**  
*list[Artifact]* – Search results.

**Example (scoped search)**
```python
best_imgs = await context.artifacts().search(kind="image", scope="graph")
```

---

## artifacts.best
```
best(*, kind: str, metric: str, mode: Literal["max","min"], scope: Scope = "run", filters: dict | None = None) -> Artifact | None
```
Return the **best** artifact by a metric, with optional filters and implicit scope.

**Parameters**

- **kind** (*str*) – Artifact kind.

- **metric** (*str*) – Metric key.

- **mode** (*{"max","min"}*) – Ranking direction.

- **scope** (*Scope*) – Implicit scope (default: "run").

- **filters** (*dict, optional*) – Additional label filters.

**Returns**  
*Artifact | None* – Best match or `None` if not found.

---

## artifacts.pin
```
pin(artifact_id: str, pinned: bool = True) -> None
```
Pin or unpin an artifact in the index.

**Parameters**

- **artifact_id** (*str*) – ID of the artifact to (un)pin.

- **pinned** (*bool*) – `True` to pin; `False` to unpin.

**Returns**  
`None`

---

## Scoping details
The facade enriches queries with labels depending on the `scope` argument:

- **node** → `{ graph_id, node_id }`  

- **graph** → `{ graph_id }`  

- **project** → `{ project_id }` (if tracked)  

- **run** → uses `list_for_run(run_id)`  

- **all** → passes through to index with no implicit labels

---

## Practical examples

**1) Direct save**
```python
uri = "/tmp/plot.png"
# ... generate image to uri ...
art = await context.artifacts().save(uri, kind="image", labels={"task":"eval"}, metrics={"psnr": 31.2})
```

**2) Stage → write → ingest**
```python
staged = await context.artifacts().stage(".csv")
with open(staged, "w", encoding="utf-8") as f:
    f.write("x,y\n1,2\n3,4\n")
art = await context.artifacts().ingest(staged_path=staged, kind="table", labels={"split":"val"})
```

**3) Search best**
```python
winner = await context.artifacts().best(kind="model", metric="val_acc", mode="max", scope="run")
if winner:
    await context.channel().send_text(f"Best model: {winner.uri} acc={winner.metrics['val_acc']:.3f}")
```

**4) Multi‑file directory**
```python
dir_path = await context.artifacts().stage_dir("_report")
# ... write several files to dir_path ...
art = await context.artifacts().ingest_dir(dir_path, kind="report", labels={"format":"html"})
```

**5) Pin**
```python
await context.artifacts().pin(artifact_id=art.id, pinned=True)
```
