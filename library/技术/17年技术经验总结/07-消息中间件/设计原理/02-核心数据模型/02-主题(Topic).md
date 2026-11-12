# 主题（Topic）

## 主题的定位：发布-订阅模式的核心抽象

> 主题（Topic）是发布-订阅（Pub/Sub）模式的核心抽象。

主题（Topic）是发布-订阅（Pub/Sub）模式的核心抽象。生产者将消息发布到主题，**所有订阅该主题的消费者都会收到消息**。主题通过标签（Tag）或主题层级结构组织消息，实现多维度分类和灵活路由。

## 数据库设计：topic_info / topic_tag / topic_message_index

### 表结构：topic_info（主题元数据表）

```sql
CREATE TABLE topic_info (
    topic_id         VARCHAR(64)         NOT NULL COMMENT '主题唯一标识(UUID)',
    topic_name       VARCHAR(255)        NOT NULL COMMENT '主题名称',
    vhost            VARCHAR(128)        NOT NULL DEFAULT '/'  COMMENT '虚拟主机',
    
    -- 主题配置
    topic_type       ENUM('fanout', ' hierarchical', 'tagged') NOT NULL DEFAULT 'tagged' COMMENT '主题类型',
    durable          BOOLEAN             NOT NULL DEFAULT TRUE COMMENT '是否持久化',
    auto_delete      BOOLEAN             NOT NULL DEFAULT FALSE COMMENT '无订阅者时是否自动删除',
    message_ttl      BIGINT             DEFAULT NULL COMMENT '消息默认TTL(毫秒)',
    max_msg_size     BIGINT             DEFAULT 1048576 COMMENT '单条消息最大字节数(默认1MB)',
    
    -- 存储配置
    retention_days   INT                DEFAULT 7 COMMENT '消息保留天数',
    compaction        BOOLEAN            NOT NULL DEFAULT FALSE COMMENT '是否启用日志压缩',
    
    -- 统计
    subscription_count  INT               NOT NULL DEFAULT 0 COMMENT '活跃订阅数',
    message_count       BIGINT           NOT NULL DEFAULT 0 COMMENT '当前消息总数',
    byte_count          BIGINT           NOT NULL DEFAULT 0 COMMENT '当前总字节数',
    
    -- 审计字段
    created_at        DATETIME(3)         NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at        DATETIME(3)         NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    deleted_at        DATETIME(3)         DEFAULT NULL,
    
    PRIMARY KEY (topic_id),
    UNIQUE KEY uk_vhost_topic_name (vhost, topic_name),
    INDEX idx_topic_type (topic_type),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '主题元数据表';
```

### 表结构：topic_tag（主题标签表）

```sql
CREATE TABLE topic_tag (
    tag_id         VARCHAR(64)       NOT NULL COMMENT '标签ID',
    topic_id       VARCHAR(64)      NOT NULL COMMENT '所属主题ID',
    tag_name       VARCHAR(128)     NOT NULL COMMENT '标签名称',
    tag_type       ENUM('category', 'attribute', 'custom') DEFAULT 'custom' COMMENT '标签类型',
    parent_tag_id   VARCHAR(64)      DEFAULT NULL COMMENT '父标签ID(层级结构)',
    color           VARCHAR(7)       DEFAULT '#1890FF' COMMENT '标签颜色(HEX)',
    description     VARCHAR(512)     DEFAULT NULL COMMENT '标签描述',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (tag_id),
    UNIQUE KEY uk_topic_tag (topic_id, tag_name),
    INDEX idx_parent (parent_tag_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '主题标签表';
```

### 表结构：topic_message_index（主题消息索引表）

```sql
CREATE TABLE topic_message_index (
    index_id        BIGINT            NOT NULL AUTO_INCREMENT COMMENT '索引ID',
    topic_id        VARCHAR(64)       NOT NULL COMMENT '主题ID',
    message_id      VARCHAR(64)       NOT NULL COMMENT '消息ID',
    sequence_num    BIGINT            NOT NULL COMMENT '消息序列号',
    
    -- 主题层级路由
    topic_path      VARCHAR(1024)     NOT NULL COMMENT '主题路径(如 order.created.pay)',
    topic_levels     JSON             DEFAULT NULL COMMENT '主题层级数组',
    
    -- 消息属性
    message_size    INT               NOT NULL COMMENT '消息大小(字节)',
    timestamp       DATETIME(3)       NOT NULL COMMENT '发布时间戳',
    producer_id     VARCHAR(64)       NOT NULL COMMENT '生产者ID',
    
    -- 索引
    INDEX idx_topic_sequence (topic_id, sequence_num),
    INDEX idx_topic_path (topic_path(255)),
    INDEX idx_timestamp (timestamp),
    INDEX idx_producer (producer_id),
    
    PRIMARY KEY (index_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '主题消息索引表(用于快速查询和回溯)';
```

---

## 三种主题类型：Fanout / Hierarchical / Tagged

### 1. Fanout Topic（广播主题）

无条件将消息投递给所有订阅者，不做过滤。

```json
{
  "topic_type": "fanout",
  "topic_name": "notifications.all"
}
```

### 2. Hierarchical Topic（层级主题）

基于点分隔的层级结构（如 `order.created`、`order.cancelled`）。

**路由规则：**
- `order.*` → 匹配 `order.created`、`order.cancelled`
- `order.#` → 匹配 `order.created.pay`、`order.created.refund`
- `order.*.pay` → 匹配 `order.created.pay`

*图：层级主题通配符匹配示例（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 200" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <text x="360" y="24" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">层级主题：通配符匹配规则</text>
  <rect x="40" y="45" width="200" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="140" y="68" text-anchor="middle" font-size="14" fill="#1e293b">order.*</text>
  <line x1="240" y1="63" x2="320" y2="63" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="330" y="45" width="350" height="36" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="505" y="68" text-anchor="middle" font-size="13" fill="#1e293b">order.created、order.cancelled</text>
  <rect x="40" y="95" width="200" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="140" y="118" text-anchor="middle" font-size="14" fill="#1e293b">order.#</text>
  <line x1="240" y1="113" x2="320" y2="113" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="330" y="95" width="350" height="36" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="505" y="118" text-anchor="middle" font-size="13" fill="#1e293b">order.created.pay、order.created.refund</text>
  <rect x="40" y="145" width="200" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="140" y="168" text-anchor="middle" font-size="14" fill="#1e293b">order.*.pay</text>
  <line x1="240" y1="163" x2="320" y2="163" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="330" y="145" width="350" height="36" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="505" y="168" text-anchor="middle" font-size="13" fill="#1e293b">order.created.pay</text>
</svg>

### 3. Tagged Topic（标签主题）

通过多个维度标签过滤消息，更灵活。

```json
{
  "topic_type": "tagged",
  "tags": ["order", "created", "vip"]
}
```

消费者通过标签组合订阅：
```json
{
  "required_tags": ["order", "vip"],
  "optional_tags": ["created", "cancelled"]
}
```

---

## 主题与队列的对比

| 特性 | Topic（主题）| Queue（队列）|
|------|-------------|--------------|
| 消息模式 | 发布-订阅 | 点对点 |
| 消费者 | 多消费者共享 | 消息仅被一个消费者消费 |
| 消息共享 | 同一消息可被多个消费者处理 | 同一消息仅被一个消费者处理 |
| 消费位置 | 可共享消费位置（Stream）| 每个消费者独立消费位置 |
| 适用场景 | 广播通知、日志分发 | 任务分发、异步处理 |

---

## 主题的 REST API

### 创建主题

```json
POST /api/v1/topics
{
  "topic_name": "order.events",
  "vhost": "/",
  "topic_type": "hierarchical",
  "durable": true,
  "retention_days": 30,
  "max_msg_size": 2097152
}
```

### 订阅主题

```json
POST /api/v1/topics/{topic_id}/subscriptions
{
  "subscription_name": "analytics-consumer",
  "consumer_group_id": "analytics-group",
  "start_policy": "latest",
  "filter_tags": ["order.created", "order.cancelled"]
}
```

### 查询主题列表

```json
GET /api/v1/topics?vhost=/&page=1&page_size=20
```

### 获取主题统计

```json
GET /api/v1/topics/{topic_id}/stats
```

---

*文档版本：v1.0 | 更新日期：2026-03-29*
