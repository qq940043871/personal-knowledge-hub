# MCP客户端

> 模块：MCP协议
> 更新时间：2026-03-29

---

MCP 客户端通过 HTTP 与服务端通信完成**初始化、工具发现、工具调用**三步；再经一层集成器，把 MCP 工具转换成 LLM 的 function 格式供模型调用。

## 一、客户端实现

> `MCPClient` 通过 HTTP POST `/mcp/v1/method` 与服务端通信：`connect` 发送 **initialize**（携带 protocolVersion、capabilities、clientInfo），随后 `refresh_tools` 拉取工具列表，`call_tool` 调用工具并从 `content[0].text` 取回结果。

*图：MCP 客户端三步调用流程（示意）*

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 130" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="50" width="150" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="72" text-anchor="middle" font-size="14" fill="#1e293b">1. initialize</text>
  <text x="95" y="92" text-anchor="middle" font-size="13" fill="#475569">初始化连接</text>
  <line x1="170" y1="78" x2="193" y2="78" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="195" y="50" width="150" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="270" y="72" text-anchor="middle" font-size="14" fill="#1e293b">2. tools/list</text>
  <text x="270" y="92" text-anchor="middle" font-size="13" fill="#475569">刷新工具列表</text>
  <line x1="345" y1="78" x2="368" y2="78" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="370" y="50" width="150" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="445" y="72" text-anchor="middle" font-size="14" fill="#1e293b">3. tools/call</text>
  <text x="445" y="92" text-anchor="middle" font-size="13" fill="#475569">调用工具</text>
  <line x1="520" y1="78" x2="543" y2="78" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="545" y="50" width="150" height="56" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="620" y="72" text-anchor="middle" font-size="14" fill="#1e293b">返回结果</text>
  <text x="620" y="92" text-anchor="middle" font-size="13" fill="#475569">content[0].text</text>
</svg>
```

```python
class MCPClient:
    """MCP客户端"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session_id = str(uuid.uuid4())
        self.tools: List[Dict] = []
        self.resources: List[Dict] = []
    
    async def connect(self):
        """连接服务器"""
        async with aiohttp.ClientSession() as session:
            # 初始化
            response = await session.post(
                f"{self.server_url}/mcp/v1/method",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"roots": {}, "sampling": {}},
                        "clientInfo": {"name": "my-app", "version": "1.0.0"}
                    }
                }
            )
            result = await response.json()
            
            # 获取工具列表
            await self.refresh_tools()
    
    async def refresh_tools(self):
        """刷新工具列表"""
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                f"{self.server_url}/mcp/v1/method",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
            )
            result = await response.json()
            self.tools = result.get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """调用工具"""
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                f"{self.server_url}/mcp/v1/method",
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
            )
            result = await response.json()
            return result.get("content", [{}])[0].get("text")
```

---

## 二、集成到LLM

> `MCPToolIntegration` 把 MCP 工具转换为 **LLM function 格式**（`name`、`description`、`inputSchema` → `parameters`），并把 LLM 发起的 tool_call 转回 MCP 的 `tools/call` 执行。

```python
class MCPToolIntegration:
    """MCP工具集成"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
    
    def get_tools_for_llm(self) -> List[Dict]:
        """转换为LLM工具格式"""
        tools = []
        for tool in self.mcp_client.tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"]
                }
            })
        return tools
    
    async def handle_tool_call(self, tool_call: Dict) -> str:
        """处理LLM的工具调用"""
        tool_name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]
        
        return await self.mcp_client.call_tool(tool_name, arguments)
```

---

*下一步：函数调用原理*
