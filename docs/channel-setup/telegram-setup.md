# Telegram Integration Setup (Local, Experimental)

This guide shows how to connect a **Telegram bot** to AetherGraph for local / personal use.

> ⚠️ **Status:** Telegram support is currently **experimental**. In practice it often works very well, but sometimes:
>
> * the polling loop can take a while to pick up the first message, or
> * you may need to restart the sidecar if the connection gets stuck.
>
> It’s great for demos and local exploration, but **not recommended yet for production-critical usage.**

We’ll keep it simple and mirror the Slack setup:

1. Create a Telegram bot with **BotFather**.
2. Paste your bot token into the AetherGraph `.env`.
3. (Optional) Choose a default Telegram chat / `channel_key`.
4. Run a quick test.

---

## 1. Create a Telegram bot (BotFather)

1. Open Telegram and start a chat with **@BotFather**.

2. Send the command `/newbot` and follow the prompts:

   * Choose a **name** (e.g. `AetherGraph Telegram Bot`).
   * Choose a **username** (must end with `bot`, e.g. `aethergraph_dev_bot`).

3. BotFather will reply with a message that includes your bot’s **token**, e.g.: `8....:hweCnwe...`

4. Copy that token — you’ll paste it into your AetherGraph `.env` file.

That’s all you need on the Telegram side for local polling.

---

## 2. Add Telegram settings to `.env`

AetherGraph reads Telegram configuration from `AETHERGRAPH_TELEGRAM__*` variables.

For local usage with polling (no public URL, no webhook), add something like this to your `.env`:

```env
# Turn Telegram integration on
AETHERGRAPH_TELEGRAM__ENABLED=true

# Bot token from BotFather
AETHERGRAPH_TELEGRAM__BOT_TOKEN=...

# Local/dev polling mode (recommended)
AETHERGRAPH_TELEGRAM__POLLING_ENABLED=true
AETHERGRAPH_TELEGRAM__WEBHOOK_ENABLED=false

# Optional: default chat ID for context.channel()
AETHERGRAPH_TELEGRAM__DEFAULT_CHAT_ID=...
```

Notes:

* `BOT_TOKEN` is the token from BotFather.
* `POLLING_ENABLED=true` tells AetherGraph to use Telegram’s `getUpdates` API (no public IP required).
* `WEBHOOK_ENABLED=false` keeps webhook mode off for now.
* `DEFAULT_CHAT_ID` is optional but convenient — AetherGraph will use it as the default Telegram chat when you call `context.channel()` with no arguments.

After editing `.env`, restart the AetherGraph sidecar so it picks up the new settings.

> 🔎 **If you previously used webhooks with this bot**: run `deleteWebhook` once so polling can receive updates:
>
> ```bash
> curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
> ```
>
> You only need to do this once per bot.

---

## 3. Default chat and `channel_key`

Internally, AetherGraph uses a **channel key** for each target. For Telegram, the canonical form is:

```text
tg:chat/<CHAT_ID>
```

For basic 1:1 chats or simple groups, that’s all you need.

### 3.1. Using `DEFAULT_CHAT_ID` (recommended)

If you set:

```env
AETHERGRAPH_TELEGRAM__DEFAULT_CHAT_ID=7663982940
```

then AetherGraph will treat:

```text
tg:chat/7663982940
```

as the default Telegram `channel_key`.

In your graph code, you can simply do:

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="hello_telegram")
async def hello_telegram(*, context: NodeContext):
    chan = context.channel()  # uses default Telegram chat
    await chan.send_text("Hello from AetherGraph via Telegram 👋")
```

### 3.2. Selecting a chat explicitly

If you want to target a specific chat (for example, while experimenting with multiple chat IDs), you can pass the `channel_key` directly:

```python
chan = context.channel("tg:chat/7663982940")
await chan.send_text("Sending to this specific Telegram chat")
```

This works the same way in both polling and webhook modes (even though webhook is not recommended for local use right now).

---

## 4. Quick test

Once your `.env` is set and the sidecar is running:

1. Make sure `AETHERGRAPH_TELEGRAM__ENABLED=true` and `POLLING_ENABLED=true`.
2. Send a message to your bot in Telegram (e.g. `/start`).
3. Run a small test graph:

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="ping_telegram")
async def ping_telegram(*, context: NodeContext):
    chan = context.channel()  # uses default Telegram chat if configured
    await chan.send_text("Ping from AetherGraph 🛰️")
```

4. Execute this graph and check that the message appears in your Telegram chat.

If the message arrives, the basic Telegram polling integration is working.

> 🧪 **Experimental note:**
>
> * On some networks, the first polling call may take a while to pick up messages.
> * If it seems stuck, try restarting the sidecar and sending a fresh message.
> * For now, treat Telegram as a **best-effort local channel**; for more robust integrations, prefer Slack or your internal web UI until Telegram support stabilizes.
