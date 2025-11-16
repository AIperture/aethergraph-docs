# `context.logger()` – Contextual Logger API Reference

`context.logger()` returns a **Logger** already bound to the current run/node (and graph when available). It exposes the standard Python logging methods and injects structured fields like `run_id`, `node_id`, and `graph_id` into every record.

> Configuration is set when you start the sidecar: 
```python
from aethergraph import start_server; 

(log_level="warning", ...)
``` 
The runtime also honors environment/app settings (e.g., JSON vs text, rotating files, per‑namespace levels).

---

## What’s included per log record

* `run_id`, `node_id`, `graph_id` (when available)
* Logger namespace (e.g., `aethergraph.node.<id>`)
* Message, level, timestamp, optional `metrics`/custom fields via `extra={...}`

---

## Quick Reference

| Method                            | Purpose                  | Inputs                          | Notes                                      |
| --------------------------------- | ------------------------ | ------------------------------- | ------------------------------------------ |
| `debug(msg, *args, **kwargs)`     | Verbose diagnostic       | `msg: str`, `*args`, `**kwargs` | Use for high‑volume internals.             |
| `info(msg, *args, **kwargs)`      | Normal operational logs  | `msg: str`, `*args`, `**kwargs` | Default level often shows this.            |
| `warning(msg, *args, **kwargs)`   | Non‑fatal issues         | `msg: str`, `*args`, `**kwargs` | Alias: `warn()` in stdlib (deprecated).    |
| `error(msg, *args, **kwargs)`     | Errors that didn’t crash | `msg: str`, `*args`, `**kwargs` | Consider `exc_info=True` for tracebacks.   |
| `exception(msg, *args, **kwargs)` | Error with traceback     | `msg: str`, `*args`, `**kwargs` | Equivalent to `error(..., exc_info=True)`. |
| `critical(msg, *args, **kwargs)`  | Severe/fatal conditions  | `msg: str`, `*args`, `**kwargs` | Might trigger alerts depending on sink.    |

**Common kwargs**

* `extra: dict` — Attach structured fields (merged with contextual fields).
* `exc_info: bool | BaseException` — Include traceback.

---

## Methods

<details markdown="1">
<summary>debug(msg, *args, **kwargs) -> None</summary>

**Description:** Emit a DEBUG‑level message.

**Inputs:**

* `msg: str`
* `*args` – `%`‑style parameters if you use `%` formatting in `msg`.
* `**kwargs` – e.g., `extra`, `exc_info`.

**Returns:**

* `None`

**Notes:** Evaluated lazily by the logging framework; cheap when DEBUG is disabled.

</details>

<details markdown="1">
<summary>info(msg, *args, **kwargs) -> None</summary>

**Description:** Emit an INFO‑level message for normal operations.

**Inputs:**

* `msg: str`
* `*args`, `**kwargs`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>warning(msg, *args, **kwargs) -> None</summary>

**Description:** Emit a WARNING‑level message for recoverable anomalies.

**Inputs:**

* `msg: str`
* `*args`, `**kwargs`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>error(msg, *args, **kwargs) -> None</summary>

**Description:** Emit an ERROR‑level message when something failed but execution continues.

**Inputs:**

* `msg: str`
* `*args`, `**kwargs` (consider `exc_info=True`)

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>exception(msg, *args, **kwargs) -> None</summary>

**Description:** Shortcut for logging an exception with traceback.

**Inputs:**

* `msg: str`
* `*args`, `**kwargs`

**Returns:**

* `None`

**Notes:** Same as `error(msg, exc_info=True)`.

</details>

<details markdown="1">
<summary>critical(msg, *args, **kwargs) -> None</summary>

**Description:** Emit a CRITICAL‑level message for severe failures.

**Inputs:**

* `msg: str`
* `*args`, `**kwargs`

**Returns:**

* `None`

</details>

---

## Configuration & Behavior

* **Startup:** `start_server(log_level="warning", ...)` sets console verbosity. File sinks, JSON formatting, and per‑namespace levels can be configured via app/env settings (`LoggingConfig`).
* **Context injection:** The logger is an adapter that auto‑merges contextual fields with any `extra` you pass.
* **Formatting:** Console is human‑readable; file logs may be text or JSON depending on configuration.
* **External noise control:** Some noisy third‑party namespaces are down‑leveled by default.

---

## Examples

```python
# Get a contextual logger inside a node/tool
log = context.logger()

log.info("starting phase %s", "A", extra={"phase": "A", "metrics": {"step": 1}})

try:
    do_risky_thing()
except Exception:
    log.exception("risky thing failed")

log.debug("intermediate state", extra={"cache_hit": True})
log.warning("fallback engaged")
log.error("partial write; retrying", extra={"retry_in": 2.5})
```

**Result:** Each record includes `run_id`, `node_id`, and (when available) `graph_id`, enabling easy correlation across tools and services.
