# Tutorial 5: Add Intelligence — LLM & RAG

This tutorial adds language models and retrieval‑augmented generation (RAG) to your agents. You’ll:

1. set up an LLM profile
2. chat from a graph function
3. build a searchable RAG corpus from your files/memory
4. answer questions grounded by retrieved context (with optional citations)

> Works with OpenAI, Azure OpenAI, Anthropic, Google (Gemini), OpenRouter, LM Studio, and Ollama via a unified `GenericLLMClient`.

---

## 1) Quick Setup: LLM Profiles

LLMs are managed by `LLMService`. You can provide keys via **environment variables** (recommended) or set a key **at runtime** for demos.

### A) Environment variables (recommended)

```bash
# Choose a provider and set its key
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
# Optionally select a default chat/embedding model
export LLM_MODEL=gpt-4o-mini
export EMBED_MODEL=text-embedding-3-small
```

### B) Runtime key injection (demo/notebook)

```python
@graph_fn(name="hello_llm")
async def hello_llm(name: str, *, context):
    # Set/override an API key for the active profile (in-memory only)
    context.llm_set_key(provider="openai", api_key="sk-YOURKEY")

    llm = context.llm()            # ← default profile
    text, usage = await llm.chat([
        {"role": "system", "content": "Be concise."},
        {"role": "user",   "content": f"Greet {name} in one line."},
    ])
    await context.channel().send_text(text)
    return {"reply": text}
```

> Tip: Use **profiles** if you need multiple providers/models. Call `context.llm("myprofile")` to get a named profile you configured in the container.

---

## 2) Chatting in Agents (with Memory logging)

Ask the user a question over your configured channel, call the LLM, and record the result to Memory for later analysis.

```python
@graph_fn(name="interactive_chat")
async def interactive_chat(*, context):
    ch = context.channel()
    question = await ch.ask_text("What do you want to know?")

    answer, usage = await context.llm().chat([
        {"role": "system", "content": "Answer briefly and clearly."},
        {"role": "user",   "content": question},
    ])

    await ch.send_text(f"🧠 {answer}")

    # Log an inspectable event for later recall/distillation
    await context.memory().record("llm.answer", {"q": question, "a": answer})
```

**Why log?** You can later `recent()`/`distill_*()` the conversation, bind it to RAG, or correlate LLM answers with artifacts produced in the same run.

---

## 3 RAG in AetherGraph — How It Works

> **Implementation note (OSS):** AetherGraph’s open‑source RAG uses a **local filesystem corpus** plus a **FAISS** vector index for embeddings/retrieval by default. If you prefer a hosted/vector DB (e.g., PgVector, Qdrant, Pinecone), plug it in via **Extend Services**.

RAG turns your files and run history into a **searchable corpus**. At answer time, the LLM sees only the most relevant chunks.

```
Your files / logs ──► Chunk & Embed ──► Vector Index ──► Retrieve top‑k ──► LLM answers from context
        ▲                     │                                 │
        └──── stored as Artifacts & Memory ─────────────────────┘
```

* **Artifacts**: PDFs, markdown, JSON, text blobs (saved under `workspace/artifacts/`).
* **RAGFacade**: handles corpora, ingestion, embeddings, search, and QA.
* **LLM**: generates the final answer using retrieved chunks as context.

---

## 4) Build a Corpus from Files (and Inline Text)

```python
@graph_fn(name="make_corpus", outputs=["corpus_id"])
async def make_corpus(*, context):
    rag = context.rag()
    corpus_id = "my_docs"  # any stable string you choose

    stats = await rag.upsert_docs(corpus_id, [
        {"path": "data/report.pdf", "labels": {"type": "report"}},
        {"text": "Experiment reached 91.2% accuracy on CIFAR-10.", "title": "exp-log"},
    ])

    await context.channel().send_text(f"Indexed {stats['chunks']} chunks in '{corpus_id}'.")
    return {"corpus_id": corpus_id}
```

**What happens under the hood**

* Each doc is **saved as an artifact** (CAS URI under `workspace/artifacts/`) and parsed to text.
* Text is **chunked and embedded**, then added to a vector index.

---

## 5) Use RAG with Memory


> **About `kinds`:** `memory.record()` lets you set **any** event `kind` and those events are eligible for RAG promotion. `memory.write_result(...)` is just a convenience that emits events with kind **`tool_result`** and updates fast indices. In examples we filter `where={"kinds":["tool_result"]}`, but you can target your own kinds (e.g., `"eval"`, `"pipeline"`).

You can also build a corpus directly from your **Memory events** (e.g., tool results recorded by `write_result`).

```python
@graph_fn(name="promote_memory_to_rag")
async def promote_memory_to_rag(*, context):
    corpus = await context.memory().rag_bind(scope="project")  # creates/binds a stable project corpus

    # Select informative events (e.g., most runs record outputs as kind="tool_result")
    await context.memory().rag_promote_events(
        corpus_id=corpus,
        where={"kinds": ["tool_result"], "limit": 200}
    )

    await context.channel().send_text("Promoted recent tool results into RAG.")
```

**What does `kinds=["tool_result"]` mean?**

* Every call to `memory.write_result(...)` becomes a structured **tool_result** event internally. Promoting these events turns your run outputs (numbers, URIs, short messages) into searchable docs.

---

## 6) Ask Questions with Citations

```python
@graph_fn(name="ask_rag")
async def ask_rag(question: str, *, context):
    rag = context.rag()
    corpus_id = "my_docs"

    ans = await rag.answer(corpus_id, question, style="concise", with_citations=True, k=6)
    # ans = { "answer": ..., "citations": [...], "resolved_citations": [...], "usage": {...} }

    await context.channel().send_text(ans.get("answer", "(no answer)"))
    # Optionally log the answer to Memory for future recall/analytics
    await context.memory().record("rag.answer", {"q": question, "a": ans.get("answer", "")})
    return {"answer": ans}
```

**Citations** include snippet + artifact URI for traceability. You can open those URIs locally via your Artifact facade when needed.

---

## 7) End‑to‑End: Files → Corpus → QA (with Memory log)

```python
@graph_fn(name="doc_qa_pipeline")
async def doc_qa_pipeline(question: str, *, context):
    rag = context.rag()
    corpus = "lab-notes"

    # 1) Ingest docs (idempotent upserts)
    await rag.upsert_docs(corpus, [
        {"path": "notes/week1.md", "labels": {"week": 1}},
        {"path": "notes/week2.md", "labels": {"week": 2}},
    ])

    # 2) Ask with context
    ans = await rag.answer(corpus, question, style="concise", with_citations=True)

    # 3) Record a typed result so you can recall latest answers fast
    await context.memory().write_result(
        topic="doc_qa",
        outputs=[
            {"name": "question", "kind": "text", "value": question},
            {"name": "answer",   "kind": "text", "value": ans.get("answer", "")},
        ],
        tags=["qa", "rag"],
    )

    return {"answer": ans.get("answer", ""), "citations": ans.get("resolved_citations", [])}
```

---

## 8) Troubleshooting & Tips

* **Keys and endpoints**: If you see auth errors, confirm the provider key and (for Azure) the deployment + endpoint vars.
* **Local models (LM Studio / Ollama)**: set `LMSTUDIO_BASE_URL` / `OLLAMA_BASE_URL` then choose an installed model.
* **Chunking too coarse/fine**: adjust chunk sizes in your `TextSplitter` if answers are missing context or too verbose.
* **Citations look odd**: verify that documents were parsed properly (PDFs especially). Consider saving the original doc as an Artifact alongside parsed text for auditability.

---

## 9) What to Use When

| Task                                   | Use                                                   |
| -------------------------------------- | ----------------------------------------------------- |
| Quick one-off LLM reply                | `context.llm().chat(...)`                             |
| Log a run’s LLM outputs                | `context.memory().record(...)` or `write_result(...)` |
| Build a knowledge base from files      | `context.rag().upsert_docs(...)`                      |
| Turn recent run history into knowledge | `context.memory().rag_promote_events(...)`            |
| Answer with sources                    | `context.rag().answer(..., with_citations=True)`      |

---

## 10) Optional: Pair with Artifacts & Memory

* Save source docs as **Artifacts** to ensure reproducibility and human‑readable URIs under `workspace/artifacts/`.
* Record important answers via **Memory** so you can later `last_by_name(...)`, `recent(...)`, or `distill_rolling_chat(...)` for summaries.

```python
# Example: record a compact summary after a Q/A session
summary = await context.memory().distill_rolling_chat(max_turns=20)
# (optionally) snapshot a RAG corpus as an Artifact bundle
snap = await context.memory().rag_snapshot(corpus_id="lab-notes", title="Weekly snapshot")
```

---

#

### Example: Load an artifact by URI and query it

Suppose you previously saved a report and only have its **URI**. Resolve it to a local path, parse the text, and upsert to a RAG corpus for querying:

```python
@graph_fn(name="artifact_to_rag_then_query", outputs=["answer"]) 
async def artifact_to_rag_then_query(report_uri: str, question: str, *, context):
    # 1) Resolve URI → local path (works for file:// and local CAS URIs)
    path = context.artifacts().to_local_path(report_uri)

    # 2) Make a project corpus (idempotent)
    corpus = await context.memory().rag_bind(scope="project")

    # 3) Ingest the artifact’s content into RAG
    docs = [{"path": path, "labels": {"kind": "report"}}]
    await context.memory().rag_upsert(corpus_id=corpus, docs=docs)

    # 4) Ask a question against the corpus
    ans = await context.memory().rag_answer(corpus_id=corpus, question=question)
    return {"answer": ans.get("answer", "")}
```

> You can also ingest **inline** text that you’ve just generated by saving it as an artifact (e.g., `save_text`) and then upserting with `{"text": ..., "title": ...}`.

## Summary

* Configure an LLM profile via env or runtime key, then call `llm.chat()`.
* Build corpora from files and/or Memory events, then answer questions grounded by retrieval.
* Use Memory + Artifacts to keep provenance: you can trace what the model answered and **why**.
