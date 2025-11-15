# Webhook Channel Setup & Usage

The **webhook channel** lets AetherGraph send JSON payloads via **HTTP POST** to any service that accepts incoming webhooks (Slack Incoming Webhooks, Discord, Zapier, etc.).

✅ **No installation or configuration in AetherGraph** — just use a webhook URL.

🔔 **One‑way only:** webhooks push notifications **out**; they **cannot** receive replies or run `ask_*` prompts.

---

## When to Use

Use webhooks for:

* **Notifications** ("run finished", progress updates).
* **Logging / audit** into external systems.
* **Triggering automations** (Zapier, Make) without writing adapters.

---

## Key Format

```text
webhook:<WEBHOOK_URL>
```

Where `<WEBHOOK_URL>` is the full URL provided by your target service (Slack, Discord, Zapier, etc.).

---

## Minimal Payload (what we send)

```json
{
  "type": "agent.message",
  "channel": "webhook:<WEBHOOK_URL>",
  "text": "Run finished ✅",
  "content": "Run finished ✅",
  "meta": {},
  "timestamp": "..."
}
```

> Services that require a custom shape can be adapted via Zapier/Make or by transforming on the receiving side.

---

## Tested Targets (Examples)

### Slack – Incoming Webhook

1. Add **Incoming Webhooks** in Slack → create a webhook for a channel.
2. Copy the URL like `https://hooks.slack.com/services/XXX/YYY/ZZZ`.
3. Use it directly as `webhook:<URL>`.

```python
SLACK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"
chan = context.channel(f"webhook:{SLACK_URL}")
await chan.send_text("AetherGraph run completed ✅")
```

### Discord – Channel Webhook

1. Server Settings → Integrations → **Webhooks** → New Webhook → choose channel.
2. Copy URL like `https://discord.com/api/webhooks/123/ABC...`.
3. Use as `webhook:<URL>`.

```python
DISCORD_URL = "https://discord.com/api/webhooks/123/ABC..."
await context.channel(f"webhook:{DISCORD_URL}").send_text("Experiment done 🎉")
```

### Zapier – Catch Hook

1. Create a Zap → Trigger: **Webhooks by Zapier → Catch Hook**.
2. Copy the **Catch Hook** URL.
3. Use as `webhook:<URL>` and map `text`/`content` in Zapier.

```python
ZAP_URL = "https://hooks.zapier.com/hooks/catch/123456/abcdef/"
await context.channel(f"webhook:{ZAP_URL}").send_text("Model training completed 🧪")
```

> The same pattern usually works with Microsoft Teams, Google Chat, Mattermost, Rocket.Chat, Zulip, or any endpoint that accepts JSON POSTs.

---

## Usage Pattern (General)

```python
from aethergraph import graph_fn, NodeContext

WEBHOOK_URL = "https://example.com/incoming"

@graph_fn(name="webhook_demo")
async def webhook_demo(*, context: NodeContext):
    chan = context.channel(f"webhook:{WEBHOOK_URL}")
    await chan.send_text("Run finished ✅")
    await chan.send_text("Metrics: acc=0.93, loss=0.12")
    return {"notified": True}
```

---

## Notes & Best Practices

* **One‑way only**: no replies/continuations; combine with other channels for interactions.
* **Resilience**: if a webhook returns 4xx/5xx or times out, we log the error; your graph continues by default.
* **Security**: treat URLs as secrets; rotate if leaked. Consider using Zapier/Make as a buffer when adapting payload shapes.
* **Multiple endpoints**: you can create multiple webhook channels within the same graph run.
