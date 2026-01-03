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
## 0. LLM Setup 
??? quote "context.llm(profile, *, provider, model, base_url, ...)"
    ::: aethergraph.core.runtime.node_context.NodeContext.llm
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "context.llm_set_key.channel(provider, model, api_key, profile)"
    ::: aethergraph.core.runtime.node_context.NodeContext.llm_set_key
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  


## 1. Main APIs

??? quote "chat(messages, *, reasoning_effort, max_output_tokens, ...)"
    ::: aethergraph.services.llm.generic_client.GenericLLMClient.chat
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "generate_image(prompt, *, model, n, ...)"
    ::: aethergraph.services.llm.generic_client.GenericLLMClient.generate_image
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  


??? quote "embed(texts, ...)"
    ::: aethergraph.services.llm.generic_client.GenericLLMClient.embed
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  


## 2. Raw API

??? quote "raw(*, method, path, url, ...)"
    ::: aethergraph.services.llm.generic_client.GenericLLMClient.raw
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  
