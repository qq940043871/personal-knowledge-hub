# 4.1 交换机 (Exchange)

## 概述

交换机（Exchange）是消息路由的核心枢纽。生产者将消息发送到交换机，交换机根据路由规则将消息转发到一个或多个队列。交换机本身不存储消息。

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 440" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="380" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">交换机与消息路由</text>
  <rect x="40" y="80" width="130" height="50" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="105" y="110" text-anchor="middle" font-size="13" fill="#1e293b">生产者</text>
  <line x1="172" y1="105" x2="244" y2="105" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="208" y="96" text-anchor="middle" font-size="12" fill="#475569">发布消息</text>
  <rect x="250" y="80" width="160" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="330" y="110" text-anchor="middle" font-size="13" fill="#1e293b">Exchange</text>
  <line x1="412" y1="105" x2="584" y2="105" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="497" y="96" text-anchor="middle" font-size="12" fill="#475569">Binding路由</text>
  <rect x="590" y="80" width="130" height="50" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="655" y="110" text-anchor="middle" font-size="13" fill="#1e293b">Queue队列</text>
  <path d="M330,130 V160 H120 V186" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M330,130 V186" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M330,130 V160 H480 V186" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M330,130 V160 H660 V186" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="40" y="190" width="160" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="120" y="216" text-anchor="middle" font-size="13" fill="#1e293b">direct 直连</text>
  <text x="120" y="238" text-anchor="middle" font-size="12" fill="#475569">精确匹配路由键</text>
  <rect x="220" y="190" width="160" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="300" y="216" text-anchor="middle" font-size="13" fill="#1e293b">fanout 广播</text>
  <text x="300" y="238" text-anchor="middle" font-size="12" fill="#475569">复制到所有队列</text>
  <rect x="400" y="190" width="160" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="480" y="216" text-anchor="middle" font-size="13" fill="#1e293b">topic 主题</text>
  <text x="480" y="238" text-anchor="middle" font-size="12" fill="#475569">通配符模式匹配</text>
  <rect x="580" y="190" width="160" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="660" y="216" text-anchor="middle" font-size="13" fill="#1e293b">headers 头部</text>
  <text x="660" y="238" text-anchor="middle" font-size="12" fill="#475569">按消息头匹配</text>
  <line x1="120" y1="254" x2="120" y2="292" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="300" y1="254" x2="300" y2="292" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="480" y1="254" x2="480" y2="292" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="660" y1="254" x2="660" y2="292" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="40" y="296" width="680" height="40" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="380" y="321" text-anchor="middle" font-size="13" fill="#1e293b">队列（一个或多个）</text>
  <text x="380" y="382" text-anchor="middle" font-size="13" fill="#475569">交换机本身不存储消息</text>
  <text x="380" y="408" text-anchor="middle" font-size="13" fill="#475569">路由失败时可转发至备用交换机</text>
</svg>

*图：交换机类型与消息路由示意（依正文整理）*

## 数据库设计

### 表结构：exchange_info（交换机元数据表）

```sql
CREATE TABLE exchange_info (
    exchange_id        VARCHAR(64)       NOT NULL COMMENT '交换机ID(UUID)',
    exchange_name      VARCHAR(255)      NOT NULL COMMENT '交换机名称',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/' COMMENT '虚拟主机',
    
    -- 交换机类型
    exchange_type      ENUM('direct', 'fanout', 'topic', 'headers') NOT NULL COMMENT '交换机类型',
    durable            BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否持久化',
    auto_delete        BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '无绑定关系时自动删除',
    internal           BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否为内部交换机(不可直接接收消息)',
    
    -- 配置
    arguments          JSON             DEFAULT NULL COMMENT '扩展参数',
    alternate_exchange VARCHAR(255)      DEFAULT NULL COMMENT '备用交换机(路由失败时转发)',
    
    -- 统计
    binding_count      INT               NOT NULL DEFAULT 0 COMMENT '绑定数量',
    message_in_count   BIGINT            NOT NULL DEFAULT 0 COMMENT '累计接收消息数',
    message_out_count  BIGINT            NOT NULL DEFAULT 0 COMMENT '累计转发消息数',
    message_drop_count BIGINT            NOT NULL DEFAULT 0 COMMENT '累计丢弃消息数',
    
    -- 状态
    status             ENUM('running', 'stopped', 'deleted') DEFAULT 'running',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    deleted_at         DATETIME(3)       DEFAULT NULL,
    
    PRIMARY KEY (exchange_id),
    UNIQUE KEY uk_vhost_name (vhost, exchange_name),
    INDEX idx_type (exchange_type),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '交换机元数据表';
```

### 表结构：exchange_stats（交换机统计表）

```sql
CREATE TABLE exchange_stats (
    stat_id            BIGINT            NOT NULL AUTO_INCREMENT,
    exchange_id        VARCHAR(64)       NOT NULL COMMENT '交换机ID',
    stat_time          DATETIME(3)       NOT NULL COMMENT '统计时间',
    
    -- 吞吐量
    messages_in        BIGINT            NOT NULL DEFAULT 0 COMMENT '入站消息数',
    messages_out       BIGINT            NOT NULL DEFAULT 0 COMMENT '出站消息数',
    messages_dropped   BIGINT            NOT NULL DEFAULT 0 COMMENT '丢弃消息数',
    rate_in            DECIMAL(10,2)    DEFAULT 0 COMMENT '入站速率(msg/s)',
    rate_out           DECIMAL(10,2)    DEFAULT 0 COMMENT '出站速率(msg/s)',
    
    -- 绑定
    active_bindings    INT               NOT NULL DEFAULT 0 COMMENT '活跃绑定数',
    
    PRIMARY KEY (stat_id),
    UNIQUE KEY uk_exchange_time (exchange_id, stat_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '交换机运行时统计表';
```

---

## 交换机类型与路由规则

### Direct（直连交换机）

精确匹配 Routing Key 与 Binding Key。

```
Binding: queue-A ← key: "order.created"
Binding: queue-B ← key: "order.cancelled"

消息 Routing Key = "order.created"  → queue-A
消息 Routing Key = "order.cancelled" → queue-B
消息 Routing Key = "order.updated"  → 无匹配，丢弃
```

### Fanout（广播交换机）

忽略 Routing Key，投递到所有绑定队列。

```
Binding: queue-A, queue-B, queue-C

任何消息 → queue-A, queue-B, queue-C
```

### Topic（主题交换机）

通配符匹配 Routing Key。

```
Binding: queue-A ← pattern: "order.*.pay"      (* 匹配一个词)
Binding: queue-B ← pattern: "order.#"           (# 匹配零或多个词)
Binding: queue-C ← pattern: "*.created"          (* 匹配一个词)

"order.created.pay"     → queue-A, queue-B
"order.created"          → queue-C, queue-B
"user.created"           → queue-C
"user.created.info"      → 无匹配
```

### Headers（首部交换机）

根据消息头匹配（不使用 Routing Key）。

```json
{
  "binding_args": {
    "x-match": "all",
    "type": "notification",
    "priority": "high"
  }
}
```

---

## 备用交换机（Alternate Exchange）

当消息无法路由到任何队列时，转发到备用交换机。

```
消息 ──▶ 主交换机 ──无匹配──▶ 备用交换机 ──▶ 未路由队列
          │ 有匹配
          ▼
      目标队列
```

配置示例：
```json
{
  "exchange_name": "main.exchange",
  "alternate_exchange": "unrouted.exchange"
}
```

---

## API 操作

### 创建交换机

```json
POST /api/v1/exchanges
{
  "exchange_name": "order.exchange",
  "vhost": "/",
  "exchange_type": "topic",
  "durable": true,
  "alternate_exchange": "dlx.exchange"
}
```

### 列出交换机

```json
GET /api/v1/exchanges?vhost=/&type=topic
```

---

*文档版本：v1.0 | 更新日期：2026-03-29*
