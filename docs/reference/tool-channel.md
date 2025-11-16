# Built-in Channel Tools (`@tool`)

AetherGraph ships a small set of **built-in channel tools** that wrap the active `context.channel()` service. They are all defined as `@tool(...)` so that:

* In **graph mode** (`@graph_fn`, `@graphify`), each call becomes a **tool node** with proper provenance.
* The `ask_*` tools support **resumable waits** (user input, approvals, file uploads).
* In immediate mode (no active graph), they behave like plain async functions returning dicts.

> **Important:** All `ask_*` tools are meant to be called **from a graph** (`@graph_fn` or `@graphify`), *not* from inside another `@tool` implementation. They rely on a `NodeContext` and wait/resume semantics that only exist at the graph level.

All tools here assume `context` is injected automatically by the runtime; you typically **do not** pass `context` yourself.

---

## 1. `ask_text` – prompt + wait for free-form reply

```python
@tool(name="ask_text", outputs=["text"])
async def ask_text(
    *,
    resume=None,
    context=None,
    prompt: str | None = None,
    silent: bool = False,
    timeout_s: int = 3600,
    channel: str | None = None,
):
    ...
```

<details markdown="1">
<summary>ask_text(*, resume=None, context=None, prompt=None, silent=False, timeout_s=3600, channel=None) -> {"text": str}</summary>

**Description:**

Send an optional `prompt` message via the active channel and **wait for a text reply**. Under the hood this uses a dual-stage tool (`ask_text_ds`) so the node can enter a **WAITING** state and be resumed later when the user responds.

**Inputs (data/control):**

* `prompt: str | None` – Text shown to the user. If `None`, some channels may only show a generic input request.
* `silent: bool` – If `True`, do not send a visible prompt; only wait for incoming text.
* `timeout_s: int` – Max seconds to wait before timing out.
* `channel: str | None` – Optional channel key or alias (Slack thread, web session, etc.). If `None`, uses the default channel.
* `resume: Any` – Continuation payload used internally on resume. You **do not** set this manually in normal usage.
* `context` – Injected `NodeContext`, used internally via `context.channel()`.

**Returns:**

* `{"text": str}` – The captured user reply as plain text.

**Notes:**

* Use this inside `@graph_fn` / `@graphify` for **resumable user input**.
* Not intended to be called from within another `@tool` implementation.

</details>

---

## 2. `wait_text` – wait for a reply without sending a prompt

```python
@tool(name="wait_text", outputs=["text"])
async def wait_text(
    *, resume=None, context=None, timeout_s: int = 3600, channel: str | None = None
):
    ...
```

<details markdown="1">
<summary>wait_text(*, resume=None, context=None, timeout_s=3600, channel=None) -> {"text": str}</summary>

**Description:**

Wait for the **next incoming text message** on a given channel without sending a new prompt. Useful when a prior node already sent a message, and you only need to block until the user responds.

**Inputs:**

* `timeout_s: int` – Max seconds to wait.
* `channel: str | None` – Channel key/alias; defaults to the current/default channel.
* `resume`, `context` – Internal, handled by the runtime.

**Returns:**

* `{"text": str}` – The received message.

**Notes:**

* Like `ask_text`, this is a **waitable tool node** – only use at graph level.

</details>

---

## 3. `ask_approval` – buttons / approval flow

```python
@tool(name="ask_approval", outputs=["approved", "choice"])
async def ask_approval(
    *,
    resume=None,
    context=None,
    prompt: str,
    options: list[str] | tuple[str, ...] = ("Approve", "Reject"),
    timeout_s: int = 3600,
    channel: str | None = None,
):
    ...
```

<details markdown="1">
<summary>ask_approval(*, prompt, options=("Approve","Reject"), timeout_s=3600, channel=None, ...) -> {"approved": bool, "choice": str}</summary>

**Description:**

Send a message with **button options** (e.g., Approve / Reject) and wait for the user to click one. Ideal for human-in-the-loop approvals in a workflow.

**Inputs:**

* `prompt: str` – Text shown above the buttons.
* `options: list[str] | tuple[str, ...]` – Labels for buttons (first is typically the "approve" action).
* `timeout_s: int` – Max seconds to wait.
* `channel: str | None` – Optional channel key/alias.
* `resume`, `context` – Internal; managed by the runtime.

**Returns:**

* `{"approved": bool, "choice": str}`

  * `approved` – `True` if the chosen label is considered positive (by current policy; typically the first option), `False` otherwise.
  * `choice` – The raw string label clicked by the user.

**Notes:**

* Implemented as a dual-stage waitable tool; use from `@graph_fn` / `@graphify`.

</details>

---

## 4. `ask_files` – prompt for uploads

```python
@tool(name="ask_files", outputs=["text", "files"])
async def ask_files(
    *,
    resume=None,
    context=None,
    prompt: str,
    accept: list[str] | None = None,
    multiple: bool = True,
    timeout_s: int = 3600,
    channel: str | None = None,
):
    ...
```

<details markdown="1">
<summary>ask_files(*, prompt, accept=None, multiple=True, timeout_s=3600, channel=None, ...) -> {"text": str, "files": list[FileRef]}</summary>

**Description:**

Ask the user to **upload one or more files**, optionally constraining allowed types, and wait until they respond.

**Inputs:**

* `prompt: str` – Text requesting the upload.
* `accept: list[str] | None` – Optional list of accepted types (MIME types or extensions), depending on channel implementation.
* `multiple: bool` – If `True`, allow multiple files; otherwise require a single upload.
* `timeout_s: int` – Max seconds to wait.
* `channel: str | None` – Optional channel key/alias.
* `resume`, `context` – Internal.

**Returns:**

* `{"text": str, "files": list[FileRef]}`

  * `text` – Optional message text the user sent along with the files.
  * `files` – List of `FileRef` objects pointing at uploaded files.

**Notes:**

* Files are typically stored via the artifact service behind the scenes; `FileRef` carries enough info to retrieve them.
* Use in graph-level code only.

</details>

---

## 5. `send_text` – fire-and-forget text message

```python
@tool(name="send_text", outputs=["ok"])
async def send_text(
    *, text: str, meta: dict[str, Any] | None = None, channel: str | None = None, context=None
):
    ...
```

<details markdown="1">
<summary>send_text(*, text, meta=None, channel=None, context=None) -> {"ok": bool}</summary>

**Description:**

Send a **text message** to the selected channel and return immediately (no wait).

**Inputs:**

* `text: str` – Message body.
* `meta: dict[str, Any] | None` – Optional metadata for the channel adapter (thread IDs, tags, etc.).
* `channel: str | None` – Target channel key/alias; defaults to the current/default channel.
* `context` – Injected `NodeContext`.

**Returns:**

* `{"ok": True}` on success.

**Notes:**

* Non-waiting tool: useful for notifications, logging, or streaming intermediate updates.

</details>

---

## 6. `send_image` – post an image

```python
@tool(name="send_image", outputs=["ok"])
async def send_image(
    *,
    url: str | None = None,
    alt: str = "image",
    title: str | None = None,
    channel: str | None = None,
    context=None,
):
    ...
```

<details markdown="1">
<summary>send_image(*, url=None, alt="image", title=None, channel=None, context=None) -> {"ok": bool}</summary>

**Description:**

Send an **image** message to the channel, typically by URL.

**Inputs:**

* `url: str | None` – Public or internally resolvable image URL.
* `alt: str` – Alt text.
* `title: str | None` – Optional title/caption.
* `channel: str | None` – Target channel key/alias.
* `context` – Injected.

**Returns:**

* `{"ok": True}` on success.

</details>

---

## 7. `send_file` – attach a file

```python
@tool(name="send_file", outputs=["ok"])
async def send_file(
    *,
    url: str | None = None,
    file_bytes: bytes | None = None,
    filename: str = "file.bin",
    title: str | None = None,
    channel: str | None = None,
    context=None,
):
    ...
```

<details markdown="1">
<summary>send_file(*, url=None, file_bytes=None, filename="file.bin", title=None, channel=None, context=None) -> {"ok": bool}</summary>

**Description:**

Send a **file attachment** to the channel, either by URL or raw bytes.

**Inputs:**

* `url: str | None` – If provided, the channel may fetch the file from this URL.
* `file_bytes: bytes | None` – Raw file contents; used when you already have the bytes in memory.
* `filename: str` – Name to show to the user.
* `title: str | None` – Optional human-friendly label.
* `channel: str | None` – Target channel key/alias.
* `context` – Injected.

**Returns:**

* `{"ok": True}` on success.

**Notes:**

* Channel adapters decide how to handle `url` vs `file_bytes`.

</details>

---

## 8. `send_buttons` – message with interactive buttons

```python
@tool(name="send_buttons", outputs=["ok"])
async def send_buttons(
    *,
    text: str,
    buttons: list[Button],
    meta: dict[str, Any] | None = None,
    channel: str | None = None,
    context=None,
):
    ...
```

<details markdown="1">
<summary>send_buttons(*, text, buttons, meta=None, channel=None, context=None) -> {"ok": bool}</summary>

**Description:**

Send a message with **interactive buttons**, without waiting for a response in this node. Useful for UI-only affordances when another node will handle the actual click.

**Inputs:**

* `text: str` – Message text.
* `buttons: list[Button]` – Channel-specific button descriptors.
* `meta: dict[str, Any] | None` – Optional metadata.
* `channel: str | None` – Target channel key/alias.
* `context` – Injected.

**Returns:**

* `{"ok": True}` on success.

**Notes:**

* To **wait** on a button click, use `ask_approval` instead.

</details>

---

## 9. `get_latest_uploads` – retrieve recent file uploads

```python
@tool(name="get_lastest_uploads", outputs=["files"])
async def get_latest_uploads(*, clear: bool = True, context) -> list[FileRef]:
    ...
```

<details markdown="1">
<summary>get_latest_uploads(*, clear=True, context) -> {"files": list[FileRef]}</summary>

**Description:**

Fetch the most recent **file uploads** associated with the current channel session. This is a convenience around `channel.get_latest_uploads`.

**Inputs:**

* `clear: bool = True` – If `True`, clear the internal buffer after reading so subsequent calls only see newer uploads.
* `context` – Injected `NodeContext`; used to access `context.channel()`.

**Returns:**

* `{"files": list[FileRef]}` – List of file references.

**Notes:**

* Tool is registered under the name `"get_lastest_uploads"` (note the spelling) but the Python symbol is `get_latest_uploads`.
* Any channel session that supports uploads will expose the same upload buffer.

</details>

---

## Usage & Resumption

* All of these are **tools**, so in `@graph_fn` and `@graphify` they appear as nodes in the `TaskGraph`.
* `ask_text`, `wait_text`, `ask_approval`, and `ask_files` are **waitable** tool nodes — they can pause a run and be resumed via continuations (Slack/web UI/etc.).
* Do **not** call these from inside another `@tool` implementation; they depend on graph-level scheduling and `NodeContext`.
* For simple, non-graph scripts, you can still `await` them directly as async functions, but you will not get resumability or persisted state unless running under the sidecar / scheduler.
