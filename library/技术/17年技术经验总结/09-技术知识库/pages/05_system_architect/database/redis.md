# Redis缓存 - 架构师学习笔记

Redis（Remote Dictionary Server）是一个开源的内存数据结构存储系统，可以用作数据库、缓存和消息中间件。Redis支持多种数据结构，如字符串、哈希、列表、集合、有序集合等，具有高性能、持久化、主从复制、事务等特性。

## Redis数据类型

### String（字符串）

- 最基本的数据类型，可以存储字符串、整数或浮点数。

```bash
# 基本操作
SET name "Redis"
GET name
INCR counter
DECR counter
APPEND name " Server"
```

### Hash（哈希）

- 键值对集合，适合存储对象。

```bash
# 基本操作
HSET user:1 name "Alice" age 25
HGET user:1 name
HGETALL user:1
HINCRBY user:1 age 1
```

### List（列表）

- 有序的字符串列表，可以在两端插入或删除元素。

```bash
# 基本操作
LPUSH tasks "task1" "task2"
RPUSH tasks "task3"
LPOP tasks
LRANGE tasks 0 -1
```

### Set（集合）

- 无序的字符串集合，元素不重复。

```bash
# 基本操作
SADD tags "redis" "database" "nosql"
SMEMBERS tags
SISMEMBER tags "redis"
SREM tags "nosql"
```

### ZSet（有序集合）

- 类似Set，但每个元素关联一个分数，按分数排序。

```bash
# 基本操作
ZADD leaderboard 100 "Alice" 90 "Bob" 95 "Charlie"
ZRANGE leaderboard 0 -1 WITHSCORES
ZSCORE leaderboard "Alice"
ZINCRBY leaderboard 10 "Alice"
```

## Redis持久化

### RDB（快照）

- 在指定时间间隔内将内存中的数据集快照写入磁盘。
- 特点：
  - 紧凑的二进制文件
  - 恢复大数据集速度快
  - 可能会丢失最后一次快照后的数据

```bash
# RDB配置
save 900 1
save 300 10
save 60 10000
```

### AOF（追加文件）

- 记录每个写操作，以文本形式追加到文件末尾。
- 特点：
  - 数据安全性高
  - 文件体积大，恢复速度慢
  - 可通过rewrite优化文件

```bash
# AOF配置
appendonly yes
appendfsync everysec
```

*图：RDB 与 AOF 持久化方式对比（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 250" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <rect x="40" y="30" width="300" height="180" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="190" y="60" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">RDB（快照）</text>
  <text x="190" y="92" text-anchor="middle" font-size="13" fill="#1e293b">定时将内存数据快照写入磁盘</text>
  <text x="190" y="116" text-anchor="middle" font-size="13" fill="#1e293b">紧凑的二进制文件</text>
  <text x="190" y="140" text-anchor="middle" font-size="13" fill="#1e293b">恢复大数据集速度快</text>
  <text x="190" y="164" text-anchor="middle" font-size="13" fill="#1e293b">可能会丢失最后一次快照后的数据</text>
  <rect x="380" y="30" width="300" height="180" rx="10" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="530" y="60" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">AOF（追加文件）</text>
  <text x="530" y="92" text-anchor="middle" font-size="13" fill="#1e293b">记录每个写操作，追加到文件末尾</text>
  <text x="530" y="116" text-anchor="middle" font-size="13" fill="#1e293b">数据安全性高</text>
  <text x="530" y="140" text-anchor="middle" font-size="13" fill="#1e293b">文件体积大，恢复速度慢</text>
  <text x="530" y="164" text-anchor="middle" font-size="13" fill="#1e293b">可通过rewrite优化文件</text>
  <text x="360" y="236" text-anchor="middle" font-size="13" fill="#475569">RDB 恢复速度快 · AOF 数据安全性高</text>
</svg>

## Redis集群

### 集群模式

- **主从复制**：一个主节点多个从节点，实现读写分离
- **哨兵模式**：自动故障转移，保证高可用性
- **Cluster模式**：官方集群方案，自动分片

### 主从复制配置

```bash
# 主节点配置
# redis.conf (master)
port 6379
requirepass masterpassword

# 从节点配置
# redis.conf (slave)
port 6380
slaveof 127.0.0.1 6379
masterauth masterpassword
```

## 缓存策略

### 缓存更新策略

- Cache-Aside Pattern：应用代码负责维护缓存
- Read-Through：缓存层负责加载数据
- Write-Through：数据同时写入缓存和数据库
- Write-Behind：先写缓存，异步写数据库

### 缓存淘汰策略

- LRU：最近最少使用
- LFU：最不经常使用
- TTL：设置过期时间
- Random：随机淘汰

```bash
# 配置最大内存和淘汰策略
maxmemory 2gb
maxmemory-policy allkeys-lru
```

## Redis事务

### 事务操作

Redis通过MULTI、EXEC、DISCARD和WATCH命令实现事务功能。

```bash
# 基本事务
MULTI
SET key1 "value1"
INCR counter
LPUSH mylist "item1"
EXEC

# 带监视的事务
WATCH balance
GET balance
MULTI
SET balance 1000
EXEC
```

### Lua脚本

通过Lua脚本实现原子性操作。

```bash
# Lua脚本示例
EVAL "local current = redis.call('GET', KEYS[1]); 
      if current == false or tonumber(current) < tonumber(ARGV[1]) then 
          redis.call('SET', KEYS[1], ARGV[1]); 
          return 1; 
      else 
          return 0; 
      end" 
1 mykey 100
```

## 性能优化

### 连接优化

- 使用连接池减少连接开销
- 合理设置超时时间
- 避免长时间阻塞操作
- 批量操作减少网络往返

### 内存优化

- 合理设置key的过期时间
- 使用Hash结构存储对象
- 压缩大value
- 定期清理无用数据

## 监控与诊断

### 监控指标

| 指标 | 说明 | 监控工具 |
|------|------|----------|
| 内存使用率 | Redis内存占用情况 | Redis CLI, Redis Stat |
| 命中率 | 缓存命中比例 | Redis CLI |
| 连接数 | 当前连接数 | Redis CLI |
| QPS | 每秒查询数 | Redis Benchmark |

### 常用命令

```bash
# 监控命令
INFO                    # 查看服务器信息
MONITOR                 # 实时监控命令
SLOWLOG GET             # 查看慢查询日志
CLIENT LIST             # 查看客户端连接

# 性能测试
redis-benchmark -h 127.0.0.1 -p 6379 -c 100 -n 100000
```

## Redis最佳实践

- 合理设计key命名规范，便于管理和监控
- 设置合适的过期时间，避免内存浪费
- 使用Pipeline批量操作，减少网络开销
- 实施监控和告警，及时发现性能问题
- 定期备份数据，确保数据安全
- 根据业务需求选择合适的持久化策略
- 使用集群模式提高可用性和扩展性
