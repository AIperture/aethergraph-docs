# `context.mcp()` – Model Context Protocol (MCP) API Reference

`context.mcp()` gives you access to the MCP service, which manages **named MCP clients** (stdio / WebSocket / HTTP), handles lifecycle (open/close), and offers thin call helpers.

> Register clients after the sidecar starts. Example below uses the helper `register_mcp_client()`.

---

## 1. MCP Clients
Three MCP clients can be established: 

??? quote "HttpMCPClient(name, client)"
    ::: aethergraph.services.mcp.http_client.HttpMCPClient
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 
            members: [] 

??? quote "WsMCPClient(name, client)"
    ::: aethergraph.services.mcp.ws_client.WsMCPClient
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 
            members: [] 

??? quote "StdioMCPClient(name, client)"
    ::: aethergraph.services.mcp.stdio_client.StdioMCPClient
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 
            members: []
---
## 2. Registration
??? quote "register_mcp_client(name, client)"
    ::: aethergraph.core.runtime.runtime_services.register_mcp_client
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "list_mcp_clients(name, client)"
    ::: aethergraph.core.runtime.runtime_services.list_mcp_clients
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

---
## 3. Service Methods

??? quote "register(name, client)"
    ::: aethergraph.services.mcp.service.MCPService.register
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "remove(name)"
    ::: aethergraph.services.mcp.service.MCPService.remove
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "has(name)"
    ::: aethergraph.services.mcp.service.MCPService.has
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "names()"
    ::: aethergraph.services.mcp.service.MCPService.names
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "list_clients()"
    ::: aethergraph.services.mcp.service.MCPService.list_clients
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "get(name='default')"
    ::: aethergraph.services.mcp.service.MCPService.get
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "open(name)"
    ::: aethergraph.services.mcp.service.MCPService.open
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "close(name)"
    ::: aethergraph.services.mcp.service.MCPService.close
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "open_all()"
    ::: aethergraph.services.mcp.service.MCPService.open_all
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "close_all()"
    ::: aethergraph.services.mcp.service.MCPService.close_all
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "call(name, tool, params=None)"
    ::: aethergraph.services.mcp.service.MCPService.call
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "list_tools(name)"
    ::: aethergraph.services.mcp.service.MCPService.list_tools
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "list_resources(name)"
    ::: aethergraph.services.mcp.service.MCPService.list_resources
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "read_resource(name, uri)"
    ::: aethergraph.services.mcp.service.MCPService.read_resource
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "set_header(name, key, value)"
    ::: aethergraph.services.mcp.service.MCPService.set_header
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 

??? quote "persist_secret(secret_name, value)"
    ::: aethergraph.services.mcp.service.MCPService.persist_secret
        options:
            show_root_heading: false
            show_root_full_path: false 
            show_source: false 


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
