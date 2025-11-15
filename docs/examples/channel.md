# Channels – Practical Usage Cheatsheet

This page is a **lightweight guide**, not a full API reference. It shows how to use channels in everyday graphs and what the most common operations look like.

---

## 1. Getting a channel

In any graph, you start from the `NodeContext`:

```python
chan = context.channel()                # default channel (often console or a default chat)
chan_slack = context.channel("slack:team/T:chan/C")
chan_file  = context.channel("file:runs/demo.log")
```

Use cases:

* **No argument** → send to whatever default channel you configured.
* **Explicit key** → target a specific channel (Slack, Telegram, file, webhook, etc.).

You then call convenient methods on `chan`.

---

## 2. Sending messages (`send_text`)

```python
await chan.send_text("Run started 🚀")
```

When to use:

* Any time you want to **tell the user something**:

  * status updates ("loading data…"),
  * final results ("accuracy = 0.93"),
  * errors, tips, or links.

Where it goes depends on the channel:

* **console** → prints to the terminal.
* **Slack / Telegram** → sends a chat message.
* **file** → appends a line to a log file.
* **webhook** → POSTs JSON to the external URL.

You usually don’t need to worry about the return value; it’s handled internally.

---

## 3. Asking for input (`ask_text`)

```python
name = await context.channel().ask_text("What is your name?")
await context.channel().send_text(f"Nice to meet you, {name}!")
```

When to use:

* You need **free-form input** from a human:

  * names, descriptions, small pieces of text,
  * short commands ("yes/no", "option A", etc.).

Supported channels:

* **console** → reads from stdin inline.
* **Slack / Telegram** → sends a prompt and waits for a reply.

Not supported / not meaningful on:

* **file** and **webhook** (those are inform-only channels).

Behind the scenes, Slack/Telegram use **continuations**, so the run can be resumed when a reply arrives.

---

## 4. Approvals & choices (`ask_approval`)

```python
res = await context.channel().ask_approval(
    "Deploy the model to production?",
    options=["Approve", "Reject"],
)

if res["approved"]:
    await context.channel().send_text("Deployment approved ✅")
else:
    await context.channel().send_text("Deployment cancelled ❌")
```

When to use:

* You want a **simple decision** from the user:

  * approve/reject,
  * pick from a short list of options.

Channel behavior:

* **console** → shows numbered options and waits for a number/label.
* **Slack / Telegram** → renders real buttons; user clicks, continuation resumes.

Again, this is not meant for file/webhook channels.

---

## 5. Files & uploads (high level)

For interactive channels (Slack, Telegram, console) and some tools, you’ll often work with **files** directly, not just links.

Typical high-level patterns:

### 5.1. Sending a file (`send_file`)

```python
# e.g. you just generated a local report
report_path = "./outputs/report.pdf"

chan = context.channel()  # default chat (Slack/Telegram/console)
await chan.send_file(report_path, caption="Here is your report 📎")
```

When to use:

* You want the user to **receive the actual file** in their chat or UI.
* Slack/Telegram will show the file as an attachment; console/file/webhook channels may log or reference it instead, depending on implementation.

### 5.2. Asking the user to upload a file (`ask_file`)

```python
files = await context.channel().ask_file("Please upload a CSV file with your data.")

# `files` is typically a list of file references with
# fields like name, uri, mimetype, etc.
for f in files:
    await context.channel().send_text(f"Got file: {f['name']}")
```

When to use:

* You need the user to **provide input as a file** (datasets, configs, documents).
* Works best on Slack/Telegram or a web UI that supports uploads.

### 5.3. Sending buttons for links

Buttons are a convenient way to surface links (e.g. to artifacts, dashboards) instead of pasting raw URLs.

Conceptually, you can build a message with one or more buttons that open URLs:

```python
from aethergraph.contracts.services.channel import Button

report_url = "https://example.com/artifacts/runs/123/report.pdf"

buttons = {
    "open_report": Button(label="Open report", url=report_url),
}

chan = context.channel()
await chan.send_buttons("Your report is ready:", buttons=buttons)
```

On rich channels (Slack/Telegram/web UI) this can render as clickable buttons; on simpler channels, it may fall back to plain text.

Use file and button helpers when you want the user to **act on artifacts directly** (download, open, inspect) rather than just reading text.

---

## 6. Streaming & progress (high level)

Some adapters (Slack, Telegram, web UI) support **streaming** and **progress** updates, so the user sees things evolve in place instead of a single final message.

A common pattern is to use a progress helper that periodically updates a status message while your work runs:

```python
@graph_fn(name="train_with_progress")
async def train_with_progress(*, context: NodeContext):
    await context.channel().send_text("Training started ⏳")

    total_steps = 5
    for step in range(1, total_steps + 1):
        # Do some work here...
        await context.channel().send_text(f"Progress: {step}/{total_steps}")

    await context.channel().send_text("Training finished ✅")
```

On rich channels (Slack/Telegram/web UI), the framework can render more advanced streaming or progress UIs using specialized helpers; the core idea is the same: **send updates frequently** so the user sees the task moving forward.

---

## 7. Putting it together – a small example

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="simple_run")
async def simple_run(*, context: NodeContext):
    # 1) Notify in the default channel
    await context.channel().send_text("Run started 🚀")

    # 2) Ask the user a question (console/Slack/Telegram)
    name = await context.channel().ask_text("What should we name this experiment?")

    # 3) Log the name to a file channel
    await context.channel("file:runs/experiment_names.log").send_text(name)

    # 4) Optionally notify an external system via webhook
    # await context.channel("webhook:https://hooks.zapier.com/hooks/catch/.../").send_text(
    #     f"New experiment: {name}"
    # )

    await context.channel().send_text(f"All set, {name} ✅")
    return {"experiment_name": name}
```

Use this cheatsheet as a **mental model** for channels:

* `channel()` → pick where messages go.
* `send_text` → tell the user or an external system something.
* `ask_*` → only on interactive channels (console/Slack/Telegram), when you need input.
* Let higher-level tooling take care of files and streaming; the channel adapters handle the transport details.
