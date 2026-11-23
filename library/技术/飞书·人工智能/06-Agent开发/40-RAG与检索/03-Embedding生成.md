# Embedding生成

> 模块：RAG检索增强  
> 更新时间：2026-11-15

---

---

核心思路：**`embed()`****统一返回****`List[List[float]]`****（与输入条数一一对应，类型口径保留）；****`_call_model`****伪代码骨架——429/5xx 指数退避重试，4xx 其他错误不重试直接报可行动错误**。批量上限 + 退避是限流的两条主防线，限流是摄取环节最高频故障。

```
<code># Embedder（伪代码：重点在限流的两道防线；完整实现见 ownrag/harness 工程）<br/>import asyncio<br/>from typing import List, Union<br/><br/>from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI<br/><br/>class Embedder:<br/>    """文本嵌入模型（OpenAI 兼容端点）。ada-002 已废弃；现行默认 text-embedding-3-small<br/>    （默认 1536 维，可用 dimensions 压到 512/1024 降维省存储——注意换维度 = 换值 = 索引全量重建）"""<br/><br/>    def __init__(self, model: str = "text-embedding-3-small",<br/>                 dimensions: int | None = None):<br/>        # ★特殊点1 配置即代码：key 一律 os.environ 读取（OPENAI_API_KEY），<br/>        self.client = AsyncOpenAI(timeout=60, max_retries=0)   # 缺失报可行动错误，禁止硬编码；<br/>        self.model, self.dimensions = model, dimensions        # 重试在 _call_model 里显式做<br/><br/>    async def embed(self, texts: Union[str, List[str]]) -&gt; List[List[float]]:<br/>        """生成嵌入向量：统一返回 List[List[float]]（一条输入对应一条向量）"""<br/>        if isinstance(texts, str):<br/>            texts = [texts]<br/>        return await self._call_model(texts)<br/><br/>    async def embed_batch(self, texts: List[str],<br/>                          batch_size: int = 128) -&gt; List[List[float]]:<br/>        # ★特殊点2 批量上限：一次塞太多文本，轻则超请求体限制，重则触发 429 限流<br/>        for i in range(0, len(texts), batch_size):<br/>            ...   # 分批调用 embed，结果按序 extend 返回<br/><br/>    async def _call_model(self, texts: List[str], retries: int = 4) -&gt; List[List[float]]:<br/>        """调用嵌入 API：429/5xx 指数退避重试；连接失败同样退避重试"""<br/>        for attempt in range(1, retries + 1):<br/>            try:<br/>                ...   # client.embeddings.create(model, input, dimensions)；<br/>                ...   # 按 resp.data 的 index 排序对齐输入，返回 [item.embedding ...]<br/>            except (APIConnectionError, APITimeoutError):<br/>                await asyncio.sleep(2 ** attempt)      # ★特殊点3 连接级失败：指数退避后重试<br/>            except APIStatusError as exc:<br/>                if exc.status_code == 429 or exc.status_code &gt;= 500:<br/>                    await asyncio.sleep(2 ** attempt)  # ★特殊点4 限流/服务端错误：指数退避<br/>                else:<br/>                    # 401/404 等是鉴权/配置问题，重试没有意义，直接给可行动报错<br/>                    raise RuntimeError(<br/>                        f"嵌入请求失败 HTTP {exc.status_code}："<br/>                        f"检查模型名 {self.model!r} 与 OPENAI_API_KEY"<br/>                    ) from exc<br/>        raise RuntimeError(f"重试 {retries} 次仍失败（限流或服务端故障），请降低 batch_size 后再试")</code>
```

---

---

核心思路：**中文场景本地跑 BAAI/bge-m3——多语言、多粒度（支持稠密/稀疏/多向量三种检索形态），不花 API 费用、数据不出域；本地模型无需 API key**。

```
<code>import numpy as np<br/>from sentence_transformers import SentenceTransformers<br/><br/># 本地加载 BGE-M3（首次运行会自动下载权重；无 GPU 也能跑，速度换设备）<br/>model = SentenceTransformers("BAAI/bge-m3")<br/><br/>doc_embeddings = model.encode(<br/>    ["公司年假政策：每年 5 天带薪年假，工龄满 10 年增至 10 天。", "报销单需部门主管与财务双签。"],<br/>    normalize_embeddings=True,  # 归一化后点积即余弦相似度<br/>)<br/>query_embedding = model.encode(["年假有几天？"], normalize_embeddings=True)<br/><br/>sims = doc_embeddings @ query_embedding.T<br/>print(sims.ravel())</code>
```

**换模型 = 换向量空间**：不同模型的向量不可混用（维度都可能不同）——切换供应商/模型/维度后，存量索引必须全量重建。

### 企业级升级要点

- **显式版本绑定**：embed_version 与向量兼容性绑定——换供应商/模型 = 换值 = 全量重建索引，禁止跨版本向量混用，见 `ai-rag-self-engineering/ownrag/ownrag/index/embedder.py` 模块注释。
- **限流是摄取最高频故障**：批量上限 + 429/5xx 指数退避是两条主防线；4xx 其他错误不重试（配置/鉴权问题，重试无用），错误分型口径见 `ai-rag-self-engineering/ownrag/ownrag/index/embedder.py` 的 `_embed_texts_openai`。
- **连接级失败熔断**：连接失败反复重试会让一次问答付两份延迟代价（SYN 被丢时本机一次就要 2 秒以上）——熔断窗口内快速失败，见同文件 `breaker_open`。
- **供应商可换不动代码**：ollama 原生 / OpenAI 兼容 /embeddings 双分派，换后端只改 base_url/model/key，见 `ai-rag-self-engineering/ownrag/ownrag/index/embedder.py` 的 `embed_texts`。
- **配置即代码**：API key 一律 `os.environ` 读取、缺失报可行动错误，见 `ai-rag-self-engineering/ownrag/ownrag/config.py`。

70-企业级工程基准

---

---