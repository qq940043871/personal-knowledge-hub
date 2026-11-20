# GraphRAG知识图谱检索

> 模块：RAG检索增强
> 更新时间：2026-11-15
> 来源：all-in-rag 工程（第 7/9 章）、tiny-universe/TinyGraphRAG（714 行可运行实现）

---

## 一、为什么需要 GraphRAG

传统向量 RAG 的两个结构性短板：

1. **分块破坏语义连续性**：切分把文档拆成孤立块，跨块的实体关系（A 章定义的实体、B 章使用的关系）在向量空间里各自为战；
2. **全局性问题答不了**：「这批文档的主要主题是什么」「A 和 B 之间有什么关联」这类问题需要跨全部块聚合，Top-K 检索天然只给局部片段。

**问题类型与检索通道的映射**（选型判断的第一问）：

| 问题类型 | 例子 | 合适通道 |
|---|---|---|
| 局部事实 | 「X 的参数是什么」 | 向量检索 |
| 关键词命中 | 「报错 E1234 怎么处理」 | BM25 |
| 多跳关系 | 「A 公司两跳内收购了哪些行业的公司」 | **图遍历** |
| 全局聚合 | 「这些文档的主要结论/主题」 | **社区摘要** |

后两类就是 GraphRAG 的地盘——**GraphRAG 不替代混合检索，而是在 [07-高级检索与查询优化](07-高级检索与查询优化.md) 的查询路由后面多接两条通道**。

## 二、通用架构三阶段

### 2.1 知识图谱构建

- **知识抽取**：LLM 从文本抽实体、关系、属性，带指代消解与别名归一；
- **质量控制**：三元组置信度评估、抽检、冲突消解，必要时本体约束校验；
- **图谱融合**：实体对齐与去重（Entity Resolution），合并跨来源知识并保留溯源信息；
- **存储与索引**：图数据库落地（Neo4j/NebulaGraph 等）+ 属性/关系索引 + 实体向量索引。

### 2.2 图谱检索

不再是纯向量相似度，而是：实体定位（实体链接或向量检索锁定核心节点）→ 子图探索（Cypher 遍历、路径发现、约束过滤）→ 结构化证据抽取（路径序列化为可读证据）→ 高级检索（社区检测产分层摘要）。

```cypher
-- 多跳示例：公司 A 两跳内的收购路径及目标行业
MATCH (a:Company {name: "A"})-[:ACQUIRED]->(b:Company)-[:IN_INDUSTRY]->(i:Industry)
RETURN a.name, b.name, i.name
UNION
MATCH (a:Company {name: "A"})-[:ACQUIRED]->(:Company)-[:ACQUIRED]->(b2)-[:IN_INDUSTRY]->(i2)
RETURN a.name, b2.name, i2.name;
```

### 2.3 增强生成

图证据与原文片段联合注入 Prompt：明确要求模型引用「图证据」并给出来源路径；三元组/路径管事实骨架，原文片段管文本细节；敏感领域（财务/医疗）用模板化输出与字段校验兜底。

## 三、local 与 global 双查询（TinyGraphRAG 主链路）

```python
# TinyGraphRAG 主链路（伪代码骨架：重点在契约与流程；完整实现见
# tiny-universe/content/TinyGraphRAG/tinygraph/graph.py，714 行）
class TinyGraph:
    def add_document(self, filepath):
        # 入库链路：分块 → 抽实体 → 抽三元组 → 消歧 → 入图
        chunks = self.split_text(filepath, segment_length=300, overlap_length=50)
        for c in chunks:
            entities = self.get_entity(c.text, c.id)          # LLM 抽实体
            triplets = self.get_triplets(c.text, entities)    # LLM 抽 (subject, predicate, object)
            self.merge_and_store(triplets, source_chunk=c.id) # ★特殊点1 实体消歧决定图质量：
            #   同名实体必须合并（或 LLM 消歧），否则图谱长成一张大团单，
            #   子图探索和社区检测全部失真；三元组必须带 source_chunk_id 溯源

    def detect_communities(self):
        # Neo4j GDS Leiden 算法分区（maxLevels=10），产出社区数与模块度
        ...   # ★特殊点2 社区检测的产物是「分层摘要」——global 查询靠它，不靠向量

    def local_query(self, query):
        # 局部查询：细节/关系问题
        emb = self.embedder.embed(query)
        top_nodes = self.get_topk_similar_entities(emb, k=5)   # 实体向量检索定位
        context = self.build_local_query_context(top_nodes)
        # 上下文四段 CSV：社区报告 / 实体描述 / 关系列表 / 来源 chunk——
        # ★特殊点3 四段各司其职：报告给背景，实体给属性，关系给结构，chunk 给原文锚点
        return self.llm.answer(query, context)

    def global_query(self, query, level: int = 1):
        # 全局查询：全景/总结问题，map-reduce 式
        points = [self.map_community_points(c, query) for c in self.communities(level)]
        ranked = sorted(points, key=lambda p: p.score, reverse=True)  # 各社区报告打分
        # ★特殊点4 level 控制摘要层级：level 越高摘要越概括——
        #   先高层定范围、再下钻一层取细节，是最省 token 的全局问答路径
        return self.llm.answer(query, top_reports(ranked))
```

## 四、框架选型对比

| 框架 | 核心思路 | 构建成本 | 适用场景 |
|---|---|---|---|
| **Microsoft GraphRAG** | Leiden 社区检测 + 分层摘要，「先建全局知识再按需检索」 | 高（构建 + 分层摘要贵） | 探索性分析、全景总结、多跳问答 |
| **LightRAG** | 双层检索轻量化，弱化社区发现，结构信号嵌入文本索引与重排 | 低 | 资源受限、快速迭代、在线更新 |
| **FRAG** | 查询分流自适应 | 中 | 按查询类型动态分配检索路径 |
| **GraphIRAG** | 迭代检索 + 信息增益停止准则 | 中 | 需要控制检索深度/成本的场景 |

评估基准：HotpotQA、2WikiMultihopQA、MuSiQue、WebQSP（均为多跳/图谱问答数据集）。

## 五、企业落地形态

企业实践是**向量主路 + 图谱辅路**并存，而非二选一：混合检索（向量+BM25）承担绝大多数流量；查询路由（见 07 篇 1.4）把「关系密集 + 多实体」的 query 分流到 GraphRAG；两路结果 RRF 融合后统一走引用闸门。all-in-rag 第 9 章（约 2300 行 C9 代码）给出了该形态的完整参考实现：LLM 四维查询分析 + 规则降级 + 三策略路由 + 父文档回填（chunk 命中后回填整篇父文档，保证步骤类问题上下文完整）。

### 企业级升级要点

- **抽取质控是生命线**：错三元组进待办人工复核（对应 [70-企业级工程基准](../70-企业级工程基准.md) RAG #12 入库前人工闸的图谱版）——图一旦错了，检索越精准、答案错得越自信。
- **三元组必须溯源**：每条三元组带 source chunk id，答案引用能回链原文——「图证据」没有锚点，闸门二（引用检查）就没法验。
- **增量更新策略提前设计**：文档变更会级联社区重算（Leiden 全图重跑），Microsoft GraphRAG 场景要配批处理/增量更新与缓存策略，或选 LightRAG 类轻量方案。
- **构建成本预算化**：每个 chunk 至少 2 次 LLM 调用（抽实体 + 抽三元组），全库构建成本 = chunk 数 × 2 次调用——先在抽样文档上跑通评测，再全量构建。
- **评测先行**：拿多跳数据集或自有 bad case 建「该图谱答得出」的评测集，再决定要不要为它付构建成本。

[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：无（RAG与检索模块到此为止，转入 50-推理与部署优化）*
