# OpenAI Embeddings

> 模块：Embedding模型
> 更新时间：2026-11-15（代码口径：openai SDK 1.x，密钥走环境变量）

---

## 一、模型介绍与可用模型

OpenAI Embeddings是**将文本转换为向量表示的模型服务**，用于文本相似度计算、语义搜索等场景。

**官网**：https://platform.openai.com/docs/guides/embeddings

**可用模型**：
- `text-embedding-3-large`：最新最强，3072维
- `text-embedding-3-small`：新性价比模型，1536维
- `text-embedding-ada-002`：经典模型，1536维

*图：文本向量化与语义搜索流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 120" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="2" y="30" width="155" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="79" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">① 文本输入</text>
  <text x="79" y="73" text-anchor="middle" font-size="13" fill="#475569">documents / query</text>
  <line x1="157" y1="58" x2="187" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="189" y="30" width="155" height="56" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="266" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">② Embeddings API</text>
  <text x="266" y="73" text-anchor="middle" font-size="13" fill="#475569">text-embedding-3-*</text>
  <line x1="344" y1="58" x2="374" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="376" y="30" width="155" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="453" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">③ 向量表示</text>
  <text x="453" y="73" text-anchor="middle" font-size="13" fill="#475569">1536 / 3072 维</text>
  <line x1="531" y1="58" x2="561" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="563" y="30" width="155" height="56" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="640" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">④ 相似度与排序</text>
  <text x="640" y="73" text-anchor="middle" font-size="13" fill="#475569">cosine · Top-K</text>
</svg>

---

## 二、实际业务应用场景

### 场景1：基础使用

```python
# pip install openai（SDK 1.x）
import os

from openai import OpenAI

# API key 一律从环境变量读取（export OPENAI_API_KEY=...），禁止硬编码
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# 获取文本嵌入
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="Python是一种高级编程语言"
)

embedding = response.data[0].embedding
print(f"向量维度: {len(embedding)}")
print(f"前5个值: {embedding[:5]}")
```

### 场景2：批量嵌入

```python
# 批量处理
texts = [
    "Python编程基础",
    "Java Web开发",
    "机器学习入门",
    "深度学习实战",
    "数据结构与算法"
]

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=texts  # 最多支持2048个
)

embeddings = [item.embedding for item in response.data]
print(f"生成 {len(embeddings)} 个向量")
```

**429 限流重试**：批量嵌入很容易触发限流（RateLimitError），生产代码要带指数退避重试：

```python
import time

from openai import OpenAI, RateLimitError

def embed_with_retry(client: OpenAI, texts: list[str],
                     model: str = "text-embedding-3-small",
                     max_retries: int = 5):
    """带指数退避的重试：429 时等待 1s/2s/4s/... 后重试（示意）。
    大批量任务也可改用 openai SDK 自带的 max_retries 参数或官方批处理接口。"""
    for attempt in range(max_retries):
        try:
            return client.embeddings.create(model=model, input=texts)
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # 指数退避：1s, 2s, 4s, ...
    raise RuntimeError("嵌入请求重试次数用尽")
```

### 场景3：语义搜索

```python
import numpy as np

# 文档
documents = [
    "Python适合快速原型开发",
    "Java是企业级开发的首选",
    "机器学习用于数据分析",
    "深度学习是AI的核心技术",
    "算法是编程的基础"
]

# 获取文档向量
doc_response = client.embeddings.create(
    model="text-embedding-3-small",
    input=documents
)
doc_embeddings = [item.embedding for item in doc_response.data]

# 查询
query = "AI和机器学习有什么关系？"
query_response = client.embeddings.create(
    model="text-embedding-3-small",
    input=query
)
query_embedding = query_response.data[0].embedding

# 计算相似度
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

results = []
for i, doc_emb in enumerate(doc_embeddings):
    similarity = cosine_similarity(query_embedding, doc_emb)
    results.append((i, documents[i], similarity))

# 排序
results.sort(key=lambda x: x[2], reverse=True)

print("搜索结果：")
for i, doc, score in results:
    print(f"  {score:.4f} - {doc}")
```

### 场景4：文档分类

```python
# 定义类别向量
categories = {
    "编程开发": ["Python", "Java", "C++", "编程", "代码", "开发"],
    "人工智能": ["AI", "机器学习", "深度学习", "神经网络", "模型"],
    "数据分析": ["数据", "分析", "统计", "可视化", "图表"]
}

# 获取类别中心向量
category_embeddings = {}
for category, keywords in categories.items():
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=" ".join(keywords)
    )
    category_embeddings[category] = response.data[0].embedding

# 分类新文档
def classify(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    text_emb = response.data[0].embedding
    
    # 计算与各类别的相似度
    scores = {}
    for category, cat_emb in category_embeddings.items():
        scores[category] = cosine_similarity(text_emb, cat_emb)
    
    # 返回最高分类
    return max(scores, key=scores.get)

# 测试
text = "使用神经网络进行图像识别"
print(classify(text))  # 输出: 人工智能
```

---

## 三、维度缩减（dimensions 参数）

```python
# text-embedding-3支持维度缩减
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="文本内容",
    dimensions=256  # 缩减到256维
)
```

---

## 四、总结与适用场景

OpenAI Embeddings是**最方便使用的Embedding服务**，适合快速原型和小型应用。

**适用场景**：
- 快速原型开发
- 小规模向量检索
- 语义相似度计算
- 文档分类

**注意**：
- 需要API Key和网络访问
- 有使用成本
- 国内访问可能不稳定

---

### 企业级升级要点

云端 Embedding 服务好用，但企业级 RAG 对嵌入层还有更多工程要求，参考 ownrag 基准工程：

- **密钥纪律**：API key 只走环境变量（本文 `os.environ["OPENAI_API_KEY"]`），不落配置文件与代码库，参考 `ownrag/config.py`（`OWNRAG_CHAT_API_KEY` 只进环境变量）。
- **限流与重试**：批量嵌入必须带指数退避重试与失败记录（本文 429 示例），必要时切自托管模型（如 BAAI/bge-m3）消除外部依赖，参考 `ownrag/index/embedder.py`。
- **模型一致性**：入库与查询必须用同一嵌入模型与维度（模型换了就要全量重建索引），ownrag 把嵌入参数纳入启动期配置校验，见 `ownrag/index/embedder.py` 与 `ownrag/config.py`。
- **成本与预算**：嵌入按 token 计费，大批量任务先估算成本、可切批处理接口；ownrag 在生成层做了 token 预算控制，思路一致，见 `ownrag/generate/budget.py`。
- **质量评测**：换嵌入模型要过评测集（召回率/排序质量回归），没有评测集不切换，见 08-评估测试 RAGAS 篇。

延伸阅读：[70-企业级工程基准](../../06-Agent开发/70-企业级工程基准.md)

---

*下一步：中文Embedding模型BGE*
