# LLMs & RAG – Central Setup Guide

This page is the one‑stop reference for configuring **LLM profiles** and **RAG** in AetherGraph. It covers environment‑based setup, runtime registration, and per‑call overrides.

---

## 1. Quick Start via `.env`

### LLM Settings (OpenAI example)

```env
# Enable LLM service
AETHERGRAPH_LLM__ENABLED=true

# Default profile "default"
AETHERGRAPH_LLM__DEFAULT__PROVIDER=openai
AETHERGRAPH_LLM__DEFAULT__MODEL=gpt-4o-mini
AETHERGRAPH_LLM__DEFAULT__TIMEOUT=60
AETHERGRAPH_LLM__DEFAULT__API_KEY=sk-...                # your OpenAI key
AETHERGRAPH_LLM__DEFAULT__EMBED_MODEL=text-embedding-3-small
```

This makes `context.llm()` (or `context.llm(profile="default")`) available everywhere.

### Extra profiles (example: Google Gemini)

```env
# Profile name: GEMINI
AETHERGRAPH_LLM__PROFILES__GEMINI__PROVIDER=google
AETHERGRAPH_LLM__PROFILES__GEMINI__MODEL=gemini-2.5-flash-lite
AETHERGRAPH_LLM__PROFILES__GEMINI__TIMEOUT=60
AETHERGRAPH_LLM__PROFILES__GEMINI__API_KEY=AIzaSy...     # your Google key
AETHERGRAPH_LLM__PROFILES__GEMINI__EMBED_MODEL=text-embedding-004
```
This makes `context.llm(profile="gemeni")` available everywhere.

You can add as many profiles as you like (Anthropic, LM Studio, Azure OpenAI, etc.).

---

## 2. Runtime Registration (no restart needed)

Use these helpers from `aethergraph.runtime` when you want to configure LLMs at runtime (e.g., notebooks, scripts):

```python
from aethergraph.server import start as start_server
from aethergraph.runtime import register_llm_client, set_rag_llm_client

# 1) Start the sidecar so services are wired
url = start_server(port=0)

# 2) Register multiple LLM profiles
openai_client = register_llm_client(
    profile="my_openai",
    provider="openai",
    model="gpt-4o-mini",
    api_key="sk-...",
)

register_llm_client(
    profile="my_lmstudio",
    provider="lmstudio",
    model="qwen/qwen2.5-vl-7b",
    base_url="http://localhost:1234/v1",   # LM Studio uses /v1
)

register_llm_client(
    profile="my_anthropic",
    provider="anthropic",
    model="claude-3",
    api_key="sk-ant-...",
)

register_llm_client(
    profile="my_gemini",
    provider="google",
    model="gemini-2.5-flash-lite",
    api_key="AIzaSy...",
)

# 3) RAG LLM client (defaults to "default" profile if not set)
set_rag_llm_client(client=openai_client)
# or create by parameters
set_rag_llm_client(
    provider="openai",
    model="gpt-4o-mini",
    embed_model="text-embedding-3-small",
    api_key="sk-...",
)
```

---

## 3. Inline Overrides in Code

When you need to switch providers/models on the fly, use the inline API on `NodeContext`:

```python
# Get existing profile (no overrides)
llm_client = context.llm(profile="default")

# Or create/update a profile inline
llm_client = context.llm(
    profile="temp_profile",
    provider="openai",
    model="gpt-4o-mini",
    api_key="sk-...",
    timeout=60,
)

# Quick credential swap
context.llm_set_key(provider="openai", model="gpt-4o-mini", api_key="sk-...", profile="default")
```

---

## 4. RAG Setup

### Defaults

* The RAG service uses the **default LLM profile** unless you explicitly set a RAG client.
* Ensure the profile used by RAG has a valid **`embed_model`**.

### `.env` RAG Settings

```env
# RAG Settings
AETHERGRAPH_RAG__BACKEND=faiss   # e.g., faiss or sqlite (faiss may need extra deps)
AETHERGRAPH_RAG__DIM=1536        # match your embedding dimensionality
```

> If FAISS isn’t available, the system will auto‑fallback to SQLite vector index.

### Runtime RAG Configuration

Use these helpers from `aethergraph.runtime`:

```python
from aethergraph.runtime import set_rag_llm_client, set_rag_index_backend

# Choose the LLM for RAG (client or by params)
rag_client = set_rag_llm_client(client=openai_client)
# or
rag_client = set_rag_llm_client(
    provider="openai",
    model="gpt-4o-mini",
    embed_model="text-embedding-3-small",
    api_key="sk-...",
)

# Configure the index backend (backend="sqlite" | "faiss")
set_rag_index_backend(backend="faiss", index_path=None, dim=1536)
```

---

## 5. Minimal Usage Example

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="llm.multiple.profile.demo")
async def llm_multiple_profile_demo(profile: str, *, context: NodeContext):
    llm_client = context.llm(profile=profile)
    messages = [
        {"role": "system", "content": "You are a concise and helpful assistant."},
        {"role": "user", "content": "In one sentence, what is an attention layer in neural networks?"},
    ]
    text, usage = await llm_client.chat(messages)

    # GPT‑5 models support optional reasoning controls, e.g.:
    # text, usage = await llm_client.chat(messages, reasoning_effort="low")

    return {"profile": profile, "answer": text, "usage": usage}
```

---

## 6. Tips & Notes

* **Security:** Keep API keys in `.env` or secret managers; avoid hard‑coding in scripts.
* **Profiles:** Name them by purpose (e.g., `summarize`, `vision`, `rag`) to keep code expressive.
* **Embedding dim:** Ensure `AETHERGRAPH_RAG__DIM` matches your selected `embed_model`.
* **LM Studio / self‑hosted:** set `base_url` (and deployment name for Azure) as required by your provider.
