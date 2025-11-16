# `context.channel()` – ChannelSession API Reference

A `ChannelSession` provides message I/O, user prompts, streaming text, and progress updates through the configured channel (console/Slack/…). It also manages continuation tokens to avoid race conditions.

---

## Channel Resolution & Defaults

* **Channel selection priority:** explicit `channel` arg → session override (from `context.channel(channel_key)`) → bus default → `console:stdin`.
* Events are published after **alias → canonical** key resolution.

---

## Quick Reference

| Method                                                                                   | Purpose                                 | Returns              |
| ---------------------------------------------------------------------------------------- | --------------------------------------- | -------------------- |
| `send(event, *, channel=None)`                                                           | Publish a pre-built `OutEvent`          | `None`               |
| `send_text(text, *, meta=None, channel=None)`                                            | Send a plain text message               | `None`               |
| `send_rich(text=None, *, rich=None, meta=None, channel=None)`                            | Send structured content + optional text | `None`               |
| `send_image(url=None, *, alt="image", title=None, channel=None)`                         | Send an image                           | `None`               |
| `send_file(url=None, *, file_bytes=None, filename="file.bin", title=None, channel=None)` | Upload/send a file                      | `None`               |
| `send_buttons(text, buttons, *, meta=None, channel=None)`                                | Send message with buttons               | `None`               |
| `ask_text(prompt, *, timeout_s=3600, silent=False, channel=None)`                        | Prompt for free‑form text               | `str`                |
| `wait_text(*, timeout_s=3600, channel=None)`                                             | Alias of `ask_text(None, silent=True)`  | `str`                |
| `ask_approval(prompt, options=("Approve","Reject"), *, timeout_s=3600, channel=None)`    | Choice/confirmation                     | `{approved, choice}` |
| `ask_files(*, prompt, accept=None, multiple=True, timeout_s=3600, channel=None)`         | Prompt for uploads                      | `{text, files}`      |
| `ask_text_or_files(*, prompt, timeout_s=3600, channel=None)`                             | Text **or** files                       | `{text, files}`      |
| `get_latest_uploads(*, clear=True)`                                                      | Read inbox uploads (Ephemeral KV)       | `list[FileRef]`      |
| `stream(channel=None)`                                                                   | Streaming text (ctx manager)            | `StreamSender`       |
| `progress(*, title="Working...", total=None, key_suffix="progress", channel=None)`       | Progress UI (ctx manager)               | `ProgressSender`     |

---

## Methods

<details markdown="1">
<summary>send(event, *, channel=None)</summary>

**Description:** Publish a pre‑built `OutEvent` to the channel.

**Inputs:**

* `event: OutEvent` – If missing `channel`, resolver fills it.
* `channel: str | None` – Optional override.

**Returns:**

* `None` (async)

**Notes:** Use when you need full control of the event payload/type.

</details>

<details markdown="1">
<summary>send_text(text, *, meta=None, channel=None)</summary>

**Description:** Send a plain text message.

**Inputs:**

* `text: str`
* `meta: dict[str, Any] | None`
* `channel: str | None`

**Returns:**

* `None` (async)

**Emits:**

* `agent.message` with `text`, optional `meta`.

</details>

<details markdown="1">
<summary>send_rich(text=None, *, rich=None, meta=None, channel=None)</summary>

**Description:** Send a message with a rich structured payload (cards/blocks), plus optional text.

**Inputs:**

* `text: str | None`
* `rich: dict[str, Any] | None`
* `meta: dict[str, Any] | None`
* `channel: str | None`

**Returns:**

* `None` (async)

**Emits:**

* `agent.message` with `text`, `rich`, `meta`.

</details>

<details markdown="1">
<summary>send_image(url=None, *, alt="image", title=None, channel=None)</summary>

**Description:** Send an image by URL.

**Inputs:**

* `url: str | None`
* `alt: str`
* `title: str | None`
* `channel: str | None`

**Returns:**

* `None` (async)

**Emits:**

* `agent.message` with `image={url, alt, title}`.

</details>

<details markdown="1">
<summary>send_file(url=None, *, file_bytes=None, filename="file.bin", title=None, channel=None)</summary>

**Description:** Upload/send a file.

**Inputs:**

* `url: str | None`
* `file_bytes: bytes | None`
* `filename: str`
* `title: str | None`
* `channel: str | None`

**Returns:**

* `None` (async)

**Emits:**

* `file.upload` with `file={filename, url?, bytes?}`.

**Notes:** Adapters decide whether to fetch `url` or accept `bytes`.

</details>

<details markdown="1">
<summary>send_buttons(text, buttons, *, meta=None, channel=None)</summary>

**Description:** Send a message with inline buttons/links.

**Inputs:**

* `text: str`
* `buttons: list[Button]`
* `meta: dict[str, Any] | None`
* `channel: str | None`

**Returns:**

* `None` (async)

**Emits:**

* `link.buttons` with `text`, `buttons`, `meta`.

</details>

<details markdown="1">
<summary>ask_text(prompt, *, timeout_s=3600, silent=False, channel=None) -> str</summary>

**Description:** Ask the user for a free‑form text reply. Race‑free via continuations.

**Inputs:**

* `prompt: str | None`
* `timeout_s: int`
* `silent: bool`
* `channel: str | None`

**Returns:**

* `str` – User’s response text (empty string if none)

**Notes:** Creates continuation `kind="user_input"` and awaits resolution; adapters may inline‑resolve.

</details>

<details markdown="1">
<summary>wait_text(*, timeout_s=3600, channel=None) -> str</summary>

**Description:** Alias for `ask_text(prompt=None, silent=True)`.

**Inputs:**

* `timeout_s: int`
* `channel: str | None`

**Returns:**

* `str`

</details>

<details markdown="1">
<summary>ask_approval(prompt, options=("Approve","Reject"), *, timeout_s=3600, channel=None) -> dict</summary>

**Description:** Ask the user to choose from options (approval/confirmation). Normalizes to `{approved, choice}`.

**Inputs:**

* `prompt: str`
* `options: Iterable[str]`
* `timeout_s: int`
* `channel: str | None`

**Returns:**

* `{ "approved": bool, "choice": Any }`

**Notes:** Continuation `kind="approval"` with payload `{prompt:{title, buttons}}`. If adapter doesn’t set explicit approval, first option means approved (case‑insensitive comparison).

</details>

<details markdown="1">
<summary>ask_files(*, prompt, accept=None, multiple=True, timeout_s=3600, channel=None) -> dict</summary>

**Description:** Ask for file upload(s), optionally with text.

**Inputs:**

* `prompt: str`
* `accept: list[str] | None` (MIME or extensions, client hints)
* `multiple: bool`
* `timeout_s: int`
* `channel: str | None`

**Returns:**

* `{ "text": str, "files": list[FileRef] }` (empty `files` on console‑only flows)

**Notes:** Continuation `kind="user_files"`.

</details>

<details markdown="1">
<summary>ask_text_or_files(*, prompt, timeout_s=3600, channel=None) -> dict</summary>

**Description:** Ask for either a text reply or file upload(s).

**Inputs:**

* `prompt: str`
* `timeout_s: int`
* `channel: str | None`

**Returns:**

* `{ "text": str, "files": list[FileRef] }`

**Notes:** Continuation `kind="user_input_or_files"`.

</details>

<details markdown="1">
<summary>get_latest_uploads(*, clear=True) -> list[FileRef]</summary>

**Description:** Retrieve recent uploads captured in the channel inbox (Ephemeral KV), optionally clearing them.

**Inputs:**

* `clear: bool` – If `True`, pops and clears; otherwise returns without clearing.

**Returns:**

* `list[FileRef]`

**Notes:** Requires `services.kv`. Raises `RuntimeError` if unavailable. Inbox key: `inbox://<resolved-channel-key>`.

</details>

<details markdown="1">
<summary>stream(channel=None) -> Async CM yielding StreamSender</summary>

**Description:** Incrementally stream text to a single upserted message; adapters rewrite one message.

**Usage:**

```python
async with context.channel().stream() as s:
    await s.delta("Hello ")
    await s.delta("world")
    await s.end()  # optional
```

**StreamSender Methods:**

* `start()` → emit `agent.stream.start` (auto‑called by first `delta`).
* `delta(text_piece: str)` → append chunk; emits `agent.message.update` with full concatenated text (buffered) using upsert key `<run_id>:<node_id>:stream`.
* `end(full_text: str | None = None)` → optional final text, then `agent.stream.end`.

**Notes:** Pass `channel=...` to target a specific channel.

</details>

<details markdown="1">
<summary>progress(*, title="Working...", total=None, key_suffix="progress", channel=None) -> Async CM yielding ProgressSender</summary>

**Description:** Report task progress with start/update/end events.

**Usage:**

```python
async with context.channel().progress(title="Downloading", total=100) as p:
    await p.update(current=10)
    await p.update(inc=15, subtitle="phase 1")
    await p.end(subtitle="Done.")
```

**ProgressSender Methods:**

* `start(subtitle: str | None = None)` → `agent.progress.start`.
* `update(*, current=None, inc=None, subtitle=None, percent=None, eta_seconds=None)` → `agent.progress.update`.

  * `percent` sets `current` when `total` known; `inc` increments; `current` overrides.
* `end(*, subtitle: str | None = "Done.", success: bool = True)` → `agent.progress.end`.

**Notes:** Upserts use key `<run_id>:<node_id>:<key_suffix>`. Use different `key_suffix` for multiple bars.

</details>

---

## Continuations & Race‑Free Waiting (behavioral notes)

1. Create continuation with `kind`, `payload`, `deadline`.
2. **Prepare wait future before notify** (prevents wait‑before‑resume race).
3. `ChannelBus.notify()` may inline‑resolve; if so, future is resolved and continuation cleaned up.
4. Bind correlators so webhooks can locate the continuation.
5. Await the prepared future until the router resolves it.

---

## Event Types (emitted)

* `agent.message`, `agent.message.update`
* `file.upload`
* `link.buttons`
* `agent.stream.start`, `agent.stream.end`
* `agent.progress.start`, `agent.progress.update`, `agent.progress.end`
