# AetherGraph — `context.logger()` Quick Reference

`context.logger()` returns a **pre‑scoped Python `logging.Logger`** bound to the current run/graph/node via the project’s `StdLoggerService`.

- Namespace: `node.<node_id>`
- Extra context on every record: `{run_id, graph_id, node_id}`
- Outputs: console (text) + rotating file (`$LOG_DIR/aethergraph.log`), optional JSON, optional async QueueHandler

---

## Basics
```python
log = context.logger()
log.info("starting step")
log.debug("inputs", extra={"shape": [n, d]})
log.warning("retrying", extra={"attempt": i})
try:
    ...
except Exception:
    log.exception("failed tool call")  # includes traceback
```

**Returns**  
`logging.Logger` — fully configured for the current node/run.

---

## Formatting & levels (service defaults)
Configured by `StdLoggerService.build(cfg)` and `LoggingConfig`:

- Global level: `cfg.level` (e.g., `INFO`) with optional per‑namespace overrides
- Console formatter: `cfg.console_pattern`
- File formatter: text (`cfg.file_pattern`) or JSON (`cfg.use_json = True`)
- File rotation: `cfg.max_bytes`, `cfg.backup_count`
- Non‑blocking file I/O: `cfg.enable_queue = True` (QueueHandler + Listener)

> You can rebuild the service on server start to apply new settings.

---

## Structured fields
Every call accepts `extra={...}` for structured, searchable fields. The service injects `{run_id, graph_id, node_id}` automatically.
```python
log.info("optimizer step", extra={"lr": 3e-4, "batch": 64, "phase": "warmup"})
```

---

## Good practices
- Use `debug` for noisy internals; rely on `INFO` for milestone breadcrumbs.
- Prefer `extra={...}` over string concatenation for metrics/values.
- Use `exception()` within `except` blocks to capture tracebacks.
- Log artifact URIs (`extra={"artifact": uri}`) instead of large payloads.

---

## One‑liner pattern in tools
```python
from aethergraph import graph_fn

@graph_fn(name="demo")
async def demo(*, context):
    log = context.logger()
    log.info("hello", extra={"stage": "start"})
    # ... work ...
    log.info("done", extra={"duration_ms": 123})
```

---

## Summary
- Call `context.logger()` inside graph/tools for a scoped logger.
- Structured fields available via `extra={...}`; run/graph/node auto‑injected.

