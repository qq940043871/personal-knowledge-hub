# RAGFlow学习笔记

## High-Level Architecture

![图片为Agent Flow System架构图。前端层有web/ React Application、Flow Canvas (ReactFlow)、Chat Interface等；API Gateway连接多个组件；Core Processing包括ragflow_server.py等；LLM Integration有rag/llm/ LLM Integration等；Document Processing有deepdoc/ Document Processing等；External Services有OpenAI、BGE、BCE、Jina models等；Storage Layer有MySQL、Redis Task Queues、MinIO Object Storage、Elasticsearch/Infinity等。该图直观呈现了系统各组件及数据流向。](https://feishu.cn/file/GQWNbJ86ioAHqrxO2qvcZVg4nRf)

## Core Components and Code Mapping

![](https://feishu.cn/file/Akk1bo4ZMoNDvRx80wGczr4RnVe)

### LLM Integration Architecture

![图片展示了RAGFlow的LLM集成架构图。左侧为Configuration，包含api/db/models.py中的LLM和TenantLLM，以及docker/service conf.yaml.template。中间是LLM抽象层，有api/db/services/llm_service.py和rag/llm/link.py。右侧是LLM实现层，包括rag/llm/chat_model.py，其下有ChatModel、Model Types、Provider Implementations等分支，各分支对应不同模型文件。该图直观呈现了LLM集成架构的结构与各部分关系。](https://feishu.cn/file/K6KMbOh7qoXCDExN09Ycer1ynIc)

## Data Flow Architecture

![图片展示了Agent Flow System中Chat Interface的流程架构图。从Query Input开始，经api/apps/conversation_app.py完成，进入Query Processing，再通过rag/finetuned_model.py嵌入，连接Knowledge Retrieval，分别与Elasticsearch和Elasticsearch Infinity进行vector_search和full_text_search，获取results后，经rag/apps/retrieval.py构建context，再由rag/finetuned_model.py chat，最后通过rag/apps/retrieval.py提取relations，完成Response Delivery，经api/libs/services/conversation_service.py发送。](https://feishu.cn/file/IcGybpndhoSXpPxkatpcUlcmnId)

## Deployment and Infrastructure

![图片展示了Agent Flow System的架构图。左侧有Compose Profiles环境、Search Backends等组件，中间是Configuration Manager、Storage Services等，右侧是Container Orchestration下的docker-compose.yml等文件。下方是Application Services，包括ragflow-server、ragflow-task-executor等。该图与文档中“Agent Flow System”章节对应，直观呈现了系统各组件及文件的关联关系。](https://feishu.cn/file/MFi1bW7YLohP8DxIJujcYmHOnEg)

### Document Processing Pipeline Architecture

![图片展示了文档处理管道架构图。从Task Queue System接收任务，经Redis Task Queue传递至TaskExecutor，其下有Document Processing和Storage Operations分支。Document Processing包含DocumentService、build_chunks()、embedding()等操作，Storage Operations涉及settings.docStoreConn、STORAGE_IMPL、RedisDistributedLock等。该图与文档中“Document Processing Pipeline Architecture”章节对应，直观呈现了文档处理流程及各组件关系。](https://feishu.cn/file/NUFQba2Rdolus3xqWTOcOnr7n7e)

### Authentication Flow

![](https://feishu.cn/file/ARFDbyJH7oT5lcxdqIPc0pG2nTg)

## Integration Architecture

![图片展示了RAGFlow系统架构图。左侧为外部客户端，包括Web应用React前端、SDK、MCP客户端等；中间是API网关层，有document、conversation、chunk等应用；右侧是服务集成，有storage、LLMBundle、redis_conn等。各部分通过箭头连接，表示数据或服务的流向。该图与文档中“Integration Architecture”部分对应，直观呈现了系统各组件间的交互关系。](https://feishu.cn/file/MDHQbcdR9oZXJjxNhWYclH3Xn2d)

## Embedding Generation and Vector Storage

![](https://feishu.cn/file/TROWbb4e0oLpmSxwivPcOPixnLd)

### Architecture Diagram

![图片展示了文档处理流水线架构图。从文档处理开始，经文档切分、实体和关系抽取，进入图构建环节，通过generate_subgraph()和merge_subgraph()生成局部子图，合并为全局知识图谱。随后进行图增强，包括实体解析、社区检测，生成社区报告。最后是存储集成，与文档存储结合，实现图增强检索。该图与文档中“Document Processing Pipeline Architecture”部分对应，直观呈现了文档处理的流程。](https://feishu.cn/file/UrM9bWO1YoutIMxH7bOcdw2rnAe)

## Agent Flow System

![图片展示了Agent Flow System的架构图。左侧为Frontend Flow Editor，包含FlowCanvas、useGraphStore、nodeTypes、FormDrawer等组件。右侧是Storage & API，有canvas_app.py、UserCanvasService、DSL JSON等。中间是Backend Execution，有DSL Parser、Canvas等。底部是ComponentBase，包含Begin、Generate、Retrieval、Answer、Other Operators等组件。该图直观呈现了系统各部分的结构及相互关系，与上下文介绍的Agent Flow System架构内容相契合。](https://feishu.cn/file/SfpSblVljolXyMxHX8WcBruKnXH)

## Chat Interface

![](https://feishu.cn/file/LpvsbbMMgosoJ9xM7UVcMD0enXi)
