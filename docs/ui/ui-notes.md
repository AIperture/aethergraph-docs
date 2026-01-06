# UI Notes, Limitations, and Common Pitfalls

This page collects practical notes and “gotchas” around the AetherGraph UI:

- Running from source vs PyPI
- Auto-reload and development workflow
- Project roots, modules, and imports
- Memory levels and scopes (quick reference)
- Current limitations and things that may change

---

## 1. Running from source vs PyPI

If you install AetherGraph from **PyPI**:

- The package ships with a prebuilt UI bundle.
- `/ui` should work out of the box.

If you run from **source**:

- The repo expects a built frontend bundle under:  
  `aethergraph/server/ui_static/`
- Until that bundle exists, hitting `/ui` will return a `501` with a message like:
  > "UI bundle not found. Please build the frontend and copy it to ui_static."

In that case, either:

- Install from PyPI for local development, or
- Build the frontend from source and copy the resulting static files into `ui_static/`.

---

## 2. Auto-reload and development workflow

For day-to-day development, prefer:

```bash
aethergraph serve --project-root . --load-module demos --reload
```

This will:

- Watch your Python files for changes.
- Restart the server when graphs change.
- Let you refresh the UI and see new graphs, agents, and apps without manual restarts.

The scripted `start_server(...)` path is **better for embedding** AetherGraph into another app, but does **not** enable uvicorn’s auto-reload by default.

---

## 3. Project roots, modules, and imports

Common pitfalls when the UI shows “no apps” or “no agents”:

1. **Module not importable**  
    - Ensure your `--project-root` or `project_root` is correct.
    - Confirm `python -c "import demos_clean"` works from that directory.

2. **Missing `__init__.py`**  
    - For packages like `demos_clean`, ensure `__init__.py` exists.

3. **Forgot `as_app` / `as_agent`**  
    - Graphs only appear in the App Gallery if they have `as_app={...}`.
    - Agents only appear in the Agent Gallery if they have `as_agent={...}` and are defined via `graph_fn`.

4. **Load flags mismatch**  
    - If you use `--load-path`, make sure you are pointing at the actual files that define your graphs/agents.
    - If you use `--load-module`, ensure the module name matches the package structure.

---

## 4. Memory levels and scopes (quick reference)

You configure agent memory via `as_agent`:

```python
as_agent={
    "id": "assistant",
    "title": "Assistant",
    "memory_level": "session",   # or "user"
    "memory_scope": "assistant.main",
}
```

- `memory_level` controls the **outer scope**:
    - `"session"` → memory is tied to a single chat session.
    - `"user"` → memory is tied to a user across sessions.

- `memory_scope` is a **namespace within that level**:
    - Multiple agents can share a `memory_scope` if you want them to see the same memory subset.
    - Or you can split scopes (`"assistant.main"`, `"assistant.research"`) for the same user/session.
    - You can totally ignore memory_scope if you want all agents see the memory in the same level.

A good default:

- For typical chat agents: `memory_level="session"`.
- For long-lived personalization: `memory_level="user"`.
- For specialized agents: `memory_level="sessin", memory_scope="assistant.simulation"` 

---

## 5. Current limitations and evolving APIs

A few things are intentionally still evolving:

### 5.1 Run outputs via `RunRecord`

Today:

- `context.spawn_run()` returns a `run_id`.
- `record = await context.wait_run(run_id)` returns a `RunRecord` with metadata (status, timestamps, etc.).
- Outputs are not yet exposed directly from `RunRecord`.

Workaround patterns:

- Use artifacts as the output contract (e.g., JSON, CSV, reports written via the artifact store).
- Use memory to persist important “results” that future runs or agents can read.

The API here is expected to expand over time; check the changelog for updates.

---

### 5.2 Files and `context_refs`

The exact structure of:

- `files` (upload payloads), and
- `context_refs` (references to selected files/artifacts/runs)

may change as the UI gains:

- Richer file browsing and selection
- Cross-run artifact linking
- More flexible context passing

The stable part is:

- Agents defined with `mode="chat_v1"` take these parameters.
- The UI will always pass in a consistent structure that the backend understands.

---

## 6. Checklist: “Why is nothing showing up in the UI?”

If you open `/ui` and see an empty App Gallery or Agent Gallery, check:

1. Did you start the server with `--load-module` or `--load-path` pointing at your code?
2. Is your module importable under `--project-root`?
3. Did you mark at least one graph with `as_app={...}`?
4. Did you define at least one `graph_fn` with `as_agent={...}` and the correct chat signature?
5. Are there any import errors in the server logs?
6. If running from source, did you build or copy the UI bundle into `ui_static/`?

If all else fails, try a minimal example:

- New project dir
- Single `demos_clean` package
- One `@graphify(..., as_app=...)`
- Start with the dev command from [Start the server](server.md)

Once that works, gradually move back to your full project.
