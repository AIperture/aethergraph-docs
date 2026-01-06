# AetherGraph UI Overview

The AetherGraph UI gives you a **visual control panel** for your graphs, agents, and runs:

- Launch **apps** from an App Gallery (one-click flows).
- Chat with **agents** that orchestrate graphs behind the scenes.
- Inspect **runs**, **sessions**, and **artifacts**.
- Resume failed or partial runs (for `graphify` graphs).

This section of the docs covers:

1. [Start the server with the built-in UI](server.md)
2. [Expose agents and apps to the UI](agents-apps.md)
3. [Important notes and troubleshooting tips](ui-notes.md)

If you only use AetherGraph as a **Python library** (no UI), you can ignore this whole section and just import and run graphs from your own code.

---

## What the UI actually does

At a high level:

- The **server** exposes:
    - A **REST API**: `/api/v1/…`
    - A **static UI bundle**: `/ui`

- The **frontend** reads metadata about:
    - **Graphs** (`@graphify`) and **graph functions** (`@graph_fn`)
    - Anything marked with `as_app` or `as_agent`

- The **UI** then lets you:
    - Start runs (apps)
    - Start chat sessions (agents)
    - Inspect runs, sessions, memory, and artifacts

You control what appears in the UI by how you define your **project module**, **apps**, and **agents**. The next pages walk you through:

- [Starting the server](server.md)
- [Defining agents and apps for the UI](agents-apps.md)

---

## When should I use the UI?

Good use cases for the UI:

- You want **non-engineers** (or future you) to use your graphs without reading code.
- You want a visual **“lab notebook”**: runs, artifacts, and memory all tracked in one workspace.
- You want to **debug** complex flows with better observability and resumption.

Cases where the UI is optional:

- Fully automated backends where you call AetherGraph purely as a library.
- One-off scripts or small experiments where a CLI is enough.

If you’re unsure, start with the UI. It’s usually easier to wire up a graph once and then reuse it from both UI and code.
