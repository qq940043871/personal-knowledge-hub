# 5.4 消费确认 (ACK)

## 什么是消费确认（ACK）

消费确认（Acknowledgment, ACK）是保证消息可靠消费的核心机制。消费者成功处理消息后发送 ACK，Broker 收到 ACK 后才删除该消息。如果消费者处理失败，可以发送 NACK 或 Reject，消息将被重新投递或进入死信队列。

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 450" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="360" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">消息确认与重投流程</text>
  <rect x="60" y="60" width="140" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="130" y="88" text-anchor="middle" font-size="13" fill="#1e293b">Broker</text>
  <rect x="520" y="60" width="140" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="590" y="88" text-anchor="middle" font-size="13" fill="#1e293b">消费者</text>
  <line x1="202" y1="83" x2="516" y2="83" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="359" y="74" text-anchor="middle" font-size="12" fill="#475569">投递消息 Deliver</text>
  <line x1="590" y1="106" x2="590" y2="134" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="490" y="140" width="200" height="50" rx="24" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="590" y="170" text-anchor="middle" font-size="13" fill="#1e293b">处理结果？</text>
  <line x1="488" y1="165" x2="400" y2="165" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="444" y="156" text-anchor="middle" font-size="12" fill="#475569">ACK</text>
  <rect x="236" y="140" width="160" height="50" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="316" y="160" text-anchor="middle" font-size="13" fill="#1e293b">ACK 确认成功</text>
  <text x="316" y="180" text-anchor="middle" font-size="12" fill="#475569">Broker删除消息</text>
  <line x1="590" y1="192" x2="590" y2="220" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="604" y="210" text-anchor="start" font-size="12" fill="#475569">NACK/Reject</text>
  <rect x="490" y="226" width="200" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="590" y="248" text-anchor="middle" font-size="13" fill="#1e293b">重新入队</text>
  <text x="590" y="268" text-anchor="middle" font-size="12" fill="#475569">再次投递消费</text>
  <path d="M490,254 H130 V112" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="300" y="245" text-anchor="middle" font-size="12" fill="#475569">redelivered=true</text>
  <line x1="590" y1="282" x2="590" y2="326" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="604" y="308" text-anchor="start" font-size="12" fill="#475569">requeue=false</text>
  <rect x="490" y="330" width="200" height="50" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="590" y="360" text-anchor="middle" font-size="13" fill="#1e293b">进入死信队列 DLX</text>
  <text x="360" y="424" text-anchor="middle" font-size="13" fill="#475569">Broker收到ACK后才删除消息，失败则重投或进入死信队列</text>
</svg>

*图：消息确认与重投流程示意（依正文整理）*

## 确认类型

| 类型 | 说明 | 消息处理 |
|------|------|---------|
| ACK | 确认成功 | Broker 删除消息 |
| NACK | 否定确认 | 消息重新入队 |
| Reject | 拒绝 | 重新入队或进入 DLX |

## 数据库设计

### 表结构：delivery_record（投递记录表）

```sql
CREATE TABLE delivery_record (
    delivery_id        VARCHAR(64)       NOT NULL COMMENT '投递记录ID',
    message_id         VARCHAR(64)       NOT NULL COMMENT '消息ID',
    consumer_id        VARCHAR(64)       NOT NULL COMMENT '消费者ID',
    queue_id           VARCHAR(64)       NOT NULL COMMENT '队列ID',
    
    -- 投递信息
    delivery_tag       BIGINT            NOT NULL COMMENT '投递标签(信道内唯一)',
    delivery_count     INT               NOT NULL DEFAULT 1 COMMENT '投递次数',
    redelivered        BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否重投',
    
    -- 时间
    delivered_at       DATETIME(3)       NOT NULL COMMENT '投递时间',
    ack_timeout_ms     INT               NOT NULL DEFAULT 30000 COMMENT '确认超时(毫秒)',
    ack_deadline       DATETIME(3)       NOT NULL COMMENT '确认截止时间',
    
    -- 确认结果
    ack_status         ENUM('pending', 'acked', 'nacked', 'rejected', 'expired') DEFAULT 'pending',
    acked_at           DATETIME(3)       DEFAULT NULL COMMENT '确认时间',
    ack_latency_ms     DECIMAL(10,2)     DEFAULT NULL COMMENT '确认耗时(毫秒)',
    
    -- NACK/Reject 详情
    nack_reason        VARCHAR(512)      DEFAULT NULL COMMENT 'NACK原因',
    requeue            BOOLEAN           DEFAULT TRUE COMMENT '是否重新入队',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (delivery_id),
    UNIQUE KEY uk_consumer_delivery_tag (consumer_id, delivery_tag),
    INDEX idx_message (message_id),
    INDEX idx_queue (queue_id),
    INDEX idx_ack_status (ack_status),
    INDEX idx_ack_deadline (ack_status, ack_deadline)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消息投递记录表';
```

---

## 确认流程

### 正常确认

```
Broker ──▶ Deliver(msg) ──▶ Consumer
Consumer ──▶ Process ──▶ ACK ──▶ Broker
Broker ──▶ 删除消息
```

### 处理失败

```
Broker ──▶ Deliver(msg) ──▶ Consumer
Consumer ──▶ Process Failed ──▶ NACK(requeue=true) ──▶ Broker
Broker ──▶ 消息重新入队
```

### 确认超时

```
Broker ──▶ Deliver(msg, deadline=30s) ──▶ Consumer
   │         │
   │    30秒无ACK
   │         │
   ▼         ▼
Broker 收回消息 → 重新投递(或进入DLX)
```

---

## 确认超时扫描

```sql
-- 查找超时未确认的消息
SELECT * FROM delivery_record
WHERE ack_status = 'pending'
  AND ack_deadline < NOW()
ORDER BY delivered_at ASC
LIMIT 100;
```

---

*文档版本：v1.0 | 更新日期：2026-03-29*
