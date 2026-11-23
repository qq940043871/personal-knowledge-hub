# Milvus向量数据库

> 模块：向量数据库  
> 更新时间：2026-11-15（代码口径：pymilvus 2.4+，推荐 MilvusClient）

---

---

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

---

```
<code>Milvus核心概念：<br/>  - Collection（集合）：相当于表<br/>  - Partition（分区）：集合的逻辑分区<br/>  - Field（字段）：Collection的列<br/>  - Entity（实体）：Collection的行<br/>  - Shard（分片）：数据分片<br/>  - Segment（段）：数据存储单元</code>
```

---

---

### 场景1：Python SDK基础操作

先看经典的 ORM 式写法（`connections.connect` + `Collection`），大量存量代码仍在使用：

```
<code>from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections<br/><br/># 1. 连接<br/>connections.connect(alias="default", host="localhost", port="19530")<br/><br/># 2. 定义Schema<br/>fields = [<br/>    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),<br/>    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),<br/>    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),<br/>    FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100)<br/>]<br/>schema = CollectionSchema(fields=fields, description="文档集合")<br/><br/># 3. 创建Collection<br/>collection = Collection(name="my_documents", schema=schema)<br/><br/># 4. 创建索引<br/>index_params = {<br/>    "index_type": "IVF_FLAT",<br/>    "metric_type": "L2",<br/>    "params": {"nlist": 128}<br/>}<br/>collection.create_index(<br/>    field_name="embedding",<br/>    index_params=index_params<br/>)<br/><br/># 5. 插入数据<br/>import numpy as np<br/><br/>entities = [<br/>    [1, 2, 3],  # id<br/>    np.random.rand(3, 768).tolist(),  # embedding<br/>    ["内容1", "内容2", "内容3"],  # content<br/>    ["科技", "教育", "娱乐"]  # category<br/>]<br/>insert_result = collection.insert(entities)<br/><br/># 6. 加载到内存<br/>collection.load()<br/><br/># 7. 搜索<br/>search_params = {"metric_type": "L2", "params": {"nprobe": 10}}<br/><br/>results = collection.search(<br/>    data=[np.random.rand(768).tolist()],  # 查询向量<br/>    anns_field="embedding",<br/>    param=search_params,<br/>    limit=10,<br/>    expr='category == "科技"',  # 过滤条件<br/>    output_fields=["id", "content", "category"]<br/>)<br/><br/>for result in results[0]:<br/>    print(f"ID: {result.id}, Distance: {result.distance}, Content: {result.entity.get('content')}")<br/><br/># 8. 查询<br/>results = collection.query(<br/>    expr='category == "科技"',<br/>    output_fields=["id", "content", "category"],<br/>    limit=10<br/>)</code>
```

**现行推荐：MilvusClient（pymilvus 2.4+）**——同样能力、更简洁的接口，新项目优先用它：

```
<code># （伪代码：保留 Schema / 索引 / dict 插入 / filter 搜索四个关键调用形态）<br/>import numpy as np<br/>from pymilvus import DataType, MilvusClient<br/># 连接（★特殊点1 默认凭据治理：token 格式 "用户名:密码"，默认 root/Milvus，<br/># 上线前必须替换并走环境变量/密钥管理）<br/>client = MilvusClient(uri="http://localhost:19530", token="root:Milvus")<br/># 1) Schema：add_field 每字段一行（content / category 等 VARCHAR 字段同形，从略）<br/>schema = client.create_schema(auto_id=False, enable_dynamic_field=True)<br/>schema.add_field("id", DataType.INT64, is_primary=True)<br/>schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=768)<br/># 2) 索引参数 + 创建集合（创建即加载到内存，可直接检索；同名集合先 drop，从略）<br/>index_params = client.prepare_index_params()<br/>index_params.add_index(field_name="embedding", index_type="IVF_FLAT",<br/>                       metric_type="L2", params={"nlist": 128})<br/>client.create_collection("my_documents", schema=schema, index_params=index_params)<br/># 3) 插入：一行一个 dict（embedding 为 768 维向量，示意 1 行）<br/>client.insert("my_documents", data=[{"id": 1, "embedding": np.random.rand(768).tolist(),<br/>                                     "content": "内容1", "category": "科技"}])<br/># 4) 搜索（现行 API：标量过滤参数是 filter=）<br/>results = client.search(<br/>    "my_documents", data=[np.random.rand(768).tolist()],   # 查询向量（示意）<br/>    anns_field="embedding", limit=10,<br/>    search_params={"metric_type": "L2", "params": {"nprobe": 10}},<br/>    filter='category == "科技"', output_fields=["id", "content", "category"])</code>
```

### 场景2：混合搜索

```
<code>import numpy as np<br/><br/># 承接场景1的 collection / search_params；以下两个变量为示意定义：<br/>query = "示例查询：向量数据库的索引类型"<br/>query_vector = np.random.rand(768).tolist()  # 示意：实际项目用 Embedding 模型把 query 编码成 768 维<br/><br/># 搜索时同时返回向量<br/>results = collection.search(<br/>    data=[query_vector],<br/>    anns_field="embedding",<br/>    param=search_params,<br/>    limit=10,<br/>    output_fields=["id", "content", "category"]<br/>)<br/><br/># 获取原始向量用于重排序<br/>results = collection.search(<br/>    data=[query_vector],<br/>    anns_field="embedding",<br/>    param={"metric_type": "L2", "params": {"nprobe": 100}},  # 检索更多<br/>    limit=50,  # 取更多候选<br/>    output_fields=["embedding", "content"]<br/>)<br/><br/>def rerank_with_cross_encoder(results, query: str):<br/>    """示意：Cross-Encoder 重排接口形态——真实实现把 (query, doc) 对喂给重排模型<br/>    （如 BAAI/bge-reranker-v2-m3）按重排分降序；provider 化与失败降级见<br/>    ownrag/retrieve/rerank.py。此处按向量距离升序返回，保证示例可独立运行。"""<br/>    return sorted(results[0], key=lambda r: r.distance)<br/><br/># 本地重排序（使用更精确的模型）<br/>reranked = rerank_with_cross_encoder(results, query)</code>
```

### 场景3：分区管理

```
<code># 创建分区<br/>collection.create_partition("category_科技")<br/>collection.create_partition("category_教育")<br/><br/># 插入到分区<br/>collection.insert(<br/>    entities,<br/>    partition_name="category_科技"<br/>)<br/><br/># 分区搜索（更快）<br/>results = collection.search(<br/>    data=[query_vector],<br/>    partition_names=["category_科技"],  # 指定分区<br/>    param=search_params,<br/>    limit=10<br/>)</code>
```

---

---

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |

```
<code># 选择索引<br/>index_params = {<br/>    "index_type": "HNSW",  # 图索引<br/>    "metric_type": "L2",<br/>    "params": {"M": 16, "efConstruction": 200}<br/>}</code>
```

---

---

### 1. Docker Compose（开发）

```
<code># docker-compose.yml<br/># 注意：下面镜像版本是旧版教学示例（v2.3.3），<br/># 生产部署请到 https://github.com/milvus-io/milvus/releases 下载与所用 pymilvus 匹配的最新稳定版 compose 文件<br/>version: '3.8'<br/><br/>services:<br/>  etcd:<br/>    image: quay.io/coreos/etcd:v3.5.5<br/>    environment:<br/>      - ETCD_AUTO_COMPACTION_MODE=revision<br/>      - ETCD_AUTO_COMPACTION_RETENTION=1000<br/>    volumes:<br/>      - etcd_data:/etcd<br/><br/>  minio:<br/>    image: minio/minio:RELEASE.2023-03-20T20-16-18Z<br/>    environment:<br/>      # 安全提示：minioadmin/minioadmin 是默认凭据，生产环境务必修改，<br/>      # 并通过密钥管理或环境变量注入，不要提交到代码仓库<br/>      MINIO_ACCESS_KEY: minioadmin<br/>      MINIO_SECRET_KEY: minioadmin<br/>    volumes:<br/>      - minio_data:/minio_data<br/><br/>  milvus:<br/>    image: milvusdb/milvus:v2.3.3  # 旧版示例，建议升级到最新稳定版<br/>    ports:<br/>      - "19530:19530"<br/>      - "9091:9091"<br/>    environment:<br/>      ETCD_ENDPOINTS: etcd:2379<br/>      MINIO_ADDRESS: minio:9000<br/>    volumes:<br/>      - milvus_data:/var/lib/milvus<br/>    depends_on:<br/>      - etcd<br/>      - minio</code>
```

### 2. Kubernetes生产部署

```
<code># milvus-cluster.yaml<br/>apiVersion: milvus.io/v1beta1<br/>kind: Milvus<br/>metadata:<br/>  name: my-milvus<br/>spec:<br/>  mode: cluster<br/>  components:<br/>    coord:<br/>      replicas: 1<br/>    data:<br/>      replicas: 2<br/>    index:<br/>      replicas: 2<br/>    query:<br/>      replicas: 2<br/>  config:<br/>    etcd:<br/>      endpoints:<br/>        - etcd:2379<br/>    storage:<br/>      type: minio</code>
```

*图：Milvus Docker Compose 部署组成（示意）*

客户端应用PyMilvus SDKMilvus 服务端口 :19530etcd :2379元数据存储MinIO :9000对象存储

---

---

```
<code># 启动Attu<br/>docker run -d -p 8000:3000 -e MILVUS_URL=http://localhost:19530 zilliz/attu:latest</code>
```

然后访问 http://localhost:8000 查看Milvus的Web管理界面。

---

---

Milvus是**企业级向量数据库的首选**，支持大规模数据、高并发、分布式部署。

**学习要点**：

1. 理解Collection和Partition概念
1. 掌握不同索引类型的适用场景
1. 熟练使用Python SDK
1. 理解分区策略
1. 了解分布式架构

**适用场景**：

- 大规模向量检索（亿级）
- 生产级RAG系统
- 推荐系统
- 图像/视频检索

---

---

Milvus 解决的是"存得下、查得快"，企业级 RAG 还要补齐检索质量与运维纪律，参考 ownrag 基准工程：

- **默认凭据必须改**：Milvus/etcd/MinIO 的默认账号密码（如 minioadmin、root/Milvus）上线前全部替换并走密钥管理，密钥只进环境变量，参考 `ownrag/config.py`。
- **混合检索**：向量召回之外补 BM25 关键词通道，双路结果用 RRF 名次融合（等权起步、评测先行），见 `ownrag/retrieve/hybrid.py`。
- **重排与降级**：粗排候选用重排模型精排（如 bge-reranker-v2-m3），provider 可插拔、失败降级可见，见 `ownrag/retrieve/rerank.py`。
- **版本与配置纪律**：镜像版本与 pymilvus 版本配套升级（本文 compose 的 v2.3.3 只是示例），配置即代码、启动期校验，避免"跑得起来但语义漂移"。
- **数据可治理**：集合/分区按业务与权限划分，能按 doc_id 精确删除与重建——参考 `ownrag/index/store.py` 的透明存储设计。

延伸阅读：70-企业级工程基准

---

---