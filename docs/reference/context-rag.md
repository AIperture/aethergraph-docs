# `RAGFacade` – Retrieval‑Augmented Generation API

> Manages corpora, document ingestion (text/files), chunking + embeddings, vector indexing, retrieval, and QA.
>
> **Backends:** defaults to a lightweight SQLite vector index. FAISS is supported locally if installed via pip. See **[LLM & Index Setup](../llm-setup/llm-setup.md)** for provider/model/index configuration.

--- 

## 1. Core Methods
These method are bounded to NodeContext with specific scope (run_id, session_id, user_id etc)

??? quote "bind_corpus(corpus_id, key, create_if_missing, labels, scope_id)"
    ::: aethergraph.services.rag.node_rag.NodeRAG.bind_corpus
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "upsert_docs(corpus_id, docs, *, scope_id)"
    ::: aethergraph.services.rag.node_rag.NodeRAG.upsert_docs
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "search(corpus_id, query, *,  k, filters, scope_id, mode)"
    ::: aethergraph.services.rag.node_rag.NodeRAG.search
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "answer(corpus_id, question, *, llm, style, with_citations, k, scope_id)"
    ::: aethergraph.services.rag.node_rag.NodeRAG.answer
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 


## 2. Storage Management
These method are direct operations in `RAGFacade` to manage all corpura and docs

??? quote "list_corpora()"
    ::: aethergraph.services.rag.facade.RAGFacade.list_corpora
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "list_docs(corpus_id, limit, after)"
    ::: aethergraph.services.rag.facade.RAGFacade.list_docs
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "delete_docs(corpus_id, doc_ids)"
    ::: aethergraph.services.rag.facade.RAGFacade.delete_docs
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "reembed(corpus_id, *, doc_ids, batch)"
    ::: aethergraph.services.rag.facade.RAGFacade.reembed
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "stats(corpus_id)"
    ::: aethergraph.services.rag.facade.RAGFacade.stats
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 
