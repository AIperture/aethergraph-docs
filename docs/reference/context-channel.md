# AetherGraph — `context.channel()` Reference

This page documents the **ChannelSession** methods returned by `context.channel()`
in a concise, PyTorch‑style format: signature, brief description, parameters, and returns.

## Overview — Choosing a channel

Use `context.channel(<key>)` to bind a **ChannelSession** to a specific destination for all subsequent calls from that session. You can also override per call with the `channel=` keyword.

**Common forms**
- `slack:#research` — a Slack channel by name

- `slack:@alice` — a Slack DM

- `telegram:@mychannel` — a Telegram channel

- `console:stdin` — console fallback (default if nothing is configured)

**Resolution order** (what channel is used?)
1. **Per‑call override**: `await context.channel().send_text("hi", channel="slack:#alerts")`

2. **Bound session key**: `ch = context.channel("slack:#research"); await ch.send_text("hi")`

3. **Bus default**: whatever `services.channels.get_default_channel_key()` returns

4. **Fallback**: `console:stdin`

**Examples**
```python
# Bind a session to #research for many messages
ch = context.channel("slack:#research")
await ch.send_text("Starting the run…")
await ch.send_text("Progress will be posted here.")

# One‑off override to a different channel
await context.channel().send_text("Heads‑up in #alerts", channel="slack:#alerts")

# Stream to #research explicitly
async with context.channel().stream(channel="slack:#research") as s:
    await s.delta("Parsing… ")
    await s.delta("OK")
    await s.end("Done")

# Progress bar to the default (no key passed)
async with context.channel().progress(title="Crunching", total=100) as bar:
    await bar.update(current=30, eta_seconds=90)
    await bar.end(subtitle="All set!")
```



---

## channel.send_text
```
send_text(text, *, meta: dict | None = None, channel: str | None = None)
```
Send a plain text message to a channel.

**Parameters**

- **text** (*str*) – Message body to send.

- **meta** (*dict, optional*) – Arbitrary metadata for adapters/analytics.

- **channel** (*str, optional*) – Per‑call channel override (e.g., `"slack:#research"`).

**Returns**  

`None`

---

<!-- ## channel.send_rich
```
send_rich(text: str | None = None, *, rich: dict | None = None, meta: dict | None = None, channel: str | None = None)
```
Send a message with optional **rich** structured payload (cards/blocks).

**Parameters**

- **text** (*str, optional*) – Optional caption.

- **rich** (*dict, optional*) – Structured payload; adapter‑defined shape.

- **meta** (*dict, optional*) – Arbitrary metadata.

- **channel** (*str, optional*) – Per‑call channel override.

**Returns**  

`None`

--- -->

## channel.send_image
```
send_image(url: str | None = None, *, alt: str = "image", title: str | None = None, channel: str | None = None)
```
Post an image by URL with `alt`/`title` text.

**Parameters**

- **url** (*str, optional*) – Image URL. Use `send_file` for file bytes.

- **alt** (*str*) – Alt text (default: `"image"`).

- **title** (*str, optional*) – Optional title/caption.

- **channel** (*str, optional*) – Per‑call channel override.

**Returns**  

`None`

---

## channel.send_file
```
send_file(url: str | None = None, *, file_bytes: bytes | None = None, filename: str = "file.bin", title: str | None = None, channel: str | None = None)
```
Upload or link a file to the channel. Provide **either** `url` or `file_bytes`.

**Parameters**

- **url** (*str, optional*) – Remote file URL to attach.

- **file_bytes** (*bytes, optional*) – Raw bytes to upload.

- **filename** (*str*) – Display filename (default: `"file.bin"`).

- **title** (*str, optional*) – Optional caption/label.

- **channel** (*str, optional*) – Per‑call channel override.

**Returns**  

`None`

---

## channel.send_buttons
```
send_buttons(text: str, buttons: list[Button], *, meta: dict | None = None, channel: str | None = None)
```
Send a short message with interactive buttons (links or postbacks depending on adapter).

**Parameters**

- **text** (*str*) – Leading text.

- **buttons** (*list[Button]*) – Button list; at minimum a `label` per button.

- **meta** (*dict, optional*) – Arbitrary metadata.

- **channel** (*str, optional*) – Per‑call channel override.


**Returns**  
`None`

---

## channel.ask_text
```
ask_text(prompt: str, *, timeout_s: int = 3600, silent: bool = False, channel: str | None = None)
```
Ask the user for free‑text using cooperative wait/continuations.

**Parameters**

- **prompt** (*str*) – Prompt text shown to the user. (Ignored if `silent=True`.)

- **timeout_s** (*int*) – Deadline in seconds (default: `3600`). 

- **silent** (*bool*) – If `True`, binds to current thread/channel without posting a prompt.

- **channel** (*str, optional*) – Per‑call channel override.

**Returns**  

*str* – The user’s text (empty string if none).

---

## channel.wait_text
```
wait_text(*, timeout_s: int = 3600, channel: str | None = None)
```
Wait for the next text reply in the current thread/channel without sending a prompt.

**Parameters**

- **timeout_s** (*int*) – Deadline in seconds (default: `3600`). 

- **channel** (*str, optional*) – Per‑call channel override.

**Returns**  

*str* – The user’s text.

---

## channel.ask_approval
```
ask_approval(prompt: str, options: Iterable[str] = ("Approve", "Reject"), *, timeout_s: int = 3600, channel: str | None = None)
```
Ask the user to approve or pick an option.

**Parameters**

- **prompt** (*str*) – Title or question.

- **options** (*Iterable[str]*) – Button labels (default: `("Approve","Reject")`).

- **timeout_s** (*int*) – Deadline in seconds (default: `3600`). 

- **channel** (*str, optional*) – Per‑call channel override.

**Returns**  

*dict* – `{ "approved": bool, "choice": str }`.

---

## channel.get_latest_uploads
```
get_latest_uploads(*, clear: bool = True)
```
Fetch latest uploaded files for this channel (Ephemeral KV required).

**Parameters**

- **clear** (*bool*) – If `True`, consume and clear the inbox (default: `True`).

**Returns**  

*list[FileRef]* – Recent file references.

**Raises**  

`RuntimeError` – if KV is not available.

---

## channel.ask_files
```
ask_files(*, prompt: str, accept: list[str] | None = None, multiple: bool = True, timeout_s: int = 3600, channel: str | None = None)
```
Ask the user to upload file(s) with optional text input.

**Parameters**

- **prompt** (*str*) – Prompt text.

- **accept** (*list[str], optional*) – MIME types or extensions (adapter‑hint only).

- **multiple** (*bool*) – Allow selecting multiple files (default: `True`). 

- **timeout_s** (*int*) – Deadline in seconds (default: `3600`). 

- **channel** (*str, optional*) – Per‑call channel override.

**Returns**  

*dict* – `{ "text": str, "files": list[FileRef] }`.

---

## channel.ask_text_or_files
```
ask_text_or_files(*, prompt: str, timeout_s: int = 3600, channel: str | None = None)
```
Let the user respond with either text or file(s).

**Parameters**

- **prompt** (*str*) – Prompt text.

- **timeout_s** (*int*) – Deadline in seconds (default: `3600`). 

- **channel** (*str, optional*) – Per‑call channel override.

**Returns**  

*dict* – `{ "text": str, "files": list[FileRef] }`.

---

## channel.stream
```
stream(channel: str | None = None)  # async context manager
```
Create a **stream** for incremental message updates (token/delta style).  
Within the context, use `s.delta()` to append text and `s.end()` to finalize.

**Parameters**

- **channel** (*str, optional*) – Per‑stream channel override.

**Yields**  
*StreamSender* – with methods:

- `start()` – explicitly start the stream (optional; auto on first delta).

- `delta(text_piece: str)` – append a delta (adapter receives upsert with full text).

- `end(full_text: str | None = None)` – finalize; optionally set final text.

**Example**
```python
from aethergraph import graph_fn

@graph_fn(name="stream_demo")
async def stream_demo(*, context):
    async with context.channel().stream() as s:
        for chunk in ["Hello", " ", "world", "…"]:
            await s.delta(chunk)
        await s.end("Hello world!")
```

---

## channel.progress
```
progress(*, title: str = "Working...", total: int | None = None, key_suffix: str = "progress", channel: str | None = None)  # async context manager
```
Create a **progress** reporter (start/update/end) bound to the current run/node.

**Parameters**

- **title** (*str*) – Progress title (default: `"Working..."`).

- **total** (*int, optional*) – If set, progress is shown as `current/total`; allows `percent` updates.

- **key_suffix** (*str*) – Included in the internal upsert key (default: `"progress"`). 

- **channel** (*str, optional*) – Per‑progress channel override.

**Yields**  
*ProgressSender* – with methods:

- `start(subtitle: str | None = None)` – start (auto on first update).

- `update(current: int | None = None, inc: int | None = None, subtitle: str | None = None, percent: float | None = None, eta_seconds: float | None = None)`

- `end(subtitle: str | None = "Done.", success: bool = True)`

**Example**
```python
from aethergraph import graph_fn

@graph_fn(name="progress_demo")
async def progress_demo(*, context):
    async with context.channel().progress(title="Crunching", total=5) as bar:
        for i in range(5):
            await bar.update(current=i+1, eta_seconds=(4-i)*0.5, subtitle=f"step {i+1}/5")
        await bar.end(subtitle="All set!")
```

---

### Channel resolution notes

- Per‑call `channel=` overrides everything.

- Otherwise, the session’s bound key (from `context.channel(bound_key)`) is used.

- Else, the bus default via `services.channels.get_default_channel_key()`.

- Else, fallback `"console:stdin"`.

### Guarantees

- Streams/progress use idempotent **upsert keys** derived from `(run_id, node_id, suffix)`.

- Ask methods **bind correlators** at both message and thread level to capture replies.
