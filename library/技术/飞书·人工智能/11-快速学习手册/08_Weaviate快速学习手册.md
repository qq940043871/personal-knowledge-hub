## 📋 概述

Weaviate 是一个开源的向量数据库，支持语义搜索、多模态数据和可扩展架构，特别适合构建智能应用。

**核心特性：**

- 向量搜索 + 传统搜索
- 图数据库能力
- 自动 schema 检测
- 多租户支持
- 企业级安全

## 🏗️ 架构设计

```
<code>┌─────────────────────────────────────────────────────┐<br/>│                 Weaviate 架构                         │<br/>├─────────────────────────────────────────────────────┤<br/>│  客户端 → API 层 → 认证层 → 向量索引 → 存储层         │<br/>│                                                     │<br/>│  租户 1 → 类 1 → 对象 1,2,3                          │<br/>│  租户 2 → 类 2 → 对象 4,5,6                          │<br/>└─────────────────────────────────────────────────────┘</code>
```

## 🚀 快速开始

### 1. 安装部署

```
<code># Docker 部署<br/> docker run -d -p 8080:8080 \<br/>  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=false \<br/>  -e AUTHENTICATION_APIKEY_ENABLED=true \<br/>  -e AUTHENTICATION_APIKEY_ALLOWED_KEYS=your-api-key \<br/>  -e AUTHENTICATION_APIKEY_USERS=admin \<br/>  semitechnologies/weaviate:1.24.2<br/><br/># 或使用 docker-compose<br/>curl -o docker-compose.yml https://raw.githubusercontent.com/weaviate/weaviate/main/docker-compose.yml<br/>docker-compose up -d</code>
```

### 2. 基本操作

```
<code># 健康检查<br/>curl http://localhost:8080/v1/meta<br/><br/># 创建 schema<br/>curl -X POST http://localhost:8080/v1/schema \<br/>  -H "Content-Type: application/json" \<br/>  -H "Authorization: Bearer your-api-key" \<br/>  -d '{<br/>    "classes": [{<br/>      "class": "Product",<br/>      "description": "商品信息",<br/>      "properties": [<br/>        {"name": "name", "dataType": ["string"]},<br/>        {"name": "price", "dataType": ["number"]},<br/>        {"name": "description", "dataType": ["text"]}<br/>      ]<br/>    }]<br/>  }'</code>
```

## 🔐 用户权限管理

### 1. 认证配置

```
<code># docker-compose.yml 配置<br/>version: '3.4'<br/>services:<br/>  weaviate:<br/>    image: semitechnologies/weaviate:1.24.2<br/>    ports:<br/>      - "8080:8080"<br/>    environment:<br/>      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "false"<br/>      AUTHENTICATION_APIKEY_ENABLED: "true"<br/>      AUTHENTICATION_APIKEY_ALLOWED_KEYS: "user1-key,user2-key,admin-key"<br/>      AUTHENTICATION_APIKEY_USERS: "user1,user2,admin"<br/>      AUTHORIZATION_ADMINLIST_ENABLED: "true"<br/>      AUTHORIZATION_ADMINLIST_USERS: "admin"</code>
```

### 2. 角色与权限

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |

### 3. 访问控制实现

```
<code>import weaviate<br/><br/># 管理员客户端<br/>client_admin = weaviate.Client(<br/>    url="http://localhost:8080",<br/>    auth_client_secret=weaviate.AuthApiKey(api_key="admin-key")<br/>)<br/><br/># 用户客户端<br/>client_user1 = weaviate.Client(<br/>    url="http://localhost:8080",<br/>    auth_client_secret=weaviate.AuthApiKey(api_key="user1-key")<br/>)<br/><br/># 检查权限<br/>try:<br/>    # 只有管理员可以创建 schema<br/>    client_admin.schema.create_class({<br/>        "class": "Product",<br/>        "properties": [<br/>            {"name": "name", "dataType": ["string"]}<br/>        ]<br/>    })<br/>    print("管理员权限正常")<br/>except Exception as e:<br/>    print(f"权限错误: {e}")</code>
```

## 🏢 多租户管理

### 1. 命名空间配置

```
<code># 创建用户专属命名空间<br/>def create_user_namespace(user_id):<br/>    """为每个用户创建独立的命名空间"""<br/>    return f"user_{user_id}_namespace"<br/><br/># 为用户1创建命名空间<br/>user1_namespace = create_user_namespace("user1")<br/>user2_namespace = create_user_namespace("user2")</code>
```

### 2. 多知识库实现

```
<code>def create_user_knowledge_base(user_id, client):<br/>    """为用户创建专属知识库"""<br/>    namespace = create_user_namespace(user_id)<br/><br/>    # 创建用户专属的商品类<br/>    class_name = f"Product_{user_id}"<br/><br/>    schema = {<br/>        "class": class_name,<br/>        "description": f"用户 {user_id} 的商品知识库",<br/>        "properties": [<br/>            {"name": "name", "dataType": ["string"]},<br/>            {"name": "price", "dataType": ["number"]},<br/>            {"name": "description", "dataType": ["text"]},<br/>            {"name": "category", "dataType": ["string"]}<br/>        ]<br/>    }<br/><br/>    try:<br/>        client.schema.create_class(schema)<br/>        return class_name<br/>    except Exception as e:<br/>        print(f"创建知识库失败: {e}")<br/>        return None<br/><br/># 为不同用户创建知识库<br/>user1_class = create_user_knowledge_base("user1", client_admin)<br/>user2_class = create_user_knowledge_base("user2", client_admin)</code>
```

### 3. 数据隔离

```
<code>def add_product_to_user_kb(user_id, product_data, client):<br/>    """向用户知识库添加商品"""<br/>    class_name = f"Product_{user_id}"<br/><br/>    # 生成 UUID（可选）<br/>    import uuid<br/>    product_id = str(uuid.uuid4())<br/><br/>    data_object = {<br/>        "id": product_id,<br/>        "class": class_name,<br/>        "properties": product_data<br/>    }<br/><br/>    try:<br/>        client.data_object.create(<br/>            data_object=data_object,<br/>            class_name=class_name<br/>        )<br/>        return product_id<br/>    except Exception as e:<br/>        print(f"添加商品失败: {e}")<br/>        return None</code>
```

## 🛍️ 商品信息管理

### 1. 添加商品

```
<code>def add_product(user_id, name, price, description, category, client):<br/>    """添加商品到用户知识库"""<br/>    product_data = {<br/>        "name": name,<br/>        "price": price,<br/>        "description": description,<br/>        "category": category<br/>    }<br/><br/>    return add_product_to_user_kb(user_id, product_data, client)<br/><br/># 示例：为用户1添加商品<br/>product_id = add_product(<br/>    user_id="user1",<br/>    name="iPhone 15",<br/>    price=5999.99,<br/>    description="苹果智能手机",<br/>    category="电子产品",<br/>    client=client_user1<br/>)<br/>print(f"商品添加成功，ID: {product_id}")</code>
```

### 2. 删除商品

```
<code>def delete_product(user_id, product_id, client):<br/>    """从用户知识库删除商品"""<br/>    class_name = f"Product_{user_id}"<br/><br/>    try:<br/>        client.data_object.delete(<br/>            uuid=product_id,<br/>            class_name=class_name<br/>        )<br/>        return True<br/>    except Exception as e:<br/>        print(f"删除商品失败: {e}")<br/>        return False<br/><br/># 示例：删除商品<br/>success = delete_product(<br/>    user_id="user1",<br/>    product_id=product_id,<br/>    client=client_user1<br/>)<br/>if success:<br/>    print("商品删除成功")</code>
```

### 3. 批量操作

```
<code>def batch_add_products(user_id, products, client):<br/>    """批量添加商品"""<br/>    class_name = f"Product_{user_id}"<br/><br/>    # 开始批量操作<br/>    with client.batch as batch:<br/>        batch.batch_size = 10  # 每批处理10个<br/><br/>        for product in products:<br/>            product_id = str(uuid.uuid4())<br/>            batch.add_data_object(<br/>                data_object=product,<br/>                class_name=class_name,<br/>                uuid=product_id<br/>            )<br/><br/>    return True<br/><br/># 批量添加示例<br/>products = [<br/>    {"name": "MacBook Pro", "price": 12999, "category": "电子产品"},<br/>    {"name": "AirPods Pro", "price": 1999, "category": "配件"},<br/>    {"name": "iPad Air", "price": 4799, "category": "平板电脑"}<br/>]<br/><br/>batch_add_products("user1", products, client_user1)</code>
```

## 🔍 语义搜索

### 1. 向量搜索

```
<code>def search_products(user_id, query, client, limit=5):<br/>    """搜索用户知识库中的商品"""<br/>    class_name = f"Product_{user_id}"<br/><br/>    response = client.query.get(<br/>        class_name,<br/>        ["name", "price", "description", "category"]<br/>    ).with_near_text(<br/>        {<br/>            "concepts": [query],<br/>            "certainty": 0.7  # 相似度阈值<br/>        }<br/>    ).with_limit(limit).do()<br/><br/>    return response.get("data", {}).get("Get", {}).get(class_name, [])<br/><br/># 搜索示例<br/>results = search_products(<br/>    user_id="user1",<br/>    query="智能手机",<br/>    client=client_user1<br/>)<br/><br/>for product in results:<br/>    print(f"商品: {product['name']}, 价格: {product['price']}")</code>
```

### 2. 混合搜索

```
<code>def hybrid_search(user_id, query, filters=None, client=None):<br/>    """混合搜索（向量+关键词）"""<br/>    class_name = f"Product_{user_id}"<br/><br/>    response = client.query.get(<br/>        class_name,<br/>        ["name", "price", "description", "category"]<br/>    ).with_hybrid(<br/>        query=query,<br/>        properties=["name^2", "description"],  # 字段权重<br/>        alpha=0.7  # 向量搜索权重<br/>    )<br/><br/>    # 添加过滤条件<br/>    if filters:<br/>        response = response.with_where(filters)<br/><br/>    return response.with_limit(5).do()<br/><br/># 带过滤条件的搜索<br/>filters = {<br/>    "path": ["price"],<br/>    "operator": "GreaterThan",<br/>    "valueNumber": 5000<br/>}<br/><br/>results = hybrid_search(<br/>    user_id="user1",<br/>    query="手机",<br/>    filters=filters,<br/>    client=client_user1<br/>)</code>
```

## 📊 数据管理

### 1. 数据导出

```
<code>def export_user_products(user_id, client):<br/>    """导出用户商品数据"""<br/>    class_name = f"Product_{user_id}"<br/><br/>    # 分页获取所有数据<br/>    results = []<br/>    after = None<br/><br/>    while True:<br/>        query = client.query.get(<br/>            class_name,<br/>            ["name", "price", "description", "category"]<br/>        )<br/><br/>        if after:<br/>            query = query.with_after(after)<br/><br/>        response = query.with_limit(100).do()<br/>        products = response.get("data", {}).get("Get", {}).get(class_name, [])<br/><br/>        if not products:<br/>            break<br/><br/>        results.extend(products)<br/>        after = products[-1].get("_additional", {}).get("id")<br/><br/>    return results<br/><br/># 导出示例<br/>user1_products = export_user_products("user1", client_user1)<br/>print(f"导出了 {len(user1_products)} 个商品")</code>
```

### 2. 数据导入

```
<code>def import_products(user_id, products, client):<br/>    """导入商品数据"""<br/>    class_name = f"Product_{user_id}"<br/><br/>    with client.batch as batch:<br/>        batch.batch_size = 50<br/><br/>        for product in products:<br/>            product_id = product.get("id", str(uuid.uuid4()))<br/>            batch.add_data_object(<br/>                data_object=product,<br/>                class_name=class_name,<br/>                uuid=product_id<br/>            )<br/><br/>    return True</code>
```

## 🔧 高级配置

### 1. 向量索引配置

```
<code>def configure_vector_index(client):<br/>    """配置向量索引"""<br/>    # 注意：这需要在创建类之前配置<br/>    client.schema.create_class({<br/>        "class": "Product",<br/>        "vectorIndexType": "hnsw",<br/>        "vectorIndexConfig": {<br/>            "skip": False,<br/>            "cleanupIntervalSeconds": 60,<br/>            "maxConnections": 64,<br/>            "efConstruction": 128,<br/>            "ef": 64,<br/>            "dynamicEfMin": 100,<br/>            "dynamicEfMax": 500,<br/>            "dynamicEfFactor": 8,<br/>            "vectorCacheMaxObjects": 1000000,<br/>            "flatSearchCutoff": 40000,<br/>            "distance": "cosine"<br/>        }<br/>    })</code>
```

### 2. 备份与恢复

```
<code># 创建备份<br/>curl -X POST http://localhost:8080/v1/backups/my-backup \<br/>  -H "Content-Type: application/json" \<br/>  -H "Authorization: Bearer admin-key" \<br/>  -d '{"include": ["Product_user1", "Product_user2"]}'<br/><br/># 恢复备份<br/>curl -X POST http://localhost:8080/v1/backups/my-backup/restore \<br/>  -H "Content-Type: application/json" \<br/>  -H "Authorization: Bearer admin-key"</code>
```

## 🐛 常见问题

### Q: 权限验证失败？

```
<code># 检查 API Key<br/>print(f"API Key: {api_key}")<br/><br/># 检查认证配置<br/>response = requests.get(<br/>    "http://localhost:8080/v1/meta",<br/>    headers={"Authorization": f"Bearer {api_key}"}<br/>)<br/>print(f"状态码: {response.status_code}")<br/>print(f"响应: {response.json()}")</code>
```

### Q: 商品添加失败？

```
<code># 检查 schema 是否存在<br/>response = client.schema.get()<br/>classes = response.get("classes", [])<br/>class_names = [cls["class"] for cls in classes]<br/>print(f"存在的类: {class_names}")<br/><br/># 检查权限<br/>try:<br/>    client.data_object.create(<br/>        data_object={"name": "Test"},<br/>        class_name="Product_user1"<br/>    )<br/>except Exception as e:<br/>    print(f"错误: {e}")</code>
```

### Q: 搜索结果不准确？

```
<code># 调整相似度阈值<br/>response = client.query.get(<br/>    "Product_user1",<br/>    ["name", "price"]<br/>).with_near_text(<br/>    {<br/>        "concepts": ["手机"],<br/>        "certainty": 0.6  # 降低阈值<br/>    }<br/>).do()<br/><br/># 检查向量索引状态<br/>response = requests.get(<br/>    "http://localhost:8080/v1/nodes",<br/>    headers={"Authorization": f"Bearer {api_key}"}<br/>)<br/>print(f"节点状态: {response.json()}")</code>
```

## 📚 相关资源

- **官方文档**: [https://weaviate.io/developers/weaviate](https://weaviate.io/developers/weaviate)
- **GitHub**: [https://github.com/weaviate/weaviate](https://github.com/weaviate/weaviate)
- **Python 客户端**: [https://weaviate.io/developers/weaviate/client-libraries/python](https://weaviate.io/developers/weaviate/client-libraries/python)
- **认证配置**: [https://weaviate.io/developers/weaviate/configuration/authentication](https://weaviate.io/developers/weaviate/configuration/authentication)
- **多租户**: [https://weaviate.io/developers/weaviate/configuration/multi-tenancy](https://weaviate.io/developers/weaviate/configuration/multi-tenancy)