# `context.kv()` – EphemeralKV API Reference

`EphemeralKV` is a **process‑local, transient key–value store** for small JSON‑serializable values and short‑lived coordination. It is thread‑safe (RLock), supports TTLs, and provides a few list helpers. **Do not use for large blobs** or durable state.

> The API below is consistent across KV backends. In `context`, this KV is ephemeral; other implementations may be pluggable later.

---

## Concepts & Defaults

* **Scope:** In‑process only; cleared on restart. Not replicated.
* **Thread‑safety:** Internal reads/writes guarded by `RLock`.
* **TTL:** Expiry is checked lazily on access and via `purge_expired()`.
* **Prefixing:** Instances may prepend a `prefix` to all keys for namespacing.

---
## 1. Core Methods

??? quote "set(key, value, *, ttl_s)"
    ::: aethergraph.services.kv.ephemeral.EphemeralKV.set
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "get(key, default)"
    ::: aethergraph.services.kv.ephemeral.EphemeralKV.get
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false  

??? quote "delete(key)"
    ::: aethergraph.services.kv.ephemeral.EphemeralKV.delete
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "list_append_unique(key, items, *, id_key, ttl_s)"
    ::: aethergraph.services.kv.ephemeral.EphemeralKV.list_append_unique
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "list_pop_all(key)"
    ::: aethergraph.services.kv.ephemeral.EphemeralKV.list_pop_all
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 


## 2. Optional Helpers


??? quote "mset(kv, *, ttl_s)"
    ::: aethergraph.services.kv.ephemeral.EphemeralKV.mset
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "mget(keys)"
    ::: aethergraph.services.kv.ephemeral.EphemeralKV.mget
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 


??? quote "expire(key, ttl_s)"
    ::: aethergraph.services.kv.ephemeral.EphemeralKV.expire
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "purge_expired(limit)"
    ::: aethergraph.services.kv.ephemeral.EphemeralKV.purge_expired
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

