## 📋 概述

Elasticsearch 是一个功能强大的搜索引擎，通过向量插件可以实现向量搜索能力，成为完整的向量数据库解决方案。

**核心优势：**

- 成熟的分布式架构
- 强大的查询能力（向量+传统搜索）
- 完整的生态系统
- 企业级可靠性

## 🏗️ 架构设计

```
<code>┌─────────────────────────────────────────────────────┐<br/>│                 ES 向量搜索架构                      │<br/>├─────────────────────────────────────────────────────┤<br/>│  客户端 → REST API → 节点 → 分片 → 倒排索引 + 向量索引  │<br/>│                                                     │<br/>│  文本 → 嵌入模型 → 向量 → ES 索引 → 向量搜索          │<br/>└─────────────────────────────────────────────────────┘</code>
```

## 🚀 快速开始

### 1. 安装部署

```
<code># 安装 Elasticsearch 8.x<br/>docker pull docker.elastic.co/elasticsearch/elasticsearch:8.12.0<br/>docker run -d -p 9200:9200 -p 9300:9300 \<br/>  -e "discovery.type=single-node" \<br/>  -e "ES_JAVA_OPTS=-Xms1g -Xmx1g" \<br/>  -e "xpack.security.enabled=false" \<br/>  --name es docker.elastic.co/elasticsearch/elasticsearch:8.12.0<br/><br/># 检查状态<br/>curl http://localhost:9200/</code>
```

### 2. 安装向量插件

```
<code># 安装 ELSER 插件（内置向量模型）<br/>docker exec -it es bin/elasticsearch-plugin install analysis-elser<br/><br/># 或安装 KNN 插件（通用向量搜索）<br/>docker exec -it es bin/elasticsearch-plugin install analysis-knn<br/><br/># 重启 ES<br/>docker restart es</code>
```

## 🔧 核心配置

### 1. 索引创建

```
<code>import requests<br/><br/>def create_vector_index(index_name):<br/>    """创建向量索引"""<br/>    url = f"http://localhost:9200/{index_name}"<br/>    headers = {"Content-Type": "application/json"}<br/><br/>    mapping = {<br/>        "settings": {<br/>            "index": {<br/>                "number_of_shards": 1,<br/>                "number_of_replicas": 0<br/>            }<br/>        },<br/>        "mappings": {<br/>            "properties": {<br/>                "text": {<br/>                    "type": "text"<br/>                },<br/>                "vector": {<br/>                    "type": "dense_vector",<br/>                    "dims": 768,  # 向量维度<br/>                    "index": True,<br/>                    "similarity": "cosine"  # 相似度计算方式<br/>                }<br/>            }<br/>        }<br/>    }<br/><br/>    response = requests.put(url, headers=headers, json=mapping)<br/>    return response.json()<br/><br/># 创建商品索引<br/>create_vector_index("products")</code>
```

### 2. 向量数据写入

```
<code>def index_document(index_name, document_id, text, vector):<br/>    """索引文档和向量"""<br/>    url = f"http://localhost:9200/{index_name}/_doc/{document_id}"<br/>    headers = {"Content-Type": "application/json"}<br/><br/>    data = {<br/>        "text": text,<br/>        "vector": vector<br/>    }<br/><br/>    response = requests.put(url, headers=headers, json=data)<br/>    return response.json()<br/><br/># 示例：索引商品<br/>product_vector = [0.1, 0.2, 0.3, ...]  # 768维向量<br/>index_document(<br/>    "products",<br/>    "1",<br/>    "iPhone 15 智能手机",<br/>    product_vector<br/>)</code>
```

## 🛍️ 商品管理

### 1. 添加商品

```
<code>import numpy as np<br/>from sentence_transformers import SentenceTransformer<br/><br/># 加载嵌入模型<br/>model = SentenceTransformer('all-MiniLM-L6-v2')<br/><br/>def add_product(product_id, name, price, description, category):<br/>    """添加商品到 ES"""<br/>    # 生成文本向量<br/>    text = f"{name} {description} {category}"<br/>    vector = model.encode(text).tolist()<br/><br/>    # 索引文档<br/>    document = {<br/>        "name": name,<br/>        "price": price,<br/>        "description": description,<br/>        "category": category,<br/>        "vector": vector<br/>    }<br/><br/>    url = f"http://localhost:9200/products/_doc/{product_id}"<br/>    headers = {"Content-Type": "application/json"}<br/>    response = requests.put(url, headers=headers, json=document)<br/><br/>    return response.json()<br/><br/># 添加商品示例<br/>add_product(<br/>    "1",<br/>    "iPhone 15",<br/>    5999.99,<br/>    "苹果智能手机，搭载 A16 芯片",<br/>    "电子产品"<br/>)</code>
```

### 2. 删除商品

```
<code>def delete_product(product_id):<br/>    """删除商品"""<br/>    url = f"http://localhost:9200/products/_doc/{product_id}"<br/>    response = requests.delete(url)<br/>    return response.json()<br/><br/># 删除商品示例<br/>delete_product("1")</code>
```

### 3. 批量操作

```
<code>def bulk_index_products(products):<br/>    """批量索引商品"""<br/>    url = "http://localhost:9200/_bulk"<br/>    headers = {"Content-Type": "application/json"}<br/><br/>    bulk_data = []<br/>    for product in products:<br/>        # 生成向量<br/>        text = f"{product['name']} {product['description']} {product['category']}"<br/>        vector = model.encode(text).tolist()<br/><br/>        # 添加索引操作<br/>        bulk_data.append({"index": {"_index": "products", "_id": product['id']}})<br/>        bulk_data.append({<br/>            "name": product['name'],<br/>            "price": product['price'],<br/>            "description": product['description'],<br/>            "category": product['category'],<br/>            "vector": vector<br/>        })<br/><br/>    # 转换为字符串格式<br/>    bulk_payload = "\n".join([json.dumps(item) for item in bulk_data]) + "\n"<br/><br/>    response = requests.post(url, headers=headers, data=bulk_payload)<br/>    return response.json()<br/><br/># 批量添加示例<br/>products = [<br/>    {"id": "1", "name": "iPhone 15", "price": 5999.99, "description": "苹果手机", "category": "电子产品"},<br/>    {"id": "2", "name": "MacBook Pro", "price": 12999, "description": "苹果笔记本", "category": "电子产品"}<br/>]<br/>bulk_index_products(products)</code>
```

## 🔍 向量搜索

### 1. 基本向量搜索

```
<code>def vector_search(query, k=5):<br/>    """向量搜索"""<br/>    # 生成查询向量<br/>    query_vector = model.encode(query).tolist()<br/><br/>    url = "http://localhost:9200/products/_search"<br/>    headers = {"Content-Type": "application/json"}<br/><br/>    search_body = {<br/>        "knn": {<br/>            "field": "vector",<br/>            "query_vector": query_vector,<br/>            "k": k,<br/>            "num_candidates": 100  # 候选数量<br/>        },<br/>        "_source": ["name", "price", "description", "category"]<br/>    }<br/><br/>    response = requests.get(url, headers=headers, json=search_body)<br/>    return response.json()<br/><br/># 搜索示例<br/>results = vector_search("智能手机")<br/>for hit in results['hits']['hits']:<br/>    print(f"商品: {hit['_source']['name']}, 得分: {hit['_score']}")</code>
```

### 2. 混合搜索

```
<code>def hybrid_search(query, filters=None, k=5):<br/>    """混合搜索（向量+关键词）"""<br/>    query_vector = model.encode(query).tolist()<br/><br/>    url = "http://localhost:9200/products/_search"<br/>    headers = {"Content-Type": "application/json"}<br/><br/>    search_body = {<br/>        "query": {<br/>            "bool": {<br/>                "should": [<br/>                    {<br/>                        "knn": {<br/>                            "field": "vector",<br/>                            "query_vector": query_vector,<br/>                            "k": k,<br/>                            "num_candidates": 100<br/>                        }<br/>                    },<br/>                    {<br/>                        "multi_match": {<br/>                            "query": query,<br/>                            "fields": ["name^2", "description", "category"]<br/>                        }<br/>                    }<br/>                ]<br/>            }<br/>        },<br/>        "size": k<br/>    }<br/><br/>    # 添加过滤条件<br/>    if filters:<br/>        search_body['query']['bool']['filter'] = filters<br/><br/>    response = requests.get(url, headers=headers, json=search_body)<br/>    return response.json()<br/><br/># 带价格过滤的搜索<br/>filters = {<br/>    "range": {<br/>        "price": {<br/>            "lte": 6000<br/>        }<br/>    }<br/>}<br/><br/>results = hybrid_search("手机", filters=filters)</code>
```

### 3. 聚合分析

```
<code>def category_aggregation():<br/>    """按分类聚合商品"""<br/>    url = "http://localhost:9200/products/_search"<br/>    headers = {"Content-Type": "application/json"}<br/><br/>    aggregation_body = {<br/>        "size": 0,<br/>        "aggs": {<br/>            "categories": {<br/>                "terms": {<br/>                    "field": "category.keyword"<br/>                },<br/>                "aggs": {<br/>                    "avg_price": {<br/>                        "avg": {<br/>                            "field": "price"<br/>                        }<br/>                    },<br/>                    "count": {<br/>                        "value_count": {<br/>                            "field": "name"<br/>                        }<br/>                    }<br/>                }<br/>            }<br/>        }<br/>    }<br/><br/>    response = requests.get(url, headers=headers, json=aggregation_body)<br/>    return response.json()<br/><br/># 分析结果<br/>agg_results = category_aggregation()<br/>for bucket in agg_results['aggregations']['categories']['buckets']:<br/>    print(f"分类: {bucket['key']}, 数量: {bucket['count']['value']}, 平均价格: {bucket['avg_price']['value']}")</code>
```

## 🏢 用户权限管理

### 1. 安全配置

```
<code># 启用安全功能<br/>docker exec -it es bin/elasticsearch-reset-password -u elastic -i<br/><br/># 创建用户<br/>curl -X POST "http://localhost:9200/_security/user/user1" \<br/>  -H "Content-Type: application/json" \<br/>  -u elastic:password \<br/>  -d '{<br/>    "password": "user1password",<br/>    "roles": ["reader"]<br/>  }'<br/><br/># 创建角色<br/>curl -X POST "http://localhost:9200/_security/role/product_manager" \<br/>  -H "Content-Type: application/json" \<br/>  -u elastic:password \<br/>  -d '{<br/>    "cluster": ["monitor"],<br/>    "indices": [<br/>      {<br/>        "names": ["products"],<br/>        "privileges": ["read", "write", "create_index"]<br/>      }<br/>    ]<br/>  }'</code>
```

### 2. 多租户实现

```
<code>def create_user_index(user_id):<br/>    """为用户创建专属索引"""<br/>    index_name = f"products_{user_id}"<br/><br/>    mapping = {<br/>        "settings": {<br/>            "index": {<br/>                "number_of_shards": 1<br/>            }<br/>        },<br/>        "mappings": {<br/>            "properties": {<br/>                "name": {"type": "text"},<br/>                "price": {"type": "float"},<br/>                "vector": {<br/>                    "type": "dense_vector",<br/>                    "dims": 768,<br/>                    "index": True,<br/>                    "similarity": "cosine"<br/>                }<br/>            }<br/>        }<br/>    }<br/><br/>    url = f"http://localhost:9200/{index_name}"<br/>    headers = {"Content-Type": "application/json"}<br/>    response = requests.put(url, headers=headers, json=mapping, auth=('elastic', 'password'))<br/>    return response.json()<br/><br/># 为用户创建索引<br/>create_user_index("user1")</code>
```

### 3. 访问控制

```
<code>def add_product_to_user_index(user_id, product):<br/>    """向用户索引添加商品"""<br/>    index_name = f"products_{user_id}"<br/>    product_id = product['id']<br/><br/>    # 生成向量<br/>    text = f"{product['name']} {product['description']}"<br/>    vector = model.encode(text).tolist()<br/><br/>    document = product.copy()<br/>    document['vector'] = vector<br/><br/>    url = f"http://localhost:9200/{index_name}/_doc/{product_id}"<br/>    headers = {"Content-Type": "application/json"}<br/>    response = requests.put(url, headers=headers, json=document, auth=('user1', 'user1password'))<br/>    return response.json()</code>
```

## 📊 性能优化

### 1. 向量索引优化

```
<code>def optimize_vector_index(index_name):<br/>    """优化向量索引"""<br/>    url = f"http://localhost:9200/{index_name}/_forcemerge?max_num_segments=1"<br/>    response = requests.post(url)<br/>    return response.json()<br/><br/># 优化索引<br/>optimize_vector_index("products")</code>
```

### 2. 查询性能优化

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |

### 3. 存储优化

```
<code>def update_index_settings(index_name):<br/>    """更新索引设置"""<br/>    url = f"http://localhost:9200/{index_name}/_settings"<br/>    headers = {"Content-Type": "application/json"}<br/><br/>    settings = {<br/>        "index": {<br/>            "queries": {<br/>                "cache": {<br/>                    "size": "10%"<br/>                }<br/>            },<br/>            "refresh_interval": "30s",<br/>            "number_of_replicas": 1<br/>        }<br/>    }<br/><br/>    response = requests.put(url, headers=headers, json=settings)<br/>    return response.json()</code>
```

## 🐛 常见问题

### Q: 向量搜索速度慢？

```
<code># 检查索引状态<br/>response = requests.get("http://localhost:9200/products/_stats")<br/>print(response.json())<br/><br/># 优化查询<br/>search_body = {<br/>    "knn": {<br/>        "field": "vector",<br/>        "query_vector": query_vector,<br/>        "k": 5,<br/>        "num_candidates": 50  # 减少候选数<br/>    }<br/>}</code>
```

### Q: 内存使用过高？

```
<code># 检查内存使用<br/>docker stats es<br/><br/># 调整 JVM 堆大小<br/>docker run -d -p 9200:9200 \<br/>  -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" \<br/>  --name es elasticsearch:8.12.0<br/><br/># 减少向量维度<br/># 使用 384 维替代 768 维</code>
```

### Q: 权限认证失败？

```
<code># 检查用户权限<br/>response = requests.get(<br/>    "http://localhost:9200/_security/user/user1",<br/>    auth=('elastic', 'password')<br/>)<br/>print(response.json())<br/><br/># 测试认证<br/>response = requests.get(<br/>    "http://localhost:9200/products/_search",<br/>    auth=('user1', 'user1password')<br/>)<br/>print(f"状态码: {response.status_code}")</code>
```

## 📚 相关资源

- **官方文档**: [https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html)
- **向量搜索指南**: [https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-approximate-search.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-approximate-search.html)
- **Python 客户端**: [https://elasticsearch-py.readthedocs.io/](https://elasticsearch-py.readthedocs.io/)
- **ELSER 插件**: [https://www.elastic.co/guide/en/elasticsearch/reference/current/elser.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/elser.html)
- **安全配置**: [https://www.elastic.co/guide/en/elasticsearch/reference/current/security.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/security.html)