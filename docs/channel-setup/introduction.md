# Channels Overview

AetherGraph supports multiple **channels** for delivering messages and interacting with users or tools. This page summarizes:

* What channels exist and what they’re good for.
* Which capabilities each channel supports.
* How `ask_*` works vs inform-only channels.
* Notes on persistence, concurrency, and security.

> **Note on OSS channels and scope**

> The channel system in the open-source AetherGraph is designed for **personal, local, and small-team use**, with a focus on convenience and easy integration into your own frontends. It is not intended as a high-scale, multi-tenant messaging infrastructure, and you should not try to “production-scale” the current adapters as-is. In particular, for safety concern, many integrations rely on local polling and simple wiring rather than hardened, multi-region webhook setups. For anything exposed publicly or handling sensitive data, you should treat these channels as experimental building blocks: keep them behind trusted networks, review security settings carefully, and expect that a future, more rigorous release will provide safer patterns for large-scale and public deployments.

---

## 1. Channels and when to use them

### Console (`console:`)

* **Default channel** when you don’t specify anything (key: `console:stdin`).
* Best for:

  * Local development and debugging.
  * Simple CLI-style interaction.
* Messages are printed to the terminal, and `ask_*` reads from standard input.
* No external setup required.

### Slack (`slack:`)

* Two-way, rich chat channel (bot-based).
* Best for:

  * Team workflows.
  * Rich notifications and approvals in Slack.
  * `ask_*` prompts that can resume even if the Python process restarts.
* Requires a Slack app + bot token.

### Telegram (`tg:`)

* Two-way, rich chat channel via the Telegram Bot API.
* Best for:

  * Individual researchers who prefer Telegram.
  * Mobile-friendly notifications and prompts.
* Uses polling (local/dev) or webhook (advanced) to receive messages.
* Support for `ask_*` with resumable waits, similar to Slack (experimental).

### File (`file:`)

* Inform-only channel that **writes messages to disk**.
* Best for:

  * Persistent logs and run transcripts.
  * Keeping a local record under `workspace/channel_files/...`.
* No user input; `ask_*` is not supported.

### Webhook (`webhook:`)

* Generic inform-only channel that **POSTs JSON to a URL**.
* Best for:

  * Sending notifications to services with incoming webhooks (Slack, Discord, etc.).
  * Triggering automation tools like Zapier/Make.
  * Integrating with custom backends.
* Outbound only; no `ask_*`.

---

## 2. Capability comparison

Legend:

* ✅ Supported in a first-class way.
* 📝 Logged/forwarded only (no interaction).
* ✖️ Not supported.

| Channel  | Key prefix / example               | Default?    | Text | Input / `ask_*`  | Buttons / approval | Image | File | Stream / edit | Inbound resume?  |
| -------- | ---------------------------------- | ----------- | ---- | ---------------- | ------------------ | ----- | ---- | ------------- | ---------------- |
| Console  | `console:stdin`                    | ✅  | ✅    | ✅ (inline)       | ✅ (numbered)       | ✖️    | ✖️   | ✖️            | ✖️ (no resume)   |
| Slack    | `slack:team/T:chan/C[:thread/TS]`  | ✖️          | ✅    | ✅                | ✅                  | ✅     | ✅    | ✅             | ✅                |
| Telegram | `tg:chat/<id>[:topic/<thread_id>]` | ✖️          | ✅    | ✅ (experimental) | ✅                  | ✅     | ✅    | ✅             | ✅ (experimental) |
| File     | `file:logs/default.log`            | ✖️          | ✅    | ✖️               | 📝 (logged only)   | 📝    | 📝   | 📝            | N/A                |
| Webhook  | `webhook:https://...`              | ✖️          | ✅    | ✖️               | 📝 (payload only)  | 📝    | 📝   | 📝            | N/A               |

Notes:

* **Console**: simple and local; great for debugging but not meant for long-term, resumable conversations.
* **Slack / Telegram**: full chat channels; support richer content and resumable `ask_*` flows.
* **File / Webhook**: inform-only; they record/deliver messages but cannot accept replies.

---

## 3. `ask_*` vs inform-only channels

### `ask_*` (interactive channels)

* `ask_text`, `ask_approval`, etc. are supported on:

  * **console** (inline input via stdin),
  * **Slack**,
  * **Telegram** (experimental).

* For **Slack/Telegram**:

    * When you call `await context.channel().ask_text(...)`, AetherGraph creates a **Continuation** and stores it.
    * The Python process can safely **wait, sleep, or even be restarted**.
    * When a user replies in Slack/Telegram, the inbound adapter maps that message to the stored Continuation and calls `resume_router.resume(...)`.
    * The graph then continues from where it left off.

### Inform-only channels

* **File** and **Webhook** are strictly **push-only**:

    * `send_text` works (log/write/POST),
    * `ask_*` is not supported and should not be used with these channels.

They’re ideal for notifications, logs, and integrations where you don’t need a conversational back-and-forth.

---

## 4. Console and resuming waits

The **console channel** is designed for simple, inline interaction:

* `send_text` prints directly to the terminal.
* `ask_*` methods read from `stdin` synchronously (via a background executor) and then immediately resume the graph.

Because of this design:

* There is **no durable, cross-process resume** for console-based `ask_*`.
* If the Python process dies while waiting for console input, that wait is not meant to be resumed later.

This is a conscious tradeoff:

* The console channel stays extremely simple and reliable for local interactive runs.
* For resumable, long-lived conversations, prefer Slack or Telegram.

---

## 5. Concurrency and multiple channels

AetherGraph’s channel layer is designed so you can:

* Send **multiple messages concurrently** on the **same channel**:
    * e.g., several `send_text` calls to Slack or file within the same graph.

* Use **multiple channels in one graph**:
    * e.g., log to file, notify via webhook, and talk to Slack in the same run.

Each `ChannelSession` and `OutEvent` is independent; the underlying adapters handle ordering and delivery.

Example pattern:

```python
async def run_with_notifications(context):
    # Console debug
    await context.channel("console:stdin").send_text("Run started")

    # Log to file
    await context.channel("file:runs/exp_01.log").send_text("Run started")

    # Notify Slack
    await context.channel("slack:team/T:chan/C").send_text("Run started in Slack")

    # Notify external system via webhook
    await context.channel("webhook:https://hooks.zapier.com/hooks/catch/.../").send_text(
        "Run started in AetherGraph"
    )
```

---

## 6. Security notes for webhook channels

Webhook channels POST data to arbitrary URLs. Keep these points in mind:

* **Treat webhook URLs as secrets:**
    * Many platforms use long, random webhook URLs as the only authentication.
    * Do not commit them to public repos or print them in logs.

* **Use HTTPS whenever possible:**
    * Always prefer `https://` URLs so notifications are encrypted in transit.

* **Optional shared secrets:**
    * If you control the receiving endpoint, you can configure the webhook adapter to send an extra header (e.g., `X-AetherGraph-Secret`) and verify it server-side.

* **Least privilege:**
    * Only enable webhook targets that you actually need.

For sensitive or production workflows, consider routing webhook events through a trusted intermediary (e.g., Zapier/Make or your own backend) rather than posting directly to critical systems.
