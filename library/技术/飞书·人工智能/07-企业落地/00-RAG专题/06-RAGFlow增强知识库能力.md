# RAGFLOW 增强知识库能力

你这个思路非常精准：**保留 Dify 做平台/编排/前端，用 MCP 把 RAGFlow 当成“外挂 RAG 引擎”补能力**，完全符合你现有栈（LangChain+LangGraph + Dify + MinerU + LLMFactory + GPUStack）的全链路离线部署。

下面我把 **MCP 对接的原理、优势、实施步骤、选型理由** 一次性讲透，可直接用于方案说明/面试口述。

*图：Dify 通过 MCP 对接 RAGFlow 的链路（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 340" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="30" y="28" width="110" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="85" y="56" text-anchor="middle" font-size="14" fill="#1e293b">用户提问</text>
  <line x1="140" y1="51" x2="228" y2="51" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="230" y="28" width="240" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="350" y="47" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">Dify 应用</text>
  <text x="350" y="66" text-anchor="middle" font-size="13" fill="#475569">聊天助手 / Chatflow 工作流</text>
  <line x1="470" y1="51" x2="518" y2="51" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="520" y="28" width="170" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="605" y="47" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">Dify 内置</text>
  <text x="605" y="66" text-anchor="middle" font-size="13" fill="#475569">MCP Client（零代码）</text>
  <line x1="605" y1="74" x2="605" y2="108" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="110" y="110" width="580" height="40" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="400" y="135" text-anchor="middle" font-size="14" fill="#1e293b">MCP 标准协议「数据线」：HTTP+SSE 流式 · 自动发现工具 · 自动鉴权 · 即插即用</text>
  <line x1="200" y1="150" x2="200" y2="188" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="110" y="190" width="180" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="200" y="211" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">RAGFlow</text>
  <text x="200" y="231" text-anchor="middle" font-size="13" fill="#475569">MCP Server</text>
  <line x1="290" y1="216" x2="328" y2="216" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="330" y="190" width="380" height="52" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="520" y="211" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">RAGFlow 专业 RAG 引擎</text>
  <text x="520" y="231" text-anchor="middle" font-size="13" fill="#475569">解析→分块→BM25+向量+重排→引用溯源</text>
  <line x1="520" y1="242" x2="520" y2="270" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="110" y="272" width="580" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="400" y="299" text-anchor="middle" font-size="14" fill="#1e293b">GPUStack 算力底座：统一调度 LLM / Embedding / Rerank / MinerU（全程内网离线）</text>
</svg>

---

## 一、为什么用 MCP 对接（而不是 API/外部知识库）

### 1. MCP 是官方标准、零代码、稳定
+ Dify v1.6.0+ **原生内置 MCP Client**（不用插件、不用写代码）
+ RAGFlow v0.18.0+ **原生内置 MCP Server**（专门给外部调用 RAG）
+ 协议统一：**HTTP+SSE 流式**，自动发现工具、自动鉴权、自动参数解析

### 2. 比“外部知识库/HTTP 节点”强在哪
+ **自动工具发现**：Dify 一键添加 RAGFlow MCP 后，自动加载：
    - `rag_retrieval`（精准检索）
    - `rag_chunk`（分块召回）
    - `rag_document`（文档列表）

不用手动写 URL/Header/Body
+ **流式返回**：支持 SSE 实时回传，问答更流畅
+ **状态与权限**：MCP 带会话/租户隔离，适合多产品线
+ **可观测**：Dify 工具面板直接看调用日志、成功率、耗时

### 3. 对你技术栈的价值（核心）
+ **不破坏原有架构**：Dify 依然是入口、权限、前端、工作流底座
+ **RAG 能力瞬间升级**：用 RAGFlow 强解析、强分块、BM25+向量+重排、层级索引、引用溯源
+ **全链路离线**：MCP 走内网 HTTP，全程无外网依赖
+ **和 LangGraph 互补**：
    - Dify+MCP：**简单 RAG 问答**（零代码）
    - LangGraph+RAGFlow SDK：**复杂多跳/多文档/决策流**（可编程）

---

## 二、MCP 对接完整实施步骤（可直接照做）

### 1. 启动 RAGFlow MCP Server（离线部署）

```bash
# docker-compose 追加（或直接启动）
ragflow-mcp:
  image: infiniflow/ragflow-mcp:latest
  ports:
    - "9382:9382"
  environment:
    - MODE=self-host                  # 单租户/多租户选host
    - BASE_URL=http://ragflow:8080    # RAGFlow 内网地址
    - API_KEY=sk-********************* # 从 RAGFlow 后台生成
    - HOST=0.0.0.0
    - PORT=9382
  depends_on:
    - ragflow
```

+ 验证：`curl http://内网IP:9382` 返回 MCP 元信息

### 2. Dify 配置 MCP Client（零代码）
1. Dify 后台 → **工具 → MCP → 添加 MCP Server（HTTP）**
2. 填写：
    - 名称：RAGFlow-RAG
    - Server URL：`http://<RAGFlow-MCP-IP>:9382`
    - API Key：填入上面的 `sk-***`
    - 图标：选知识库
3. 保存 → **自动发现 3～5 个 RAG 工具**

### 3. 在 Dify 应用中使用（两种方式）

#### 方式A：聊天助手（自动调用）
+ 启用 **工具调用** → 勾选 `rag_retrieval`
+ 提示词简单写：

> 有问题先调用 rag_retrieval 查询知识库，**必须引用来源**，不知道就说“未找到”。

+ 效果：用户提问 → Dify Agent → MCP → RAGFlow 高精度检索 → 带引用回答

#### 方式B：工作流（Chatflow，可控）
+ 开始 → **MCP 工具节点**（选 rag_retrieval）
+ 输入：`query=$query`、`top_k=5`、`score_threshold=0.7`
+ 输出：把 RAGFlow 召回的**原文+来源+分数**传给 LLM
+ 优势：可加**判断节点**（置信度<0.7拒答/转人工）、**多轮召回**、**格式强化**

---

## 三、这套方案的核心选型理由（面试/汇报直接用）

### 1. 架构合理性（解耦最优）
+ **Dify 定位**：应用平台、前端、权限、工作流、多模型管理、API 网关
+ **RAGFlow 定位**：专业 RAG 引擎（文档解析→分块→向量→混合检索→重排→溯源）
+ **MCP 定位**：标准化“数据线”，**即插即用、不侵入、可替换**

### 2. 能力补强（精准解决 Dify RAG 弱）
+ **文档解析**：RAGFlow（MinerU 级）→ 解决 PDF/表格/公式/扫描件乱序
+ **分块策略**：智能语义分块、父子块、层级 → 比 Dify 固定分块强太多
+ **检索精度**：BM25+向量+Rerank 三阶段 → 比 Dify 基础混合召回高 20%+
+ **幻觉抑制**：**强制引用来源、置信度阈值、拒答机制** → Dify 几乎没有
+ **知识管理**：RAGFlow 专业知识库、版本、权限、批量导入 → Dify 知识库偏简单

### 3. 全链路离线可控（企业必备）
+ 全程内网：Dify ↔ MCP ↔ RAGFlow ↔ MinerU ↔ GPUStack ↔ LLMFactory
+ 无云依赖、无外网、数据不出域
+ 可监控、可扩容、可灰度、可回滚

### 4. 与你现有栈完美融合
+ **MinerU**：RAGFlow 默认用 MinerU 做深度解析 → 文档质量拉满
+ **LLMFactory**：Dify/RAGFlow 都可接入微调后的领域模型 → 幻觉更低
+ **GPUStack**：统一调度 LLM/Embedding/Rerank/MinerU → 资源利用率最高
+ **LangChain+LangGraph**：复杂流程用 LangGraph 直连 RAGFlow SDK，简单场景用 Dify+MCP → **高低搭配、全覆盖**

---

## 四、一句话总结（3分钟口述版）

> 采用 **Dify 作为平台底座 + MCP 协议对接 RAGFlow**，形成 **平台+编排+专业RAG+模型+算力** 的完整闭环。

我采用 **Dify 作为平台底座 + MCP 协议对接 RAGFlow** 的方案：

+ 保留 Dify 擅长的**前端、权限、工作流、多模型管理、快速上线**；
+ 通过 **MCP 标准协议** 零代码接入 RAGFlow 的**专业 RAG 能力**（强解析、智能分块、三重混合检索、引用溯源）；
+ 完美解决 Dify 原生 RAG 弱、幻觉高、复杂文档处理差的问题；
+ 全程**离线私有化、全链路可控、可扩展、稳定生产级**；
+ 与现有栈（LangChain+LangGraph、MinerU、LLMFactory、GPUStack）深度融合，形成 **平台+编排+专业RAG+模型+算力** 的完整闭环。

---

要不要我把 **Dify+RAGFlow MCP 对接的关键配置、常见问题、性能调参** 整理成一页可直接复制的**实施清单**？
