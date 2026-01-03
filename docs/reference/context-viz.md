# `context.viz()` – WebUI Visualization API

The visualization service offers a convenient way to log data from agents into persistent storage. It is typically used in conjunction with AG's WebUI to automatically visualize each run. For manual generation of visualization data, it is recommended to use the corresponding Python package.

---

## 1. Data Visualization 

??? quote "scalar(track_id, *, step, value, ...)"
    ::: aethergraph.services.viz.facade.VizFacade.scalar
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "vector(track_id, *, step, values, ...)"
    ::: aethergraph.services.viz.facade.VizFacade.vector
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  


??? quote "matrix(track_id, *, step, matrix, ...)"
    ::: aethergraph.services.viz.facade.VizFacade.matrix
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  





## 2. Artifact Visualization (image etc.)


??? quote "image_from_artifact(track_id, *, step, artifact, ...)"
    ::: aethergraph.services.viz.facade.VizFacade.image_from_artifact
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "image_from_bytes(track_id, *, step, data, ...)"
    ::: aethergraph.services.viz.facade.VizFacade.image_from_bytes
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  