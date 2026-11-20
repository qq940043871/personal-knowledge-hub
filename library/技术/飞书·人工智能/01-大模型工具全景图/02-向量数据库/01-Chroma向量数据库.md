# Chroma向量数据库

> 模块：向量数据库
> 更新时间：2026-11-15（代码口径：chromadb 0.4+ / langchain-chroma 分包）

---

## 一、框架介绍与核心特点

Chroma是一个**开源的向量数据库，专门为LLM应用设计**，专注于存储和检索嵌入向量。

**官网**：https://www.trychroma.com
**GitHub**：https://github.com/chroma-core/chroma

**核心特点**：
- 轻量级，易于部署
- 支持元数据过滤
- 与LangChain/LlamaIndex无缝集成
- 支持Python和JavaScript
- 本地存储，无需云服务

*图：Chroma 从添加数据到查询结果的流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 120" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="3" y="30" width="122" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="64" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">① 添加数据</text>
  <text x="64" y="73" text-anchor="middle" font-size="13" fill="#475569">documents+metadata</text>
  <line x1="127" y1="58" x2="149" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="151" y="30" width="122" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="212" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">② 向量嵌入</text>
  <text x="212" y="73" text-anchor="middle" font-size="13" fill="#475569">Embedding</text>
  <line x1="275" y1="58" x2="297" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="299" y="30" width="122" height="56" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">③ Collection 存储</text>
  <text x="360" y="73" text-anchor="middle" font-size="13" fill="#475569">HNSW 索引</text>
  <line x1="423" y1="58" x2="445" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="447" y="30" width="122" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="508" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">④ 相似查询</text>
  <text x="508" y="73" text-anchor="middle" font-size="13" fill="#475569">query + where 过滤</text>
  <line x1="571" y1="58" x2="593" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="595" y="30" width="122" height="56" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="656" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">⑤ 返回结果</text>
  <text x="656" y="73" text-anchor="middle" font-size="13" fill="#475569">n_results 条</text>
</svg>

---

## 二、核心概念：Collection、Embedding 与 Metadata

```
Chroma核心概念：
  - Collection（集合）：类似表
  - Embeddings（嵌入）：向量数据
  - Documents（文档）：原始文本
  - Metadata（元数据）：附加信息
```

---

## 三、实际业务应用场景

### 场景1：快速入门

```python
import chromadb

# 1. 创建客户端
client = chromadb.Client()

# 2. 创建集合
collection = client.create_collection(
    name="my_documents",
    metadata={"hnsw:space": "cosine"}  # 距离度量
)

# 3. 添加数据
collection.add(
    documents=[
        "Python是一种高级编程语言",
        "JavaScript用于Web开发",
        "机器学习是AI的子领域"
    ],
    ids=["doc1", "doc2", "doc3"],
    metadatas=[
        {"source": "python", "category": "编程"},
        {"source": "javascript", "category": "编程"},
        {"source": "ml", "category": "AI"}
    ]
)

# 4. 查询
results = collection.query(
    query_texts=["什么是Python？"],
    n_results=2
)

print(results)

# 5. 查找带过滤
results = collection.query(
    query_texts=["编程语言"],
    where={"category": "编程"}  # 元数据过滤
)
```

### 场景2：持久化存储

```python
import chromadb

# 持久化客户端
client = chromadb.PersistentClient(
    path="./chroma_data"  # 本地存储路径
)

# 创建或获取集合
collection = client.get_or_create_collection("my_docs")

# 后续可以直接加载
# client = chromadb.PersistentClient(path="./chroma_data")
# collection = client.get_collection("my_docs")
```

### 场景3：与LangChain集成

```python
# 现行分包：pip install langchain-community langchain-openai langchain-chroma langchain-text-splitters
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 加载文档
loader = TextLoader("document.txt")
documents = loader.load()

# 2. 分块
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# 3. 存入Chroma（persist_directory 指定后自动持久化）
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=OpenAIEmbeddings(),
    persist_directory="./chroma_db"  # 持久化目录
)

# 4. 检索
docs = vectorstore.similarity_search("Python的特点", k=3)

# 注意：chromadb 0.4+ 起 data 写入即自动持久化，vectorstore.persist() 已废弃并被移除，
# 无需（也不能）再手动调用
```

### 场景4：元数据过滤

```python
# 创建带元数据的集合
collection.add(
    documents=[
        "产品A的详细描述...",
        "产品B的详细描述...",
        "产品C的详细描述..."
    ],
    ids=["p1", "p2", "p3"],
    metadatas=[
        {"category": "电子产品", "price": 2999, "in_stock": True},
        {"category": "服装", "price": 199, "in_stock": True},
        {"category": "电子产品", "price": 5999, "in_stock": False}
    ]
)

# 过滤查询：找电子产品且有库存
results = collection.query(
    query_texts=["好的产品推荐"],
    where={
        "category": "电子产品",
        "in_stock": True
    }
)

# 价格范围过滤
results = collection.query(
    query_texts=["性价比高的"],
    where={
        "price": {"$gte": 1000, "$lte": 5000}
    }
)
```

---

## 四、高级特性：批量操作与距离度量

### 1. 批量操作

```python
# 批量添加
collection.add(
    documents=["doc1", "doc2", "doc3"],
    ids=["id1", "id2", "id3"],
    embeddings=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]  # 可选
)

# 批量更新
collection.update(
    ids=["id1"],
    documents=["更新的内容"]
)

# 批量删除
collection.delete(ids=["id1", "id2"])
```

### 2. 获取和计数

```python
# 获取集合中所有数据
all_data = collection.get()

# 获取指定ID
data = collection.get(ids=["id1", "id2"])

# 统计数量
count = collection.count()

# 列出所有集合
collections = client.list_collections()
```

### 3. 距离度量

```python
# 余弦相似度（默认）
collection = client.create_collection(
    name="cosine_demo",
    metadata={"hnsw:space": "cosine"}
)

# 欧氏距离
collection = client.create_collection(
    name="l2_demo",
    metadata={"hnsw:space": "l2"}
)

# 点积
collection = client.create_collection(
    name="ip_demo",
    metadata={"hnsw:space": "ip"}
)
```

---

## 五、部署方式：本地 / 服务 / Docker

### 1. 本地模式（开发）

```python
# 直接使用客户端
client = chromadb.Client()
```

### 2. 服务模式（生产）

```bash
# 启动Chroma服务
pip install chromadb[server]
# 生产环境务必开启鉴权（token 认证示例），避免检索端口裸奔：
#   export CHROMA_SERVER_AUTHN_PROVIDER=chromadb.auth.token_authn.TokenAuthServerProvider
#   export CHROMA_SERVER_AUTHN_CREDENTIALS_FILE=./chroma_token.txt
chroma run --host localhost --port 8000

# 客户端连接（对应携带同一 token）
client = chromadb.HttpClient(
    host="localhost",
    port=8000,
    headers={"Authorization": "Bearer <你的token>"},  # 与服务端配置一致
)
```

### 3. Docker部署

```yaml
version: '3.8'

services:
  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
```

---

## 六、总结与适用场景

Chroma是**入门向量数据库的最佳选择**，轻量、简单、功能齐全。

**学习要点**：
1. 理解Collection和Document概念
2. 掌握添加、查询、过滤操作
3. 熟练与LangChain/LlamaIndex集成
4. 了解不同的距离度量方式
5. 理解持久化存储

**适用场景**：
- 个人项目/小规模应用
- 原型验证
- 学习和实验
- 简单RAG系统

**注意**：对于大规模生产环境，建议使用Milvus或Pinecone。

---

### 企业级升级要点

Chroma 适合原型与中小规模，企业级 RAG 还要补齐以下工程能力，参考 ownrag 基准工程（D:\ai_person\personal-ai-engineering\ai-rag-self-engineering\ownrag）：

- **存储可审计**：ownrag 的向量库是本地可审计存储（建表/写索引/检索全透明、可物理删除），见 `ownrag/index/store.py`——生产要能回答"数据在哪、怎么删、谁动过"。
- **服务隔离与鉴权**：向量库作为独立服务部署时必须加鉴权与网络隔离（本文服务模式的 token 即此意），密钥只走环境变量，参考 `ownrag/config.py`。
- **混合检索**：纯向量召回会漏关键词精确命中，ownrag 用向量+BM25 双路 → RRF 名次融合，见 `ownrag/retrieve/hybrid.py`。
- **重排与降级**：召回结果用重排模型（如 bge-reranker-v2-m3）精排、provider 失败降级可见，见 `ownrag/retrieve/rerank.py`。
- **规模拐点**：数据到千万级/多租户时迁移 Milvus 等分布式方案，迁移前先用评测集确认召回质量不回退。

延伸阅读：[70-企业级工程基准](../../06-Agent开发/70-企业级工程基准.md)

---

*下一步：Milvus分布式向量数据库*
