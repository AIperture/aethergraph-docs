# AetherGraph UI + Sidecar Server Tutorial

This guide walks through how to:

* Start the AetherGraph sidecar server (from **terminal** and **Python script**).
* Define **Apps** with `@graphify(..., as_app={...})` so they show up in the App Gallery.
* Define **chat Agents** with `@graph_fn(..., as_agent={...})` so they show up in the Agent Gallery.
* Wire the server and frontend together.
* Follow a few **best practices** so the UI feels fast and responsive.

> This tutorial uses the `chat_with_memory_demo` app and a `lead_agent` example for agents.

---

## 1. Core concepts

AetherGraph is split into two main pieces:

1. **Sidecar server (FastAPI + Uvicorn)**

   * Hosts APIs for runs, sessions, artifacts, memory, etc.
   * Loads your graphs, apps, and agents from Python modules.

2. **AetherGraph UI (React app)**

   * Talks to the sidecar over HTTP.
   * Shows **App Gallery** (for `as_app`) and **Agent Gallery** (for `as_agent`).

You can run the server either:

* From the **CLI**: `python -m aethergraph serve ...` (good for the UI / demos).
* From a **Python script or notebook**: `start_server(...)` (good for local hacking or embedding).

Both approaches use the same underlying server.

---

## 2. Starting the server from the terminal (CLI)

The CLI entrypoint is `python -m aethergraph`. The `serve` subcommand starts the sidecar.

Minimal example:

```bash
python -m aethergraph serve \
  --project-root . \
  --load-path demo_examples/1_chat_with_memory.py
```


Typical dev setup for the UI:

```bash
# From the project root
python -m aethergraph serve \
  --host 127.0.0.1 \
  --port 8000 \
  --project-root . \
  --load-path demo_examples/1_chat_with_memory.py \
  --load-path demo_examples/2_design_review.py \
  --reuse
```
See [server API](../reference/runtime-server.md) for complete docs.

The command prints the API URL, e.g.:

```text
http://127.0.0.1:8000
```

The React UI should be configured to talk to this URL.


### Stopping the CLI server

When you start via CLI, the process runs **blocking**. You can stop it with `Ctrl+C`.

The workspace also keeps a lightweight `server.json` with the host, port, and PID. The `--reuse` flag uses this to avoid spawning multiple servers for the same workspace.

---

## 3. Starting the server from a Python script or notebook

For programmatic usage (scripts, notebooks, tests), you can use the helper functions in `aethergraph.server.startup`:

```python
from aethergraph.server import start_server

if __name__ == "__main__":
    url, handle = start_server(
        port=8000,  # match your UI config
        project_root=".",
        load_paths=["demo_examples/1_chat_with_memory.py"],
        return_handle=True,
    )

    print("Server running at", url)

    try:
        # Block until interrupted
        handle.block()
    except KeyboardInterrupt:
        print("\nStopping server...")
        handle.stop()
```

Notes:

* `start_server(...)` starts Uvicorn in a **background thread** and returns `(url, handle)`.
* `handle.block()` joins that thread (useful in scripts / `__main__`).
* `handle.stop()` sets `server.should_exit = True` and waits for shutdown.

See [server API](../reference/runtime-server.md) for complete docs.


## 4. Defining Apps with `@graphify(..., as_app=...)`

**Apps** are static graphs you can launch from the **App Gallery** in the AG UI. They:

* Don’t take direct chat input.
* Are usually “pipelines” with a fixed DAG.
* Can still interact with users via channels inside tools.

### Example: `chat_with_memory_demo`

```python
@graphify(
    name="chat_with_memory_demo",
    inputs=[],                       # <-- no inputs, easy to run from UI
    outputs=["turns", "summary"],
    as_app={
        "id": "chat_with_memory_demo",
        "name": "Chat with Memory",
    },
)
def chat_with_memory_demo():
    ... # your workflow 
    return {
        "turns": ...,
        "summary": ...,
    }
```

Important points:

| Field            | Purpose / Notes                                                                                                      |
|------------------|----------------------------------------------------------------------------------------------------------------------|
| `inputs=[]`      | Apps in the UI are easier to run if they don’t require explicit inputs. Use channels (e.g. `context.channel()`) inside the graph to collect dynamic user input. |
| `outputs=[...]`  | Named outputs become fields on the run result and can be surfaced in the UI.                                         |
| `as_app={...}`   | This metadata makes the graph appear in the **App Gallery**.                                                         |
| &nbsp;&nbsp;• `id`   | Stable slug used by the backend and UI. Don’t change it once shipped.                                                |
| &nbsp;&nbsp;• `name` | Human-facing display name in the App Gallery.                                                                       |
| &nbsp;&nbsp;• (optional UX fields) | `short_description`, `badge`, `category`, `icon_key`, `features`, `githubUrl`. See full meta definition [here](../reference/graphify-graphfn.md). |


Once the module containing this graph is loaded by the server (`--load-path` or `--load-module`), the UI will show "Chat with Memory" in the App Gallery.

---

## 5. Defining chat Agents with `@graph_fn(..., as_agent=...)`

**Agents** are chat-oriented nodes that appear in the **Agent Gallery** and can be used in chat sessions.

They are implemented as `@graph_fn` functions with a fixed signature that the UI expects.

### Required input signature

A chat agent should look like this:

```python
@graph_fn(
    name="lead_agent",
    inputs=["message", "files", "context_refs", "session_id", "user_meta"],
    outputs=["reply"],
    as_agent={
        "id": "lead",
        "title": "Design Lead",
        "run_visibility": "inline",
        "memory_level": "session",      # use session-scoped memory
        "memory_scope": "role:lead",    # suffix for mem scope id
    },
)
async def lead_agent(
    message: str,
    files: Optional[list[Any]] = None,
    session_id: Optional[str] = None,
    user_meta: Optional[dict[str, Any]] = None,
    context_refs: Optional[list[dict[str, Any]]] = None,
    *,
    context: NodeContext,
) -> dict[str, Any]:
    ...
    return {"reply": reply_text}
```

The inputs list and the function parameters must match:


| Parameter      | Type                          | Description                                                                                                                      |
|----------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `message`      | `str`                         | The latest user message in the current chat turn.                                                                                |
| `files`        | `Optional[list[Any]]`         | Files uploaded with this message (if any). You can ignore it if you don’t support file inputs yet.                               |
| `context_refs` | `Optional[list[dict[str, Any]]]` | References to prior runs, artifacts, or other context objects (optional).                                                        |
| `session_id`   | `Optional[str]`               | Stable ID for this chat session. Combine this with `memory_level` and `memory_scope` to get good memory behavior.               |
| `user_meta`    | `Optional[dict[str, Any]]`    | Extra metadata about the user (role, permissions, etc.) if needed.                                                               |
| `context`      | `NodeContext` (keyword-only)  | Gives you access to services: LLMs, memory, artifacts, channels, `spawn_run`, etc.                                              |

The `as_agent={...}` block is what makes this graph function show up in the **Agent Gallery**. Critical fields to care about:

| Field           | Description                                                                                                                                                                                                                  |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `id`            | Stable identifier for the agent. This is how the backend and UI refer to it. Don’t change it casually.                                                                               |
| `title`         | Display name in the Agent Gallery.                                                                                                                                                    |
| `run_visibility`| Controls how this agent’s runs show up in the UI. For most chat agents, `"normal"` is preferred so the user can see tool runs and subgraphs alongside the conversation.               |
| `memory_level`  | How much memory the agent gets:<br>• `"none"` – no persistent memory.<br>• `"session"` – remember within a single chat session.<br>• `"global"` – share memory across sessions.<br>For chat agents that should remember context per conversation, `"session"` is usually the sweet spot. |
| `memory_scope`  | Namespace for memory within a level. For example, `"role:lead"` keeps the lead agent’s memory separate from other roles.                                                              |

Other fields like `description`, `icon`, `color`, `tool_graphs`, etc. improve UX but are not critical for wiring. see full meta definition [here](../reference/graphify-graphfn.md).


### Where do agents show up?

Once the module defining `lead_agent` is loaded by the server, the UI will:

* Display it in the **Agent Gallery**.
* Allow you to start chat sessions using that agent.

---

## 6. Making sure the server loads your apps and agents

The server only knows about graphs, apps, and agents if the Python module that defines them is imported.

With the CLI, you have two main options:

### Option A: `--load-path` (scripts by path)

```bash
python -m aethergraph serve \
  --workspace ./aethergraph_data \
  --project-root . \
  --load-path demo_examples/1_chat_with_memory.py \
  --load-path demo_examples/2_design_review.py
```

This is convenient if you want to refer to specific files.

### Option B: `--load-module` (importable modules)

If your examples are laid out as a package, you can do:

```bash
python -m aethergraph serve \
  --workspace ./aethergraph_data \
  --project-root . \
  --load-module demo_examples.chat_with_memory \
  --load-module demo_examples.design_review
```

In both cases:

* Any `@graphify(..., as_app=...)` graph becomes an **App** in the UI.
* Any `@graph_fn(..., as_agent=...)` function becomes an **Agent** in the UI.

When starting the server programmatically (`start_server(...)`), you pass equivalent `load_modules` / `load_paths` arguments.

---

## 7. Hooking up the AetherGraph UI

The React UI needs to know the sidecar base URL. Typically this is controlled by a Vite env variable such as:

```bash
VITE_AG_SERVER_URL=http://127.0.0.1:8000
```

(or whatever name you use in your frontend; adjust accordingly.)

A typical dev setup is:

1. Start the server:

   ```bash
   python -m aethergraph serve \
     --workspace ./aethergraph_data \
     --host 127.0.0.1 \
     --port 8000 \
     --project-root . \
     --load-path demo_examples/1_chat_with_memory.py \
     --load-path demo_examples/2_design_review.py \
     --reuse
   ```

2. Start the UI:
    Simply lauch the app, and in `Setting` change the server as `127.0.0.1:8000`. 

In most of the cases, the frontend should have the same backend server address by default. 

---

## 8. Best practices for defining agents and apps

### 8.1 Keep Apps input-free and use channels

For Apps, prefer:

* `inputs=[]` in `@graphify`.
* Collect dynamic information via channels inside the graph:

  ```python
  ui = context.channel()
  user_prompt = await ui.ask_text("What would you like to chat about?")
  ```

This makes Apps easy to launch from the UI with a single "Run" button.

### 8.2 Use `spawn_run` for heavy work

For chat agents, you don’t want the user to wait while a huge simulation or optimization blocks the reply.

Instead:

* Have the agent send a quick reply.
* Use `context.spawn_run(...)` (or equivalent) to kick off longer-running graphs in the background.

Pattern:

```python
async def lead_agent(..., context: NodeContext) -> dict[str, Any]:
    # 1) Parse the user request
    plan = ...

    # 2) Spawn a longer pipeline run (non-blocking)
    await context.spawn_run(
        graph_name="design_sim_pipeline",
        inputs={"spec": plan.spec},
        importance="normal",
    )

    # 3) Immediately reply in chat
    reply = "Got it. I’ve kicked off a simulation run; I’ll summarize the results when it finishes."
    return {"reply": reply}
```

This keeps the chat responsive and allows the UI to show the spawned run in the timeline.

### 8.3 Be deliberate with `memory_level` and `memory_scope`

For each agent:

* Ask: *Should this agent remember things across turns? Across sessions? Ever?*

Guidance:

* Use `memory_level="session"` for most chat agents. They remember within a single chat session, which matches user expectations.
* Use `memory_level="global"` only for agents that truly need cross-session memory.
* Use `memory_scope` to separate roles, e.g. `role:lead`, `role:designer`, so they don’t step on each other’s memories.

### 8.4 Keep IDs stable

* `as_app.id` and `as_agent.id` should be treated like persistent IDs.
  Changing them will break existing saved runs / bookmarks and may confuse the UI.

### 8.5 Group definitions into clean modules

It’s often helpful to:

* Put each demo in its own module or file (`demo_examples/1_chat_with_memory.py`, `demo_examples/2_design_review.py`, etc.).
* Keep the `@graphify(..., as_app=...)` definition close to the actual tool/graph pipeline it uses.
* Keep agents that cooperate (e.g. Design Lead, Optical Designer, Simulation Runner) in a single module with shared utilities.

This makes it straightforward to load them via `--load-module` or `--load-path` and to reason about what the UI will show.

---

## 9. Putting it all together

1. **Write your app and agent definitions** using `@graphify(..., as_app=...)` and `@graph_fn(..., as_agent=...)`.
2. **Start the sidecar server** via CLI or script, making sure to load the modules/files that define those graphs.
3. **Point the AG UI** at the server URL.
4. **Use Apps** for static pipelines that can gather inputs via channels.
5. **Use Agents** for interactive chat, with well-defined signatures and memory policies.
6. **Use `spawn_run`** from agents to kick off heavy graphs without blocking the chat reply.

With this structure, you get a clean separation between:

* The **agentic logic** (in your graphs and agents),
* The **sidecar runtime** (server + storage), and
* The **user experience** (AG UI),

while still keeping everything Python-first and composable.
