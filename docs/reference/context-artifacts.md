# `context.artifacts()` – ArtifactFacade API Reference

The `ArtifactFacade` wraps an `AsyncArtifactStore` (persistence) and an `AsyncArtifactIndex` (search/metadata) and automatically indexes artifacts you create within a node/run.

---
## 1. Save API

??? quote "save_file(path, *, kind, labels, ...)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.save_file
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "save_text(payload, *, ...)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.save_text
        options: 
            show_root_heading: false
            show_root_full_path: false
            show_source: false  
    
??? quote "save_json(payload, *, ...)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.save_json
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false   

??? quote "writer(*, kind, planned_ext, ...)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.writer
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  
 
## 2. Search API 
??? quote "get_by_id(artifact_id)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.get_by_id
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "list(*, view)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.list
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "search(*, kind, labels, metric, ...)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.search
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  
  
??? quote "best(*, kind, metric, ...)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.best
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "pin(artifact_id, pinned)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.pin
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

## 3. Stage/Ingest API
??? quote "stage_path(ext)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.stage_path
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "stage_dir(suffix)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.stage_dir
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  
 
??? quote "ingest_file(staged_path, *, kind, ...)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.ingest_file
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "ingest_dir(staged_path, **kwargs)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.ingest_dir
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

## 4. Load API
??? quote "load_bytes_by_id(artifact_id)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.load_bytes_by_id
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "load_text_by_id(artifact_id, *, ...)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.load_text_by_id
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "load_json_by_id(artifact_id, *, ...)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.load_json_by_id
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "load_bytes(uri)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.load_bytes
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  


??? quote "load_text(uri)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.load_text
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  

??? quote "load_json(uri)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.load_json
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  


## 5. Helpers
??? quote "as_local_dir(artifact_or_uri, *, must_exist)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.as_local_dir
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  


??? quote "as_local_file(artifact_or_uri, *, must_exist)"
    ::: aethergraph.services.artifacts.facade.ArtifactFacade.as_local_file
        options:
            show_root_heading: false
            show_root_full_path: false
            show_source: false  