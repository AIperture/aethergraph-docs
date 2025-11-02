# AetherGraph — `context.rag()` Reference

This page documents the **RAGFacade** returned by `context.rag()` in a concise format: signature, brief description, parameters, returns, and practical examples.

The facade covers: **corpus management**, **document ingestion (upsert)**, **retrieval (search/retrieve)**, and **question answering** with optional citation resolution.

---

## Overview
`context.rag()` provides high‑level helpers backed by:

- an **Artifact Store** (for persisted doc assets),
- an **Embedding client** (e.g., `context.llm().embed()`),
- a **Vector index backend** (add/search),
- a **TextSplitter** (chunking before embedding), and
- an optional **LLM client** for QA.

---

## rag.add_corpus
```
add_corpus(corpus_id: str, meta: dict | None = None) -> None
```
Create a new corpus directory with metadata if it does not exist.

**Parameters**

- **corpus_id** (*str*) – Unique identifier for the corpus.

- **meta** (*dict, optional*) – Arbitrary metadata stored alongside the corpus.

**Returns**  
`None`

---

## rag.upsert_docs
```
upsert_docs(corpus_id: str, docs: list[dict]) -> dict
```
Ingest and index a list of documents (file‑based or inline text). Handles artifact persistence, chunking, embedding, and index add.

**Parameters**

- **corpus_id** (*str*) – Target corpus identifier.

- **docs** (*list[dict]*) – Each doc is either:

  - **File doc**: `{ "path": "/path/to/file.pdf", "labels": {...}, "title": "Optional" }`

  - **Inline text doc**: `{ "text": "...", "title": "Optional", "labels": {...} }`

**Returns**  
*dict* – Summary like `{ "added": int, "chunks": int, "index": "BackendName" }`.

**Notes**
- PDFs and Markdown are parsed with built‑in extractors; other files default to text.

- Each doc and chunk is assigned a stable SHA‑derived ID and recorded in `docs.jsonl` / `chunks.jsonl` under the corpus folder.

---

## rag.search
```
search(corpus_id: str, query: str, k: int = 8, filters: dict | None = None, mode: str = "hybrid") -> list[SearchHit]
```
Hybrid retrieval: dense vector search with optional lexical fusion, returning the top‑k chunks.

**Parameters**

- **corpus_id** (*str*) – Target corpus.

- **query** (*str*) – Natural language query.

- **k** (*int*) – Number of results (default 8).

- **filters** (*dict, optional*) – Reserved for metadata filtering (adapter‑specific).

- **mode** (*{"dense","hybrid"}*) – Retrieval mode (default `"hybrid"`).

**Returns**  
*list[SearchHit]* – Ranked hits with `chunk_id`, `doc_id`, `corpus_id`, `score`, `text`, `meta`.

---

## rag.retrieve
```
retrieve(corpus_id: str, query: str, k: int = 6, rerank: bool = True) -> list[SearchHit]
```
Convenience wrapper over `search(..., mode="hybrid")` for top‑k retrieval.

**Parameters**

- **corpus_id** (*str*) – Target corpus.

- **query** (*str*) – Natural language query.

- **k** (*int*) – Number of results (default 6).

- **rerank** (*bool*) – Currently ignored (hybrid already fuses scores).

**Returns**  
*list[SearchHit]* – Ranked hits.

---

## rag.answer
```
answer(corpus_id: str, question: str, *, llm: GenericLLMClient | None = None, style: str = "concise", with_citations: bool = True, k: int = 6) -> dict
```
Answer a question using retrieved context and an LLM.

**Parameters**

- **corpus_id** (*str*) – Target corpus.

- **question** (*str*) – End‑user question.

- **llm** (*GenericLLMClient, optional*) – LLM to use; defaults to the facade’s configured client.

- **style** (*{"concise","detailed"}*) – Answer verbosity/style.

- **with_citations** (*bool*) – Whether to include resolved citations.

- **k** (*int*) – Retrieval depth (default 6).

**Returns**  
*dict* – `{ "answer": str, "citations": [...], "usage": {...}, "resolved_citations": [...]? }`.

**Behavior**
- Builds a context block from top‑k chunks (numbered `[1]`, `[2]`, ...).

- Prompts the LLM to answer **only** from the provided context and cite chunk numbers.

---

## rag.resolve_citations
```
resolve_citations(corpus_id: str, citations: list[dict]) -> list[dict]
```
Resolve citation metadata for display/download.

**Parameters**

- **corpus_id** (*str*) – Target corpus.

- **citations** (*list[dict]*) – Items like `{ "chunk_id", "doc_id", "rank" }`.

**Returns**  
*list[dict]* – Sorted by `rank`, each `{ rank, doc_id, title, uri, chunk_id, snippet }`.

---

## Practical examples

**1) Create a corpus and ingest docs**
```python
from aethergraph import graph_fn

@graph_fn(name="rag_ingest")
async def rag_ingest(*, context):
    await context.rag().add_corpus("notes")
    stats = await context.rag().upsert_docs(
        corpus_id="notes",
        docs=[
            {"text": "Optics basics: Snell's law relates angles of incidence and refraction." , "title": "optics"},
            {"path": "/data/papers/holography.md", "labels": {"topic": "holography"}},
        ],
    )
    await context.channel().send_text(f"RAG upsert: {stats}")
```

**2) Search and preview hits**
```python
@graph_fn(name="rag_search_preview")
async def rag_search_preview(*, context, q: str):
    hits = await context.rag().search(corpus_id="notes", query=q, k=5)
    for i, h in enumerate(hits, 1):
        await context.channel().send_text(f"[{i}] score={h.score:.3f}  doc={h.doc_id}\n{h.text[:200]}")
```

**3) Answer with citations**
```python
@graph_fn(name="rag_answer_with_citations")
async def rag_answer_with_citations(*, context, q: str):
    out = await context.rag().answer(corpus_id="notes", question=q, style="concise", k=6)
    ans = out.get("answer", "")
    cites = out.get("resolved_citations", [])
    await context.channel().send_text(ans)
    for c in cites[:3]:
        await context.channel().send_text(f"[#{c['rank']}] {c['title']} — {c['snippet']}")
```

---

## Notes & behaviors
- **Chunking & Embedding**: Documents are split via `TextSplitter` then embedded in batch; the index stores `(chunk_id, vector, meta)`.

- **Artifacts**: File docs and inline text are persisted to the Artifact Store; returned URIs appear in doc metadata and resolved citations.

- **IDs**: `doc_id` and `chunk_id` are stable SHA‑derived IDs; re‑ingesting the same content usually yields the same IDs (subject to meta changes).

- **Filters**: `filters` is reserved for future adapter support (label‑based narrowing).

- **LLM & Usage**: `answer()` returns provider usage where available; some providers may omit it.

