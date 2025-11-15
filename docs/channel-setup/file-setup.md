# File Channel Setup

The **file channel** is a simple, one‑way output channel that appends messages from AetherGraph to **files on disk**.

✅ **No setup required** — writes under your workspace `workspace/channel_files`.

🗂️ **Key format:** `file:<relative/path/to/file>`

---

## When to Use

* Persistent, local **run logs** (steps, status, results) with custom format
* **Transcripts** for papers/debugging
* Plain‑text output you can open with any editor

---

## Where Files Are Written

Files are created under:

```
<workspace>/channel_files
```

* `<workspace>` is your AetherGraph data root.
* The portion **after** `file:` becomes a **relative path** under `channel_files`.

**Example**

```python
chan = context.channel("file:runs/demo_run.log")
await chan.send_text("Demo run started")
```

Writes (appends) to:

```
<workspace>/channel_files/runs/demo_run.log
```

Parent directories are created automatically.

---

## Usage

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="file_channel_demo")
async def file_channel_demo(*, context: NodeContext):
    chan = context.channel("file:logs/experiment_01.txt")
    await chan.send_text("Run began")
    await chan.send_text("Metric: acc=0.93, loss=0.12")
    return {"logged": True}
```

---

## Notes

* **One‑way**: no `ask_*` prompts (write‑only).
* **Append behavior**: messages are appended; rotate/cleanup as needed.
* **Organization tip**: include date/run IDs in paths (e.g., `file:runs/2025-11-15/expA.txt`).
