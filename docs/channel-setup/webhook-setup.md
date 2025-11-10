# Webhook Channel Setup & Usage

The **webhook channel** lets AetherGraph send events to almost any external service that accepts an HTTP POST.

> 🔔 **One-way only:** webhook channels are **inform-only**. They push messages *out* from AetherGraph, but cannot receive replies or drive `ask_*` prompts.
>
> This makes them perfect for notifications, logs, and status updates.

We’ll cover:

1. What the webhook channel is and when to use it.
2. Supported platforms (tested examples).
3. How to use `webhook:` channels in your graphs.

---

## 1. What is the webhook channel?

A **webhook channel** is a generic one-way output channel:

* When your graph calls:

  ```python
  await context.channel("webhook:<URL>").send_text("Run finished ✅")
  ```

* AetherGraph’s webhook adapter will `POST` a small JSON payload to `<URL>` with fields like:

  ```json
  {
    "type": "agent.message",
    "channel": "webhook:<URL>",
    "text": "Run finished ✅",
    "content": "Run finished ✅",
    "meta": {},
    "timestamp": "..."
  }
  ```

* The external service (Slack, Discord, Zapier, etc.) receives that payload and does something with it.

Key properties:

* **Inform-only:** no replies, no continuations, no `ask_*`.
* **Outbound-only:** AetherGraph only makes HTTP requests; no need to expose a public server for this.
* **Very flexible:** one adapter can talk to many tools, depending on the URL you plug in.

Use webhooks when you want to:

* Get notifications in Slack/Discord when a run finishes.
* Pipe run updates into automation tools like Zapier.
* Trigger external workflows (email, Notion, issue tracking, etc.) without building a custom adapter.

---

## 2. Supported platforms (tested examples)

The webhook channel is **generic**, but a few platforms have been tested and work well:

### 2.1. Slack (Incoming Webhook)

Slack has a built-in **Incoming Webhook** feature:

1. In Slack, go to **Apps → Manage Apps → Search for “Incoming Webhooks”**.
2. Add the **Incoming Webhooks** app to your workspace.
3. Create a new webhook for a specific channel.
4. Slack will give you a URL like:

   ```text
   https://hooks.slack.com/services/XXX/YYY/ZZZ
   ```

You can use this URL directly in a `webhook:` channel.

### 2.2. Discord (Webhook)

Discord servers support **webhooks** on a per-channel basis:

1. In your Discord server, go to **Server Settings → Integrations → Webhooks**.
2. Create a **New Webhook**, choose a target channel.
3. Copy the **Webhook URL**, which looks like:

   ```text
   https://discord.com/api/webhooks/1234567890/ABCDEF...
   ```

You can use this URL directly in a `webhook:` channel.

### 2.3. Zapier (Catch Hook)

Zapier’s **Webhooks by Zapier → Catch Hook** trigger works perfectly with AetherGraph’s webhook payload.

1. In Zapier, create a new **Zap**.

2. Set the **Trigger** to **“Webhooks by Zapier → Catch Hook”**.

3. Zapier gives you a URL like:

   ```text
   https://hooks.zapier.com/hooks/catch/123456/abcdef/
   ```

4. Use this URL in a `webhook:` channel.

5. In Zapier, map the incoming `text`/`content` fields to whatever action you like (Slack message, email, Notion page, etc.).

These three platforms cover a huge range of use cases. Anything that can accept an HTTP POST can likely be wired in the same way.

---

## 3. How to use the webhook channel

The webhook channel uses a simple key format:

```text
webhook:<WEBHOOK_URL>
```

Where `<WEBHOOK_URL>` is the full URL provided by Slack, Discord, Zapier, etc.

### 3.1. Example: Discord notification

Suppose Discord gives you this URL:

```text
https://discord.com/api/webhooks/1437303232475959398/UFD16h-JMadbKfTbigsTYTRQ7F_rcaAe2-4ZIpVP8tNGhJgbhTm_peQRWU0V86qi39Yx
```

You can send messages to that channel with:

```python
from aethergraph import graph_fn, NodeContext, run

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1437303232475959398/UFD16h-JMadbKfTbigsTYTRQ7F_rcaAe2-4ZIpVP8tNGhJgbhTm_peQRWU0V86qi39Yx"

@graph_fn(name="webhook_discord_demo")
async def webhook_discord_demo(*, context: NodeContext):
    channel_key = f"webhook:{DISCORD_WEBHOOK_URL}"
    chan = context.channel(channel_key)

    await chan.send_text("AetherGraph run finished 🎉")
    await chan.send_text("Model: demo-model-v1\nAccuracy: 0.93\nLoss: 0.12")

    return {"notified": True}
```

When this graph runs, the messages appear in your Discord channel via the webhook.

### 3.2. Example: Zapier Catch Hook

If Zapier gives you a URL like:

```text
https://hooks.zapier.com/hooks/catch/123456/abcdef/
```

You can send events to it with:

```python
ZAP_URL = "https://hooks.zapier.com/hooks/catch/123456/abcdef/"

@graph_fn(name="webhook_zapier_demo")
async def webhook_zapier_demo(*, context: NodeContext):
    chan = context.channel(f"webhook:{ZAP_URL}")

    await chan.send_text("AetherGraph just completed an experiment 🧪")
    await chan.send_text("You can map this 'text' field in Zapier to Slack, email, or Notion.")

    return {"notified": True}
```

In Zapier, you can then:

* Use the **Catch Hook** trigger to receive the JSON payload.
* Map the `text` or `content` field to downstream actions (Slack, Gmail, Notion, etc.).

### 3.3. Example: Slack Incoming Webhook

If Slack gives you a webhook URL like:

```text
https://hooks.slack.com/services/XXX/YYY/ZZZ
```

You can send notifications with:

```python
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"

@graph_fn(name="webhook_slack_demo")
async def webhook_slack_demo(*, context: NodeContext):
    chan = context.channel(f"webhook:{SLACK_WEBHOOK_URL}")

    await chan.send_text("AetherGraph run completed ✅")

    return {"notified": True}
```

Slack receives the JSON payload and posts the message into the configured channel.


You can also use this pattern with **other tools that provide incoming webhooks**, such as Microsoft Teams, Google Chat, Mattermost, Rocket.Chat, or Zulip. These aren’t officially tested yet in AetherGraph, but as long as you have a webhook URL and the service accepts JSON via HTTP POST, you can usually connect it either directly via `webhook:<URL>` or by running the payload through an intermediate tool like Zapier/Make to adapt the JSON shape.

---

## 4. Notes & best practices

* The webhook channel is **one-way**: it does not support `ask_*` or replies.
* It is ideal for **notifications, logging, and triggering external workflows**.
* You can safely combine it with other channels (console, Slack adapter, Telegram, file) in the same graph.
* Error handling is **best-effort**:

  * If the target URL returns a 4xx/5xx or times out, the adapter logs a warning but does not fail your graph.

As long as you have a webhook URL from an external service, you can plug it into `webhook:<URL>` and let AetherGraph deliver your messages there.
