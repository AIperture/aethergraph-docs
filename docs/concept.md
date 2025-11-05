# AetherGraph — Architecture Overview (1‑page)

> **Goal:** Give newcomers a single "big picture" of how AetherGraph fits together, then provide a tiny legend so they know what to look up next.

```
┌────────────────────────────────────────────────────────────────────┐
│                          AetherGraph Runtime                       │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Python Code (your repo)                                           │
│  ────────────────────────────────────────────────────────          │
│  @graph_fn nodes           Tools (@tool)            Services       │
│  (code-native agents)      (reusable ops,           (external ctx) │
│                            checkpointable)                          │
│       │                           │                    │            │
│       ▼                           ▼                    ▼            │
│  ┌──────────────┐          ┌─────────────┐      ┌──────────────┐    │
│  │  Node Exec   │◀────────▶│  Tool Exec  │      │  Service API │    │
│  └──────────────┘          └─────────────┘      └──────────────┘    │
│        │                                                         │    │
│        ▼                                                         │    │
│                       ┌──────────────────────────┐                   │
│                       │        NodeContext       │  (per node call)  │
│                       ├──────────────────────────┤                   │
│                       │ channel()   →  chat/CLI/GUI (send/ask)       │
│                       │ memory()    →  record/recent/query           │
│                       │ artifacts() →  write/read refs (provenance)  │
│                       │ kv()        →  small fast key–value          │
│                       │ logger()    →  structured logs               │
│                       │ services()  →  external ctx (domain APIs)    │
│                       └──────────────────────────┘                   │
│                                │                                     │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │               Sidecar / Adapters (inline server)               │ │
│  │  - Console/CLI channel                                         │ │
│  │  - Slack / PyQt / HTTP webhooks                                │ │
│  │  - File/artifact endpoints (optional, later hosted)            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Legend (skim-first)

* **`@graph_fn` (code‑native agents):** Turn a plain async Python function into a *node* with a `NodeContext` injected.
* **Tools (`@tool`):** Small, explicit, reusable operations. Great for checkpoints, retries, and sharing across graphs.
* **NodeContext:** Where your node *talks* to the world: `channel()`, `memory()`, `artifacts()`, `kv()`, `logger()`, `services()`.
* **Channel:** Unifies human I/O (console/Slack/PyQt). Use `send_text`, `ask_text`, and progress APIs.
* **Memory & Artifacts:** Event‑first memory with provenance; artifacts store files/results with stable refs.
* **External Context (Services):** Register domain services (e.g., job runner, materials DB) so nodes call them like built‑ins.
* **Sidecar:** Inline server that powers channels/adapters locally; later you can host these endpoints.

**Next:** See *Memory Internals* below, then the *Submit → Poll → Notify* tutorial.

---

# Memory Internals (diagram)

> **Goal:** Show how event logging, persistence, indices, and optional RAG hang together.

```
              ┌─────────────────────────────────────────┐
              │          memory().record(...)           │
              │   kind • data • tags • entities • ...   │
              └─────────────────────────────────────────┘
                                  │
                                  ▼
                   (in‑process event stream / bus)
                                  │
          ┌────────────────────────┴────────────────────────┐
          ▼                                                 ▼
┌───────────────────────────┐                  ┌───────────────────────────┐
│  JSONL Persistence Log    │  append‑only     │   KV / Indices            │
│  (provenance timeline)    │  (durable)       │   (fast lookup/filter)    │
│  e.g., runs/YYYY/MM/*.jsonl│                 │   tags, kinds, entity ids │
└───────────────────────────┘                  └───────────────────────────┘
          │                                                 │
          │                                                 │
          ▼                                                 ▼
┌───────────────────────────┐                  ┌───────────────────────────┐
│ Derived Views / Cursors   │  recent(...)     │   Optional RAG Binding    │
│ e.g., last_by_name,       │  query(...)      │   (vector index)          │
│ latest_refs_by_kind       │                  │   embed(data/artifacts)   │
└───────────────────────────┘                  └───────────────────────────┘
          │                                                 │
          └──────────────►  NodeContext.memory().query(...) ◄─────────────┘

```

* **Record:** Write small structured events with `kind`, `data`, `tags`, `entities`, `metrics`.
* **Persist:** Append to a **JSONL** log for durability & replay; perfect for provenance.
* **Index:** Maintain fast **KV/indices** for quick filters (by kind/tags/entity/time).
* **RAG (optional):** Bind a vector index to selectively embed text/artifact content for semantic search.
* **Query:** Use `recent`, `query`, and helpers like `latest_refs_by_kind` to drive summaries & reports.

**When to use RAG?** When you want semantic retrieval over larger text blocks or artifact‑derived content; otherwise rely on indices and tags for speed/clarity.

---

# Tutorial — Submit → Poll → Notify (single file, runnable)

> **Goal:** Minimal end‑to‑end job orchestration with human notification and provenance. Keep it console‑only, no external infra.

```python
# examples/tutorial_submit_poll_notify.py
from __future__ import annotations
import asyncio, random, time
from typing import Dict, Optional

# AetherGraph imports (adjust paths/names to your package layout)
from aethergraph import graph_fn, NodeContext
from aethergraph.server import start
from aethergraph.v3.core.runtime.runtime_services import register_context_service

# --- 1) Start the inline sidecar so channel/memory/artifacts work locally ---
start()  # prints a local URL; not required to save here

# --- 2) A tiny external service: fake job runner (auto‑bound to NodeContext) ---
class FakeJobRunner:
    """Pretend to submit a remote job and poll until it finishes.
    In a real impl, call your cloud API here.
    """
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Optional[str]]] = {}

    async def submit(self, spec: Dict) -> str:
        job_id = f"job_{int(time.time()*1000)}_{random.randint(100,999)}"
        # status can be: queued → running → (succeeded | failed)
        self._jobs[job_id] = {"status": "queued", "result": None}
        # Background simulation
        asyncio.create_task(self._simulate(job_id, spec))
        return job_id

    async def poll(self, job_id: str) -> Dict[str, Optional[str]]:
        return self._jobs[job_id]

    async def _simulate(self, job_id: str, spec: Dict):
        # Fake lifecycle with sleeps
        await asyncio.sleep(0.5)
        self._jobs[job_id]["status"] = "running"
        await asyncio.sleep(1.2)
        if random.random() < 0.85:
            self._jobs[job_id]["status"] = "succeeded"
            self._jobs[job_id]["result"] = f"Result for {spec.get('name','demo')}"
        else:
            self._jobs[job_id]["status"] = "failed"
            self._jobs[job_id]["result"] = None

# Register the service under the name "jobs" and auto‑bind it to context as context.jobs()
register_context_service("jobs", FakeJobRunner())

# --- 3) The graph node: submit → poll → notify, with artifacts & memory ---
@graph_fn(name="submit_poll_notify")
async def submit_poll_notify(spec: Dict, *, context: NodeContext) -> Dict:
    ch = context.channel()
    mem = context.memory()
    arts = context.artifacts()
    jobs = context.jobs()  # auto‑bound external service

    await ch.send_text("Submitting your job…")
    job_id = await jobs.submit(spec)
    await mem.record(kind="job_submitted", data={"job_id": job_id, "spec": spec}, tags=["demo"])

    # Persist the spec as an artifact
    spec_ref = await arts.write_text(f"spec_{job_id}.json", content=str(spec))

    # Poll until terminal
    while True:
        info = await jobs.poll(job_id)
        status = info.get("status")
        await ch.send_text(f"Status: {status}")
        if status in {"succeeded", "failed"}:
            break
        await asyncio.sleep(0.6)

    if status == "succeeded":
        result_text = info.get("result") or "<no result>"
        res_ref = await arts.write_text(f"result_{job_id}.txt", content=result_text)
        await mem.record(kind="job_succeeded", data={"job_id": job_id, "result_ref": res_ref})
        await ch.send_text(f"✅ Job {job_id} finished. Saved result → {res_ref}")
        return {"job_id": job_id, "status": status, "spec_ref": spec_ref, "result_ref": res_ref}
    else:
        await mem.record(kind="job_failed", data={"job_id": job_id})
        ans = await ch.ask_text(f"❌ Job {job_id} failed. Retry? (yes/no)")
        if str(ans).strip().lower().startswith("y"):
            return await submit_poll_notify(spec=spec, context=context)
        await ch.send_text("Not retrying; stopping here.")
        return {"job_id": job_id, "status": status, "spec_ref": spec_ref}

# --- 4) Tiny runner for local testing ---
if __name__ == "__main__":
    async def main():
        out = await submit_poll_notify(spec={"name": "toy-sim", "steps": 3})
        print("FINAL OUTPUT:\n", out)
    asyncio.run(main())
```

### What this tutorial demonstrates

* **Channel I/O:** human‑visible status + retry prompt.
* **External Service:** a domain API (`jobs`) registered once, used like a built‑in via `context.jobs()`.
* **Memory:** durable events (`job_submitted`, `job_succeeded`, `job_failed`).
* **Artifacts & provenance:** spec/result written with stable refs; returned in the node output.
* **Low friction:** single file; console channel only; no extra infra.

**Next:**

* Swap `FakeJobRunner` for your cloud client.
* Replace `ask_text` with an approval UI (Slack/PyQt) once you enable those adapters.
* Emit metrics in `mem.record(..., metrics={...})` and add a summary node to close the loop.
