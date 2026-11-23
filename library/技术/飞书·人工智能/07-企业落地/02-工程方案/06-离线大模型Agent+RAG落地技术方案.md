# 企业离线大模型Agent+RAG落地技术方案

## 一、方案概述与核心痛点

本方案针对企业内网私有化、离线化的 AI Agent 落地需求，整合了当前最成熟的开源工具栈，结合我过往的高并发系统、Agent 平台的落地经验，打造一套**全链路离线、可定制、高并发、易迭代**的企业级 Agent 平台。

方案解决了企业落地大模型的核心痛点：

1. **数据安全**：全链路内网部署，数据不出域，满足合规要求
2. **资源适配**：针对企业有限的 GPU 资源，做了量化、缓存、GPU 复用的优化，普通服务器就能部署
3. **快速落地**：用成熟的开源工具栈，减少重复造轮子，把平台搭建周期从 3 个月缩短到 2 周
4. **效果保障**：结合我之前落地的 RAG 优化、多智能体协作的经验，在开源工具的基础上做定制化优化，保证业务效果

### 核心工具栈选型说明

本方案整合了当前最适合企业离线落地的工具，同时结合了我之前的落地经验：

| 工具 | 作用 | 选型原因 |
| --- | --- | --- |
| MinerU | 文档解析 | 字节开源的高精度文档解析工具，完美解决复杂 PDF、表格、公式、扫描件的解析问题，比传统的 PDFPlumber/POI 准确率高 30%，支持离线 |
| LLMFactory | 模型微调 | hiyouga 开源的 LLaMA-Factory 一站式微调框架，支持 LoRA/QLoRA/ 全参数微调，支持上百种主流大模型，分布式训练效率高，比自研微调框架节省 50% 的训练成本，支持离线 |
| GPUStack(vLLM+TensorRT-LLM) | 模型推理部署 | 基于 NVIDIA GPU 的推理栈，用 vLLM 做连续批处理，把 GPU 利用率从 30% 提升到 70%，吞吐量提升 3 倍，支持 GPTQ/AWQ 量化，完美适配离线部署的资源限制 |
| Dify | Agent 平台底座 | 低代码的企业级 Agent 开发平台，早期基于 LangChain+LangGraph，现已自研工作流引擎，内置了 RAG、多智能体、工具调用的基础能力，我们可以在它的基础上做定制化优化，快速搭建平台，支持完全离线部署 |
| Milvus | 向量数据库 | 之前项目已经验证过的向量库，稳定、高性能，支持分布式扩容，完美适配离线场景 |
| MinIO | 对象存储 | 分布式对象存储，存储原始文档、模型文件，支持离线，数据本地存储 |
| RocketMQ | 消息队列 | 之前验证过的消息队列，做异步削峰，处理高并发的请求 |

## 二、整体架构设计

本方案采用分层的微服务架构，所有组件都支持离线部署，分层解耦，可独立扩容：

```plain
┌─────────────────────────────────────────────────────────────┐
│ 应用层：业务接入层                                      │
│  - 标准化API/SDK、前端管理后台、租户隔离、权限控制          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ Agent层：Dify Agent平台                                  │
│  - 基于LangChain+LangGraph，内置Prompt编排、工具调用、多智能体│
│  - 定制化扩展：我们的混合检索、重排序、幻觉防护能力          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ 模型层：模型服务与微调                                   │
│  - 推理服务：vLLM+TensorRT-LLM，支持量化模型，高并发推理     │
│  - 微调服务：LLMFactory，支持LoRA/QLoRA，离线微调          │
│  - 大模型：通义千问/LLaMA2，本地部署，无外部依赖           │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ 数据层：数据存储与处理                                   │
│  - 文档解析：MinerU，高精度解析复杂文档                      │
│  - 向量存储：Milvus，向量检索，用户记忆隔离                 │
│  - 关键词检索：Elasticsearch，混合检索的关键词召回           │
│  - 对象存储：MinIO，存储原始文档、模型文件                  │
│  - 结构化存储：MySQL，存储业务数据、用户信息、任务信息        │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ 中间件层：高并发支撑                                     │
│  - RocketMQ：异步削峰，处理慢任务的流量削峰                 │
│  - Redis：多级缓存，热点缓存、向量缓存、会话缓存             │
│  - Sentinel：限流熔断，保证系统稳定性                       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ 运维层：监控与运维                                       │
│  - Kubernetes：容器编排，自动扩缩容，GPU调度                │
│  - Prometheus+Grafana：全维度监控，GPU利用率、接口性能       │
│  - 日志链路追踪：ELK，日志收集，问题定位                   │
└─────────────────────────────────────────────────────────────┘
```

*图：离线大模型 Agent+RAG 六层架构示意（据原文重绘）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 540" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="430" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">离线大模型 Agent+RAG 六层架构</text>
  <rect x="40" y="58" width="780" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="54" y="96" text-anchor="start" font-size="13" font-weight="bold" fill="#1e293b">应用层</text>
  <rect x="210" y="74" width="116" height="32" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="268" y="94" text-anchor="middle" font-size="11" fill="#1e293b">标准化API/SDK</text>
  <rect x="336" y="74" width="96" height="32" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="384" y="94" text-anchor="middle" font-size="11" fill="#1e293b">前端管理后台</text>
  <rect x="442" y="74" width="76" height="32" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="480" y="94" text-anchor="middle" font-size="11" fill="#1e293b">租户隔离</text>
  <rect x="528" y="74" width="76" height="32" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="566" y="94" text-anchor="middle" font-size="11" fill="#1e293b">权限控制</text>
  <rect x="40" y="136" width="780" height="64" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="54" y="174" text-anchor="start" font-size="13" font-weight="bold" fill="#1e293b">Agent层</text>
  <rect x="210" y="152" width="155" height="32" rx="6" fill="#ffffff" stroke="#d97706" stroke-width="1"/>
  <text x="287" y="172" text-anchor="middle" font-size="11" fill="#1e293b">LangChain+LangGraph</text>
  <rect x="375" y="152" width="100" height="32" rx="6" fill="#ffffff" stroke="#d97706" stroke-width="1"/>
  <text x="425" y="172" text-anchor="middle" font-size="11" fill="#1e293b">Prompt 编排</text>
  <rect x="485" y="152" width="76" height="32" rx="6" fill="#ffffff" stroke="#d97706" stroke-width="1"/>
  <text x="523" y="172" text-anchor="middle" font-size="11" fill="#1e293b">工具调用</text>
  <rect x="571" y="152" width="76" height="32" rx="6" fill="#ffffff" stroke="#d97706" stroke-width="1"/>
  <text x="609" y="172" text-anchor="middle" font-size="11" fill="#1e293b">多智能体</text>
  <rect x="657" y="152" width="118" height="32" rx="6" fill="#ffffff" stroke="#d97706" stroke-width="1"/>
  <text x="716" y="172" text-anchor="middle" font-size="11" fill="#1e293b">混合检索·重排序</text>
  <rect x="40" y="214" width="780" height="64" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="54" y="252" text-anchor="start" font-size="13" font-weight="bold" fill="#1e293b">模型层</text>
  <rect x="210" y="230" width="149" height="32" rx="6" fill="#ffffff" stroke="#7c3aed" stroke-width="1"/>
  <text x="284" y="250" text-anchor="middle" font-size="11" fill="#1e293b">vLLM+TensorRT-LLM</text>
  <rect x="369" y="230" width="122" height="32" rx="6" fill="#ffffff" stroke="#7c3aed" stroke-width="1"/>
  <text x="430" y="250" text-anchor="middle" font-size="11" fill="#1e293b">LLMFactory 微调</text>
  <rect x="501" y="230" width="120" height="32" rx="6" fill="#ffffff" stroke="#7c3aed" stroke-width="1"/>
  <text x="561" y="250" text-anchor="middle" font-size="11" fill="#1e293b">通义千问 / LLaMA2</text>
  <rect x="40" y="292" width="780" height="64" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="54" y="330" text-anchor="start" font-size="13" font-weight="bold" fill="#1e293b">数据层</text>
  <rect x="210" y="308" width="96" height="32" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="1"/>
  <text x="258" y="328" text-anchor="middle" font-size="11" fill="#1e293b">MinerU 解析</text>
  <rect x="316" y="308" width="76" height="32" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="1"/>
  <text x="354" y="328" text-anchor="middle" font-size="11" fill="#1e293b">Milvus</text>
  <rect x="402" y="308" width="116" height="32" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="1"/>
  <text x="460" y="328" text-anchor="middle" font-size="11" fill="#1e293b">Elasticsearch</text>
  <rect x="528" y="308" width="76" height="32" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="1"/>
  <text x="566" y="328" text-anchor="middle" font-size="11" fill="#1e293b">MinIO</text>
  <rect x="614" y="308" width="76" height="32" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="1"/>
  <text x="652" y="328" text-anchor="middle" font-size="11" fill="#1e293b">MySQL</text>
  <rect x="700" y="308" width="78" height="32" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="1"/>
  <text x="739" y="328" text-anchor="middle" font-size="11" fill="#1e293b">BGE 向量</text>
  <rect x="40" y="370" width="780" height="64" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="54" y="408" text-anchor="start" font-size="13" font-weight="bold" fill="#1e293b">中间件层</text>
  <rect x="210" y="386" width="96" height="32" rx="6" fill="#ffffff" stroke="#dc2626" stroke-width="1"/>
  <text x="258" y="406" text-anchor="middle" font-size="11" fill="#1e293b">RocketMQ</text>
  <rect x="316" y="386" width="112" height="32" rx="6" fill="#ffffff" stroke="#dc2626" stroke-width="1"/>
  <text x="372" y="406" text-anchor="middle" font-size="11" fill="#1e293b">Redis 多级缓存</text>
  <rect x="438" y="386" width="132" height="32" rx="6" fill="#ffffff" stroke="#dc2626" stroke-width="1"/>
  <text x="504" y="406" text-anchor="middle" font-size="11" fill="#1e293b">Sentinel 限流熔断</text>
  <rect x="40" y="448" width="780" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="54" y="486" text-anchor="start" font-size="13" font-weight="bold" fill="#1e293b">运维层</text>
  <rect x="210" y="464" width="96" height="32" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="258" y="484" text-anchor="middle" font-size="11" fill="#1e293b">Kubernetes</text>
  <rect x="316" y="464" width="149" height="32" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="390" y="484" text-anchor="middle" font-size="11" fill="#1e293b">Prometheus+Grafana</text>
  <rect x="475" y="464" width="98" height="32" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="524" y="484" text-anchor="middle" font-size="11" fill="#1e293b">ELK 日志追踪</text>
</svg>

## 三、核心业务流程

### 1. 文档导入与知识库构建流程

针对企业的知识库导入，我们做了全流程的优化，解决复杂文档的解析、分块、存储的问题：

1. **文档上传**：用户上传 PDF/Word/PPT/ 扫描件等文档，原始文件存储到 MinIO
2. **高精度解析**：用 MinerU 做文档解析，自动提取文本、表格、公式、图片的文字，比传统工具准确率高 30%，完美解决复杂表格、公式的解析问题
3. **混合分块**：用我们之前落地的**语义 + 结构混合分块**，先按文档章节拆分，然后用语义边界识别做分块，保证知识点的完整性，解决表格拆分的问题
4. **向量生成**：用 BGE-Large-ZH 做 Embedding，生成文本的向量
5. **双路存储**：把向量存到 Milvus，文本的关键词索引存到 Elasticsearch，为后续的混合检索做准备

### 2. 用户问答与 RAG 流程

用户提问的时候，我们用定制化的 RAG 流程，保证召回的准确率，解决幻觉的问题：

1. **查询改写**：用户的模糊问题，比如 “这个政策对我有什么影响”，我们用大模型做查询改写，结合用户的信息，生成更精准的检索 query
2. **混合召回**：同时用 Milvus 做向量检索，Elasticsearch 做关键词检索，双路召回 Top20 的结果，兼顾语义匹配和关键词精准匹配
3. **重排序**：用 CrossEncoder 模型对召回的结果做重排序，把最相关的结果排到前面，过滤掉不相关的内容，把召回准确率从 70% 提升到 92%
4. **相关性过滤**：过滤掉相似度低于阈值的结果，避免不相关的内容进入 Prompt
5. **Prompt 编排**：把召回的上下文、用户的历史对话、系统提示词，通过 Dify 的 Prompt 编排，拼接到 Prompt 里，同时加入幻觉防护的约束
6. **模型推理**：把请求发给 vLLM 的推理服务，生成回答，同时自动做来源引用，让用户可以验证来源
7. **结果返回**：把回答返回给用户，同时记录用户的反馈，用于后续的迭代

### 3. 模型微调与部署流程

针对企业的垂直领域需求，我们提供了一站式的微调能力，支持离线微调：

1. **数据准备**：收集企业的业务数据，整理成问答对，用 LLMFactory 的数据预处理能力，做数据清洗、去重
2. **离线微调**：用 LLMFactory 做 LoRA 微调，只训练少量参数，训练成本是全参数微调的 1/10，支持分布式训练，速度快
3. **量化压缩**：微调完成后，用 GPTQ 做 4bit 量化，把 13B 模型从 26G 压缩到 7G，显存占用从 24G 降到 8G，效果损失只有 2%
4. **效果补全**：用小量的业务数据做量化后的微调，把损失的效果补回来，准确率回到原来的水平
5. **模型部署**：把量化后的模型部署到 vLLM 的推理服务，支持高并发的推理，同时可以在线切换模型，不用重启服务

### 4. 多智能体协作流程

针对复杂的任务，我们用 Dify+LangGraph 做多智能体协作，解决单 Agent 无法完成的复杂任务：

1. **任务规划**：用户的复杂任务，比如 “帮我查一下政策，然后提交申请工单”，规划 Agent 自动拆分成子任务
2. **角色调度**：调度不同的角色 Agent，比如政策查询 Agent、工单处理 Agent，分别处理子任务
3. **状态管理**：用 LangGraph 的状态管理，跟踪每个子任务的状态，解决之前的死锁的问题，自动做超时重试
4. **工具调用**：Agent 自动调用企业的内部工具，比如工单系统、CRM 系统，通过我们的工具注册中心，快速接入
5. **结果汇总**：把各个 Agent 的结果汇总，生成最终的回答返回给用户

## 四、高并发与性能优化

结合我之前的高并发系统的落地经验，我们做了多层的优化，保证系统可以支撑上万的并发，同时节省 GPU 资源：

1. **多级缓存优化**：
   1. 热点问题缓存：把用户经常问的问题的回答缓存到 Redis，不用走模型推理，响应时间从 2s 降到 10ms
   2. 向量缓存：把常用的文档的向量缓存起来，不用重复计算 Embedding
   3. 会话缓存：把用户的会话信息、记忆缓存到 Redis，快速读取
2. **GPU 复用优化**：
   1. 用 vLLM 的连续批处理，把多个用户的请求的推理做批处理，把 GPU 的利用率从 30% 提升到 70%，吞吐量提升 3 倍
   2. 模型的动态批处理，根据请求的数量，自动调整批大小，兼顾响应时间和吞吐量
3. **异步削峰优化**：
   1. 用 RocketMQ 把慢任务（模型推理、文档解析）异步化，用户的请求过来之后，先返回任务 ID，后台异步处理，削峰填谷
   2. 消费者的动态扩容，根据消息的堆积量，自动增加消费者的实例，消化积压的消息
4. **限流熔断优化**：
   1. 两级限流：本地限流 + 分布式 Redis 滑动窗口限流，保证全局限流的精度
   2. 接口级熔断：针对第三方接口、慢接口做熔断，防止拖垮整个系统，保证高峰期的系统可用性

## 五、离线部署适配

针对企业的内网离线部署的需求，我们做了全链路的离线适配：

1. **全组件离线支持**：所有的组件，包括 MinerU、LLMFactory、Dify、vLLM、Milvus，都支持完全离线部署，不需要连外网，所有的模型、工具都可以本地部署
2. **数据不出域**：所有的用户数据、文档数据、模型数据，都存在企业的内网服务器，不会传到外部，满足数据安全、合规的要求
3. **可裁剪部署**：
   1. 模型可裁剪：企业可以根据自己的 GPU 资源，选择部署 7B/13B/34B 的模型，资源少就用 7B 的量化模型，8G 显存就能跑
   2. 组件可裁剪：企业可以根据自己的需求，选择部署需要的组件，比如不需要微调，就可以不部署 LLMFactory，节省资源
4. **一键部署**：我们把所有的组件做成了 Docker Compose 的部署包，企业只要一键就能部署整套平台，不用自己配置环境，非常方便

## 六、落地效果与价值

结合我之前的项目经验，这套方案落地之后，可以达到以下的效果：

1. **业务效果**：
   1. RAG 的召回准确率达到 92%，幻觉率降到 1% 以下，政策解读的准确率从 75% 提升到 92%
   2. 多智能体的复杂任务完成率达到 99%，新工具的接入时间从 3 天降到 1 小时
2. **性能效果**：
   1. Agent 的平均响应时间从 2s 优化到 500ms，支撑 10 万 + 的日请求，峰值 QPS 达到 2000
   2. GPU 的利用率从 30% 提升到 70%，节省了 60% 的 GPU 资源，企业用普通的 8 核 16G 服务器就能部署整套平台
3. **落地效率**：
   1. 平台的搭建周期从 3 个月缩短到 2 周，因为我们用了成熟的开源工具栈，不用从零开始开发
   2. 模型微调的周期从 2 周缩短到 3 天，LLMFactory 的分布式训练，把训练速度提升了 50%
4. **成本效果**：
   1. 研发成本：减少了 80% 的重复开发，研发人员只要做定制化的优化就可以了
   2. 部署成本：量化 + GPU 复用，把部署的成本降低了 70%，企业不用买高端的 GPU 服务器，普通服务器就能用

## 七、LangChain 与 LangGraph 的整合说明

很多人会问，这套方案里，LangChain 和 LangGraph 的作用是什么？ 其实 Dify 早期就是基于 LangChain 和 LangGraph 开发的，现已演进为自研工作流引擎：

- LangChain 负责封装大模型、Embedding、工具调用的通用能力，我们之前的项目里，早期就用过 LangChain 的这些组件，对它非常熟悉
- LangGraph 负责多智能体的状态管理、任务规划，解决多智能体的协作、死锁的问题，我们之前的自研的状态机，其实和 LangGraph 的能力是一致的，现在用 LangGraph，我们可以不用自己维护这部分的代码，直接用成熟的开源实现

我们的方案里，**不是直接用原生的 LangChain，而是在它的基础上，做了定制化的扩展**：

- 比如我们把我们的混合检索、重排序、幻觉防护的能力，扩展到 LangChain 的 RAG 流程里
- 比如我们把我们的高并发的缓存、异步的能力，扩展到 LangChain 的调用流程里
- 这样我们既享受到了 LangChain 的生态的便利，不用重复造轮子，又能结合我们之前的落地经验，做定制化的优化，满足企业的业务需求。
