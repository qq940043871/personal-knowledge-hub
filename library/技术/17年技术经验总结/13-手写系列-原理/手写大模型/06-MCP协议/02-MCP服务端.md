# MCP服务端

> 模块：MCP协议
> 更新时间：2026-03-29

---

MCP 服务端负责承载协议方法：基于 FastAPI 暴露请求入口与 SSE 事件流，并把请求按 `method` 分发到对应处理器；工具则以 JSON Schema 定义入参。

## 一、服务端实现

> `MCPServer` 基于 FastAPI 实现：`POST /mcp/v1/method` 接收 MCP 请求并按 `method` 分发（tools/list、tools/call、resources/list、initialize），`GET /mcp/v1/events` 提供 SSE 事件流；工具、资源、提示分别存放在三个字典中。

*图：MCP 服务端请求分发流程（示意）*

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="220" y="20" width="280" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="14" fill="#1e293b">客户端请求 POST /mcp/v1/method</text>
  <line x1="360" y1="64" x2="360" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="250" y="84" width="220" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="111" text-anchor="middle" font-size="14" fill="#1e293b">按 method 字段分发</text>
  <line x1="470" y1="106" x2="516" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="520" y="84" width="180" height="44" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="610" y="111" text-anchor="middle" font-size="13" fill="#1e293b">未知方法抛 ValueError</text>
  <line x1="360" y1="128" x2="97" y2="146" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="128" x2="272" y2="146" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="128" x2="447" y2="146" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="128" x2="622" y2="146" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="20" y="150" width="155" height="60" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="97" y="174" text-anchor="middle" font-size="13" fill="#1e293b">tools/list</text>
  <text x="97" y="194" text-anchor="middle" font-size="13" fill="#475569">列出工具</text>
  <rect x="195" y="150" width="155" height="60" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="272" y="174" text-anchor="middle" font-size="13" fill="#1e293b">tools/call</text>
  <text x="272" y="194" text-anchor="middle" font-size="13" fill="#475569">调用工具</text>
  <rect x="370" y="150" width="155" height="60" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="447" y="174" text-anchor="middle" font-size="13" fill="#1e293b">resources/list</text>
  <text x="447" y="194" text-anchor="middle" font-size="13" fill="#475569">列出资源</text>
  <rect x="545" y="150" width="155" height="60" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="622" y="174" text-anchor="middle" font-size="13" fill="#1e293b">initialize</text>
  <text x="622" y="194" text-anchor="middle" font-size="13" fill="#475569">初始化连接</text>
</svg>
```

```python
class MCPServer:
    """MCP服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.prompts: Dict[str, Prompt] = {}
        self.app = FastAPI()
        self.setup_routes()
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.post("/mcp/v1/method")
        async def handle_method(request: MCPRequest):
            """处理MCP请求"""
            method = request.method
            params = request.params or {}
            
            if method == "tools/list":
                return await self.list_tools()
            elif method == "tools/call":
                return await self.call_tool(params)
            elif method == "resources/list":
                return await self.list_resources()
            elif method == "initialize":
                return await self.initialize(params)
            else:
                raise ValueError(f"Unknown method: {method}")
        
        @self.app.get("/mcp/v1/events")
        async def events(request: Request):
            """SSE事件流"""
            async def event_generator():
                # 实现SSE推送
                ...
            return EventSourceResponse(event_generator())
    
    async def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    async def call_tool(self, params: Dict) -> Dict:
        """调用工具"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        result = await tool.execute(arguments)
        return {"content": [{"type": "text", "text": str(result)}]}
```

---

## 二、工具定义

> 工具用 `Tool` 数据类定义：`name` + `description` + **JSON Schema 形式的 `input_schema`**；示例 `WeatherTool` 演示了天气查询工具的完整实现（`city` 必填、`country` 默认 `CN`）。

```python
@dataclass
class Tool:
    """MCP工具"""
    name: str
    description: str
    input_schema: Dict  # JSON Schema
    
    async def execute(self, arguments: Dict) -> Any:
        raise NotImplementedError


class WeatherTool(Tool):
    """天气查询工具"""
    
    name = "weather"
    description = "查询指定城市的天气信息"
    input_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称"
            },
            "country": {
                "type": "string",
                "description": "国家代码"
            }
        },
        "required": ["city"]
    }
    
    async def execute(self, arguments: Dict) -> Dict:
        city = arguments["city"]
        country = arguments.get("country", "CN")
        return await self.weather_api.get_weather(city, country)
```

---

*下一步：MCP客户端*
