#  Graph Function `graph_fn` Quickstart & Reference

Make any Python async function a runnable, inspectable **Graph Function** with a single decorator. You keep normal Python control‑flow; AetherGraph wires in runtime services via `context` and exposes your outputs as graph boundaries.

---

## TL;DR
```python
from aethergraph import graph_fn

@graph_fn(name="hello")
async def hello(name: str, *, context):
    await context.channel().send_text(f"Hi {name}! 👋")
    return {"greeting": f"Hello, {name}"}

# Run (async)
res = await hello(name="Aether")          # → {"greeting": "Hello, Aether"}

# Or run (sync) for quick scripts
out = hello.sync(name="Aether")            # same result
```

---

## What is a Graph Function?
A **Graph Function** is a small wrapper around your Python function that:

- builds a fresh internal TaskGraph,

- injects a `NodeContext` if your function declares `*, context`,

- executes your function (awaiting if needed),

- normalizes the return value into named outputs, and

- records graph boundary outputs for downstream composition/inspection.

You do **not** need to learn a new DSL. Write Python; use `context.<service>()` when you need IO/state.

---

## Decorator signature
```python
@graph_fn(
    name: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    version: str = "0.1.0",
    agent: str | None = None,  # optional: also register as an agent name
)
```

**Required**

- **name** (*str*) – Unique identifier for this graph function.

**Optional**

- **inputs** (*list[str]*) – Declares input names for docs/registry (not enforced at call time).

- **outputs** (*list[str]*) – Declares output names/order; enables single‑literal returns.

- **version** (*str*) – Semantic version for registry/discovery.

- **agent** (*str*) – Also register in the `agent` namespace (advanced).

---

## Function shape
```python
@graph_fn(name="example", inputs=["x"], outputs=["y"])
async def example(x: int, *, context):
    # use services via context: channel/memory/artifacts/kv/llm/rag/mcp/logger
    await context.channel().send_text(f"x={x}")
    return {"y": x + 1}
```
- Positional/keyword parameters are **your** API.

- Include `*, context` to receive the `NodeContext`. If you don’t declare it, nothing is injected.

---

## Returning values (normalization rules)
Your return can be:

1) **Dict of outputs** (recommended)
```python
return {"result": 42, "note": "ok"}
```

2) **Single literal** — only if you declared **exactly one** output
```python
@graph_fn(name="one", outputs=["y"])
async def one(*, context):
    return 123  # normalized to {"y": 123}
```

3) **NodeHandle / Refs** (advanced)
If you return node handles or refs created by graph utilities, they’re exposed as boundary outputs automatically. For most users, plain dicts/literals are enough.

**Validation**
- If `outputs` are declared, missing keys raise: `ValueError("Missing declared outputs: ...")`.
- Returning a single literal without exactly one declared output raises an error.

---

## Running
```python
# Async (preferred in apps/servers)
res = await my_fn(a=1, b=2)

# Sync helper (scripts/CLI/tests)
out = my_fn.sync(a=1, b=2)
```
Internally this builds a fresh runtime environment, constructs a TaskGraph, executes your function in an interpreter, and returns the normalized outputs.

---

## Accessing Context
Declare `*, context` to use built‑ins:
```python
@graph_fn(name="report", outputs=["uri"])
async def report(data: dict, *, context):
    # Log breadcrumbs
    log = context.logger(); log.info("building report")

    # Save an artifact
    art = await context.artifacts().save(path="/tmp/report.pdf", kind="report", labels={"exp":"A"})

    # Record a typed result in memory
    await context.memory().write_result(topic="report", outputs=[{"name":"uri","kind":"uri","value": art.uri}])

    # Notify user
    await context.channel().send_text(f"Report ready: {art.uri}")
    return {"uri": art.uri}
```

---

## Concurrency & retry (advanced)
`GraphFunction.run()` accepts knobs used by the interpreter/runtime:
```python
await my_fn.run(
    env=None,                            # supply a prebuilt RuntimeEnv, or let the runner build one
    retry=RetryPolicy(),                 # backoff/retries for node execution
    max_concurrency: int | None = None,  # cap parallelism inside the interpreter
    **inputs,
)
```
For most users, calling `await my_fn(...)` / `.sync(...)` is sufficient; the runner chooses sensible defaults.

---

## Minimal patterns
**Hello + context**
```python
@graph_fn(name="hello")
async def hello(name: str, *, context):
    await context.channel().send_text(f"Hi {name}")
    return {"greeting": f"Hello, {name}"}
```

**One output (literal)**
```python
@graph_fn(name="square", outputs=["y"])
async def square(x: int, *, context):
    return x * x
```

**Multi‑output dict**
```python
@graph_fn(name="stats", outputs=["mean","std"])
async def stats(xs: list[float], *, context):
    import statistics as st
    return {"mean": st.mean(xs), "std": st.pstdev(xs)}
```

---

## Tips & gotchas
- Always include `*, context` when you need services (channel/memory/llm/etc.).
- Declare `outputs=[...]` if you want to return a single literal; otherwise return a dict.
- Output validation is strict when `outputs` are declared—return all of them.
- `inputs=[...]` is for documentation/registry; your Python signature is the source of truth at call time.
- You can also register the function as an **agent** by passing `agent="name"` (covered later).

---

## Next steps
- **`graphify`**: combine multiple functions into a larger graph with explicit edges.
- **`@tool`**: publish functions as reusable nodes (IO typed), then orchestrate with `graphify`.
- **Context services**: `channel`, `artifacts`, `memory`, `kv`, `llm`, `rag`, `m