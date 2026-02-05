# `context.planner()` – NodePlanner for Typed DAG Planning

`context.planner()` returns a `NodePlanner`: a **node-bound façade** over `PlannerService` that generates and executes **typed DAG plans** with an LLM.

Today, planning is **static**: the planner proposes a DAG from the available graphs/skills, validates it against typed inputs/outputs, then you execute it. In the future, this will evolve toward **dynamic planning** (re-planning based on intermediate execution signals, tool feedback, and typed state).

## Core ideas

### Typed DAG planning

- Each plan is a **directed acyclic graph (DAG)** of steps.
- Each step references an action (`action_ref`) plus `inputs`.
- The planner uses typed input/output constraints to ensure the plan is executable.

### Flow constraints (`flow_ids`)

`flow_ids` is a list of flow identifiers used to **constrain the search space**. This can be specified when defining the graph/graph function in the decorator `@graph(flow_id=...)` or `@graph_fn(flow_id=...)`. Any graphs/actions registered under the same flow list can be combined into a single valid DAG (subject to type compatibility).

### Node-bound execution context

`NodePlanner` auto-fills execution metadata from the active `NodeContext` (identity/session/app/agent), while still allowing overrides via keyword arguments.

---

## 1. Planning Types and Dataclasses

These dataclasses define the planning protocol and validation surface.

??? quote "PlanStep"
    ::: aethergraph.services.planning.plan_types.PlanStep
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "CandidatePlan"
    ::: aethergraph.services.planning.plan_types.CandidatePlan
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "ValidationIssue"
    ::: aethergraph.services.planning.plan_types.ValidationIssue
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "ValidationResult"
    ::: aethergraph.services.planning.plan_types.ValidationResult
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "PlanningEvent"
    ::: aethergraph.services.planning.plan_types.PlanningEvent
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "PlanningContext"
    ::: aethergraph.services.planning.plan_types.PlanningContext
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "PlanResult"
    ::: aethergraph.services.planning.plan_types.PlanResult
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

---

## 2. Execution Types and Dataclasses

Execution returns structured events and results, and can be run synchronously or in the background.

??? quote "ExecutionEvent"
    ::: aethergraph.services.planning.plan_executor.ExecutionEvent
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "ExecutionResult"
    ::: aethergraph.services.planning.plan_executor.ExecutionResult
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

??? quote "BackgroundExecutionHandle"
    ::: aethergraph.services.planning.plan_executor.BackgroundExecutionHandle
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
            members: []

---

## 3. Core APIs

Below are the primary entry points. **Paths are stable** (do not change imports/targets for these API docs).

### Plan

- `plan()` is the standard entry point for planning with high-level inputs.
- `plan_with_context()` is a lower-level entry point when you already have a `PlanningContext`.
- `parse_inputs()` extracts missing structured inputs from free-form user text.

??? quote "plan(*, goal, user_inputs, external_slots, flow_id, ...)"
    ::: aethergraph.services.planning.node_planner.NodePlanner.plan
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "plan_with_context(ctx, *, on_event)"
    ::: aethergraph.services.planning.node_planner.NodePlanner.plan_with_context
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "parse_inputs(*, message, missing_keys, instruction)"
    ::: aethergraph.services.planning.node_planner.NodePlanner.parse_inputs
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

### Execute

- `execute()` runs a validated `CandidatePlan` immediately.
- `execute_background()` runs the plan asynchronously and returns a handle.

??? quote "execute(plan, *, user_inputs, on_event, ...)"
    ::: aethergraph.services.planning.node_planner.NodePlanner.execute
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "execute_background(plan, *, user_inputs, on_event, ...)"
    ::: aethergraph.services.planning.node_planner.NodePlanner.execute_background
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false
