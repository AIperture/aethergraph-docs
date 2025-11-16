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

## Quick Reference

| Method                                                       | Purpose                              | Returns            |
| ------------------------------------------------------------ | ------------------------------------ | ------------------ |
| `get(key, default=None)`                                     | Get value if present and not expired | `Any`              |
| `set(key, value, *, ttl_s=None)`                             | Set value with optional TTL          | `None`             |
| `delete(key)`                                                | Remove key if present                | `None`             |
| `list_append_unique(key, items, *, id_key="id", ttl_s=None)` | Append unique dict items to a list   | `list[dict]`       |
| `list_pop_all(key)`                                          | Pop and return entire list           | `list`             |
| `mget(keys)`                                                 | Batch get                            | `list[Any]`        |
| `mset(kv, *, ttl_s=None)`                                    | Batch set with optional TTL          | `None`             |
| `expire(key, ttl_s)`                                         | Set/refresh expiry for a key         | `None`             |
| `purge_expired(limit=1000)`                                  | GC expired entries (best‑effort)     | `int` count purged |

---

## Methods

<details markdown="1">
<summary>get(key, default=None) -> Any</summary>

**Description:** Return the current value for `key` unless missing or expired; otherwise return `default`.

**Inputs:**

* `key: str`
* `default: Any`

**Returns:**

* `Any`

**Notes:** Expired entries are deleted on read.

</details>

<details markdown="1">
<summary>set(key, value, *, ttl_s=None) -> None</summary>

**Description:** Set `key` to `value` with optional TTL in seconds.

**Inputs:**

* `key: str`
* `value: Any` – Prefer small JSON‑serializable payloads.
* `ttl_s: int | None` – Time‑to‑live (seconds).

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>delete(key) -> None</summary>

**Description:** Delete `key` if present.

**Inputs:**

* `key: str`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>list_append_unique(key, items, *, id_key="id", ttl_s=None) -> list[dict]</summary>

**Description:** Append dict `items` to the list at `key`, skipping any whose `id_key` duplicates an existing item.

**Inputs:**

* `key: str`
* `items: list[dict]`
* `id_key: str` – Field used to determine uniqueness (default `"id"`).
* `ttl_s: int | None`

**Returns:**

* `list[dict]` – The updated list.

**Notes:** Non‑dict items are ignored.

</details>

<details markdown="1">
<summary>list_pop_all(key) -> list</summary>

**Description:** Atomically pop and return the entire list at `key`. If missing or non‑list, return an empty list.

**Inputs:**

* `key: str`

**Returns:**

* `list`

</details>

<details markdown="1">
<summary>mget(keys) -> list[Any]</summary>

**Description:** Batch get for multiple keys.

**Inputs:**

* `keys: list[str]`

**Returns:**

* `list[Any]` – Values in the same order as `keys` (expired/missing → `None` or default semantics of `get`).

</details>

<details markdown="1">
<summary>mset(kv, *, ttl_s=None) -> None</summary>

**Description:** Batch set multiple entries with an optional TTL applied to each.

**Inputs:**

* `kv: dict[str, Any]`
* `ttl_s: int | None`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>expire(key, ttl_s) -> None</summary>

**Description:** Set or refresh the expiry for `key`.

**Inputs:**

* `key: str`
* `ttl_s: int`

**Returns:**

* `None`

**Notes:** No‑op if `key` is missing.

</details>

<details markdown="1">
<summary>purge_expired(limit=1000) -> int</summary>

**Description:** Remove up to `limit` expired entries.

**Inputs:**

* `limit: int`

**Returns:**

* `int` – Number of entries purged.

**Notes:** Expiry is also enforced lazily on `get()`; this provides proactive cleanup.

</details>

---

## Usage Notes

* **Not durable:** For persistent state, use artifacts, memory persistence, or a durable KV backend when available.
* **Small values only:** Store references/IDs, not large byte blobs.
* **Namespacing:** Prefer scoping keys (e.g., `f"run:{run_id}:…"`) to avoid collisions across flows.
