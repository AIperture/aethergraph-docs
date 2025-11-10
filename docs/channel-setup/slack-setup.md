# Slack Integration Setup (Socket Mode)

This guide walks you through connecting Slack to AetherGraph using **Socket Mode**. This works great for local / individual use — no public URL or ngrok required.

We’ll do it in three steps:

1. Create and configure a Slack app using a manifest.
2. Configure AetherGraph via `.env`.
3. Choose a default Slack channel and `channel_key` (with optional aliases).

---

## 1. Create a Slack App (with manifest)

1. Go to **[https://api.slack.com/apps](https://api.slack.com/apps)** and click **“Create New App” → “From an app manifest”**.
2. Choose the workspace where you want to use AetherGraph.
3. Paste the following manifest (adjust the `display_information.name` if you like):

```yaml
_display_information:
  name: AetherGraph
features:
  bot_user:
    display_name: AetherGraph
    always_online: true
oauth_config:
  scopes:
    bot:
      - chat:write
      - chat:write.public
      - channels:history
      - groups:history
      - im:history
      - mpim:history
settings:
  interactivity:
    is_enabled: true
  event_subscriptions:
    bot_events:
      - message.channels
      - message.im
      - app_mention
```

> **Note:** When using Socket Mode, you **do not** need to configure an HTTP Request URL for Events or Interactivity.

4. Click **Create**.
5. Go to **OAuth & Permissions → Install App to Workspace** and complete the install.

### Enable Socket Mode and get tokens

1. In your Slack app, go to **Socket Mode** in the left sidebar.
2. Toggle **Enable Socket Mode** → **ON**.
3. Click **“Generate App-Level Token”**:

   * Name it something like `aethergraph-app-token`.
   * Grant it the **`connections:write`** scope.
   * Copy the resulting token (it starts with `xapp-…`).
4. Go to **OAuth & Permissions** and copy the **Bot User OAuth Token** (starts with `xoxb-…`).

You now have:

* **Bot token** (e.g. `xoxb-...`)
* **App token** (e.g. `xapp-...`)
* Optional: **Signing secret** (used later for webhook mode)

You can find the signing secret under **Basic Information → App Credentials → Signing Secret**.

---

## 2. Configure `.env` for AetherGraph

AetherGraph reads Slack settings from `AETHERGRAPH_SLACK__*` entries in your `.env`.

Add the following variables:

```env
# Turn Slack on
AETHERGRAPH_SLACK__ENABLED=true

# Tokens from Slack
AETHERGRAPH_SLACK__BOT_TOKEN=xoxb-your-bot-token-here
AETHERGRAPH_SLACK__APP_TOKEN=xapp-your-app-token-here

# Optional but recommended to set now (used for future webhook mode)
AETHERGRAPH_SLACK__SIGNING_SECRET=your-signing-secret-here

# Transport mode (recommended defaults for local / individual use)
AETHERGRAPH_SLACK__SOCKET_MODE_ENABLED=true
AETHERGRAPH_SLACK__WEBHOOK_ENABLED=false
```

With this configuration:

* The AetherGraph sidecar opens a **WebSocket connection to Slack** (Socket Mode).
* You **do not** need a public URL, ngrok, or any `/slack/events` endpoint.

Restart your AetherGraph sidecar after editing `.env` so the new settings take effect.

---

## 3. Choosing a default Slack channel and `channel_key`

AetherGraph uses a **channel key** to know where to send messages. For Slack, the canonical format is:

```text
slack:team/<TEAM_ID>:chan/<CHANNEL_ID>
```

You can set a default channel in two ways:

### 3.1. Using `DEFAULT_TEAM_ID` / `DEFAULT_CHANNEL_ID`

1. In Slack, find your **team (workspace) ID** and **channel ID**:

   * Team ID: often visible in the URL or via a quick Slack API call.
   * Channel ID: right-click a channel → *Copy link* and grab the `C...` part.
2. Add these to your `.env`:

```env
AETHERGRAPH_SLACK__DEFAULT_TEAM_ID=T0123456789
AETHERGRAPH_SLACK__DEFAULT_CHANNEL_ID=C0123456789
```

AetherGraph will then derive the canonical channel key:

```text
slack:team/T0123456789:chan/C0123456789
```

When you call:

```python
chan = context.channel()
await chan.send_text("Hello from AetherGraph 👋")
```

it will use this default Slack channel.

### 3.2. Using `DEFAULT_CHANNEL_KEY` directly

If you prefer, you can set the full key yourself:

```env
AETHERGRAPH_SLACK__DEFAULT_CHANNEL_KEY=slack:team/T0123456789:chan/C0123456789
```

This is the most explicit and is what AetherGraph uses internally.

---

## 4. Using channel keys for multiple Slack channels

The canonical Slack `channel_key` used by AetherGraph has the form:

```text
slack:team/<TEAM_ID>:chan/<CHANNEL_ID>
```

You can use this in two main ways:

1. **Set a default channel for most runs** (recommended)

   * Use `AETHERGRAPH_SLACK__DEFAULT_TEAM_ID` and `AETHERGRAPH_SLACK__DEFAULT_CHANNEL_ID` in your `.env`.
   * AetherGraph will derive the canonical key internally.
   * When you call `context.channel()` without arguments, it will use that default Slack channel.

2. **Select a channel explicitly in code**

   * If you have multiple Slack channels you want to talk to, you can always pass a `channel_key` directly:

   ```python
   chan = context.channel("slack:team/T0123456789:chan/C0123456789")
   await chan.send_text("Sending to this specific channel")
   ```

   This bypasses any default and sends to the channel you specify.

> **Note:** you don’t have to set a default Slack channel. If no default is configured, AetherGraph falls back to `console:stdin` for `context.channel()`; you can still target Slack explicitly by passing a full `channel_key` when you need it.

---

## 5. Quick test

Once everything is configured:

1. Ensure your `.env` has the Slack values and the sidecar is running.
2. Run a small test graph:

    ```python
    from aethergraph import graph_fn, NodeContext

    @graph_fn(name="hello_slack")
    async def hello_slack(*, context: NodeContext):
        chan = context.channel()  # uses default Slack channel
        await chan.send_text("Hello from AetherGraph 👋")
    ```

3. Execute this graph and confirm that the message appears in your chosen Slack channel.

If the message arrives, your Slack Socket Mode integration is working.

### Note: local-only pattern

This Socket Mode setup is intended for **local / personal use**: AetherGraph runs on your machine or a dev box, and connects out to Slack over a secure WebSocket. We do not support production webhook with the initial release.

Do **not** expose your local sidecar directly to the public internet!
