# Offset 管理

## Offset：消费进度的持久化表示

Offset（消费偏移量）记录了消费者消费到了哪一条消息，是消息消费进度的持久化表示。**Offset 管理确保消费者重启或故障恢复后能从上次消费的位置继续**。

## 数据库设计：偏移量明细表与变更历史表

### 表结构：consumer_offset_detail（消费偏移量明细表）

```sql
CREATE TABLE consumer_offset_detail (
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
```

### 表结构：offset_history（偏移量变更历史表）

```sql
CREATE TABLE offset_history (
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
```

## Offset 提交策略：Auto Commit、Manual Sync 与 Manual Async

| 策略 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| Auto Commit | 每隔固定时间自动提交 | 简单 | 可能重复消费或丢失消息 |
| Manual Sync | 处理完手动同步提交 | 精确 | 阻塞等待确认，影响吞吐 |
| Manual Async | 处理完异步提交 | 高吞吐 | 提交可能失败，需重试 |

*图：三种 Offset 提交策略的权衡（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 300" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="40" width="150" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="60" text-anchor="middle" font-size="14" fill="#1e293b">Auto Commit</text>
  <text x="95" y="80" text-anchor="middle" font-size="12" fill="#475569">自动提交</text>
  <rect x="210" y="40" width="210" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="315" y="71" text-anchor="middle" font-size="13" fill="#1e293b">每隔固定时间自动提交</text>
  <rect x="460" y="40" width="250" height="52" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="585" y="60" text-anchor="middle" font-size="12" fill="#1e293b">优点：简单</text>
  <text x="585" y="80" text-anchor="middle" font-size="12" fill="#dc2626">缺点：可能重复消费或丢失消息</text>
  <line x1="170" y1="66" x2="208" y2="66" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="420" y1="66" x2="458" y2="66" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="20" y="124" width="150" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="144" text-anchor="middle" font-size="14" fill="#1e293b">Manual Sync</text>
  <text x="95" y="164" text-anchor="middle" font-size="12" fill="#475569">手动同步提交</text>
  <rect x="210" y="124" width="210" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="315" y="155" text-anchor="middle" font-size="13" fill="#1e293b">处理完手动同步提交</text>
  <rect x="460" y="124" width="250" height="52" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="585" y="144" text-anchor="middle" font-size="12" fill="#1e293b">优点：精确</text>
  <text x="585" y="164" text-anchor="middle" font-size="12" fill="#dc2626">缺点：阻塞等待确认，影响吞吐</text>
  <line x1="170" y1="150" x2="208" y2="150" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="420" y1="150" x2="458" y2="150" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="20" y="208" width="150" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="228" text-anchor="middle" font-size="14" fill="#1e293b">Manual Async</text>
  <text x="95" y="248" text-anchor="middle" font-size="12" fill="#475569">手动异步提交</text>
  <rect x="210" y="208" width="210" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="315" y="239" text-anchor="middle" font-size="13" fill="#1e293b">处理完异步提交</text>
  <rect x="460" y="208" width="250" height="52" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="585" y="228" text-anchor="middle" font-size="12" fill="#1e293b">优点：高吞吐</text>
  <text x="585" y="248" text-anchor="middle" font-size="12" fill="#dc2626">缺点：提交可能失败，需重试</text>
  <line x1="170" y1="234" x2="208" y2="234" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="420" y1="234" x2="458" y2="234" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
</svg>

## Offset 重置场景：操作与命令

| 场景 | 操作 | 命令 |
|------|------|------|
| 从头重新消费 | offset → 0 | `--from-beginning` |
| 从最新开始 | offset → latest | `--to-latest` |
| 跳转到指定时间 | offset → timestamp | `--to-datetime 2026-03-29T10:00:00` |
| 回退 N 条 | offset -= N | `--rewind 100` |

*文档版本：v1.0 | 更新日期：2026-03-29*
