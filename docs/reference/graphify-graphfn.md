# `@graphify` and `graph_fn` — Convert Python Functions to Graphs


## Introduction

This document explains how to use the `@graphify` decorator and the `graph_fn` function to convert Python functions into executable graphs within the Aethergraph framework. These tools enable you to define, orchestrate, and manage complex workflows as graphs, making it easier to build modular agents and applications. You will also learn how to provide metadata for agents and apps, and how these components interact with the Aethergraph UI.

---

## 1. Core APIs

The `@graphify` decorator defines a `TaskGraph`, where each node must be annotated with `@tool`. When a `TaskGraph` is triggered, all execution traces are preserved, and the graph can be resumed automatically if a `run_id` is provided. Note that direct invocation of subgraphs or nested graphs within a `TaskGraph` is not supported; instead, use `context.spawn_run(...)` or other context runner methods to launch nested graphs.

In contrast, `@graph_fn` offers a more intuitive way to define a graph from a standard Python function. It converts a Python function—typically one that accepts a `context` parameter—into an executable graph. You can run the resulting graph as you would any async Python function, and you can nest subgraphs using `run`, `async_run`, or `context.spawn_run(...)`. However, be aware that concurrency limits may not be enforced if you invoke the graph directly using native Python calls (e.g., `await my_fn(...)`).

??? quote "@graphify(name, inputs, outputs, version, ... )"
    ::: aethergraph.core.graph.graphify.graphify
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "@graph_fn(name, inputs, outputs, version, *, ...)"
    ::: aethergraph.core.graph.graph_fn.graph_fn
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

## 2. Agent/App Metadata
When using agents with Aethergraph, you must declare the __entry graph__ as either an `agent` or an `app`.

An **agent** is triggered by a Workspace message and requires the following input signature:

```python
@graph_fn(
    name="my_agent",
    inputs=["message", "files", "context_refs", "session_id", "user_meta"],
    # outputs can be arbitrary
    as_agent={
        id="...",
        title="My Agent",         # Displayed in the Avatar
        mode="chat_v1",           # Specifies as a session workspace agent
        run_visibility="inline",  # "inline" hides run status
        memory_level="session",   # "user" | "session" | "run", etc.
    }
)
```

You do not need to start the agent manually using `run` or `run_async`; the UI will automatically trigger the agent with the following default attributes:

- `message`: The message sent from the UI.
- `files`: Attached files from the UI, parsed as `FileRef`.
- `context_refs`: Artifact links from the UI, typically a list of dicts with `artifact_id`.
- `session_id`: Convenient access to the session ID (same as `context.session_id`).
- `user_meta`: Currently not in use.

It is recommended to use `graph_fn` for agents to enable dynamic routing and orchestration. For better UI responsiveness, use `context.spawn_run(...)` to launch other agents or graphs. You do not need to invoke `app` graphs from within agents.

An **app** is a reusable graph listed in the Aethergraph UI. Apps are typically single graphs without direct inputs. If you need to collect inputs, use `context.ui_run_channel().ask_text(...)` or other `ask_*` methods to prompt for arguments.

It is recommended to use `graphify` for apps. The `graphify` decorator allows all node execution statuses to be displayed in the UI, and the app can be terminated manually.

??? quote "`as_agent` meta keys"
    ::: aethergraph.services.registry.agent_app_meta.AgentConfig
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  
            members: []

??? quote "`as_app` meta keys"
    ::: aethergraph.services.registry.agent_app_meta.AppConfig
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  
            members: []
