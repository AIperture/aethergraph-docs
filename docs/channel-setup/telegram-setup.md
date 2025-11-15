# Telegram Integration Setup (Local, Experimental)

Connect a **Telegram bot** to **AetherGraph** for local / personal use via polling.

✅ **No public URL or webhook required** (polling).

✅ **Great for demos and quick experiments.**

⚠️ **Status:** Experimental — if the first message is slow to appear or polling stalls, wait a few more seconds before sending or restart the sidecar and send a fresh message.

---

## Before You Start

1. You don't need to install additional dependencies for local Telegram setup

2. Ensure you have a `.env` file in your project root. AetherGraph reads Telegram settings from it.

---

## 1. Create a Telegram Bot (BotFather)

1. In Telegram, start a chat with **@BotFather**.
2. Send `/newbot` and follow prompts:

   * Pick a **name** (e.g., `AetherGraph Telegram Bot`).
   * Pick a **username** ending in `bot` (e.g., `aethergraph_dev_bot`).
3. Copy the **bot token** BotFather returns (looks like `123456789:ABC...`).

> That’s all you need for local polling mode.

---

## 2. Configure `.env` for AetherGraph

Add the following variables (update the values you received):

```env
# Telegram (optional)
AETHERGRAPH_TELEGRAM__ENABLED=true               # must be true to enable
AETHERGRAPH_TELEGRAM__BOT_TOKEN=123456789:ABC... # from BotFather

# Local/dev polling mode (keep this for local usage)
AETHERGRAPH_TELEGRAM__POLLING_ENABLED=true
AETHERGRAPH_TELEGRAM__WEBHOOK_ENABLED=false
```

After saving, **restart** your AetherGraph sidecar so the new settings take effect.

> If you previously used webhooks with this bot, disable them once so polling receives updates:
> ```bash
> curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
> ```

---

## 3. Channel Keys, Defaults, and Aliases

AetherGraph uses a **channel key** to address targets. For Telegram, the canonical format is:

```text
tg:chat/<CHAT_ID>
```

You can wire this up in startup code just like Slack:

```python
import os
from aethergraph.channels import set_default_channel, set_channel_alias

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your-telegram-chat-id")
telegram_channel_key = f"tg:chat/{TELEGRAM_CHAT_ID}"  # Telegram channel key format

# Set as the default channel for context.channel()
set_default_channel(telegram_channel_key)

# Optional: create a friendly alias
set_channel_alias("my_tg", telegram_channel_key)
```

Usage patterns:

```python
chan = context.channel()              # uses default Telegram chat (if set)
await chan.send_text("Hello from AetherGraph via Telegram 👋")

chan2 = context.channel("my_tg")     # use alias explicitly
await chan2.send_text("Message via alias")

# Or target explicitly at call time
await context.channel().send_text("Custom target", channel=telegram_channel_key)
```

**Fallback:** If Telegram isn’t configured, `context.channel()` falls back to `console:stdin`.

---

## 4. Finding Your Telegram Chat ID

* **1:1 chats:** Start a conversation with your bot (send `/start`). Then either:

    * Check recent updates using the Bot API `getUpdates` (your chat ID appears in the payload), or
    * Forward any message to a utility bot like `@userinfobot` to read the numeric ID it reports. (Recommended)

* **Groups / supergroups:** Add your bot to the group and send a message in the group. The chat ID is usually a negative number (often begins with `-100...`). Retrieve it via `getUpdates`.

> See Appendix to learn how to use `@userinfobot` and `getUpdates`

---

## 5. Add the Bot to a Group (Optional)

If you want the bot to post in a group:

1. Add the bot to the group (use the group’s add dialog or mention the bot and choose **Add to Group**).
2. If your flow requires reading history or reacting to commands, ensure the bot has the needed group permissions.
3. Use the group’s chat ID (negative number) as your target.

---

## 6. Quick Test

Create a tiny graph and send a message:

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="ping_telegram")
async def ping_telegram(*, context: NodeContext):
    chan = context.channel()  # uses default Telegram chat if configured
    await chan.send_text("Ping from AetherGraph 🛰️")
    return {"ok": True}
```

Run the graph and confirm the message appears in your Telegram chat.

---

### Notes & Troubleshooting

* First message pickup can be slow on some networks. Send a new message to the bot (e.g., `/start`) and re-run the test.
* If polling appears stuck, restart the sidecar.
* Treat Telegram as **best-effort** for now; for robust production flows, prefer Slack or your internal web UI until Telegram stabilizes.


## Appendix: Get Your Telegram Chat ID (easiest: @userinfobot) 


* **Private 1:1 (DM):**

    - Open @userinfobot and tap Start.
    - It replies with Your ID: <number> — this is your chat ID.
    - Use it as: tg:chat/<number>.

* **Group / Supergroup:**

    - Add @userinfobot to the group.
    - Send any message (e.g., /start or any text).
    - The bot posts the Group ID (a negative number, often -100…).
    - Use it as: tg:chat/<negative_number>.

* **Channel:**

    - Option A (forward): Post in the channel, then forward that post to @userinfobot — it replies with the Channel ID (negative number).
    - Option B (temporary add): Add @userinfobot to the channel (temporarily, usually as admin), post once, and the bot will report the Channel ID.

You can remove @userinfobot after you’ve captured the ID.

> Optional alternative: You can also retrieve the ID using Telegram’s Bot API getUpdates and reading chat.id from the JSON. See Telegram official documents on how to use it.