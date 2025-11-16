# `context.artifacts()` – ArtifactFacade API Reference

The `ArtifactFacade` wraps an `AsyncArtifactStore` (persistence) and an `AsyncArtifactIndex` (search/metadata) and automatically indexes artifacts you create within a node/run.

---

## Concepts & Defaults

* **Store vs Index:** `store` persists bytes/objects; `index` stores searchable metadata and supports ranking, pinning, and scoping.
* **Automatic indexing:** `ingest`, `save*`, `writer`, and `ingest_dir` all **upsert** into the index and **record an occurrence**.
* **Scoping:** Many queries default to the **current run**; you can widen to `"graph"`, `"node"`, or `"all"`.
* **`last_artifact`:** Updated to the most recently created/ingested artifact when applicable; `None` otherwise (e.g., no write in `writer`).
* **`suggested_uri`:** A hint for stores that support friendly paths; stores may ignore or normalize it.
* **`pin`:** Marks an artifact as pinned in the index to prevent GC or to highlight in UIs (store behavior may vary).

### Artifact Schema (contract)

A minimal summary of `Artifact` fields for reference:

```
Artifact(
  artifact_id: str,
  uri: str,
  kind: str,
  bytes: int,
  sha256: str,
  mime: str | None,
  run_id: str, graph_id: str, node_id: str,
  tool_name: str, tool_version: str,
  created_at: str,
  labels: dict[str, Any],
  metrics: dict[str, Any],
  preview_uri: str | None = None,
  pinned: bool = False,
)
```

---

## Quick Reference

| Method                                                                                            | Purpose                              | Returns             |       |
| ------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------- | ----- |
| `stage(ext="")`                                                                                   | Plan a staging file path             | `str` path          |       |
| `ingest(staged_path, *, kind, labels=None, metrics=None, suggested_uri=None, pin=False)`          | Ingest a staged file and index it    | `Artifact`          |       |
| `save(path, *, kind, labels=None, metrics=None, suggested_uri=None, pin=False)`                   | Save an existing file and index it   | `Artifact`          |       |
| `save_text(payload, *, suggested_uri=None)`                                                       | Save small text as an artifact       | `Artifact`          |       |
| `save_json(payload, *, suggested_uri=None)`                                                       | Save JSON-serializable object        | `Artifact`          |       |
| `writer(*, kind, planned_ext=None, pin=False)`                                                    | Open a write context (yields writer) | *(context manager)* |       |
| `stage_dir(suffix="")`                                                                            | Plan a staging directory             | `str` path          |       |
| `ingest_dir(staged_dir, **kw)`                                                                    | Ingest a whole directory             | `Artifact`          |       |
| `tmp_path(suffix="")`                                                                             | Alias to plan a staging file path    | `str` path          |       |
| `load_bytes(uri)`                                                                                 | Read raw bytes                       | `bytes`             |       |
| `load_text(uri, *, encoding="utf-8", errors="strict")`                                            | Read text                            | `str`               |       |
| `load_json(uri, *, encoding="utf-8", errors="strict")`                                            | Read JSON                            | `Any`               |       |
| `load_artifact(uri)`                                                                              | Load Artifact metadata/object        | `Artifact           | Any`  |
| `load_artifact_bytes(uri)`                                                                        | Read bytes from artifact URI         | `bytes`             |       |
| `list(*, scope="run")`                                                                            | List artifacts by scope              | `list[Artifact]`    |       |
| `search(*, kind=None, labels=None, metric=None, mode=None, scope="run", extra_scope_labels=None)` | Search with filters/metrics          | `list[Artifact]`    |       |
| `best(*, kind, metric, mode, scope="run", filters=None)`                                          | Best-scoring artifact                | `Artifact           | None` |
| `pin(artifact_id, pinned=True)`                                                                   | Pin/unpin in the index               | `None`              |       |
| `to_local_path(uri_or_path, *, must_exist=True)`                                                  | Resolve to local path (file:// only) | `str`               |       |
| `to_local_file(uri_or_path, *, must_exist=True)`                                                  | Resolve & assert file                | `str`               |       |
| `to_local_dir(uri_or_path, *, must_exist=True)`                                                   | Resolve & assert dir                 | `str`               |       |

---

## Methods

<details markdown="1">
<summary>stage(ext="") -> str</summary>

**Description:** Plan a **staging file** location for temporary writes outside the index. Use with external writers, then call `ingest()`.

**Inputs:**

* `ext: str` – Optional extension (e.g., `.png`, `.txt`).

**Returns:**

* `str` – Path to a writable staging file.

**Notes:** Staging does not create or index the artifact; call `ingest()` afterward.

</details>

<details markdown="1">
<summary>ingest(staged_path, *, kind, labels=None, metrics=None, suggested_uri=None, pin=False) -> Artifact</summary>

**Description:** Ingest a previously **staged file** into the store, then **upsert** & **record occurrence** in the index.

**Inputs:**

* `staged_path: str`
* `kind: str` – Domain tag (e.g., `"image"`, `"report"`).
* `labels: dict | None`
* `metrics: dict | None`
* `suggested_uri: str | None`
* `pin: bool` – Mark as pinned in the index.

**Returns:**

* `Artifact`

**Notes:** Sets `last_artifact` to the newly ingested item.

</details>

<details markdown="1">
<summary>save(path, *, kind, labels=None, metrics=None, suggested_uri=None, pin=False) -> Artifact</summary>

**Description:** Save an **existing file** to the store and index it.

**Inputs:**

* `path: str`
* `kind: str`
* `labels: dict | None`
* `metrics: dict | None`
* `suggested_uri: str | None`
* `pin: bool`

**Returns:**

* `Artifact`

**Notes:** Updates `last_artifact`.

</details>

<details markdown="1">
<summary>save_text(payload, *, suggested_uri=None) -> Artifact</summary>

**Description:** Save a **small text blob**; store chooses encoding/URI. Indexed automatically.

**Inputs:**

* `payload: str`
* `suggested_uri: str | None`

**Returns:**

* `Artifact`

**Notes:** Prefer `save()` for large files; stores may have size limits for text.

</details>

<details markdown="1">
<summary>save_json(payload, *, suggested_uri=None) -> Artifact</summary>

**Description:** Save a **JSON-serializable object**.

**Inputs:**

* `payload: dict`
* `suggested_uri: str | None`

**Returns:**

* `Artifact`

**Notes:** Useful for configs, specs, and structured reports.

</details>

<details markdown="1">
<summary>writer(*, kind, planned_ext=None, pin=False) -> Async CM (yields writer)</summary>

**Description:** Open a **writer context** provided by the store; write bytes within the block. On exit, the created artifact (if any) is indexed.

**Inputs:**

* `kind: str`
* `planned_ext: str | None` – Hint for file extension.
* `pin: bool`

**Returns:**

* *(Context Manager)* – Yields a `writer` implementing `write(...)` (store-specific).

**Notes:**

* If the writer actually creates an artifact, it will be available as `writer._artifact` on exit and set as `last_artifact`.
* Use this when you don’t have the data on disk yet and want the store to manage file lifecycle.

**Example:**

```python
async with context.artifacts().writer(kind="report", planned_ext=".txt") as w:
    w.write(b"hello world")
# last_artifact now refers to the saved report
```

</details>

<details markdown="1">
<summary>stage_dir(suffix="") -> str</summary>

**Description:** Plan a **staging directory** path. Use with tools that emit multiple files before ingestion.

**Inputs:**

* `suffix: str` – Optional suffix/name.

**Returns:**

* `str` – Path to a staging directory.

</details>

<details markdown="1">
<summary>ingest_dir(staged_dir, **kw) -> Artifact</summary>

**Description:** Ingest a **directory** (e.g., a report folder) into the store and index it.

**Inputs:**

* `staged_dir: str`
* `**kw` – Store/index-specific options (e.g., `kind`, `labels`, `metrics`, `pin`).

**Returns:**

* `Artifact`

**Notes:** Updates `last_artifact`.

</details>

<details markdown="1">
<summary>tmp_path(suffix="") -> str</summary>

**Description:** Convenience alias to plan a **staging file** path.

**Inputs:**

* `suffix: str`

**Returns:**

* `str`

</details>

<details markdown="1">
<summary>load_bytes(uri) -> bytes</summary>

**Description:** Load **raw bytes** from an artifact URI.

**Inputs:**

* `uri: str`

**Returns:**

* `bytes`

</details>

<details markdown="1">
<summary>load_text(uri, *, encoding="utf-8", errors="strict") -> str</summary>

**Description:** Load **text** from an artifact URI.

**Inputs:**

* `uri: str`
* `encoding: str`
* `errors: str`

**Returns:**

* `str`

</details>

<details markdown="1">
<summary>load_json(uri, *, encoding="utf-8", errors="strict") -> Any</summary>

**Description:** Load **JSON** from an artifact URI.

**Inputs:**

* `uri: str`
* `encoding: str`
* `errors: str`

**Returns:**

* `Any`

</details>

<details markdown="1">
<summary>load_artifact(uri) -> Artifact | Any</summary>

**Description:** Load an **Artifact** or store-specific artifact object from URI.

**Inputs:**

* `uri: str`

**Returns:**

* `Artifact | Any`

</details>

<details markdown="1">
<summary>load_artifact_bytes(uri) -> bytes</summary>

**Description:** Load **bytes** from an artifact URI (explicit artifact pathway).

**Inputs:**

* `uri: str`

**Returns:**

* `bytes`

</details>

<details markdown="1">
<summary>list(*, scope="run") -> list[Artifact]</summary>

**Description:** Quick listing of artifacts **scoped** to `"run"` by default.

**Inputs:**

* `scope: Literal["node", "run", "graph", "all"]`

**Returns:**

* `list[Artifact]`

**Notes:**

* `node` → labels `(run_id, graph_id, node_id)`; `graph` → `(run_id, graph_id)`; `run` → by `run_id`; `all` → no implicit filters.

</details>

<details markdown="1">
<summary>search(*, kind=None, labels=None, metric=None, mode=None, scope="run", extra_scope_labels=None) -> list[Artifact]</summary>

**Description:** Search the index with optional **kind**, **labels**, and **metric ranking**.

**Inputs:**

* `kind: str | None`
* `labels: dict[str, Any] | None`
* `metric: str | None`
* `mode: Literal["max", "min"] | None`
* `scope: Literal["node", "run", "graph", "all"]`
* `extra_scope_labels: dict[str, Any] | None`

**Returns:**

* `list[Artifact]`

**Notes:** Applies scope labels automatically when scope is `node` or `graph`. `extra_scope_labels` lets you add more filters.

</details>

<details markdown="1">
<summary>best(*, kind, metric, mode, scope="run", filters=None) -> Artifact | None</summary>

**Description:** Return the **best-scoring** artifact for a metric (e.g., highest accuracy).

**Inputs:**

* `kind: str`
* `metric: str`
* `mode: Literal["max", "min"]`
* `scope: Literal["node", "run", "graph", "all"]`
* `filters: dict[str, Any] | None`

**Returns:**

* `Artifact | None`

**Notes:** Applies scope filters automatically for `node` or `graph`.

</details>

<details markdown="1">
<summary>pin(artifact_id, pinned=True) -> None</summary>

**Description:** Pin or unpin an artifact in the index.

**Inputs:**

* `artifact_id: str`
* `pinned: bool`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>to_local_path(uri_or_path, *, must_exist=True) -> str</summary>

**Description:** Resolve a **file://** URI or local path to an absolute native path.

**Inputs:**

* `uri_or_path: str | Path | Artifact`
* `must_exist: bool`

**Returns:**

* `str` – Absolute path or input string for non-file schemes.

**Notes:**

* If the input uses a non-file scheme (e.g., `s3://`, `http://`), the string is returned unchanged.
* Raises `FileNotFoundError` if `must_exist=True` and path missing.

</details>

<details markdown="1">
<summary>to_local_file(uri_or_path, *, must_exist=True) -> str</summary>

**Description:** Resolve to a **file path** and assert it is a file.

**Inputs:**

* `uri_or_path: str | Path | Artifact`
* `must_exist: bool`

**Returns:**

* `str`

**Notes:** Raises `IsADirectoryError` if path is a directory when `must_exist=True`.

</details>

<details markdown="1">
<summary>to_local_dir(uri_or_path, *, must_exist=True) -> str</summary>

**Description:** Resolve to a **directory path** and assert it is a directory.

**Inputs:**

* `uri_or_path: str | Path | Artifact`
* `must_exist: bool`

**Returns:**

* `str`

**Notes:** Raises `NotADirectoryError` if path is a file when `must_exist=True`.

</details>
