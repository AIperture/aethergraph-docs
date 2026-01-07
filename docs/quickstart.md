# Quick Start

A 5‑minute on‑ramp to AetherGraph: install, start the sidecar server, and run your first `@graph_fn`.

---

## 1. Install

```bash
pip install aethergraph
# or, from source
# pip install -e .
```

> **Python**: 3.10+

---

## 2. Start the sidecar server (one‑liner)

AetherGraph ships a lightweight sidecar that wires up core services (logger, artifacts, memory, KV, channels, etc.)

```python
# quickstart_server.py
from aethergraph import start_server

url = start_server()
```

Run it:

```bash
python quickstart_server.py
```

You should see a default HTTP URL `http://127.0.0.1:8745` printed with UI (if available) and API urls. 

---

## 3. Your first graph function

`@graph_fn` turns an ordinary async Python function into a runnable graph entrypoint. If you include a `context` parameter, you get access to built‑in services like `context.channel()` and `context.memory()`.

```python
# quickstart_graph_fn.py
from aethergraph import graph_fn, NodeContext
from aethergraph import start_server

# 1) Start the sidecar so services are available
start_server()

# 2) Define a small graph function
@graph_fn(name="hello.world", inputs=["name"], outputs=["greeting"])
async def hello_world(name: str, *, context: NodeContext):
    # Use the channel to send a message (console by default)
    await context.channel().send_text(f"👋 Hello, {name}! Running graph…")

    # Do any Python you want here — call tools, query memory, etc.
    greeting = f"Hello, {name}. Nice to meet you from AetherGraph."

    # Return outputs as a dict (keys must match `outputs=[...]`)
    return {"greeting": greeting}

# 3) Run it (async wrapper provided)
if __name__ == "__main__":
    import asyncio
    async def main():
        res = await hello_world(name="Researcher")
        print("Result:", res)
    asyncio.run(main())
```

Run it:

```bash
python quickstart_graph_fn.py
```

You should see a console message from the channel and printed output like:

```
Result: {"greeting": "Hello, Researcher. Nice to meet you from AetherGraph."}
```

---

## 4. What just happened?

* **Sidecar server** booted in the background and installed default services (channels, artifacts, memory, KV, logger).
* **`@graph_fn`** built a tiny task graph from your function and executed it.
* **`context.channel()`** used the default channel (console) to emit a message.

> Tip: You can override the channel at call‑site with `context.channel(channel_key=...)`, once you’ve configured adapters like Slack, Telegram or Aethergraph UI.

---

## 5. Next steps

* Add **tools** with `@tool` to wrap reusable steps and surface inputs/outputs.
* Use **`@graphify`** for fan‑in / fan‑out graph construction when the body is mostly tool calls.
* Explore **artifacts** (`context.artifacts()`), **memory** (`context.memory()`), and **RAG** (`context.rag()`)
* Config `.env` file to integrate external channel and llm features