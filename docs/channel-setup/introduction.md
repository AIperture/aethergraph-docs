# Channels Overview

AetherGraph ships with multiple **channels** for delivering messages and (optionally) interacting with users or tools. This page gives you a compact map of what exists, when to use each, and what they can do.

> **Scope (OSS build):** Channels are designed for **personal, local, and small‑team** use. Treat them as convenient building blocks, not as a hardened, multi‑tenant messaging stack. For public or sensitive deployments, keep channels behind trusted networks and review security settings carefully.

---

## 1. Channel quick picks (when to use what)

* **Console (`console:`)** – Default. Local dev, quick demos, CLI‑style prompts. No setup.
* **Slack (`slack:`)** – Team chat, rich approvals, durable `ask_*` resumes. Requires Slack app.
* **Telegram (`tg:`)** – Mobile‑friendly prompts and notifications. Polling (local) or webhook (advanced). Experimental for `ask_*`.
* **File (`file:`)** – Write‑only logs/transcripts to disk under your workspace. Zero setup.
* **Webhook (`webhook:`)** – Write‑only JSON POST to any incoming webhook (Slack Incoming, Discord, Zapier, etc.). Zero setup in AetherGraph.

---

## 2. Capabilities at a glance

Legend: ✅ supported • 📝 forwarded/logged only • ✖️ not supported

| Channel  | Key prefix / example                   | Default | Text | Input / `ask_*`      | Buttons / approval | Image | File | Streaming/Edit | Inbound resume   |
| -------- | -------------------------------------- | ------- | ---- | -------------------- | ------------------ | ----- | ---- | -------------- | ---------------- |
| Console  | `console:stdin`                        | ✅       | ✅    | ✅ (inline via stdin) | ✅ (numbered)       | ✖️    | ✖️   | ✖️             | ✖️               |
| Slack    | `slack:team/T:chan/C[:thread/TS]`      | ✖️      | ✅    | ✅                    | ✅                  | ✅     | ✅    | ✅              | ✅                |
| Telegram | `tg:chat/<id>[:topic/<thread_id>]`     | ✖️      | ✅    | ✅ (experimental)     | ✅                  | ✅     | ✅    | ✅              | ✅ (experimental) |
| File     | `file:logs/experiment_01.txt`          | ✖️      | ✅    | ✖️                   | 📝                 | 📝    | 📝   | 📝             | N/A              |
| Webhook  | `webhook:https://hooks.zapier.com/...` | ✖️      | ✅    | ✖️                   | 📝                 | 📝    | 📝   | 📝             | N/A              |

**Notes**

* **Console** is simple and local; great for development but not built for durable, cross‑process resumes.
* **Slack/Telegram** provide two‑way chat; Telegram’s interaction support is still **experimental**.
* **File/Webhook** are **inform‑only**: push messages out, no replies.

---

## 3. `ask_*` vs inform‑only

**Interactive (`ask_*`)**

* Supported: **Console**, **Slack**, **Telegram**.
* In `@graphify`, Slack/Telegram create a **Continuation** and can **resume** even if your Python process restarts.
* Console reads inline from stdin; no durable, cross‑process resume.

**Inform‑only**

* **File** and **Webhook** only push out.
* Use them for notifications, logging, and triggering automations; do **not** call `ask_*` on these.

---

## 4. Concurrency & multi‑channel patterns

* You can send **multiple messages concurrently** on a channel.
* You can use **multiple channels in the same graph** (e.g., console debug + file log + Slack + webhook).

Example:

```python
async def run_with_notifications(context):
    await context.channel("console:stdin").send_text("Run started")
    await context.channel("file:runs/exp_01.log").send_text("Run started")
    await context.channel("slack:team/T:chan/C").send_text("Run started (Slack)")
    await context.channel("webhook:https://hooks.zapier.com/hooks/catch/.../").send_text("Run started (Webhook)")
```

---

## 5. Security tips (webhook & chat)

* **Treat webhook URLs as secrets**; rotate if leaked. Prefer **HTTPS**.
* For custom receivers, add a shared secret header (e.g., `X-AetherGraph-Secret`) and verify server‑side.
* Keep public exposure minimal; prefer trusted networks or intermediaries (Zapier/Make, your backend) when adapting payload shapes.
* Review bot/app permissions on Slack/Telegram—grant only what you need.

---

## 6. Key formats (cheat sheet)

* **Console:** `console:stdin`
* **Slack:** `slack:team/<TEAM_ID>:chan/<CHANNEL_ID>[:thread/<TS>]`
* **Telegram:** `tg:chat/<CHAT_ID>[:topic/<THREAD_ID>]`
* **File:** `file:<relative/path/inside/channel_files>`
* **Webhook:** `webhook:<FULL_WEBHOOK_URL>`

Use these keys directly with `context.channel(<key>)`, or set defaults/aliases as needed.
