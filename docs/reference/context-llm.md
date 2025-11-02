# AetherGraph — `context.llm()` Reference

This page documents the **LLM client** retrieved via `context.llm(profile="default")`, in a concise format. The client implements two core calls:

- `chat(messages, **kwargs) -> (text: str, usage: dict)`
- `embed(texts, **kwargs) -> list[list[float]]`

Profiles are managed by an `LLMService` that holds one or more configured clients ("default", "azure", "local", etc.).

---

## Quick start
```python
# 1) Use the default LLM profile
llm = context.llm()                # == context.llm("default")
text, usage = await llm.chat([
    {"role":"system", "content":"You are a helpful assistant."},
    {"role":"user",   "content":"Summarize AetherGraph in one sentence."},
])

# 2) Switch/set a key at runtime (in‑memory only)
context.llm_set_key(provider="openai", api_key="sk-...", profile="default")

# 3) Use a named profile (must exist in LLMService)
llm = context.llm("azure")
```

---

## Supported providers (via GenericLLMClient)
`{"openai","azure","anthropic","google","openrouter","lmstudio","ollama"}`

> Credentials and endpoints are read from environment by default, but can be provided at construction time. Runtime key overrides are allowed via `context.llm_set_key(...)`.

Common env vars:

- `OPENAI_API_KEY`, `OPENAI_BASE_URL`
- `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `OPENROUTER_API_KEY`
- `LMSTUDIO_BASE_URL` (default `http://localhost:1234/v1`)
- `OLLAMA_BASE_URL`   (default `http://localhost:11434/v1`)

---

## llm.chat
```
chat(messages: list[dict], **kw) -> tuple[str, dict]
```
Send a chat completion request and return `(text, usage)`.

**Parameters**

- **messages** (*list[dict]*) – OpenAI‑style conversation turns, e.g. `{"role":"system"|"user"|"assistant", "content": str}`.

- **kw** – Common knobs (provider‑dependent):  
  
  - **model** (*str, optional*) – Model name (defaults to client’s configured model).  
  
  - **temperature** (*float, optional*) – Sampling temperature (default `0.5`).  
  
  - **top_p** (*float, optional*) – Nucleus sampling (default `1.0`).  
  
  - **max_tokens** (*int, optional*) – Max tokens (Anthropic/Azure/Google paths).  

**Returns**  
*tuple[str, dict]* – Generated `text` and a `usage` dict (token counts where supported).

**Example**
```python
sys = {"role":"system","content":"Be concise."}
usr = {"role":"user","content":"What is AetherGraph?"}
text, usage = await context.llm().chat([sys, usr], temperature=0.2)
await context.channel().send_text(text)
```

---

## llm.embed
```
embed(texts: list[str], **kw) -> list[list[float]]
```
Return embeddings for a list of strings.

**Parameters**

- **texts** (*list[str]*) – Text strings to embed.

- **kw** – Common knobs (provider‑dependent):  
  
  - **model** (*str, optional*) – Embedding model name (default `text-embedding-3-small` for OpenAI‑like providers).

**Returns**  
*list[list[float]]* – Embedding vectors.

**Example**
```python
vecs = await context.llm().embed(["lens design", "holography basics"])  # [[...], [...]]
```

---

## Profiles and keys

### `context.llm(profile: str = "default") -> LLMClient`
Retrieve the configured LLM client for a named profile. Raises if `LLMService` is not bound or profile missing.

### `context.llm_set_key(provider: str, api_key: str, profile: str = "default") -> None`
Override an API key **in memory** for the given profile (good for demos/notebooks). Does not persist.

**Example**
```python
# Switch the default profile to use a local LM Studio server at runtime
context.llm_set_key(provider="lmstudio", api_key="sk-ignore", profile="default")
text, _ = await context.llm().chat([
    {"role":"user","content":"Say hi from LM Studio"}
])
```

> For long‑lived storage, use your project’s Secrets provider and `LLMService.persist_key(secret_name, api_key)` if available.

---

## Provider‑specific notes
- **OpenAI / OpenRouter / LM Studio / Ollama** – uses OpenAI‑style `/chat/completions` and `/embeddings` routes. `usage` is included where supported.

- **Azure OpenAI** – requires `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT`; uses Azure routes.

- **Anthropic (Claude)** – converts OpenAI‑style messages to Anthropic’s message format; returns concatenated text blocks.

- **Google (Gemini)** – uses `:generateContent` and `:embedContent`; `usage` shape differs and may be empty.

- **Embeddings** – not supported for Anthropic in this client.

---

## Error handling & retries
The client wraps calls with exponential backoff (`_Retry`) for transient HTTP errors (`ReadTimeout`, `ConnectError`, `HTTPStatusError`). You may still want to catch and surface provider‑specific errors around quota/keys.

**Example**
```python
try:
    text, usage = await context.llm().chat([{ "role":"user", "content":"ping" }])
except Exception as e:
    await context.channel().send_text(f"LLM error: {e}")
```

---

## Patterns with Context

**Router‑then‑Act**
```python
from aethergraph import graph_fn

@graph_fn(name="router_then_act")
async def router_then_act(*, context):
    sys = {"role":"system","content":"Route to 'summarize' or 'plot'"}
    usr = {"role":"user","content":"Summarize this research log."}
    decision, _ = await context.llm().chat([sys, usr], temperature=0.0)
    if "summarize" in decision.lower():
        # Call downstream tool and write a result
        await context.memory().write_result(
            topic="router",
            outputs=[{"name":"route","kind":"text","value":"summarize"}],
        )
        await context.channel().send_text("Routing → summarize")
```

**RAG: retrieve → answer**
```python
@graph_fn(name="rag_answer")
async def rag_answer(*, context, q: str):
    hits = await context.memory().rag_search(corpus_id="notes", query=q, k=6)
    prompt = [{"role":"system","content":"Answer using the provided notes."},
              {"role":"user","content":"\n\n".join(h.get("text","") for h in hits) + "\n\nQ: " + q}]
    text, usage = await context.llm().chat(prompt, temperature=0.2, model="gpt-4o-mini")
    return {"answer": text, "tokens": usage.get("total_tokens")}
```

---

<!-- ## Lifecycle
If you manage clients directly, close them on shutdown:
```python
await context.runtime().llm.aclose()
``` -->

---

## Summary
- Use `context.llm()` to get a ready‑to‑use client for the current profile.
- `chat()` returns `(text, usage)`; `embed()` returns vectors.
- Switch keys ad‑hoc with `context.llm_set_key(...)`; persist via your Secrets provider when available.
