# Event‑Driven Waits: Cooperative vs Dual‑Stage

AetherGraph agents are **event‑driven**: they can pause mid‑flow and safely **resume** when a reply, upload, or callback arrives. There are two complementary wait modes, and you can use them flexibly in both `@graph_fn` and `@graphify`‑built graphs.

* **Cooperative waits** — via `context.channel().ask_*`. Simplest way to prompt + wait in reactive agents.
* **Dual‑stage waits** — via `@tool` nodes that split into **Stage A (prompt/setup)** and **Stage B (resume/produce)**. Best for static graphs and reliable orchestration.

> **Flexibility:** `context.*` methods are available **inside `@tool` nodes** (therefore inside `@graphify`). Dual‑stage tools can also be **`await`‑ed directly inside `@graph_fn`**. In either case, they form a node and persist a continuation.

---

## 1 Cooperative Waits (Channel‑first)

**What:** `context.channel().ask_text / ask_approval / ask_files` send a prompt and **yield** until a reply or timeout. The runtime persists a **continuation token** so the run can resume after restarts.

**Where:** Primarily inside `@graph_fn`. Can also be called from within a `@tool` if you want cooperative logic inside a node.

**Example**

```python
from aethergraph import graph_fn

@graph_fn(name="cooperative_demo", outputs=["msg"]) 
async def cooperative_demo(*, context):
    name = await context.channel().ask_text("Your name?")
    await context.channel().send_text(f"Hi, {name}!")
    return {"msg": f"greeted:{name}"}
```

**Properties**

* Minimal code, great for exploratory, chat‑style agents.
* Thread/channel‑aware correlation.
* Durable continuations; survives restarts.

---

## 2 Dual‑Stage Waits (Tool‑first)

**What:** A node splits into two stages: **A** emits the prompt/sets up state, **B** resumes once the event arrives and produces outputs. Maps cleanly to static DAGs and lets the **global scheduler** manage resumptions and retries.

**Use in both places:**

* **In `@graphify`** as standard tool nodes.
* **In `@graph_fn`** with `await` for immediate use — they still become nodes under the hood.

**Built‑in channel tools**

```python
# Use these in either style:
from aethergraph.tools import ask_text, ask_approval, ask_files

# A) Inside a static graph
from aethergraph import graphify

@graphify(name="collect_input", inputs=[], outputs=["greeting"]) 
def collect_input():
    name = ask_text(prompt="Your name?")      # node yields → resumes on reply
    return {"greeting": name.text}

# B) Await directly in a graph_fn
from aethergraph import graph_fn

@graph_fn(name="dualstage_in_fn", outputs=["choice"]) 
async def dualstage_in_fn(*, context):
    res = await ask_approval(prompt="Proceed?", options=("Yes","No"))
    return {"choice": res["choice"]}
```

**Properties**

* Node‑level persistence, retries, and metrics.
* Works seamlessly with **global scheduling** (centralized control, resumptions at scale).
* Great for UI + pipeline hybrids (prompt in Stage A, compute in Stage B).

---

## 3 Using `context.*` inside `@graphify`

`context` methods (channels, memory, artifacts, kv, logger, etc.) are available **inside `@tool` nodes**. This means your static graphs can still interact, log, and persist during node execution while retaining DAG inspectability.

```python
from aethergraph import tool

@tool(outputs=["ok"]) 
async def notify_and_tag(*, context):
    await context.channel().send_text("Started node…")
    await context.memory().record(kind="status", data={"stage":"start"})
    return {"ok": True}
```

---

## 4 Comparison: Cooperative vs Dual‑Stage vs Manual Checkpoints


| **Aspect**              | **Cooperative (`context.channel().ask_*`)**                | **Dual-Stage (`@tool` ask_*)**                                | **Manual checkpoints**               |
| ----------------------- | ---------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------ |
| **Authoring style**     | Inline, minimal                                            | Explicit node with A/B stages                                 | N/A in AG (not built-in)             |
| **Resumability**        | Hard — stateless unless save the state to memory manually          | **Native continuations** per node (resumeable after restart)  | Possible but manual/fragile          |
| **Retry / Idempotency** | Coarse (re-invoke the whole function)                      | Fine (node-level retry, idempotent resumes)                   | Manual                               |
| **Scale**               | Great for interactive sessions, small graphs               | **Excellent for large runs / thousands of waits**             | Limited by implementation            |
| **CPU load (waiting)**  | Keeps process / event loop alive; lightweight but not zero | **Zero CPU** — node is dormant until resumed                  | Depends on checkpointing backend     |
| **Memory footprint**    | Held in local task heap (light)                            | **Released after serialization**; only metadata retained      | Depends on snapshot granularity      |
| **Disk usage**          | Optional if memory writes used                             | **Tiny (~1–10 KB per node)** — correlator + inputs serialized | Potentially heavy (full state dump)  |
| **Latency to resume**   | Instant within current process                             | Slightly higher (resume event → lookup → dispatch)            | Potentially high (manual restore)    |


**Why Dual‑Stage scales**

* **Node‑granular control:** retries, backoff, and resumption are local to the waiting node.
* **Central orchestration:** the global scheduler can queue, shard, or migrate blocked nodes.
* **Observability:** each wait is a first‑class node with metrics and logs.
* **Determinism:** Stage boundaries clarify side‑effects and make runs reproducible.

> *Manual checkpoints* (framework‑agnostic snapshots) aren’t part of AetherGraph. Dual‑stage nodes cover the same reliability space with less boilerplate and better provenance.


---

## 5 Extending Dual‑Stage Tools

You can author custom dual‑stage nodes with **`DualStageTool`** to model your own A/B waits (e.g., submit job → wait → collect). Some examples of the usage include 

- custom channel waits
- submit/run long simualtion on the cloud
- data/model training pipeline on external systems
- external API Polling that reports a compleltion asynchronously

A compact public API for this is planned; detailed docs will ship soon.

---

## 6 Takeaways

* All `context.channel().ask_*` calls are **cooperative waits** by default.
* **Dual‑stage** tools work in both `@graphify` **and** `@graph_fn` (awaitable) and always materialize as nodes.
* For large, reliable systems: prefer **dual‑stage** for node‑level retries, metrics, and scheduler control.
* `context.*` is available inside `@tool` nodes, so static graphs can still interact, log, and persist cleanly.
* Manual checkpointing isn’t needed; dual‑stage nodes give better reliability with less boilerplate.
