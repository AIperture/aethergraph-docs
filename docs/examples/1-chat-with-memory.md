# Example: First Steps with Memory, Channel, LLM & Artifacts

> **Who is this for?** Folks who have never used AetherGraph (AG). We’ll build a tiny chat agent that **remembers** what was said, **responds** using an LLM, and **saves** a session summary — all step‑by‑step.

---

## What you’ll build

A stateful chat agent that:

1. **Stores** each message as a `chat_turn` **event** in AG Memory.
2. **Reads** prior events on startup to preload context.
3. **Chats** with you via `context.channel()` (console/Slack/Web supported).
4. **Uses** `context.llm()` to reply and later **summarize** the session.
5. **Saves** the transcript + summary as an **artifact** (a file you can inspect).

This mirrors real apps: assistants, experiment logs, ops runbooks, or optimization loops that need persistent context.

---

## Prerequisites (2 minutes)

* **Python 3.10+**
* **Install AG** (adjust to your package source):

  ```bash
  pip install aethergraph
  ```
* **LLM key** (e.g., OpenAI) in your environment or `.env`:

  ```bash
  export OPENAI_API_KEY=sk-...
  ```
* **(Optional) Slack/Web UI:** Not required for this tutorial; we use the console channel. You can switch to Slack/Web later without changing the agent code.

---

## Glossary (AG in 60 seconds)

* **`@graph_fn`**: A Python function that AG can schedule/run (think: a task node with helpful runtime wiring).
* **`NodeContext`**: Passed into your `@graph_fn`; gives you **services**:

  * `context.memory()` – record & query **events** (structured log).
  * `context.channel()` – input/output with the user (console/Slack/Web).
  * `context.llm()` – talk to an LLM provider using a unified API.
  * `context.artifacts()` – save/load files, JSON, blobs.
* **Events (Memory)**: Append‑only records with fields like `kind`, `text`, `metrics`, `tags`, `stage`, `severity`. You choose the schema; AG stores and fetches them for you.

> Key idea: keep your logic in **plain Python**; treat services (memory, channel, llm, artifacts) as pluggable I/O.

---

## Step 0 — Minimal run harness

We’ll run two functions in one process: one to **seed** memory, one to **chat**.

```python
# run_harness.py
if __name__ == "__main__":
    import asyncio
    from aethergraph.runner import run_async
    from aethergraph import start_server

    # Start the sidecar: enables interactive I/O and resumable waits
    url = start_server(port=8000, log_level="warning")
    print("Sidecar:", url)

    async def main():
        # Same run_id so they share the same memory namespace
        await run_async(seed_chat_memory_demo, inputs={}, run_id="demo_chat_with_memory")
        result = await run_async(chat_agent_with_memory, inputs={}, run_id="demo_chat_with_memory")
        print("Result:", result)

    asyncio.run(main())
```

> **Why a sidecar?** For console/Slack/Web prompts (`ask_*`) AG uses event‑driven waits that the sidecar hosts. Pure compute graphs can run without it.

---

## Step 1 — Seed memory (why & how)

**Why:** Many real agents need past context on first run (previous chats, last experiment settings, etc.). We’ll **preload** two `chat_turn` events so the agent “remembers” something before you type.

```python
# seed.py
from aethergraph import graph_fn, NodeContext

@graph_fn(name="seed_chat_memory_demo")
async def seed_chat_memory_demo(*, context: NodeContext):
    mem = context.memory()
    logger = context.logger()

    # Each record() call writes an Event. `data` is JSON‑encoded into Event.text.
    await mem.record(
        kind="chat_turn",
        data={"role": "user", "text": "We talked about integrating AetherGraph into my project."},
        tags=["chat", "user", "seed"], severity=2, stage="observe",
    )
    await mem.record(
        kind="chat_turn",
        data={"role": "assistant", "text": "Start with a simple graph_fn and add services later."},
        tags=["chat", "assistant", "seed"], severity=2, stage="act",
    )

    logger.info("Seeded two chat turns.")
    return {"seeded": True}
```

> **Design tip:** Use `kind` consistently (`"chat_turn"`) so you can query exactly what you need later. `tags`, `stage`, and `severity` help with reporting and filtering.

---

## Step 2 — Load prior events (make memory useful)

**Goal:** On startup, fetch recent `chat_turn` events, decode them, and **prime** the chat history.

```python
# load_history.py (excerpt inside the agent)
previous_turns = await mem.recent_data(kinds=["chat_turn"], limit=50)
conversation = []
for d in previous_turns:
    if isinstance(d, dict) and d.get("role") in ("user", "assistant") and d.get("text"):
        conversation.append({"role": d["role"], "text": d["text"]})

if conversation:
    await chan.send_text(f"🧠 I loaded {len(conversation)} prior turns. I’ll use them as context.")
else:
    await chan.send_text("👋 New session. I’ll remember as we go.")
```

> **Why not read raw events?** `recent_data()` returns the **decoded** JSON payloads you originally wrote via `data=...`. It’s the fastest way to get back to your domain objects.

---

## Step 3 — Talk to the user (Channel 101)

**Goal:** Use `channel.ask_text()` to get input and `channel.send_text()` to reply. This works the same in console, Slack, or a web adapter.

```python
# channel_loop.py (excerpt inside the agent)
while True:
    user = await chan.ask_text("You:")
    if not user:
        continue
    if user.strip().lower() in ("quit", "exit"):
        await chan.send_text("👋 Ending. Let me summarize...")
        break

    # Store the user turn in memory *and* in our local transcript
    conversation.append({"role": "user", "text": user})
    await mem.record(kind="chat_turn", data={"role": "user", "text": user},
                     tags=["chat", "user"], severity=2, stage="observe")
```

> **Why Channel?** It abstracts the transport. Your agent code stays the same whether you test locally or ship to Slack/Web.

---

## Step 4 — Call the LLM (compact history)

**Goal:** Build a small window from the transcript (e.g., last 10 turns) and call `llm.chat()`.

```python
# llm_reply.py (excerpt inside the agent)
history_tail = conversation[-10:]
messages = ([{"role": "system", "content": "You are a helpful, concise assistant."}] +
            [{"role": t["role"], "content": t["text"]} for t in history_tail])

reply, _usage = await llm.chat(messages=messages)
conversation.append({"role": "assistant", "text": reply})
await mem.record(kind="chat_turn", data={"role": "assistant", "text": reply},
                 tags=["chat", "assistant"], severity=2, stage="act")
await chan.send_text(reply)
```

> **Why only last 10 turns?** Keep prompts cheap. Memory retains *all* history; your prompt includes a **smart slice**.

---

## Step 5 — Summarize & Save (Artifacts)

**Goal:** Generate a session summary, then persist both transcript and summary for later inspection.

```python
# summarize_and_save.py (excerpt inside the agent)
hist_text = "
".join(f"{t['role']}: {t['text']}" for t in conversation[-20:])
summary_text, _ = await llm.chat(messages=[
    {"role": "system", "content": "You write clear, concise summaries."},
    {"role": "user", "content": "Summarize the conversation, focusing on main topics and TODOs.

" + hist_text},
])
await chan.send_text("📌 Session summary:
" + summary_text)

payload = {"conversation": conversation, "summary": summary_text}
try:
    saved = await artifacts.save_json(payload, suggested_uri="./chat_session_with_memory.json")
except Exception:
    saved = None
```

> **Artifacts** act like a project filesystem managed by AG. Save JSON, images, binaries — and load them from other runs.

---

## Step 6 — Put it together: the agent

Below is the **full** `@graph_fn` combining Steps 2–5. (Utility imports omitted for brevity.)

```python
from typing import Any, Dict, List
from aethergraph import graph_fn, NodeContext

@graph_fn(name="chat_agent_with_memory")
async def chat_agent_with_memory(*, context: NodeContext):
    logger = context.logger()
    chan = context.channel()
    mem = context.memory()
    artifacts = context.artifacts()
    llm = context.llm()

    conversation: List[Dict[str, Any]] = []

    # Load prior history
    try:
        previous_turns = await mem.recent_data(kinds=["chat_turn"], limit=50)
    except Exception:
        previous_turns = []
    for d in previous_turns:
        if isinstance(d, dict) and d.get("role") in ("user", "assistant") and d.get("text"):
            conversation.append({"role": d["role"], "text": d["text"]})

    await chan.send_text(
        f"🧠 I loaded {len(conversation)} prior turns. Type 'quit' to end."
        if conversation else "👋 New session. Type 'quit' to end."
    )

    # Chat loop
    while True:
        user = await chan.ask_text("You:")
        if not user:
            continue
        if user.strip().lower() in ("quit", "exit"):
            await chan.send_text("👋 Ending. Let me summarize...")
            break

        conversation.append({"role": "user", "text": user})
        await mem.record(kind="chat_turn", data={"role": "user", "text": user},
                         tags=["chat", "user"], severity=2, stage="observe")

        history_tail = conversation[-10:]
        messages = ([{"role": "system", "content": "You are a helpful, concise assistant."}] +
                    [{"role": t["role"], "content": t["text"]} for t in history_tail])
        reply, _ = await llm.chat(messages=messages)

        conversation.append({"role": "assistant", "text": reply})
        await mem.record(kind="chat_turn", data={"role": "assistant", "text": reply},
                         tags=["chat", "assistant"], severity=2, stage="act")
        await chan.send_text(reply)

    # Summarize & save
    hist_text = "
".join(f"{t['role']}: {t['text']}" for t in conversation[-20:])
    summary_text, _ = await llm.chat(messages=[
        {"role": "system", "content": "You write clear, concise summaries."},
        {"role": "user", "content": "Summarize the conversation with decisions/TODOs.

" + hist_text},
    ])
    await chan.send_text("📌 Session summary:
" + summary_text)

    try:
        await artifacts.save_json({"conversation": conversation, "summary": summary_text},
                                  suggested_uri="./chat_session_with_memory.json")
    except Exception:
        pass

    return {"turns": len(conversation), "summary": summary_text}
```

---

## Step 7 — Run it

From your shell:

```bash
python run_harness.py
```

You’ll see the sidecar URL and then a prompt:

```
You: hello
... assistant replies ...
You: quit
```

A `chat_session_with_memory.json` artifact will be saved. Rerun — the agent will preload what was said last time.

---

## Variations & next steps

* **Filter by time/kind/tags:** `recent_data(kinds=[...], limit=..., since=...)`.
* **Track metrics:** add `metrics={...}` to `record()` and chart them later.
* **Multiple channels:** same agent works with Slack/Web by switching adapters.
* **Long‑term summaries:** store occasional `kind="session_summary"` events.
* **Privacy/retention:** implement deletion or redaction policies per `tags` or `stage`.

---

## Troubleshooting

* **No replies?** Check your LLM key and provider quota.
* **Ask/answer stuck?** Ensure the sidecar started (see console log for URL).
* **Artifact not saved?** Verify write permissions in the working directory.

---

## Summary & Full Example Link

You built a **stateful chat agent** without any AG prior knowledge: you logged **events**, recalled them, chatted via **Channel**, used **LLM** to reply/summarize, and persisted results with **Artifacts**.

**Full example in repo:** *TBD (link placeholder)*
