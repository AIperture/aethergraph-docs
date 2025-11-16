# Slack Integration Setup (Socket Mode)

This guide shows you how to connect **Slack** to **AetherGraph** using **Socket Mode** — ideal for local or individual use.

✅ **No public URL or ngrok required**.

✅ **Runs securely via WebSocket**.

---

## Before You Start

1. Install AetherGraph with Slack extras:

   ```bash
   pip install "aethergraph[slack]"
   ```

2. Make sure you have a `.env` file in your project root. AetherGraph will read Slack configuration from it.

---

## 1. Create a Slack App (with Manifest JSON)

1. Go to **[https://api.slack.com/apps](https://api.slack.com/apps)** → click **“Create New App” → “From an app manifest.”**
2. Choose your workspace.
3. Paste the following JSON manifest (you can rename the app if you wish):

   ```json
    {
        "display_information": {
            "name": "AetherGraph"
        },
        "features": {
            "bot_user": {
                "display_name": "AetherGraph",
                "always_online": true
            }
        },
        "oauth_config": {
            "scopes": {
                "bot": [
                    "app_mentions:read",
                    "channels:history",
                    "chat:write",
                    "channels:manage",
                    "channels:read",
                    "files:read",
                    "files:write",
                    "groups:read",
                    "groups:history"
                ]
            }
        },
        "settings": {
            "event_subscriptions": {
                "bot_events": [
                    "app_mention",
                    "message.channels",
                    "message.groups"
                ]
            },
            "interactivity": {
                "is_enabled": true
            },
            "org_deploy_enabled": false,
            "socket_mode_enabled": true,
            "token_rotation_enabled": false
        }
    }
   ```

> **Note:** For Socket Mode, you do **not** need to configure an HTTP Request URL for events or interactivity.

4. Click **Create App**.
5. Go to **OAuth & Permissions → Install App to Workspace** and complete installation.

---

## 2. Enable Socket Mode and Get Tokens

1. In your app’s left sidebar, go to **Socket Mode**.
2. Toggle **Enable Socket Mode → ON.**
3. Click **“Generate App-Level Token”**:

   * Name it something like `aethergraph-app-token`.
   * Grant it the **`connections:write`** scope.
   * Copy the token (starts with `xapp-...`).
4. Go to **OAuth & Permissions**, install the app to Slack, and copy the **Bot User OAuth Token** (starts with `xoxb-...`).

You now have:

* **Bot token** (`xoxb-…`)
* **App token** (`xapp-…`)
* *(Optional)* **Signing secret** — found under *Basic Information → App Credentials → Signing Secret*

---

## 3. Configure `.env` for AetherGraph

AetherGraph reads Slack settings from your environment variables.

Add the following lines to your `.env`:

```env
# Slack (optional)
AETHERGRAPH_SLACK__ENABLED=true             # must be true to enable
AETHERGRAPH_SLACK__BOT_TOKEN=xoxb-your-bot-token-here
AETHERGRAPH_SLACK__APP_TOKEN=xapp-your-app-token-here
AETHERGRAPH_SLACK__SIGNING_SECRET=your-signing-secret-here
AETHERGRAPH_SLACK__SOCKET_MODE_ENABLED=true  # usually true for local testing
AETHERGRAPH_SLACK__WEBHOOK_ENABLED=false     # usually false for local testing
```

After saving `.env`, restart your AetherGraph sidecar so the new settings take effect.

With this setup:

* AetherGraph connects to Slack via WebSocket (Socket Mode).
* You **don’t** need ngrok or a public URL.

---

## 4. Setting Up Slack Channels and Aliases

Once Slack is enabled, you can define which channel AetherGraph should talk to.

Here’s a typical setup pattern:

```python
import os
from aethergraph.channels import set_default_channel, set_channel_alias

SLACK_TEAM_ID = os.getenv("SLACK_TEAM_ID", "your-slack-team-id")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "your-slack-channel-id")
slack_channel_key = f"slack:team/{SLACK_TEAM_ID}:chan/{SLACK_CHANNEL_ID}"  # Slack channel key format

# Set as the default channel
set_default_channel(slack_channel_key)

# Optional: define an alias
set_channel_alias("my_slack", slack_channel_key)
```

Usage examples:

```python
chan = context.channel()  # uses the default Slack channel
await chan.send_text("Hello from AetherGraph 👋")

chan2 = context.channel("my_slack")  # use a named alias
await chan2.send_text("Message to my_slack alias")

# or directly specify the channel
await context.channel().send_text("Custom target", channel=slack_channel_key)
```

If nothing is set up, AetherGraph automatically falls back to `console:stdin`.


**Finding your Team & Channel IDs**

* **Channel ID**: Open Slack in a browser → navigate to the channel → copy the `C…` (public) or `G…` (private) part from the URL.
* **Team ID**: In the same URL, copy the `T…` segment (your workspace ID).

---

## 5. Quick Test

Once everything is configured, test your integration:

**Invite the bot to your channel**

* Private channels require the bot to be a member before it can post. Invite it via Add people or mention `@YourBot` and select Invite to channel.

* For DMs, post to the DM channel ID (`D…`), not a user ID.

Run the graph — if your message appears in Slack, you’re all set!

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="hello_slack")
async def hello_slack(*, context: NodeContext):
    chan = context.channel()
    await chan.send_text("Hello from AetherGraph 👋")
    return {"ok": True}
```


---

### Notes

* This Socket Mode setup is **for local / individual use only**.
* Do **not** expose your sidecar server directly to the internet.
* Future versions will include webhook-based production integrations.
