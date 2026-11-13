# MCP工具定义

> 模块：MCP协议
> 更新时间：2026-03-29

---

MCP 工具定义围绕三件事：**Schema 规范**（name / description / inputSchema）、**定义实现**（ToolParameter → JSON Schema → 参数校验）、**注解注册**（ToolRegistry 装饰器）。

## 一、Tool Schema规范

> MCP 工具定义三要素：**name**（工具唯一标识，如 `weather.get_forecast`）、**description**（工具功能描述，供 LLM 理解何时调用）、**inputSchema**（JSON Schema 格式的参数定义，含 type、properties、required）。

```
MCP工具定义结构：
  - name：工具唯一标识（如 "weather.get_forecast"）
  - description：工具功能描述（供LLM理解何时调用）
  - inputSchema：JSON Schema格式的参数定义
    - type: "object"
    - properties: 参数字段定义
    - required: 必填字段列表
```

---

## 二、Tool定义实现

> `ToolDefinition` 用 `ToolParameter` 列表描述参数，`to_schema` 导出 JSON Schema，`validate_input` 基于 **jsonschema** 校验入参，失败抛 `ValueError`。

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import jsonschema


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str              # string / number / integer / boolean / array / object
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Any = None


@dataclass
class ToolDefinition:
    """MCP工具定义"""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    handler: Optional[Callable] = None

    def to_schema(self) -> Dict:
        """导出为JSON Schema格式"""
        properties = {}
        required = []

        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = enum
            if param.default is not None:
                prop["default"] = param.default

            properties[param.name] = prop
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        }

    def validate_input(self, arguments: Dict) -> bool:
        """校验输入参数"""
        schema = self.to_schema()["inputSchema"]
        try:
            jsonschema.validate(instance=arguments, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            raise ValueError(f"参数校验失败: {e.message}")
```

---

## 三、工具注解与注册

> `ToolRegistry` 提供装饰器注册（`@registry.tool(...)`）、Schema 列表输出与统一调用入口；`call_tool` 依次完成**查找工具 → 参数校验 → 执行 handler**，任一步失败都抛 `ValueError`。

*图：工具调用流程（示意）*

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 340" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="220" y="20" width="280" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="14" fill="#1e293b">call_tool(name, arguments)</text>
  <line x1="360" y1="64" x2="360" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="220" y="84" width="280" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="111" text-anchor="middle" font-size="14" fill="#1e293b">1. 查找工具 registry.tools</text>
  <text x="595" y="111" text-anchor="middle" font-size="13" fill="#dc2626">未找到 → ValueError</text>
  <line x1="360" y1="128" x2="360" y2="144" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="220" y="148" width="280" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="175" text-anchor="middle" font-size="14" fill="#1e293b">2. 参数校验 jsonschema.validate</text>
  <text x="595" y="175" text-anchor="middle" font-size="13" fill="#dc2626">校验失败 → ValueError</text>
  <line x1="360" y1="192" x2="360" y2="208" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="220" y="212" width="280" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="239" text-anchor="middle" font-size="14" fill="#1e293b">3. 执行 handler</text>
  <text x="595" y="239" text-anchor="middle" font-size="13" fill="#dc2626">无 handler → ValueError</text>
  <line x1="360" y1="256" x2="360" y2="272" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="220" y="276" width="280" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="303" text-anchor="middle" font-size="14" fill="#1e293b">返回执行结果</text>
</svg>
```

```python
from functools import wraps


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}

    def tool(self, name: str, description: str,
             parameters: List[ToolParameter] = None):
        """工具注册装饰器"""
        def decorator(func: Callable):
            definition = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters or [],
                handler=func,
            )
            self.tools[name] = definition

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self.tools.get(name)

    def list_tools(self) -> List[Dict]:
        """列出所有工具的Schema"""
        return [tool.to_schema() for tool in self.tools.values()]

    async def call_tool(self, name: str, arguments: Dict) -> Any:
        """调用工具"""
        tool = self.tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        # 参数校验
        tool.validate_input(arguments)

        # 执行
        if tool.handler:
            return await tool.handler(**arguments)
        raise ValueError(f"Tool {name} has no handler")


# 使用示例
registry = ToolRegistry()

@registry.tool(
    name="weather.get_forecast",
    description="获取指定城市的天气预报",
    parameters=[
        ToolParameter(
            name="city",
            type="string",
            description="城市名称",
            required=True,
        ),
        ToolParameter(
            name="days",
            type="integer",
            description="预报天数（1-7）",
            required=False,
            default=3,
        ),
    ]
)
async def get_forecast(city: str, days: int = 3) -> Dict:
    return {"city": city, "days": days, "forecast": "晴天"}
```

---

*（本系列后续篇章未完成）*
