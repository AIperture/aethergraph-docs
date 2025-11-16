# `RAGFacade` – Retrieval‑Augmented Generation API

> Manages corpora, document ingestion (text/files), chunking + embeddings, vector indexing, retrieval, and QA.
>
> **Backends:** defaults to a lightweight SQLite vector index. FAISS is supported locally if installed via pip. See **[LLM & Index Setup](../llm-setup/llm-setup.md)** for provider/model/index configuration.

## Quick Reference

| Method                                                                             | Purpose                                        | Returns                                             |
| ---------------------------------------------------------------------------------- | ---------------------------------------------- | --------------------------------------------------- |
| `set_llm_client(client)`                                                           | Swap the LLM used for QA                       | `None`                                              |
| `set_index_backend(index_backend)`                                                 | Swap the vector index backend                  | `None`                                              |
| `add_corpus(corpus_id, meta=None)`                                                 | Create/ensure a corpus                         | `None`                                              |
| `upsert_docs(corpus_id, docs)`                                                     | Ingest docs → chunk, embed, index              | `dict` {added,chunks,index}                         |
| `search(corpus_id, query, k=8, filters=None, mode="hybrid")`                       | Retrieve top chunks                            | `list[SearchHit]`                                   |
| `retrieve(corpus_id, query, k=6, rerank=True)`                                     | Alias to `search(..., mode="hybrid")`          | `list[SearchHit]`                                   |
| `answer(corpus_id, question, llm=None, style="concise", with_citations=True, k=6)` | QA over retrieved context                      | `dict` {answer,citations,usage,resolved_citations?} |
| `resolve_citations(corpus_id, citations)`                                          | Enrich citation refs with titles/URIs/snippets | `list[dict]`                                        |
| `list_corpora()`                                                                   | Enumerate corpora in `corpus_root`             | `list[dict]`                                        |
| `list_docs(corpus_id, limit=200, after=None)`                                      | Page through docs                              | `list[dict]`                                        |
| `delete_docs(corpus_id, doc_ids)`                                                  | Remove docs + chunks (+drop from index)        | `dict`                                              |
| `reembed(corpus_id, doc_ids=None, batch=64)`                                       | Recompute embeddings & re‑add to index         | `dict`                                              |
| `stats(corpus_id)`                                                                 | Simple counts + metadata                       | `dict`                                              |

---

## Data Types

**`SearchHit`**

* `chunk_id: str`
* `doc_id: str`
* `corpus_id: str`
* `score: float`
* `text: str`
* `meta: dict[str, Any]`

---

## Methods

<details markdown="1">
<summary>set_llm_client(client) -> None</summary>

**Description:** Set/replace the LLM client for QA.

**Inputs:**

* `client: LLMClientProtocol`

**Returns:**

* `None`

**Notes:**

* Requires `client.model` and `client.embed_model` to be set; asserts on missing values.

</details>

<details markdown="1">
<summary>set_index_backend(index_backend) -> None</summary>

**Description:** Swap the underlying vector index backend.

**Inputs:**

* `index_backend: Any` – Must implement `add(corpus_id, ids, vectors, metas)` and `search(corpus_id, qvec, k)`; optionally `remove`/`delete`.

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>add_corpus(corpus_id, meta=None) -> None</summary>

**Description:** Create/ensure a corpus directory with `corpus.json`.

**Inputs:**

* `corpus_id: str`
* `meta: dict[str, Any] | None`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>upsert_docs(corpus_id, docs) -> dict</summary>

**Description:** Ingest documents, chunk, embed, and add vectors to the index.

**Inputs:**

* `corpus_id: str`
* `docs: list[dict]` – Each doc is one of:

  * File doc: `{ "path": "/path/to/file.ext", "labels": {...} }`
  * Inline text: `{ "text": "...", "title": "Doc Title", "labels": {...} }`

**Returns:**

* `dict` – `{ "added": int, "chunks": int, "index": str }`

**Notes:**

* Files are persisted via the artifact store; PDFs/Markdown/Plain‑text are parsed to text.
* Requires an embedding client; raises if not configured.

</details>

<details markdown="1">
<summary>search(corpus_id, query, k=8, filters=None, mode="hybrid") -> list[SearchHit]</summary>

**Description:** Dense retrieval (embeds query, searches index) with optional hybrid lexical fusion.

**Inputs:**

* `corpus_id: str`
* `query: str`
* `k: int`
* `filters: dict | None` – Reserved; not applied in current implementation.
* `mode: str` – `"dense"` or `"hybrid"`.

**Returns:**

* `list[SearchHit]`

**Notes:**

* When `mode="dense"`, returns top‑`k` dense hits.
* When `mode="hybrid"`, fuses dense hits with lexical scoring for re‑ranking.

</details>

<details markdown="1">
<summary>retrieve(corpus_id, query, k=6, rerank=True) -> list[SearchHit]</summary>

**Description:** Convenience alias to `search(..., mode="hybrid")`.

**Inputs:**

* `corpus_id: str`
* `query: str`
* `k: int`
* `rerank: bool` – Currently ignored (hybrid fusion already sorts).

**Returns:**

* `list[SearchHit]`

</details>

<details markdown="1">
<summary>answer(corpus_id, question, llm=None, style="concise", with_citations=True, k=6) -> dict</summary>

**Description:** Compose a system+user prompt from retrieved chunks and answer with the LLM.

**Inputs:**

* `corpus_id: str`
* `question: str`
* `llm: LLMClientProtocol | None` – If `None`, uses the facade’s LLM.
* `style: str` – `"concise"` or `"detailed"`.
* `with_citations: bool`
* `k: int`

**Returns:**

* `dict` with keys:

  * `answer: str`
  * `citations: list[dict]` – `{chunk_id, doc_id, rank}`
  * `usage: dict` – model usage as provided by the LLM
  * `resolved_citations (optional): list[dict]` – enriched refs (see below)

**Notes:**

* See **LLM & Index Setup** for configuring provider/model.

</details>

<details markdown="1">
<summary>resolve_citations(corpus_id, citations) -> list[dict]</summary>

**Description:** Map `{chunk_id, doc_id, rank}` to `{rank, doc_id, title, uri, chunk_id, snippet}`.

**Inputs:**

* `corpus_id: str`
* `citations: list[dict]`

**Returns:**

* `list[dict]` sorted by `rank`.

</details>

<details markdown="1">
<summary>list_corpora() -> list[dict]</summary>

**Description:** Enumerate all corpora under `corpus_root`.

**Inputs:**

* —

**Returns:**

* `list[dict]` – `[{corpus_id, meta}, ...]`

</details>

<details markdown="1">
<summary>list_docs(corpus_id, limit=200, after=None) -> list[dict]</summary>

**Description:** Stream-like pagination over `docs.jsonl`.

**Inputs:**

* `corpus_id: str`
* `limit: int`
* `after: str | None` – Resume from a specific `doc_id`.

**Returns:**

* `list[dict]`

</details>

<details markdown="1">
<summary>delete_docs(corpus_id, doc_ids) -> dict</summary>

**Description:** Remove docs + their chunks; drop vectors from index if supported.

**Inputs:**

* `corpus_id: str`
* `doc_ids: list[str]`

**Returns:**

* `dict` – `{removed_docs: int, removed_chunks: int}`

</details>

<details markdown="1">
<summary>reembed(corpus_id, doc_ids=None, batch=64) -> dict</summary>

**Description:** Re‑embed selected (or all) chunks and re‑add them to the index.

**Inputs:**

* `corpus_id: str`
* `doc_ids: list[str] | None`
* `batch: int`

**Returns:**

* `dict` – `{reembedded: int, model: str | None}`

</details>

<details markdown="1">
<summary>stats(corpus_id) -> dict</summary>

**Description:** Return corpus stats and stored metadata.

**Inputs:**

* `corpus_id: str`

**Returns:**

* `dict` – `{corpus_id, docs, chunks, meta}`

</details>

---

## Examples

```python
# 1) Create/ensure a corpus
cid = "research-papers"
await rag.add_corpus(cid, meta={"owner": "team-ml"})

# 2) Ingest two docs (one file, one inline)
stats = await rag.upsert_docs(
    cid,
    docs=[
        {"path": "./notes/attention_is_all_you_need.pdf", "labels": {"kind": "paper"}},
        {"text": open("README.md", encoding="utf-8").read(), "title": "repo-readme"},
    ],
)

# 3) Search and answer
hits = await rag.search(cid, query="self-attention complexity", k=5)
ans = await rag.answer(cid, question="What is the time complexity of self-attention?", k=6)

# 4) Inspect/enrich citations
resolved = rag.resolve_citations(cid, ans["citations"])  # already included if with_citations=True

# 5) Maintenance
await rag.reembed(cid, doc_ids=[h.doc_id for h in hits])
await rag.delete_docs(cid, doc_ids=[hits[0].doc_id])
info = await rag.stats(cid)
```

**Notes & Setup:**

* **Embeddings/LLM:** configure providers/models via your LLM service. See **[LLM & Index Setup](../llm-setup/llm-setup.md)**.
* **Index:** defaults to SQLite‑based vectors; FAISS is supported if installed.
* **Artifacts:** binary sources are stored via the artifact store (CAS) before parsing.
