# Embedding生成

> 模块：RAG检索增强
> 更新时间：2026-11-15

---

## 一、Embedding模型

核心思路：**`embed()` 统一返回 `List[List[float]]`（与输入条数一一对应，类型口径保留）；`_call_model` 伪代码骨架——429/5xx 指数退避重试，4xx 其他错误不重试直接报可行动错误**。批量上限 + 退避是限流的两条主防线，限流是摄取环节最高频故障。

```python
# Embedder（伪代码：重点在限流的两道防线；完整实现见 ownrag/harness 工程）
import asyncio
from typing import List, Union

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI

class Embedder:
    """文本嵌入模型（OpenAI 兼容端点）。ada-002 已废弃；现行默认 text-embedding-3-small
    （默认 1536 维，可用 dimensions 压到 512/1024 降维省存储——注意换维度 = 换值 = 索引全量重建）"""

    def __init__(self, model: str = "text-embedding-3-small",
                 dimensions: int | None = None):
        # ★特殊点1 配置即代码：key 一律 os.environ 读取（OPENAI_API_KEY），
        self.client = AsyncOpenAI(timeout=60, max_retries=0)   # 缺失报可行动错误，禁止硬编码；
        self.model, self.dimensions = model, dimensions        # 重试在 _call_model 里显式做

    async def embed(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """生成嵌入向量：统一返回 List[List[float]]（一条输入对应一条向量）"""
        if isinstance(texts, str):
            texts = [texts]
        return await self._call_model(texts)

    async def embed_batch(self, texts: List[str],
                          batch_size: int = 128) -> List[List[float]]:
        # ★特殊点2 批量上限：一次塞太多文本，轻则超请求体限制，重则触发 429 限流
        for i in range(0, len(texts), batch_size):
            ...   # 分批调用 embed，结果按序 extend 返回

    async def _call_model(self, texts: List[str], retries: int = 4) -> List[List[float]]:
        """调用嵌入 API：429/5xx 指数退避重试；连接失败同样退避重试"""
        for attempt in range(1, retries + 1):
            try:
                ...   # client.embeddings.create(model, input, dimensions)；
                ...   # 按 resp.data 的 index 排序对齐输入，返回 [item.embedding ...]
            except (APIConnectionError, APITimeoutError):
                await asyncio.sleep(2 ** attempt)      # ★特殊点3 连接级失败：指数退避后重试
            except APIStatusError as exc:
                if exc.status_code == 429 or exc.status_code >= 500:
                    await asyncio.sleep(2 ** attempt)  # ★特殊点4 限流/服务端错误：指数退避
                else:
                    # 401/404 等是鉴权/配置问题，重试没有意义，直接给可行动报错
                    raise RuntimeError(
                        f"嵌入请求失败 HTTP {exc.status_code}："
                        f"检查模型名 {self.model!r} 与 OPENAI_API_KEY"
                    ) from exc
        raise RuntimeError(f"重试 {retries} 次仍失败（限流或服务端故障），请降低 batch_size 后再试")
```

---

## 二、中文模型：BGE-M3（SentenceTransformers）

核心思路：**中文场景本地跑 BAAI/bge-m3——多语言、多粒度（支持稠密/稀疏/多向量三种检索形态），不花 API 费用、数据不出域；本地模型无需 API key**。

```python
import numpy as np
from sentence_transformers import SentenceTransformers

# 本地加载 BGE-M3（首次运行会自动下载权重；无 GPU 也能跑，速度换设备）
model = SentenceTransformers("BAAI/bge-m3")

doc_embeddings = model.encode(
    ["公司年假政策：每年 5 天带薪年假，工龄满 10 年增至 10 天。", "报销单需部门主管与财务双签。"],
    normalize_embeddings=True,  # 归一化后点积即余弦相似度
)
query_embedding = model.encode(["年假有几天？"], normalize_embeddings=True)

sims = doc_embeddings @ query_embedding.T
print(sims.ravel())
```

**换模型 = 换向量空间**：不同模型的向量不可混用（维度都可能不同）——切换供应商/模型/维度后，存量索引必须全量重建。

### 企业级升级要点

- **显式版本绑定**：embed_version 与向量兼容性绑定——换供应商/模型 = 换值 = 全量重建索引，禁止跨版本向量混用，见 `ai-rag-self-engineering/ownrag/ownrag/index/embedder.py` 模块注释。
- **限流是摄取最高频故障**：批量上限 + 429/5xx 指数退避是两条主防线；4xx 其他错误不重试（配置/鉴权问题，重试无用），错误分型口径见 `ai-rag-self-engineering/ownrag/ownrag/index/embedder.py` 的 `_embed_texts_openai`。
- **连接级失败熔断**：连接失败反复重试会让一次问答付两份延迟代价（SYN 被丢时本机一次就要 2 秒以上）——熔断窗口内快速失败，见同文件 `breaker_open`。
- **供应商可换不动代码**：ollama 原生 / OpenAI 兼容 /embeddings 双分派，换后端只改 base_url/model/key，见 `ai-rag-self-engineering/ownrag/ownrag/index/embedder.py` 的 `embed_texts`。
- **配置即代码**：API key 一律 `os.environ` 读取、缺失报可行动错误，见 `ai-rag-self-engineering/ownrag/ownrag/config.py`。

[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：检索排序*
