# Starting the AetherGraph Server with the Built-in UI

This guide walks through:

1. Installing / upgrading AetherGraph
2. Defining a project module for your graphs & apps
3. Starting the server from the terminal (recommended, with auto-reload)
4. Optionally starting the server from a Python script

Once the server is running, you’ll be able to open the UI at `/ui`. From there, you’ll see your **App Gallery**, **Agent Gallery**, **Runs**, **Sessions**, and **Artifacts**.

---

## 1. Install / upgrade AetherGraph

From your virtual environment:

```bash
pip install -U aethergraph
```

If you are working from the **source repo** instead:

```bash
# From the repo root
pip install -e .
```

> **Note**
> The published PyPI package includes a prebuilt UI bundle.
> If you run from source and haven’t built the UI, `/ui` will return a 501
> until you build the frontend and copy the bundle into `aethergraph/server/ui_static/`.
> See [UI notes](ui-notes.md#running-from-source-vs-pypi) for details.

---

## 2. Define a project module with graphs & apps

Create a project folder, for example:

```text
my_project/
  demos/
    __init__.py
    chat_demo.py
  aethergraph_data/   # workspace (created automatically as needed)
```

In `demos/chat_demo.py`, define a graph and expose it as an app so the UI can display it in the App Gallery:

```python
# demos/chat_demo.py
from aethergraph import graphify

@graphify(
    name="chat_with_memory_demo",
    inputs=[],
    outputs=["turns", "summary"],
    as_app={
        "id": "chat_with_memory_demo",
        "name": "Chat with Memory",
    },
)
def chat_with_memory_demo():
    # Your graph implementation here – tools, nodes, etc.
    ...
```

Key points:

- The module must be **importable** from your project root (e.g. `import demos` must work).
- `@graphify(..., as_app={...})` registers this graph as an **app**, so it appears in the UI.
- You can have multiple files and nested modules under `demos`; everything is imported when you pass `--load-module demos` to the server.

> Later, you can also add **agents** (chat endpoints) as `graph_fn` functions.
> See [Agents & Apps](agents-apps.md) for details.

---

## 3. Start the server from the terminal (recommended)

From your project root (the folder containing `demos/`), run:

### Minimal dev command

```bash
aethergraph serve --project-root . --load-module demos --reload
```

This will:

- Add `.` to `sys.path` so `demos` can be imported.
- Load all graphs / apps defined in the `demos` module.
- Start the API + UI server on `http://127.0.0.1:8745`.
- Enable **auto-reload**: editing your graph files triggers a server restart and reload of your graphs.

You should see output similar to:

```text
[AetherGraph] 🚀  Server started at: http://127.0.0.1:8745
[AetherGraph] 🖥️  UI:                http://127.0.0.1:8745/ui
[AetherGraph] 📡  API:               http://127.0.0.1:8745/api/v1/
[AetherGraph] 📂  Workspace:         ./aethergraph_data
[AetherGraph] ♻️  Auto-reload:       enabled
```

Now open:

- **UI:** `http://127.0.0.1:8745/ui` – App Gallery, Runs, Sessions, Artifacts, etc.
- **API:** `http://127.0.0.1:8745/api/v1/` – for direct API calls.

---

## 3.1 Common CLI flags

**Project / workspace**

- `--project-root PATH`  
  Root directory to temporarily add to `sys.path` when loading user graphs.  
  Default: `.` (current directory).

- `--workspace PATH`  
  Directory where runs, artifacts, and other state are stored.  
  Default: `./aethergraph_data`.

**Loading graphs**

- `--load-module NAME` (repeatable)  
  Python module(s) to import before the server starts.  
  Example: `--load-module demos` imports everything under `demos`.

- `--load-path PATH` (repeatable)  
  Python file(s) to load directly.  
  Example: `--load-path ./examples/my_graph.py`.

**Network / dev**

- `--host HOST` / `--port PORT`  
  Host and port to bind (e.g. `--host 0.0.0.0 --port 8745`).  
  Use `--port 0` to let the OS pick a free port.

- `--reload`  
  Enable uvicorn’s auto-reload. Any `.py` changes under the project root (and `--load-path` files) will restart the server and reload your graphs.  
  **Strongly recommended for local development and debugging.**

- `--strict-load`  
  If set, the server will abort on the first graph load error instead of continuing with partial results.

More gotchas and deployment tips: see [UI notes](ui-notes.md).

---

## 4. Starting the server from a Python script (optional)

You can also start the server from a Python script, for example to embed AetherGraph into your own launcher:

```python
# start_server.py
from aethergraph import start_server

if __name__ == "__main__":
    start_server(
        workspace="./aethergraph_data",
        project_root=".",
        load_module=["demos"],
        host="127.0.0.1",
        port=8745,
    )
```

Then run:

```bash
python start_server.py
```

This is convenient when you want to:

- Package AetherGraph inside a larger application.
- Start the server from an IDE run configuration.

> **For active development and debugging, the CLI with `--reload` is strongly recommended.**
>
> The scripted `start_server` path does not automatically enable uvicorn’s file-watching reload. With
> `aethergraph serve --reload`, you get a much smoother loop:
>
> 1. Edit graphs  
> 2. Uvicorn reloads the server  
> 3. Refresh the UI and see your changes immediately

Use `start_server` when you want a simple “embed AetherGraph in my program” story; use `aethergraph serve` for day-to-day graph and app development.
