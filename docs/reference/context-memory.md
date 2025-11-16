# `context.memory()` – MemoryFacade API Reference

`MemoryFacade` coordinates **HotLog** (fast recent events), **Persistence** (durable JSONL event log + JSON blobs), and **Indices** (derived KV views), with optional **Artifacts** and **RAG** helpers. All public methods are async.

---

## Concepts & Defaults

* **Three core services**

  * **HotLog**: append/recent for fast, transient access (TTL, ring buffer).
  * **Persistence**: durable append/replay (e.g., FS JSONL, S3, DB).
  * **Indices**: fast lookups (e.g., last by name/topic, latest refs by kind), updated by `write_result()`.
* **Scope binding**: Instance carries `{run_id, graph_id, node_id, agent_id}` and stamps them on events.
* **Signal heuristic**: If not provided, `record_raw()` estimates a `signal` (0.0–1.0) from text length, metrics, and severity.
* **RAG integration**: Optional `RAGFacade` for corpora, upserts, search, and QA; gated by configuration.

### Event Schema (contract excerpt)

Essential `Event` fields used by this facade (not exhaustive):

```
Event(
  event_id: str, ts: str, kind: str, stage: str | None, severity: int,
  text: str | None, metrics: dict[str, Any] | None, signal: float | None,
  tool: str | None, tags: list[str], entities: list[str],
  inputs: list[dict] | None, outputs: list[dict] | None,
  run_id: str, graph_id: str | None, node_id: str | None, agent_id: str | None,
)
```

---

## Quick Reference

| Method                                                                                                                                             | Purpose                                             | Returns           |       |       |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ----------------- | ----- | ----- |
| `record_raw(*, base, text=None, metrics=None, sources=None)`                                                                                       | Append normalized event to HotLog + Persistence     | `Event`           |       |       |
| `record(kind, data, tags=None, entities=None, severity=2, stage=None, inputs_ref=None, outputs_ref=None, metrics=None, sources=None, signal=None)` | Convenience wrapper that stringifies `data`         | `Event`           |       |       |
| `write_result(*, topic, inputs=None, outputs=None, tags=None, metrics=None, message=None, severity=3)`                                             | Record a typed tool/agent result and update indices | `Event`           |       |       |
| `recent(*, kinds=None, limit=50)`                                                                                                                  | Recent events from HotLog                           | `list[Event]`     |       |       |
| `recent_data(*, kinds, limit=50)`                                                                                                                  | Recent events → decoded JSON/text list              | `list[Any]`       |       |       |
| `rag_upsert(*, corpus_id, docs, topic=None)`                                                                                                       | Upsert docs into RAG                                | `dict` stats      |       |       |
| `rag_bind(*, corpus_id=None, key=None, create_if_missing=True, labels=None)`                                                                       | Get/create corpus id                                | `str` corpus_id   |       |       |
| `rag_status(*, corpus_id)`                                                                                                                         | Corpus stats                                        | `dict`            |       |       |
| `rag_snapshot(*, corpus_id, title, labels=None)`                                                                                                   | Export corpus as artifact bundle and log result     | `dict` bundle     |       |       |
| `rag_promote_events(*, corpus_id, events=None, where=None, policy=None)`                                                                           | Convert events → docs → upsert                      | `dict` stats      |       |       |
| `rag_search(*, corpus_id, query, k=8, filters=None, mode="hybrid")`                                                                                | Hybrid/dense search                                 | `list[dict]` hits |       |       |
| `rag_answer(*, corpus_id, question, style="concise", with_citations=True, k=6)`                                                                    | Answer with citations + log                         | `dict` answer     |       |       |
| `last_by_name(name)`                                                                                                                               | Latest output value by name (fast)                  | `dict             | Any   | None` |
| `last_outputs_by_topic(topic)`                                                                                                                     | Latest outputs map for a topic                      | `dict[str, Any]   | None` |       |


---

## Methods

<details markdown="1">
<summary>record_raw(*, base, text=None, metrics=None, sources=None) -> Event</summary>

**Description:** Append a normalized `Event` to **HotLog** (fast) and **Persistence** (durable). Stamps missing scope fields and computes a lightweight `signal` if absent.

**Inputs:**

* `base: dict[str, Any]` – Must include classification fields like `kind`, `stage`, `severity`, `tool` (optional), `tags`, `entities`, `inputs`, `outputs`. Missing scope fields are added.
* `text: str | None` – Optional human-readable message.
* `metrics: dict[str, Any] | None` – Numeric map (latency, token counts, costs, etc.).
* `sources: list[str] | None` – Upstream event_ids this event derives from.

**Returns:**

* `Event`

**Notes:**

* Does **not** update `indices` automatically. Use `write_result()` for index updates.

</details>

<details markdown="1">
<summary>record(kind, data, tags=None, entities=None, severity=2, stage=None, inputs_ref=None, outputs_ref=None, metrics=None, sources=None, signal=None) -> Event</summary>

**Description:** Convenience wrapper around `record_raw()`; stringifies `data` to `text` (JSON if possible).

**Inputs:**

* `kind: str`
* `data: Any` – Will be stringified; if non-serializable, a warning is logged (when logger is set).
* `tags: list[str] | None`
* `entities: list[str] | None`
* `severity: int`
* `stage: str | None`
* `inputs_ref: list[dict] | None`
* `outputs_ref: list[dict] | None`
* `metrics: dict[str, Any] | None`
* `sources: list[str] | None`
* `signal: float | None`

**Returns:**

* `Event`

</details>

<details markdown="1">
<summary>write_result(*, topic, inputs=None, outputs=None, tags=None, metrics=None, message=None, severity=3) -> Event</summary>

**Description:** Record a typed **tool/agent result** (`kind="tool_result"`) and update **Indices** (latest-by-name, latest refs by kind, last outputs-by-topic).

**Inputs:**

* `topic: str` – Tool/agent/flow identifier (used in indices).
* `inputs: list[dict] | None` – List of typed values (`Value`-like dicts).
* `outputs: list[dict] | None` – **Primary source** for index updates.
* `tags: list[str] | None`
* `metrics: dict[str, float] | None`
* `message: str | None`
* `severity: int`

**Returns:**

* `Event`

</details>

<details markdown="1">
<summary>recent(*, kinds=None, limit=50) -> list[Event]</summary>

**Description:** Get recent events from **HotLog** (most recent last).

**Inputs:**

* `kinds: list[str] | None`
* `limit: int`

**Returns:**

* `list[Event]`

</details>

<details markdown="1">
<summary>recent_data(*, kinds, limit=50) -> list[Any]</summary>

**Description:** Convenience wrapper returning decoded `data` payloads (prefers JSON decode; falls back to raw text).

**Inputs:**

* `kinds: list[str]`
* `limit: int`

**Returns:**

* `list[Any]`

</details>

--- 

<details markdown="1">
<summary>rag_upsert(*, corpus_id, docs, topic=None) -> dict</summary>

**Description:** Upsert documents into a **RAG** corpus via `RAGFacade`.

**Inputs:**

* `corpus_id: str`
* `docs: Sequence[dict[str, Any]]` – Each doc should include `text` and optional `title`, `labels`.
* `topic: str | None` – Reserved for future logging (not used in current function body).

**Returns:**

* `dict` – Stats from index (e.g., `added`, `chunks`).

**Notes:** Requires `self.rag` configured; otherwise raises `RuntimeError`.

</details>

<details markdown="1">
<summary>rag_bind(*, corpus_id=None, key=None, create_if_missing=True, labels=None) -> str</summary>

**Description:** Return a corpus id, optionally creating it. If `corpus_id` is omitted, a stable id is derived from `key` (or `run_id`).

**Inputs:**

* `corpus_id: str | None`
* `key: str | None` – If not provided, `run_id` is used.
* `create_if_missing: bool`
* `labels: dict | None`

**Returns:**

* `str` – Corpus id.

**Notes:** Requires `self.rag` configured.

</details>

<details markdown="1">
<summary>rag_status(*, corpus_id) -> dict</summary>

**Description:** Lightweight corpus stats.

**Inputs:**

* `corpus_id: str`

**Returns:**

* `dict`

**Notes:** Requires `self.rag`.

</details>

<details markdown="1">
<summary>rag_snapshot(*, corpus_id, title, labels=None) -> dict</summary>

**Description:** Export corpus to an **artifact bundle** and log a `tool_result`.

**Inputs:**

* `corpus_id: str`
* `title: str`
* `labels: dict | None`

**Returns:**

* `dict` – Bundle descriptor `{ uri, ... }`.

**Notes:** Requires `self.rag`. Uses `write_result()` to record bundle URI.

</details>

<details markdown="1">
<summary>rag_promote_events(*, corpus_id, events=None, where=None, policy=None) -> dict</summary>

**Description:** Select events (by `where` or `recent`) → convert to docs → upsert into RAG.

**Inputs:**

* `corpus_id: str`
* `events: list[Event] | None`
* `where: dict | None` – e.g., `{ "kinds": ["tool_result"], "min_signal": 0.25, "limit": 200 }`.
* `policy: dict | None` – e.g., `{ "min_signal": float }`.

**Returns:**

* `dict` – Upsert stats (e.g., `added`, `chunks`).

**Notes:** Requires `self.rag`. Also logs a `tool_result` with counts.

</details>

<details markdown="1">
<summary>rag_search(*, corpus_id, query, k=8, filters=None, mode="hybrid") -> list[dict]</summary>

**Description:** Search a RAG corpus and return serializable hits.

**Inputs:**

* `corpus_id: str`
* `query: str`
* `k: int`
* `filters: dict | None`
* `mode: Literal["hybrid", "dense"]`

**Returns:**

* `list[dict]` – Each hit includes `chunk_id`, `doc_id`, `corpus_id`, `score`, `text`, `meta`.

**Notes:** Requires `self.rag`.

</details>

<details markdown="1">
<summary>rag_answer(*, corpus_id, question, style="concise", with_citations=True, k=6) -> dict</summary>

**Description:** Answer with citations using RAG + optional LLM; logs the answer as a `tool_result` (with usage metrics when available).

**Inputs:**

* `corpus_id: str`
* `question: str`
* `style: Literal["concise", "detailed"]`
* `with_citations: bool`
* `k: int`

**Returns:**

* `dict` – Includes `answer`, `citations`/`resolved_citations`, and `usage` (if provided by LLM).

**Notes:** Requires `self.rag`. Outputs are flattened into `write_result()` for indexing.

</details>

---

<details markdown="1">
<summary>last_by_name(name) -> dict | Any | None</summary>

**Description:** Return the **latest output value** by `name` from **Indices** (fast path). Useful for grabbing a single named value most recently produced by any tool that wrote it via `write_result()`.

**Inputs:**

* `name: str`

**Returns:**

* `dict | Any | None` – Store-dependent value or `None` if not found.

</details>

<details markdown="1">
<summary>last_outputs_by_topic(topic) -> dict[str, Any] | None</summary>

**Description:** Return the **latest outputs map** for a given `topic` (tool/flow/agent) from **Indices**.

**Inputs:**

* `topic: str` – The identifier you passed as `topic` to `write_result()`.

**Returns:**

* `dict[str, Any] | None` – Name→value map of last outputs, or `None` if not found.

</details>

## Behavioral Notes

* **Indices updates:** Only `write_result()` updates indices by default; this keeps ad-hoc `record_*` logs cheap.
* **Event ordering:** HotLog returns most recent last; consumers may reverse if needed.
* **RAG gating:** All `rag_*` methods raise `RuntimeError` if `self.rag` is not configured.
* **Unused parameters:** Current `record()` will log a warning on unserializable `data` if a logger is provided; otherwise it silently stringifies.
