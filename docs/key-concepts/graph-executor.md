# Graph Executor — Schedulers

AetherGraph’s execution model uses **schedulers** to drive node execution, handle dependencies, and coordinate events across graphs. There are two major modes:

* **Local scheduler** – lightweight, per‑graph control loop used by `@graph_fn`.
* **Global scheduler** – centralized, event‑driven scheduler managing all graphs submitted by `@graphify`.

---

## 1. Local vs Global Schedulers

### Local Scheduler (used by `@graph_fn`)

* Each `@graph_fn` invocation runs in its **own event loop context**, orchestrated directly by Python’s async runtime.
* It executes sequentially or with lightweight concurrency (via `await` and tasks).
* **No graph queueing** — tool calls execute immediately or schedule via local awaits.
* Ideal for **reactive, interactive agents** where quick iteration matters.
* Regular Python functions (non‑tool calls) **bypass scheduling entirely**, running through the native Python runtime.

### Global Scheduler (used by `@graphify`)

* A **single global event loop** drives all active graphs and nodes across runs.
* Implements **fair, event‑driven scheduling** with per‑run capacity, retry policies, and backoff.
* Nodes enter the global queue when ready, and yield back control when waiting for continuations or dependencies.
* Perfect for **static DAGs**, **multi‑run orchestration**, and **large‑scale deployments**.

---

## 2. Conceptual Diagram

```
          ┌────────────────────────────┐
          │        Local Scheduler     │
          │  (per @graph_fn runtime)   │
          │                            │
   async →│ executes Python awaitables │
  calls → │ immediate tool invocations │
          │  small scale, no registry  │
          └────────────┬───────────────┘
                       │ submits TaskGraph (optional)
                       ▼
          ┌────────────────────────────┐
          │       Global Scheduler     │
          │ (multi‑graph orchestrator) │
          │  • One event loop          │
          │  • Runs across all graphs  │
          │  • Event‑driven resumes    │
          │  • Backoff & retries       │
          └────────────────────────────┘
```

---

## 3. Scheduler Algorithm Overview

### Core Loop Type

The **GlobalForwardScheduler** is **event‑driven**, not polling‑based.

* It sleeps until an event (resume, wakeup, or node completion) is emitted.
* Once awakened, it drains queued events, checks for ready nodes, and dispatches eligible tasks.
* Each run has bounded concurrency, and optionally, a global cap across all runs.

### Simplified Flow

```
while not terminated:
    drain control events (resume, wakeup)
    schedule resumed nodes first
    schedule ready nodes (deps satisfied)
    await first_completed(running_tasks or new events)
    on node_done → emit event → unblock dependents
```

* **Event sources:** resume signals, new runs, wakeups, and node completions.
* **Scheduling order:** resumed nodes → explicitly pending → dependency‑ready nodes.
* **Fairness:** round‑robin across runs.
* **Idle handling:** if no nodes running, block until the next event.

---

## 4. Resource Model

| Resource    | Local Scheduler (`@graph_fn`)                | Global Scheduler (`@graphify`)                            |
| ----------- | -------------------------------------------- | --------------------------------------------------------- |
| **CPU**     | Uses local async tasks; minimal overhead     | Centralized asyncio event loop with per‑run task pools    |
| **Memory**  | In‑process; short‑lived per function         | Persistent per‑run state tables (node states, queues)     |
| **Disk**    | None unless memory/artifact writes used      | Writes resumable states and continuations (~1–10 KB/node) |
| **Network** | Only if context services use remote backends | Communicates via Resume/Wakeup buses for distributed runs |

---

## 5. Why This Design Works

* **Local scheduler** — fast, minimal overhead, ideal for reactive research and small DAGs.
* **Global scheduler** — durable, resumable, and optimized for long‑running or large workflows.
* **Event‑driven architecture** — ensures zero busy‑waiting and minimal CPU when idle.
* **Per‑run independence** — each graph maintains its own capacity, backoff, and retry settings.

---

## 6. Summary

| Aspect                     | Local Scheduler (`@graph_fn`)   | Global Scheduler (`@graphify`)           |
| -------------------------- | ------------------------------- | ---------------------------------------- |
| **Scope**                  | One runtime function            | Many graphs, many runs                   |
| **Control**                | Immediate async execution       | Central event bus + scheduling queues    |
| **Scheduling granularity** | Function level                  | Node level (with retries/resume)         |
| **Persistence**            | Ephemeral                       | Durable; resumable                       |
| **Best for**               | Interactive or exploratory runs | Deterministic, large‑scale orchestration |

> In short: **`@graph_fn`** runs live, reactive agents; **`@graphify`** builds orchestrated pipelines under a global, event‑driven scheduler.
