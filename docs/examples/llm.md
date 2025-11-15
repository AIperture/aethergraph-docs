# `context.llm()` Mini Tutorial

This is a quick guide to the `NodeContext.llm()` helper in Aethergraph: how it’s wired, how to use profiles, how to configure providers in `.env`, and how embeddings + RAG fit in.

---

## 1. What `context.llm()` is (and supported providers)

`context.llm()` is a **convenience accessor** that gives you a ready-to-use LLM client for the current run.

Under the hood it returns a `GenericLLMClient`, which implements:

* `await client.chat(messages, **kw)`  – text (and multimodal) chat
* `await client.embed(texts, **kw)`    – embeddings

The client is created from config (`LLMSettings`) and currently supports these providers:

* `openai`    – OpenAI-compatible API (GPT‑4o, GPT‑5, etc.)
* `anthropic` – Claude 3.x models via `/v1/messages`
* `google`    – Gemini models via `generateContent` / `embedContent`
* `lmstudio`  – LM Studio’s OpenAI-compatible local server
* `ollama`    – Ollama’s OpenAI-compatible local server

(Plus `azure` and `openrouter` if you configure them.)

> **Important:** This layer is meant as a *lightweight* helper. It is **not exhaustively tested across every model and provider variant**. If you hit an edge case or a model with a quirky API, you can:
>
> * Call the HTTP APIs yourself with plain Python, or
> * Register your own extended service and bypass `context.llm()` for that use case.

---

## 2. What is a “profile”?

A **profile** is a named LLM configuration: provider + model + optional base URL, timeout, and secrets.

Structurally (from config):

```python
class LLMProfile(BaseModel):
    provider: Provider = "openai"      # e.g. "openai", "anthropic", "google", "lmstudio", "ollama"
    model: str = "gpt-4o-mini"         # chat / reasoning model
    embed_model: str | None = None      # optional embedding model
    base_url: str | None = None
    timeout: float = 60.0
    azure_deployment: str | None = None
    api_key: SecretStr | None = None
    api_key_ref: str | None = None

class LLMSettings(BaseModel):
    enabled: bool = True
    default: LLMProfile = LLMProfile()
    profiles: Dict[str, LLMProfile] = Field(default_factory=dict)
```

At runtime, these become `GenericLLMClient` instances keyed by profile name:

* `"default"` – always present
* `"gemini"`, `"anthropic"`, `"local"`, etc. – optional extra profiles

---

## 3. Using `context.llm()` inside a node

### 3.1 Basic usage (default profile)

```python
async def hello_world(*, context: NodeContext, input_text: str):
    llm = context.llm()  # same as context.llm("default")

    text, usage = await llm.chat([
        {"role": "system", "content": "Be brief."},
        {"role": "user", "content": f"Say hi back to: {input_text}"},
    ])

    return {"reply": text, "usage": usage}
```

### 3.2 Using a named profile

```python
async def multi_vendor_demo(*, context: NodeContext, query: str):
    openai_client   = context.llm("default")   # e.g. OpenAI
    gemini_client   = context.llm("gemini")    # Google Gemini profile
    anthropic_client = context.llm("anthropic") # Claude profile

    o_text, _ = await openai_client.chat([
        {"role": "user", "content": f"OpenAI: {query}"},
    ])

    g_text, _ = await gemini_client.chat([
        {"role": "user", "content": f"Gemini: {query}"},
    ])

    a_text, _ = await anthropic_client.chat([
        {"role": "user", "content": f"Claude: {query}"},
    ])

    return {"openai": o_text, "gemini": g_text, "anthropic": a_text}
```

### 3.3 Embeddings via `embed()`

```python
async def embed_example(*, context: NodeContext, texts: list[str]):
    # Use default profile’s embedding model (see .env config section below)
    client = context.llm()

    vectors = await client.embed(texts)
    # vectors: List[List[float]]

    return {"embeddings": vectors}
```

### 3.4 Reasoning effort for GPT‑5 (OpenAI)

For OpenAI GPT‑5-family models (e.g. `gpt-5-nano`, `gpt-5-mini`, etc.), you can pass an optional `reasoning_effort` kwarg:

```python
async def gpt5_reasoning_example(*, context: NodeContext):
    client = context.llm("default")  # configured with a gpt-5-* model

    text, usage = await client.chat(
        [
            {"role": "system", "content": "Think step-by-step."},
            {"role": "user", "content": "Explain why 2 + 2 = 4."},
        ],
        reasoning_effort="high",  # "low" | "medium" | "high" (OpenAI GPT‑5 only)
    )

    return {"answer": text, "usage": usage}
```

For non‑GPT‑5 models or non‑OpenAI providers, `reasoning_effort` is ignored.

---

## 4. Configuring profiles via `.env`

### 4.1 Default profile

`AppSettings` uses:

* `env_prefix="AETHERGRAPH_"`
* `env_nested_delimiter="__"`

So the default LLM profile is configured by env vars like:

```env
# Turn LLM on globally
AETHERGRAPH_LLM__ENABLED=true

# Default profile ("default")
AETHERGRAPH_LLM__DEFAULT__PROVIDER=openai
AETHERGRAPH_LLM__DEFAULT__MODEL=gpt-4o-mini
AETHERGRAPH_LLM__DEFAULT__EMBED_MODEL=text-embedding-3-small
AETHERGRAPH_LLM__DEFAULT__BASE_URL=https://api.openai.com/v1
AETHERGRAPH_LLM__DEFAULT__TIMEOUT=60
AETHERGRAPH_LLM__DEFAULT__API_KEY=sk-proj-...
```

### 4.2 Additional named profiles

Profiles live under `llm.profiles["NAME"]`, which maps to env like:

```env
# Gemini profile
AETHERGRAPH_LLM__PROFILES__GEMINI__PROVIDER=google
AETHERGRAPH_LLM__PROFILES__GEMINI__MODEL=gemini-1.5-pro-latest
AETHERGRAPH_LLM__PROFILES__GEMINI__EMBED_MODEL=text-embedding-004
AETHERGRAPH_LLM__PROFILES__GEMINI__TIMEOUT=60
AETHERGRAPH_LLM__PROFILES__GEMINI__API_KEY=AIzaSy...

# Anthropic profile
AETHERGRAPH_LLM__PROFILES__ANTHROPIC__PROVIDER=anthropic
AETHERGRAPH_LLM__PROFILES__ANTHROPIC__MODEL=claude-3-7-sonnet-20250219
AETHERGRAPH_LLM__PROFILES__ANTHROPIC__TIMEOUT=60
AETHERGRAPH_LLM__PROFILES__ANTHROPIC__API_KEY=ant-...

# LM Studio local profile
AETHERGRAPH_LLM__PROFILES__LOCAL__PROVIDER=lmstudio
AETHERGRAPH_LLM__PROFILES__LOCAL__MODEL=your-lmstudio-model-id
AETHERGRAPH_LLM__PROFILES__LOCAL__BASE_URL=http://localhost:1234/v1
AETHERGRAPH_LLM__PROFILES__LOCAL__TIMEOUT=60
```

Then you can access them via:

```python
context.llm()               # default
context.llm("gemini")      # Gemini
context.llm("anthropic")   # Claude
context.llm("local")       # LM Studio
```

> **Note:** `embed_model` is optional. If omitted, `embed()` will fall back to `EMBED_MODEL` env or a sensible default (e.g. `text-embedding-3-small`).

---

## 5. Embeddings & RAG default behavior

For RAG and other embedding-heavy workflows, Aethergraph’s helpers (e.g. index / vector store integration) will typically use the **default profile’s embedding configuration**, i.e.:

* `AETHERGRAPH_LLM__DEFAULT__EMBED_MODEL` if set,
* otherwise `EMBED_MODEL` env var,
* otherwise a built‑in default like `text-embedding-3-small`.

So if you want to control which embedding model is used for **global RAG**, set:

```env
AETHERGRAPH_LLM__DEFAULT__EMBED_MODEL=text-embedding-3-small
```

or override per call:

```python
vectors = await context.llm().embed(texts, model="text-embedding-3-large")
```

---

## 6. Adding / overriding profiles at runtime

You don’t have to declare everything in `.env`. You can also create or update profiles **in code at runtime**.

### 6.1 Quick runtime profile with `llm_set_key`

`NodeContext.llm_set_key()` is a convenience for creating or updating a profile in memory:

```python
async def runtime_profile_demo(*, context: NodeContext):
    # Create/update profile "runtime-openai" on the fly
    context.llm_set_key(
        provider="openai",
        model="gpt-4o-mini",               # NEW: model included for convenience
        api_key="sk-proj-...",            # in-memory only
        profile="runtime-openai",
    )

    client = context.llm("runtime-openai")

    text, _ = await client.chat([
        {"role": "user", "content": "Hello from runtime profile!"},
    ])

    return {"reply": text}
```

This does **not** persist anything to disk or secrets store; it’s only for the current process.

### 6.2 Fully configuring a profile via `llm()`

You can also configure a profile in one shot using `context.llm()` with overrides:

```python
async def llm_inline_config_demo(*, context: NodeContext):
    client = context.llm(
        profile="lab",
        provider="google",
        model="gemini-1.5-pro-latest",
        api_key="AIzaSy...",
        base_url="https://generativelanguage.googleapis.com",
        timeout=60.0,
    )

    text, _ = await client.chat([
        {"role": "user", "content": "Hi from the lab profile!"},
    ])

    return {"reply": text}
```

If the profile doesn’t exist, it will be created. If it exists, it will be updated in place.

---

## 7. Provider-specific config notes

### 7.1 OpenAI (`provider="openai"`)

**Required:**

* `AETHERGRAPH_LLM__...__API_KEY` – or `OPENAI_API_KEY` if using env-based fallback.

**Optional / defaults:**

* `base_url` – defaults to `https://api.openai.com/v1`.
* `timeout` – defaults to `60` seconds.
* `model` – any chat/vision/reasoning model (e.g. `gpt-4o-mini`, `gpt-4o`, `gpt-5-nano`).
* `embed_model` – e.g. `text-embedding-3-small`.

### 7.2 Anthropic (`provider="anthropic"`)

**Required:**

* `api_key` – `ANTHROPIC_API_KEY` or `AETHERGRAPH_LLM__...__API_KEY`.
* `model` – e.g. `claude-3-7-sonnet-20250219`.

**Optional / defaults:**

* `base_url` – defaults to `https://api.anthropic.com`.
* `timeout` – defaults to `60`.

> Anthropic does **not** support embeddings via this client. `embed()` will raise `NotImplementedError` for `provider="anthropic"`.

### 7.3 Google / Gemini (`provider="google"`)

**Required:**

* `api_key` – `AETHERGRAPH_LLM__...__API_KEY`.
* `model` – e.g. `gemini-1.5-pro-latest` for chat.

**Optional / defaults:**

* `base_url` – defaults to `https://generativelanguage.googleapis.com`.
* `embed_model` – e.g. `text-embedding-004`.

**Endpoints used:**

* Chat: `POST /v1/models/{model}:generateContent`.
* Embeddings: `POST /v1/models/{embed_model}:embedContent`.

### 7.4 LM Studio (`provider="lmstudio"`)

LM Studio exposes an OpenAI-compatible server.

**Required:**

* `base_url` – usually `http://localhost:1234/v1` (or whatever the LM Studio UI shows).
* `model` – the LM Studio model ID (shown in the UI).

**Optional:**

* No API key is required by default.

**Endpoints used:**

* Chat: `POST {base_url}/chat/completions`.
* Embeddings: `POST {base_url}/embeddings`.

### 7.5 Ollama (`provider="ollama"`)

Ollama also provides an OpenAI-compatible mode.

**Required/Defaults:**

* `base_url` – defaults to `http://localhost:11434/v1` if not set.
* `model` – an Ollama model name (e.g. `llama3`, `mistral`, etc. configured in Ollama).

**Optional:**

* Usually no API key.

**Endpoints used:**

* Chat: `POST {base_url}/chat/completions`.
* Embeddings: `POST {base_url}/embeddings`.

---

## 8. When *not* to use `context.llm()`

`context.llm()` is intentionally thin and opinionated. You might want to bypass it when:

* You need cutting-edge / experimental API features that aren’t wired yet.
* You want a very custom request/response shape.
* You’re targeting a provider that isn’t in the built-in list.

In those cases you can:

* Use `httpx` (or the vendor’s official SDK) directly inside your node, or
* Wrap your own client as a separate service and inject it into `NodeServices`.

The built-in `llm()` helper gives you a fast “happy path” for common providers and models, without preventing you from going lower-level when you need to.
