# Choosing: `graph_fn` vs `@graphify` vs `@tool`

Use this one-screen guide to pick the right entry point.

## Start simple
- `@graph_fn` — quickest way to ship a working function with `context.*`. Add a couple of `@tool` calls inside if you want visible/inspectable steps.

## Scale up when needed
- `@graphify` — when you need explicit DAG control:
  - fan-out / fan-in / map-reduce
  - `_after` (barriers) and `_alias`/`_labels` for orchestration and UI
  - subgraph reuse and IO/spec inspection

## `@tool` is a building block
- Wrap any function to make it a typed node.
- Works in both: inside `@graph_fn` (immediate run, visible steps) and in `@graphify` (adds nodes to DAG).
- Control kwargs (`_after`, `_alias`, `_labels`, `_id`) apply only in graph build contexts.

### Quick comparison

| Capability                         | `@graph_fn`            | `@graphify`             | `@tool`                     |
|-----------------------------------|------------------------|-------------------------|-----------------------------|
| Immediate "just run"              | Yes                    | Build first             | Yes (outside graph)         |
| Full `context.*` access           | Yes (via `context`)    | via tools/subgraphs     | when called under `graph_fn`|
| Visible per-step nodes            | via `@tool` calls      | native                  | yes                         |
| Fan-out / fan-in (map/reduce)     | limited (Python loops) | Yes (concise)           | building block              |
| Control edges (`_after`/barrier)  | No                     | Yes                     | Yes in graph build          |
| Graph spec/IO inspection          | implicit               | Yes (`.spec()/.io()`)   | n/a                         |
| Best for                          | demos, services        | pipelines, orchestration| atomic operations           |

Rule of thumb: Start with `@graph_fn`. When you feel the need for explicit topology or orchestration, switch the same steps into `@graphify` using the exact same `@tool`s.
