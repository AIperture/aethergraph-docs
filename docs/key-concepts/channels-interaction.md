# Channels and Interaction

A **channel** is how an agent *communicates* with the outside world — Slack, Telegram, Console, Web, or any other adapter. The `context.channel()` method returns a **ChannelSession**, a lightweight helper that provides a consistent Python API for sending and receiving messages, buttons, files, streams, and progress updates — regardless of which adapter you use.

> **Default behavior:** If no adapters are configured, AetherGraph automatically uses the console (`"console:stdin"`) as the default channel for input/output. To target Slack, Telegram, or Web, see [*Channel Setup*](../channel-setup/introduction.md) section; your agent code remains unchanged in all channels.

> **In short:** Switch communication targets freely. The agent logic stays identical.

---

## 1. What Is a Channel?

A **channel** is a routing target for interaction. It allows you to interact with an Agent inside a Python function. 

You can specify a channel key or alias (e.g., `"slack:team/T:chan/C[:thread/TS]"`) or rely on the system default. See [*Channel Setup*](../channel-setup/introduction.md) for non-console key setup. 

### Resolution Order

1. **Per-call override:** `await context.channel().send_text("hi", channel="slack:team/T:chan/C[:thread/TS]")`
2. **Bound session key:** `ch = context.channel("slack:team/T:chan/C[:thread/TS]"); await ch.send_text("hi")`
3. **Bus default:** taken from `services.channels.get_default_channel_key()`
4. **Fallback:** `console:stdin`

When using **Aethergraph UI**

- Use `context.ui_run_channel()` to get the run workspace channel adapter (equivalent to `context.channel("ui:run/run_id"))
- Use `context.ui_session_channel()` to get the session workspace channel adapter (equivalent to `context.channel("ui:session/session_id))

---

## 2. Quick Start

```python
from aethergraph import graph_fn

@graph_fn(name="channel_demo")
async def channel_demo(*, context):
    ch = context.channel()
    await ch.send_text("Starting experiment…")
    resp = await ch.ask_approval("Proceed?", options=["Yes", "No"])
    if resp["approved"]:
        await ch.send_text("✅ Launching run.")
```

> Channels handle both output and input asynchronously — messages, approvals, file uploads, and more — using cooperative waits under the hood.

---

## 3. Core Methods

> Availability depends on the adapter’s capabilities (e.g., file uploads are not supported in the console channel).

| Method                                                                                   | Purpose                                           |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `send_text()`  / `ask_text()`                                                     | Send/ask a plain text message.                        |
| `send_file()` / `ask_file()`  | Upload/ask a file.                          |
| `ask_approval()`    | Request approval or a choice.                     |
| `send_buttons()` | Send buttons to UI with links | 
| `stream()`                                                                   | Open a streaming session for incremental updates. |
| `get_last_uploads()` | Fetch uploaded files from UI at anytime | 

> All `ask_*` methods use event-driven continuations, ensuring replies are properly correlated to their originating node.

For exact usage, refer to `context.channel()` API. 

---


## 4. Concurrency and Fan-Out

You can launch multiple concurrent asks in the same bound channel session and correlate the results:

```python
import asyncio

@graph_fn(name="concurrent_asks")
async def concurrent_asks(*, context):
    ch = context.channel()

    async def one(tag):
        name = await ch.ask_text(f"[{tag}] What’s your name?")
        await ch.send_text(f"[{tag}] Thanks, {name}!")
        return {tag: name}

    a, b = await asyncio.gather(one("A"), one("B"))
    return {"names": a | b}
```

---

## 5. Extensibility

The channel interface can be extended to support **any platform** with a compatible API (HTTP, WebSocket, SDK). In practice, the inbound method for resuming interactions depends heavily on the target platform’s event model.

* For **notification-only** channels, the API is straightforward — send events, no continuations.
* For **interactive channels** (e.g., Slack, Telegram, Web), resumptions rely on correlation IDs and continuation stores.

In the OSS edition, AetherGraph currently includes built-in support for **Console**, **Slack**, **Telegram**,  **Webhooks**, and **native Aethergraph UI**. We will release adapter protocal API for extension and support for additional adapters in future releases.

---

## Summary

* Channels unify all interaction patterns (text, files, approvals, progress, and streaming) under one async API.
* Default channel is console; others (Slack, Telegram, Web) are pluggable.
* All `ask_*` methods suspend execution via event-driven continuations, resuming seamlessly upon reply.
* Channels are **adapter-agnostic** and **fully extensible** — swap backends, not code.

> Write once, interact anywhere — your agents stay Pythonic, event‑driven, and platform‑neutral.