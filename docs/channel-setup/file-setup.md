# File Channel Overview

The **file channel** is a simple, one-way output channel that writes messages from AetherGraph directly to files on disk.

## When to use the file channel

Use the file channel when you want to:

* Keep a **persistent log** of what a graph did (steps, status, results).
* Save **run transcripts** for later inspection, papers, or debugging.
* Capture output in a way that can be easily opened with any text editor.

It’s ideal for individual researchers who want lightweight, local logging without setting up external services.

## Where files are written

In this setup, the file channel writes under:

```text
<workspace>/channel_files
```

* `<workspace>` is the root directory you configured for AetherGraph.
* Inside `channel_files`, the rest of the path is taken from your channel key.

For example, if your workspace is `./aethergraph_data` and you use:

```python
chan = context.channel("file:runs/demo_run.log")
await chan.send_text("Demo run started")
```

The message will be appended to:

```text
./aethergraph_data/channel_files/runs/demo_run.log
```

You can define any relative path after `file:` (e.g., `file:logs/experiment_01.txt`), and AetherGraph will create the parent directories if needed.

This makes it easy to organize logs by project, experiment, or date while keeping everything local to your workspace.
