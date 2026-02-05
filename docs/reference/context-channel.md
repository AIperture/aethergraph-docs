# `context.channel()` – ChannelSession API Reference

A `ChannelSession` provides message I/O, user prompts, streaming text, and progress updates through the configured channel (console/Slack/…). It also manages continuation tokens to avoid race conditions.

---

## Channel Resolution & Defaults

* **Channel selection priority:** explicit `channel` arg → session override (from `context.channel(channel_key)`) → bus default → `console:stdin`.
* Events are published after **alias → canonical** key resolution.

---
## 0. Channel Setup
??? quote "context.channel(channel_key)"
    ::: aethergraph.core.runtime.node_context.NodeContext.channel
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "context.ui_run_channel()"
    ::: aethergraph.core.runtime.node_context.NodeContext.ui_run_channel
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "context.ui_session_channel()"
    ::: aethergraph.core.runtime.node_context.NodeContext.ui_session_channel
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

## 1. Send Methods

??? quote "send(event, *, channel, ...)"
    ::: aethergraph.services.channel.session.ChannelSession.send
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "send_text(text, *, meta, channel, ...)"
    ::: aethergraph.services.channel.session.ChannelSession.send_text
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "send_image(url, *, alt, title, channel, ...)"
    ::: aethergraph.services.channel.session.ChannelSession.send_image
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "send_file(url, *, file_bytes, filename, title, channel, ...)"
    ::: aethergraph.services.channel.session.ChannelSession.send_file
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "send_buttons(text, buttons, *, meta, channel, ...)"
    ::: aethergraph.services.channel.session.ChannelSession.send_buttons
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  


??? quote "send_rich(text, *, rich, meta, channel, ...)"
    ::: aethergraph.services.channel.session.ChannelSession.send_rich
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "send_phase(phase, status, *, label, detail, code, channel, key_suffix)"
    ::: aethergraph.services.channel.session.ChannelSession.send_phase
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

> For the capability and tutorial of AG UI on rich content rendering sent by `send_rich()`, see [Rich Card](../ui/ui-rich-card.md) page for instruction. 

## 2. Ask Methods
Ask method automatic implemented continuation so that the agent will resume running when triggered from external channels. 

??? quote "ask_text(prompt, *, timeout_s, silent, channel)"
    ::: aethergraph.services.channel.session.ChannelSession.ask_text
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "wait_text(*, timeout_s, silent, channel)"
    ::: aethergraph.services.channel.session.ChannelSession.wait_text
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "ask_approval(prompt, options, *, timeout_s, channel)"
    ::: aethergraph.services.channel.session.ChannelSession.ask_approval
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  


??? quote "ask_files(prompt, *, accept, multiple, timeout_s, channel)"
    ::: aethergraph.services.channel.session.ChannelSession.ask_files
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  


## 3. Streaming 

??? quote "stream(channel)"
    ::: aethergraph.services.channel.session.ChannelSession.stream
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

## 4. Utilities

??? quote "get_latest_uploads(*, clear)"
    ::: aethergraph.services.channel.session.ChannelSession.get_latest_uploads
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  