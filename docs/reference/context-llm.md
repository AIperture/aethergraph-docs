# `context.llm()` – LLM Client & Profiles API Reference

`context.llm()` returns an LLM client (**profile‑aware**) with a consistent API across providers (OpenAI, Azure OpenAI, Anthropic, Google, OpenRouter, LM Studio, Ollama). Use it for **chat**, **embeddings**, and **raw** HTTP calls with built‑in retries and sane defaults.

> See **[LLM Setup & Providers](../llm-setup/llm-setup.md)** for configuring providers, base URLs, and API keys.

---

## Profiles & Configuration

* **Profiles:** Named client configs (default: `"default"`).
* **Get existing:** `client = context.llm()` or `context.llm(profile="myprofile")`.
* **Override/update:** Pass any of `provider/model/base_url/api_key/azure_deployment/timeout` to **create or update** a profile at runtime.
* **Quick set key:** `context.llm_set_key(provider, model, api_key, profile="default")`.

Supported providers: `openai`, `azure`, `anthropic`, `google`, `openrouter`, `lmstudio`, `ollama`.

---

## Quick Reference

| Method                                                                                                    | Purpose                                   | Inputs                                                                     | Returns                          |
| --------------------------------------------------------------------------------------------------------- | ----------------------------------------- | -------------------------------------------------------------------------- | -------------------------------- |
| `chat(messages, *, reasoning_effort=None, max_output_tokens=None, **kw)`                                  | Multi‑turn chat completion                | `messages: list[dict]` • optional `temperature`, `top_p`, `model` override | `(text: str, usage: dict)`       |
| `embed(texts, **kw)`                                                                                      | Compute embeddings                        | `texts: list[str]` • optional `model` override                             | `list[list[float]]`              |
| `raw(*, method="POST", path=None, url=None, json=None, params=None, headers=None, return_response=False)` | Low‑level HTTP with provider auth/headers | See details                                                                | `Any` (JSON or `httpx.Response`) |
| `aclose()`                                                                                                | Close the underlying HTTP client          | —                                                                          | `None`                           |

**Context helpers**

* `context.llm(profile="default", provider=None, model=None, base_url=None, api_key=None, azure_deployment=None, timeout=None)` → `LLMClient`
* `context.llm_set_key(provider, model, api_key, profile="default")` → `None`

---

## Messages Format

Use OpenAI‑style messages:

```python
messages = [
  {"role": "system", "content": "You are concise."},
  {"role": "user", "content": "Summarize this:"},
]
```

Provider adapters translate to vendor formats as needed (e.g., Anthropic messages blocks, Google content parts).

---

## Methods

<details markdown="1">
<summary>chat(messages, *, reasoning_effort=None, max_output_tokens=None, **kw) -> (str, dict)</summary>

**Description:** Send a chat request to the active provider/model and return `(text, usage)`.

**Inputs:**

* `messages: list[dict]`
* `reasoning_effort: str | None` – Provider‑specific hint (e.g., OpenAI Responses).
* `max_output_tokens: int | None`
* `**kw` (optional runtime overrides):

  * `model: str | None`
  * `temperature: float | None`
  * `top_p: float | None`

**Returns:**

* `(text: str, usage: dict)`

**Notes:**

* Implements exponential backoff for transient HTTP errors.
* Normalizes different provider response shapes to a first `text` string.

</details>

<details markdown="1">
<summary>embed(texts, **kw) -> list[list[float]]</summary>

**Description:** Return embeddings for input strings via the provider‑specific embeddings endpoint.

**Inputs:**

* `texts: list[str]`
* `**kw` (optional):

  * `model: str | None`

**Returns:**

* `list[list[float]]`

**Notes:**

* **Anthropic** does not provide embeddings → not implemented.
* **Google** returns a single vector for the concatenated text; client normalizes to a `list[list[float]]`.

</details>

<details markdown="1">
<summary>raw(*, method="POST", path=None, url=None, json=None, params=None, headers=None, return_response=False) -> Any</summary>

**Description:** Escape hatch for provider APIs. Uses the client’s base URL, authentication, and retry logic.

**Inputs:**

* `method: str` – HTTP method (default `"POST"`).
* `path: str | None` – Joined to the client’s `base_url` when `url` is not provided.
* `url: str | None` – Full URL (overrides `path`).
* `json: Any | None` – JSON body.
* `params: dict[str, Any] | None` – Query params.
* `headers: dict[str, str] | None` – Extra headers (merged over defaults).
* `return_response: bool` – If `True`, returns raw `httpx.Response`.

**Returns:**

* `Any` – Parsed JSON by default, or `httpx.Response` when `return_response=True`.

**Notes:**

* Applies provider‑specific auth headers (e.g., `Authorization: Bearer ...`, `x-api-key`, `api-key`).
* Ensures the underlying HTTP client is bound to the current event loop.

</details>

<details markdown="1">
<summary>aclose() -> None</summary>

**Description:** Close the internal `httpx.AsyncClient`.

**Inputs:**

* —

**Returns:**

* `None`

</details>

---

## Profiles via `context.llm()`

<details markdown="1">
<summary>context.llm(profile="default", *, provider=None, model=None, base_url=None, api_key=None, azure_deployment=None, timeout=None) -> LLMClient</summary>

**Description:** Get an LLM client for `profile`. If any overrides are provided, **configure or update** that profile on the fly and return the new client.

**Inputs:**

* `profile: str`
* `provider: str | None`
* `model: str | None`
* `base_url: str | None`
* `api_key: str | None`
* `azure_deployment: str | None`
* `timeout: float | None`

**Returns:**

* `LLMClient`

**Notes:**

* If no overrides are provided, this is a pure getter.
* Profiles are maintained by the runtime LLM service and are reusable across nodes.

</details>

<details markdown="1">
<summary>context.llm_set_key(provider, model, api_key, profile="default") -> None</summary>

**Description:** Quickly set/override provider credentials for a profile.

**Inputs:**

* `provider: str` – One of the supported providers.
* `model: str`
* `api_key: str`
* `profile: str` – Defaults to `"default"`.

**Returns:**

* `None`

**Notes:**

* See **[LLM Setup & Providers](./llm-setup.md)** for guidance on keys, endpoints, and environment variables. (placeholder link)

</details>

---

## Provider Behaviors (Summary)

* **OpenAI**: Uses `/v1/responses` for chat (supports `reasoning_effort`). Embeddings via `/v1/embeddings`.
* **Anthropic**: Converts messages to `v1/messages` format. **No embeddings**.
* **Google (Gemini)**: Converts to `generateContent`/`embedContent` requests with API key in URL.
* **OpenRouter/LM Studio/Ollama**: OpenAI‑compatible `/chat/completions` and `/embeddings` endpoints.

---

## Examples

```python
# 1) Use default profile
llm = context.llm()
text, usage = await llm.chat([
    {"role": "system", "content": "Be terse."},
    {"role": "user", "content": "One sentence on FFT."},
])

# 2) Create/update a named profile at runtime
llm_fast = context.llm(
    profile="fast", provider="openai", model="gpt-4o-mini", timeout=20.0,
)

# 3) Quick key configure
context.llm_set_key("openai", "gpt-4o-mini", "sk-...", profile="prod")

# 4) Embeddings
vecs = await llm.embed(["optical flow", "phase mask"])

# 5) Raw call (escape hatch)
resp = await llm.raw(path="/models", method="GET")
```

**Tip:** Prefer `context.llm()` profiles for reuse across nodes and flows; use per‑call overrides for experiments or one‑offs.
