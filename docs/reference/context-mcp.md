# `context.mcp()` – Model Context Protocol (MCP) API Reference

`context.mcp()` gives you access to the MCP service, which manages **named MCP clients** (stdio / WebSocket / HTTP), handles lifecycle (open/close), and offers thin call helpers.

> Register clients after the sidecar starts. Example below uses the helper `register_mcp_client()`.

---

## Quick Reference

| Method                               | Purpose                               | Returns              |
| ------------------------------------ | ------------------------------------- | -------------------- |
| `register(name, client)`             | Add/replace an MCP client             | `None`               |
| `remove(name)`                       | Unregister a client                   | `None`               |
| `has(name)`                          | Check if a client exists              | `bool`               |
| `names()` / `list_clients()`         | List registered client names          | `list[str]`          |
| `get(name="default")`                | Get a client by name (or error)       | `MCPClient`          |
| `open(name)` / `close(name)`         | Open/close a single client            | `None`               |
| `open_all()` / `close_all()`         | Open/close all clients                | `None`               |
| `call(name, tool, params=None)`      | Invoke a tool on a client             | `dict` (tool result) |
| `list_tools(name)`                   | Enumerate tools on a client           | `list[MCPTool]`      |
| `list_resources(name)`               | Enumerate resources                   | `list[MCPResource]`  |
| `read_resource(name, uri)`           | Fetch a resource by URI               | `dict`               |
| `set_header(name, key, value)`       | (WS) Set/override a header at runtime | `None`               |
| `persist_secret(secret_name, value)` | Persist a secret via secrets provider | `None`               |

---

## Methods

<details markdown="1">
<summary>register(name, client) -> None</summary>

**Description:** Register or replace an MCP client under `name`.

**Inputs:**

* `name: str`
* `client: MCPClientProtocol`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>remove(name) -> None</summary>

**Description:** Unregister a client if present.

**Inputs:**

* `name: str`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>has(name) -> bool</summary>

**Description:** Check whether a client is registered.

**Inputs:**

* `name: str`

**Returns:**

* `bool`

</details>

<details markdown="1">
<summary>names() / list_clients() -> list[str]</summary>

**Description:** Return all registered client names.

**Inputs:**

* —

**Returns:**

* `list[str]`

</details>

<details markdown="1">
<summary>get(name="default") -> MCPClientProtocol</summary>

**Description:** Return a client by name or raise `KeyError` if missing.

**Inputs:**

* `name: str`

**Returns:**

* `MCPClientProtocol`

</details>

<details markdown="1">
<summary>open(name) -> None</summary>

**Description:** Ensure the client connection is open.

**Inputs:**

* `name: str`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>close(name) -> None</summary>

**Description:** Close the client connection; logs a warning on failure.

**Inputs:**

* `name: str`

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>open_all() -> None</summary>

**Description:** Open all registered clients.

**Inputs:**

* —

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>close_all() -> None</summary>

**Description:** Close all registered clients (best‑effort).

**Inputs:**

* —

**Returns:**

* `None`

</details>

<details markdown="1">
<summary>call(name, tool, params=None) -> dict</summary>

**Description:** Lazy‑open the client and invoke an MCP tool.

**Inputs:**

* `name: str`
* `tool: str` – Tool identifier on the target MCP server.
* `params: dict[str, Any] | None`

**Returns:**

* `dict` – Tool response.

**Notes:** Clients also self‑reconnect on demand.

</details>

<details markdown="1">
<summary>list_tools(name) -> list[MCPTool]</summary>

**Description:** List available tools exposed by the MCP server.

**Inputs:**

* `name: str`

**Returns:**

* `list[MCPTool]`

</details>

<details markdown="1">
<summary>list_resources(name) -> list[MCPResource]</summary>

**Description:** List available resources exposed by the MCP server.

**Inputs:**

* `name: str`

**Returns:**

* `list[MCPResource]`

</details>

<details markdown="1">
<summary>read_resource(name, uri) -> dict</summary>

**Description:** Read a resource by URI from the MCP server.

**Inputs:**

* `name: str`
* `uri: str`

**Returns:**

* `dict`

</details>

<details markdown="1">
<summary>set_header(name, key, value) -> None</summary>

**Description:** For **WebSocket** clients, set/override a header at runtime (useful in notebooks/demos).

**Inputs:**

* `name: str`
* `key: str`
* `value: str`

**Returns:**

* `None`

**Notes:** Raises `RuntimeError` if the client does not support headers.

</details>

<details markdown="1">
<summary>persist_secret(secret_name, value) -> None</summary>

**Description:** Persist a secret via the bound secrets provider (if writable).

**Inputs:**

* `secret_name: str`
* `value: str`

**Returns:**

* `None`

**Notes:** Raises `RuntimeError` when no writable secrets provider is configured.

</details>

---

## Registering Clients (after sidecar starts)

Start the sidecar, then register one or more MCP clients:

```python
from aethergraph import start_server
from aethergraph.runtime import register_mcp_client
from aethergraph.plugins.mcp import StdioMCPClient, WsMCPClient, HttpMCPClient
import sys

# 1) Start sidecar (choose your port/logging as you prefer)
start_server(port=0)

# 2) Register a local stdio MCP (no auth/network)
register_mcp_client(
    "local",
    client=StdioMCPClient(cmd=[sys.executable, "-m", "aethergraph.plugins.mcp.fs_server"]),
)

# 3) (Optional) Register a WebSocket MCP
register_mcp_client(
    "ws",
    client=WsMCPClient(
        url="wss://mcp.example.com/ws",
        headers={"Authorization": "Bearer <token>"},
        timeout=60.0,
    ),
)

# 4) (Optional) Register an HTTP MCP
register_mcp_client(
    "http",
    client=HttpMCPClient(
        base_url="https://mcp.example.com/api",
        headers={"Authorization": "Bearer <token>"},
        timeout=60.0,
    ),
)
```

**Client types:**

* **`StdioMCPClient(cmd, env=None, timeout=60.0)`** – JSON‑RPC over stdio to a subprocess.
* **`WsMCPClient(url, headers=None, timeout=60.0, ping_interval=20.0, ping_timeout=10.0)`** – JSON‑RPC over WebSocket.
* **`HttpMCPClient(base_url, headers=None, timeout=60.0)`** – JSON‑RPC over HTTP.

---

## Examples

```python
# Get tool list and call a tool
mcp = context.mcp()

tools = await mcp.list_tools("local")
res = await mcp.call("local", tool="fs.read_text", params={"path": "/etc/hosts"})

# Read a resource listing from WS backend
await mcp.open("ws")
resources = await mcp.list_resources("ws")

# Set a header on the WS client (e.g., late‑bound token)
mcp.set_header("ws", "Authorization", "Bearer NEW_TOKEN")

# Clean up
await mcp.close_all()
```

**Notes:**

* Clients lazy‑open for operations; you may still call `open()` explicitly.
* Errors from the server propagate; inspect tool/resource contracts on the MCP server side for required params and shapes.
