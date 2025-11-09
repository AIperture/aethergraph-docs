# Tutorial 3: Talk to Your Graph — Channels and Waits

This tutorial explains **how your graph talks back** — how agents communicate with the outside world and how different kinds of waits work under the hood. You’ll learn the difference between **cooperative waits** (for live, stateless agents) and **dual-stage waits** (for resumable workflows), and how to use each effectively.

> **Goal:** Understand how channels unify I/O, and why only `@graphify` with dual-stage waits can resume safely after a crash.

---

## 1) What Is a Channel?

A **channel** is your agent’s communication route — Slack, Telegram, Web UI, or Console. It lets your code send messages, request input, and stream updates through a consistent API.

```python
from aethergraph import graph_fn

@graph_fn(name="greet")
async def greet(*, context):
    ch = context.channel("slack:#research")   # pick a target channel
    await ch.send_text("Starting demo…")
    name = await ch.ask_text("Your name?")    # cooperative wait
    await ch.send_text(f"Nice to meet you, {name}!")
    return {"user": name}
```

* The **`context.channel()`** method returns a `ChannelSession` helper with async methods like `send_text`, `ask_text`, `ask_approval`, `ask_files`, `stream`, and `progress`.
* If no channel is configured, it falls back to the console (`console:stdin`).

> 💡 Channel setup and adapter configuration (Slack, Telegram, Web) are covered in **Adapters & Setup**.

---

## 2) The Two Wait Models

AetherGraph supports two wait mechanisms — **cooperative** and **dual-stage** — both built on the continuation system but with very different lifecycles.

### Cooperative waits — via `context.channel()` methods

* Implemented by `ChannelSession` (`ask_text`, `ask_approval`, `ask_files`, etc.).
* Work *inside a running process* — the node suspends, then resumes when the reply arrives.
* These waits are **stateless beyond memory**; if the process dies, the session is lost.
* Used mainly in **`@graph_fn`** agents, which execute immediately and stay alive.

### Dual-stage waits — via built-in channel tools

* Implemented as **@tool nodes** in `aethergraph.builtins.toolset` (`ask_text`, `send_text`, etc.).
* Each wait becomes a **graph node** stored in the runtime snapshot.
* Can **pause indefinitely** and **resume** after restarts using `run_id`.
* Used in **`@graphify`** graphs, which are strictly persisted and versioned.

> ⚠️ All built-in dual-stage methods are `@tool`s — do **not** call them inside another tool. They are meant for use in graphify or top-level graph_fn logic, not nested nodes.

---

## 3) Lifecycle and Persistence

| Concept            | `@graph_fn`                                    | `@graphify` + Dual-Stage Waits                       |
| ------------------ | ---------------------------------------------- | ---------------------------------------------------- |
| Execution          | Runs immediately (reactive)                    | Builds DAG, runs with scheduler                      |
| State              | Stateless during execution (in-memory only)    | Snapshot persisted to disk or DB                     |
| Inspection         | Use `.last_graph()` to see implicit tool nodes | Graph spec is explicit and inspectable via `.spec()` |
| Wait behavior      | Cooperative (in-process)                       | Dual-stage (resumable)                               |
| Resume after crash | ❌ Lost                                         | ✅ Recoverable with `run_id`                          |

**In short:**

* `graph_fn` is *stateless* and great for live agents or notebooks.
* `graphify` is *stateful*, recording every node and state transition.
* Only **dual-stage waits** persist the wait state and allow resumption.

---

## 4) Cooperative Wait Example

```python
from aethergraph import graph_fn

@graph_fn(name="cooperative_wait")
async def cooperative_wait(*, context):
    ch = context.channel()
    await ch.send_text("Processing...")
    ans = await ch.ask_approval("Continue?", options=["Yes", "No"])
    if ans["approved"]:
        await ch.send_text("✅ Proceeding.")
    else:
        await ch.send_text("❌ Stopped.")
    return {"ok": ans["approved"]}
```

* Perfect for short-lived interactive runs.
* Not resumable if interrupted; all state is lost when the process exits.
* Consider saving states to memory for sementic recovery for non-critical tasks.

---

## 5) Dual-Stage Wait Example (Resumable)

```python
from aethergraph import graphify
from aethergraph.builtins.toolset import send_text, ask_text

@graphify(name="dual_stage_greet", inputs=["channel"], outputs=["greeting"])
def dual_stage_greet(channel: str):
    a = send_text(text="Hello!", channel=channel, _id="start")
    b = ask_text(prompt="What's your name?", channel=channel, _after=a, _id="wait_name")
    c = send_text(text=f"Hi {b.text}!", channel=channel, _after=b, _id="reply")
    return {"greeting": c.text}
```

* Each step is a **tool node** with a unique `_id`.
* If the process stops after `ask_text`, simply rerun with the same `run_id` to resume.
* The system restores from the last persisted snapshot.

---

## 6) Visual Comparison

```
COOPERATIVE (graph_fn + context.channel())
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ send_text() │→│ ask_text()   │→│ continue...  │
└─────────────┘  └──────────────┘  └──────────────┘
(process alive, ephemeral)

DUAL-STAGE (graphify + builtin tools)
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ send_text@ │→│ ask_text@    │→│ resume later │
└─────────────┘  └──────────────┘  └──────────────┘
(persisted nodes, resumable)
```

---

## 7) When to Use Which

| Scenario                      | Recommended Wait | Why                             |
| ----------------------------- | ---------------- | ------------------------------- |
| Quick console interaction     | Cooperative      | Simple, stateless, no setup     |
| Slack/Web chat that may pause | Dual-stage       | Safe to resume after restart    |
| Human approval pipeline       | Dual-stage       | Supports indefinite waiting     |
| Notebook prototype            | Cooperative      | Lightweight, immediate feedback |

---

## 8) Key Takeaways

* `context.channel()` methods implement **cooperative waits** — great for live agents.
* Built-in channel tools (`ask_text`, `send_text`, etc.) implement **dual-stage waits** — required for resumable graphs.
* `graph_fn` is **stateless**, inspectable via `.last_graph()` but not recoverable.
* `graphify` uses **snapshots** to persist progress and enable recovery with `run_id`.
* Dual-stage tools are `@tool` nodes — never call them *inside* another tool.

> Channels make your graph talk. Wait models decide *how long it remembers the conversation.*
