# `context.logger()` – Contextual Logger API Reference

The `context.logger()` function returns a **Logger** instance automatically bound to the current run, node, and, when available, graph context. This logger provides the standard Python logging interface, while automatically injecting structured fields such as `run_id`, `node_id`, and `graph_id` into every log record.

> **Configuration:**  
> Set logging options when starting the sidecar:
> ```python
> from aethergraph import start_server
>
> start_server(log_level="warning", ...)
> ```
> The runtime also respects environment and application settings (e.g., JSON vs. text output, log rotation, per-namespace log levels).

---

## Log Record Fields

Each log record includes:

- `run_id`, `node_id`, `graph_id` (when available)
- Logger namespace (e.g., `aethergraph.node.<id>`)
- Message, level, timestamp
- Optional `metrics` or custom fields via `extra={...}`

---

## Quick Reference: Logger Methods

Use the logger as you would a standard Python `Logger`:

| Method                            | Purpose                  | Inputs                          | Notes                                      |
| --------------------------------- | ------------------------ | ------------------------------- | ------------------------------------------ |
| `debug(msg, *args, **kwargs)`     | Verbose diagnostics      | `msg: str`, `*args`, `**kwargs` | For high-volume internal logs.             |
| `info(msg, *args, **kwargs)`      | General information      | `msg: str`, `*args`, `**kwargs` | Default level; typically visible.          |
| `warning(msg, *args, **kwargs)`   | Non-fatal issues         | `msg: str`, `*args`, `**kwargs` | Alias: `warn()` (deprecated in stdlib).    |
| `error(msg, *args, **kwargs)`     | Recoverable errors       | `msg: str`, `*args`, `**kwargs` | Use `exc_info=True` for tracebacks.        |
| `exception(msg, *args, **kwargs)` | Error with traceback     | `msg: str`, `*args`, `**kwargs` | Same as `error(..., exc_info=True)`.       |
| `critical(msg, *args, **kwargs)`  | Severe/fatal conditions  | `msg: str`, `*args`, `**kwargs` | May trigger alerts depending on sink.      |

**Common `kwargs`:**

- `extra: dict` — Attach additional structured fields (merged with contextual fields).
- `exc_info: bool | BaseException` — Include exception traceback.

