# Design Your Own Waits & Adapters (Coming Soon)

This chapter is a **roadmap** for a feature that’s not public yet: defining your own **dual‑stage waits** and **adapters** so external systems can safely pause and resume graphs.

You can treat this as a design note: it explains *what* is coming and *how to think about it*, without locking you into any final API.

---

## 1. Why Custom Waits?

Today you’ve seen two wait styles:

* **Cooperative waits** via `context.channel().ask_*` inside `@graph_fn`.

  * Great for interactive agents while the process is alive.
  * Not resumable after the Python process dies.
* **Dual‑stage waits** via built‑in tools used in `@graphify` static graphs.

  * The graph can pause indefinitely (e.g., waiting for Slack/Web reply).
  * You can **cold‑resume** with the same `run_id` much later.

Custom waits are about taking that second pattern and making it available for **your own backends**:

* external approval systems
* internal job schedulers
* lab/experiment queues
* human‑in‑the‑loop tools that live outside channels like Slack/Telegram

The goal: let you say *“pause here until X happens in system Y, then resume this node safely”*.

---

## 2. What Exists Today

You already have:

* Cooperative waits on `NodeContext.channel()` (`ask_text`, `ask_approval`, `ask_files`, etc.).
* Built‑in **dual‑stage wait tools** (used in the channel tutorial) that:

  * create a continuation token
  * emit an outgoing event (e.g. to Slack/Web)
  * persist a snapshot
  * resume when an inbound event matches that token

These built‑ins are wired to existing adapters (console, Slack, etc.) and work out of the box for common interaction flows.

> What’s missing right now is a **public, stable API** for defining your own dual‑stage tools and adapters.

That’s what this “coming soon” chapter is preparing you for.

---

## 3. Design Shape of a Dual‑Stage Tool (Conceptual)

At a high level, a dual‑stage tool will look like:

1. **Stage A – schedule / emit**

   * Construct a request payload.
   * Register a continuation token with the runtime.
   * Send an event to some external system (HTTP, MQ, email, etc.).
   * Return a **WAITING** status instead of a final result.

2. **Stage B – resume / handle reply**

   * An inbound event (webhook, poller, bridge) calls back with the same token.
   * Runtime restores the graph + node and hands you the reply payload.
   * Your tool continues execution and returns a normal result.

### Possible future shape (pseudo‑code, not final)

```python
class ApproveJob(DualStageTool):  # name TBD
    async def build_request(self, spec: dict, *, context):
        # Stage A: emit request + return a continuation descriptor
        token = await context.create_continuation(kind="job_approval", payload={"spec": spec})
        await self.emit_request(spec=spec, token=token)
        return self.wait(token)   # tells runtime: this node is now WAITING

    async def on_resume(self, reply: dict, *, context):
        # Stage B: this runs when the continuation is resumed
        approved = bool(reply.get("approved", False))
        return {"approved": approved}
```

Again: this is **illustrative only** — the real base class and method names will be documented once the API is ready.

The important idea is the split between **“set up a wait + emit a request”** and **“handle the resume payload”**, wired together by a continuation token.

---

## 4. Adapters: Bridging External Systems

Custom waits are only half the story — you also need a way to **bridge** an external system to AetherGraph’s continuation store.

Conceptually, an adapter will:

1. **Listen** for inbound events from your system (webhook, queue consumer, polling loop).
2. **Parse** them into a payload `{token, data}`.
3. **Call the runtime** to resolve the corresponding continuation and resume the graph.

In practice this might look like (pseudo‑code):

```python
# somewhere in your web app / worker

@app.post("/callbacks/job-approved")
async def job_approved(req):
    token = req.json()["token"]
    payload = {"approved": req.json()["approved"]}
    await runtime.resolve_continuation(token=token, payload=payload)
    return {"ok": True}
```

Behind the scenes, the runtime will:

* load the snapshot for the relevant `run_id` / graph
* mark the waiting node as ready
* resume execution from that node using the payload

The **adapter API** that makes this nicer to write will be documented with the dual‑stage tool support.

---

## 5. How This Relates to `graph_fn` and `graphify`

It’s useful to remember the three modes:

| Mode                             | Wait type available today   | Cold‑resume after process exit? |
| -------------------------------- | --------------------------- | ------------------------------- |
| `graph_fn` + `context.channel()` | Cooperative waits (`ask_*`) | ❌ No                            |
| `graphify` + built‑in dual waits | Dual‑stage tools            | ✅ Yes                           |
| `graphify` + custom dual waits   | **Coming soon**             | ✅ Yes (for your own waits)      |

Once custom dual‑stage tools are available, you’ll:

* Use `graph_fn` when you want **live, in‑process agents**. You can certainly combine `graph_fn` and `DualStageTool`, it's just `graph_fn` does not preserve states and resumption is not protected if the process gets interrupted. 
* Use `graphify` + dual‑stage waits when you want **hard guarantees** about resuming long‑running flows.
* Wrap external systems (HPC, approval workflows, human review portals) as first‑class wait nodes.

---

## 6. What You Can Do Today

While the custom API is still baking, you can already:

* Use **built‑in dual‑stage waits** with channels (Slack/Web) in static graphs to pause and resume runs.
* Use **cooperative waits** (`context.channel().ask_*`) in `graph_fn` agents when you don’t need cold‑resume.
* Front external systems with simple scripts or services that call existing channel tools (for example, sending a Slack approval that resumes a static graph).

When the public dual‑stage API lands, you’ll be able to replace those scripts with:

* explicit `@tool`‑style wait nodes, and
* small, typed adapters that speak your domain’s language.

---

## 7. Looking Ahead

This chapter is intentionally high‑level and labeled **Coming Soon**. The final documentation will include:

* A concrete **base class or decorator** for defining dual‑stage wait tools.
* A small **adapter kit** for wiring external callbacks into the continuation store.
* End‑to‑end examples: long‑running jobs, external approval systems, and custom interactive apps.

Until then, you can design your flows with this mental model in mind:

> *“Anything that can emit a token and later send it back can be turned into a resumable node.”*

Once the API is ready, you’ll drop in the real primitives and your graphs will gain robust, resumable waits across all your systems.
