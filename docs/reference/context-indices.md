# `context.indices()` – Global Index API Reference

`context.indices()` returns a **scope-aware** `ScopedIndices` wrapper around the global `SearchBackend`.

It is the primary API for **writing** and **retrieving** text records (e.g., memory snippets, run events, artifacts)
while automatically attaching and enforcing **scope metadata**.

## What “scoped” means

Each `ScopedIndices` instance carries:

- `scope`: a `Scope` object describing the active org/user/app/session/run/node context.
- `scope_id` (optional): an extra logical partition key (commonly a `memory_scope_id` for memory-tied corpora).

### Writes: automatic metadata

On `upsert()`, `ScopedIndices` merges your provided `metadata` with base scope labels
(e.g. user/org/app/session/run/node identifiers) and drops keys whose values are `None`.

### Reads: automatic filters

On `search()`, `ScopedIndices` automatically applies base scope filters (and optional `scope_id`),
then merges in any user-provided `filters` (dropping `None` values).

## Quickstart

### Upsert a document

```python
indices = context.indices()

await indices.upsert(
    corpus="artifact",
    item_id="artifact:123",
    text="Design review notes for v2 surrogate workflow...",
    metadata={"kind": "note", "tag": "surrogate"},
)
```

### Search within a corpus

```python
indices = context.indices()

items = await indices.search(
    corpus="artifact",
    query="surrogate workflow",
    top_k=10,
    filters={"tag": "surrogate"},
    time_window="7d",  # optional: interpreted as [now - 7d, now]
)
```

### Convenience helpers

```python
indices = context.indices()

events = await indices.search_events("error", top_k=20, time_window="24h")
artifacts = await indices.search_artifacts("invoice template", top_k=10)
```

> Note: `time_window` is ignored if `created_at_min` is provided. You can also pass
> `created_at_min` / `created_at_max` as UNIX timestamps for precise control.

---

## 1. Upsert any text

??? quote "upsert(*, corpus, item_id, text, metadata=None)"
    ::: aethergraph.services.indices.scoped_indices.ScopedIndices.upsert
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

## 2. Search API

??? quote "search(*, corpus, query, top_k=10, filters=None, time_window=None, created_at_min=None, created_at_max=None)"
    ::: aethergraph.services.indices.scoped_indices.ScopedIndices.search
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "search_events(query, *, top_k=20, filters=None, time_window=None, created_at_min=None, created_at_max=None)"
    ::: aethergraph.services.indices.scoped_indices.ScopedIndices.search_events
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "search_artifacts(query, *, top_k=20, filters=None, time_window=None, created_at_min=None, created_at_max=None)"
    ::: aethergraph.services.indices.scoped_indices.ScopedIndices.search_artifacts
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
