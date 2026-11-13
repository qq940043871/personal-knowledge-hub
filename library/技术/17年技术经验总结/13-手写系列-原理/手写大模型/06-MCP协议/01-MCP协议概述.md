# MCP协议概述

> 模块：MCP协议
> 更新时间：2026-03-29

---

本文从定义、协议结构、集成架构三个方面概述 MCP 协议。

## 一、MCP定义

> MCP 是 **Anthropic 推出的模型上下文协议**（Model Context Protocol），提供标准化的工具/资源定义，支持双向 JSON-RPC 通信，定位类似 OpenAI 的 Function Calling；核心概念有三个：Resources、Tools、Prompts。

*图：MCP 三大核心概念（示意）*

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="230" y="20" width="260" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="15" fill="#1e293b">MCP 协议核心概念</text>
  <line x1="330" y1="64" x2="130" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="64" x2="360" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="390" y1="64" x2="590" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="30" y="110" width="200" height="96" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="130" y="136" text-anchor="middle" font-size="14" fill="#1e293b">Resources（资源）</text>
  <text x="130" y="160" text-anchor="middle" font-size="13" fill="#475569">可访问的外部数据</text>
  <text x="130" y="180" text-anchor="middle" font-size="13" fill="#475569">文件、API、数据库等</text>
  <rect x="260" y="110" width="200" height="96" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="136" text-anchor="middle" font-size="14" fill="#1e293b">Tools（工具）</text>
  <text x="360" y="160" text-anchor="middle" font-size="13" fill="#475569">LLM 可调用的函数</text>
  <text x="360" y="180" text-anchor="middle" font-size="13" fill="#475569">带参数 schema</text>
  <rect x="490" y="110" width="200" height="96" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="590" y="136" text-anchor="middle" font-size="14" fill="#1e293b">Prompts（提示模板）</text>
  <text x="590" y="160" text-anchor="middle" font-size="13" fill="#475569">预定义的提示词</text>
  <text x="590" y="180" text-anchor="middle" font-size="13" fill="#475569">可参数化</text>
</svg>
```

```
MCP（Model Context Protocol）：
  - Anthropic推出的模型上下文协议
  - 标准化的工具/资源定义
  - 支持双向JSON-RPC通信
  - 类似OpenAI的Function Calling

核心概念：
  1. Resources（资源）
     - 可访问的外部数据
     - 文件、API、数据库等
  
  2. Tools（工具）
     - LLM可调用的函数
     - 带参数schema
  
  3. Prompts（提示模板）
     - 预定义的提示词
     - 可参数化
```

---

## 二、协议结构

> MCP 消息即 JSON-RPC 消息：`Request`（method + params）与 `Response`（result / error）；核心方法覆盖**初始化、资源、工具、提示**四组。

```python
class MCPMessage:
    """MCP消息"""
    
    @dataclass
    class Request:
        jsonrpc: str = "2.0"
        id: Union[str, int] = None
        method: str = None
        params: Dict = None
    
    @dataclass
    class Response:
        jsonrpc: str = "2.0"
        id: Union[str, int] = None
        result: Any = None
        error: Dict = None


# 核心方法
MCP_METHODS = {
    # 初始化
    "initialize": "初始化连接",
    "initialized": "初始化完成",
    
    # 资源
    "resources/list": "列出资源",
    "resources/read": "读取资源",
    "resources/subscribe": "订阅资源",
    
    # 工具
    "tools/list": "列出工具",
    "tools/call": "调用工具",
    
    # 提示
    "prompts/list": "列出提示",
    "prompts/get": "获取提示",
}
```

---

## 三、集成架构

> 集成架构分两层：LLM 应用内的 **MCP Client**（维护连接、序列化/反序列化、重试/超时处理），通过 JSON-RPC（HTTP/SSE/WebSocket）连接 **MCP Server** 的 Tool Handler（工具注册、参数验证、结果处理）。

```
┌─────────────────────────────────────────────────────────┐
│                    LLM应用                               │
│  ┌─────────────────────────────────────────────────┐  │
│  │              MCP Client                            │  │
│  │  - 维护连接                                    │  │
│  │  - 序列化/反序列化                             │  │
│  │  - 重试/超时处理                              │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                    JSON-RPC over
                    HTTP/SSE/WebSocket
                            │
┌─────────────────────────────────────────────────────────┐
│                    MCP Server                            │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Tool Handler                         │  │
│  │  - 工具注册                                   │  │
│  │  - 参数验证                                   │  │
│  │  - 结果处理                                   │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

*下一步：MCP服务端*
