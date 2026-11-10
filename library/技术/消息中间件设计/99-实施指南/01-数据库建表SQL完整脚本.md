# 数据库建表 SQL 完整脚本

> 本文件整合了所有模块中的建表语句，复制到数据库执行即可初始化完整 schema。

---

## 初始化脚本

```sql
-- ==============================================
-- 消息中间件数据库 - 完整建表脚本
-- 版本: v1.0
-- 注：原稿在 6.2 表处截断且仅含前 20 张表；其余 96 张建表语句已从本仓库各模块文档（01~10 目录）原样并入，合计 116 张。
-- 日期: 2026-03-29
-- ==============================================

CREATE DATABASE IF NOT EXISTS message_broker
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE message_broker;

-- =============================================
-- 1. 概要设计模块
-- =============================================

-- (无独立表，概要设计为文档说明模块)

-- =============================================
-- 2. 核心数据模型
-- =============================================

-- 2.1 队列元数据表
CREATE TABLE IF NOT EXISTS queue_info (
    queue_id         VARCHAR(64)         NOT NULL COMMENT '队列唯一标识(UUID)',
    queue_name       VARCHAR(255)       NOT NULL COMMENT '队列名称',
    vhost            VARCHAR(128)       NOT NULL DEFAULT '/'  COMMENT '虚拟主机',
    exchange_name    VARCHAR(255)       NOT NULL COMMENT '绑定的交换机名称',
    binding_key      VARCHAR(255)       NOT NULL COMMENT '绑定键',
    queue_type       ENUM('classic', 'quorum', 'stream') NOT NULL DEFAULT 'classic' COMMENT '队列类型',
    durable          BOOLEAN            NOT NULL DEFAULT TRUE COMMENT '是否持久化',
    auto_delete      BOOLEAN            NOT NULL DEFAULT FALSE COMMENT '所有消费者断开后是否自动删除',
    exclusive        BOOLEAN            NOT NULL DEFAULT FALSE COMMENT '是否独占队列',
    arguments        JSON               DEFAULT NULL COMMENT '队列扩展参数(JSON)',
    max_length       BIGINT             DEFAULT NULL COMMENT '队列最大消息数',
    max_bytes        BIGINT             DEFAULT NULL COMMENT '队列最大字节数',
    overflow_policy  ENUM('reject-publish', 'drop-head', 'flow-control') DEFAULT NULL COMMENT '溢出策略',
    dead_letter_exchange   VARCHAR(255)  DEFAULT NULL COMMENT '死信交换机名称',
    dead_letter_routing_key VARCHAR(255)  DEFAULT NULL COMMENT '死信路由键',
    message_ttl      BIGINT             DEFAULT NULL COMMENT '队列默认消息TTL(毫秒)',
    status           ENUM('running', 'suspending', 'deleted') DEFAULT 'running' COMMENT '队列状态',
    message_count    BIGINT             NOT NULL DEFAULT 0 COMMENT '当前消息数量',
    consumer_count   INT                NOT NULL DEFAULT 0 COMMENT '当前消费者数量',
    created_at       DATETIME(3)         NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    updated_at       DATETIME(3)         NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
    deleted_at       DATETIME(3)         DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (queue_id),
    UNIQUE KEY uk_vhost_queue_name (vhost, queue_name),
    INDEX idx_exchange_binding (exchange_name, binding_key),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '队列元数据表';

-- 2.2 队列统计表
CREATE TABLE IF NOT EXISTS queue_stats (
    stat_id          BIGINT             NOT NULL AUTO_INCREMENT COMMENT '统计记录ID',
    queue_id         VARCHAR(64)        NOT NULL COMMENT '队列ID',
    stat_time        DATETIME(3)        NOT NULL COMMENT '统计时间点',
    message_count    BIGINT             NOT NULL DEFAULT 0 COMMENT '当前消息数',
    message_rate_in  DECIMAL(10,2)      DEFAULT 0 COMMENT '消息入队速率(条/秒)',
    message_rate_out DECIMAL(10,2)      DEFAULT 0 COMMENT '消息出队速率(条/秒)',
    consumer_count   INT                NOT NULL DEFAULT 0 COMMENT '消费者数量',
    unacked_count    BIGINT             NOT NULL DEFAULT 0 COMMENT '未确认消息数',
    queue_size_bytes BIGINT             NOT NULL DEFAULT 0 COMMENT '队列总字节数',
    avg_latency_ms   DECIMAL(10,2)      DEFAULT NULL COMMENT '平均消息延迟(毫秒)',
    PRIMARY KEY (stat_id),
    UNIQUE KEY uk_queue_stat_time (queue_id, stat_time),
    INDEX idx_stat_time (stat_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '队列运行时统计表';

-- 2.3 主题元数据表
CREATE TABLE IF NOT EXISTS topic_info (
    topic_id         VARCHAR(64)         NOT NULL COMMENT '主题唯一标识(UUID)',
    topic_name       VARCHAR(255)        NOT NULL COMMENT '主题名称',
    vhost            VARCHAR(128)        NOT NULL DEFAULT '/'  COMMENT '虚拟主机',
    topic_type       ENUM('fanout', 'hierarchical', 'tagged') NOT NULL DEFAULT 'tagged' COMMENT '主题类型',
    durable          BOOLEAN             NOT NULL DEFAULT TRUE COMMENT '是否持久化',
    auto_delete      BOOLEAN             NOT NULL DEFAULT FALSE COMMENT '无订阅者时是否自动删除',
    message_ttl      BIGINT             DEFAULT NULL COMMENT '消息默认TTL(毫秒)',
    max_msg_size     BIGINT             DEFAULT 1048576 COMMENT '单条消息最大字节数(默认1MB)',
    retention_days   INT                DEFAULT 7 COMMENT '消息保留天数',
    compaction       BOOLEAN            NOT NULL DEFAULT FALSE COMMENT '是否启用日志压缩',
    subscription_count  INT               NOT NULL DEFAULT 0 COMMENT '活跃订阅数',
    message_count       BIGINT           NOT NULL DEFAULT 0 COMMENT '当前消息总数',
    byte_count          BIGINT           NOT NULL DEFAULT 0 COMMENT '当前总字节数',
    created_at        DATETIME(3)         NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at        DATETIME(3)         NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    deleted_at        DATETIME(3)         DEFAULT NULL,
    PRIMARY KEY (topic_id),
    UNIQUE KEY uk_vhost_topic_name (vhost, topic_name),
    INDEX idx_topic_type (topic_type)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '主题元数据表';

-- 2.4 消息主表
CREATE TABLE IF NOT EXISTS message (
    message_id           VARCHAR(64)         NOT NULL COMMENT '消息唯一标识(UUID)',
    vhost                VARCHAR(128)       NOT NULL DEFAULT '/' COMMENT '虚拟主机',
    exchange_name        VARCHAR(255)       NOT NULL COMMENT '入站交换机',
    routing_key          VARCHAR(1024)      NOT NULL COMMENT '入站路由键',
    destination_type     ENUM('queue', 'topic') NOT NULL COMMENT '目的地类型',
    destination_id       VARCHAR(64)        NOT NULL COMMENT '目的地ID(队列或主题ID)',
    content_type         VARCHAR(128)       DEFAULT 'application/json' COMMENT '内容类型',
    content_encoding     VARCHAR(64)        DEFAULT 'utf-8' COMMENT '内容编码',
    delivery_mode        TINYINT            NOT NULL DEFAULT 1 COMMENT '1=非持久, 2=持久',
    priority             TINYINT            NOT NULL DEFAULT 5 COMMENT '优先级 0-9',
    message_timestamp    DATETIME(3)        NOT NULL COMMENT '消息创建时间',
    payload_size         INT                NOT NULL COMMENT '消息体大小(字节)',
    payload_checksum     VARCHAR(32)        DEFAULT NULL COMMENT '消息体校验和(MD5)',
    payload_ref          VARCHAR(512)       DEFAULT NULL COMMENT '大消息体引用(外部存储)',
    producer_id          VARCHAR(64)        NOT NULL COMMENT '生产者ID',
    producer_session_id  VARCHAR(64)        DEFAULT NULL COMMENT '生产者会话ID',
    user_id              VARCHAR(128)       DEFAULT NULL COMMENT '应用级用户ID',
    message_status       ENUM('pending', 'delivered', 'acknowledged', 'dead', 'expired') 
                         NOT NULL DEFAULT 'pending' COMMENT '消息状态',
    redelivered          BOOLEAN            NOT NULL DEFAULT FALSE COMMENT '是否重投',
    redelivery_count     INT                NOT NULL DEFAULT 0 COMMENT '重投次数',
    expiration           BIGINT             DEFAULT NULL COMMENT '消息过期时间(毫秒Unix时间戳)',
    ttl                  BIGINT             DEFAULT NULL COMMENT 'TTL(毫秒)',
    delivery_start_time  DATETIME(3)        DEFAULT NULL COMMENT '可开始投递时间(延迟消息)',
    transaction_id       VARCHAR(64)        DEFAULT NULL COMMENT '所属事务ID',
    is_transactional     BOOLEAN            NOT NULL DEFAULT FALSE COMMENT '是否事务消息',
    correlation_id       VARCHAR(255)       DEFAULT NULL COMMENT '关联ID(用于响应链)',
    reply_to             VARCHAR(255)       DEFAULT NULL COMMENT '回复目标地址',
    created_at            DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at            DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (message_id),
    INDEX idx_destination (destination_type, destination_id),
    INDEX idx_status (message_status),
    INDEX idx_expiration (expiration),
    INDEX idx_delivery_start (delivery_start_time),
    INDEX idx_timestamp (message_timestamp),
    INDEX idx_producer (producer_id),
    INDEX idx_routing_key (routing_key(255)),
    INDEX idx_transaction (transaction_id),
    INDEX idx_correlation (correlation_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '消息主表';

-- 2.5 消息扩展属性表
CREATE TABLE IF NOT EXISTS message_header (
    id              BIGINT            NOT NULL AUTO_INCREMENT COMMENT '属性ID',
    message_id      VARCHAR(64)       NOT NULL COMMENT '消息ID',
    header_key      VARCHAR(255)      NOT NULL COMMENT '属性键',
    header_value    TEXT              NOT NULL COMMENT '属性值(JSON序列化)',
    header_type     ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string' COMMENT '值类型',
    is_system       BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否系统属性',
    created_at      DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (id),
    UNIQUE KEY uk_message_header (message_id, header_key),
    INDEX idx_message (message_id),
    INDEX idx_header_key (header_key)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '消息扩展属性表';

-- 2.6 消费者元数据表
CREATE TABLE IF NOT EXISTS consumer_info (
    consumer_id         VARCHAR(64)         NOT NULL COMMENT '消费者唯一标识(UUID)',
    consumer_tag        VARCHAR(255)        NOT NULL COMMENT '消费者标签(客户端指定)',
    vhost               VARCHAR(128)       NOT NULL DEFAULT '/' COMMENT '虚拟主机',
    user_id             VARCHAR(128)       DEFAULT NULL COMMENT '所属用户ID',
    application_id      VARCHAR(128)      DEFAULT NULL COMMENT '应用ID',
    connection_id       VARCHAR(64)        NOT NULL COMMENT '所属连接ID',
    remote_ip           VARCHAR(45)        DEFAULT NULL COMMENT '客户端IP',
    client_name         VARCHAR(255)       DEFAULT NULL COMMENT '客户端名称',
    client_version      VARCHAR(64)        DEFAULT NULL COMMENT '客户端版本',
    protocol_version    VARCHAR(16)        DEFAULT NULL COMMENT '协议版本',
    consume_mode        ENUM('exclusive', 'shared', 'work') NOT NULL DEFAULT 'shared' COMMENT '消费模式',
    prefetch_count      INT                NOT NULL DEFAULT 10 COMMENT '预取消息数量',
    prefetch_size       INT                DEFAULT 0 COMMENT '预取大小(字节)',
    auto_ack            BOOLEAN            NOT NULL DEFAULT FALSE COMMENT '是否自动确认',
    status              ENUM('active', 'idle', 'paused', 'disconnected') DEFAULT 'active' COMMENT '消费者状态',
    last_heartbeat      DATETIME(3)        DEFAULT NULL COMMENT '最后心跳时间',
    messages_consumed   BIGINT             NOT NULL DEFAULT 0 COMMENT '累计消费消息数',
    bytes_consumed      BIGINT             NOT NULL DEFAULT 0 COMMENT '累计消费字节数',
    avg_latency_ms      DECIMAL(10,3)      DEFAULT NULL COMMENT '平均消费延迟(毫秒)',
    connected_at        DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '连接时间',
    disconnected_at     DATETIME(3)        DEFAULT NULL COMMENT '断开时间',
    created_at          DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at          DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (consumer_id),
    UNIQUE KEY uk_connection_tag (connection_id, consumer_tag),
    INDEX idx_vhost_user (vhost, user_id),
    INDEX idx_status (status),
    INDEX idx_connection (connection_id),
    INDEX idx_last_heartbeat (last_heartbeat)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '消费者元数据表';

-- 2.7 消费者偏移量表
CREATE TABLE IF NOT EXISTS consumer_offset (
    offset_id          VARCHAR(64)        NOT NULL COMMENT '偏移量记录ID',
    consumer_id        VARCHAR(64)        NOT NULL COMMENT '消费者ID',
    destination_type   ENUM('queue', 'topic') NOT NULL COMMENT '目的地类型',
    destination_id     VARCHAR(64)        NOT NULL COMMENT '目的地ID',
    offset             BIGINT             NOT NULL COMMENT '当前消费偏移量',
    offset_type        ENUM('message_id', 'sequence', 'timestamp', 'log_offset') NOT NULL DEFAULT 'sequence' COMMENT '偏移量类型',
    partition_id       INT                DEFAULT NULL COMMENT '分区ID',
    pending_offset     BIGINT             DEFAULT NULL COMMENT '待确认的偏移量(in-flight)',
    acknowledged_offset BIGINT             DEFAULT NULL COMMENT '已确认的最大偏移量',
    last_consumed_at   DATETIME(3)        DEFAULT NULL COMMENT '最后消费时间',
    lag                BIGINT             DEFAULT 0 COMMENT '当前消费滞后量',
    created_at         DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (offset_id),
    UNIQUE KEY uk_consumer_destination_offset (consumer_id, destination_type, destination_id, partition_id),
    INDEX idx_offset (destination_type, destination_id, partition_id, offset)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '消费者消费偏移量表';

-- 2.8 生产者元数据表
CREATE TABLE IF NOT EXISTS producer_info (
    producer_id         VARCHAR(64)         NOT NULL COMMENT '生产者唯一标识(UUID)',
    producer_name       VARCHAR(255)       NOT NULL COMMENT '生产者名称(客户端指定)',
    vhost               VARCHAR(128)       NOT NULL DEFAULT '/' COMMENT '虚拟主机',
    user_id             VARCHAR(128)       DEFAULT NULL COMMENT '所属用户ID',
    application_id      VARCHAR(128)      DEFAULT NULL COMMENT '应用ID',
    connection_id       VARCHAR(64)        NOT NULL COMMENT '所属连接ID',
    remote_ip           VARCHAR(45)        DEFAULT NULL COMMENT '客户端IP',
    client_name         VARCHAR(255)       DEFAULT NULL COMMENT '客户端名称',
    client_version      VARCHAR(64)        DEFAULT NULL COMMENT '客户端版本',
    protocol_version    VARCHAR(16)        DEFAULT NULL COMMENT '协议版本',
    publisher_confirms  BOOLEAN            NOT NULL DEFAULT FALSE COMMENT '是否启用发布确认',
    publisher_returns   BOOLEAN            NOT NULL DEFAULT FALSE COMMENT '是否启用退回消息',
    channel_max         INT                DEFAULT 0 COMMENT '最大信道数',
    status              ENUM('active', 'idle', 'blocked', 'disconnected') DEFAULT 'active',
    last_heartbeat      DATETIME(3)        DEFAULT NULL COMMENT '最后心跳时间',
    messages_sent       BIGINT             NOT NULL DEFAULT 0 COMMENT '累计发送消息数',
    bytes_sent          BIGINT             NOT NULL DEFAULT 0 COMMENT '累计发送字节数',
    confirm_success     BIGINT             NOT NULL DEFAULT 0 COMMENT '确认成功次数',
    confirm_failed      BIGINT             NOT NULL DEFAULT 0 COMMENT '确认失败次数',
    return_count        BIGINT             NOT NULL DEFAULT 0 COMMENT '退回消息次数',
    connected_at        DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    disconnected_at     DATETIME(3)        DEFAULT NULL,
    created_at          DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at          DATETIME(3)        NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (producer_id),
    UNIQUE KEY uk_connection_name (connection_id, producer_name),
    INDEX idx_vhost_user (vhost, user_id),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '生产者元数据表';

-- 2.9 交换机元数据表
CREATE TABLE IF NOT EXISTS exchange_info (
    exchange_id        VARCHAR(64)       NOT NULL COMMENT '交换机ID(UUID)',
    exchange_name      VARCHAR(255)       NOT NULL COMMENT '交换机名称',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/' COMMENT '虚拟主机',
    exchange_type      ENUM('direct', 'fanout', 'topic', 'headers') NOT NULL COMMENT '交换机类型',
    durable            BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否持久化',
    auto_delete        BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '无绑定关系时自动删除',
    internal           BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否为内部交换机',
    arguments          JSON              DEFAULT NULL COMMENT '扩展参数',
    alternate_exchange VARCHAR(255)       DEFAULT NULL COMMENT '备用交换机',
    binding_count      INT               NOT NULL DEFAULT 0 COMMENT '绑定数量',
    message_in_count   BIGINT            NOT NULL DEFAULT 0 COMMENT '累计接收消息数',
    message_out_count  BIGINT            NOT NULL DEFAULT 0 COMMENT '累计转发消息数',
    message_drop_count BIGINT            NOT NULL DEFAULT 0 COMMENT '累计丢弃消息数',
    status             ENUM('running', 'stopped', 'deleted') DEFAULT 'running',
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    deleted_at         DATETIME(3)        DEFAULT NULL,
    PRIMARY KEY (exchange_id),
    UNIQUE KEY uk_vhost_name (vhost, exchange_name),
    INDEX idx_type (exchange_type),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '交换机元数据表';

-- 2.10 绑定关系表
CREATE TABLE IF NOT EXISTS binding (
    binding_id         VARCHAR(64)       NOT NULL COMMENT '绑定ID(UUID)',
    source_exchange    VARCHAR(255)      NOT NULL COMMENT '源交换机名称',
    destination_type   ENUM('queue', 'exchange') NOT NULL DEFAULT 'queue' COMMENT '目标类型',
    destination_name   VARCHAR(255)      NOT NULL COMMENT '目标队列或交换机名称',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    binding_key        VARCHAR(1024)     DEFAULT '' COMMENT '绑定键',
    binding_headers    JSON              DEFAULT NULL COMMENT '头匹配规则(Headers交换机)',
    arguments          JSON              DEFAULT NULL COMMENT '扩展参数',
    is_dlx             BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否为死信绑定',
    active             BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否激活',
    messages_routed    BIGINT            NOT NULL DEFAULT 0 COMMENT '累计路由消息数',
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (binding_id),
    UNIQUE KEY uk_source_dest_key (vhost, source_exchange, destination_type, destination_name, binding_key),
    INDEX idx_source (source_exchange),
    INDEX idx_destination (destination_type, destination_name),
    INDEX idx_active (active)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '绑定关系表';

-- 2.11 主题标签表
CREATE TABLE IF NOT EXISTS topic_tag (
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

-- 2.12 主题消息索引表(用于快速查询和回溯)
CREATE TABLE IF NOT EXISTS topic_message_index (
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

-- 2.13 死信消息记录表
CREATE TABLE IF NOT EXISTS message_dead_letter (
    dead_letter_id   VARCHAR(64)       NOT NULL COMMENT '死信记录ID',
    message_id       VARCHAR(64)       NOT NULL COMMENT '原始消息ID',
    original_queue   VARCHAR(255)       NOT NULL COMMENT '原始队列名称',
    original_exchange VARCHAR(255)     NOT NULL COMMENT '原始交换机',
    
    -- 死信原因
    reason           ENUM('rejected', 'expired', 'max_redeliveries', 'consumer_crash', 'invalid_payload') 
                      NOT NULL COMMENT '死信原因',
    error_message    TEXT              DEFAULT NULL COMMENT '错误详情',
    stack_trace      TEXT              DEFAULT NULL COMMENT '异常堆栈',
    
    -- 处理记录
    dlx_exchange     VARCHAR(255)       DEFAULT NULL COMMENT '死信交换机',
    dlx_routing_key  VARCHAR(255)       DEFAULT NULL COMMENT '死信路由键',
    retry_count      INT               NOT NULL DEFAULT 0 COMMENT '重试次数',
    
    -- 状态
    status           ENUM('pending', 'retrying', 'archived', 'discarded') DEFAULT 'pending',
    
    -- 审计
    first_failed_at  DATETIME(3)        NOT NULL COMMENT '首次失败时间',
    last_failed_at   DATETIME(3)        NOT NULL COMMENT '最近失败时间',
    resolved_at      DATETIME(3)        DEFAULT NULL COMMENT '解决时间',
    
    PRIMARY KEY (dead_letter_id),
    INDEX idx_message (message_id),
    INDEX idx_status (status),
    INDEX idx_first_failed (first_failed_at),
    INDEX idx_reason (reason)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '死信消息记录表';

-- 2.14 消息幂等去重表
CREATE TABLE IF NOT EXISTS message_idempotency (
    idempotency_key   VARCHAR(255)     NOT NULL COMMENT '幂等键(producer_id + message_key)',
    message_id        VARCHAR(64)      NOT NULL COMMENT '已存储的消息ID',
    producer_id       VARCHAR(64)      NOT NULL COMMENT '生产者ID',
    created_at        DATETIME(3)      NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    expires_at        DATETIME(3)      NOT NULL COMMENT '幂等键过期时间',
    
    PRIMARY KEY (idempotency_key),
    INDEX idx_producer (producer_id),
    INDEX idx_expires (expires_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消息幂等去重表';

-- 2.15 消费者订阅关系表
CREATE TABLE IF NOT EXISTS consumer_subscription (
    subscription_id   VARCHAR(64)       NOT NULL COMMENT '订阅关系ID',
    consumer_id       VARCHAR(64)       NOT NULL COMMENT '消费者ID',
    destination_type   ENUM('queue', 'topic') NOT NULL COMMENT '目的地类型',
    destination_id    VARCHAR(64)       NOT NULL COMMENT '队列或主题ID',
    
    -- 订阅配置
    subscription_mode ENUM('exclusive', 'shared', 'failover') DEFAULT 'shared' COMMENT '订阅模式',
    filter_pattern    VARCHAR(1024)     DEFAULT NULL COMMENT '消息过滤模式',
    filter_headers    JSON              DEFAULT NULL COMMENT '头过滤规则',
    no_local          BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '禁止接收自己生产的消息',
    
    -- 消费位置
    start_policy      ENUM('first', 'last', 'timestamp', 'sequence') DEFAULT 'last' COMMENT '消费起始策略',
    start_timestamp   DATETIME(3)       DEFAULT NULL COMMENT '起始时间戳',
    start_sequence    BIGINT            DEFAULT NULL COMMENT '起始序列号',
    
    -- 状态
    status            ENUM('active', 'paused', 'pending_rebalance') DEFAULT 'active',
    
    -- 审计
    subscribed_at     DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    unsubscribed_at    DATETIME(3)       DEFAULT NULL,
    
    PRIMARY KEY (subscription_id),
    UNIQUE KEY uk_consumer_destination (consumer_id, destination_type, destination_id),
    INDEX idx_destination (destination_type, destination_id),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消费者订阅关系表';

-- 2.16 消费者运行时统计表
CREATE TABLE IF NOT EXISTS consumer_stats (
    stat_id           BIGINT            NOT NULL AUTO_INCREMENT COMMENT '统计ID',
    consumer_id       VARCHAR(64)       NOT NULL COMMENT '消费者ID',
    stat_time         DATETIME(3)       NOT NULL COMMENT '统计时间点',
    
    -- 吞吐量统计
    messages_consumed BIGINT            NOT NULL DEFAULT 0 COMMENT '周期内消费消息数',
    bytes_consumed    BIGINT            NOT NULL DEFAULT 0 COMMENT '周期内消费字节数',
    rate_msg_per_sec  DECIMAL(10,2)     DEFAULT 0 COMMENT '消费速率(条/秒)',
    
    -- 延迟统计
    avg_latency_ms    DECIMAL(10,2)     DEFAULT NULL COMMENT '平均延迟(毫秒)',
    p99_latency_ms    DECIMAL(10,2)     DEFAULT NULL COMMENT 'P99延迟(毫秒)',
    
    -- 错误统计
    error_count       INT               NOT NULL DEFAULT 0 COMMENT '处理错误次数',
    retry_count       INT               NOT NULL DEFAULT 0 COMMENT '重试次数',
    
    -- 滞后统计
    avg_lag           BIGINT             DEFAULT 0 COMMENT '平均消费滞后',
    
    PRIMARY KEY (stat_id),
    UNIQUE KEY uk_consumer_stat_time (consumer_id, stat_time),
    INDEX idx_stat_time (stat_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消费者运行时统计表';

-- 2.17 生产者事务表
CREATE TABLE IF NOT EXISTS producer_transaction (
    transaction_id      VARCHAR(64)       NOT NULL COMMENT '事务ID',
    producer_id         VARCHAR(64)       NOT NULL COMMENT '生产者ID',
    vhost               VARCHAR(128)      NOT NULL DEFAULT '/',
    
    -- 事务内容
    operation_type      ENUM('publish', 'ack', 'nack', 'commit', 'rollback') NOT NULL COMMENT '操作类型',
    message_ids         JSON              DEFAULT NULL COMMENT '事务包含的消息ID列表',
    exchange_name       VARCHAR(255)       DEFAULT NULL COMMENT '目标交换机',
    routing_keys        JSON              DEFAULT NULL COMMENT '路由键列表',
    
    -- 事务状态
    transaction_status  ENUM('pending', 'committing', 'committed', 'rolled_back', 'failed') DEFAULT 'pending',
    timeout_at          DATETIME(3)        DEFAULT NULL COMMENT '事务超时时间',
    
    -- 审计
    created_at          DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    completed_at        DATETIME(3)       DEFAULT NULL,
    
    PRIMARY KEY (transaction_id),
    INDEX idx_producer (producer_id),
    INDEX idx_status (transaction_status),
    INDEX idx_timeout (timeout_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '生产者事务表';

-- 2.18 生产者运行时统计表
CREATE TABLE IF NOT EXISTS producer_stats (
    stat_id             BIGINT            NOT NULL AUTO_INCREMENT COMMENT '统计ID',
    producer_id         VARCHAR(64)       NOT NULL COMMENT '生产者ID',
    stat_time           DATETIME(3)       NOT NULL COMMENT '统计时间点',
    
    -- 吞吐量
    messages_sent       BIGINT            NOT NULL DEFAULT 0 COMMENT '周期内发送消息数',
    bytes_sent          BIGINT            NOT NULL DEFAULT 0 COMMENT '周期内发送字节数',
    rate_msg_per_sec    DECIMAL(10,2)    DEFAULT 0 COMMENT '发送速率(条/秒)',
    
    -- 延迟
    avg_latency_ms      DECIMAL(10,2)    DEFAULT NULL COMMENT '平均发送延迟(毫秒)',
    p99_latency_ms      DECIMAL(10,2)    DEFAULT NULL COMMENT 'P99发送延迟(毫秒)',
    
    -- 错误统计
    error_count         INT               NOT NULL DEFAULT 0 COMMENT '发送失败次数',
    confirm_failed      INT               NOT NULL DEFAULT 0 COMMENT '确认失败次数',
    return_count        INT               NOT NULL DEFAULT 0 COMMENT '退回消息次数',
    
    PRIMARY KEY (stat_id),
    UNIQUE KEY uk_producer_stat_time (producer_id, stat_time),
    INDEX idx_stat_time (stat_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '生产者运行时统计表';

-- 2.19 订阅主表
CREATE TABLE IF NOT EXISTS subscription (
    subscription_id     VARCHAR(64)       NOT NULL COMMENT '订阅ID(UUID)',
    subscription_name   VARCHAR(255)      NOT NULL COMMENT '订阅名称',
    
    -- 归属
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    owner_type         ENUM('consumer', 'application', 'system') NOT NULL DEFAULT 'consumer' COMMENT '拥有者类型',
    owner_id           VARCHAR(64)       NOT NULL COMMENT '拥有者ID',
    
    -- 目的地
    destination_type   ENUM('queue', 'topic') NOT NULL COMMENT '目的地类型',
    destination_id     VARCHAR(64)       NOT NULL COMMENT '队列或主题ID',
    
    -- 过滤规则
    filter_type        ENUM('none', 'routing_key', 'header', 'sql') DEFAULT 'none' COMMENT '过滤类型',
    filter_pattern     VARCHAR(1024)     DEFAULT NULL COMMENT '过滤模式(路由键通配符)',
    filter_headers     JSON             DEFAULT NULL COMMENT '头过滤规则',
    filter_sql         TEXT             DEFAULT NULL COMMENT 'SQL过滤表达式',
    
    -- 订阅配置
    subscription_mode  ENUM('exclusive', 'shared', 'failover', 'cluster') DEFAULT 'shared' COMMENT '订阅模式',
    priority           INT               DEFAULT 0 COMMENT '订阅优先级(同目的地高优先级优先)',
    no_local          BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '不接收本地消息',
    
    -- 消费起始
    start_policy       ENUM('first', 'last', 'timestamp', 'sequence') DEFAULT 'last' COMMENT '起始策略',
    start_timestamp   DATETIME(3)       DEFAULT NULL COMMENT '起始时间',
    start_sequence    BIGINT            DEFAULT NULL COMMENT '起始序列号',
    
    -- 状态
    status             ENUM('active', 'paused', 'resuming', 'deleted') DEFAULT 'active',
    paused_reason      VARCHAR(255)      DEFAULT NULL COMMENT '暂停原因',
    
    -- 统计
    messages_delivered BIGINT            NOT NULL DEFAULT 0 COMMENT '累计投递消息数',
    bytes_delivered    BIGINT            NOT NULL DEFAULT 0 COMMENT '累计投递字节数',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    deleted_at         DATETIME(3)       DEFAULT NULL,
    
    PRIMARY KEY (subscription_id),
    UNIQUE KEY uk_owner_destination (owner_id, destination_type, destination_id),
    INDEX idx_destination (destination_type, destination_id),
    INDEX idx_owner (owner_type, owner_id),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '订阅主表';

-- 2.20 订阅路由表(消息流转路径)
CREATE TABLE IF NOT EXISTS subscription_route (
    route_id            VARCHAR(64)       NOT NULL COMMENT '路由ID',
    subscription_id    VARCHAR(64)       NOT NULL COMMENT '订阅ID',
    
    -- 源
    source_exchange     VARCHAR(255)      NOT NULL COMMENT '源交换机',
    source_routing_key  VARCHAR(1024)     DEFAULT NULL COMMENT '源路由键',
    
    -- 目标
    target_exchange     VARCHAR(255)      DEFAULT NULL COMMENT '目标交换机',
    target_routing_key  VARCHAR(1024)     DEFAULT NULL COMMENT '目标路由键',
    
    -- 转换
    transform_type     ENUM('none', 'header_rewrite', 'payload_transform') DEFAULT 'none' COMMENT '转换类型',
    transform_config   JSON              DEFAULT NULL COMMENT '转换配置',
    
    -- 状态
    active             BOOLEAN           NOT NULL DEFAULT TRUE,
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (route_id),
    INDEX idx_subscription (subscription_id),
    INDEX idx_source (source_exchange, source_routing_key)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '订阅路由表(消息流转路径)';

-- =============================================
-- 3. 消息管理
-- =============================================

-- 3.1 消息生命周期状态表
CREATE TABLE IF NOT EXISTS message_lifecycle (
    lifecycle_id        VARCHAR(64)       NOT NULL COMMENT '生命周期记录ID',
    message_id          VARCHAR(64)       NOT NULL COMMENT '消息ID',
    current_state       ENUM('created', 'confirmed', 'ready', 'in_flight', 'backlog', 
                              'acknowledged', 'redelivered', 'dead_letter', 'expired', 'archived') 
                         NOT NULL DEFAULT 'created',
    state_changed_at   DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '状态变更时间',
    consumer_id         VARCHAR(64)       DEFAULT NULL COMMENT '当前持有消费者ID',
    delivery_tag        BIGINT            DEFAULT NULL COMMENT '投递标签',
    delivery_start_at   DATETIME(3)       DEFAULT NULL COMMENT '开始投递时间',
    redelivery_count    INT               NOT NULL DEFAULT 0 COMMENT '重投次数',
    max_redeliveries    INT               NOT NULL DEFAULT 10 COMMENT '最大重投次数',
    last_redelivery_at  DATETIME(3)       DEFAULT NULL COMMENT '上次重投时间',
    redelivery_reason   VARCHAR(512)      DEFAULT NULL COMMENT '重投原因',
    created_at          DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    expires_at          DATETIME(3)       DEFAULT NULL COMMENT '过期时间',
    archived_at         DATETIME(3)       DEFAULT NULL COMMENT '归档时间',
    state_history       JSON              DEFAULT NULL COMMENT '状态历史变更链',
    PRIMARY KEY (lifecycle_id),
    UNIQUE KEY uk_message (message_id),
    INDEX idx_current_state (current_state),
    INDEX idx_consumer (consumer_id),
    INDEX idx_expires (expires_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '消息生命周期状态表';

-- 3.2 存储分段表
CREATE TABLE IF NOT EXISTS storage_segment (
    segment_id          VARCHAR(64)       NOT NULL COMMENT '分段ID',
    destination_type    ENUM('queue', 'topic') NOT NULL COMMENT '目的地类型',
    destination_id      VARCHAR(64)       NOT NULL COMMENT '目的地ID',
    partition_id        INT               DEFAULT 0 COMMENT '分区ID',
    segment_index       INT               NOT NULL COMMENT '分段序号',
    segment_type        ENUM('write', 'read', 'archive') DEFAULT 'write' COMMENT '分段类型',
    file_path           VARCHAR(1024)     NOT NULL COMMENT '物理文件路径',
    file_size           BIGINT            NOT NULL DEFAULT 0 COMMENT '当前文件大小(字节)',
    max_file_size       BIGINT            NOT NULL DEFAULT 536870912 COMMENT '最大文件大小(默认512MB)',
    start_offset        BIGINT            NOT NULL COMMENT '起始偏移量',
    end_offset          BIGINT            NOT NULL COMMENT '结束偏移量',
    message_count       INT               NOT NULL DEFAULT 0 COMMENT '消息数量',
    status              ENUM('active', 'sealed', 'archived', 'deleted') DEFAULT 'active',
    sealed_at           DATETIME(3)       DEFAULT NULL COMMENT '封存时间',
    first_message_time  DATETIME(3)       DEFAULT NULL COMMENT '首条消息时间',
    last_message_time   DATETIME(3)       DEFAULT NULL COMMENT '末条消息时间',
    created_at          DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at          DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (segment_id),
    UNIQUE KEY uk_destination_segment (destination_type, destination_id, partition_id, segment_index),
    INDEX idx_destination_status (destination_type, destination_id, status),
    INDEX idx_file_path (file_path)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '存储分段表';

-- 3.3 消息存储索引表(消息ID/序列号到物理位置的映射)
CREATE TABLE IF NOT EXISTS storage_index (
    index_id           BIGINT            NOT NULL AUTO_INCREMENT COMMENT '索引ID',
    destination_type   ENUM('queue', 'topic') NOT NULL COMMENT '目的地类型',
    destination_id     VARCHAR(64)       NOT NULL COMMENT '目的地ID',
    partition_id       INT               DEFAULT 0 COMMENT '分区ID',
    
    -- 消息定位
    message_id         VARCHAR(64)       NOT NULL COMMENT '消息ID',
    sequence_num       BIGINT            NOT NULL COMMENT '序列号',
    offset             BIGINT            NOT NULL COMMENT '物理偏移量',
    segment_id         VARCHAR(64)       NOT NULL COMMENT '所在分段ID',
    
    -- 消息元数据
    timestamp          DATETIME(3)       NOT NULL COMMENT '消息时间戳',
    payload_size       INT               NOT NULL COMMENT '消息体大小',
    
    PRIMARY KEY (index_id),
    UNIQUE KEY uk_destination_sequence (destination_type, destination_id, partition_id, sequence_num),
    INDEX idx_message (message_id),
    INDEX idx_segment (segment_id),
    INDEX idx_timestamp (timestamp)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消息存储索引表(消息ID/序列号到物理位置的映射)';

-- 3.4 存储策略配置表
CREATE TABLE IF NOT EXISTS storage_policy (
    policy_id          VARCHAR(64)       NOT NULL COMMENT '策略ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    destination_type   ENUM('queue', 'topic', 'global') NOT NULL DEFAULT 'global' COMMENT '应用类型',
    destination_id     VARCHAR(64)       DEFAULT NULL COMMENT '目的地ID(NULL表示全局)',
    
    -- 容量策略
    max_segment_size   BIGINT           NOT NULL DEFAULT 536870912 COMMENT '单分段最大大小(512MB)',
    max_segment_count  INT              DEFAULT NULL COMMENT '最大分段数量，NULL无限制',
    max_storage_size   BIGINT           DEFAULT NULL COMMENT '最大存储空间(NULL无限制)',
    
    -- 清理策略
    cleanup_type       ENUM('retention_time', 'size_based', 'message_count', 'never') DEFAULT 'retention_time' COMMENT '清理类型',
    retention_days     INT              DEFAULT 7 COMMENT '消息保留天数',
    cleanup_interval_hours INT           DEFAULT 24 COMMENT '清理周期(小时)',
    
    -- 压缩策略
    compaction_enabled  BOOLEAN          NOT NULL DEFAULT FALSE COMMENT '是否启用压缩',
    compaction_interval_hours INT        DEFAULT 72 COMMENT '压缩周期(小时)',
    compaction_min_ratio DECIMAL(5,2)   DEFAULT 0.5 COMMENT '压缩触发最小比率',
    
    -- 写入策略
    flush_type         ENUM('sync', 'async', 'batch') DEFAULT 'batch' COMMENT '刷盘策略',
    flush_interval_ms  INT               DEFAULT 100 COMMENT '批量刷盘间隔(毫秒)',
    flush_batch_size   INT               DEFAULT 100 COMMENT '批量刷盘条数',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (policy_id),
    INDEX idx_vhost_destination (vhost, destination_type, destination_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '存储策略配置表';

-- 3.5 消息生命周期事件表(完整审计链)
CREATE TABLE IF NOT EXISTS message_lifecycle_event (
    event_id           BIGINT            NOT NULL AUTO_INCREMENT COMMENT '事件ID',
    message_id         VARCHAR(64)       NOT NULL COMMENT '消息ID',
    
    -- 事件信息
    event_type         ENUM('created', 'confirmed', 'ready', 'delivered', 
                           'acked', 'nacked', 'redelivered', 'expired', 'dead_letter', 'archived') 
                      NOT NULL COMMENT '事件类型',
    from_state         VARCHAR(32)       DEFAULT NULL COMMENT '原状态',
    to_state           VARCHAR(32)       NOT NULL COMMENT '新状态',
    
    -- 事件上下文
    consumer_id        VARCHAR(64)       DEFAULT NULL COMMENT '相关消费者ID',
    reason             VARCHAR(512)      DEFAULT NULL COMMENT '变更原因',
    error_message      TEXT              DEFAULT NULL COMMENT '错误信息',
    
    -- 事件时间
    event_time         DATETIME(3)       NOT NULL COMMENT '事件发生时间',
    
    -- 性能指标
    latency_ms         DECIMAL(10,2)     DEFAULT NULL COMMENT '该阶段耗时(毫秒)',
    
    PRIMARY KEY (event_id),
    INDEX idx_message (message_id),
    INDEX idx_event_time (event_time),
    INDEX idx_event_type (event_type)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消息生命周期事件表(完整审计链)';

-- 3.6 优先级队列索引表
CREATE TABLE IF NOT EXISTS priority_queue_index (
    index_id          BIGINT            NOT NULL AUTO_INCREMENT COMMENT '索引ID',
    queue_id          VARCHAR(64)       NOT NULL COMMENT '队列ID',
    message_id        VARCHAR(64)       NOT NULL COMMENT '消息ID',
    
    -- 优先级
    priority          TINYINT           NOT NULL COMMENT '优先级 0-9',
    
    -- 位置信息
    sequence_num      BIGINT            NOT NULL COMMENT '队列内部序列号',
    enqueue_time      DATETIME(3)       NOT NULL COMMENT '入队时间',
    
    -- 状态
    status            ENUM('pending', 'dispatched', 'consumed', 'expired') DEFAULT 'pending',
    dispatched_at     DATETIME(3)       DEFAULT NULL COMMENT '分发时间',
    
    PRIMARY KEY (index_id),
    INDEX idx_queue_priority_time (queue_id, priority DESC, enqueue_time ASC),
    INDEX idx_queue_status (queue_id, status),
    INDEX idx_message (message_id),
    
    UNIQUE KEY uk_queue_sequence (queue_id, sequence_num)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '优先级队列索引表';

-- 3.7 队列优先级定义表
CREATE TABLE IF NOT EXISTS priority_definition (
    definition_id     VARCHAR(64)       NOT NULL COMMENT '定义ID',
    queue_id          VARCHAR(64)       NOT NULL COMMENT '队列ID',
    
    -- 优先级配置
    max_priority      TINYINT           NOT NULL DEFAULT 10 COMMENT '最大优先级级别(不含)',
    default_priority  TINYINT           NOT NULL DEFAULT 5 COMMENT '默认优先级',
    
    -- 队列模式
    priority_enabled  BOOLEAN          NOT NULL DEFAULT TRUE COMMENT '是否启用优先级',
    priority_ordering ENUM('strict', 'weighted') DEFAULT 'weighted' COMMENT '优先级排序模式',
    
    -- Weighted 模式权重配置
    weight_config     JSON             DEFAULT NULL COMMENT '优先级权重配置',
    /*
    {
      "0": 1,
      "1": 2,
      "2": 3,
      "3": 5,
      "4": 8,
      "5": 13,
      "6": 21,
      "7": 34,
      "8": 55,
      "9": 100
    }
    */
    
    -- 统计
    priority_distribution JSON           DEFAULT NULL COMMENT '优先级分布统计',
    
    -- 审计
    created_at       DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at       DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (definition_id),
    UNIQUE KEY uk_queue (queue_id),
    INDEX idx_priority_enabled (priority_enabled)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '队列优先级定义表';

-- 3.8 延迟消息表
CREATE TABLE IF NOT EXISTS delayed_message (
    delayed_id         VARCHAR(64)       NOT NULL COMMENT '延迟记录ID',
    message_id         VARCHAR(64)       NOT NULL COMMENT '消息ID',
    queue_id           VARCHAR(64)       NOT NULL COMMENT '目标队列ID',
    
    -- 延迟类型
    delay_type         ENUM('relative', 'absolute', 'cron') NOT NULL COMMENT '延迟类型',
    
    -- 延迟配置
    delay_ms           BIGINT             DEFAULT NULL COMMENT '相对延迟(毫秒)',
    scheduled_time     DATETIME(3)        DEFAULT NULL COMMENT '绝对定时时间',
    cron_expression    VARCHAR(64)       DEFAULT NULL COMMENT 'CRON表达式',
    
    -- 状态
    status             ENUM('waiting', 'ready', 'dispatched', 'cancelled', 'expired') DEFAULT 'waiting',
    
    -- 执行信息
    ready_time         DATETIME(3)        NOT NULL COMMENT '消息就绪时间',
    dispatched_time    DATETIME(3)        DEFAULT NULL COMMENT '实际投递时间',
    
    -- 重复执行
    repeat_count       INT               NOT NULL DEFAULT 0 COMMENT '已重复次数',
    max_repeat         INT               DEFAULT NULL COMMENT '最大重复次数，NULL无限',
    repeat_interval_ms BIGINT            DEFAULT NULL COMMENT '重复间隔(毫秒)',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    cancelled_at       DATETIME(3)        DEFAULT NULL COMMENT '取消时间',
    cancel_reason      VARCHAR(512)      DEFAULT NULL COMMENT '取消原因',
    
    PRIMARY KEY (delayed_id),
    UNIQUE KEY uk_message (message_id),
    INDEX idx_status_ready (status, ready_time),
    INDEX idx_ready_time (ready_time),
    INDEX idx_queue (queue_id),
    INDEX idx_cron (cron_expression)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '延迟消息表';

-- 3.9 分层时间轮表(高效延迟消息调度)
CREATE TABLE IF NOT EXISTS timer_wheel (
    wheel_id           VARCHAR(64)       NOT NULL COMMENT '时间轮ID',
    bucket_index       INT               NOT NULL COMMENT '时间轮格子索引',
    slot_time          DATETIME(3)       NOT NULL COMMENT '该格子对应的时间点',
    
    -- 格子内容
    delayed_messages   JSON              DEFAULT NULL COMMENT '该时间格内的延迟消息ID列表',
    message_count      INT               NOT NULL DEFAULT 0 COMMENT '消息数量',
    
    -- 轮状态
    status             ENOLEAN           NOT NULL DEFAULT 'active' COMMENT '是否激活',
    
    -- 元信息
    wheel_resolution_ms BIGINT          NOT NULL COMMENT '时间轮精度(毫秒)',
    wheel_capacity      INT             NOT NULL COMMENT '时间轮容量(格子数)',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (wheel_id, bucket_index),
    INDEX idx_slot_time (slot_time),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '分层时间轮表(高效延迟消息调度)';

-- 3.10 定时任务表
CREATE TABLE IF NOT EXISTS scheduled_task (
    task_id            VARCHAR(64)       NOT NULL COMMENT '任务ID',
    task_name          VARCHAR(255)      NOT NULL COMMENT '任务名称',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    
    -- 任务配置
    task_type          ENUM('cron', 'interval', 'once') NOT NULL COMMENT '任务类型',
    cron_expression    VARCHAR(64)       DEFAULT NULL COMMENT 'CRON表达式',
    interval_ms        BIGINT            DEFAULT NULL COMMENT '间隔执行(毫秒)',
    once_time          DATETIME(3)       DEFAULT NULL COMMENT '一次性执行时间',
    
    -- 关联的消息/模板
    message_template   JSON              NOT NULL COMMENT '消息模板',
    destination_type   ENUM('queue', 'topic') NOT NULL COMMENT '目的地类型',
    destination_id     VARCHAR(64)       NOT NULL COMMENT '目的地ID',
    
    -- 执行配置
    max_executions     INT               DEFAULT NULL COMMENT '最大执行次数，NULL无限',
    execution_count    INT               NOT NULL DEFAULT 0 COMMENT '已执行次数',
    next_execution_time DATETIME(3)      DEFAULT NULL COMMENT '下次执行时间',
    
    -- 状态
    status             ENUM('active', 'paused', 'completed', 'failed') DEFAULT 'active',
    last_execution_at  DATETIME(3)        DEFAULT NULL COMMENT '上次执行时间',
    last_execution_result JSON            DEFAULT NULL COMMENT '上次执行结果',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (task_id),
    INDEX idx_status_next (status, next_execution_time),
    INDEX idx_vhost (vhost)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '定时任务表';

-- 3.11 事务主表
CREATE TABLE IF NOT EXISTS transaction (
    transaction_id     VARCHAR(64)       NOT NULL COMMENT '事务ID',
    transaction_type   ENUM('publish', 'saga', 'coordinator') NOT NULL COMMENT '事务类型',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    
    -- 参与者
    coordinator_id     VARCHAR(64)       NOT NULL COMMENT '协调者ID',
    participant_count   INT               NOT NULL DEFAULT 0 COMMENT '参与者数量',
    
    -- 事务状态
    status             ENUM('init', 'preparing', 'prepared', 'committing', 'committed', 
                           'rolling_back', 'rolled_back', 'failed', 'cancelled') 
                      NOT NULL DEFAULT 'init',
    
    -- 超时控制
    timeout_ms         BIGINT            NOT NULL DEFAULT 30000 COMMENT '事务超时(毫秒)',
    started_at         DATETIME(3)       NOT NULL COMMENT '事务开始时间',
    expired_at         DATETIME(3)       NOT NULL COMMENT '事务过期时间',
    
    -- 结果
    result_code        VARCHAR(32)       DEFAULT NULL COMMENT '结果码',
    result_message     TEXT              DEFAULT NULL COMMENT '结果消息',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (transaction_id),
    INDEX idx_coordinator (coordinator_id),
    INDEX idx_status (status),
    INDEX idx_expired (expired_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '事务主表';

-- 3.12 事务消息关联表
CREATE TABLE IF NOT EXISTS transaction_message (
    id                 BIGINT            NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    transaction_id     VARCHAR(64)       NOT NULL COMMENT '事务ID',
    message_id         VARCHAR(64)       NOT NULL COMMENT '消息ID',
    
    -- 操作类型
    operation_type     ENUM('publish', 'ack', 'nack', 'compensate') NOT NULL COMMENT '操作类型',
    
    -- 消息详情
    exchange_name      VARCHAR(255)       NOT NULL COMMENT '目标交换机',
    routing_key        VARCHAR(1024)     NOT NULL COMMENT '路由键',
    payload_preview    VARCHAR(512)       DEFAULT NULL COMMENT '消息体预览',
    
    -- 执行状态
    execute_status     ENUM('pending', 'executing', 'success', 'failed') DEFAULT 'pending',
    execute_order      INT               NOT NULL COMMENT '执行顺序',
    error_message      TEXT              DEFAULT NULL COMMENT '错误信息',
    
    -- 补偿操作
    compensated        BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否已补偿',
    compensated_at     DATETIME(3)        DEFAULT NULL COMMENT '补偿时间',
    compensate_action  ENUM('delete', 'publish_dlq', 'rollback') DEFAULT NULL COMMENT '补偿动作',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    executed_at        DATETIME(3)       DEFAULT NULL COMMENT '执行时间',
    
    PRIMARY KEY (id),
    INDEX idx_transaction (transaction_id),
    INDEX idx_message (message_id),
    INDEX idx_execute_order (transaction_id, execute_order)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '事务消息关联表';

-- 3.13 Saga参与者表
CREATE TABLE IF NOT EXISTS saga_participant (
    participant_id     VARCHAR(64)       NOT NULL COMMENT '参与者ID',
    saga_id            VARCHAR(64)       NOT NULL COMMENT 'Saga事务ID',
    participant_name   VARCHAR(255)      NOT NULL COMMENT '参与者名称',
    service_name       VARCHAR(128)      NOT NULL COMMENT '服务名称',
    
    -- Saga 步骤
    step_order         INT               NOT NULL COMMENT '步骤顺序',
    step_type          ENUM('action', 'compensation') NOT NULL COMMENT '步骤类型',
    
    -- 执行配置
    action_type        VARCHAR(64)       NOT NULL COMMENT '动作类型',
    action_payload     JSON              NOT NULL COMMENT '动作参数',
    
    -- 执行状态
    status             ENUM('pending', 'executing', 'completed', 'failed', 'compensated', 'skip') 
                      DEFAULT 'pending',
    result             JSON              DEFAULT NULL COMMENT '执行结果',
    error_message      TEXT              DEFAULT NULL COMMENT '错误信息',
    
    -- 重试
    retry_count        INT               NOT NULL DEFAULT 0 COMMENT '重试次数',
    max_retry          INT               DEFAULT 3 COMMENT '最大重试次数',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    executed_at        DATETIME(3)       DEFAULT NULL COMMENT '执行时间',
    completed_at       DATETIME(3)       DEFAULT NULL COMMENT '完成时间',
    
    PRIMARY KEY (participant_id),
    INDEX idx_saga (saga_id),
    INDEX idx_saga_step (saga_id, step_order)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'Saga参与者表';

-- =============================================
-- 4. 高可用与集群
-- =============================================

-- 4.1 集群节点表
CREATE TABLE IF NOT EXISTS cluster_node (
    node_id            VARCHAR(64)       NOT NULL COMMENT '节点ID',
    node_name          VARCHAR(128)      NOT NULL COMMENT '节点名称',
    host               VARCHAR(255)      NOT NULL COMMENT '主机地址',
    port               INT               NOT NULL DEFAULT 5672 COMMENT 'AMQP端口',
    management_port    INT               DEFAULT 15672 COMMENT '管理API端口',
    cluster_id         VARCHAR(64)       NOT NULL COMMENT '所属集群ID',
    node_type          ENUM('leader', 'follower', 'standalone') DEFAULT 'standalone' COMMENT '节点类型',
    role               ENUM('primary', 'secondary', 'arbiter') DEFAULT 'primary' COMMENT '角色',
    data_center        VARCHAR(64)       DEFAULT NULL COMMENT '数据中心',
    cpu_cores          INT               DEFAULT NULL COMMENT 'CPU核心数',
    memory_bytes       BIGINT            DEFAULT NULL COMMENT '内存大小',
    disk_bytes         BIGINT            DEFAULT NULL COMMENT '磁盘大小',
    status             ENUM('running', 'stopped', 'joining', 'leaving', 'failed') DEFAULT 'running',
    version            VARCHAR(32)       DEFAULT NULL COMMENT '节点版本',
    uptime_seconds     BIGINT            DEFAULT 0 COMMENT '运行时间(秒)',
    connections_count  INT               NOT NULL DEFAULT 0 COMMENT '连接数',
    channels_count     INT               NOT NULL DEFAULT 0 COMMENT '信道数',
    queues_count       INT               NOT NULL DEFAULT 0 COMMENT '队列数',
    consumers_count    INT               NOT NULL DEFAULT 0 COMMENT '消费者数',
    joined_at          DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '加入集群时间',
    last_heartbeat_at  DATETIME(3)       DEFAULT NULL COMMENT '最后心跳',
    PRIMARY KEY (node_id),
    UNIQUE KEY uk_node_name (node_name),
    INDEX idx_cluster (cluster_id),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '集群节点表';

-- 4.2 集群配置表
CREATE TABLE IF NOT EXISTS cluster_config (
    cluster_id         VARCHAR(64)       NOT NULL COMMENT '集群ID',
    cluster_name       VARCHAR(128)      NOT NULL COMMENT '集群名称',
    consensus_algorithm ENUM('raft', 'gossip', 'zab', 'paxos') DEFAULT 'raft' COMMENT '共识算法',
    election_timeout_ms BIGINT            NOT NULL DEFAULT 5000 COMMENT '选举超时(毫秒)',
    heartbeat_interval_ms BIGINT          NOT NULL DEFAULT 1000 COMMENT '心跳间隔(毫秒)',
    default_replicas   INT               NOT NULL DEFAULT 2 COMMENT '默认副本数',
    discovery_type     ENUM('static', 'dns', 'etcd', 'k8s') DEFAULT 'static' COMMENT '节点发现方式',
    discovery_config   JSON              DEFAULT NULL COMMENT '发现配置',
    status             ENUM('healthy', 'degraded', 'unavailable') DEFAULT 'healthy',
    node_count         INT               NOT NULL DEFAULT 1 COMMENT '节点数',
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (cluster_id),
    UNIQUE KEY uk_name (cluster_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '集群配置表';

-- 4.3 复制配置表
CREATE TABLE IF NOT EXISTS replication_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    source_node        VARCHAR(128)      NOT NULL COMMENT '源节点',
    target_node        VARCHAR(128)      NOT NULL COMMENT '目标节点',
    
    -- 复制配置
    replication_mode    ENUM('sync', 'async', 'semi_sync') NOT NULL DEFAULT 'async' COMMENT '复制模式',
    ack_policy         ENUM('leader', 'majority', 'all') DEFAULT 'leader' COMMENT '确认策略',
    
    -- 同步配置
    batch_size         INT               NOT NULL DEFAULT 100 COMMENT '批量同步大小',
    flush_interval_ms  INT               NOT NULL DEFAULT 1000 COMMENT '刷盘间隔(毫秒)',
    max_lag_bytes      BIGINT            DEFAULT 1073741824 COMMENT '最大允许滞后(1GB)',
    max_lag_seconds    INT               DEFAULT 300 COMMENT '最大允许滞后时间(秒)',
    
    -- 状态
    status             ENUM('active', 'paused', 'catching_up', 'failed') DEFAULT 'active',
    
    -- 统计
    replication_lag    BIGINT            NOT NULL DEFAULT 0 COMMENT '当前复制滞后量',
    last_sync_at       DATETIME(3)       DEFAULT NULL COMMENT '最后同步时间',
    bytes_replicated   BIGINT            NOT NULL DEFAULT 0 COMMENT '累计复制字节',
    
    PRIMARY KEY (config_id),
    UNIQUE KEY uk_source_target (source_node, target_node),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '复制配置表';

-- 4.4 复制日志表
CREATE TABLE IF NOT EXISTS replication_log (
    log_id             BIGINT            NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    source_node        VARCHAR(128)      NOT NULL COMMENT '源节点',
    target_node        VARCHAR(128)      NOT NULL COMMENT '目标节点',
    
    -- 操作
    operation_type     ENUM('write', 'delete', 'update', 'snapshot') NOT NULL COMMENT '操作类型',
    operation_data     JSON             NOT NULL COMMENT '操作数据',
    
    -- 状态
    status             ENUM('pending', 'replicated', 'failed') DEFAULT 'pending',
    
    -- 位置
    log_offset         BIGINT            NOT NULL COMMENT '日志偏移量',
    log_timestamp      DATETIME(3)       NOT NULL COMMENT '日志时间',
    replicated_at      DATETIME(3)       DEFAULT NULL COMMENT '复制完成时间',
    
    PRIMARY KEY (log_id),
    INDEX idx_source_target (source_node, target_node, log_offset),
    INDEX idx_status (status),
    INDEX idx_timestamp (log_timestamp)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '复制日志表';

-- 4.5 分区配置表
CREATE TABLE IF NOT EXISTS partition_config (
    partition_id       VARCHAR(64)       NOT NULL COMMENT '分区ID',
    queue_id           VARCHAR(64)       NOT NULL COMMENT '所属队列ID',
    partition_index     INT              NOT NULL COMMENT '分区序号',
    
    -- 分区位置
    leader_node        VARCHAR(128)      NOT NULL COMMENT '主节点',
    replica_nodes      JSON             DEFAULT NULL COMMENT '副本节点列表',
    
    -- 分区状态
    status             ENUM('active', 'offline', 'migrating', 'shrinking') DEFAULT 'active',
    message_count      BIGINT            NOT NULL DEFAULT 0 COMMENT '消息数量',
    bytes_used         BIGINT            NOT NULL DEFAULT 0 COMMENT '已用字节数',
    
    -- 分区范围
    start_key          VARCHAR(255)      DEFAULT NULL COMMENT '范围分区起始键',
    end_key            VARCHAR(255)      DEFAULT NULL COMMENT '范围分区结束键',
    hash_range_start   BIGINT            DEFAULT NULL COMMENT '哈希分区起始值',
    hash_range_end     BIGINT            DEFAULT NULL COMMENT '哈希分区结束值',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (partition_id),
    UNIQUE KEY uk_queue_index (queue_id, partition_index),
    INDEX idx_leader (leader_node),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '分区配置表';

-- 4.6 分区重分配记录表
CREATE TABLE IF NOT EXISTS partition_reassignment (
    reassignment_id    VARCHAR(64)       NOT NULL COMMENT '重分配ID',
    partition_id       VARCHAR(64)       NOT NULL COMMENT '分区ID',
    
    -- 变更
    source_node        VARCHAR(128)      NOT NULL COMMENT '原节点',
    target_node        VARCHAR(128)      NOT NULL COMMENT '目标节点',
    
    -- 状态
    status             ENUM('pending', 'in_progress', 'completed', 'failed') DEFAULT 'pending',
    progress_percent    DECIMAL(5,2)     DEFAULT 0 COMMENT '进度百分比',
    started_at         DATETIME(3)       DEFAULT NULL,
    completed_at       DATETIME(3)       DEFAULT NULL,
    
    PRIMARY KEY (reassignment_id),
    INDEX idx_partition (partition_id),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '分区重分配记录表';

-- 4.7 故障切换记录表
CREATE TABLE IF NOT EXISTS failover_record (
    failover_id        VARCHAR(64)       NOT NULL COMMENT '切换记录ID',
    cluster_id         VARCHAR(64)       NOT NULL COMMENT '集群ID',
    
    -- 节点信息
    failed_node        VARCHAR(128)      NOT NULL COMMENT '故障节点',
    promoted_node      VARCHAR(128)      NOT NULL COMMENT '提升节点',
    
    -- 故障原因
    failure_type       ENUM('heartbeat_timeout', 'network_partition', 'disk_failure', 
                           'oom_killed', 'process_crash', 'manual') NOT NULL COMMENT '故障类型',
    failure_detail     TEXT              DEFAULT NULL COMMENT '故障详情',
    
    -- 切换过程
    detected_at        DATETIME(3)       NOT NULL COMMENT '检测时间',
    initiated_at       DATETIME(3)       NOT NULL COMMENT '发起切换时间',
    completed_at       DATETIME(3)       DEFAULT NULL COMMENT '切换完成时间',
    duration_ms        BIGINT            DEFAULT NULL COMMENT '切换耗时(毫秒)',
    
    -- 数据状态
    data_loss          BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否有数据丢失',
    lost_messages      INT               DEFAULT NULL COMMENT '丢失消息数(如果有的话)',
    
    -- 结果
    status             ENUM('success', 'partial', 'failed') DEFAULT 'success',
    
    PRIMARY KEY (failover_id),
    INDEX idx_cluster (cluster_id),
    INDEX idx_failed_node (failed_node),
    INDEX idx_time (detected_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '故障切换记录表';

-- 4.8 一致性配置表
CREATE TABLE IF NOT EXISTS consensus_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    queue_id           VARCHAR(64)       DEFAULT NULL COMMENT '队列ID(为NULL表示全局)',
    topic_id           VARCHAR(64)       DEFAULT NULL COMMENT '主题ID(为NULL表示全局)',
    
    -- 一致性模型
    consistency_model  ENUM('strong', 'sequential', 'eventual', 'causal') 
                      NOT NULL DEFAULT 'sequential' COMMENT '一致性模型',
    
    -- 写入确认
    write_ack_policy   ENUM('leader', 'majority', 'all') DEFAULT 'leader' COMMENT '写入确认策略',
    min_isr            INT               DEFAULT 1 COMMENT '最小同步副本数',
    
    -- 读取策略
    read_policy        ENUM('leader', 'follower', 'closest') DEFAULT 'leader' COMMENT '读取策略',
    read_after_write   BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '写后读一致性',
    
    -- 幂等
    idempotent_enabled  BOOLEAN          NOT NULL DEFAULT TRUE COMMENT '幂等写入',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (config_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '一致性配置表';

-- 4.9 共识日志表
CREATE TABLE IF NOT EXISTS consensus_log (
    log_id             BIGINT            NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    cluster_id         VARCHAR(64)       NOT NULL COMMENT '集群ID',
    term               BIGINT            NOT NULL COMMENT '任期号',
    index              BIGINT            NOT NULL COMMENT '日志索引',
    
    -- 操作
    operation          ENUM('write', 'delete', 'config_change', 'leader_change') NOT NULL,
    operation_data     JSON             NOT NULL COMMENT '操作数据',
    
    -- 共识状态
    committed          BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否已提交',
    committed_at       DATETIME(3)       DEFAULT NULL COMMENT '提交时间',
    applied            BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否已应用',
    applied_at         DATETIME(3)       DEFAULT NULL COMMENT '应用时间',
    
    PRIMARY KEY (log_id),
    UNIQUE KEY uk_cluster_term_index (cluster_id, term, index),
    INDEX idx_committed (committed, committed_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '共识日志表';

-- 4.10 虚拟主机表
CREATE TABLE IF NOT EXISTS vhost (
    vhost_id          VARCHAR(64)       NOT NULL COMMENT '虚拟主机ID',
    vhost_name        VARCHAR(128)      NOT NULL COMMENT '虚拟主机名称',
    
    -- 配置
    description        VARCHAR(512)     DEFAULT NULL COMMENT '描述',
    
    -- 资源配额
    max_connections    INT               DEFAULT NULL COMMENT '最大连接数，NULL=无限制',
    max_channels       INT               DEFAULT NULL COMMENT '最大信道数，NULL=无限制',
    max_queues         INT               DEFAULT NULL COMMENT '最大队列数，NULL=无限制',
    max_exchanges      INT               DEFAULT NULL COMMENT '最大交换机数，NULL=无限制',
    max_message_size   BIGINT            DEFAULT 10485760 COMMENT '单消息最大大小(默认10MB)',
    max_storage_bytes  BIGINT            DEFAULT NULL COMMENT '最大存储字节数，NULL=无限制',
    
    -- 配额策略
    quota_policy       ENUM('block', 'reject', 'evict') DEFAULT 'block' COMMENT '配额超限策略',
    
    -- 资源使用
    current_connections INT              NOT NULL DEFAULT 0 COMMENT '当前连接数',
    current_queues      INT              NOT NULL DEFAULT 0 COMMENT '当前队列数',
    current_exchanges   INT              NOT NULL DEFAULT 0 COMMENT '当前交换机数',
    current_storage_bytes BIGINT         NOT NULL DEFAULT 0 COMMENT '当前存储字节数',
    
    -- 多租户
    tenant_id         VARCHAR(64)       DEFAULT NULL COMMENT '租户ID',
    
    -- 状态
    status             ENUM('active', 'suspended', 'deleted') DEFAULT 'active',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    deleted_at         DATETIME(3)       DEFAULT NULL,
    
    PRIMARY KEY (vhost_id),
    UNIQUE KEY uk_name (vhost_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '虚拟主机表';

-- 4.11 虚拟主机资源使用统计表
CREATE TABLE IF NOT EXISTS vhost_resource_usage (
    usage_id           BIGINT            NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    vhost_id           VARCHAR(64)       NOT NULL COMMENT '虚拟主机ID',
    stat_time          DATETIME(3)       NOT NULL COMMENT '统计时间点',
    
    -- 资源使用
    connections_count  INT               NOT NULL DEFAULT 0 COMMENT '连接数',
    channels_count     INT               NOT NULL DEFAULT 0 COMMENT '信道数',
    queues_count       INT               NOT NULL DEFAULT 0 COMMENT '队列数',
    exchanges_count    INT               NOT NULL DEFAULT 0 COMMENT '交换机数',
    storage_bytes      BIGINT            NOT NULL DEFAULT 0 COMMENT '存储字节数',
    messages_total     BIGINT            NOT NULL DEFAULT 0 COMMENT '累计消息数',
    
    -- 吞吐量
    msg_in_rate       DECIMAL(10,2)    DEFAULT 0 COMMENT '入消息速率(/秒)',
    msg_out_rate      DECIMAL(10,2)    DEFAULT 0 COMMENT '出消息速率(/秒)',
    bytes_in_rate      DECIMAL(10,2)    DEFAULT 0 COMMENT '入字节速率(/秒)',
    bytes_out_rate     DECIMAL(10,2)    DEFAULT 0 COMMENT '出字节速率(/秒)',
    
    PRIMARY KEY (usage_id),
    UNIQUE KEY uk_vhost_time (vhost_id, stat_time),
    INDEX idx_stat_time (stat_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '虚拟主机资源使用统计表';

-- 4.12 网络分区事件表
CREATE TABLE IF NOT EXISTS partition_event (
    event_id           VARCHAR(64)       NOT NULL COMMENT '事件ID',
    cluster_id         VARCHAR(64)       NOT NULL COMMENT '集群ID',
    
    -- 分区信息
    partition_id       INT               NOT NULL COMMENT '分区编号(自动递增)',
    partition_type     ENUM('suspected', 'confirmed', 'recovering', 'resolved') NOT NULL DEFAULT 'suspected',
    
    -- 节点分布
    majority_nodes     JSON              DEFAULT NULL COMMENT '多数派节点列表',
    minority_nodes     JSON              DEFAULT NULL COMMENT '少数派节点列表',
    isolated_nodes     JSON              DEFAULT NULL COMMENT '完全隔离节点列表',
    
    -- 时间线
    suspected_at       DATETIME(3)       NOT NULL COMMENT '开始怀疑时间',
    confirmed_at       DATETIME(3)       DEFAULT NULL COMMENT '确认时间',
    recovery_started_at DATETIME(3)     DEFAULT NULL COMMENT '开始恢复时间',
    resolved_at        DATETIME(3)       DEFAULT NULL COMMENT '解决时间',
    
    -- 检测依据
    detection_method   ENUM('heartbeat', 'raft_timeout', 'quorum_check', 'manual') NOT NULL,
    heartbeat_missed  INT               DEFAULT NULL COMMENT '连续丢失心跳次数',
    
    -- 影响
    messages_lost     INT               DEFAULT NULL COMMENT '可能丢失消息数',
    transactions_aborted INT             DEFAULT NULL COMMENT '中止事务数',
    affected_vhosts   JSON              DEFAULT NULL COMMENT '受影响VHost列表',
    
    -- 决策
    resolution        ENUM('auto', 'manual', 'graceful_shutdown') DEFAULT 'auto',
    winning_node      VARCHAR(128)       DEFAULT NULL COMMENT '获胜节点',
    shutdown_nodes    JSON              DEFAULT NULL COMMENT '被关闭节点列表',
    
    -- 结果
    status            ENUM('investigating', 'acting', 'recovering', 'resolved', 'failed') DEFAULT 'investigating',
    resolution_detail TEXT              DEFAULT NULL COMMENT '解决详情',
    
    PRIMARY KEY (event_id),
    INDEX idx_cluster (cluster_id),
    INDEX idx_type (partition_type),
    INDEX idx_time (suspected_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '网络分区事件表';

-- 4.13 分区决策日志表
CREATE TABLE IF NOT EXISTS partition_decision_log (
    log_id             BIGINT            NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    event_id           VARCHAR(64)       NOT NULL COMMENT '分区事件ID',
    decision_round     INT               NOT NULL COMMENT '决策轮次',
    
    -- 决策内容
    node_name          VARCHAR(128)      NOT NULL COMMENT '做出决策的节点',
    decision_type      ENUM('claim_leadership', 'yield_leadership', 'shutdown', 'continue_raft') NOT NULL,
    reasoning         TEXT              NOT NULL COMMENT '决策依据',
    
    -- 执行
    executed           BOOLEAN           NOT NULL DEFAULT FALSE,
    executed_at        DATETIME(3)       DEFAULT NULL COMMENT '执行时间',
    execution_result   TEXT              DEFAULT NULL COMMENT '执行结果',
    
    PRIMARY KEY (log_id),
    INDEX idx_event (event_id),
    INDEX idx_round (event_id, decision_round)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '分区决策日志表';

-- =============================================
-- 5. 安全与权限
-- =============================================

-- 5.1 用户表
CREATE TABLE IF NOT EXISTS user (
    user_id            VARCHAR(64)       NOT NULL COMMENT '用户ID',
    username           VARCHAR(128)      NOT NULL COMMENT '用户名',
    vhost              VARCHAR(128)      DEFAULT '/' COMMENT '默认虚拟主机',
    auth_type          ENUM('password', 'token', 'certificate', 'ldap', 'oauth2') 
                      NOT NULL DEFAULT 'password' COMMENT '认证方式',
    password_hash      VARCHAR(255)      DEFAULT NULL COMMENT '密码哈希(bcrypt)',
    salt               VARCHAR(64)       DEFAULT NULL COMMENT '盐值',
    access_token       VARCHAR(512)      DEFAULT NULL COMMENT '访问令牌',
    token_expires_at   DATETIME(3)       DEFAULT NULL COMMENT '令牌过期时间',
    status             ENUM('active', 'disabled', 'locked') DEFAULT 'active',
    login_attempts     INT               NOT NULL DEFAULT 0 COMMENT '连续登录失败次数',
    max_login_attempts INT               NOT NULL DEFAULT 5 COMMENT '最大登录尝试',
    locked_until       DATETIME(3)       DEFAULT NULL COMMENT '锁定截止时间',
    tags               JSON              DEFAULT NULL COMMENT '用户标签',
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    last_login_at      DATETIME(3)       DEFAULT NULL COMMENT '最后登录时间',
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_username (username)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表';

-- 5.2 角色表
CREATE TABLE IF NOT EXISTS role (
    role_id            VARCHAR(64)       NOT NULL COMMENT '角色ID',
    role_name          VARCHAR(128)      NOT NULL COMMENT '角色名称',
    description        VARCHAR(512)      DEFAULT NULL COMMENT '角色描述',
    parent_role_id     VARCHAR(64)       DEFAULT NULL COMMENT '父角色ID',
    status             ENUM('active', 'disabled') DEFAULT 'active',
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (role_id),
    UNIQUE KEY uk_name (role_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '角色表';

-- 5.3 权限表
CREATE TABLE IF NOT EXISTS permission (
    permission_id      VARCHAR(64)       NOT NULL COMMENT '权限ID',
    role_id            VARCHAR(64)       NOT NULL COMMENT '角色ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/' COMMENT '虚拟主机',
    resource_type      ENUM('queue', 'exchange', 'topic', 'connection', 'channel', 'user', 'policy', 'parameter', 'vhost') 
                      NOT NULL COMMENT '资源类型',
    resource_name      VARCHAR(255)      NOT NULL COMMENT '资源名称(支持通配符)',
    actions            JSON              NOT NULL COMMENT '允许的操作列表',
    active             BOOLEAN           NOT NULL DEFAULT TRUE,
    PRIMARY KEY (permission_id),
    INDEX idx_role (role_id),
    INDEX idx_resource (resource_type, resource_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '权限表';

-- 5.4 审计日志表
CREATE TABLE IF NOT EXISTS audit_log (
    log_id             BIGINT            NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    user_id            VARCHAR(64)       DEFAULT NULL COMMENT '操作用户ID',
    username           VARCHAR(128)      DEFAULT NULL COMMENT '操作用户名',
    client_ip          VARCHAR(45)       DEFAULT NULL COMMENT '客户端IP',
    session_id         VARCHAR(64)       DEFAULT NULL COMMENT '会话ID',
    operation_type     ENUM('create', 'update', 'delete', 'read', 'config_change', 
                           'auth_success', 'auth_failure', 'acl_check', 'admin_action') 
                      NOT NULL COMMENT '操作类型',
    resource_type      VARCHAR(64)       NOT NULL COMMENT '资源类型',
    resource_name      VARCHAR(255)      DEFAULT NULL COMMENT '资源名称',
    resource_id        VARCHAR(64)       DEFAULT NULL COMMENT '资源ID',
    success            BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否成功',
    error_message      TEXT              DEFAULT NULL COMMENT '错误信息',
    event_time         DATETIME(3)       NOT NULL COMMENT '事件时间',
    duration_ms        INT               DEFAULT NULL COMMENT '操作耗时(毫秒)',
    archived           BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否已归档',
    PRIMARY KEY (log_id),
    INDEX idx_user_time (user_id, event_time),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_type (operation_type),
    INDEX idx_event_time (event_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '审计日志表';

-- 5.5 认证会话表
CREATE TABLE IF NOT EXISTS auth_session (
    session_id         VARCHAR(64)       NOT NULL COMMENT '会话ID',
    user_id            VARCHAR(64)       NOT NULL COMMENT '用户ID',
    
    -- 会话信息
    connection_id      VARCHAR(64)       NOT NULL COMMENT '关联连接ID',
    protocol           VARCHAR(32)       NOT NULL COMMENT '协议',
    remote_address     VARCHAR(45)       NOT NULL COMMENT '远程地址',
    
    -- Token
    session_token      VARCHAR(512)      NOT NULL COMMENT '会话令牌',
    refresh_token      VARCHAR(512)      DEFAULT NULL COMMENT '刷新令牌',
    
    -- 时间
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    expires_at         DATETIME(3)       NOT NULL COMMENT '过期时间',
    last_activity_at    DATETIME(3)      DEFAULT NULL COMMENT '最后活动时间',
    
    -- 状态
    status             ENUM('active', 'expired', 'revoked') DEFAULT 'active',
    revoked_at         DATETIME(3)       DEFAULT NULL COMMENT '撤销时间',
    revoke_reason      VARCHAR(255)      DEFAULT NULL COMMENT '撤销原因',
    
    PRIMARY KEY (session_id),
    INDEX idx_user (user_id),
    INDEX idx_token (session_token),
    INDEX idx_status_expires (status, expires_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '认证会话表';

-- 5.6 用户角色关联表
CREATE TABLE IF NOT EXISTS user_role (
    id                 BIGINT            NOT NULL AUTO_INCREMENT COMMENT 'ID',
    user_id            VARCHAR(64)       NOT NULL COMMENT '用户ID',
    role_id            VARCHAR(64)       NOT NULL COMMENT '角色ID',
    
    -- 作用域
    vhost              VARCHAR(128)      DEFAULT NULL COMMENT '生效的虚拟主机(NULL=全部)',
    
    -- 时间
    granted_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    expires_at         DATETIME(3)       DEFAULT NULL COMMENT '过期时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_role_vhost (user_id, role_id, vhost)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '用户角色关联表';

-- 5.7 加密配置表
CREATE TABLE IF NOT EXISTS encryption_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    
    -- TLS 配置
    tls_enabled        BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否启用TLS',
    tls_cert_path      VARCHAR(512)      DEFAULT NULL COMMENT '证书路径',
    tls_key_path       VARCHAR(512)      DEFAULT NULL COMMENT '私钥路径',
    tls_ca_path        VARCHAR(512)      DEFAULT NULL COMMENT 'CA证书路径',
    tls_min_version    VARCHAR(16)       DEFAULT 'TLS1.2' COMMENT '最低TLS版本',
    tls_verify_client  ENUM('none', 'optional', 'require') DEFAULT 'none' COMMENT '客户端证书验证',
    
    -- 消息加密
    payload_encryption BOOLEAN          NOT NULL DEFAULT FALSE COMMENT '是否启用消息体加密',
    encryption_algorithm ENUM('AES-128-GCM', 'AES-256-GCM', 'ChaCha20-Poly1305') DEFAULT 'AES-256-GCM',
    key_rotation_days  INT               DEFAULT 90 COMMENT '密钥轮换周期(天)',
    
    -- 密钥管理
    kms_provider       ENUM('builtin', 'aws_kms', 'hashicorp_vault', 'aliyun_kms') DEFAULT 'builtin',
    kms_config         JSON             DEFAULT NULL COMMENT 'KMS配置',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (config_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '加密配置表';

-- 5.8 密钥管理表
CREATE TABLE IF NOT EXISTS encryption_key (
    key_id             VARCHAR(64)       NOT NULL COMMENT '密钥ID',
    key_alias          VARCHAR(128)      NOT NULL COMMENT '密钥别名',
    
    -- 密钥信息
    algorithm          VARCHAR(32)       NOT NULL COMMENT '加密算法',
    key_version        INT               NOT NULL COMMENT '密钥版本',
    key_status         ENUM('active', 'deprecated', 'expired', 'destroyed') DEFAULT 'active',
    
    -- 生命周期
    created_at         DATETIME(3)       NOT NULL COMMENT '创建时间',
    expires_at         DATETIME(3)       DEFAULT NULL COMMENT '过期时间',
    deprecated_at      DATETIME(3)       DEFAULT NULL COMMENT '废弃时间',
    
    -- 使用范围
    vhost              VARCHAR(128)      DEFAULT NULL COMMENT '适用的虚拟主机',
    queues             JSON             DEFAULT NULL COMMENT '适用的队列列表',
    
    PRIMARY KEY (key_id),
    UNIQUE KEY uk_alias_version (key_alias, key_version),
    INDEX idx_status (key_status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '密钥管理表';

-- 5.9 安全扫描记录表
CREATE TABLE IF NOT EXISTS security_scan_record (
    scan_id            VARCHAR(64)       NOT NULL COMMENT '扫描ID',
    scan_type          ENUM('dependency', 'config', 'network', 'full') NOT NULL COMMENT '扫描类型',
    
    -- 扫描范围
    scope             VARCHAR(1024)      NOT NULL COMMENT '扫描范围描述',
    node_name         VARCHAR(128)       DEFAULT NULL COMMENT '节点名称',
    
    -- 扫描结果
    total_issues      INT               NOT NULL DEFAULT 0 COMMENT '发现问题总数',
    critical_count    INT               NOT NULL DEFAULT 0 COMMENT '严重问题数',
    high_count        INT               NOT NULL DEFAULT 0 COMMENT '高危问题数',
    medium_count      INT               NOT NULL DEFAULT 0 COMMENT '中危问题数',
    low_count         INT               NOT NULL DEFAULT 0 COMMENT '低危问题数',
    
    -- 报告
    report_ref        VARCHAR(512)       DEFAULT NULL COMMENT '详细报告引用',
    raw_output        TEXT              DEFAULT NULL COMMENT '原始扫描输出',
    
    -- 扫描器
    scanner_name      VARCHAR(64)        NOT NULL COMMENT '扫描工具名称',
    scanner_version   VARCHAR(32)        DEFAULT NULL COMMENT '扫描工具版本',
    
    -- 状态
    status            ENUM('running', 'completed', 'failed') DEFAULT 'running',
    started_at        DATETIME(3)       NOT NULL COMMENT '扫描开始时间',
    completed_at      DATETIME(3)       DEFAULT NULL COMMENT '扫描结束时间',
    
    PRIMARY KEY (scan_id),
    INDEX idx_type_time (scan_type, started_at),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '安全扫描记录表';

-- 5.10 漏洞记录表
CREATE TABLE IF NOT EXISTS vulnerability (
    vuln_id            VARCHAR(64)       NOT NULL COMMENT '漏洞ID',
    vuln_code          VARCHAR(64)       DEFAULT NULL COMMENT '漏洞编号(如 CVE-2024-xxxx)',
    
    -- 漏洞信息
    title             VARCHAR(512)       NOT NULL COMMENT '漏洞标题',
    description        TEXT              DEFAULT NULL COMMENT '漏洞描述',
    severity          ENUM('critical', 'high', 'medium', 'low', 'info') NOT NULL COMMENT '严重程度',
    cvss_score        DECIMAL(3,1)     DEFAULT NULL COMMENT 'CVSS评分(0-10)',
    cvss_vector       VARCHAR(256)      DEFAULT NULL COMMENT 'CVSS向量',
    
    -- 影响范围
    affected_component VARCHAR(256)      NOT NULL COMMENT '受影响组件',
    affected_versions  VARCHAR(512)      DEFAULT NULL COMMENT '受影响版本',
    fixed_versions    VARCHAR(512)      DEFAULT NULL COMMENT '修复版本',
    
    -- 检测信息
    detection_source  VARCHAR(128)       NOT NULL COMMENT '检测来源(扫描工具/情报)',
    scan_id           VARCHAR(64)       DEFAULT NULL COMMENT '关联扫描ID',
    detected_at       DATETIME(3)       NOT NULL COMMENT '发现时间',
    
    -- 状态
    status            ENUM('open', 'in_progress', 'mitigated', 'accepted', 'fixed', 'false_positive') 
                      DEFAULT 'open' COMMENT '漏洞状态',
    priority          INT               DEFAULT 5 COMMENT '处理优先级(1-10)',
    
    -- 处置
    assigned_to       VARCHAR(128)      DEFAULT NULL COMMENT '处理人',
    remediation_plan   TEXT              DEFAULT NULL COMMENT '修复计划',
    mitigation_plan   TEXT              DEFAULT NULL COMMENT '缓解方案',
    resolved_at       DATETIME(3)       DEFAULT NULL COMMENT '解决时间',
    resolution_note   TEXT              DEFAULT NULL COMMENT '解决说明',
    
    PRIMARY KEY (vuln_id),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    INDEX idx_detected (detected_at),
    INDEX idx_component (affected_component)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '漏洞记录表';

-- 5.11 安全策略表
CREATE TABLE IF NOT EXISTS security_policy (
    policy_id          VARCHAR(64)       NOT NULL COMMENT '策略ID',
    vhost              VARCHAR(128)      DEFAULT NULL COMMENT '虚拟主机(NULL表示全局)',
    
    -- 策略类型
    policy_type        ENUM('password', 'connection', 'encryption', 'audit', 'compliance') NOT NULL,
    policy_name        VARCHAR(255)      NOT NULL COMMENT '策略名称',
    description        VARCHAR(512)      DEFAULT NULL COMMENT '策略描述',
    
    -- 策略规则
    rules              JSON              NOT NULL COMMENT '策略规则(JSON)',
    /*
    密码策略示例:
    {
      "min_length": 12,
      "require_uppercase": true,
      "require_lowercase": true,
      "require_digit": true,
      "require_special": true,
      "max_age_days": 90,
      "history_count": 5
    }
    */
    
    -- 强制级别
    enforcement        ENUM('enforce', 'audit', 'advisory') DEFAULT 'enforce' COMMENT '执行级别',
    
    -- 状态
    enabled            BOOLEAN           NOT NULL DEFAULT TRUE,
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (policy_id),
    INDEX idx_type (policy_type)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '安全策略表';

-- 5.12 TLS证书管理表
CREATE TABLE IF NOT EXISTS certificate (
    cert_id            VARCHAR(64)       NOT NULL COMMENT '证书ID',
    
    -- 证书信息
    common_name        VARCHAR(256)      NOT NULL COMMENT '通用名称(CN)',
    organization       VARCHAR(256)      DEFAULT NULL COMMENT '组织(O)',
    organizational_unit VARCHAR(256)    DEFAULT NULL COMMENT '组织单元(OU)',
    
    -- 证书内容
    cert_pem           TEXT              NOT NULL COMMENT '证书PEM内容',
    cert_chain_pem     TEXT              DEFAULT NULL COMMENT '证书链PEM内容',
    private_key_pem    TEXT              DEFAULT NULL COMMENT '私钥PEM内容(加密存储)',
    
    -- 证书属性
    serial_number      VARCHAR(128)      DEFAULT NULL COMMENT '序列号',
    issuer             VARCHAR(256)      DEFAULT NULL COMMENT '颁发者',
    signature_algorithm VARCHAR(64)      DEFAULT NULL COMMENT '签名算法',
    key_algorithm      VARCHAR(64)       DEFAULT NULL COMMENT '密钥算法',
    key_size           INT               DEFAULT NULL COMMENT '密钥长度(位)',
    
    -- 有效期
    not_before         DATETIME(3)       NOT NULL COMMENT '生效时间',
    not_after          DATETIME(3)       NOT NULL COMMENT '过期时间',
    
    -- 用途
    cert_type          ENUM('server', 'client', 'ca', 'self_signed') NOT NULL COMMENT '证书类型',
    usage              JSON              DEFAULT NULL COMMENT '扩展密钥用途',
    /*
    示例: ["server_auth", "client_auth"]
    */
    
    -- 指纹
    sha256_fingerprint VARCHAR(64)       NOT NULL COMMENT 'SHA256指纹',
    sha1_fingerprint   VARCHAR(40)       DEFAULT NULL COMMENT 'SHA1指纹',
    
    -- 自动续期
    auto_renew         BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否自动续期',
    renew_before_days  INT               DEFAULT 30 COMMENT '提前多少天续期',
    
    -- 关联
    ca_cert_id         VARCHAR(64)       DEFAULT NULL COMMENT 'CA证书ID',
    
    -- 状态
    status             ENUM('active', 'expired', 'revoked', 'pending_renewal') DEFAULT 'active',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    revoked_at         DATETIME(3)       DEFAULT NULL COMMENT '吊销时间',
    revoked_reason     VARCHAR(512)      DEFAULT NULL COMMENT '吊销原因',
    
    PRIMARY KEY (cert_id),
    UNIQUE KEY uk_fingerprint (sha256_fingerprint),
    INDEX cn (common_name),
    INDEX idx_status (status),
    INDEX idx_expiry (not_after),
    INDEX idx_renew (auto_renew, not_after)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'TLS证书管理表';

-- 5.13 API密钥管理表
CREATE TABLE IF NOT EXISTS api_key (
    key_id             VARCHAR(64)       NOT NULL COMMENT '密钥ID',
    key_name           VARCHAR(255)      NOT NULL COMMENT '密钥名称',
    
    -- 密钥内容
    api_key            VARCHAR(256)      NOT NULL COMMENT 'API Key明文(仅创建时可见)',
    key_hash           VARCHAR(128)      NOT NULL COMMENT 'API Key哈希(SHA256)',
    key_prefix         VARCHAR(16)       NOT NULL COMMENT 'Key前缀(用于识别)',
    
    -- 关联
    user_id            VARCHAR(64)       DEFAULT NULL COMMENT '关联用户',
    vhost              VARCHAR(128)      DEFAULT NULL COMMENT '关联VHost',
    app_name           VARCHAR(255)      DEFAULT NULL COMMENT '应用名称',
    
    -- 权限
    permissions        JSON              NOT NULL COMMENT '权限列表',
    /*
    示例:
    {
      "allow": ["queue:read", "queue:write", "exchange:read"],
      "deny": ["admin:*"],
      "rate_limit": 10000
    }
    */
    
    -- 限制
    ip_whitelist       JSON              DEFAULT NULL COMMENT 'IP白名单',
    allowed_apis       JSON              DEFAULT NULL COMMENT '允许的API列表',
    
    -- 有效期
    valid_from         DATETIME(3)       DEFAULT CURRENT_TIMESTAMP(3) COMMENT '生效时间',
    valid_until        DATETIME(3)       DEFAULT NULL COMMENT '过期时间(NULL=永不过期)',
    
    -- 使用统计
    total_requests     BIGINT            NOT NULL DEFAULT 0 COMMENT '累计请求次数',
    last_used_at       DATETIME(3)       DEFAULT NULL COMMENT '最后使用时间',
    
    -- 状态
    status             ENUM('active', 'disabled', 'expired', 'revoked') DEFAULT 'active',
    
    -- 审计
    created_by         VARCHAR(128)      DEFAULT NULL COMMENT '创建人',
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    revoked_at         DATETIME(3)       DEFAULT NULL COMMENT '吊销时间',
    
    PRIMARY KEY (key_id),
    UNIQUE KEY uk_key_hash (key_hash),
    UNIQUE KEY uk_key_prefix (key_prefix),
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_expiry (valid_until)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'API密钥管理表';

-- =============================================
-- 6. 监控与运维
-- =============================================

-- 6.1 告警规则表
CREATE TABLE IF NOT EXISTS alert_rule (
    rule_id            VARCHAR(64)       NOT NULL COMMENT '规则ID',
    rule_name          VARCHAR(255)      NOT NULL COMMENT '规则名称',
    metric_name        VARCHAR(128)      NOT NULL COMMENT '监控指标',
    condition_type     ENUM('threshold', 'rate', 'absence', 'anomaly') NOT NULL COMMENT '条件类型',
    operator           ENUM('gt', 'gte', 'lt', 'lte', 'eq', 'neq') NOT NULL COMMENT '比较运算符',
    threshold          DOUBLE            NOT NULL COMMENT '阈值',
    duration_seconds   INT               DEFAULT 0 COMMENT '持续时长(秒)',
    severity           ENUM('critical', 'warning', 'info') NOT NULL COMMENT '告警级别',
    notify_channels    JSON              NOT NULL COMMENT '通知渠道',
    silence_period_min INT               DEFAULT 0 COMMENT '静默周期(分钟)',
    repeat_interval_min INT              DEFAULT 60 COMMENT '重复通知间隔(分钟)',
    enabled            BOOLEAN           NOT NULL DEFAULT TRUE,
    labels             JSON              DEFAULT NULL COMMENT '告警标签',
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    PRIMARY KEY (rule_id),
    UNIQUE KEY uk_name (rule_name),
    INDEX idx_metric (metric_name),
    INDEX idx_severity (severity),
    INDEX idx_enabled (enabled)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '告警规则表';

-- 6.2 运维操作记录表
CREATE TABLE IF NOT EXISTS ops_record (
    ops_id             VARCHAR(64)       NOT NULL COMMENT '操作记录ID',
    operator_id        VARCHAR(64)       NOT NULL COMMENT '操作人ID',
    operator_name      VARCHAR(128)      NOT NULL COMMENT '操作人名称',
    operation_type     ENUM('queue_create', 'queue_delete', 'queue_purge', 'connection_close',
                           'consumer_kick', 'policy_set', 'cluster_restart', 'backup', 'restore',
                           'config_change', 'failover_trigger') NOT NULL COMMENT '操作类型',
    resource_type      VARCHAR(64)       DEFAULT NULL COMMENT '资源类型',
    resource_id        VARCHAR(64)       DEFAULT NULL COMMENT '资源ID',
    resource_name      VARCHAR(255)      DEFAULT NULL COMMENT '资源名称',
    description        TEXT              DEFAULT NULL COMMENT '操作描述',
    params             JSON              DEFAULT NULL COMMENT '操作参数',
    result             TEXT              DEFAULT NULL COMMENT '操作结果',
    affected_messages  INT               DEFAULT NULL COMMENT '影响消息数',
    affected_consumers INT               DEFAULT NULL COMMENT '影响消费者数',
    executed_at        DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    client_ip          VARCHAR(45)       DEFAULT NULL COMMENT '操作来源IP',
    PRIMARY KEY (ops_id),
    INDEX idx_operator (operator_id),
    INDEX idx_type (operation_type),
    INDEX idx_time (executed_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '运维操作记录表';
-- 6.3 指标配置表
CREATE TABLE IF NOT EXISTS metric_config (
    metric_id          VARCHAR(64)       NOT NULL COMMENT '指标ID',
    metric_name        VARCHAR(128)      NOT NULL COMMENT '指标名称',
    metric_group       ENUM('broker', 'queue', 'exchange', 'consumer', 'producer', 'connection', 'disk', 'memory', 'os') 
                      NOT NULL COMMENT '指标分组',
    
    -- 指标定义
    metric_type        ENUM('counter', 'gauge', 'histogram', 'summary') NOT NULL COMMENT '指标类型',
    unit               VARCHAR(32)       DEFAULT NULL COMMENT '单位(msg/s, bytes, ms, %)',
    description        VARCHAR(512)      DEFAULT NULL COMMENT '指标描述',
    
    -- 采集配置
    collect_interval_s INT               NOT NULL DEFAULT 10 COMMENT '采集间隔(秒)',
    enabled            BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否启用',
    
    -- Prometheus 标签
    labels             JSON             DEFAULT NULL COMMENT '标签定义',
    
    PRIMARY KEY (metric_id),
    UNIQUE KEY uk_name (metric_name),
    INDEX idx_group (metric_group)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '指标配置表';

-- 6.4 指标时序数据表
CREATE TABLE IF NOT EXISTS metric_data (
    id                 BIGINT            NOT NULL AUTO_INCREMENT COMMENT 'ID',
    metric_name        VARCHAR(128)      NOT NULL COMMENT '指标名称',
    node_name          VARCHAR(128)      DEFAULT NULL COMMENT '节点名称',
    
    -- 维度
    labels_json        JSON             DEFAULT NULL COMMENT '标签(JSON)',
    
    -- 数据
    value              DOUBLE            NOT NULL COMMENT '指标值',
    timestamp          DATETIME(3)       NOT NULL COMMENT '采集时间',
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_metric_node_time (metric_name, node_name, timestamp),
    INDEX idx_metric_time (metric_name, timestamp),
    INDEX idx_node_time (node_name, timestamp)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '指标时序数据表';

-- 6.5 告警记录表
CREATE TABLE IF NOT EXISTS alert_record (
    alert_id           VARCHAR(64)       NOT NULL COMMENT '告警ID',
    rule_id            VARCHAR(64)       NOT NULL COMMENT '规则ID',
    
    severity           ENUM('critical', 'warning', 'info') NOT NULL,
    title              VARCHAR(512)      NOT NULL COMMENT '告警标题',
    description        TEXT              DEFAULT NULL COMMENT '告警描述',
    current_value      DOUBLE            DEFAULT NULL COMMENT '当前指标值',
    
    status             ENUM('firing', 'resolved', 'acknowledged', 'silenced') DEFAULT 'firing',
    fired_at           DATETIME(3)       NOT NULL COMMENT '触发时间',
    resolved_at        DATETIME(3)       DEFAULT NULL COMMENT '恢复时间',
    acknowledged_at     DATETIME(3)      DEFAULT NULL COMMENT '确认时间',
    acknowledged_by     VARCHAR(128)     DEFAULT NULL COMMENT '确认人',
    
    notify_sent        BOOLEAN           NOT NULL DEFAULT FALSE,
    notify_sent_at     DATETIME(3)       DEFAULT NULL,
    labels             JSON             DEFAULT NULL,
    
    PRIMARY KEY (alert_id),
    INDEX idx_rule (rule_id),
    INDEX idx_status (status),
    INDEX idx_fired (fired_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '告警记录表';

-- 6.6 追踪Trace主表
CREATE TABLE IF NOT EXISTS trace_record (
    trace_id           VARCHAR(64)       NOT NULL COMMENT 'Trace ID',
    
    -- 基本信息
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    first_service      VARCHAR(128)      NOT NULL COMMENT '首个服务名称',
    
    -- 时间
    start_time        DATETIME(3)       NOT NULL COMMENT 'Trace 开始时间',
    end_time           DATETIME(3)       DEFAULT NULL COMMENT 'Trace 结束时间',
    duration_ms        BIGINT            DEFAULT NULL COMMENT '总耗时(毫秒)',
    
    -- 结果
    status             ENUM('ok', 'error', 'in_progress') DEFAULT 'in_progress',
    error_count        INT               NOT NULL DEFAULT 0 COMMENT '错误数量',
    
    -- 采样
    sampling_rate      DECIMAL(5,2)     DEFAULT 1.0 COMMENT '采样率(0-1)',
    sampled            BOOLEAN          NOT NULL DEFAULT TRUE COMMENT '是否被采样',
    
    PRIMARY KEY (trace_id),
    INDEX idx_start_time (start_time),
    INDEX idx_status (status),
    INDEX idx_service (first_service)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '追踪Trace主表';

-- 6.7 追踪Span明细表
CREATE TABLE IF NOT EXISTS span_record (
    span_id            VARCHAR(64)       NOT NULL COMMENT 'Span ID',
    trace_id           VARCHAR(64)       NOT NULL COMMENT 'Trace ID',
    
    -- Span 信息
    span_name          VARCHAR(256)      NOT NULL COMMENT 'Span名称',
    service_name       VARCHAR(128)      NOT NULL COMMENT '服务名称',
    operation_name     VARCHAR(256)      NOT NULL COMMENT '操作名称',
    
    -- 层级
    parent_span_id     VARCHAR(64)       DEFAULT NULL COMMENT '父Span ID',
    span_kind          ENUM('producer', 'consumer', 'client', 'server', 'internal') NOT NULL COMMENT 'Span类型',
    depth              INT               NOT NULL DEFAULT 0 COMMENT '调用深度',
    
    -- 时间
    start_time         DATETIME(3)       NOT NULL COMMENT 'Span开始时间',
    end_time           DATETIME(3)       DEFAULT NULL COMMENT 'Span结束时间',
    duration_ms        BIGINT            DEFAULT NULL COMMENT 'Span耗时(毫秒)',
    
    -- 消息追踪
    message_id         VARCHAR(64)       DEFAULT NULL COMMENT '关联消息ID',
    queue_id           VARCHAR(64)       DEFAULT NULL COMMENT '关联队列ID',
    node_name          VARCHAR(128)      DEFAULT NULL COMMENT '处理节点',
    
    -- 结果
    status_code        ENUM('ok', 'error') DEFAULT 'ok',
    error_type         VARCHAR(128)      DEFAULT NULL COMMENT '错误类型',
    error_message      TEXT              DEFAULT NULL COMMENT '错误信息',
    
    -- 标签
    tags               JSON              DEFAULT NULL COMMENT 'Span标签',
    /*
    {
      "messaging.system": "rabbitmq",
      "messaging.destination": "order.queue",
      "messaging.operation": "receive"
    }
    */
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (span_id),
    INDEX idx_trace (trace_id),
    INDEX idx_parent (parent_span_id),
    INDEX idx_service (service_name),
    INDEX idx_start_time (start_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '追踪Span明细表';

-- 6.8 备份任务表
CREATE TABLE IF NOT EXISTS backup_job (
    job_id             VARCHAR(64)       NOT NULL COMMENT '备份任务ID',
    job_name           VARCHAR(255)      NOT NULL COMMENT '备份任务名称',
    
    -- 备份类型
    backup_type        ENUM('full', 'incremental', 'differential', 'snapshot') NOT NULL DEFAULT 'full',
    target_type         ENUM('metadata', 'messages', 'config', 'full') NOT NULL COMMENT '备份目标',
    target_scope        JSON              DEFAULT NULL COMMENT '备份范围',
    /*
    示例:
    {
      "vhosts": ["/", "/tenant-a"],
      "queues": ["queue-1", "queue-2"]
    }
    */
    
    -- 存储配置
    storage_type       ENUM('local', 's3', 'oss', 'minio', 'nfs') NOT NULL COMMENT '存储类型',
    storage_path        VARCHAR(1024)     NOT NULL COMMENT '存储路径/桶名',
    retention_days      INT               NOT NULL DEFAULT 30 COMMENT '保留天数',
    
    -- 调度
    schedule_type       ENUM('manual', 'cron', 'interval') NOT NULL DEFAULT 'manual',
    cron_expression     VARCHAR(64)       DEFAULT NULL COMMENT 'CRON表达式',
    interval_hours     INT               DEFAULT NULL COMMENT '间隔小时数(interval模式)',
    
    -- 状态
    status              ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    progress_percent    DECIMAL(5,2)     DEFAULT 0 COMMENT '进度百分比',
    
    -- 结果
    backup_file_ref    VARCHAR(512)       DEFAULT NULL COMMENT '备份文件引用',
    backup_size_bytes   BIGINT            DEFAULT NULL COMMENT '备份大小',
    duration_seconds   INT               DEFAULT NULL COMMENT '备份耗时(秒)',
    started_at         DATETIME(3)       DEFAULT NULL COMMENT '开始时间',
    completed_at       DATETIME(3)       DEFAULT NULL COMMENT '完成时间',
    
    -- 校验
    checksum            VARCHAR(64)       DEFAULT NULL COMMENT '校验和(SHA256)',
    verified            BOOLEAN           DEFAULT FALSE COMMENT '是否已校验',
    verified_at         DATETIME(3)       DEFAULT NULL COMMENT '校验时间',
    
    -- 关联
    triggered_by        VARCHAR(64)       DEFAULT NULL COMMENT '触发人/系统',
    
    PRIMARY KEY (job_id),
    INDEX idx_status (status),
    INDEX idx_type_time (backup_type, completed_at),
    INDEX idx_schedule (schedule_type)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '备份任务表';

-- 6.9 恢复任务表
CREATE TABLE IF NOT EXISTS restore_job (
    job_id             VARCHAR(64)       NOT NULL COMMENT '恢复任务ID',
    job_name           VARCHAR(255)      NOT NULL COMMENT '恢复任务名称',
    
    -- 关联备份
    backup_job_id      VARCHAR(64)       NOT NULL COMMENT '源备份ID',
    backup_file_ref    VARCHAR(512)       NOT NULL COMMENT '备份文件引用',
    backup_timestamp   DATETIME(3)       NOT NULL COMMENT '备份时间点',
    
    -- 恢复范围
    restore_scope      JSON              NOT NULL COMMENT '恢复范围',
    restore_mode       ENUM('overwrite', 'merge', 'verify_only') NOT NULL DEFAULT 'overwrite',
    
    -- 目标
    target_vhost       VARCHAR(128)       DEFAULT NULL COMMENT '恢复到指定VHost',
    target_node        VARCHAR(128)       DEFAULT NULL COMMENT '恢复到指定节点',
    
    -- 状态
    status              ENUM('pending', 'preparing', 'running', 'completed', 'failed', 'rolled_back') 
                      DEFAULT 'pending',
    progress_percent    DECIMAL(5,2)     DEFAULT 0 COMMENT '进度百分比',
    
    -- 结果
    messages_restored   BIGINT            DEFAULT NULL COMMENT '恢复消息数',
    duration_seconds   INT               DEFAULT NULL COMMENT '恢复耗时(秒)',
    started_at         DATETIME(3)       DEFAULT NULL COMMENT '开始时间',
    completed_at       DATETIME(3)       DEFAULT NULL COMMENT '完成时间',
    
    -- 验证
    verified            BOOLEAN           DEFAULT FALSE COMMENT '是否验证成功',
    verification_detail TEXT              DEFAULT NULL COMMENT '验证详情',
    
    -- 回滚
    rollback_available  BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否可回滚',
    rolled_back         BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否已回滚',
    
    PRIMARY KEY (job_id),
    INDEX idx_backup (backup_job_id),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '恢复任务表';

-- 6.10 灾难恢复计划表
CREATE TABLE IF NOT EXISTS disaster_recovery_plan (
    plan_id            VARCHAR(64)       NOT NULL COMMENT '计划ID',
    plan_name          VARCHAR(255)      NOT NULL COMMENT '计划名称',
    
    -- 目标
    rto_minutes        INT               NOT NULL COMMENT '恢复时间目标(分钟)',
    rpo_minutes        INT               NOT NULL COMMENT '数据恢复点目标(分钟)',
    
    -- 站点
    primary_site        VARCHAR(128)      NOT NULL COMMENT '主站点',
    secondary_site      VARCHAR(128)      NOT NULL COMMENT '备站点',
    site_type          ENUM('active', 'passive', 'active_active') DEFAULT 'passive',
    
    -- 复制配置
    replication_type   ENUM('sync', 'async', 'crossover') NOT NULL DEFAULT 'async',
    replication_lag_seconds INT          DEFAULT 60 COMMENT '复制滞后容忍(秒)',
    
    -- 切换配置
    auto_failover_enabled BOOLEAN       NOT NULL DEFAULT FALSE COMMENT '是否启用自动切换',
    failover_trigger   VARCHAR(512)      DEFAULT NULL COMMENT '触发条件',
    
    -- 状态
    status             ENUM('draft', 'active', 'testing', 'suspended') DEFAULT 'draft',
    last_tested_at     DATETIME(3)       DEFAULT NULL COMMENT '最后测试时间',
    last_failover_at  DATETIME(3)       DEFAULT NULL COMMENT '最后切换时间',
    
    -- 步骤
    recovery_steps     JSON              NOT NULL COMMENT '恢复步骤定义',
    /*
    [
      {"step": 1, "action": "activate_site", "target": "secondary_site"},
      {"step": 2, "action": "dns_switch", "delay_seconds": 10},
      {"step": 3, "action": "verify_services", "timeout_seconds": 300}
    ]
    */
    
    -- 联系人
    contacts           JSON              DEFAULT NULL COMMENT '应急联系人列表',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (plan_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '灾难恢复计划表';

-- 6.11 容量规划表
CREATE TABLE IF NOT EXISTS capacity_plan (
    plan_id            VARCHAR(64)       NOT NULL COMMENT '规划ID',
    vhost              VARCHAR(128)      DEFAULT NULL COMMENT '虚拟主机',
    
    -- 业务预测
    forecast_period_start DATE          NOT NULL COMMENT '预测起始日期',
    forecast_period_end   DATE          NOT NULL COMMENT '预测结束日期',
    
    -- 消息量预测
    expected_msg_per_sec  DECIMAL(12,2) DEFAULT NULL COMMENT '预期消息速率(/秒)',
    expected_bytes_per_sec DECIMAL(12,2) DEFAULT NULL COMMENT '预期字节速率(/秒)',
    expected_peak_ratio DECIMAL(5,2)   DEFAULT 3.0 COMMENT '峰值倍率',
    expected_msg_size_avg_bytes BIGINT DEFAULT NULL COMMENT '平均消息大小',
    
    -- 存储需求
    expected_storage_gb  DECIMAL(10,2)  DEFAULT NULL COMMENT '预期存储需求(GB)',
    retention_hours     INT               DEFAULT NULL COMMENT '消息保留时长(小时)',
    storage_growth_rate DECIMAL(5,2)   DEFAULT NULL COMMENT '存储月增长率(%)',
    
    -- 连接数预测
    expected_connections INT            DEFAULT NULL COMMENT '预期连接数',
    expected_consumers   INT            DEFAULT NULL COMMENT '预期消费者数',
    expected_producers   INT            DEFAULT NULL COMMENT '预期生产者数',
    
    -- 资源需求
    required_cpu_cores   INT            DEFAULT NULL COMMENT '所需CPU核心数',
    required_memory_gb   DECIMAL(10,2) DEFAULT NULL COMMENT '所需内存(GB)',
    required_disk_gb     DECIMAL(10,2) DEFAULT NULL COMMENT '所需磁盘(GB)',
    required_network_mbps BIGINT        DEFAULT NULL COMMENT '所需网络带宽(Mbps)',
    
    -- 节点规划
    recommended_nodes    INT            DEFAULT NULL COMMENT '建议节点数',
    node_spec           JSON            DEFAULT NULL COMMENT '节点规格',
    /*
    {
      "cpu": "8c",
      "memory": "32GiB",
      "disk": "500GB SSD",
      "network": "1Gbps"
    }
    */
    
    -- 安全水位
    safety_margin_pct    DECIMAL(5,2)   DEFAULT 30 COMMENT '安全余量(%)',
    
    -- 状态
    status             ENUM('draft', 'approved', 'active', 'expired') DEFAULT 'draft',
    approved_by        VARCHAR(128)      DEFAULT NULL COMMENT '审批人',
    approved_at        DATETIME(3)       DEFAULT NULL COMMENT '审批时间',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (plan_id),
    INDEX idx_period (forecast_period_start, forecast_period_end),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '容量规划表';

-- 6.12 弹性伸缩策略表
CREATE TABLE IF NOT EXISTS auto_scaling_policy (
    policy_id          VARCHAR(64)       NOT NULL COMMENT '策略ID',
    vhost              VARCHAR(128)      DEFAULT NULL COMMENT '虚拟主机',
    
    -- 伸缩类型
    scaling_type       ENUM('horizontal', 'vertical') NOT NULL COMMENT '伸缩类型',
    scaling_direction  ENUM('up', 'down', 'both') NOT NULL DEFAULT 'both',
    
    -- 触发条件
    trigger_metrics    JSON              NOT NULL COMMENT '触发指标',
    /*
    [
      {"metric": "cpu_usage", "operator": ">", "threshold": 75, "duration_seconds": 300},
      {"metric": "queue_depth", "operator": ">", "threshold": 100000, "duration_seconds": 60},
      {"metric": "consumer_lag", "operator": ">", "threshold": 50000, "duration_seconds": 120}
    ]
    */
    
    -- 伸缩配置
    min_nodes          INT               DEFAULT 3 COMMENT '最小节点数',
    max_nodes          INT               DEFAULT 20 COMMENT '最大节点数',
    scale_step         INT               DEFAULT 1 COMMENT '每次伸缩步长(节点)',
    cooldown_seconds   INT               NOT NULL DEFAULT 300 COMMENT '冷却时间(秒)',
    
    -- 垂直伸缩
    resource_adjustment JSON             DEFAULT NULL COMMENT '资源调整规则',
    /*
    {
      "memory_gb": {"min": 8, "max": 64, "step": 8},
      "cpu_cores": {"min": 4, "max": 32, "step": 4}
    }
    */
    
    -- 预测伸缩
    predictive_enabled  BOOLEAN          DEFAULT FALSE COMMENT '是否启用预测伸缩',
    look_ahead_minutes INT               DEFAULT 30 COMMENT '预测前置时间(分钟)',
    prediction_model   VARCHAR(128)      DEFAULT NULL COMMENT '预测模型名称',
    
    -- 状态
    enabled            BOOLEAN           NOT NULL DEFAULT TRUE,
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (policy_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '弹性伸缩策略表';

-- =============================================
-- 7. 队列与路由
-- =============================================

-- 7.1 交换机运行时统计表
CREATE TABLE IF NOT EXISTS exchange_stats (
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

-- 7.2 路由规则表
CREATE TABLE IF NOT EXISTS routing_rule (
    rule_id            VARCHAR(64)       NOT NULL COMMENT '规则ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    exchange_name      VARCHAR(255)      NOT NULL COMMENT '交换机名称',
    
    -- 规则定义
    rule_name          VARCHAR(255)      NOT NULL COMMENT '规则名称',
    rule_type          ENUM('exact', 'prefix', 'suffix', 'wildcard', 'regex', 'composite') 
                      NOT NULL DEFAULT 'exact' COMMENT '规则类型',
    pattern            VARCHAR(1024)     NOT NULL COMMENT '匹配模式',
    
    -- 目标
    target_queue       VARCHAR(255)      NOT NULL COMMENT '目标队列',
    priority           INT               NOT NULL DEFAULT 0 COMMENT '规则优先级(高优先级先匹配)',
    
    -- 条件
    condition_headers  JSON             DEFAULT NULL COMMENT '附加头条件',
    condition_script    TEXT             DEFAULT NULL COMMENT '条件脚本(可选)',
    
    -- 状态
    active             BOOLEAN           NOT NULL DEFAULT TRUE,
    
    -- 统计
    match_count        BIGINT            NOT NULL DEFAULT 0 COMMENT '匹配次数',
    last_match_at      DATETIME(3)       DEFAULT NULL COMMENT '最后匹配时间',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (rule_id),
    INDEX idx_exchange (exchange_name),
    INDEX idx_target (target_queue),
    INDEX idx_priority (exchange_name, priority DESC)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '路由规则表';

-- 7.3 死信队列配置表
CREATE TABLE IF NOT EXISTS dlx_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    
    -- 死信交换机
    dlx_exchange_name  VARCHAR(255)      NOT NULL COMMENT '死信交换机名称',
    dlx_exchange_type  ENUM('direct', 'fanout', 'topic') DEFAULT 'fanout' COMMENT '死信交换机类型',
    dlx_routing_key    VARCHAR(1024)     DEFAULT NULL COMMENT '死信路由键模板',
    
    -- 关联源队列
    source_queue_id    VARCHAR(64)       DEFAULT NULL COMMENT '关联的源队列ID(NULL表示全局)',
    source_queue_name  VARCHAR(255)      DEFAULT NULL COMMENT '关联的源队列名称',
    
    -- 重投策略
    max_redeliveries   INT               NOT NULL DEFAULT 10 COMMENT '最大重投次数',
    retry_strategy     ENUM('fixed', 'exponential', 'custom') DEFAULT 'exponential' COMMENT '重试策略',
    retry_delay_ms     BIGINT            NOT NULL DEFAULT 5000 COMMENT '重试延迟(毫秒)',
    retry_multiplier    DECIMAL(5,2)     DEFAULT 2.0 COMMENT '指数退避乘数',
    max_retry_delay_ms BIGINT            NOT NULL DEFAULT 3600000 COMMENT '最大重试延迟(1小时)',
    
    -- 自动处理
    auto_reprocess      BOOLEAN          NOT NULL DEFAULT FALSE COMMENT '是否自动重新处理',
    reprocess_delay_ms  BIGINT           DEFAULT NULL COMMENT '自动重新处理延迟',
    
    -- 告警
    alert_enabled      BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否启用死信告警',
    alert_threshold     INT              DEFAULT 100 COMMENT '告警阈值(死信数)',
    alert_channels     JSON             DEFAULT NULL COMMENT '告警通知渠道',
    
    -- 状态
    status             ENUM('active', 'paused') DEFAULT 'active',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (config_id),
    UNIQUE KEY uk_vhost_exchange (vhost, dlx_exchange_name),
    INDEX idx_source_queue (source_queue_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '死信队列配置表';

-- 7.4 死信消息记录表
CREATE TABLE IF NOT EXISTS dlx_message (
    dlx_record_id      VARCHAR(64)       NOT NULL COMMENT '死信记录ID',
    original_message_id VARCHAR(64)      NOT NULL COMMENT '原始消息ID',
    
    -- 来源信息
    source_exchange    VARCHAR(255)      NOT NULL COMMENT '原始交换机',
    source_queue       VARCHAR(255)      NOT NULL COMMENT '原始队列',
    source_routing_key VARCHAR(1024)     NOT NULL COMMENT '原始路由键',
    source_consumer_id VARCHAR(64)       DEFAULT NULL COMMENT '最后处理该消息的消费者ID',
    
    -- 死信原因
    dead_reason        ENUM('rejected', 'expired', 'max_redeliveries', 'queue_full', 'consumer_crash', 'invalid_payload') 
                      NOT NULL COMMENT '死信原因',
    error_message      TEXT              DEFAULT NULL COMMENT '错误详情',
    
    -- 消息快照(用于人工排查)
    message_headers    JSON             DEFAULT NULL COMMENT '原始消息头快照',
    payload_preview    VARCHAR(1024)     DEFAULT NULL COMMENT '消息体预览',
    
    -- 重投信息
    redelivery_count   INT               NOT NULL DEFAULT 0 COMMENT '累计重投次数',
    next_retry_at      DATETIME(3)       DEFAULT NULL COMMENT '下次重试时间',
    
    -- 处理状态
    status             ENUM('pending', 'retrying', 'reprocessed', 'archived', 'discarded') DEFAULT 'pending',
    resolution         VARCHAR(512)      DEFAULT NULL COMMENT '处理结果说明',
    resolved_by        VARCHAR(128)      DEFAULT NULL COMMENT '处理人(系统或人工)',
    resolved_at        DATETIME(3)       DEFAULT NULL COMMENT '处理时间',
    
    -- 审计
    first_failed_at    DATETIME(3)       NOT NULL COMMENT '首次失败时间',
    dead_at            DATETIME(3)       NOT NULL COMMENT '进入死信时间',
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (dlx_record_id),
    INDEX idx_original_message (original_message_id),
    INDEX idx_status (status),
    INDEX idx_reason (dead_reason),
    INDEX idx_source_queue (source_queue),
    INDEX idx_next_retry (status, next_retry_at),
    INDEX idx_dead_at (dead_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '死信消息记录表';

-- 7.5 队列镜像策略表
CREATE TABLE IF NOT EXISTS mirror_policy (
    policy_id          VARCHAR(64)       NOT NULL COMMENT '策略ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    pattern            VARCHAR(255)      NOT NULL COMMENT '队列名称匹配模式(正则)',
    
    -- 镜像配置
    ha_mode            ENUM('all', 'exactly', 'nodes') NOT NULL COMMENT 'HA模式',
    ha_sync_mode       ENUM('automatic', 'manual', 'queued') NOT NULL DEFAULT 'automatic' COMMENT '同步模式',
    ha_sync_batch_size INT               NOT NULL DEFAULT 4096 COMMENT '同步批次大小',
    
    -- HA Mode 参数
    ha_promote_on_shutdown ENUM('always', 'when_synced', 'manual') DEFAULT 'when_synced' COMMENT '关闭时提升策略',
    ha_node_count       INT              DEFAULT NULL COMMENT '镜像节点数(exactly模式)',
    target_nodes        JSON             DEFAULT NULL COMMENT '目标节点列表(nodes模式)',
    
    -- 状态
    status             ENUM('active', 'paused', 'deleted') DEFAULT 'active',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (policy_id),
    UNIQUE KEY uk_vhost_pattern (vhost, pattern),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '队列镜像策略表';

-- 7.6 镜像副本状态表
CREATE TABLE IF NOT EXISTS mirror_replica (
    replica_id         VARCHAR(64)       NOT NULL COMMENT '副本ID',
    queue_id           VARCHAR(64)       NOT NULL COMMENT '队列ID',
    node_name          VARCHAR(128)      NOT NULL COMMENT '节点名称',
    
    -- 角色与状态
    role               ENUM('master', 'slave', 'recovering') NOT NULL COMMENT '角色',
    sync_status        ENUM('synced', 'unsynced', 'syncing', 'offline') NOT NULL COMMENT '同步状态',
    is_active          BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否活跃',
    
    -- 同步进度
    sync_progress      DECIMAL(5,2)      DEFAULT NULL COMMENT '同步进度(%)',
    last_sync_at       DATETIME(3)       DEFAULT NULL COMMENT '最后同步时间',
    sync_lag_bytes     BIGINT            NOT NULL DEFAULT 0 COMMENT '同步落后字节数',
    sync_lag_messages  BIGINT            NOT NULL DEFAULT 0 COMMENT '同步落后消息数',
    
    -- 统计
    messages_stored    BIGINT            NOT NULL DEFAULT 0 COMMENT '存储消息数',
    bytes_stored       BIGINT            NOT NULL DEFAULT 0 COMMENT '存储字节数',
    
    -- 审计
    joined_at          DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '加入时间',
    promoted_at        DATETIME(3)       DEFAULT NULL COMMENT '提升为主节点时间',
    left_at            DATETIME(3)       DEFAULT NULL COMMENT '离开时间',
    
    PRIMARY KEY (replica_id),
    UNIQUE KEY uk_queue_node (queue_id, node_name),
    INDEX idx_node (node_name, role),
    INDEX idx_sync_status (sync_status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '镜像副本状态表';

-- =============================================
-- 8. 消费者管理
-- =============================================

-- 8.1 消费者注册表
CREATE TABLE IF NOT EXISTS consumer_registration (
    registration_id    VARCHAR(64)       NOT NULL COMMENT '注册ID',
    consumer_tag       VARCHAR(255)      NOT NULL COMMENT '消费者标签',
    
    -- 连接信息
    connection_id      VARCHAR(64)       NOT NULL COMMENT '连接ID',
    channel_id         VARCHAR(64)       DEFAULT NULL COMMENT '信道ID',
    node_name          VARCHAR(128)      NOT NULL COMMENT '所在节点',
    remote_address     VARCHAR(45)       DEFAULT NULL COMMENT '客户端地址(IP:Port)',
    
    -- 客户端信息
    client_name        VARCHAR(255)      DEFAULT NULL COMMENT '客户端名称',
    client_version     VARCHAR(64)       DEFAULT NULL COMMENT '客户端版本',
    client_os          VARCHAR(128)      DEFAULT NULL COMMENT '客户端操作系统',
    client_language    VARCHAR(64)       DEFAULT NULL COMMENT '客户端编程语言',
    protocol           ENUM('amqp', 'mqtt', 'http', 'custom') DEFAULT 'amqp' COMMENT '协议类型',
    protocol_version   VARCHAR(16)       DEFAULT NULL COMMENT '协议版本',
    
    -- 用户信息
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    username           VARCHAR(128)      DEFAULT NULL COMMENT '认证用户名',
    
    -- 注册时间
    registered_at      DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '注册时间',
    last_heartbeat_at  DATETIME(3)       DEFAULT NULL COMMENT '最后心跳',
    heartbeat_timeout  INT               NOT NULL DEFAULT 60 COMMENT '心跳超时(秒)',
    
    -- 状态
    status             ENUM('active', 'idle', 'blocked', 'disconnected') DEFAULT 'active',
    
    PRIMARY KEY (registration_id),
    UNIQUE KEY uk_connection_tag (connection_id, consumer_tag),
    INDEX idx_node (node_name),
    INDEX idx_vhost (vhost),
    INDEX idx_status (status),
    INDEX idx_heartbeat (last_heartbeat_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消费者注册表';

-- 8.2 消费者心跳记录表
CREATE TABLE IF NOT EXISTS consumer_heartbeat (
    id                 BIGINT            NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    consumer_id        VARCHAR(64)       NOT NULL COMMENT '消费者ID',
    node_name          VARCHAR(128)      NOT NULL COMMENT '节点名称',
    heartbeat_time     DATETIME(3)       NOT NULL COMMENT '心跳时间',
    rtt_ms             DECIMAL(10,2)     DEFAULT NULL COMMENT '往返时延(毫秒)',
    
    PRIMARY KEY (id),
    INDEX idx_consumer_time (consumer_id, heartbeat_time),
    INDEX idx_node (node_name, heartbeat_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消费者心跳记录表';

-- 8.3 消费模式配置表
CREATE TABLE IF NOT EXISTS consume_mode_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    consumer_id        VARCHAR(64)       NOT NULL COMMENT '消费者ID',
    queue_id           VARCHAR(64)       NOT NULL COMMENT '队列ID',
    
    -- 消费模式
    consume_mode       ENUM('pull', 'push', 'streaming') NOT NULL COMMENT '消费模式',
    
    -- Pull 模式配置
    pull_batch_size    INT               DEFAULT 10 COMMENT '拉取批量大小',
    pull_max_wait_ms   INT               DEFAULT 5000 COMMENT '最大等待时间(毫秒)',
    pull_timeout_ms    INT               DEFAULT 30000 COMMENT '拉取超时(毫秒)',
    
    -- Push 模式配置
    push_prefetch_count INT              DEFAULT 10 COMMENT '预取数量',
    push_prefetch_size  INT              DEFAULT 0 COMMENT '预取大小(字节,0=无限制)',
    
    -- Streaming 模式配置
    stream_start_offset BIGINT           DEFAULT NULL COMMENT '起始偏移量',
    stream_commit_mode ENUM('auto', 'manual') DEFAULT 'auto' COMMENT '提交模式',
    stream_commit_interval_ms BIGINT     DEFAULT 5000 COMMENT '自动提交间隔',
    
    -- 确认模式
    ack_mode           ENUM('auto', 'manual', 'transactional') DEFAULT 'manual' COMMENT '确认模式',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (config_id),
    UNIQUE KEY uk_consumer_queue (consumer_id, queue_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消费模式配置表';

-- 8.4 消费偏移量明细表
CREATE TABLE IF NOT EXISTS consumer_offset_detail (
    offset_id          VARCHAR(64)       NOT NULL COMMENT '偏移量ID',
    consumer_group_id  VARCHAR(64)       NOT NULL COMMENT '消费者分组ID',
    topic_id           VARCHAR(64)       NOT NULL COMMENT '主题ID',
    partition_id       INT               NOT NULL DEFAULT 0 COMMENT '分区ID',
    
    -- 偏移量
    current_offset     BIGINT            NOT NULL DEFAULT -1 COMMENT '已提交的偏移量(-1=未消费)',
    pending_offset     BIGINT            DEFAULT NULL COMMENT '待确认的最大偏移量(in-flight)',
    committed_offset   BIGINT            NOT NULL DEFAULT -1 COMMENT '最终确认偏移量',
    
    -- Epoch 版本(用于并发控制)
    epoch              BIGINT            NOT NULL DEFAULT 0 COMMENT '偏移量版本号',
    
    -- 消费进度
    lag                BIGINT            NOT NULL DEFAULT 0 COMMENT '消费滞后量',
    last_commit_time   DATETIME(3)       DEFAULT NULL COMMENT '最后提交时间',
    last_consume_time  DATETIME(3)       DEFAULT NULL COMMENT '最后消费时间',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (offset_id),
    UNIQUE KEY uk_group_topic_partition (consumer_group_id, topic_id, partition_id),
    INDEX idx_topic_partition (topic_id, partition_id),
    INDEX idx_lag (lag)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消费偏移量明细表';

-- 8.5 偏移量变更历史表
CREATE TABLE IF NOT EXISTS offset_history (
    history_id         BIGINT            NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    consumer_group_id  VARCHAR(64)       NOT NULL COMMENT '消费者分组ID',
    topic_id           VARCHAR(64)       NOT NULL COMMENT '主题ID',
    partition_id       INT               NOT NULL DEFAULT 0,
    
    -- 变更
    from_offset        BIGINT            NOT NULL COMMENT '变更前偏移量',
    to_offset          BIGINT            NOT NULL COMMENT '变更后偏移量',
    commit_type        ENUM('auto', 'manual', 'admin') NOT NULL COMMENT '提交类型',
    
    -- 上下文
    consumer_id        VARCHAR(64)       DEFAULT NULL COMMENT '实际提交的消费者ID',
    node_name          VARCHAR(128)      DEFAULT NULL COMMENT '提交所在节点',
    
    -- 时间
    commit_time        DATETIME(3)       NOT NULL COMMENT '提交时间',
    
    PRIMARY KEY (history_id),
    INDEX idx_group (consumer_group_id),
    INDEX idx_topic (topic_id, partition_id),
    INDEX idx_commit_time (commit_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '偏移量变更历史表';

-- 8.6 消息投递记录表
CREATE TABLE IF NOT EXISTS delivery_record (
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

-- 8.7 消费者分组表
CREATE TABLE IF NOT EXISTS consumer_group (
    group_id           VARCHAR(64)       NOT NULL COMMENT '分组ID',
    group_name         VARCHAR(255)      NOT NULL COMMENT '分组名称',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    
    -- 分组配置
    rebalance_strategy ENUM('range', 'roundrobin', 'sticky', 'cooperative_sticky') 
                      NOT NULL DEFAULT 'range' COMMENT '重平衡策略',
    max_members        INT               DEFAULT NULL COMMENT '最大成员数，NULL不限',
    min_members        INT               DEFAULT 1 COMMENT '最小成员数',
    
    -- 订阅
    subscribed_topics   JSON             DEFAULT NULL COMMENT '订阅的主题ID列表',
    subscribed_queues   JSON             DEFAULT NULL COMMENT '订阅的队列ID列表',
    
    -- 状态
    status             ENUM('active', 'empty', 'preparing_rebalance', 'stable', 'dead') 
                      DEFAULT 'active',
    member_count       INT               NOT NULL DEFAULT 0 COMMENT '当前成员数',
    generation_id      BIGINT            NOT NULL DEFAULT 0 COMMENT '代次ID(每次rebalance递增)',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (group_id),
    UNIQUE KEY uk_vhost_name (vhost, group_name),
    INDEX idx_status (status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消费者分组表';

-- 8.8 分组成员表
CREATE TABLE IF NOT EXISTS consumer_group_member (
    member_id          VARCHAR(64)       NOT NULL COMMENT '成员ID',
    group_id           VARCHAR(64)       NOT NULL COMMENT '分组ID',
    consumer_id        VARCHAR(64)       NOT NULL COMMENT '消费者ID',
    
    -- 分配
    assigned_partitions JSON             DEFAULT NULL COMMENT '分配的分区列表',
    assigned_queues     JSON             DEFAULT NULL COMMENT '分配的队列列表',
    
    -- 状态
    status             ENUM('active', 'leaving', 'revoking', 'joined') DEFAULT 'active',
    joined_at          DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    last_heartbeat     DATETIME(3)       DEFAULT NULL,
    
    PRIMARY KEY (member_id),
    UNIQUE KEY uk_group_consumer (group_id, consumer_id),
    INDEX idx_group (group_id, status)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '分组成员表';

-- 8.9 限流配置表
CREATE TABLE IF NOT EXISTS flow_control_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    
    -- 限流维度
    target_type        ENUM('consumer', 'producer', 'queue', 'connection') NOT NULL COMMENT '限流目标类型',
    target_id          VARCHAR(64)       NOT NULL COMMENT '限流目标ID',
    
    -- 限流策略
    throttle_type      ENUM('prefetch', 'rate', 'credit', 'adaptive') NOT NULL COMMENT '限流策略类型',
    
    -- Prefetch 限流
    prefetch_count     INT               DEFAULT 10 COMMENT '预取消息数',
    prefetch_size      INT               DEFAULT 0 COMMENT '预取字节大小',
    
    -- Rate 限流
    max_rate_per_sec   INT               DEFAULT NULL COMMENT '最大速率(条/秒)',
    max_bytes_per_sec  BIGINT            DEFAULT NULL COMMENT '最大速率(字节/秒)',
    
    -- Credit 限流
    initial_credits    INT               DEFAULT 100 COMMENT '初始信用额度',
    credit_refill_rate INT               DEFAULT 50 COMMENT '信用恢复速率(/秒)',
    credit_refill_interval_ms INT        DEFAULT 100 COMMENT '信用恢复间隔(毫秒)',
    
    -- Adaptive 自适应限流
    adaptive_enabled   BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否启用自适应',
    adaptive_max_lag    BIGINT           DEFAULT 10000 COMMENT '最大允许滞后量',
    adaptive_min_lag    BIGINT           DEFAULT 100 COMMENT '最小滞后量(恢复限流)',
    
    -- 背压配置
    backpressure_enabled BOOLEAN         NOT NULL DEFAULT TRUE COMMENT '是否启用背压',
    backpressure_threshold BIGINT        DEFAULT 100000 COMMENT '背压触发阈值',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (config_id),
    UNIQUE KEY uk_target (target_type, target_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '限流配置表';

-- 8.10 限流运行时状态表
CREATE TABLE IF NOT EXISTS flow_control_state (
    state_id           VARCHAR(64)       NOT NULL COMMENT '状态ID',
    target_type        ENUM('consumer', 'producer', 'queue', 'connection') NOT NULL,
    target_id          VARCHAR(64)       NOT NULL COMMENT '目标ID',
    
    -- 当前状态
    is_throttled       BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否正在限流',
    throttle_start_at  DATETIME(3)       DEFAULT NULL COMMENT '限流开始时间',
    
    -- 指标
    current_rate       DECIMAL(10,2)     DEFAULT 0 COMMENT '当前速率',
    allowed_rate       DECIMAL(10,2)     DEFAULT 0 COMMENT '允许速率',
    
    -- Credit
    available_credits  INT               NOT NULL DEFAULT 100 COMMENT '可用信用',
    
    -- 背压
    backpressure_active BOOLEAN          NOT NULL DEFAULT FALSE COMMENT '背压是否激活',
    current_lag        BIGINT            NOT NULL DEFAULT 0 COMMENT '当前滞后量',
    
    -- 审计
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (state_id),
    UNIQUE KEY uk_target (target_type, target_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '限流运行时状态表';

-- 8.11 连接池配置表
CREATE TABLE IF NOT EXISTS connection_pool_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/' COMMENT '虚拟主机',
    
    -- 池配置
    pool_type          ENUM('consumer', 'producer', 'shared') NOT NULL COMMENT '池类型',
    owner_id           VARCHAR(64)       DEFAULT NULL COMMENT '拥有者ID(NULL表示全局)',
    
    -- 容量配置
    min_idle           INT               NOT NULL DEFAULT 5 COMMENT '最小空闲连接数',
    max_idle           INT               NOT NULL DEFAULT 20 COMMENT '最大空闲连接数',
    max_total          INT               NOT NULL DEFAULT 100 COMMENT '最大总连接数',
    max_wait_ms        INT               NOT NULL DEFAULT 30000 COMMENT '获取连接最大等待(毫秒)',
    
    -- 生命周期
    connection_timeout_ms INT            NOT NULL DEFAULT 10000 COMMENT '连接建立超时',
    idle_timeout_ms    INT               NOT NULL DEFAULT 300000 COMMENT '空闲超时(毫秒,5分钟)',
    max_lifetime_ms    INT               NOT NULL DEFAULT 1800000 COMMENT '连接最大生命周期(30分钟)',
    
    -- 心跳
    heartbeat_interval INT               NOT NULL DEFAULT 30 COMMENT '心跳间隔(秒)',
    heartbeat_timeout  INT               NOT NULL DEFAULT 60 COMMENT '心跳超时(秒)',
    
    -- 状态
    enabled            BOOLEAN           NOT NULL DEFAULT TRUE,
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (config_id),
    UNIQUE KEY uk_type_owner (pool_type, owner_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '连接池配置表';

-- 8.12 连接池运行时统计表
CREATE TABLE IF NOT EXISTS connection_pool_stats (
    stat_id           BIGINT            NOT NULL AUTO_INCREMENT COMMENT '统计ID',
    config_id         VARCHAR(64)       NOT NULL COMMENT '连接池配置ID',
    node_name         VARCHAR(128)      NOT NULL COMMENT '节点名称',
    stat_time         DATETIME(3)       NOT NULL COMMENT '统计时间点',
    
    -- 连接状态
    total_connections INT               NOT NULL DEFAULT 0 COMMENT '当前总连接数',
    active_connections INT              NOT NULL DEFAULT 0 COMMENT '活跃连接数',
    idle_connections  INT              NOT NULL DEFAULT 0 COMMENT '空闲连接数',
    waiting_requests  INT               NOT NULL DEFAULT 0 COMMENT '等待获取连接的请求数',
    
    -- 性能指标
    borrow_count      BIGINT            NOT NULL DEFAULT 0 COMMENT '累计借用次数',
    return_count      BIGINT            NOT NULL DEFAULT 0 COMMENT '累计归还次数',
    timeout_count     BIGINT            NOT NULL DEFAULT 0 COMMENT '获取超时次数',
    borrow_latency_avg_ms DECIMAL(10,2) DEFAULT NULL COMMENT '平均借用延迟(毫秒)',
    
    -- 错误统计
    connection_errors BIGINT            NOT NULL DEFAULT 0 COMMENT '连接错误次数',
    validation_errors BIGINT            NOT NULL DEFAULT 0 COMMENT '验证失败次数',
    
    PRIMARY KEY (stat_id),
    UNIQUE KEY uk_config_node_time (config_id, node_name, stat_time),
    INDEX idx_stat_time (stat_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '连接池运行时统计表';

-- 8.13 信道池配置表
CREATE TABLE IF NOT EXISTS channel_pool_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    connection_id      VARCHAR(64)       NOT NULL COMMENT '所属连接ID',
    
    -- 容量
    max_channels       INT               NOT NULL DEFAULT 256 COMMENT '最大信道数',
    max_wait_channels  INT              NOT NULL DEFAULT 50 COMMENT '等待获取信道最大数',
    
    -- 复用策略
    reuse_strategy     ENUM('fifo', 'lru', 'random') DEFAULT 'lru' COMMENT '信道复用策略',
    channel_idle_timeout_ms INT         DEFAULT 60000 COMMENT '信道空闲超时(毫秒)',
    enable_multiplex   BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否启用多路复用',
    
    -- 预热
    prewarm_enabled    BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否预热',
    prewarm_count      INT               DEFAULT 10 COMMENT '预热信道数',
    
    PRIMARY KEY (config_id),
    UNIQUE KEY uk_connection (connection_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '信道池配置表';

-- 8.14 消息重投策略表
CREATE TABLE IF NOT EXISTS redelivery_policy (
    policy_id          VARCHAR(64)       NOT NULL COMMENT '策略ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    queue_id           VARCHAR(64)       DEFAULT NULL COMMENT '队列ID(NULL表示全局)',
    
    -- 重投配置
    max_redeliveries   INT               NOT NULL DEFAULT 10 COMMENT '最大重投次数',
    retry_strategy     ENUM('fixed', 'linear', 'exponential', 'fibonacci', 'custom') 
                      NOT NULL DEFAULT 'exponential' COMMENT '重试策略',
    
    -- 固定间隔
    fixed_delay_ms     BIGINT            DEFAULT 1000 COMMENT '固定重投延迟(毫秒)',
    
    -- 线性退避
    linear_delay_base_ms BIGINT          DEFAULT 1000 COMMENT '线性退避初始延迟',
    linear_delay_max_ms BIGINT          DEFAULT 60000 COMMENT '线性退避最大延迟',
    
    -- 指数退避
    exp_delay_initial_ms BIGINT          DEFAULT 1000 COMMENT '指数退避初始延迟(毫秒)',
    exp_delay_multiplier DECIMAL(5,2)   DEFAULT 2.0 COMMENT '指数退避乘数',
    exp_delay_max_ms    BIGINT          DEFAULT 3600000 COMMENT '指数退避最大延迟(1小时)',
    
    -- 自定义间隔
    custom_delays_ms   JSON              DEFAULT NULL COMMENT '自定义间隔列表(毫秒)',
    
    -- 触发条件
    trigger_on_timeout BOOLEAN          NOT NULL DEFAULT TRUE COMMENT '超时触发重投',
    trigger_on_nack    BOOLEAN           NOT NULL DEFAULT TRUE COMMENT 'NACK触发重投',
    trigger_on_reject   BOOLEAN          NOT NULL DEFAULT TRUE COMMENT 'Reject触发重投',
    
    -- 状态
    enabled            BOOLEAN           NOT NULL DEFAULT TRUE,
    
    PRIMARY KEY (policy_id),
    INDEX idx_queue (queue_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消息重投策略表';

-- 8.15 消息幂等处理记录表(用于去重)
CREATE TABLE IF NOT EXISTS idempotency_record (
    idempotency_key    VARCHAR(255)     NOT NULL COMMENT '幂等键',
    
    -- 关联
    producer_id        VARCHAR(64)       NOT NULL COMMENT '生产者ID',
    destination_type   ENUM('queue', 'topic') NOT NULL COMMENT '目的地类型',
    destination_id     VARCHAR(64)       NOT NULL COMMENT '目的地ID',
    
    -- 处理结果
    original_message_id VARCHAR(64)      NOT NULL COMMENT '原始消息ID',
    result             ENUM('accepted', 'duplicate', 'failed') NOT NULL COMMENT '处理结果',
    processed_at       DATETIME(3)       NOT NULL COMMENT '处理时间',
    
    -- 过期
    expires_at        DATETIME(3)        NOT NULL COMMENT '过期时间(建议保留7天)',
    
    PRIMARY KEY (idempotency_key),
    INDEX idx_producer (producer_id),
    INDEX idx_destination (destination_type, destination_id),
    INDEX idx_expires (expires_at),
    INDEX idx_processed (processed_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '消息幂等处理记录表(用于去重)';

-- =============================================
-- 9. 消息协议
-- =============================================

-- 9.1 AMQP连接表
CREATE TABLE IF NOT EXISTS amqp_connection (
    connection_id       VARCHAR(64)      NOT NULL COMMENT '连接ID',
    
    -- 连接信息
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    remote_address     VARCHAR(45)       NOT NULL COMMENT '远程地址',
    remote_port        INT               NOT NULL COMMENT '远程端口',
    local_address      VARCHAR(45)       DEFAULT NULL COMMENT '本地地址',
    
    -- 客户端
    client_properties  JSON             DEFAULT NULL COMMENT '客户端属性',
    /*
    {
      "product": "MyApp",
      "version": "1.0.0",
      "platform": "Java 17",
      "capabilities": {
        "publisher_confirms": true,
        "consumer_cancel_notify": true
      }
    }
    */
    
    -- 连接配置
    channel_max        INT               DEFAULT 0 COMMENT '最大信道数(0=不限)',
    frame_max          INT               DEFAULT 131072 COMMENT '最大帧大小',
    heartbeat          INT               DEFAULT 0 COMMENT '心跳间隔(秒,0=关闭)',
    
    -- 用户
    username           VARCHAR(128)      NOT NULL COMMENT '认证用户',
    
    -- 状态
    status             ENUM('opening', 'running', 'closing', 'closed') DEFAULT 'opening',
    channels_open      INT               NOT NULL DEFAULT 0 COMMENT '打开的信道数',
    
    -- 审计
    connected_at       DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    disconnected_at     DATETIME(3)      DEFAULT NULL,
    close_reason       VARCHAR(512)      DEFAULT NULL COMMENT '关闭原因',
    
    PRIMARY KEY (connection_id),
    INDEX idx_vhost (vhost),
    INDEX idx_status (status),
    INDEX idx_remote (remote_address),
    INDEX idx_username (username)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'AMQP连接表';

-- 9.2 AMQP信道表
CREATE TABLE IF NOT EXISTS amqp_channel (
    channel_id         VARCHAR(64)       NOT NULL COMMENT '信道ID',
    connection_id      VARCHAR(64)       NOT NULL COMMENT '所属连接ID',
    channel_number     INT               NOT NULL COMMENT '信道编号',
    
    -- 信道状态
    status             ENUM('opening', 'running', 'flow', 'closing', 'closed') DEFAULT 'opening',
    
    -- 事务
    transaction_active BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否有活跃事务',
    transaction_id     VARCHAR(64)       DEFAULT NULL COMMENT '事务ID',
    
    -- 确认
    confirm_mode       BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否开启confirm模式',
    unconfirmed_count  INT               NOT NULL DEFAULT 0 COMMENT '未确认消息数',
    
    -- 消费者
    consumer_count     INT               NOT NULL DEFAULT 0 COMMENT '该信道的消费者数',
    
    -- 审计
    opened_at          DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    closed_at          DATETIME(3)       DEFAULT NULL,
    
    PRIMARY KEY (channel_id),
    UNIQUE KEY uk_connection_number (connection_id, channel_number)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'AMQP信道表';

-- 9.3 MQTT会话表
CREATE TABLE IF NOT EXISTS mqtt_session (
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

-- 9.4 MQTT订阅表
CREATE TABLE IF NOT EXISTS mqtt_subscription (
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

-- 9.5 MQTT保留消息表
CREATE TABLE IF NOT EXISTS mqtt_retained_message (
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

-- 9.6 协议版本表
CREATE TABLE IF NOT EXISTS protocol_version (
    version_id         VARCHAR(64)       NOT NULL COMMENT '版本ID',
    protocol_name      VARCHAR(64)       NOT NULL COMMENT '协议名称(AMQP/MQTT/HTTP)',
    version_number     VARCHAR(32)       NOT NULL COMMENT '版本号(如 0.9.1, 5.0)',
    
    -- 状态
    status             ENUM('supported', 'deprecated', 'removed') NOT NULL DEFAULT 'supported',
    deprecation_date   DATE              DEFAULT NULL COMMENT '废弃日期',
    removal_date       DATE              DEFAULT NULL COMMENT '移除日期',
    
    -- 兼容性
    min_client_version VARCHAR(32)       DEFAULT NULL COMMENT '最低兼容客户端版本',
    max_client_version VARCHAR(32)       DEFAULT NULL COMMENT '最高兼容客户端版本',
    
    -- 功能矩阵
    capabilities       JSON             DEFAULT NULL COMMENT '支持的功能列表',
    limitations        JSON             DEFAULT NULL COMMENT '已知限制',
    
    -- 审计
    added_at           DATE              NOT NULL COMMENT '添加日期',
    
    PRIMARY KEY (version_id),
    UNIQUE KEY uk_protocol_version (protocol_name, version_number)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '协议版本表';

-- 9.7 协议迁移规则表
CREATE TABLE IF NOT EXISTS protocol_migration (
    migration_id       VARCHAR(64)       NOT NULL COMMENT '迁移ID',
    from_protocol      VARCHAR(64)       NOT NULL COMMENT '源协议',
    from_version       VARCHAR(32)       NOT NULL COMMENT '源版本',
    to_protocol        VARCHAR(64)       NOT NULL COMMENT '目标协议',
    to_version         VARCHAR(32)       NOT NULL COMMENT '目标版本',
    
    -- 迁移规则
    field_mappings     JSON             NOT NULL COMMENT '字段映射规则',
    header_transforms  JSON             DEFAULT NULL COMMENT '头转换规则',
    feature_downgrades JSON             DEFAULT NULL COMMENT '功能降级说明',
    
    -- 兼容性提示
    warnings           JSON             DEFAULT NULL COMMENT '兼容性警告',
    
    PRIMARY KEY (migration_id),
    UNIQUE KEY uk_from_to (from_protocol, from_version, to_protocol, to_version)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '协议迁移规则表';

-- 9.8 协议转换网关配置表
CREATE TABLE IF NOT EXISTS gateway_config (
    gateway_id         VARCHAR(64)       NOT NULL COMMENT '网关ID',
    gateway_name       VARCHAR(255)      NOT NULL COMMENT '网关名称',
    
    -- 协议映射
    source_protocol    ENUM('amqp', 'mqtt', 'http', 'kafka', 'custom') NOT NULL COMMENT '源协议',
    target_protocol    ENUM('amqp', 'mqtt', 'http', 'kafka', 'custom') NOT NULL COMMENT '目标协议',
    
    -- 转换规则
    routing_rules      JSON             NOT NULL COMMENT '路由映射规则',
    property_mappings  JSON             DEFAULT NULL COMMENT '属性映射配置',
    header_mappings    JSON             DEFAULT NULL COMMENT '头映射配置',
    payload_transforms  JSON            DEFAULT NULL COMMENT '消息体转换规则',
    
    -- QoS 映射
    qos_mapping        JSON             DEFAULT NULL COMMENT 'QoS等级映射',
    /*
    AMQP → MQTT:
    {
      "durable_true": 1,
      "durable_false": 0
    }
    */
    
    -- 状态
    status             ENUM('active', 'paused', 'disabled') DEFAULT 'active',
    
    -- 统计
    messages_converted BIGINT            NOT NULL DEFAULT 0 COMMENT '累计转换消息数',
    errors             BIGINT            NOT NULL DEFAULT 0 COMMENT '累计转换错误数',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (gateway_id),
    UNIQUE KEY uk_name (gateway_name),
    INDEX idx_protocols (source_protocol, target_protocol)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '协议转换网关配置表';

-- 9.9 网关主题映射表
CREATE TABLE IF NOT EXISTS gateway_mapping (
    mapping_id         VARCHAR(64)       NOT NULL COMMENT '映射ID',
    gateway_id         VARCHAR(64)       NOT NULL COMMENT '网关ID',
    
    -- 映射规则
    source_topic       VARCHAR(1024)     NOT NULL COMMENT '源主题/队列',
    target_topic       VARCHAR(1024)     NOT NULL COMMENT '目标主题/队列',
    direction          ENUM('source_to_target', 'bidirectional') DEFAULT 'source_to_target' COMMENT '方向',
    
    -- 过滤
    filter_expression  VARCHAR(1024)     DEFAULT NULL COMMENT '过滤表达式',
    
    -- 状态
    active             BOOLEAN           NOT NULL DEFAULT TRUE,
    
    PRIMARY KEY (mapping_id),
    INDEX idx_gateway (gateway_id),
    INDEX idx_source (source_topic)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '网关主题映射表';

-- 9.10 AMQP扩展头定义表
CREATE TABLE IF NOT EXISTS amqp_extension_header (
    header_id         VARCHAR(64)       NOT NULL COMMENT '扩展头ID',
    header_name       VARCHAR(128)      NOT NULL COMMENT '扩展头名称',
    header_code       VARCHAR(64)       NOT NULL COMMENT '头代码(如 x-shared-vhost)',
    protocol_version   VARCHAR(16)      NOT NULL COMMENT '适用协议版本',
    
    -- 定义
    data_type         ENUM('boolean', 'int8', 'int16', 'int32', 'int64', 
                           'float', 'double', 'string', 'binary', 'map', 'list') 
                      NOT NULL COMMENT '数据类型',
    is_mandatory      BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否必填',
    default_value     TEXT              DEFAULT NULL COMMENT '默认值',
    valid_range       VARCHAR(256)      DEFAULT NULL COMMENT '有效值范围',
    description        VARCHAR(512)     DEFAULT NULL COMMENT '说明',
    
    -- 兼容性
    deprecated        BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否已废弃',
    replacement_id    VARCHAR(64)       DEFAULT NULL COMMENT '替代扩展头ID',
    
    -- 审计
    created_at        DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at        DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (header_id),
    UNIQUE KEY uk_code_version (header_code, protocol_version),
    INDEX idx_protocol (protocol_version),
    INDEX idx_deprecated (deprecated)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'AMQP扩展头定义表';

-- 9.11 AMQP特性协商记录表
CREATE TABLE IF NOT EXISTS amqp_feature_negotiation (
    negotiation_id    VARCHAR(64)       NOT NULL COMMENT '协商ID',
    connection_id      VARCHAR(64)       NOT NULL COMMENT '连接ID',
    
    -- 协商特性
    feature_name       VARCHAR(128)      NOT NULL COMMENT '特性名称',
    feature_version    VARCHAR(32)      NOT NULL COMMENT '特性版本',
    
    -- 协商状态
    client_supported   BOOLEAN          NOT NULL COMMENT '客户端是否支持',
    server_supported   BOOLEAN          NOT NULL COMMENT '服务端是否支持',
    negotiated         BOOLEAN          NOT NULL DEFAULT FALSE COMMENT '是否协商成功',
    negotiated_value   TEXT              DEFAULT NULL COMMENT '协商后的值',
    
    -- 优先级
    priority          INT               NOT NULL DEFAULT 0 COMMENT '协商优先级',
    
    -- 审计
    negotiated_at      DATETIME(3)       NOT NULL COMMENT '协商时间',
    
    PRIMARY KEY (negotiation_id),
    INDEX idx_connection (connection_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'AMQP特性协商记录表';

-- 9.12 AMQP信道流控状态表
CREATE TABLE IF NOT EXISTS amqp_flow_control (
    flow_id           VARCHAR(64)       NOT NULL COMMENT '流控ID',
    channel_id        VARCHAR(64)       NOT NULL COMMENT '信道ID',
    
    -- 令牌桶配置
    token_bucket_enabled BOOLEAN         NOT NULL DEFAULT FALSE COMMENT '是否启用令牌桶',
    token_rate         INT               NOT NULL DEFAULT 0 COMMENT '令牌产生速率(个/秒)',
    bucket_capacity    INT               NOT NULL DEFAULT 0 COMMENT '令牌桶容量',
    available_tokens   INT               NOT NULL DEFAULT 0 COMMENT '当前可用令牌数',
    
    -- 信用控制
    credit_mode       ENUM('none', 'prefetch', 'window') NOT NULL DEFAULT 'prefetch' COMMENT '信用模式',
    credit_value       INT               NOT NULL DEFAULT 10 COMMENT '信用额度',
    
    -- 主动关闭
    drain_enabled     BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否启用主动排空',
    
    -- 状态
    is_blocked        BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '信道是否阻塞',
    blocked_reason     VARCHAR(512)      DEFAULT NULL COMMENT '阻塞原因',
    
    -- 审计
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (flow_id),
    UNIQUE KEY uk_channel (channel_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'AMQP信道流控状态表';

-- 9.13 WebSocket会话表
CREATE TABLE IF NOT EXISTS websocket_session (
    session_id         VARCHAR(64)       NOT NULL COMMENT '会话ID',
    
    -- 连接信息
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    user_id            VARCHAR(64)       DEFAULT NULL COMMENT '用户ID',
    remote_address     VARCHAR(45)       NOT NULL COMMENT '客户端IP',
    user_agent         VARCHAR(512)      DEFAULT NULL COMMENT 'User-Agent',
    
    -- 协议
    protocol_version   VARCHAR(32)       DEFAULT '13' COMMENT 'WebSocket版本',
    subprotocol        VARCHAR(128)      DEFAULT NULL COMMENT '子协议(如 wamp)',
    
    -- 订阅
    subscriptions      JSON             DEFAULT NULL COMMENT '订阅的队列/主题列表',
    /*
    示例: [
      {"type": "queue", "id": "xxx", "filter": "*"},
      {"type": "topic", "id": "yyy", "filter": "order.*"}
    ]
    */
    
    -- 连接状态
    connected_at       DATETIME(3)       NOT NULL COMMENT '连接时间',
    last_message_at    DATETIME(3)       DEFAULT NULL COMMENT '最后消息时间',
    disconnected_at    DATETIME(3)       DEFAULT NULL COMMENT '断开时间',
    close_code         INT               DEFAULT NULL COMMENT '关闭码(1000=正常)',
    close_reason       VARCHAR(512)       DEFAULT NULL COMMENT '关闭原因',
    
    -- 帧统计
    frames_sent        BIGINT            NOT NULL DEFAULT 0 COMMENT '发送帧数',
    frames_received     BIGINT            NOT NULL DEFAULT 0 COMMENT '接收帧数',
    bytes_sent         BIGINT            NOT NULL DEFAULT 0 COMMENT '发送字节',
    bytes_received     BIGINT            NOT NULL DEFAULT 0 COMMENT '接收字节',
    
    -- 状态
    status             ENUM('connected', 'authenticated', 'subscribed', 'closing', 'closed') 
                      DEFAULT 'connected',
    
    PRIMARY KEY (session_id),
    INDEX idx_vhost (vhost),
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_last_message (last_message_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'WebSocket会话表';

-- 9.14 SSE订阅表
CREATE TABLE IF NOT EXISTS sse_subscription (
    subscription_id    VARCHAR(64)       NOT NULL COMMENT '订阅ID',
    session_id         VARCHAR(64)       NOT NULL COMMENT '会话ID',
    
    -- 订阅配置
    destination_type   ENUM('queue', 'topic') NOT NULL COMMENT '目的地类型',
    destination_id     VARCHAR(64)       NOT NULL COMMENT '目的地ID',
    filter_pattern     VARCHAR(1024)      DEFAULT NULL COMMENT '过滤模式',
    
    -- 消费位置
    start_policy      ENUM('first', 'last') DEFAULT 'last' COMMENT '起始策略',
    start_offset      BIGINT            DEFAULT NULL COMMENT '起始偏移量',
    
    -- 推送配置
    format            ENUM('json', 'protobuf', 'text') DEFAULT 'json' COMMENT '消息格式',
    include_metadata  BOOLEAN           NOT NULL DEFAULT TRUE COMMENT '是否包含元数据',
    max_batch_size    INT               DEFAULT 10 COMMENT '最大批量推送条数',
    max_batch_interval_ms INT           DEFAULT 1000 COMMENT '最大批量间隔(毫秒)',
    
    -- 状态
    status            ENUM('active', 'paused', 'closed') DEFAULT 'active',
    active_since      DATETIME(3)       NOT NULL COMMENT '订阅开始时间',
    
    PRIMARY KEY (subscription_id),
    INDEX idx_session (session_id),
    INDEX idx_destination (destination_type, destination_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'SSE订阅表';

-- =============================================
-- 10. 性能与优化
-- =============================================

-- 10.1 存储引擎配置表
CREATE TABLE IF NOT EXISTS storage_engine_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    vhost              VARCHAR(128)      NOT NULL DEFAULT '/',
    
    -- 引擎选择
    engine_type        ENUM('append_only_log', 'lsm_tree', 'btree', 'hybrid') 
                      NOT NULL DEFAULT 'append_only_log' COMMENT '存储引擎类型',
    
    -- 写入配置
    write_mode         ENUM('sync', 'async', 'batch') DEFAULT 'batch' COMMENT '写入模式',
    sync_interval_ms   INT               DEFAULT 100 COMMENT '同步间隔(毫秒)',
    batch_size         INT               DEFAULT 1000 COMMENT '批量写入大小',
    
    -- 存储配置
    data_dir           VARCHAR(1024)     NOT NULL COMMENT '数据存储目录',
    index_dir          VARCHAR(1024)     DEFAULT NULL COMMENT '索引存储目录',
    max_segment_size   BIGINT            NOT NULL DEFAULT 1073741824 COMMENT '单文件最大大小(1GB)',
    
    -- 缓存
    page_cache_size_mb INT               DEFAULT 4096 COMMENT '页缓存大小(MB)',
    block_cache_size_mb INT              DEFAULT 1024 COMMENT '块缓存大小(MB)',
    
    -- 压缩
    compression_type   ENUM('none', 'snappy', 'lz4', 'zstd', 'gzip') DEFAULT 'lz4' COMMENT '压缩算法',
    compression_level  INT               DEFAULT 3 COMMENT '压缩级别',
    
    -- 清理
    cleanup_policy     ENUM('delete', 'compact', 'compact_and_delete') DEFAULT 'delete' COMMENT '清理策略',
    retention_hours    INT               DEFAULT 168 COMMENT '数据保留时间(7天)',
    compaction_enabled  BOOLEAN          NOT NULL DEFAULT FALSE COMMENT '是否启用压缩',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (config_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '存储引擎配置表';

-- 10.2 索引配置表
CREATE TABLE IF NOT EXISTS index_config (
    index_id           VARCHAR(64)       NOT NULL COMMENT '索引ID',
    table_name         VARCHAR(128)      NOT NULL COMMENT '表名',
    index_name         VARCHAR(128)      NOT NULL COMMENT '索引名称',
    
    -- 索引定义
    index_type         ENUM('btree', 'hash', 'bitmap', 'fulltext', 'spatial') NOT NULL COMMENT '索引类型',
    columns            JSON             NOT NULL COMMENT '索引列定义',
    unique             BOOLEAN           NOT NULL DEFAULT FALSE COMMENT '是否唯一索引',
    
    -- 状态
    status             ENUM('building', 'active', 'disabled', 'rebuilding') DEFAULT 'active',
    
    -- 性能
    size_bytes         BIGINT            DEFAULT NULL COMMENT '索引大小(字节)',
    row_count          BIGINT            DEFAULT NULL COMMENT '索引行数',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    last_rebuilt_at     DATETIME(3)      DEFAULT NULL COMMENT '上次重建时间',
    
    PRIMARY KEY (index_id),
    UNIQUE KEY uk_table_name (table_name, index_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '索引配置表';

-- 10.3 message_partitioned
CREATE TABLE IF NOT EXISTS message_partitioned (
    message_id VARCHAR(64),
    created_at DATETIME,
    payload BLOB,
    PRIMARY KEY (message_id, created_at)
) PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p202601 VALUES LESS THAN (202602),
    PARTITION p202602 VALUES LESS THAN (202603),
    PARTITION p202603 VALUES LESS THAN (202604),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 10.4 分片配置表
CREATE TABLE IF NOT EXISTS shard_config (
    shard_id           INT               NOT NULL COMMENT '分片ID',
    shard_name         VARCHAR(64)       NOT NULL COMMENT '分片名称',
    
    -- 节点配置
    primary_node       VARCHAR(128)      NOT NULL COMMENT '主节点',
    replica_nodes      JSON              DEFAULT NULL COMMENT '副本节点列表',
    /*
    ["broker-replica-01", "broker-replica-02"]
    */
    
    -- 分片规则
    sharding_type      ENUM('hash', 'range', 'directory') NOT NULL,
    sharding_key       VARCHAR(64)       DEFAULT NULL COMMENT '分片键',
    sharding_algorithm  VARCHAR(256)     DEFAULT NULL COMMENT '分片算法表达式',
    
    -- 范围（range 类型）
    range_start        VARCHAR(255)      DEFAULT NULL COMMENT '范围起始值',
    range_end          VARCHAR(255)      DEFAULT NULL COMMENT '范围结束值',
    
    -- 容量
    max_capacity       BIGINT            DEFAULT 100000000 COMMENT '最大容量(条)',
    current_count      BIGINT            NOT NULL DEFAULT 0 COMMENT '当前消息数',
    current_size_bytes BIGINT            NOT NULL DEFAULT 0 COMMENT '当前存储(字节)',
    
    -- 状态
    status             ENUM('active', 'readonly', 'draining', 'offline') DEFAULT 'active',
    weight             INT               DEFAULT 100 COMMENT '负载权重(1-1000)',
    
    -- 位置
    datacenter         VARCHAR(64)       DEFAULT NULL COMMENT '所属机房',
    rack               VARCHAR(64)       DEFAULT NULL COMMENT '所属机架',
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (shard_id),
    KEY uk_name (shard_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '分片配置表';

-- 10.5 分片重平衡任务表
CREATE TABLE IF NOT EXISTS shard_rebalance_job (
    job_id             VARCHAR(64)       NOT NULL COMMENT '任务ID',
    job_type           ENUM('move', 'split', 'merge', 'rebalance') NOT NULL,
    
    -- 源和目标
    source_shard_id    INT               NOT NULL COMMENT '源分片ID',
    target_shard_id    INT               DEFAULT NULL COMMENT '目标分片ID',
    
    -- 范围
    move_key_start     VARCHAR(255)      DEFAULT NULL COMMENT '迁移键起始',
    move_key_end       VARCHAR(255)      DEFAULT NULL COMMENT '迁移键结束',
    
    -- 进度
    total_records      BIGINT            NOT NULL DEFAULT 0 COMMENT '总记录数',
    moved_records      BIGINT            NOT NULL DEFAULT 0 COMMENT '已迁移数',
    progress_pct       DECIMAL(5,2)     NOT NULL DEFAULT 0 COMMENT '进度百分比',
    
    -- 限速
    rate_limit_records INT               DEFAULT 10000 COMMENT '迁移速率限制(条/秒)',
    pause_on_high_load BOOLEAN          NOT NULL DEFAULT TRUE COMMENT '高负载时暂停',
    
    -- 状态
    status             ENUM('pending', 'running', 'paused', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    started_at         DATETIME(3)       DEFAULT NULL,
    completed_at       DATETIME(3)       DEFAULT NULL,
    
    -- 错误
    error_message      TEXT              DEFAULT NULL,
    retry_count        INT               NOT NULL DEFAULT 0,
    
    PRIMARY KEY (job_id),
    INDEX idx_status (status),
    INDEX idx_source (source_shard_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '分片重平衡任务表';

-- 10.6 sharded_config
CREATE TABLE IF NOT EXISTS sharded_config (
    config_key VARCHAR(128),
    config_value TEXT,
    updated_at DATETIME(3),
    PRIMARY KEY (config_key)
) ALL SHARDS;

-- 10.7 内存配置表
CREATE TABLE IF NOT EXISTS memory_config (
    config_id          VARCHAR(64)       NOT NULL COMMENT '配置ID',
    node_name          VARCHAR(128)      DEFAULT NULL COMMENT '节点名称(NULL表示全局)',
    
    -- JVM 配置
    jvm_heap_min_mb   INT               NOT NULL DEFAULT 2048 COMMENT '最小堆大小(MB)',
    jvm_heap_max_mb   INT               NOT NULL DEFAULT 8192 COMMENT '最大堆大小(MB)',
    jvm_gc_type       ENUM('serial', 'parallel', 'cms', 'g1', 'zgc', 'shenandoah') 
                      DEFAULT 'g1' COMMENT 'GC类型',
    
    -- 堆外内存
    offheap_max_mb    INT               DEFAULT 1024 COMMENT '堆外最大内存(MB)',
    direct_buffer_size_mb INT          DEFAULT 512 COMMENT 'Direct Buffer大小(MB)',
    
    -- 消息缓存
    message_cache_size_mb INT          DEFAULT 1024 COMMENT '消息缓存大小(MB)',
    page_cache_size_mb INT              DEFAULT 4096 COMMENT '页缓存大小(MB)',
    
    -- 元数据缓存
    metadata_cache_size_mb INT          DEFAULT 256 COMMENT '元数据缓存大小(MB)',
    
    -- 网络缓冲区
    network_buffer_min_mb INT          DEFAULT 128 COMMENT '网络缓冲最小(MB)',
    network_buffer_max_mb INT           DEFAULT 512 COMMENT '网络缓冲最大(MB)',
    
    -- 状态
    enabled            BOOLEAN           NOT NULL DEFAULT TRUE,
    
    -- 审计
    created_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updated_at         DATETIME(3)       NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    
    PRIMARY KEY (config_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '内存配置表';

-- 10.8 GC日志分析表
CREATE TABLE IF NOT EXISTS gc_log (
    log_id             BIGINT            NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    node_name          VARCHAR(128)      NOT NULL COMMENT '节点名称',
    
    -- GC 信息
    gc_type            ENUM('young', 'old', 'full', 'mixed') NOT NULL COMMENT 'GC类型',
    collector_name      VARCHAR(64)        NOT NULL COMMENT '收集器名称',
    
    -- 时间
    start_time         DATETIME(3)       NOT NULL COMMENT '开始时间',
    end_time           DATETIME(3)       NOT NULL COMMENT '结束时间',
    duration_ms        BIGINT            NOT NULL COMMENT 'GC耗时(毫秒)',
    
    -- 内存变化
    heap_before_mb    BIGINT            NOT NULL COMMENT 'GC前堆大小(MB)',
    heap_after_mb     BIGINT            NOT NULL COMMENT 'GC后堆大小(MB)',
    heap_used_before_mb BIGINT          NOT NULL COMMENT 'GC前已用堆(MB)',
    heap_used_after_mb BIGINT           NOT NULL COMMENT 'GC后已用堆(MB)',
    
    -- YGC 特有
    eden_before_mb    BIGINT            DEFAULT NULL COMMENT 'Eden区GC前(MB)',
    eden_after_mb     BIGINT            DEFAULT NULL COMMENT 'Eden区GC后(MB)',
    survivor_before_mb BIGINT          DEFAULT NULL COMMENT 'Survivor区GC前(MB)',
    survivor_after_mb BIGINT            DEFAULT NULL COMMENT 'Survivor区GC后(MB)',
    
    -- Full GC 特有
    cause              VARCHAR(128)      DEFAULT NULL COMMENT 'Full GC原因',
    
    -- 影响
    stw_pause_ms      BIGINT            NOT NULL COMMENT 'Stop-The-World暂停(毫秒)',
    application_pause  BOOLEAN          NOT NULL DEFAULT FALSE COMMENT '是否影响应用',
    
    PRIMARY KEY (log_id),
    INDEX idx_node_time (node_name, start_time),
    INDEX idx_gc_type (gc_type),
    INDEX idx_duration (duration_ms)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'GC日志分析表';

-- 10.9 JVM诊断快照表
CREATE TABLE IF NOT EXISTS jvm_diagnostic_snapshot (
    snapshot_id        VARCHAR(64)       NOT NULL COMMENT '快照ID',
    node_name          VARCHAR(128)      NOT NULL COMMENT '节点名称',
    
    -- JVM 信息
    jvm_version        VARCHAR(128)      NOT NULL COMMENT 'JVM版本',
    java_version        VARCHAR(128)      NOT NULL COMMENT 'Java版本',
    vm_name            VARCHAR(128)      NOT NULL COMMENT '虚拟机名称',
    
    -- 运行时
    uptime_seconds     BIGINT            NOT NULL COMMENT '运行时长(秒)',
    start_time         DATETIME(3)       NOT NULL COMMENT '启动时间',
    snapshot_time       DATETIME(3)       NOT NULL COMMENT '快照时间',
    
    -- 堆内存
    heap_init_mb      BIGINT            NOT NULL COMMENT '堆初始化(MB)',
    heap_used_mb       BIGINT            NOT NULL COMMENT '堆已用(MB)',
    heap_committed_mb  BIGINT            NOT NULL COMMENT '堆提交(MB)',
    heap_max_mb        BIGINT            NOT NULL COMMENT '堆最大(MB)',
    heap_occupancy_pct DECIMAL(5,2)     NOT NULL COMMENT '堆占用比例(%)',
    
    -- 非堆内存
    nonheap_init_mb   BIGINT            NOT NULL COMMENT '非堆初始化(MB)',
    nonheap_used_mb   BIGINT            NOT NULL COMMENT '非堆已用(MB)',
    metaspace_used_mb BIGINT            NOT NULL COMMENT 'Metaspace已用(MB)',
    code_cache_used_mb BIGINT            NOT NULL COMMENT 'CodeCache已用(MB)',
    
    -- 线程
    thread_count       INT               NOT NULL COMMENT '线程总数',
    peak_thread_count  INT               NOT NULL COMMENT '峰值线程数',
    daemon_thread_count INT              NOT NULL COMMENT '守护线程数',
    
    -- 类加载
    classes_loaded     BIGINT            NOT NULL COMMENT '当前加载类数',
    classes_total_loaded BIGINT          NOT NULL COMMENT '累计加载类数',
    classes_unloaded   BIGINT            NOT NULL COMMENT '卸载类数',
    
    -- GC 统计
    young_gc_count    BIGINT            NOT NULL DEFAULT 0 COMMENT 'Young GC次数',
    young_gc_time_ms  BIGINT            NOT NULL DEFAULT 0 COMMENT 'Young GC总耗时',
    old_gc_count      BIGINT            NOT NULL DEFAULT 0 COMMENT 'Old GC次数',
    old_gc_time_ms    BIGINT            NOT NULL DEFAULT 0 COMMENT 'Old GC总耗时',
    
    -- 系统
    system_load_avg   DECIMAL(5,2)     DEFAULT NULL COMMENT '系统负载均值',
    cpu_usage_pct     DECIMAL(5,2)     DEFAULT NULL COMMENT 'CPU使用率(%)',
    open_fd_count     INT               DEFAULT NULL COMMENT '打开文件描述符数',
    max_fd_count      INT               DEFAULT NULL COMMENT '最大文件描述符数',
    
    PRIMARY KEY (snapshot_id),
    INDEX idx_node_time (node_name, snapshot_time)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = 'JVM诊断快照表';

-- 10.10 线程快照表
CREATE TABLE IF NOT EXISTS thread_dump_record (
    dump_id            VARCHAR(64)       NOT NULL COMMENT '快照ID',
    node_name          VARCHAR(128)      NOT NULL COMMENT '节点名称',
    snapshot_time       DATETIME(3)       NOT NULL COMMENT '快照时间',
    
    -- 线程信息
    thread_name        VARCHAR(255)      NOT NULL COMMENT '线程名称',
    thread_id          BIGINT            NOT NULL COMMENT '线程ID',
    thread_type        ENUM('user', 'daemon', 'system') NOT NULL COMMENT '线程类型',
    
    -- 状态
    thread_state        VARCHAR(32)       NOT NULL COMMENT '线程状态',
    is_suspended        BOOLEAN          NOT NULL COMMENT '是否挂起',
    is_in_native        BOOLEAN          NOT NULL COMMENT '是否执行本地代码',
    
    -- 堆栈
    stack_trace        TEXT              NOT NULL COMMENT '完整堆栈',
    monitor_info       JSON              DEFAULT NULL COMMENT '锁信息',
    /*
    {
      "locked_monitors": [
        {"class": "java.lang.Object", "identity_hash": "xxx", "locked_at": "stack_frame"}
      ],
      "locked_synchronizers": [
        {"class": "java.util.concurrent.locks.ReentrantLock", "identity_hash": "xxx"}
      ],
      "blocked_on": {"class": "xxx", "identity_hash": "xxx", "blocked_at": "stack_frame"}
    }
    */
    
    -- CPU
    cpu_time_ms        BIGINT            DEFAULT NULL COMMENT 'CPU占用时间(毫秒)',
    
    -- 上下文
    context_class_loader VARCHAR(256)    DEFAULT NULL COMMENT '上下文类加载器',
    stack_depth        INT               NOT NULL COMMENT '堆栈深度',
    
    PRIMARY KEY (dump_id),
    INDEX idx_node_time (node_name, snapshot_time),
    INDEX idx_thread_state (thread_state)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  COMMENT = '线程快照表';

```
