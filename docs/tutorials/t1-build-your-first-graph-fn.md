# Tutorial 1: Build Your First `graph_fn`

This tutorial walks you through the **core API** of AetherGraph and helps you build your first reactive agent using the `@graph_fn` decorator.

---

## 🚀 Overview

AetherGraph introduces a **Python‑native way** to create agents that can think, wait, and talk — all inside a normal Python function. With the `@graph_fn` decorator, you can:

* Add **context‑aware I/O** (`context.channel()`, `context.llm()`, `context.memory()`)
* Run interactively or headlessly
* Chain, nest, and resume computations without defining a custom graph DSL

In this tutorial, you will:

1. Start the AetherGraph server (the **sidecar**)
2. Define your first `graph_fn`
3. Call an LLM and send messages through the channel
4. Run it synchronously and see the result

---

## 1. Boot the Sidecar

Before you run any agent, you must start the **sidecar server**, which wires up the runtime services such as channel communication, artifact storage, memory, and resumptions.

```python
from aethergraph import start_server

url = start_server()  # launches a lightweight FastAPI server in the background
print("AetherGraph sidecar server started at:", url)
```

> The sidecar is safe to start anywhere — even in Jupyter or interactive shells. It sets up a workspace under `./aethergraph_data` by default. Your data, including artifacts, memory, resumption files, will all be exported to workspace for persist access.

---

## 2. Define a Minimal Agent

A `graph_fn` is a **context‑injected async function** that represents a reactive node or agent.

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="hello_world")
async def hello_world(input_text: str, *, context: NodeContext):
    context.logger().info("hello_world started")

    # Send a message via the default channel (console)
    await context.channel().send_text(f"👋 Hello! You sent: {input_text}")

    # Optional: Call an LLM directly from the context
    llm_text, _usage = await context.llm().chat(
        messages=[
            {"role": "system", "content": "Be brief."},
            {"role": "user", "content": f"Say hi back to: {input_text}"},
        ]
    )
    await context.channel().send_text(f"LLM replied: {llm_text}")

    output = input_text.upper()
    context.logger().info("hello_world finished")
    return {"final_output": output}
```

> **Return value**:
Although you can return any data type in a dictionary, it is suggested to return a dictionary of **JSON-serializable results** (e.g. `{"result": value}`).
For large data or binary files, save them via `context.artifacts().write(...)` and return the artifact path/uri instead for later reuse. 


### Key Concepts

| Concept                 | Description                                                                  |
| ----------------------- | ---------------------------------------------------------------------------- |
| **`@graph_fn`**         | Turns a plain async Python function into a context‑aware agent.              |
| **`NodeContext`**       | Injected automatically. Gives access to channels, memory, LLMs, and logging. |
| **`context.channel()`** | Sends and receives messages (console, Slack, web UI, etc.).                  |
| **`context.llm()`**     | Unified interface to language models via environment configuration.          |
| **`context.logger()`**  | Node‑aware structured logging.                                               |

See the full API of `graph_fn` at *Graph Function API*

---

## 3. Run the Agent

You can run your `graph_fn` directly or use helper runners.

```python
from aethergraph import run

if __name__ == "__main__":
    result = run(hello_world, inputs={"input_text": "hello world"})
    print("Result:", result)
```

Output example:

```
[AetherGraph] 👋 Hello! You sent: hello world
[AetherGraph] LLM replied: Hi there!
Result: {'final_output': 'HELLO WORLD'}
```

> You can also `await hello_world(...)` in any async context — all `graph_fn`s are awaitable by design.

---

## 4. Why This is Different

AetherGraph’s `@graph_fn` model is **Pythonic yet agentic**. Unlike traditional workflow frameworks that require static DAG definitions, AetherGraph lets you:

* **Run without pre‑declaring a graph** – it dynamically builds one as you go.
* **Access unified runtime services** – channels, memory, artifacts, LLMs, and schedulers are all injected via context.
* **Compose natively** – you can `await` another `graph_fn`, mix `@tool`s, or parallelize with `asyncio.gather`.
* **Stay resumable** – everything you run is automatically backed by a persistent runtime; you can resume mid‑flow later.

These traits make AetherGraph unique among Python agent frameworks — designed not only for chatbots, but also for **scientific, engineering, and simulation workflows**.

---

## 5. Next Steps

In the next tutorial, you’ll learn how to turn these reactive functions into **static DAGs** using `graphify()`, enabling resumable and inspectable computation graphs.
