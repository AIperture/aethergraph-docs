# Launching Agent Runs with the `context` Method

Aethergraph provides a flexible interface for managing agent runs through the `NodeContext` object. This approach goes beyond simple nested calls to `graph_fn`, allowing you to spawn, monitor, and control runs with fine-grained operations. The `context` method is designed for general use with any agent, and it supplies metadata that supports seamless integration with the AG web UI.

---

## Async Run

You can initiate an agent run asynchronously using the `context.spawn_run` method. This "fire and forget" approach lets you start a run without waiting for its completion.

???+ quote "context.spawn_run(graph_id, *, inputs, session_id, tags, ...)"
    ::: aethergraph.core.runtime.node_context.NodeContext.spawn_run
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

To monitor the progress or completion of an asynchronous run, use the `context.wait_run` method. This allows you to block until the run finishes or a timeout occurs.

???+ quote "context.wait_run(run_id, *, timeout_s)"
    ::: aethergraph.core.runtime.node_context.NodeContext.wait_run
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

## Kick off a Run and Wait

If you need to start a run and wait for its result in a single step, the `context.run_and_wait` method provides a convenient solution. Note this method blocks the process and does not honor the concurrency limit. 

??? quote "context.run_and_wait(graph_id, *, inputs, session_id, tags, ...)"
    ::: aethergraph.core.runtime.node_context.NodeContext.run_and_wait
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

## Cancellation

Aethergraph also supports run cancellation, allowing you to terminate a run that is no longer needed or is taking too long.

??? quote "context.cancel_run(run_id)"
    ::: aethergraph.core.runtime.node_context.NodeContext.cancel_run
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  
