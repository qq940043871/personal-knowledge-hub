# RAG原理

> 模块：RAG检索增强
> 更新时间：2026-11-15

---

## RAG架构：检索 → 增强 → 生成

核心思路：**大模型不直接凭参数记忆回答，而是先从知识库检索相关内容、把检索结果加入 Prompt，再让 LLM 基于增强后的上下文生成**。优势：知识可更新、减少幻觉、可追溯可解释。

```text
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

## 最小可运行组件：Embedder / VectorStore / LLM

核心思路：**三个组件各给一份伪代码骨架——Embedder 走 OpenAI 兼容端点（key 从环境变量读取），VectorStore 用 numpy 余弦相似度（万条以内够用），LLM 用 openai 客户端**；组件实现可替换，流水线逻辑不变。完整实现见 ownrag/harness 工程。

```python
# 三个组件的最小形态（伪代码：重点在接口契约与特殊点；完整实现见 ownrag/harness 工程）
import os
from dataclasses import dataclass

import numpy as np
from openai import AsyncOpenAI

if not os.environ.get("OPENAI_API_KEY"):        # ★特殊点1 配置即代码：key 只走环境变量，
    raise RuntimeError("缺少 OPENAI_API_KEY，请先 export 再运行")   #   启动期校验，缺 key 当场报错

client = AsyncOpenAI(timeout=60, max_retries=2)  # ★特殊点2 显式超时与重试：网络抖动不直接失败
#   （默认读 OPENAI_API_KEY / OPENAI_BASE_URL）

@dataclass
class Doc:
    content: str
    source: str   # 来源路径/标题——没有来源，答案就无法溯源

class Embedder:
    """OpenAI 兼容端点（ada-002 已废弃，现行 text-embedding-3-small；中文本地方案见 03-Embedding生成）"""
    async def embed(self, texts):
        ...   # str 归一为 [str]；按 resp.data 的 index 排序对齐输入再返回

class VectorStore:
    """numpy 余弦相似度（万条以内够用；生产换 Chroma/FAISS，接口不变）"""
    def add(self, doc: Doc, vector: np.ndarray): ...
    async def search(self, query_embedding, top_k: int = 5):
        ...   # 全量余弦相似度 → 取 top_k，返回 [(doc, 相似度), ...]

class LLM:
    """OpenAI 兼容 chat（模型名走 RAG_CHAT_MODEL 环境变量）"""
    async def generate(self, prompt: str) -> str:
        ...   # resp.choices[0].message.content
```

---

## RAG 流水线实现：从问题到回答的五步

核心思路：**流水线依次完成嵌入问题、向量检索、拼接上下文、组装 Prompt、调用 LLM 生成；Prompt 中明确要求「上下文中没有相关信息就说明」，抑制幻觉；空检索显式拒答不进模型，答案附来源溯源**。

```python
# RAG 流水线（伪代码：五步主流程，重点在两个特殊点；完整实现见 ownrag/harness 工程）
class RAGPipeline:
    """空检索显式拒答；答案附来源（返回 dict，含 answer 与 sources）"""

    def __init__(self, embedder: Embedder, vector_store: VectorStore, llm: LLM):
        ...

    async def query(self, question: str, top_k: int = 5) -> dict:
        query_embedding = (await self.embedder.embed(question))[0]        # 1. 嵌入问题
        results = await self.vector_store.search(query_embedding, top_k)  # 2. 检索

        if not results:
            # ★特殊点3 空检索显式拒答：连上下文都没有，进模型只会诱导编造
            return {"answer": "未找到有效依据，无法回答。", "sources": []}
            #   ——不花这次 token 的合法拒答

        context = "\n\n".join(                       # 3. 构建上下文：带编号与来源
            f"[{i}]（来源：{doc.source}）\n{doc.content}"
            for i, (doc, _) in enumerate(results, start=1))

        prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请说明。
上下文：
{context}
问题：{question}
回答："""                        # 4. 构建提示词：明确要求「没有就说明」，抑制幻觉

        response = await self.llm.generate(prompt)   # 5. 生成回答
        return {"answer": response, "sources": [doc.source for doc, _ in results]}
        # ★特殊点4 来源溯源：答案附上命中的来源清单——可追溯可解释
```

### 企业级升级要点

- **空检索显式拒答**：检索不到就直说「未找到有效依据」，不把空上下文喂给模型——零模型消耗的合法拒答，是证据充分性闸门的最简形态，见 `ai-rag-self-engineering/ownrag/ownrag/generate/gates.py` 的 `sufficiency_check`。
- **答案必附来源溯源**：上下文块带编号与来源入 Prompt，返回值带 `sources`——可追溯可解释是 RAG 相对裸 LLM 的核心优势，见 `ai-rag-self-engineering/ownrag/ownrag/generate/budget.py` 的 `block_prompt`（块头格式与拼装口径一致）。
- **配置即代码**：API key / 模型名一律 `os.environ` 读取，缺失时报可行动错误——见 `ai-rag-self-engineering/ownrag/ownrag/config.py`。
- **显式超时与重试**：`AsyncOpenAI(timeout=60, max_retries=2)`，网络抖动不直接失败，失败也不静默——见 `ai-rag-self-engineering/ownrag/ownrag/generate/openai_client.py`。

[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：文档切分*
