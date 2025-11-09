# Tutorial 6: Use External Tools — The MCP Example

AetherGraph supports external tool integration via the **Model Context Protocol (MCP)** — a simple JSON‑RPC 2.0 interface for listing and calling tools, reading resources, and managing structured outputs from remote services. In short, MCP lets your graph talk to **anything** that can expose a compliant interface: local CLI utilities, web services, or even another AI system.

---

## 1. What Is MCP?

The **Model Context Protocol** defines a standard way for an AI or orchestration framework to:

* **List tools** that an external process or service provides.
* **Call those tools** with structured arguments.
* **List or read resources**, such as files, datasets, or model outputs.

AetherGraph’s `MCPService` provides a unified layer for managing multiple MCP clients — e.g. a local subprocess (`StdioMCPClient`), a WebSocket endpoint (`WsMCPClient`), or an HTTP service (`HttpMCPClient`).

> Each MCP client conforms to a minimal contract:
>
> ```python
> class MCPClientProtocol:
>     async def list_tools(self) -> List[MCPTool]: ...
>     async def call(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]: ...
>     async def list_resources(self) -> List[MCPResource]: ...
>     async def read_resource(self, uri: str) -> Dict[str, Any]: ...
> ```

You can register many clients under names (e.g. `default`, `local`, `remote`), and access them via `context.mcp(name)`.

---

## 2. Minimal Example — Query a Local MCP Tool

Suppose you have a local script or service exposing MCP over stdio. You can wrap it with `StdioMCPClient`:

```python
from aethergraph.services.mcp.stdio_client import StdioMCPClient
from aethergraph.services.mcp.service import MCPService

# Initialize the service manually (usually handled by container)
client = StdioMCPClient(["python", "my_mcp_server.py"])
mcp = MCPService({"default": client})

# Example call to a tool named "summarize_text"
async def main():
    await mcp.open("default")
    tools = await mcp.list_tools("default")
    print("Available tools:", [t.name for t in tools])

    result = await mcp.call("default", "summarize_text", {"text": "Hello MCP!"})
    print("Result:", result)

asyncio.run(main())
```

This works the same if you use a WebSocket or HTTP‑based MCP server — just replace the client class.

---

## 3. Inside AetherGraph — Access via NodeContext

In real usage, you never have to wire the service manually. The `NodeContext` injects it automatically, so any `graph_fn` or `@tool` can access it:

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="mcp_query")
async def mcp_query(*, context: NodeContext):
    # List tools available on the default MCP server
    tools = await context.mcp("default").list_tools()
    context.logger().info(f"Available MCP tools: {[t.name for t in tools]}")

    # Call a specific tool
    result = await context.mcp("default").call("summarize_text", {"text": "Explain MCP in one line."})
    await context.channel().send_text(f"Summary: {result['summary']}")

    return {"result": result}
```

Run this function via `run(graph, inputs)` or within a larger workflow — it will connect automatically to the configured MCP client.

---

## 4. When to Use MCP

MCP is useful when you want to:

* Bridge **external AI systems** (like a local LM Studio model or an in‑house LLM server) into AetherGraph.
* Integrate **existing Python tools or APIs** without writing new wrappers.
* Query **live data services** (e.g., weather, finance, or database APIs) through a JSON‑RPC layer.

Because MCP uses async JSON‑RPC, it can easily be multiplexed across multiple nodes or graphs — even concurrently.

---

## 5. Available Clients

| Client Type   | Class            | Transport               | Use Case                      |
| ------------- | ---------------- | ----------------------- | ----------------------------- |
| **Stdio**     | `StdioMCPClient` | stdin/stdout subprocess | Run local CLI tools           |
| **WebSocket** | `WsMCPClient`    | persistent WS channel   | Long‑lived AI services        |
| **HTTP**      | `HttpMCPClient`  | RESTful endpoint        | Web APIs with JSON‑RPC routes |

You can register any number of them:

```python
from aethergraph.services.mcp.ws_client import WsMCPClient
mcp = MCPService({
    "default": WsMCPClient("wss://example.com/mcp"),
    "local": StdioMCPClient(["python", "my_local_tool.py"])
})
```

---

## 6. Combined Example — HTTP Tool Call in Graph

```python
from aethergraph import graph_fn, NodeContext

@graph_fn(name="fetch_weather")
async def fetch_weather(city: str, *, context: NodeContext):
    # Connect to HTTP MCP backend
    result = await context.mcp("default").call("get_weather", {"city": city})
    
    report = result.get("report", "No data returned.")
    await context.channel().send_text(f"Weather in {city}: {report}")
    return {"city": city, "report": report}
```

This looks like any other AetherGraph node — but the heavy lifting happens externally. MCP makes any compliant server a first‑class citizen in your graphs.

---

## 7. Notes & Tips

* **Auto‑Reconnect:** MCP clients auto‑reopen when disconnected, so you can safely call `context.mcp("local")` multiple times.
* **Multiple Servers:** You can connect to multiple MCPs simultaneously for different tool domains.
<!-- * **Secrets Integration:** Use `persist_secret()` or your workspace’s `Secrets` service to store API keys or headers securely. -->
* **Chained Tools:** Results from MCP calls are just Python dicts — they can be piped to other `@tool`s or stored as artifacts for later retrieval.

---

### Summary

MCP integration turns AetherGraph into a universal **agent‑to‑agent protocol bridge**. You can:

1. Connect external AI or data tools via stdio, WebSocket, or HTTP.
2. Access them with one unified API: `context.mcp(name)`.
3. Call, list, and read resources without writing custom adapters.

In the next section, we’ll explore **Extending Services** — showing how to register your own MCP‑like service or log LLM prompts for inspection.

---

## Register a Client & Expose It to `context.mcp(...)`

Before using the examples above, wire a client and make it available on the NodeContext:

```python
from aethergraph.server import start
from aethergraph.services.mcp.service import MCPService
from aethergraph.services.mcp.clients.stdio import StdioMCPClient
from aethergraph.runtime.services import set_mcp_service
import sys

# 1) Boot the sidecar (enables IO + resumptions for adapters)
start()

# 2) Create the MCP service and register a local stdio MCP server
svc = MCPService()
svc.register("local", StdioMCPClient(cmd=[sys.executable, "-m", "aethergraph.plugins.mcp.fs_server"]))

# 3) Make it available on the NodeContext via context.mcp(...)
set_mcp_service(svc)
```

### Invoke from a graph with `context.mcp("local")`

```python
from aethergraph import graph_fn
from aethergraph.runtime.context import NodeContext

@graph_fn(name="mcp.local_list", version="0.1.0", inputs=["path"]) 
async def mcp_local_list(path: str, *, context: NodeContext):
    """
    Calls the local MCP 'fs_server' over stdio:
      - tools: listDir, readFile, writeFile, stat (your server may expose a subset)
    """
    # A) discover tools
    tools = await context.mcp("local").list_tools()
    # B) list directory
    listing = await context.mcp("local").call("listDir", {"path": path})
    return {"tools": tools[:5], "list_dir": listing}
```

> You can still use the HTTP and WebSocket client shapes from earlier; just register them with `MCPService.register(name, client)` and call via `context.mcp(name)`.

---

## No MCP server? Use a native service

If you don’t want to start a server to “make tools,” implement a **native AetherGraph service** and register it on the container. Then call it as `context.my_service()` from your nodes. This avoids network setup while keeping the same agent orchestration benefits. MCP remains ideal when you need language/runtime isolation or want to interoperate with third‑party tools.

## Wrap-up

You now have a working pattern to: (1) register an MCP client once, (2) invoke tools from any graph via `context.mcp("local")`, and (3) keep outputs traceable with Artifacts/Memory when it matters.
