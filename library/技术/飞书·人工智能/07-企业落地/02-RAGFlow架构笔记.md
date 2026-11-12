# RAGFlow架构笔记

## High-Level Architecture

> 图片为Agent Flow System架构图。前端层有web/ React Application、Flow Canvas (ReactFlow)、Chat Interface等；API Gateway连接多个组件；Core Processing包括ragflow_server.py等；LLM Integration有rag/llm/ LLM Integration等；Document Processing有deepdoc/ Document Processing等；External Services有OpenAI、BGE、BCE、Jina models等；Storage Layer有MySQL、Redis Task Queues、MinIO Object Storage、Elasticsearch/Infinity等。该图直观呈现了系统各组件及数据流向。

*图：RAGFlow 高层架构分层（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 400" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw1" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="60" y="20" width="600" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="40" text-anchor="middle" font-size="12" fill="#475569">前端层</text>
  <text x="360" y="60" text-anchor="middle" font-size="13" fill="#1e293b">web/ React Application、Flow Canvas (ReactFlow)、Chat Interface</text>
  <line x1="360" y1="74" x2="360" y2="86" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="60" y="88" width="600" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="112" text-anchor="middle" font-size="14" fill="#1e293b">API Gateway</text>
  <line x1="360" y1="130" x2="360" y2="142" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="60" y="144" width="600" height="52" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="164" text-anchor="middle" font-size="13" fill="#1e293b">Core Processing</text>
  <text x="360" y="184" text-anchor="middle" font-size="12" fill="#475569">ragflow_server.py 等</text>
  <line x1="360" y1="198" x2="360" y2="210" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="60" y="212" width="600" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="236" text-anchor="middle" font-size="13" fill="#1e293b">LLM Integration（rag/llm/） · Document Processing（deepdoc/）</text>
  <line x1="360" y1="254" x2="360" y2="266" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="60" y="268" width="600" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="288" text-anchor="middle" font-size="13" fill="#1e293b">External Services</text>
  <text x="360" y="308" text-anchor="middle" font-size="12" fill="#475569">OpenAI、BGE、BCE、Jina models</text>
  <line x1="360" y1="322" x2="360" y2="334" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="60" y="336" width="600" height="52" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="356" text-anchor="middle" font-size="13" fill="#1e293b">Storage Layer</text>
  <text x="360" y="376" text-anchor="middle" font-size="12" fill="#475569">MySQL、Redis Task Queues、MinIO Object Storage、Elasticsearch/Infinity</text>
</svg>

## Core Components and Code Mapping

### LLM Integration Architecture

> 图片展示了RAGFlow的LLM集成架构图。左侧为Configuration，包含api/db/models.py中的LLM和TenantLLM，以及docker/service conf.yaml.template。中间是LLM抽象层，有api/db/services/llm_service.py和rag/llm/link.py。右侧是LLM实现层，包括rag/llm/chat_model.py，其下有ChatModel、Model Types、Provider Implementations等分支，各分支对应不同模型文件。该图直观呈现了LLM集成架构的结构与各部分关系。

## Data Flow Architecture

> 图片展示了Agent Flow System中Chat Interface的流程架构图。从Query Input开始，经api/apps/conversation_app.py完成，进入Query Processing，再通过rag/finetuned_model.py嵌入，连接Knowledge Retrieval，分别与Elasticsearch和Elasticsearch Infinity进行vector_search和full_text_search，获取results后，经rag/apps/retrieval.py构建context，再由rag/finetuned_model.py chat，最后通过rag/apps/retrieval.py提取relations，完成Response Delivery，经api/libs/services/conversation_service.py发送。

*图：Chat Interface 查询处理数据流（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 260" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw2" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="95" y="24" width="110" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="150" y="50" text-anchor="middle" font-size="13" fill="#1e293b">Query Input</text>
  <line x1="207" y1="46" x2="233" y2="46" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="235" y="24" width="210" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="340" y="50" text-anchor="middle" font-size="13" fill="#1e293b">api/apps/conversation_app.py</text>
  <line x1="447" y1="46" x2="473" y2="46" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="475" y="24" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="550" y="50" text-anchor="middle" font-size="13" fill="#1e293b">Query Processing</text>
  <path d="M550,70 L550,86 L125,86 L125,102" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="25" y="104" width="200" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="125" y="130" text-anchor="middle" font-size="13" fill="#1e293b">rag/finetuned_model.py 嵌入</text>
  <line x1="227" y1="126" x2="253" y2="126" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="255" y="104" width="170" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="340" y="130" text-anchor="middle" font-size="13" fill="#1e293b">Knowledge Retrieval</text>
  <line x1="427" y1="126" x2="453" y2="126" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="455" y="104" width="230" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="570" y="130" text-anchor="middle" font-size="13" fill="#1e293b">vector_search / full_text_search</text>
  <path d="M570,150 L570,166 L120,166 L120,182" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="5" y="184" width="230" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="120" y="206" text-anchor="middle" font-size="13" fill="#1e293b">获取 results</text>
  <text x="120" y="224" text-anchor="middle" font-size="12" fill="#475569">构建 context（rag/apps/retrieval.py）</text>
  <line x1="237" y1="212" x2="263" y2="212" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="265" y="184" width="230" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="380" y="206" text-anchor="middle" font-size="13" fill="#1e293b">rag/finetuned_model.py chat</text>
  <text x="380" y="224" text-anchor="middle" font-size="12" fill="#475569">rag/apps/retrieval.py 提取 relations</text>
  <line x1="497" y1="212" x2="523" y2="212" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="525" y="184" width="190" height="56" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="620" y="206" text-anchor="middle" font-size="13" fill="#1e293b">Response Delivery</text>
  <text x="620" y="224" text-anchor="middle" font-size="12" fill="#475569">conversation_service.py</text>
</svg>

## Deployment and Infrastructure

> 图片展示了Agent Flow System的架构图。左侧有Compose Profiles环境、Search Backends等组件，中间是Configuration Manager、Storage Services等，右侧是Container Orchestration下的docker-compose.yml等文件。下方是Application Services，包括ragflow-server、ragflow-task-executor等。该图与文档中“Agent Flow System”章节对应，直观呈现了系统各组件及文件的关联关系。

### Document Processing Pipeline Architecture

> 图片展示了文档处理管道架构图。从Task Queue System接收任务，经Redis Task Queue传递至TaskExecutor，其下有Document Processing和Storage Operations分支。Document Processing包含DocumentService、build_chunks()、embedding()等操作，Storage Operations涉及settings.docStoreConn、STORAGE_IMPL、RedisDistributedLock等。该图与文档中“Document Processing Pipeline Architecture”章节对应，直观呈现了文档处理流程及各组件关系。

### Authentication Flow

> 注：原导出此节仅含一张图片（飞书死链已移除），无文字内容。

## Integration Architecture

> 图片展示了RAGFlow系统架构图。左侧为外部客户端，包括Web应用React前端、SDK、MCP客户端等；中间是API网关层，有document、conversation、chunk等应用；右侧是服务集成，有storage、LLMBundle、redis_conn等。各部分通过箭头连接，表示数据或服务的流向。该图与文档中“Integration Architecture”部分对应，直观呈现了系统各组件间的交互关系。

## Embedding Generation and Vector Storage

### Architecture Diagram

> 图片展示了文档处理流水线架构图。从文档处理开始，经文档切分、实体和关系抽取，进入图构建环节，通过generate_subgraph()和merge_subgraph()生成局部子图，合并为全局知识图谱。随后进行图增强，包括实体解析、社区检测，生成社区报告。最后是存储集成，与文档存储结合，实现图增强检索。该图与文档中“Document Processing Pipeline Architecture”部分对应，直观呈现了文档处理的流程。

## Agent Flow System

> 图片展示了Agent Flow System的架构图。左侧为Frontend Flow Editor，包含FlowCanvas、useGraphStore、nodeTypes、FormDrawer等组件。右侧是Storage & API，有canvas_app.py、UserCanvasService、DSL JSON等。中间是Backend Execution，有DSL Parser、Canvas等。底部是ComponentBase，包含Begin、Generate、Retrieval、Answer、Other Operators等组件。该图直观呈现了系统各部分的结构及相互关系，与上下文介绍的Agent Flow System架构内容相契合。

## Chat Interface

> 注：原导出此节仅含一张图片（飞书死链已移除），无文字内容。
