# `context.memory()` – MemoryFacade API Reference

`MemoryFacade` coordinates **HotLog** (fast recent events), **Persistence** (durable JSONL), and **Indices** (derived KV views).

It is accessed via `node_context.memory` but aggregates functionality from several internal mixins.

Methods for vector-memory storage and search is under development.

<!-- # Memory Contracts -->

<!-- ???+ quote "Event Schema"
    ::: aethergraph.contracts.services.memory.Event
        options:  
            show_root_heading: true   # Show "class Event"
            show_root_full_path: false # Show just "Event"
            show_category_heading: false
            members: []  # <-- TRICK: Hide methods, show only attributes/docstring

--- -->

## 1. Core Recording
Basic event logging and raw data access for general messages/memory.  
??? quote "record_raw(*, base, text, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.record_raw
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 

??? quote "record(kind, data, tags, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.record
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 


??? quote "recent(kinds, limit)"
    ::: aethergraph.services.memory.facade.MemoryFacade.recent
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 


??? quote "recent_data(kinds, limit)"
    ::: aethergraph.services.memory.facade.MemoryFacade.recent_data
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 

??? quote "search(query, kinds, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.search
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 


## 2. Chat Operations
Convenience method for recording chat-related memory events.

??? quote "record_chat(role, text, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.record_chat
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "record_chat_user(text, *, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.record_chat_user 
        options: 
            show_root_heading: false
            show_root_full_path: false
            show_source: false 

??? quote "record_chat_assistant(text, *, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.record_chat_assistant 
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 

??? quote "record_chat_system(text, *, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.record_chat_system 
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 

??? quote "recent_chat(*, limit, roles)"
    ::: aethergraph.services.memory.facade.MemoryFacade.recent_chat 
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 



## 3. Tool-related Memory


??? quote "record_tool_result(tool, inputs, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.record_tool_result
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "recent_tool_results(*, tool, limit, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.recent_tool_results
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  


??? quote "recent_tool_result_data(*, tool, limit, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.recent_tool_result_data
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  



## 4. Memory Distillation 

??? quote "distill_long_term(scope_id, *, summary_tag, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.distill_long_term
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  


??? quote "distill_meta_summary(scope_id, *, summary_kind, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.distill_meta_summary  
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  


??? quote "load_recent_summaries(scope_id, *,  summary_tag, limit)"
    ::: aethergraph.services.memory.facade.MemoryFacade.load_recent_summaries
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 

??? quote "load_last_summary(scope_id, *,  summary_tag)"
    ::: aethergraph.services.memory.facade.MemoryFacade.load_last_summary
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 

??? quote "soft_hydrate_last_summary(scope_id, *, summary_tag, summary_kind)"
    ::: aethergraph.services.memory.facade.MemoryFacade.soft_hydrate_last_summary
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

## 5. Vector Memory
??? quote "rag_remember_events(*, key='default', where=None, policy=None)"
    ::: aethergraph.services.memory.facade.MemoryFacade.rag_remember_events
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "rag_remember_docs(docs, *, key='default', labels=None)"
    ::: aethergraph.services.memory.facade.MemoryFacade.rag_remember_docs
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "rag_search_by_key(*, key='default', query, k=8, filters=None, mode='hybrid')"
    ::: aethergraph.services.memory.facade.MemoryFacade.rag_search_by_key
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "rag_answer_by_key(*, key='default', question, style='concise', with_citations=True, k=6)"
    ::: aethergraph.services.memory.facade.MemoryFacade.rag_answer_by_key
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

## 6. Utilities

??? quote "chat_history_for_llm(*, limit, include_system_summary, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.chat_history_for_llm 
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 

??? quote "build_prompt_segments(*, recent_chat_limit, include_long_term, ...)"
    ::: aethergraph.services.memory.facade.MemoryFacade.build_prompt_segments
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false 


<!-- ??? quote "rag_upsert(*, corpus_id, docs, topic=None)"
    ::: aethergraph.services.memory.facade.MemoryFacade.rag_upsert
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "rag_bind(*, corpus_id=None, key=None, create_if_missing=True, labels=None)"
    ::: aethergraph.services.memory.facade.MemoryFacade.rag_bind
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "rag_promote_events(*, corpus_id, events=None, where=None, policy=None)"
    ::: aethergraph.services.memory.facade.MemoryFacade.rag_promote_events
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "rag_answer(*, corpus_id, question, style='concise', with_citations=True, k=6)"
    ::: aethergraph.services.memory.facade.MemoryFacade.rag_answer
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false

??? quote "rag_search(*, corpus_id, query, k=8, filters=None, mode='hybrid')"
    ::: aethergraph.services.memory.facade.MemoryFacade.rag_search
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false -->