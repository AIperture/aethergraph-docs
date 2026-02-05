# `send_rich()` – AG Web UI Rich Messages

`send_rich()` lets an agent send **UI-aware messages** to the AG Web UI (while still optionally emitting a plain-text prefix for non-UI adapters).

At a high level, a rich message looks like:

- **`text`**: optional markdown text shown above the rich content (and used for down-level adapters)
- **`rich`**: a structured payload the UI can render as one or more **blocks**

---

## What are “blocks”?

A **block** is a single renderable UI unit: a card, a plot, an embedded webapp, etc.

You can send:

- **One block**: `rich={"kind": ..., "payload": ...}`
- **Multiple blocks**: `rich={"blocks": [ ...block, ...block ]}`

The UI renders blocks top-to-bottom in the order provided.

### Single-block shape

```python
await chan.send_rich(
    text="Optional markdown above the block.",
    rich={
        "kind": "component",
        "payload": { ... }
    },
)
```

### Multi-block shape

```python
await chan.send_rich(
    text="Optional markdown above all blocks.",
    rich={
        "blocks": [
            {"kind": "plot", "payload": { ... }},
            {"kind": "component", "payload": { ... }},
        ]
    },
)
```

---

## 1) React component blocks (UI cards)

Use this when you want **structured UI** (status, kv tables, timelines, actions) rather than free-form markdown.

### Generic Card: `ag.ui.card.v1`

The **generic card** is the main “Swiss army knife” for rich UI. You send:

- `kind: "component"`
- `payload.component_type: "ag.ui.card.v1"`
- `payload.props`: a JSON object shaped like `CardSpecV1` (header + sections + footer)

(See the full schema and section types in the Generic Card reference.)

**Minimal example**

```python
await chan.send_rich(
    text="Run status:",
    rich={
        "kind": "component",
        "payload": {
            "component_type": "ag.ui.card.v1",
            "props": {
                "version": "card.v1",
                "header": {"title": "Run", "right_text": "RUNNING", "tone": "info"},
                "sections": [
                    {
                        "type": "kv",
                        "columns": 2,
                        "items": [
                            {"label": "run_id", "value": "run_123", "mono": True},
                            {"label": "node", "value": "trainer", "mono": True},
                        ],
                    }
                ],
            },
        },
    },
)
```

### When to use component cards

- Planner output summaries (steps, missing inputs)
- Execution progress (phases, statuses)
- Metrics strips and key/value snapshots
- Debug JSON (collapsible)
- “Next action” buttons (links)

---

## 2) Vega / Vega-Lite plot blocks

Use this when you want **interactive charts** rendered by the UI.

### Vega-Lite example

```python
loss_vega_spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "data": {"values": [{"step": 1, "loss": 0.9}, {"step": 2, "loss": 0.7}]},
    "mark": "line",
    "encoding": {
        "x": {"field": "step", "type": "quantitative"},
        "y": {"field": "loss", "type": "quantitative"},
    },
}

await chan.send_rich(
    text="Here is the loss curve:",
    rich={
        "kind": "plot",
        "title": "Training loss",
        "payload": {
            "engine": "vega-lite",
            "spec": loss_vega_spec,
        },
    },
)
```

### When to use plots

- Training curves (loss/accuracy)
- Scatter / residual plots
- Histograms and distributions
- Any data summary where visual inspection matters

---

## 3) WebApp embed blocks (WebAppCard)

Use this when you want to embed an **external web experience** in the UI (maps, dashboards, internal tools) via an iframe-style card.

### WebAppCard example

```python
webapp_url = (
    "https://embed.windy.com/embed2.html?lat=-37.817&lon=144.955&zoom=5"
    "&level=surface&overlay=wind&menu=&message=&marker=&calendar=now"
)

await chan.send_rich(
    text=(
        "Next, here’s an **embedded map** using the WebAppCard. "
        "In a real deployment this could be your internal app."
    ),
    rich={
        "kind": "web_app",
        "title": "WebApp Demo",
        "payload": {
            "component_type": "ag.ui.web_app_card.v1",
            "props": {
                "title": "Map View",
                "subtitle": "Embedded web app (demo)",
                "url": webapp_url,
                "params": {},
                "view": {
                    "initialMode": "inline",
                    "autoActivate": True,
                },
            },
        },
    },
)
```

### When to use WebApp embeds

- Maps / location views
- Monitoring dashboards
- Interactive internal tools (authenticated environments)
- “Bring-your-own-UI” surfaces while you prototype native cards

---

## Recommended patterns

### A) Text + one block

Use this for most updates:

- `text` explains what the user is seeing
- the block provides the UI surface

### B) Multi-block “report”

A common pattern is:

1) a plot block (visual)
2) a card block (key metrics + next actions)
3) optionally a debug JSON block (collapsed)

---

## More cards are coming

Current rich surfaces cover:

- **React component cards** (generic card + specialized components)
- **Vega / Vega-Lite plots**
- **WebApp embeds**

Planned / on-the-way examples:

- **Three.js** (3D viewers, geometry, point clouds)
- **Plotly** (interactive scientific charts)
- **Tables / spreadsheets** (editable grids)
- **File preview cards** (PDF/image/code rendering)

---

## Notes on compatibility

- AG Web UI renders blocks natively.
- Other adapters may down-level to plain text, or ignore `rich` entirely.
- Prefer concise blocks: one card per concept, avoid overloading a single message.

---

## Component recipes for `ag.ui.card.v1`

This section lists the main **card section types** you can use with the generic card component.
Each recipe shows a minimal `send_rich(...)` call with a single section inside `props.sections`.

All of them follow the same outer shape:

```python
await chan.send_rich(
    text="Optional markdown above the card.",
    rich={
        "kind": "component",
        "payload": {
            "component_type": "ag.ui.card.v1",
            "props": {
                "version": "card.v1",
                "sections": [
                    {  # one of the section types below }
                ],
            },
        },
    },
)
```

### Section cheatsheet

#### `callout`

??? quote "callout – warnings / info"
    ```python
    await chan.send_rich(
        text="Input validation:",
        rich={
            "kind": "component",
            "payload": {
                "component_type": "ag.ui.card.v1",
                "props": {
                    "version": "card.v1",
                    "sections": [
                        {
                            "type": "callout",
                            "tone": "warning",  # info | success | danger | warning
                            "title": "Missing input",
                            "message": "train_ratio is missing. Provide it to continue.",
                            "details": "Expected a float between 0 and 1.",
                        }
                    ],
                },
            },
        },
    )
    ```

#### `kv` (key/value grid)

??? quote "kv – key/value grid"
    ```python
    await chan.send_rich(
        text="Run details:",
        rich={
            "kind": "component",
            "payload": {
                "component_type": "ag.ui.card.v1",
                "props": {
                    "version": "card.v1",
                    "sections": [
                        {
                            "type": "kv",
                            "columns": 2,  # 1 or 2
                            "items": [
                                {"label": "run_id", "value": "run_demo_001", "mono": True},
                                {"label": "session_id", "value": "sess_abc", "mono": True},
                                {"label": "dataset_path", "value": "dummy_path/data.csv", "mono": True},
                                {"label": "train_ratio", "value": None, "hint": "missing"},
                            ],
                        }
                    ],
                },
            },
        },
    )
    ```

#### `timeline`

??? quote "timeline – step-wise flow"
    ```python
    await chan.send_rich(
        text="Plan progress:",
        rich={
            "kind": "component",
            "payload": {
                "component_type": "ag.ui.card.v1",
                "props": {
                    "version": "card.v1",
                    "sections": [
                        {
                            "type": "timeline",
                            "steps": [
                                {"id": "load", "label": "Load dataset", "status": "done"},
                                {"id": "train", "label": "Train surrogate", "status": "running"},
                                {"id": "eval", "label": "Evaluate grid", "status": "pending"},
                            ],
                        }
                    ],
                },
            },
        },
    )
    ```

#### `list`

??? quote "list – verbose items"
    ```python
    await chan.send_rich(
        text="Plan steps:",
        rich={
            "kind": "component",
            "payload": {
                "component_type": "ag.ui.card.v1",
                "props": {
                    "version": "card.v1",
                    "sections": [
                        {
                            "type": "list",
                            "items": [
                                {
                                    "primary": "load • load_surrogate_dataset",
                                    "secondary": '{"dataset_path":"dummy_path/data.csv"}',
                                    "status": "done",
                                },
                                {
                                    "primary": "train • train_surrogate_model",
                                    "secondary": '{"lr":0.2,"epochs":20}',
                                    "status": "running",
                                },
                                {
                                    "primary": "eval • evaluate_grid",
                                    "secondary": "Pending execution",
                                    "status": "pending",
                                },
                            ],
                        }
                    ],
                },
            },
        },
    )
    ```

#### `metrics`

??? quote "metrics – compact stats"
    ```python
    await chan.send_rich(
        text="Key metrics:",
        rich={
            "kind": "component",
            "payload": {
                "component_type": "ag.ui.card.v1",
                "props": {
                    "version": "card.v1",
                    "sections": [
                        {
                            "type": "metrics",
                            "items": [
                                {"label": "val_loss", "value": "0.023", "delta": "-0.004", "trend": "down"},
                                {"label": "train_loss", "value": "0.041", "delta": "-0.002", "trend": "down"},
                                {"label": "epoch", "value": "20", "delta": "+1", "trend": "up"},
                                {"label": "lr", "value": "0.2"},
                            ],
                        }
                    ],
                },
            },
        },
    )
    ```

#### `code`

??? quote "code – code snippet"
    ```python
    await chan.send_rich(
        text="Example helper function:",
        rich={
            "kind": "component",
            "payload": {
                "component_type": "ag.ui.card.v1",
                "props": {
                    "version": "card.v1",
                    "sections": [
                        {
                            "type": "code",
                            "language": "python",
                            "code": "def f(x):\n    return x * x\n",
                        }
                    ],
                },
            },
        },
    )
    ```

#### `json`

??? quote "json – collapsible JSON blob"
    ```python
    await chan.send_rich(
        text="Debug plan JSON:",
        rich={
            "kind": "component",
            "payload": {
                "component_type": "ag.ui.card.v1",
                "props": {
                    "version": "card.v1",
                    "sections": [
                        {
                            "type": "json",
                            "collapsed": True,
                            "data": {
                                "plan_id": "plan_demo_001",
                                "steps": [
                                    {"id": "load", "action": "load_surrogate_dataset"},
                                ],
                            },
                        }
                    ],
                },
            },
        },
    )
    ```

#### `actions`

??? quote "actions – next-step buttons / links"
    ```python
    await chan.send_rich(
        text="Next steps:",
        rich={
            "kind": "component",
            "payload": {
                "component_type": "ag.ui.card.v1",
                "props": {
                    "version": "card.v1",
                    "sections": [
                        {
                            "type": "actions",
                            "actions": [
                                {"id": "docs", "label": "Open docs", "href": "https://example.com/docs"},
                                {"id": "runs", "label": "View runs", "href": "https://example.com/runs"},
                            ],
                        }
                    ],
                },
            },
        },
    )
    ```

- AG Web UI renders blocks natively.
- For general text and markdown (equations, code), prefer to use send_text. UI will render them properly.
- Other adapters may down-level to plain text, or ignore `rich` entirely.
- Prefer concise blocks: one card per concept, avoid overloading a single message.

