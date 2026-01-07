# Tutorial 3: Talk to Your Graph — Channels and Waits

This tutorial explains **how your graph talks back** — how agents communicate with the outside world and how different kinds of waits work under the hood. You’ll learn the difference between **cooperative waits** (for live, stateless agents) and **dual-stage waits** (for resumable workflows), and how to use each effectively.

> **Goal:** Understand how channels unify I/O, and why only `@graphify` with dual-stage waits can resume safely after a crash.

---

## 1. What Is a Channel?

A **channel** is your agent’s communication route — Slack, Telegram, Web UI, or Console. It lets your code send messages, request input, and stream updates through a consistent API.

```python
from aethergraph import graph_fn

@graph_fn(name="greet")
async def greet(*, context):
    ch = context.channel() 
    await ch.send_text("Starting demo…")
    name = await ch.ask_text("Your name?")    # cooperative wait
    await ch.send_text(f"Nice to meet you, {name}!")
    return {"user": name}
```

* The **`context.channel()`** method returns a `ChannelSession` helper with async methods like `send_text`, `ask_text`, `ask_approval`, `ask_files`, `stream`, and `progress`.
* If no channel is configured, it falls back to the console (`console:stdin`).

> 💡 Channel setup and adapter configuration (Slack, Telegram, Web) are covered in **Channel Setup**.

---

## 2. The Two Wait Models

AetherGraph supports two wait mechanisms — **cooperative** and **dual-stage** — both built on the continuation system but with very different lifecycles.

<img src="/assets/images/waits.png" alt="waits" width="600">

### Cooperative waits — via `context.channel()` methods

* Implemented by `ChannelSession` (`ask_text`, `ask_approval`, `ask_files`, etc.).
* Work *inside a running process* — the node suspends, then resumes when the reply arrives.
* These waits are **stateful** for inspection, but not resumable; if the process dies, the session is lost.
* Used mainly in **`@graph_fn`** agents, which execute immediately and stay alive.

### Dual-stage waits — via built-in channel tools

* Implemented as **@tool nodes** in `aethergraph.tools` (`ask_text`, `send_text`, etc.).
* Each wait becomes a **graph node** stored in the runtime snapshot.
* Can **pause indefinitely** and **resume** after restarts using `run_id` in `@graphify`.
* Used in **`@graphify`** graphs, which are strictly persisted and versioned.

> ⚠️ All built-in dual-stage methods are `@tool`s — do **not** call them inside another tool. They are meant for use in graphify or top-level graph_fn logic, not nested nodes.

---

## 3. Lifecycle and Persistence

| Concept            | `@graph_fn` + **Cooperative Waits**                                    | `@graphify` + Dual-Stage Waits                       |
| ------------------ | ---------------------------------------------- | ---------------------------------------------------- |
| Execution          | Runs immediately (reactive)                    | Builds DAG, runs with scheduler                      |
| State              | Stateful for in-process waits    | Snapshot persisted to disk or DB                     |
| Wait behavior      | Cooperative (in-process)                       | Dual-stage (resumable)                               |
| Resume after crash | ❌ Lost, consider saving progress in memory and sementic recovery                                        | ✅ Recoverable with `run_id`  and stable `node_id`; set up `_id` when building the graph                   |

> You can also use the `context.channel()` method in `@graphify` for convenience within a `@tool`, or use dual-stage wait tools in `graph_fn`. However, these approaches cannot guarantee resumption due to the stateful nature of the method or graph.
> **Caveat for console dual-stage tools:** Console input is handled differently, and dual-stage waits do not support resumption for console channels. However, it is rare for a local process using the console to terminate unexpectedly.

---

## 4. Cooperative Wait Example

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

## 5. Dual-Stage Wait Example (Resumable)

```python
from aethergraph import graphify
from aethergraph.tools import send_text, ask_text # built-in `@tool`. Do not use them in anohter `@tool`

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

## Key Takeaways

* `context.channel()` methods implement **cooperative waits** — great for live agents.
* Built-in channel tools (`ask_text`, `send_text`, etc.) implement **dual-stage waits** — required for resumable graphs.
* `graph_fn` is **stateless**, inspectable via `.last_graph` but not recoverable.
* `graphify` uses **snapshots** to persist progress and enable recovery with `run_id`.
* Dual-stage tools are `@tool` nodes — never call them *inside* another tool.

> Channels make your graph talk. Wait models decide *how long it remembers the conversation.*
