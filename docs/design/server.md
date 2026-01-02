# AetherGraph Deployment Modes & Data Flow

This doc outlines three primary deployment modes for AetherGraph (AG), how the sidecar/server behaves in each, and how data flows between clients (Slack, browser UI, other services), AG, and storage.

We’ll describe:

* **Mode 1 — Local Sidecar (Developer / Researcher)**
* **Mode 2 — Single-Tenant App Server (Enterprise Self-Hosted)**
* **Mode 3 — SaaS Control Plane + Worker Pool (Hosted by AIperture)**

For each mode, we’ll specify:

* Responsibilities of the server
* Data flow for channel events (e.g., Slack) and UI
* Where storage lives and how the primitives (BlobStore, DocStore, EventLog, VectorIndex) fit

At the end, we’ll summarize how to evolve from Mode 1 → Mode 2 → Mode 3 without changing graph/tool APIs.

---

## Shared Concepts Across All Modes

Before diving into modes, here are the shared pieces that exist in *every* deployment:

* **AG Runtime**

  * Executes graphs and tools.
  * Uses `ExecutionContext` and services (artifacts, memory, state, continuations, LLM, custom services, etc.).

* **Storage primitives**

  * **BlobStore** – raw bytes (artifacts, bundles, large snapshots).
  * **DocStore** – keyed JSON docs (summaries, config, snapshot metadata, continuation payloads, etc.).
  * **EventLog** – append-only events (chat turns, tool_results, state events, memory events).
  * **VectorIndex** – embeddings search for RAG and semantic retrieval.

* **Domain facades**

  * `ArtifactFacade` (ArtifactStore + ArtifactIndex)
  * `MemoryFacade` (hot log + durable log + doc summaries + optional vector)
  * `GraphStateStore` (snapshots + state events)
  * `ContinuationStore` (continuations + token/correlator indices)

* **Channel / Interaction layer**

  * Normalises *external* messages into AG events (e.g. Slack, HTTP chat, WebSocket).
  * Uses continuations + resume router for DualStage tools.

* **HTTP/WS API surface** (varies by mode)

  * `/api/graph/{graph_id}/run` – invoke a graph.
  * `/api/events` – query events for observability.
  * `/api/events/stream` – live events via WS or SSE.
  * `/api/artifacts` – upload/download artifact bytes.
  * `/api/channel/*` – channel-specific endpoints (Slack, HTTP chat, etc.).

---

## Mode 1 — Local Sidecar (Developer / Researcher)

**Mental model:**

> “AG runs on my laptop as a sidecar process. It executes graphs and exposes local HTTP/WS APIs for UI & tools. Storage is local.”

### Responsibilities

* Run the **AG runtime and scheduler**.
* Own **all storage primitives** (BlobStore, DocStore, EventLog, VectorIndex) locally.
* Expose HTTP/WS endpoints on `localhost` for:

  * Running graphs (`/api/graph/{id}/run`).
  * Observability (`/api/events`, `/api/runs`, `/api/artifacts`).
  * Optional local UI (web frontend) and channel adapters.

### Typical Topology

```text
+-------------------------------+
|  User Laptop                  |
|                               |
|  +------------------------+   |
|  | AG Sidecar Process     |   |
|  |  - Runtime             |   |
|  |  - Storage primitives  |   |
|  |  - Channel endpoints   |   |
|  +-----------+------------+   |
|              | HTTP/WS        |
|         +----v-------------+  |
|         | Local UI / CLI   |  |
|         |  (React app,     |  |
|         |   console, etc.) |  |
|         +------------------+  |
+-------------------------------+
```

* All connections are **local (`127.0.0.1`)**.
* Slack (if used) might be wired directly to the laptop via a tunnel (ngrok) or WS hack, but that’s a power-user setup.

### Data Flow Examples

1. **Run a graph from the terminal**

```text
User → `python my_graph.py`
  → AG Runtime executes graph
    → Facades write artifacts/memory/state to local FS/DB
  → Terminal prints outputs
```

2. **Inspect runs via local UI**

```text
Browser (localhost:3000) → /api/events?run_id=... (HTTP)
                           /api/events/stream (WS/SSE)
  → Sidecar reads from EventLog / DocStore
  → UI renders run timeline & artifacts
```

### When to Use

* Individual R&D, notebooks, experiments.
* Local “agent companions” or sidecar tools.
* No need for remote access by default; safe by binding to `localhost` only.

---

## Mode 2 — Single-Tenant App Server (Enterprise Self-Hosted)

**Mental model:**

> “The sidecar *is* our main production AG server. It runs in the company’s cloud or on-prem cluster and exposes AG APIs internally.”

### Responsibilities

* Same as Mode 1, but now:

  * Runs on a **server/cluster** inside the enterprise network.
  * Might have **multiple replicas** behind a load balancer.
  * Uses **shared storage backends** (S3, Postgres, Redis, etc.).

* Expose **stable HTTP/WS APIs** for:

  * Internal services (e.g., `foo-service` calling `/api/graph/optimize_lens/run`).
  * Internal UIs (AG dashboard, custom apps).
  * Channel integrations (Slack, Teams, internal chat).

### Topology

```text
                 Enterprise Network
+-------------------------------------------------+
|                                                 |
|  +----------------------+     +--------------+  |
|  | Load Balancer        |     | Storage      |  |
|  | (HTTPS)              |     | (S3, DB, KV) |  |
|  +----------+-----------+     +------+-------+  |
|             |                         ^          |
|       +-----v----------------+        |          |
|       |  AG App Server       |        |          |
|       |  (one or many pods)  |        |          |
|       |  - Runtime           |        |          |
|       |  - Storage adapters  +--------+          |
|       |  - Channel endpoints |                   |
|       +----------+-----------+                   |
|                  | HTTP/WS                       |
|   +--------------v-------------+                 |
|   | Internal UIs / Services    |                 |
|   | (Dashboards, APIs, etc.)   |                 |
|   +----------------------------+                 |
+-------------------------------------------------+
```

### Data Flow (Slack example)

```text
Slack → HTTPS → AG App Server /api/channel/slack/events
      → AG normalizes to ChannelEvent
      → AG runtime routes to appropriate graph / continuation
      → Graph runs, writes events/artifacts to storage
      → AG App Server responds to Slack via Slack Web API
```

### Data Flow (internal HTTP client)

```text
Internal service → POST /api/graph/{id}/run {input JSON}
AG App Server   → Executes graph
                → Writes artifacts / events / memory
                → Returns outputs (or run_id for async)
```

### When to Use

* Enterprise wants full control and **self-hosts** AG.
* AG integrates with internal systems, SSO, internal Slack.
* Scaling = add more AG App Server replicas using shared storage.

---

## Mode 3 — SaaS Control Plane + Worker Pool (Hosted by AIperture)

**Mental model:**

> “AG is a cloud platform. A control-plane handles APIs, channels, and UI, while a pool of workers runs graphs. Storage is shared. Slack and UIs talk only to the control-plane.”

### Responsibilities

**Control Plane**

* Owns:

  * Public APIs (`/api/graph/run`, `/api/channel/*`, `/api/events`, `/api/artifacts`).
  * Auth, multi-tenant routing (which workspace/tenant is this?).
  * Slack/Teams/other channel integrations.
  * Web UI and dashboards.
  * Job dispatch to workers (via queue or internal RPC).

**Worker Plane**

* Multiple AG **worker processes/containers**:

  * Each runs the AG runtime.
  * Pulls jobs from a queue (or receives them via WS/gRPC).
  * Writes artifacts/memory/state to shared storage.
  * Optionally opens a WS back to control-plane for live events.

### Topology Diagram

```text
                   Internet
                      |
          +-----------+------------+
          |  Control Plane (CP)    |
          |  - Public APIs         |
          |  - Channel endpoints   |
          |  - UI                  |
          |  - Auth & routing      |
          +-----+-------------+----+
                |             |
      Slack /   |             | HTTP/WS
      Webhooks  |             v
                |      +-------------+
                |      |  Job Queue  |
                |      +------+------+ 
                |             ^
                |             |
                |      (jobs: run graph X)
                |             |
+-----------------------------+---------------------------+
|                   Worker Plane                           |
|                                                         |
|   +--------------------+     +--------------------+     |
|   | AG Worker 1        | ... | AG Worker N        |     |
|   | - Runtime          |     | - Runtime          |     |
|   | - Services         |     | - Services         |     |
|   +---------+----------+     +----------+---------+     |
|             |                           |               |
|             +------------+--------------+               |
|                          |                              |
|                     Shared Storage                      |
|               (BlobStore, DocStore, EventLog,          |
|                VectorIndex: S3/DB/etc.)                |
+---------------------------------------------------------+
```

### Data Flow (Slack → CP → Worker → Slack)

1. **Incoming event**

```text
Slack → CP /api/channel/slack/events
  → CP authenticates & normalizes event
  → CP enqueues a job: {workspace, graph_id, run_id?, input}
```

2. **Execution**

```text
Worker → pulls job from queue
       → runs graph via AG runtime
       → writes events to EventLog, artifacts to BlobStore, etc.
       → optionally sends live events back to CP via WS
```

3. **Outgoing message**

```text
CP → reads events (or receives streamed ones)
   → detects outgoing messages for Slack
   → calls Slack Web API using stored tokens
Slack channel shows assistant response
```

### Data Flow (Browser UI)

```text
Browser → CP /api/graph/run (start run)
CP      → enqueues job
Worker  → executes, writes events/artifacts
Browser → CP /api/events?run_id=... (poll) or /api/events/stream (WS)
```

### Local Worker Hybrid (optional future pattern)

* A user can run an **AG Worker locally** that connects outbound to the control-plane over WS:

```text
Local Worker → opens WS to CP: "I am worker for workspace X"
CP           → sends jobs over WS instead of cloud queue
Worker       → runs graphs locally, writes to either:
              - local storage, and forwards key metadata, or
              - remote storage via HTTP APIs
```

This allows “no exposed local IP” while still leveraging local compute.

---

## Capability Summary Per Mode

| Capability         | Mode 1: Local Sidecar        | Mode 2: Single-Tenant Server           | Mode 3: SaaS CP + Workers                       |
| ------------------ | ---------------------------- | -------------------------------------- | ----------------------------------------------- |
| Where AG runs      | Laptop / single machine      | Single service / several replicas      | Control plane + many workers                    |
| Storage backends   | Local FS / SQLite            | S3, Postgres, Redis (enterprise infra) | Managed S3/DB, multi-tenant                     |
| Channel entrypoint | Localhost / optional tunnel  | Internal URL (Slack, internal apps)    | Public URL at your domain                       |
| Who owns Slack app | User (local dev)             | Enterprise (self-hosted app)           | You (AIperture-managed Slack app)               |
| Graph invocation   | CLI, localhost HTTP/WS       | Internal HTTP/WS                       | Public API → queued → workers                   |
| Observability      | Local UI/CLI via /api/events | Internal dashboards via /api/events    | SaaS UI reading from shared EventLog + DocStore |
| Scaling            | Single process               | Scale out app servers                  | Scale control plane + worker pool independently |

---

## How to Think About Evolution

### From Mode 1 → Mode 2

* Take the existing **sidecar** and:

  * Run it on a server instead of a laptop.
  * Swap storage adapters for cloud ones (S3/DB instead of local FS/SQLite).
  * Add auth, TLS, and a proper domain.

* Graphs, tools, and services do **not** need to change — they still talk to `ArtifactFacade`, `MemoryFacade`, etc.

### From Mode 2 → Mode 3

* Split responsibilities into:

  * **Control Plane**: keep existing HTTP/WS APIs, add multi-tenancy, job queue, auth, and UI.
  * **Workers**: run a headless version of the AG runtime that:

    * Listens for jobs (via queue/WS/gRPC).
    * Uses the same storage adapters.

* Again, graph/tool APIs stay the same; only the **deployment topology** changes.

---

## Takeaways

* The **sidecar** you’re building now is already the core of:

  * A local dev tool (Mode 1),
  * A self-hosted app server (Mode 2), and
  * The worker & API pieces of a SaaS platform (Mode 3).

* By keeping:

  * storage unified via `BlobStore / DocStore / EventLog / VectorIndex`, and
  * interaction unified via channel + continuation APIs,

  you can change **where** and **how many** processes run AG without changing how users write graphs and tools.
