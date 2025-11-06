# Channels and Interaction

A **channel** is how your agent *talks* to the outside world (Slack, Telegram, Console, Web, …). `context.channel()` returns a **ChannelSession** — a small helper you use to send/receive messages, buttons, files, streams, and progress with the same Python API, regardless of adapter.

> **Defaults:** If you haven't configured any adapters, AetherGraph uses the console (`"console:stdin"`) as the default channel for all communication. To target Slack/Telegram/Web, see the adapter setup guides and provide credentials/keys; your agent code does not change.

> **In short:** Switch destinations without changing your agent logic. Use a bound session for many messages, or override per call.

---

## 1. What is a Channel?

A **routing target** for interaction. You can invoke a channel session using a key like `"slack:#research"`, or rely on the default configuration.

**Common keys**

* `slack:#research`  (channel)
* `slack:@alice`     (DM)
* `telegram:@mybot`  (chat)
* `console:stdin`    (default fallback)

**Resolution order**

1. Per‑call override → `await context.channel().send_text("hi", channel="slack:#alerts")`
2. Bound session key → `ch = context.channel("slack:#research"); await ch.send_text("hi")`
3. Bus default → `services.channels.get_default_channel_key()`
4. Fallback → `console:stdin`

---

## 2. Quick Start

```python
from aethergraph import graph_fn

@graph_fn(name="channel_demo")
async def channel_demo(*, context):
    ch = context.channel("slack:#research")
    await ch.send_text("Starting experiment…")
    resp = await ch.ask_approval("Proceed?", options=["Yes", "No"])  # {approved, choice}
    if resp["approved"]:
        await ch.send_text("Great — launching run.")
```

---

## 3. Core Methods

| Method                                                                                   | Purpose                                            |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `send_text(text, *, channel=None)`                                                       | Send a plain text message.                         |
| `send_image(url, *, alt="image", title=None, channel=None)`                              | Post an image by URL.                              |
| `send_file(url=None, *, file_bytes=None, filename="file.bin", title=None, channel=None)` | Upload or attach a file.                           |
| `send_buttons(text, buttons, *, channel=None)`                                           | Message with interactive buttons.                  |
| `ask_text(prompt, *, timeout_s=3600, channel=None)`                                      | Ask for free‑text (cooperative wait).              |
| `ask_approval(prompt, options=("Approve","Reject"), *, timeout_s=3600, channel=None)`    | Approve/pick an option.                            |
| `ask_files(prompt, *, accept=None, multiple=True, timeout_s=3600, channel=None)`         | Request file upload(s).                            |
| `ask_text_or_files(prompt, *, timeout_s=3600, channel=None)`                             | Let user reply with text or files.                 |
| `stream(channel=None)`                                                                   | Async context for incremental token/delta updates. |
| `progress(title="Working...", total=None, *, channel=None)`                              | Async context for live progress.                   |

> All *ask* methods use cooperative waits with continuations; replies are correlated to the originating thread.

---

## 4. Streaming & Progress

**Streams** are ideal for tokenized outputs or live logs:

```python
@graph_fn(name="stream_demo")
async def stream_demo(*, context):
    async with context.channel().stream() as s:
        for chunk in ["Hello", " ", "world", "…"]:
            await s.delta(chunk)
        await s.end("Hello world!")
```

**Progress** exposes structured updates (current/total/percent/ETA):

```python
@graph_fn(name="progress_demo")
async def progress_demo(*, context):
    async with context.channel().progress(title="Crunching", total=5) as bar:
        for i in range(5):
            await bar.update(current=i+1, eta_seconds=(4-i)*0.5, subtitle=f"step {i+1}/5")
        await bar.end(subtitle="All set!", success=True)
```

---

## 5. File Uploads & Mixed Replies

Request files (optionally with a text note):

```python
@graph_fn(name="upload_demo")
async def upload_demo(*, context):
    ans = await context.channel().ask_files(
        prompt="Upload your dataset and add a brief note:", accept=[".csv", "application/zip"], multiple=True
    )
    # ans = { "text": str, "files": list[FileRef] }
    await context.channel().send_text(f"Received {len(ans['files'])} file(s). Thanks!")
```

---

## 6. Concurrency Pattern (fan‑out)

You can issue concurrent asks to the **same bound session** and correlate the replies:

```python
import asyncio

@graph_fn(name="concurrent_asks")
async def concurrent_asks(*, context):
    ch = context.channel("slack:#research")
    async def one(tag):
        name = await ch.ask_text(f"[{tag}] What's your name?")
        await ch.send_text(f"[{tag}] thanks, {name}!")
        return {tag: name}
    a, b = await asyncio.gather(one("A"), one("B"))
    return {"names": a | b}
```

---

## 7. Guarantees & Notes

* **Idempotent upserts**: streams/progress use stable keys derived from `(run_id, node_id, suffix)`.
* **Thread correlation**: ask/wait methods bind correlators so replies route to the right node.
* **Adapter agnostic**: change destinations by key; your agent code stays the same.

**See also**: Context Overview → Channels · Continuations & Waits · Slack/Telegram/Web adapters
