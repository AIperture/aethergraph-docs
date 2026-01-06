# Defining Apps and Agents for the AetherGraph UI

This page explains:

- What **agents** and **apps** are in AetherGraph
- When you need them (only if you’re using the **AG UI**)
- How to define them with minimal metadata
- Best practices for orchestration and memory
- How the UI passes information (messages, files, context refs) into your backend entrypoints

If you’re only using AetherGraph as a **Python library (no UI)**, you **don’t need** to define agents or apps at all. You can just call your graphs directly.

---

## 1. Concepts: Agent vs App

### 1.1 Agent

An **agent** is a **chat endpoint** exposed to the AG UI.

- It shows up in the **Agent Gallery**.
- The UI creates a **chat session** bound to that agent.
- Each user message is turned into a run of the **agent’s graph function**, using a fixed "chat" signature.
- Inside the agent, you can:
    - Call tools and other graphs
    - Spawn background runs
    - Write to memory
    - Log artifacts, etc.

Key points:

- An agent must be a **`graph_fn`** (a function-like entrypoint), not a full `@graphify` flow.
- That `graph_fn` uses a **fixed input signature** for `mode="chat_v1"` (the default chat agent mode).
- The agent can **internally** spawn or run other `graphify` graphs or `graph_fn`s.

Think of the agent as the **front door for conversation**, not as the place to do all heavy work. Use it as a thin router that delegates to other graphs.

> The structure of `files` and `context_refs` may evolve as the UI grows. The idea stays the same: the UI collects what the user selected (files, artifacts, runs) and passes them to your agent.

---

### 1.2 App

An **app** is a **click-to-run flow** exposed to the AG UI.

- It shows up in the **App Gallery**.
- The user clicks an app card to start a new **run**.
- The run is tracked, visualized, and (for graphs) can be resumed in the UI.

Key points:

- An app can be backed by either:
    - a `@graphify` **graph** (recommended), or
    - a `@graph_fn` **function**.
- For observability and resumption, **`graphify` is strongly recommended**:
    - You get full run history and node-level status.
    - Resumption and partial reruns are easier.

Apps are ideal for flows like:

- ETL / batch processing
- Data analysis pipelines
- Long-running workflows kicked off by a single click

---

### 1.3 When do I need agents/apps?

You only need to define agents and apps if you want your logic to appear in the **UI** as:

- a **chat agent**, or
- a **launchable app** from the galleries.

If you’re building a purely programmatic pipeline with no UI, you can ignore `as_agent` and `as_app` entirely.

---

## 2. Minimal definitions (the happy path)

AetherGraph is designed so you can start with **minimal metadata** and still get a usable UI:

- Agents: only `id` and `title` are required.
- Apps: only `id` and `name` are required.

Everything else is optional and has sensible defaults.

### 2.1 Minimal agent

```python
from aethergraph import graph_fn

@graph_fn(
    name="demo_agent",
    as_agent={
        "id": "demo_agent",
        "title": "Demo Agent",
        # everything else (mode, badge, category, etc.) is optional
    },
)
async def demo_agent(
    message: str,
    files: list[dict] | None,
    context_refs: list[dict] | None,
    session_id: str,
    user_meta: dict | None,
    *,
    context,
) -> str:
    # Thin conversational entrypoint; do as little as possible here.
    return f"You said: {message}"
```

Defaults you get automatically (from backend meta building):

- `mode = "chat_v1"` (chat-style agent)
- `status = "available"`
- `session_kind = "chat"`

Category, badge, color, tags, etc. are optional. The UI will still show a functional card in the **Agent Gallery** and let you open a chat session.

---

### 2.2 Minimal app

```python
from aethergraph import graphify

@graphify(
    name="demo_app",
    inputs=[],   # recommended: no required inputs; configure via channels/memory
    as_app={
        "id": "demo_app",
        "name": "Demo App",
    },
)
def demo_app():
    """Example of a simple app-backed graph."""
    ...
```

Defaults you get automatically:

- `mode = "no_input_v1"`
- `status = "available"`

If you don’t specify a category, the app still shows up in the gallery (e.g. under an "Other Apps" section). As you grow the project, you can later add richer metadata without touching the core graph code.

---

## 3. Agent requirements & patterns

### 3.1 Fixed input signature for `chat_v1`

For the default chat agent mode (`mode="chat_v1"`):

- The agent **must** be a `graph_fn`.
- It must accept the standard chat inputs:

  - `message`: the user’s message text
  - `files`: any uploaded files / attachments for this turn
  - `context_refs`: references to selected files, artifacts, or runs in the UI
  - `session_id`: the current chat session ID
  - `user_meta`: optional metadata about the user
  - `context`: the injected `NodeContext` (keyword-only argument)

The exact structure of `files` and `context_refs` may change, but we keep the signature stable and the intent the same.

---

### 3.2 Use the agent as a thin router

Best practice: **keep the agent entrypoint light**. It should mostly:

1. Parse the message and decide what to do.
2. Use the **context methods** to orchestrate background work.

For example:

- Call another graph to process data.
- Spawn a long-running run in the background.
- Store or retrieve memory.

This keeps the chat UI responsive and prevents your agent from blocking on long tasks.

---

## 4. Apps: `graphify` vs `graph_fn`

You can define an app on:

- a `@graphify` graph (recommended), or
- a `@graph_fn` function.

**Recommended:** use `graphify` whenever you care about:

- Step-by-step observability in the UI
- Resuming after failures
- Visualizing the structure of your flow

Example:

```python
from aethergraph import graphify

@graphify(
    name="batch_import",
    inputs=[],
    as_app={"id": "batch_import", "name": "Batch Import"},
)
def batch_import():
    """Example app that runs as a tracked, resumable graph."""
    ...
```

You can still call the same `batch_import` graph from agents or from code using context methods or normal Python calls.

---

## 5. Metadata: minimal vs richer UI

You already have a detailed reference page for all metadata keys.
Here we keep it high-level and opinionated.

### 5.1 Minimal agent metadata

```python
as_agent={
    "id": "assistant",
    "title": "Assistant",
}
```

Everything else is optional. When you want nicer cards and better grouping, you can add:

- `badge`: small label on the card, e.g. `"Chat Agent"`.
- `category`: e.g. `"Core"`, `"R&D Lab"`, `"Infra"`, `"Productivity"`.
- `short_description`: brief summary for the gallery card.
- `icon_key`: icon to use in the gallery (e.g. `"message-circle"`).
- `color`: accent color token (e.g. `"emerald"`).
- `tags`: for filtering and search.
- `features`: bullet points for the detail panel.
- `github_url`: link to the agent’s implementation.

---

### 5.2 Minimal app metadata

```python
as_app={
    "id": "demo_app",
    "name": "Demo App",
}
```

Same idea as agents: start minimal, add more when you care about presentation and grouping.

---

## 6. Best practices: orchestration from agents

### 6.1 Use agents as "front doors"

Good pattern:

- Define one or a few **well-scoped agents** as entrypoints.
- Inside each agent:
  - Parse the request.
  - Decide which graphs to call.
  - **Spawn** the actual work as runs.

This keeps:

- The chat UI responsive.
- Runs organized by agent, session, and tags.
- Your core graphs reusable across agents, apps, and scripts.

---

### 6.2 `spawn_run` as the default orchestration primitive

From your agent (or any graph function) you can access a `context` object that offers helpers like `spawn_run` and `wait_run`.

Example pattern:

```python
from aethergraph.runtime import RunVisibility

@graph_fn(
    name="assistant_agent",
    as_agent={"id": "assistant", "title": "Assistant"},
)
async def assistant_agent(message: str, files, context_refs, session_id: str, user_meta, *, context):
    if "analyze" in message:
        run_id = await context.spawn_run(
            "analysis_graph",
            inputs={"message": message},
            visibility=RunVisibility.normal,
        )
        return f"I started an analysis run (run_id={run_id}). I’ll let you know when it’s done."

    # Simple inline reply
    return f"Quick answer to: {message}"
```

Notes:

- `spawn_run` returns quickly and does not block the agent.
- You only need minimal inputs: graph name, optional `inputs`, and `visibility`.
- Later you can pass tags, parent IDs, or other metadata if needed.

When you **do** need the result of a run, you can call:

```python
record = await context.wait_run(run_id)
```

> Today, `RunRecord` contains run metadata (timestamps, status, etc.) but does **not** expose outputs yet.
> That API will evolve; see [UI notes](ui-notes.md#current-limitations) for up-to-date caveats.

---

## 7. Memory in agents

Agents often need **persistent memory** to behave coherently across runs and sessions. You configure this via `memory_level` and `memory_scope` in `as_agent`.

### 7.1 Memory levels (common pattern)

Typical levels:

- `"session"` – memory is scoped per chat session.
- `"user"` – memory is scoped per user across sessions.

Example:

```python
@graph_fn(
    name="assistant_agent",
    as_agent={
        "id": "assistant",
        "title": "Assistant",
        "memory_level": "session",   # one memory store per chat session
        "memory_scope": "assistant.main",
    },
)
async def assistant_agent(..., *, context):
    ...
```

### 7.2 Memory scope: a namespace *within* the level

`memory_scope` is a **logical namespace inside the chosen level**.

You can think of it as:

> **Memory = f(memory_level, memory_scope, user/session)**

Some examples:

- `memory_level="session", memory_scope="assistant.main"`  
  → Each session gets its own “assistant.main” store.
- `memory_level="user", memory_scope="assistant.main"`  
  → Same assistant memory shared across sessions for the same user.
- `memory_level="user", memory_scope="assistant.research"`  
  → A separate research-specific store per user.

Scopes are just strings; using dotted names (`"assistant.main"`, `"planner.global"`) keeps things tidy.

> A useful mental model: **scope is a subset within a level.**  
> For example, multiple agents in the same session can intentionally share a `memory_scope`,
> while using `memory_level="session"` to ensure that memory is not persisted beyond that session.

---

## 8. Summary

- **Agents**: chat entrypoints based on `graph_fn` with a fixed chat signature. Use them as thin routers that spawn real work into graphs.
- **Apps**: click-to-run flows, ideally `graphify` graphs, for launch-and-observe workflows.
- **Minimal meta**:
    - Agents: `as_agent={"id": "...", "title": "..."}` is enough.
    - Apps: `as_app={"id": "...", "name": "..."}` is enough.
- **Best practices**:
    - Keep agents lean and orchestrate via `spawn_run`.
    - Use `graphify` for flows you want to observe and resume.
    - Configure `memory_level` and `memory_scope` so that related agents share the right subset of memory (within a session, or across sessions for a user).
    - Expect the details around file handling and `context_refs` to evolve; the high-level pattern (UI selects things, agent receives them as parameters) will stay stable.

For source / deployment caveats and current limitations, see [UI notes](ui-notes.md).
