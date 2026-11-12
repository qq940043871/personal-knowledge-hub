# RAG原理

> 模块：RAG检索增强
> 更新时间：2026-03-29

---

## RAG架构：检索 → 增强 → 生成

核心思路：**大模型不直接凭参数记忆回答，而是先从知识库检索相关内容、把检索结果加入 Prompt，再让 LLM 基于增强后的上下文生成**。优势：知识可更新、减少幻觉、可追溯可解释。

```
RAG（Retrieval-Augmented Generation）：
  1. 检索：从知识库检索相关内容
  2. 增强：将检索结果加入Prompt
  3. 生成：LLM基于增强的上下文生成

优势：
  - 知识可更新
  - 减少幻觉
  - 可追溯可解释
```

*图：RAG 检索增强问答流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 180" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="15" y="50" width="120" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="75" y="81" text-anchor="middle" font-size="13" fill="#1e293b">1. 嵌入问题</text>
  <line x1="138" y1="76" x2="155" y2="76" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="157" y="50" width="120" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="217" y="71" text-anchor="middle" font-size="13" fill="#1e293b">2. 检索相关文档</text>
  <text x="217" y="90" text-anchor="middle" font-size="12" fill="#475569">（向量库 Top-K）</text>
  <line x1="280" y1="76" x2="297" y2="76" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="299" y="50" width="120" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="359" y="81" text-anchor="middle" font-size="13" fill="#1e293b">3. 构建上下文</text>
  <line x1="422" y1="76" x2="439" y2="76" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="441" y="50" width="120" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="501" y="81" text-anchor="middle" font-size="13" fill="#1e293b">4. 构建提示词</text>
  <line x1="564" y1="76" x2="581" y2="76" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="583" y="50" width="120" height="52" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="643" y="81" text-anchor="middle" font-size="13" fill="#1e293b">5. 生成回答</text>
  <text x="360" y="150" text-anchor="middle" font-size="13" fill="#475569">将检索结果加入 Prompt，LLM 基于增强后的上下文生成回答</text>
</svg>

---

## RAG 流水线实现：从问题到回答的五步

核心思路：**流水线依次完成嵌入问题、向量检索、拼接上下文、组装 Prompt、调用 LLM 生成；Prompt 中明确要求「上下文中没有相关信息就说明」，抑制幻觉**。

```python
class RAGPipeline:
    """RAG流水线"""

    def __init__(self, embedder: Embedder, 
                 vector_store: VectorStore,
                 llm: LLM):
        self.embedder = embedder
        self.vector_store = vector_store
        self.llm = llm

    async def query(self, question: str, top_k: int = 5) -> str:
        # 1. 嵌入问题
        query_embedding = await self.embedder.embed(question)

        # 2. 检索相关文档
        docs = await self.vector_store.search(query_embedding, top_k)

        # 3. 构建上下文
        context = "\n\n".join([doc.content for doc in docs])

        # 4. 构建提示词
        prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请说明。

上下文：
{context}

问题：{question}

回答："""

        # 5. 生成回答
        response = await self.llm.generate(prompt)
        return response
```

---

*下一步：文档切分*
