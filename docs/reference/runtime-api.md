# Runtime Services API – Global Services & Helpers

AetherGraph keeps core runtime services (channels, LLM, RAG, logger, external services, MCP, etc.) in a **services container**. These helpers give you a consistent way to:

* Install or swap the global services container.
* Access channel/LLM/RAG/logger services outside of a `NodeContext`.
* Register **extra context services** reachable via `context.<name>()`.
* Configure RAG backends and MCP clients.

> In most applications you don’t call these directly. When you start the sidecar server via `start_server()` / `start(...)`, it builds a default container (using `build_default_container`) and installs it so that `current_services()` and friends have something to return. The low‑level APIs below are mainly for advanced setups, tests, and custom hosts.

---

## 1. Core Services Container

These functions manage the **process‑wide services container**. Very likely user does not need to manage these manually.

<details markdown="1">
<summary>install_services(services) -> None</summary>

**Description:** Install a services container globally and in the current `ContextVar`.

**Inputs:**

* `services: Any` – Typically the result of `build_default_container()` or your own container.

**Returns:**

* `None`

**Notes:**

* Call this once at app startup if you’re not using the sidecar server.
* `current_services()` will fail until either `install_services(...)` or `ensure_services_installed(...)` has been used.

</details>

<details markdown="1">
<summary>ensure_services_installed(factory) -> Any</summary>

**Description:** Lazily create and install a services container if none exists, using `factory()`.

**Inputs:**

* `factory: Callable[[], Any]` – Function that returns a new services container.

**Returns:**

* `Any` – The active services container.

**Notes:**

* Used internally by the runner to ensure a container exists (`build_default_container`).
* If a container is already installed, it is reused and just bound into the current context.

</details>

<details markdown="1">
<summary>current_services() -> Any</summary>

**Description:** Get the **currently active services container**.

**Inputs:**

* —

**Returns:**

* `Any` – The services container instance.

**Notes:**

* Raises `RuntimeError` if no services have been installed yet.
* Under normal use, this is wired automatically when the server starts.

</details>

<details markdown="1">
<summary>use_services(services) -> context manager</summary>

**Description:** Temporarily override the services container within a `with` block.

**Inputs:**

* `services: Any` – Services container to use inside the context.

**Returns:**

* Context manager – Restores the previous services value on exit.

**Notes:**

* Handy for tests or one‑off experiments where you want an isolated container.

</details>

---

## 2. Channel Service Helpers

Channel helpers give you direct access to the **channel bus** (the same system behind `context.channel()`), and let you configure defaults and aliases.

<details markdown="1">
<summary>get_channel_service() -> Any</summary>

**Description:** Return the channel bus from the current services container.

**Inputs:**

* —

**Returns:**

* `ChannelBus` (typed as `Any` here)

</details>

<details markdown="1">
<summary>set_default_channel(key) -> None</summary>

**Description:** Set the **default channel key** used when no explicit channel is specified.

**Inputs:**

* `key: str` – Channel key (e.g., `"console"`, `"slack:my-bot"`).

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>get_default_channel() -> str</summary>

**Description:** Get the current default channel key.

**Inputs:**

* —

**Returns:**

* `str` – Default channel key.

</details>

<details markdown="1">
<summary>set_channel_alias(alias, channel_key) -> None</summary>

**Description:** Register a **human‑friendly alias** for a channel key.

**Inputs:**

* `alias: str` – Short name to use in configs / code.
* `channel_key: str` – Real channel key (e.g., full Slack route).

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>register_channel_adapter(name, adapter) -> None</summary>

**Description:** Register a **channel adapter implementation** (e.g., Slack, Telegram, custom UI) under a name.

**Inputs:**

* `name: str` – Identifier for the adapter.
* `adapter: Any` – Adapter instance implementing the channel interface.

**Returns:**

* `None`

**Notes:**

* Adapters are usually wired by the server configuration; you rarely need this in everyday graph code.

</details>

---

## 3. LLM & RAG Service Helpers

These helpers configure the process‑wide **LLM client profiles** and the **RAG backend**.

<details markdown="1">
<summary>get_llm_service() -> Any</summary>

**Description:** Return the LLM service from the current container (the same one backing `context.llm()`).

**Inputs:**

* —

**Returns:**

* `Any` – LLM service.

</details>

<details markdown="1">
<summary>register_llm_client(profile, provider, model, embed_model=None, base_url=None, api_key=None, timeout=None) -> None</summary>

**Description:** Configure or update an LLM **profile** on the global LLM service.

**Inputs:**

* `profile: str` – Profile name (e.g., `"default"`, `"fast"`).
* `provider: str` – Provider ID (`"openai"`, `"anthropic"`, etc.).
* `model: str` – Chat/completion model name.
* `embed_model: str | None` – Optional embeddings model.
* `base_url: str | None`
* `api_key: str | None`
* `timeout: float | None`

**Returns:**

* `None` (under the hood the configured client is created and stored).

**Notes:**

* Alias: `set_llm_client = register_llm_client`.
* Equivalent to calling `svc.llm.configure_profile(...)` on the container.

</details>

<details markdown="1">
<summary>set_rag_llm_client(client=None, *, provider=None, model=None, embed_model=None, base_url=None, api_key=None, timeout=None) -> LLMClientProtocol</summary>

**Description:** Set the **LLM client used by the RAG service**.

**Inputs:**

* `client: LLMClientProtocol | None` – Existing client instance. If `None`, a new `GenericLLMClient` is created.
* `provider: str | None`
* `model: str | None`
* `embed_model: str | None`
* `base_url: str | None`
* `api_key: str | None`
* `timeout: float | None`

**Returns:**

* `LLMClientProtocol` – The RAG LLM client actually installed.

**Notes:**

* If `client` is `None`, you **must** provide `provider`, `model`, and `embed_model` to construct a `GenericLLMClient`.
* The chosen client is stored via `svc.rag.set_llm_client(...)`.

</details>

<details markdown="1">
<summary>set_rag_index_backend(*, backend=None, index_path=None, dim=None) -> Any</summary>

**Description:** Configure the **vector index backend** for the RAG service.

**Inputs:**

* `backend: str | None` – e.g., `"sqlite"` or `"faiss"` (defaults from `settings.rag.backend`).
* `index_path: str | None` – Relative or absolute path (defaults from `settings.rag.index_path`).
* `dim: int | None` – Embedding dimension (defaults from `settings.rag.dim`).

**Returns:**

* `Any` – The created vector index instance.

**Notes:**

* Uses `create_vector_index(...)` under the hood and registers it via `svc.rag.set_index_backend(...)`.
* If `backend="faiss"` but FAISS isn’t available, the factory may log a warning and fall back to SQLite.

</details>

---

## 4. Logger Helper

<details markdown="1">
<summary>current_logger_factory() -> Any</summary>

**Description:** Get the logger factory from the services container.

**Inputs:**

* —

**Returns:**

* `Any` – Logger factory; typical usage is `current_logger_factory().for_scheduler()` or similar.

</details>

---

## 5. External Context Services

External context services are extra objects you register on the container and then access via `context.<name>()` inside nodes and tools.

<details markdown="1">
<summary>register_context_service(name, service) -> None</summary>

**Description:** Register a custom service in `svc.ext_services`.

**Inputs:**

* `name: str` – Name under which it will be exposed (e.g., `"trainer"`, `"materials"`).
* `service: Any` – Service instance.

**Returns:**

* `None`

**Notes:**

* Once registered, your `NodeContext` can expose it using a helper like `context.trainer()` (depending on your `NodeContext` implementation).

</details>

<details markdown="1">
<summary>get_ext_context_service(name) -> Any</summary>

**Description:** Get a previously registered external context service.

**Inputs:**

* `name: str`

**Returns:**

* `Any | None` – The service instance or `None` if not present.

</details>

<details markdown="1">
<summary>list_ext_context_services() -> list[str]</summary>

**Description:** List all registered external context service names.

**Inputs:**

* —

**Returns:**

* `list[str]` – Names registered in `svc.ext_services`.

</details>

---

## 6. MCP Service Helpers

These functions configure the **Model Context Protocol (MCP)** integration on the services container.

<details markdown="1">
<summary>set_mcp_service(mcp_service) -> None</summary>

**Description:** Install an MCP service object on the container.

**Inputs:**

* `mcp_service: Any` – Service implementing MCP coordination.

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>get_mcp_service() -> Any</summary>

**Description:** Get the current MCP service instance.

**Inputs:**

* —

**Returns:**

* `Any` – The MCP service instance.

</details>

<details markdown="1">
<summary>register_mcp_client(name, client) -> None</summary>

**Description:** Register an MCP client with the active MCP service.

**Inputs:**

* `name: str` – Logical client name.
* `client: Any` – MCP client instance.

**Returns:**

* `None`

**Notes:**

* Raises `RuntimeError` if no MCP service has been installed (`set_mcp_service(...)`).

</details>

<details markdown="1">
<summary>list_mcp_clients() -> list[str]</summary>

**Description:** List all registered MCP client names.

**Inputs:**

* —

**Returns:**

* `list[str]` – Client names; returns `[]` if no MCP service or clients.

</details>

---

## 7. Summary

* The **services container** is the central place where channels, LLM, RAG, logger, external services, and MCP live.
* The sidecar server normally installs this container for you; otherwise use `install_services(...)` / `ensure_services_installed(...)`.
* Channel, LLM, RAG, and MCP helpers let you configure global behavior without touching individual graphs.
* `register_context_service(...)` is the main hook for extending `NodeContext` with custom domain services (e.g., trainers, simulators, material DBs).
