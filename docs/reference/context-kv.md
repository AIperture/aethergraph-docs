# AetherGraph — `context.kv()` Reference

This page documents the **Key–Value API** available via `context.kv()` in a concise format. The KV store is **process‑local and transient** — ideal for coordination, small caches, inboxes, and short‑lived lists. Not intended for large blobs or durability.

---

## Overview
- Keys are simple strings; values can be any JSON‑serializable Python object (adapters may allow arbitrary picklables, but keep it small).
- Most methods support **TTL** (time‑to‑live in seconds). Expired entries are pruned lazily or via `purge_expired()`.
- For namespacing, prefer prefixes like `"run:<id>:..."`, `"inbox:<channel>"`, etc.

---

## kv.get
```
get(key: str, default: Any = None) -> Any
```
Fetch a value by key; returns `default` if missing or expired.

**Parameters**

- **key** (*str*) – Lookup key.

- **default** (*Any, optional*) – Value to return when absent/expired (default `None`).

**Returns**  
*Any* – Stored value or `default`.

---

## kv.set
```
set(key: str, value: Any, *, ttl_s: int | None = None) -> None
```
Set a key to a value with optional TTL.

**Parameters**

- **key** (*str*) – Key to write.

- **value** (*Any*) – Value to store.

- **ttl_s** (*int, optional*) – Expiration in seconds.

**Returns**  
`None`

---

## kv.delete
```
delete(key: str) -> None
```
Remove a key if present.

**Parameters**

- **key** (*str*) – Key to delete.

**Returns**  
`None`

---

## kv.list_append_unique
```
list_append_unique(key: str, items: list[dict], *, id_key: str = "id", ttl_s: int | None = None) -> list[dict]
```
Append unique dict items to a **list** value under `key`. Uniqueness is determined by `item[id_key]`.

**Parameters**

- **key** (*str*) – List container key.

- **items** (*list[dict]*) – Items to append.

- **id_key** (*str*) – Field name used for uniqueness (default: `"id"`).

- **ttl_s** (*int, optional*) – Reset TTL for the list.

**Returns**  
*list[dict]* – Updated list.

---

## kv.list_pop_all
```
list_pop_all(key: str) -> list
```
Pop and return the entire **list** stored at `key`. Empties the container.

**Parameters**

- **key** (*str*) – List container key.

**Returns**  
*list* – Previous list content (empty list if none or not a list).

---

## kv.mget
```
mget(keys: list[str]) -> list[Any]
```
Batch get multiple keys.

**Parameters**

- **keys** (*list[str]*) – Keys to read.

**Returns**  
*list[Any]* – Values in the same order as `keys`.

---

## kv.mset
```
mset(kv: dict[str, Any], *, ttl_s: int | None = None) -> None
```
Batch set multiple keys with an optional shared TTL.

**Parameters**

- **kv** (*dict[str, Any]*) – Key–value pairs.

- **ttl_s** (*int, optional*) – TTL to apply to all entries.

**Returns**  
`None`

---

## kv.expire
```
expire(key: str, ttl_s: int) -> None
```
Update/assign a TTL for an existing key.

**Parameters**

- **key** (*str*) – Key to expire.

- **ttl_s** (*int*) – Time‑to‑live in seconds from now.

**Returns**  
`None`

---

## kv.purge_expired
```
purge_expired(limit: int = 1000) -> int
```
Remove up to `limit` expired keys.

**Parameters**

- **limit** (*int*) – Maximum removals per call (default: 1000).

**Returns**  
*int* – Number of keys purged.

---

## Practical examples

**1) Channel inbox (files/messages)**
```python
# Adapter pushes uploads into an inbox list
await context.kv().list_append_unique(
    key=f"inbox:{channel_key}",
    items=[{"id": file_id, "filename": name, "url": url}],
    ttl_s=3600,
)

# Agent consumes the inbox later
files = await context.kv().list_pop_all(f"inbox:{channel_key}")
if files:
    await context.channel().send_text(f"Received {len(files)} file(s)")
```

**2) Short‑lived cache with TTL**
```python
k = f"run:{context.run_id}:spec"
spec = await context.kv().get(k)
if spec is None:
    spec = await expensive_fetch()
    await context.kv().set(k, spec, ttl_s=300)  # cache for 5 minutes
```

**3) Batch write/read**
```python
await context.kv().mset({
    f"run:{context.run_id}:step": 42,
    f"run:{context.run_id}:eta": 120,
}, ttl_s=600)

vals = await context.kv().mget([
    f"run:{context.run_id}:step",
    f"run:{context.run_id}:eta",
])
step, eta = vals
```

**4) Update TTL**
```python
await context.kv().expire(f"run:{context.run_id}:spec", ttl_s=900)
```

---

## Notes & behaviors
- **Transient**: data is in‑process only; it disappears on restart.

- **Small values**: do not store large binaries; use `context.artifacts()` for blobs.

- **Concurrency**: the implementation uses an internal lock; operations are atomic per call.

- **TTL semantics**: reads lazily drop expired entries; use `purge_expired()` to actively clean.
