# Milvus向量数据库

> 模块：向量数据库
> 更新时间：2026-11-15（代码口径：pymilvus 2.4+，推荐 MilvusClient）

---

## 一、框架介绍与核心特点

Milvus是Apache软件基金会的顶级项目，是一个**开源的分布式向量数据库，专为大规模向量相似性搜索设计**。

**官网**：https://milvus.io
**GitHub**：https://github.com/milvus-io/milvus

**核心特点**：
- 十亿级向量支持
- 分布式架构
- 多种索引类型
- 高性能检索
- 云原生设计

---

## 二、核心概念：Collection、Partition 与 Segment

```
Milvus核心概念：
  - Collection（集合）：相当于表
  - Partition（分区）：集合的逻辑分区
  - Field（字段）：Collection的列
  - Entity（实体）：Collection的行
  - Shard（分片）：数据分片
  - Segment（段）：数据存储单元
```

---

## 三、实际业务应用场景

### 场景1：Python SDK基础操作

先看经典的 ORM 式写法（`connections.connect` + `Collection`），大量存量代码仍在使用：

```python
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections

# 1. 连接
connections.connect(alias="default", host="localhost", port="19530")

# 2. 定义Schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100)
]
schema = CollectionSchema(fields=fields, description="文档集合")

# 3. 创建Collection
collection = Collection(name="my_documents", schema=schema)

# 4. 创建索引
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "params": {"nlist": 128}
}
collection.create_index(
    field_name="embedding",
    index_params=index_params
)

# 5. 插入数据
import numpy as np

entities = [
    [1, 2, 3],  # id
    np.random.rand(3, 768).tolist(),  # embedding
    ["内容1", "内容2", "内容3"],  # content
    ["科技", "教育", "娱乐"]  # category
]
insert_result = collection.insert(entities)

# 6. 加载到内存
collection.load()

# 7. 搜索
search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

results = collection.search(
    data=[np.random.rand(768).tolist()],  # 查询向量
    anns_field="embedding",
    param=search_params,
    limit=10,
    expr='category == "科技"',  # 过滤条件
    output_fields=["id", "content", "category"]
)

for result in results[0]:
    print(f"ID: {result.id}, Distance: {result.distance}, Content: {result.entity.get('content')}")

# 8. 查询
results = collection.query(
    expr='category == "科技"',
    output_fields=["id", "content", "category"],
    limit=10
)
```

**现行推荐：MilvusClient（pymilvus 2.4+）**——同样能力、更简洁的接口，新项目优先用它：

```python
# （伪代码：保留 Schema / 索引 / dict 插入 / filter 搜索四个关键调用形态）
import numpy as np
from pymilvus import DataType, MilvusClient
# 连接（★特殊点1 默认凭据治理：token 格式 "用户名:密码"，默认 root/Milvus，
# 上线前必须替换并走环境变量/密钥管理）
client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")
# 1) Schema：add_field 每字段一行（content / category 等 VARCHAR 字段同形，从略）
schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
schema.add_field("id", DataType.INT64, is_primary=True)
schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=768)
# 2) 索引参数 + 创建集合（创建即加载到内存，可直接检索；同名集合先 drop，从略）
index_params = client.prepare_index_params()
index_params.add_index(field_name="embedding", index_type="IVF_FLAT",
                       metric_type="L2", params={"nlist": 128})
client.create_collection("my_documents", schema=schema, index_params=index_params)
# 3) 插入：一行一个 dict（embedding 为 768 维向量，示意 1 行）
client.insert("my_documents", data=[{"id": 1, "embedding": np.random.rand(768).tolist(),
                                     "content": "内容1", "category": "科技"}])
# 4) 搜索（现行 API：标量过滤参数是 filter=）
results = client.search(
    "my_documents", data=[np.random.rand(768).tolist()],   # 查询向量（示意）
    anns_field="embedding", limit=10,
    search_params={"metric_type": "L2", "params": {"nprobe": 10}},
    filter='category == "科技"', output_fields=["id", "content", "category"])
```

### 场景2：混合搜索

```python
import numpy as np

# 承接场景1的 collection / search_params；以下两个变量为示意定义：
query = "示例查询：向量数据库的索引类型"
query_vector = np.random.rand(768).tolist()  # 示意：实际项目用 Embedding 模型把 query 编码成 768 维

# 搜索时同时返回向量
results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param=search_params,
    limit=10,
    output_fields=["id", "content", "category"]
)

# 获取原始向量用于重排序
results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param={"metric_type": "L2", "params": {"nprobe": 100}},  # 检索更多
    limit=50,  # 取更多候选
    output_fields=["embedding", "content"]
)

def rerank_with_cross_encoder(results, query: str):
    """示意：Cross-Encoder 重排接口形态——真实实现把 (query, doc) 对喂给重排模型
    （如 BAAI/bge-reranker-v2-m3）按重排分降序；provider 化与失败降级见
    ownrag/retrieve/rerank.py。此处按向量距离升序返回，保证示例可独立运行。"""
    return sorted(results[0], key=lambda r: r.distance)

# 本地重排序（使用更精确的模型）
reranked = rerank_with_cross_encoder(results, query)
```

### 场景3：分区管理

```python
# 创建分区
collection.create_partition("category_科技")
collection.create_partition("category_教育")

# 插入到分区
collection.insert(
    entities,
    partition_name="category_科技"
)

# 分区搜索（更快）
results = collection.search(
    data=[query_vector],
    partition_names=["category_科技"],  # 指定分区
    param=search_params,
    limit=10
)
```

---

## 四、索引类型

| 索引类型 | 适用场景 | 特点 |
|---------|---------|------|
| FLAT | 小规模数据 | 精确检索，100%召回 |
| IVF_FLAT | 中等规模 | 聚类+精确检索 |
| IVF_SQ8 | 大规模数据 | 量化压缩 |
| HNSW | 追求速度 | 图索引，高召回 |
| ANNOY | 追求内存效率 | 树索引 |

```python
# 选择索引
index_params = {
    "index_type": "HNSW",  # 图索引
    "metric_type": "L2",
    "params": {"M": 16, "efConstruction": 200}
}
```

---

## 五、部署方式：Docker Compose 与 Kubernetes

### 1. Docker Compose（开发）

```yaml
# docker-compose.yml
# 注意：下面镜像版本是旧版教学示例（v2.3.3），
# 生产部署请到 https://github.com/milvus-io/milvus/releases 下载与所用 pymilvus 匹配的最新稳定版 compose 文件
version: '3.8'

services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
    volumes:
      - etcd_data:/etcd
  
  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      # 安全提示：minioadmin/minioadmin 是默认凭据，生产环境务必修改，
      # 并通过密钥管理或环境变量注入，不要提交到代码仓库
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - minio_data:/minio_data
  
  milvus:
    image: milvusdb/milvus:v2.3.3  # 旧版示例，建议升级到最新稳定版
    ports:
      - "19530:19530"
      - "9091:9091"
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    depends_on:
      - etcd
      - minio
```

### 2. Kubernetes生产部署

```yaml
# milvus-cluster.yaml
apiVersion: milvus.io/v1beta1
kind: Milvus
metadata:
  name: my-milvus
spec:
  mode: cluster
  components:
    coord:
      replicas: 1
    data:
      replicas: 2
    index:
      replicas: 2
    query:
      replicas: 2
  config:
    etcd:
      endpoints:
        - etcd:2379
    storage:
      type: minio
```

*图：Milvus Docker Compose 部署组成（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 220" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="92" width="160" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="100" y="115" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">客户端应用</text>
  <text x="100" y="135" text-anchor="middle" font-size="13" fill="#475569">PyMilvus SDK</text>
  <line x1="180" y1="120" x2="236" y2="120" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="240" y="92" width="180" height="56" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="330" y="115" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">Milvus 服务</text>
  <text x="330" y="135" text-anchor="middle" font-size="13" fill="#475569">端口 :19530</text>
  <line x1="420" y1="112" x2="500" y2="72" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="420" y1="128" x2="500" y2="164" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="504" y="40" width="180" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="594" y="63" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">etcd :2379</text>
  <text x="594" y="83" text-anchor="middle" font-size="13" fill="#475569">元数据存储</text>
  <rect x="504" y="140" width="180" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="594" y="163" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">MinIO :9000</text>
  <text x="594" y="183" text-anchor="middle" font-size="13" fill="#475569">对象存储</text>
</svg>

---

## 六、Attu图形界面

```bash
# 启动Attu
docker run -d -p 8000:3000 -e MILVUS_URL=http://localhost:19530 zilliz/attu:latest
```

然后访问 http://localhost:8000 查看Milvus的Web管理界面。

---

## 七、总结与适用场景

Milvus是**企业级向量数据库的首选**，支持大规模数据、高并发、分布式部署。

**学习要点**：
1. 理解Collection和Partition概念
2. 掌握不同索引类型的适用场景
3. 熟练使用Python SDK
4. 理解分区策略
5. 了解分布式架构

**适用场景**：
- 大规模向量检索（亿级）
- 生产级RAG系统
- 推荐系统
- 图像/视频检索

---

### 企业级升级要点

Milvus 解决的是"存得下、查得快"，企业级 RAG 还要补齐检索质量与运维纪律，参考 ownrag 基准工程：

- **默认凭据必须改**：Milvus/etcd/MinIO 的默认账号密码（如 minioadmin、root/Milvus）上线前全部替换并走密钥管理，密钥只进环境变量，参考 `ownrag/config.py`。
- **混合检索**：向量召回之外补 BM25 关键词通道，双路结果用 RRF 名次融合（等权起步、评测先行），见 `ownrag/retrieve/hybrid.py`。
- **重排与降级**：粗排候选用重排模型精排（如 bge-reranker-v2-m3），provider 可插拔、失败降级可见，见 `ownrag/retrieve/rerank.py`。
- **版本与配置纪律**：镜像版本与 pymilvus 版本配套升级（本文 compose 的 v2.3.3 只是示例），配置即代码、启动期校验，避免"跑得起来但语义漂移"。
- **数据可治理**：集合/分区按业务与权限划分，能按 doc_id 精确删除与重建——参考 `ownrag/index/store.py` 的透明存储设计。

延伸阅读：[70-企业级工程基准](../../06-Agent开发/70-企业级工程基准.md)

---

*下一步：Embedding模型详解*
