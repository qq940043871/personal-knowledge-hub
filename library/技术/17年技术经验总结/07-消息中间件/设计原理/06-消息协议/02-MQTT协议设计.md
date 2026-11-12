# MQTT 协议设计

## MQTT：面向物联网的轻量级协议

MQTT（Message Queuing Telemetry Transport）是**面向物联网和移动端的轻量级消息协议**。支持发布/订阅模式和 QoS 等级控制，适合低带宽和高延迟网络环境。

## 数据库设计

### 表结构：mqtt_session（MQTT会话表）

```sql
CREATE TABLE mqtt_session (
    client_id          VARCHAR(256)      NOT NULL COMMENT 'MQTT客户端ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    
    -- 会话配置
    clean_start        BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否清除会话',
    session_expiry     INT               DEFAULT 0 COMMENT '会话过期时间(秒,0=不过期)',
    
    -- QoS 配置
    default_qos        TINYINT           NOT NULL DEFAULT 0 COMMENT '默认QoS等级(0/1/2)',
    retain_available   BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否支持保留消息',
    
    -- 状态
    connected          BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否在线',
    keepalive          INT               NOT NULL DEFAULT 60 COMMENT '心跳间隔(秒)',
    connected_at       DATETIME(3)       DEFAULT NULL COMMENT '连接时间',
    disconnected_at     DATETIME(3)      DEFAULT NULL COMMENT '断开时间',
    
    -- 遗嘱消息
    will_enabled       BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否设置遗嘱',
    will_topic         VARCHAR(1024)     DEFAULT NULL COMMENT '遗嘱主题',
    will_qos           TINYINT           DEFAULT 0 COMMENT '遗嘱QoS',
    will_retain        BOOLEAN           DEFAULT FALSE COMMENT '遗嘱是否保留',
    
    -- 统计
    messages_received  BIGINT            NOT NULL DEFAULT 0 COMMENT '接收消息数',
    messages_sent      BIGINT            NOT NULL DEFAULT 0 COMMENT '发送消息数',
    
    PRIMARY KEY (client_id),
    INDEX idx_vhost (vhost),
    INDEX idx_connected (connected)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'MQTT会话表';
```

### 表结构：mqtt_subscription（MQTT订阅表）

```sql
CREATE TABLE mqtt_subscription (
    subscription_id    VARCHAR(64)       NOT NULL COMMENT '订阅ID',
    client_id          VARCHAR(256)      NOT NULL COMMENT '客户端ID',
    
    -- 订阅配置
    topic_filter       VARCHAR(1024)     NOT NULL COMMENT '主题过滤器(支持通配符)',
    qos               TINYINT           NOT NULL DEFAULT 0 COMMENT '订阅QoS',
    no_local          BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '不接收本地消息',
    retain_as_published BOOLEAN          NOT NULL DEFAULT FALSE COMMENT '保留原始标志',
    subscription_id_flag VARCHAR(32)    DEFAULT NULL COMMENT '订阅标识符',
    
    -- 状态
    active             BOOLEAN           NOT NULL DEFAULT TRUE,
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (subscription_id),
    UNIQUE KEY uk_client_topic (client_id, topic_filter),
    INDEX idx_topic_filter (topic_filter)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'MQTT订阅表';
```

### 表结构：mqtt_retained_message（保留消息表）

```sql
CREATE TABLE mqtt_retained_message (
    id                 BIGINT            NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    topic              VARCHAR(1024)     NOT NULL COMMENT '主题',
    payload            MEDIUMBLOB        NOT NULL COMMENT '消息体',
    qos               TINYINT           NOT NULL DEFAULT 0 COMMENT 'QoS等级',
    
    -- 元数据
    publisher_id       VARCHAR(256)      DEFAULT NULL COMMENT '发布者客户端ID',
    published_at       DATETIME(3)       NOT NULL COMMENT '发布时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_topic (topic),
    INDEX idx_qos (qos)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'MQTT保留消息表';
```

---

## QoS 等级

| QoS | 名称 | 传递保证 | 开销 |
|-----|------|---------|------|
| 0 | At Most Once | 最多一次（可能丢） | 最低 |
| 1 | At Least Once | 至少一次（可能重） | 中等 |
| 2 | Exactly Once | 恰好一次（可靠） | 最高 |

*图：MQTT 三级 QoS 对比（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 210" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <text x="120" y="24" text-anchor="middle" font-size="13" fill="#475569">等级</text>
  <text x="395" y="24" text-anchor="middle" font-size="13" fill="#475569">传递保证</text>
  <text x="635" y="24" text-anchor="middle" font-size="13" fill="#475569">开销</text>
  <rect x="20" y="34" width="200" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="120" y="61" text-anchor="middle" font-size="14" fill="#1e293b">QoS 0 · At Most Once</text>
  <rect x="250" y="34" width="290" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="395" y="61" text-anchor="middle" font-size="14" fill="#1e293b">最多一次（可能丢）</text>
  <rect x="570" y="34" width="130" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="635" y="61" text-anchor="middle" font-size="14" fill="#1e293b">最低</text>
  <rect x="20" y="90" width="200" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="120" y="117" text-anchor="middle" font-size="14" fill="#1e293b">QoS 1 · At Least Once</text>
  <rect x="250" y="90" width="290" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="395" y="117" text-anchor="middle" font-size="14" fill="#1e293b">至少一次（可能重）</text>
  <rect x="570" y="90" width="130" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="635" y="117" text-anchor="middle" font-size="14" fill="#1e293b">中等</text>
  <rect x="20" y="146" width="200" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="120" y="173" text-anchor="middle" font-size="14" fill="#1e293b">QoS 2 · Exactly Once</text>
  <rect x="250" y="146" width="290" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="395" y="173" text-anchor="middle" font-size="14" fill="#1e293b">恰好一次（可靠）</text>
  <rect x="570" y="146" width="130" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="635" y="173" text-anchor="middle" font-size="14" fill="#1e293b">最高</text>
</svg>

---

## MQTT 主题通配符

| 通配符 | 说明 | 示例 |
|--------|------|------|
| `+` | 单层通配 | `sensor/+/temperature` 匹配 `sensor/room1/temperature` |
| `#` | 多层通配 | `sensor/#` 匹配 `sensor/room1/temperature` |

---

*文档版本：v1.0 | 更新日期：2026-03-29*
