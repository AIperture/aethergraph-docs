# Channels and Interaction

A **channel** is how an agent *communicates* with the outside world — Slack, Telegram, Console, Web, or any other adapter. The `context.channel()` method returns a **ChannelSession**, a lightweight helper that provides a consistent Python API for sending and receiving messages, buttons, files, streams, and progress updates — regardless of which adapter you use.

> **Default behavior:** If no adapters are configured, AetherGraph automatically uses the console (`"console:stdin"`) as the default channel for input/output. To target Slack, Telegram, or Web, configure their adapters with valid credentials; your agent code remains unchanged.

> **In short:** Switch communication targets freely. The agent logic stays identical.

---

## 1. What Is a Channel?

A **channel** is a routing target for interaction. It represents where your agent sends or receives messages. You can specify a channel key (e.g., `"slack:#research"`) or rely on the system default.

### Resolution Order

1. **Per-call override:** `await context.channel().send_text("hi", channel="slack:#alerts")`
2. **Bound session key:** `ch = context.channel("slack:#research"); await ch.send_text("hi")`
3. **Bus default:** taken from `services.channels.get_default_channel_key()`
4. **Fallback:** `console:stdin`

---

## 2. Quick Start

```python
from aethergraph import graph_fn

@graph_fn(name="channel_demo")
async def channel_demo(*, context):
    ch = context.channel("slack:#research")
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
| `send_text(text, *, channel=None)`                                                       | Send a plain text message.                        |
| `send_file(url=None, *, file_bytes=None, filename="file.bin", title=None, channel=None)` | Upload or attach a file.                          |
| `send_buttons(text, buttons, *, channel=None)`                                           | Send a message with interactive buttons.          |
| `ask_text(prompt, *, timeout_s=3600, channel=None)`                                      | Ask for free-text input (cooperative wait).       |
| `ask_approval(prompt, options=("Approve","Reject"), *, timeout_s=3600, channel=None)`    | Request approval or a choice.                     |
| `ask_files(prompt, *, accept=None, multiple=True, timeout_s=3600, channel=None)`         | Request file upload(s).                           |
| `stream(channel=None)`                                                                   | Open a streaming session for incremental updates. |
| `progress(title="Working...", total=None, *, channel=None)`                              | Create a live progress bar context.               |

> All `ask_*` methods use event-driven continuations, ensuring replies are properly correlated to their originating node.

---

## 4. Streaming and Progress

### Streaming

Use streams for live token or log updates:

```python
@graph_fn(name="stream_demo")
async def stream_demo(*, context):
    async with context.channel().stream() as s:
        for chunk in ["Hello", " ", "world", "…"]:
            await s.delta(chunk)
        await s.end("Hello world!")
    return {"ok": True}
```

### Progress

Track task progress with structured updates (current, total, percent, ETA):

```python
@graph_fn(name="progress_demo")
async def progress_demo(*, context):
    async with context.channel().progress(title="Crunching", total=5) as bar:
        for i in range(5):
            await bar.update(current=i+1, eta_seconds=(4-i)*0.5, subtitle=f"step {i+1}/5")
        await bar.end(subtitle="All done!", success=True)
    return {"ok": True}
```

---

## 5. File Uploads and Mixed Replies

Request files, optionally with a text comment:

```python
@graph_fn(name="upload_demo")
async def upload_demo(*, context):
    ans = await context.channel().ask_files(
        prompt="Upload your dataset and add a note:",
        accept=[".csv", "application/zip"],
        multiple=True,
    )
    await context.channel().send_text(f"Received {len(ans['files'])} file(s). Thanks!")
    return {"ok": True}
```

`ans` contains both `text` and `files`, where each file is a structured `FileRef` object with metadata and a retrievable URI.

---

## 6. Concurrency and Fan-Out

You can launch multiple concurrent asks in the same bound channel session and correlate the results:

```python
import asyncio

@graph_fn(name="concurrent_asks")
async def concurrent_asks(*, context):
    ch = context.channel("slack:#research")

    async def one(tag):
        name = await ch.ask_text(f"[{tag}] What’s your name?")
        await ch.send_text(f"[{tag}] Thanks, {name}!")
        return {tag: name}

    a, b = await asyncio.gather(one("A"), one("B"))
    return {"names": a | b}
```

---

## 7. Extensibility

The channel interface can be extended to support **any platform** with a compatible API (HTTP, WebSocket, SDK). In practice, the inbound method for resuming interactions depends heavily on the target platform’s event model.

* For **notification-only** channels, the API is straightforward — send events, no continuations.
* For **interactive channels** (e.g., Slack, Telegram, Web), resumptions rely on correlation IDs and continuation stores.

In the OSS edition, AetherGraph currently includes built-in support for **Console**, **Slack**, and **Telegram**. Support for additional adapters (e.g., Web or REST endpoints) will be provided in future releases.

---

## 8. Guarantees and Notes

* **Idempotent updates:** `stream()` and `progress()` use stable keys derived from `(run_id, node_id, suffix)`.
* **Thread-safe correlation:** all `ask_*` calls automatically bind correlators for proper reply routing.
* **Adapter-agnostic:** switch destinations by changing the channel key — agent logic remains identical.
* **Unified abstraction:** all adapters implement the same interface; only configuration changes per environment.

---

## Summary

* Channels unify all interaction patterns (text, files, approvals, progress, and streaming) under one async API.
* Default channel is console; others (Slack, Telegram, Web) are pluggable.
* All `ask_*` methods suspend execution via event-driven continuations, resuming seamlessly upon reply.
* Channels are **adapter-agnostic** and **fully extensible** — swap backends, not code.

> Write once, interact anywhere — your agents stay Pythonic, event‑driven, and platform‑neutral.