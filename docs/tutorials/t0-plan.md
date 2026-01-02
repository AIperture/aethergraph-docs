# Agentic R&D in 60 Seconds – with AetherGraph

Short, practical demos of agentic R&D workflows in plain Python, using AetherGraph.

* Format: ~60s video + LinkedIn post + example link
* Focus: “What can I do THIS WEEK that makes R&D less painful?”
* Core building blocks:

  * Channels – Python that talks back
  * Artifacts – stop losing results
  * Memory – pipeline as a lab notebook
  * External services – glue for your stack
  * Bonus: LLMs – reasoning inside the flow

---

## Series Overview (for intro / guides page)

Most “agentic frameworks” promise the world.
I just want my R&D scripts to talk back, remember things, and organize results — without leaving Python.

“Agentic R&D in 60 Seconds – with AetherGraph” is a short series of ~1-minute demos where I slowly build up practical “agentic” behaviors on top of normal Python code:

* Ep.1 – Channels: Python that talks back.
* Ep.2 – Artifacts: stop losing results in random folders.
* Ep.3 – Memory: your pipeline as a lightweight lab notebook.
* Ep.4 – External services: glue for your existing stack.
* Ep.5 (Bonus) – LLMs: let the model look at your data and suggest next steps.

AetherGraph can be used to build much more complex agentic systems, but this series stays deliberately practical:

→ What can I do this week that makes my R&D life less painful?

---

## Episode 1 – Python That Talks Back (Channels)

### LinkedIn Post Draft

Most “agentic frameworks” promise the world.
I just want my R&D scripts to talk back, remember things, and organize results — without leaving Python.

Over the next few weeks I’m sharing a short mini-series:

“Agentic R&D in 60 Seconds – with AetherGraph”

Each post = a ~1 minute demo + a small code snippet, focused on one capability in AetherGraph:

* Channels – Python that talks back
* Artifacts – stop losing results in random folders
* Memory – your pipeline as a lightweight lab notebook
* External services – glue for your existing stack

AetherGraph can be used to build much fancier agentic systems, but in this series I want to stay very practical:

→ “What can I do this week that makes my R&D life less painful?”

Ep.1 – Python that talks back (channels)

In this first demo, I turn a plain Python script into a tiny “experiment setup wizard”.

The script:

* Asks for a project name
* Asks how many steps to run
* Lets you enable or skip an “advanced mode”
* Then prints the final config and starts the run

All of this is powered by AetherGraph’s channel API, but it still looks and feels like normal async Python.

Code sketch:

from aethergraph import graph_fn
from aethergraph.core.runtime import ExecutionContext

@graph_fn(name="channel_wizard")
async def channel_wizard(context: ExecutionContext):
chan = context.channel()

```
project = await chan.ask_text("Project name?")
steps = int(
    await chan.ask_text("Number of steps (e.g. 10)?")
)

advanced_choice = await chan.ask_approval(
    "Enable advanced mode?",
    options=["Yes", "No"],
)

config = {
    "project": project,
    "steps": steps,
    "advanced": (advanced_choice == "Yes"),
}

await chan.send_text(f"Running experiment with config: {config}")

# Replace this with your real workload
# e.g. run_training(config), submit_job(config), etc.
await chan.send_text("Experiment started ✅")
```

Beyond this demo

Once you’re comfortable with context.channel(), you can:

* Turn any CLI script into a chat-like wizard (console today, Slack / others later).
* Ask for approvals before expensive steps (e.g. “Submit this job to the cluster?”).
* Build interactive workflows where the system asks you for missing pieces instead of failing.

Links you can add:

* Examples repo
* Main repo
* Intro page

---

## Episode 2 – Stop Losing Your Results (Artifacts)

Most R&D projects eventually become a graveyard of:

* final_results_v7_really_final.json
* new_final_results_latest.csv

In Ep.2 of “Agentic R&D in 60 Seconds – with AetherGraph”, I show how to use artifacts so your workflow always knows where its outputs live.

Demo idea:

A tiny analysis script:

* Loads a CSV
* Computes a small summary (e.g. min / max / mean)
* Saves it as a versioned artifact tied to an experiment scope
* Prints the artifact URI so you can retrieve it later

Code sketch:

from aethergraph import graph_fn
from aethergraph.core.runtime import ExecutionContext

import pandas as pd

@graph_fn(name="summarize_csv")
async def summarize_csv(context: ExecutionContext, path: str, scope: str = "demo_exp"):
df = pd.read_csv(path)

```
summary = {
    "rows": int(len(df)),
    "cols": int(len(df.columns)),
    "col_names": list(df.columns),
    "mean_of_first_col": float(df[df.columns[0]].mean()),
}

ref = await context.artifacts.save_json(
    data=summary,
    scope=scope,
    tag="summary",
)

await context.channel().send_text(
    f"Saved summary artifact:\n{ref.uri}"
)

return {"artifact_uri": ref.uri}
```

A second graph to load the last summary:

@graph_fn(name="load_last_summary")
async def load_last_summary(context: ExecutionContext, scope: str = "demo_exp"):
last = await context.artifacts.load_last(
scope=scope,
tag="summary",
)
await context.channel().send_text(f"Last summary:\n{last}")

Beyond this demo

With artifacts you can:

* Version reports, plots, and models per experiment or per run.
* Build “latest report” and “latest metrics” helpers instead of guessing file names.
* Connect artifacts with memory (e.g. log events that reference artifact URIs).

---

## Episode 3 – Pipelines With a Memory (Memory)

Most R&D work gets lost in log files and screenshots.
The process — which configs you tried, what worked, what failed — is rarely captured in a way you can query.

In Ep.3 of “Agentic R&D in 60 Seconds – with AetherGraph”, I treat the pipeline itself as a tiny lab notebook using the memory layer.

Demo idea:

Each run:

* Logs its config and metric as a memory event
* Tags events by experiment scope
* Then we ask memory to summarize the last few runs

Code sketch for logging a run:

from aethergraph import graph_fn
from aethergraph.core.runtime import ExecutionContext

@graph_fn(name="train_once")
async def train_once(
context: ExecutionContext,
lr: float,
steps: int,
scope: str = "exp1",
):
chan = context.channel()
mem = context.memory()

```
metric = 0.75 + (lr * 0.05)  # fake metric

await chan.send_text(f"Run finished: lr={lr}, steps={steps}, metric={metric:.3f}")

await mem.log_event(
    scope_id=scope,
    kind="run",
    payload={
        "lr": lr,
        "steps": steps,
        "metric": metric,
    },
    tags=["demo", "train_run"],
)

return {"metric": metric}
```

Code sketch for summarizing recent runs:

@graph_fn(name="summarize_recent_runs")
async def summarize_recent_runs(context: ExecutionContext, scope: str = "exp1"):
mem = context.memory()
chan = context.channel()

```
summary = await mem.distill_long_term(
    scope_id=scope,
    question="Summarize the last 3 runs and what changed between them.",
    include_kinds=["run"],
    max_events=3,
)

await chan.send_text("Summary of recent runs:")
await chan.send_text(summary["text"])
```

Beyond this demo

With memory you can:

* Keep a queryable history of runs (config + results + comments).
* Ask the system to highlight trends.
* Combine with channels: ask for human notes mid-run and store them.

---

## Episode 4 – Glue for Your Stack (External Services)

Real R&D rarely lives in one library.
You probably have:

* a simulation codebase over here
* a queue / job runner over there
* some custom Python scripts everywhere

In Ep.4 of “Agentic R&D in 60 Seconds – with AetherGraph”, I treat one of those tools as a first-class service inside the execution context.

Demo idea:

* Define a simple SimService that mocks running a simulation.
* Register it with the AetherGraph runtime as a context service.
* Call it from a graph function, then save results as artifacts.

Service sketch:

class SimService:
async def run(self, config: dict) -> dict:
return {
"status": "ok",
"config": config,
"result": 42.0,
}

# Register under the name "sim" in your container / setup

Graph sketch:

from aethergraph import graph_fn
from aethergraph.core.runtime import ExecutionContext

@graph_fn(name="run_sim_experiment")
async def run_sim_experiment(
context: ExecutionContext,
steps: int = 10,
param: float = 0.5,
scope: str = "sim_demo",
):
chan = context.channel()
arts = context.artifacts()
sim = context.ext_service("sim")  # or context.sim

```
config = {"steps": steps, "param": param}
await chan.send_text(f"Submitting simulation with config: {config}")

result = await sim.run(config)
await chan.send_text(f"Simulation finished with result={result['result']}")

ref = await arts.save_json(
    data=result,
    scope=scope,
    tag="sim_result",
)

await chan.send_text(f"Saved result as artifact: {ref.uri}")
return {"artifact_uri": ref.uri}
```

Beyond this demo

With external services you can:

* Wrap existing simulators, API clients, or job runners as context services.
* Keep your graph logic clean while delegating heavy lifting to those services.
* Combine with channels, memory, and artifacts to build a coherent workflow.

---

## Episode 5 (Bonus) – Let the LLM Look at Your Data (context.llm())

We now have:

* Channels – Python that talks back
* Artifacts – structured results you can find again
* Memory – a lightweight lab notebook
* External services – glue to call your existing stack

In this bonus episode of “Agentic R&D in 60 Seconds – with AetherGraph”, I plug in the last piece:

Let an LLM look at your data inside the flow, instead of manually copying logs into a chat box.

Demo idea:

* Load the last summary artifact for an experiment.
* Call context.llm("default").chat(...) to ask for an explanation.
* Have the pipeline print / send the explanation back via the channel.

Code sketch:

from aethergraph import graph_fn
from aethergraph.core.runtime import ExecutionContext

@graph_fn(name="explain_last_summary")
async def explain_last_summary(
context: ExecutionContext,
scope: str = "demo_exp",
profile: str = "default",
):
chan = context.channel()
arts = context.artifacts()
llm = context.llm(profile)

```
last = await arts.load_last(scope=scope, tag="summary")
if last is None:
    await chan.send_text("No summary artifact found yet.")
    return

user_content = (
    "Here is a JSON summary of a recent experiment:\n\n"
    f"{last}\n\n"
    "Explain what this tells us, and suggest one reasonable next experiment to run."
)

text, usage = await llm.chat(
    messages=[
        {"role": "system", "content": "You are an R&D lab assistant."},
        {"role": "user", "content": user_content},
    ],
)

await chan.send_text("LLM analysis of last summary:")
await chan.send_text(text)

return {"analysis": text, "usage": usage}
```

Beyond this demo

With context.llm() you can:

* Explain artifact contents.
* Summarize memory events.
* Propose next steps based on metrics and configs.
* Implement small policy loops where the LLM suggests new parameters and the graph runs them (with human approvals in the loop).

This is where the earlier pieces come together:

* Channels → interactive conversation.
* Artifacts → structured results to feed the model.
* Memory → history and context.
* External services → real simulators and tools.
