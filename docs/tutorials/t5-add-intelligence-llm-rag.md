# Tutorial 5: Add Intelligence — LLM & RAG

This tutorial adds language models and retrieval‑augmented generation (RAG) to your agents. You’ll:

1. set up an LLM profile
2. chat from a graph function
3. build a searchable RAG corpus from your files/memory
4. answer questions grounded by retrieved context (with optional citations)

> Works with OpenAI, Anthropic, Google (Gemini), OpenRouter, LM Studio, and Ollama via a unified **GenericLLMClient**.

---

## 0. Mental model

* **LLM**: a provider‑agnostic client you access via `context.llm(...)` for chat and embeddings.
* **RAG**: a corpus of documents (from files and/or Memory events) that are chunked, embedded, and retrieved to ground LLM answers.

```python
llm = context.llm(profile="default")   # chat & embed
rag = context.rag()                     # corpora, upsert, search, answer
```

---

## 1. Prerequisites

* API keys for the providers you want (e.g., OpenAI, Anthropic, Gemini, OpenRouter).
* If using local models: LM Studio or Ollama running locally and a base URL.

---

## 2. Configure LLMs (Profiles)

You can configure profiles in **environment variables** (recommended) or **at runtime**. See [docs](../llm-setup/llm-setup.md) for complete setup method.

### A) `.env` profiles (recommended)

Profiles are named by the section after `LLM__`. Example: a profile called **`MY_OPENAI`**:

```dotenv
AETHERGRAPH_LLM__MY_OPENAI__PROVIDER=openai
AETHERGRAPH_LLM__MY_OPENAI__MODEL=gpt-4o-mini
AETHERGRAPH_LLM__MY_OPENAI__TIMEOUT=60
AETHERGRAPH_LLM__MY_OPENAI__API_KEY=sk-...
AETHERGRAPH_LLM__MY_OPENAI__EMBED_MODEL=text-embedding-3-small  # needed for llm().embed() or RAG
```

Then in code:

```python
llm = context.llm(profile="my_openai")
text, usage = await llm.chat([...])
```

> The **default** profile comes from your container config. Use profiles when you want to switch providers/models per node or per run.

### B) Register at runtime (programmatic)

Useful for notebooks/demos or dynamically wiring services:

```python
from aethergraph.llm import register_llm_client, set_rag_llm_client

client = register_llm_client(
    profile="runtime_openai",
    provider="openai",
    model="gpt-4o-mini",
    api_key="sk-...",
)

# RAG can use a dedicated LLM (for embedding + answering). If not set, it uses the default profile.
set_rag_llm_client(client=client)
```

You can also pass parameters directly to `set_rag_llm_client(provider=..., model=..., embed_model=..., api_key=...)`.

### C) One‑off key injection

If you just need to override a key in memory for a demo:

```python
context.llm_set_key(provider="openai", api_key="sk-...")
```

> **Sidecar note:** If your run needs channels, resumable waits, or shared services, start the sidecar server before using runtime registration.

---

## 3. Chat & Embed from a Graph Function

### Chat (provider‑agnostic)

```python
@graph_fn(name="ask_llm")
async def ask_llm(question: str, *, context):
    llm = context.llm(profile="my_openai")  # or omit profile for default
    messages = [
        {"role": "system", "content": "You are concise and helpful."},
        {"role": "user",   "content": question},
    ]
    reply, usage = await llm.chat(messages)
    return {"answer": reply, "usage": usage}
```

### Embeddings

```python
vectors = await context.llm(profile="my_openai").embed([
    "First text chunk", "Second text chunk"
])
```

> RAG needs an **embed model** configured on the chosen profile.

### Optional reasoning knobs

Some models (e.g., GPT‑5) accept reasoning parameters such as `reasoning_effort="low|medium|high"` via `llm.chat(..., reasoning_effort=...)`.

---

## 4. Raw API escape hatch

For power users who need endpoints not yet covered by the high‑level client (such as low-level inputs, VLM models, custom models):

```python
openai = context.llm(profile="my_openai")
payload = {
    "model": "gpt-4o-mini",
    "input": [
        {"role": "system", "content": "You are concise."},
        {"role": "user",   "content": "Explain attention in one sentence."}
    ],
    "max_output_tokens": 128,
    "temperature": 0.3,
}
raw = await openai.raw(path="/responses", json=payload)
```

* `raw(path=..., json=...)` sends a verbatim request to the provider base URL.
* You are responsible for parsing the returned JSON shape.

> Use this when experimenting with new provider features before first‑class support lands in the client.

---

## 5. RAG: From Docs & Memory to Grounded Answers

**Flow:** `Files/Events → chunk + embed → index → retrieve top‑k → LLM answers with context`.

* **Corpora** live behind `context.rag()`.
* Ingest **files** (by path) and **inline text**, and/or **promote Memory events** into a corpus.

### A) Backend & storage

**Default vector index:** **SQLite** (local, zero‑dep) — great for laptops and small corpora.

**Switch to FAISS:** faster ANN search for larger corpora.

Set up RAG backend: 

* **Env:**

```dotenv
# RAG Settings
AETHERGRAPH_RAG__BACKEND=faiss        # or sqlite
AETHERGRAPH_RAG__DIM=1536             # embedding dimension (e.g., OpenAI text-embedding-3-small)
```

* **Runtime:**

```python
from aethergraph.services.rag import set_rag_index_backend

set_rag_index_backend(backend="faiss", dim=1536)
# If FAISS is not installed, it logs a warning and falls back to SQLite automatically.
```

* **On‑disk layout:** each corpus stores `corpus.json`, `docs.jsonl`, `chunks.jsonl`; source files are saved as **Artifacts** for provenance.

### B) Build / update a corpus from files & text

```python
await context.rag().upsert_docs(
    corpus_id="my_docs",
    docs=[
        {"path": "data/report.pdf", "labels": {"type": "report"}},
        {"text": "Experiment hit 91.2% accuracy on CIFAR-10.", "title": "exp-log"},
    ],
)
```

* Use file docs when you already have a local file: `{"path": "/abs/or/relative.ext", "labels": {...}}`. Supported “smart-parsed” types are `.pdf`, `.md/markdown`, and `.txt` (others are treated as plain text). The original file is saved as an **Artifact** for provenance; if your PDF is a scan, run OCR first (we only extract selectable text). 

* Use inline docs when you have content in memory: `{"text": "...", "title": "nice-short-title", "labels": {...}}`. Keep titles short and meaningful; add 1–3 optional labels you’ll actually filter by (e.g., `{"source":"lab", "week":2}`).

Behind the scenes: documents are stored as Artifacts, parsed, chunked, embedded, and added to the vector index.

### C) Promote Memory events into RAG

```python
corpus = await context.memory().rag_bind()
await context.memory().rag_promote_events(
    corpus_id=corpus,
    where={"kinds": ["tool_result"], "limit": 200},
)
```

You can promote any custom `kind` you recorded for later vector-based search and answer in a same `corpus_id`.

### D) Search, retrieve, answer (with citations)

```python
hits = await context.rag().search("my_docs", "key findings", k=8, mode="hybrid")
ans  = await context.rag().answer(
    corpus_id="my_docs",
    question="Summarize the main findings and list key metrics.",
    style="concise",
    with_citations=True,
    k=6,
)
# ans → { "answer": str, "citations": [...], "resolved_citations": [...], "usage": {...} }
```

Use `resolved_citations` to map snippets back to Artifact URIs for auditability.

### E) Choosing the LLM for RAG

RAG uses a dedicated **RAG LLM client** that must have **both** `model` **and** `embed_model` set.

**Runtime:**

  ```python
  from aethergraph.llm import set_rag_llm_client
  set_rag_llm_client(provider="openai", model="gpt-4o-mini", embed_model="text-embedding-3-small", api_key="sk-…")
  ```

If you don’t set one, it falls back to the default LLM profile (ensure that profile also has an `embed_model`).

### F) Corpus management (ops)

For maintenance and ops you can:

* **List corpora / docs** to inspect what’s indexed.
* **Delete docs** to remove vectors and records.
* **Re‑embed** to refresh vectors after changing embed model or chunking.
* **Stats** to view counts of docs/chunks and corpus metadata.

These live on the same facade: `rag.list_corpora()`, `rag.list_docs(...)`, `rag.delete_docs(...)`, `rag.reembed(...)`, `rag.stats(...)`.

---

## 6. Practical recipes

* **Switch providers** by changing `profile=` in `context.llm(...)` without touching your code elsewhere.
* **Save docs as Artifacts** (e.g., `save_text`, `save(path=...)`) and ingest by `{"path": local_path}` so RAG can cite their URIs.
* **Log LLM outputs** with `context.memory().record(...)` or `write_result(...)` to enable recency views, distillation, and RAG promotion later.

---

## 7. Troubleshooting

* **Auth/Endpoints**: Check keys; for Azure, confirm deployment + endpoint. For LM Studio, the base URL must include `/v1`.
* **No citations or odd snippets**: Verify parsing (PDFs can be tricky). Consider storing originals as Artifacts alongside parsed text.
* **Answers miss context**: Increase `k`, adjust chunk sizes, or broaden your `where` filter when promoting events.
* **Latency/Cost**: Keep chunks compact, and filter ingestion to what you’ll actually ask about.

---

## Summary

* Configure **LLM profiles** via `.env` or runtime registration, then use `llm.chat()` / `llm.embed()`.
* Build RAG corpora from **files** and **Memory events**, then call `rag.answer(..., with_citations=True)` for grounded responses.
* Use **Artifacts + Memory** for provenance so you can trace *what the model answered* and *why*.

**See also:** `context.llm()` · `context.rag()` · `context.memory().rag_*` · `register_llm_client` · `set_rag_llm_client` · `llm.raw`
