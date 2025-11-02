# AetherGraph — `context.mcp()` Reference

This page documents the **Model Context Protocol (MCP)** client you obtain with `context.mcp(name)`. Use it to call tools, list resources, or read resources exposed by a remote/local MCP server over **stdio**, **WebSocket**, or **HTTP**.

> Import surface (for examples below):
> ```python
> from aethergraph.services.mcp import (
>     MCPService,
>     StdioMCPClient,
>     WsMCPClient,
>     HttpMCPClient,
> )
> ```

---

## Concepts
- **MCPService**: registry of named MCP clients (e.g., `"local"`, `"ws"`, `"http"`), handles lazy open/close and convenience calls.
- **MCPClientProtocol**: transport‑specific client implementing `open()`, `close()`, `call(tool, params)`, `list_tools()`, `list_resources()`, `read_resource(uri)`.
- **Tools**: remote RPCs exposed by the MCP server (e.g., `readFile`, `search`, `stat`).
- **Resources**: server‑advertised URIs you can `read_resource()` (e.g., `file://…`, `repo://…`).

`context.mcp(name)` returns the client registered under `name` via your process‑global `MCPService`.

---

## MCPService (registry)

### register
```
register(name: str, client: MCPClientProtocol) -> None
```
Register a client under a name.

### remove
```
remove(name: str) -> None
```
Unregister a client.

### has / names / get
```
has(name: str) -> bool
names() -> list[str]
get(name: str = "default") -> MCPClientProtocol
```
Query and retrieve clients by name.

### open / close
```
open(name: str) -> None
close(name: str) -> None
open_all() -> None
close_all() -> None
```
Manage client lifecycles. `call()/list_*()` implicitly `open()` on first use.

### call helpers
```
call(name: str, tool: str, params: dict | None = None) -> dict
list_tools(name: str) -> list[MCPTool]
list_resources(name: str) -> list[MCPResource]
read_resource(name: str, uri: str) -> dict
```
Thin wrappers to keep call sites small; auto‑open if needed.

### optional secrets/runtime headers
```
set_header(name: str, key: str, value: str) -> None
persist_secret(secret_name: str, value: str) -> None
```
`set_header()` is handy for WS/HTTP auth tokens at runtime. `persist_secret()` stores a credential via your Secrets provider (if writable).

---

## Transport clients

### StdioMCPClient
```
StdioMCPClient(cmd: list[str], env: dict[str,str] | None = None, timeout: float = 60.0)
```
Spawn a subprocess and speak JSON‑RPC over stdio.

### WsMCPClient
```
WsMCPClient(url: str, *, headers: dict[str,str] | None = None, timeout: float = 60.0, ping_interval: float = 20.0, ping_timeout: float = 10.0)
```
Connect to an MCP server over WebSocket.

### HttpMCPClient
```
HttpMCPClient(base_url: str, *, headers: dict[str,str] | None = None, timeout: float = 60.0)
```
Call an MCP server over HTTP (JSON).

---

## context.mcp(name)
```
context.mcp(name: str) -> MCPClientProtocol
```
Return the named client. Typically you register names like `"local"`, `"ws"`, `"http"` during app startup, then retrieve them inside tools/agents.

**Example**
```python
client = context.mcp("ws")
out = await client.call("search", {"q": "holography", "k": 5})
```

---

## Calling tools
```
client.call(tool: str, params: dict | None = None) -> dict
```
Invoke a remote tool by name with JSON‑serializable params.

**Parameters**
- **tool** (*str*) – Tool name (server‑defined).
- **params** (*dict, optional*) – Arguments for the tool.

**Returns**  
*dict* – Tool result payload (shape defined by the server).

**Example**
```python
# Filesystem‑like server
res = await context.mcp("local").call("readFile", {"path": "/data/notes.txt"})
text = res.get("text") or res.get("content") or ""
await context.channel().send_text(f"len={len(text)}")
```

---

## Listing tools & resources
```
client.list_tools() -> list[MCPTool]
client.list_resources() -> list[MCPResource]
client.read_resource(uri: str) -> dict
```
Enumerate server capabilities and read advertised resources.

**Example**
```python
# Tool discovery
for t in await context.mcp("http").list_tools():
    await context.channel().send_text(f"tool: {t.name} — {t.description}")

# Resource fetch
for r in await context.mcp("ws").list_resources():
    if r.uri.startswith("file://"):
        blob = await context.mcp("ws").read_resource(r.uri)
        await context.channel().send_text(f"read {r.uri} → {len(blob.get('text',''))} chars")
```

---

## End‑to‑end setup (startup)
```python
from aethergraph.services.mcp import MCPService, StdioMCPClient, WsMCPClient, HttpMCPClient
from aethergraph.v3.core.runtime.runtime_services import set_mcp_service
import os, sys

DEMO_HTTP_TOKEN = os.environ.setdefault("DEMO_HTTP_TOKEN", "demo_token_123")

mcp = MCPService()
mcp.register("local", StdioMCPClient(cmd=[sys.executable, "-m", "aethergraph.plugins.mcp.fs_server"]))
mcp.register("ws", WsMCPClient(url="ws://localhost:8765", headers={"Authorization": "Bearer demo_token_123"}))
mcp.register("http", HttpMCPClient("http://127.0.0.1:8769", headers={"Authorization": f"Bearer {DEMO_HTTP_TOKEN}"}))

set_mcp_service(mcp)  # make available to NodeContext
```

---

## Using inside a graph function
```python
from aethergraph import graph_fn

@graph_fn(name="mcp_search_demo", inputs=["q"], outputs=["text"], version="0.1.0")
async def mcp_search_demo(q: str, *, context):
    out = await context.mcp("ws").call("search", {"q": q, "k": 5})
    text = out.get("text") or out.get("content") or ""
    await context.channel().send_text(text[:200] + ("…" if len(text) > 200 else ""))
    return {"text": text}
```

---

## Choosing a transport
- **stdio**: best when you ship or control the server process (local tools, file system, Git, CLI wrappers). Minimal latency, simple auth via env.
- **WebSocket**: interactive servers that push events, need long‑lived sessions, or custom headers/tokens.
- **HTTP**: stateless request/response, easy to deploy behind gateways; good fit for cloud MCP services.

**Tip**: You can register multiple transports to the **same** logical backend under different names (`"fs-local"`, `"fs-ws"`) and switch per call.

---

## Auth & headers
- Pass headers at client construction (`headers={"Authorization": "Bearer …"}`).
- Update at runtime via `MCPService.set_header(name, key, value)` for WS/HTTP clients.
- Persist tokens via `MCPService.persist_secret(...)` when your Secrets provider supports writes.

---

## Error handling
Wrap calls to surface clear messages back to the user.
```python
try:
    res = await context.mcp("http").call("search", {"q": "mtf"})
except KeyError:
    await context.channel().send_text("Unknown MCP profile. Did you register it?")
except Exception as e:
    await context.channel().send_text(f"MCP error: {e}")
```

---

## Summary
- Register your clients at startup with `MCPService.register()` and wire the service into runtime so `context.mcp(name)` can retrieve them.
- Use `.call()` for tools, `.list_tools()/.list_resources()` for discovery, and `.read_resource()` to fetch URIs.
- Choose stdio/WS/HTTP based on deployment and interaction needs; manage auth via headers/