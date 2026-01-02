# Channels & External Interaction

AetherGraph’s **channel system** is how graphs talk to the outside world:

* Send messages, buttons, progress, and files **out** to users / tools.
* Receive replies and uploads **in** and resume waiting nodes.
* Integrate with Slack, Telegram, web UIs, CLIs, and custom transports.

At a high level, there are five pieces:

1. **ChannelBus** – orchestrates outbound events and binds correlators.
2. **ChannelAdapter** – per-platform sender (Slack, Telegram, WS/HTTP, etc.).
3. **Continuation Store** – remembers which continuation is waiting on which channel/thread.
4. **ChannelIngress** – canonical inbound entry point (external → AG).
5. **HTTP/WS endpoints + ChannelClient** – optional transport for generic web UIs / scripts.

The design is:

> **Adapters handle outbound; Ingress handles inbound; the continuation store ties them together.**

---

## 1. Outbound: ChannelBus & ChannelAdapter

When a graph calls `context.channel().send_text()` or `context.channel().ask_text()`, the flow is:

1. The **ChannelSession** builds an `OutEvent` and hands it to **ChannelBus**.
2. ChannelBus picks an adapter based on the **channel key** (e.g. `"slack:team/T:chan/C"`, `"tg:chat/123"`, `"ext:chan/user-123"`).
3. ChannelBus applies **capability-aware fallbacks** (e.g. buttons → text if the adapter has no `"buttons"` capability).
4. The adapter sends the shaped event to the external platform.
5. If the adapter returns a **Correlator**, ChannelBus binds it to the continuation token via the continuation store.

### 1.1 ChannelBus basics

```python
class ChannelBus:
    def __init__(
        self,
        adapters: dict[str, ChannelAdapter],
        *,
        default_channel: str = "console:stdin",
        channel_aliases: dict[str, str] | None = None,
        logger=None,
        resume_router=None,
        store=None,
    ):
        ...

    async def publish(self, event: OutEvent) -> dict | None:
        """Send any OutEvent; smart fallbacks; bind correlator if any."""

    async def notify(self, continuation) -> dict | None:
        """Ask for input/approval/files from a Continuation."""

    async def peek_correlator(self, channel_key: str) -> Correlator | None:
        ...
```

Key ideas:

* **Channel prefix → adapter**: `"slack:..."` goes to the Slack adapter, `"tg:..."` to Telegram, `"ext:..."` to the generic WS/HTTP adapter, etc.
* **Capability-aware fallbacks**: if an adapter doesn’t support buttons or file upload, ChannelBus degrades gracefully to text (numbered options, file links, etc.).
* **Correlator binding**: when an adapter returns a `Correlator`, ChannelBus records a mapping `token → (scheme, channel, thread)` in the continuation store.

### 1.2 ChannelAdapter protocol

Adapters implement a simple protocol:

```python
class ChannelAdapter(Protocol):
    capabilities: set[str]  # e.g. {"text", "buttons", "image", "file", "stream"}

    async def send(self, event: OutEvent) -> dict | None:
        ...
```

* `OutEvent` carries everything the adapter might need:

  * `type`: e.g. `"agent.message"`, `"session.need_input"`, `"session.need_approval"`, `"agent.stream.delta"`, `"agent.progress.update"`, `"file.upload"`, etc.
  * `channel`: channel key string (e.g. `"slack:team/T:chan/C:thread/TS"`).
  * `text`, `buttons`, `file`, `rich`, `upsert_key`, `meta` (including `run_id`, `node_id`, `token`, `resume_key`, etc.).
* The adapter is responsible for mapping `OutEvent` to the platform-specific API.

**You can register custom adapters** at container wiring time:

```python
queue_adapter = QueueChannelAdapter(container, scheme="ext")
container.channel_bus.register_adapter("ext", queue_adapter)
container.channel_bus.set_default_channel_key("ext:chan/default")
```

You are not limited to built-in ones; any prefix (e.g. `"mychat"`) can be mapped to your own adapter.

---

## 2. Continuations, correlators, and resumption

Whenever a node calls `ask_text`, `ask_approval`, or similar:

1. A **Continuation** object is created and stored:

   * `run_id`, `node_id`, `token`, `kind` (e.g. `"user_input"`, `"approval"`, `"user_files"`).
   * `channel` (where replies must come back).
   * `prompt` and optional payload.
2. `ChannelBus.notify(continuation)` sends a prompt event.
3. If the adapter returns a **Correlator**, ChannelBus binds:

   * continuation token → correlator `(scheme, channel, thread)` in the continuation store.
4. When an inbound message arrives, AG uses this mapping to find and resume the right continuation.

A `Correlator` typically looks like:

```python
Correlator(
    scheme="slack",
    channel="slack:team/T:chan/C:thread/TS",
    thread="TS",          # Slack thread_ts
    message="1700000000.1" # (optional) message ts
)
```

### 2.1 Matching inbound messages to a continuation

On the inbound side, we want to answer:

> “Given this (scheme, channel, thread), which continuation is waiting?”

The pattern is:

1. Reconstruct a `Correlator` key from the inbound event:

   * Slack: `scheme="slack"`, `channel="slack:team/T:chan/C[:thread/TS]"`, `thread=thread_ts or ""`.
   * Telegram: `scheme="tg"`, `channel="tg:chat/<chat_id>[:topic/<topic_id>]"`, `thread=str(topic_id or "")`.
   * Generic: `scheme="ext"`, `channel="ext:chan/<channel_id>"`, `thread=provided thread_id or ""`.

2. Ask the continuation store:

   ```python
   cont = await cont_store.find_by_correlator(corr)
   ```

3. If found, call:

   ```python
   await resume_router.resume(run_id=cont.run_id, node_id=cont.node_id, token=cont.token, payload=...)
   ```

For advanced use cases, there is also a **manual resume** endpoint that bypasses channels entirely and resumes directly with `run_id/node_id/token`.

---

## 3. Slack & Telegram: full-featured adapters

Slack and Telegram are the most feature-complete channel adapters today. They serve as reference implementations for how to:

* Send text, buttons, streamed updates, progress, and file uploads.
* Verify inbound webhooks.
* Match inbound messages back to continuations.

### 3.1 Slack: HTTP and Socket Mode

Slack integration consists of:

* A `SlackChannelAdapter` implementing `ChannelAdapter`:

  * `capabilities = {"text", "buttons", "image", "file", "edit", "stream"}`.
  * Sends messages via `chat.postMessage`, `chat.update`, `files.upload_v2`, blocks for buttons, etc.
  * Returns a `Correlator` so the continuation store can bind channel/thread ↔ token.
* HTTP routes:

  * `POST /slack/events` (Events API webhooks).
  * `POST /slack/interact` (interactive buttons).
  * Both verify signatures via Slack’s signing secret.
* Optional **Socket Mode** runner:

  * Uses `SocketModeClient` to receive events and interactive payloads over WebSocket instead of HTTP.
  * Calls the same shared handlers as HTTP.

Slack uses a rich channel key format, e.g.:

```text
slack:team/T123:chan/C456[:thread/1700000000.12345]
```

The Slack utilities:

* Normalize this into a `channel_key`.
* Download and save files as artifacts.
* Append file_refs to a per-channel inbox in `kv_hot`.
* Resume continuations with `{text, files}` payloads when appropriate.

### 3.2 Telegram

Telegram has a similar structure:

* Webhook route: `POST /telegram/webhook` with custom header verification.
* Helpers to:

  * Build channel keys: `tg:chat/<chat_id>[:topic/<topic_id>]`.
  * Download photos/documents and store them as artifacts.
  * Append file_refs to a per-channel inbox.
* Matching strategy:

  * Uses correlators with `scheme="tg"`, `channel="tg:chat/..."`, `thread=str(topic_id or "")`.
  * For inline buttons (callback queries), it can also use a `resume_key` and alias → token mapping for more precise routing.

Slack and Telegram show the **full power** of the channel system: provider-specific verification, downloads, capability mapping, and rich correlator usage.

---

## 4. Generic channels: ChannelIngress, HTTP, and WS

Most users will eventually want a **custom UI** (React app, internal tool, notebook script) rather than Slack/Telegram. For that, AG provides a generic, provider-agnostic path:

* `ChannelIngress` – handles inbound messages (external → AG) in a uniform way.
* `QueueChannelAdapter` – writes outbound events to `kv_hot` outboxes.
* HTTP route `POST /channel/incoming` – generic inbound endpoint.
* WS route `/ws/channel` – generic outbound event stream.
* `ChannelClient` – a small Python client for talking to the server.

### 4.1 ChannelIngress: the inbound core

`ChannelIngress` is the canonical entry point for inbound messages:

```python
@dataclass
class IncomingMessage:
    scheme: str             # e.g. "ext", "mychat", "tg", "slack-http"
    channel_id: str         # logical channel / user id
    thread_id: str | None = None

    text: str | None = None
    files: list[IncomingFile] | None = None
    choice: str | None = None
    meta: dict[str, Any] | None = None


class ChannelIngress:
    async def handle(self, msg: IncomingMessage) -> bool:
        """Resume the matching continuation if any. Returns True if resumed."""
```

The default implementation:

1. Builds a canonical `channel_key` from `(scheme, channel_id)` (e.g. `"ext:chan/user-123"`).
2. Finds a continuation by correlator:

   * Prefer `(scheme, channel_key, thread_id)`.
   * Fallback to `(scheme, channel_key, thread="")`.
3. Optionally downloads files or uses provided URIs and writes them to the artifact store.
4. If a continuation is found, builds a payload based on its `kind`:

   * `"approval"` → `{"choice", "channel_key", "thread_id", "meta"}`.
   * `"user_files"` / `"user_input_or_files"` → `{"text", "files", ...}`.
   * default → `{"text", ...}`.
5. Calls `resume_router.resume(...)` and returns `True`.

You can sub-class `ChannelIngress` to support existing formats (e.g. Telegram’s `tg:chat/...` keys) by overriding `_channel_key`.

### 4.2 QueueChannelAdapter: a generic outbox

For custom UIs, AG ships a generic adapter that pushes events into an **outbox** in `kv_hot`:

```python
class QueueChannelAdapter(ChannelAdapter):
    capabilities: set[str] = {"text", "buttons", "image", "file", "edit", "stream"}

    async def send(self, event: OutEvent) -> dict | None:
        ch_key = event.channel       # e.g. "ext:chan/user-123"
        outbox_key = f"outbox://{ch_key}"

        payload = {
            "type": event.type,
            "channel": event.channel,
            "text": event.text,
            "meta": event.meta,
            "rich": event.rich,
            "upsert_key": event.upsert_key,
            "file": event.file,
            "buttons": [...],   # flattened label/value/style/url
            "ts": ...,
        }

        await container.kv_hot.list_append(outbox_key, [payload])
        return {}
```

The **purpose of `kv_hot` here is not correlation**, but buffering:

* The runtime writes outbound events into outboxes.
* The WS server (and any debugging tools) read from these outboxes.
* You can cap/trim these lists or move them to a more scalable queue later.

### 4.3 HTTP inbound: `/channel/incoming` and manual `/channel/resume`

A generic HTTP route for inbound messages looks like:

```python
@router.post("/channel/incoming")
async def channel_incoming(body: ChannelIncomingBody, request: Request):
    container = request.app.state.container
    ingress: ChannelIngress = container.channel_ingress

    files = [... convert to IncomingFile ...]

    ok = await ingress.handle(
        IncomingMessage(
            scheme=body.scheme,
            channel_id=body.channel_id,
            thread_id=body.thread_id,
            text=body.text,
            files=files or None,
            choice=body.choice,
            meta=body.meta,
        )
    )
    return {"ok": True, "resumed": ok}
```

For power users, a **manual resume** endpoint bypasses channels and correlators entirely:

```python
@router.post("/channel/resume")
async def channel_resume(body: ChannelManualResumeBody, request: Request):
    container = request.app.state.container
    await container.resume_router.resume(
        run_id=body.run_id,
        node_id=body.node_id,
        token=body.token,
        payload=body.payload or {},
    )
    return {"ok": True}
```

### 4.4 WS outbound: `/ws/channel`

To stream outbound events to a UI over WebSocket, AG exposes a generic endpoint:

```python
@router.websocket("/ws/channel")
async def ws_channel(ws: WebSocket):
    await ws.accept()

    hello = await ws.receive_json()
    scheme = hello.get("scheme") or "ext"
    channel_id = hello["channel_id"]

    container = ws.app.state.container
    c = container

    ch_key = f"{scheme}:chan/{channel_id}"
    outbox_key = f"outbox://{ch_key}"

    last_idx = 0
    try:
        while True:
            await asyncio.sleep(0.25)
            events = await c.kv_hot.list_get(outbox_key) or []
            if last_idx < len(events):
                for ev in events[last_idx:]:
                    await ws.send_json(ev)
                last_idx = len(events)
    except WebSocketDisconnect:
        return
```

This gives you a **generic AG channel over WS**:

* UI connects to `/ws/channel` and sends a handshake: `{ "scheme": "ext", "channel_id": "user-123" }`.
* UI calls `POST /channel/incoming` to send messages back.
* All heavy lifting (continuation matching, resumption) is done by `ChannelIngress` + continuation store.

### 4.5 ChannelClient: talking to AG from Python

For scripts, notebooks, or simple tools, AG provides a small `ChannelClient`:

```python
client = ChannelClient(
    base_url="http://localhost:8000",  # your AG server
    scheme="ext",
    channel_id="me",
)

# send message into AG
await client.send_text("hello from my script")

# listen for events from AG
async for ev in client.iter_events():
    print("AG event:", ev["type"], ev.get("text"))
```

This is purely a convenience wrapper around:

* `POST /channel/incoming` (for inbound → AG), and
* `/ws/channel` (for outbound → client).

You can subclass or wrap it to add headers, auth tokens, retry logic, etc.

---

## 5. Auth & security

AG does **not** enforce a global authentication scheme for channels. Responsibilities are split:

* **Provider-specific webhooks (Slack, Telegram, etc.)**:

  * The integration modules include helpers like `_verify_sig` (Slack) and `_verify_secret` (Telegram).
  * These implement the provider’s required verification (HMAC signatures, secret headers).
  * They are *examples* of transport-level security, not a global policy.

* **Generic endpoints (`/channel/incoming`, `/ws/channel`, `/channel/resume`)**:

  * AG treats these as **application-level** concerns.
  * The framework assumes that if a request reaches these routes, it has already passed whatever authentication / authorization your app requires.
  * You are expected to wrap these routes with your own auth, for example:

    ```python
    from fastapi import Depends
    from myapp.auth import require_user

    @router.post("/channel/incoming")
    async def channel_incoming(
        body: ChannelIncomingBody,
        request: Request,
        user = Depends(require_user),  # your auth
    ):
        ...
    ```

* **ChannelClient**:

  * Out of the box, it performs no auth.
  * To use it against a secured AG server, you should:

    * wrap it to add headers (e.g. `Authorization: Bearer ...` or `X-AG-Token`), and
    * configure your server-side routes to check those.

### 5.1 Future: simple shared channel token (idea)

For solo researchers or simple setups, we may add an optional **single shared channel token**:

* Env var: `AETHERGRAPH_CHANNEL_TOKEN="some-long-random-secret"`.

* If set, the built-in `/channel/incoming` and `/ws/channel` routes would require a header like:

  ```http
  X-AG-Channel-Token: some-long-random-secret
  ```

* `ChannelClient` would grow a `token=` argument that automatically adds this header.

This would provide a very simple “personal secure channel” without forcing a full auth stack, while still leaving real authentication/authorization to the host application for multi-user deployments.

---

## 6. Recommended usage patterns

### 6.1 Simple chat UI (one conversation per channel)

For a basic custom UI:

* Use `QueueChannelAdapter` with prefix `"ext"`.
* Use `/channel/incoming` + `/ws/channel` + `ChannelClient`.
* Treat `(scheme, channel_id)` as **one conversation at a time**.
* Let `ChannelIngress` handle matching and resumption.

### 6.2 Multiple flows per user

If you need multiple concurrent prompts per user:

* Distinguish flows via `thread_id` or synthetic `channel_id` values:

  * e.g. `channel_id="user-123:flow-1"`, `thread_id="run-abc"`.
* Ensure adapters return correlators with these details so the continuation store can distinguish them.
* Optionally expose `resume_key` / `run_id/node_id/token` to the UI and use `/channel/resume` directly.

### 6.3 Provider-specific integrations

For Slack/Telegram/other platforms:

* Implement a dedicated `ChannelAdapter` and small provider-specific HTTP routes.
* Use their verification mechanisms (signing secrets, webhook tokens).
* Normalize channel keys and threads into a `Correlator` pattern compatible with your continuation store.

---

## 7. Mental model

You can summarize the channel system as:

* **ChannelBus** – decides *what* to send *where*, and binds correlators.
* **ChannelAdapter** – knows *how* to talk to a specific platform.
* **Continuation store** – remembers *who is waiting* on which channel/thread.
* **ChannelIngress** – turns inbound messages into resumes.
* **HTTP/WS endpoints + ChannelClient** – optional, generic transport for custom UIs.

Everything else is a specialization of this pattern.

This separation keeps AetherGraph’s core runtime clean while still making it easy to:

* integrate deeply with rich platforms like Slack/Telegram, and
* support lightweight custom channels via simple HTTP/WS + a small Python client.
