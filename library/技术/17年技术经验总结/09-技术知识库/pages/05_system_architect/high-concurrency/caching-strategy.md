# 缓存策略 - 架构师学习笔记

缓存是一种存储技术，通过将数据存储在**高速访问的介质**中，减少数据获取时间，提高系统性能。在高并发系统中，合理使用缓存可以**显著降低数据库压力**，提高响应速度和系统吞吐量。

## 缓存的作用

- **提高访问速度**：缓存数据存储在内存中，访问速度远超磁盘数据库。
- **减轻数据库压力**：大部分请求从缓存获取数据，减少数据库访问次数。
- **提升系统性能**：通过缓存热点数据，提高系统整体吞吐量。

## 缓存分类

### 按存储位置分类

#### 客户端缓存

- 浏览器缓存、APP缓存等，减少网络请求。
  - 浏览器缓存
  - 本地存储
  - 内存缓存

#### 服务端缓存

- 应用服务器内部缓存，提高处理速度。
  - 进程内缓存
  - 分布式缓存
  - CDN缓存

#### 数据库缓存

- 数据库内置缓存机制，加速查询操作。
  - 查询缓存
  - 缓冲池
  - 索引缓存

### 按缓存策略分类

| 策略 | 特点 | 适用场景 |
|------|------|----------|
| Cache-Aside | 应用代码维护缓存 | 读多写少场景 |
| Read-Through | 缓存层负责加载数据 | 简化应用逻辑 |
| Write-Through | 数据同时写入缓存和存储 | 强一致性要求 |
| Write-Behind | 先写缓存，异步写存储 | 高写入性能要求 |

## 缓存模式

### Cache-Aside Pattern

- **应用代码负责维护缓存**，是最常用的缓存模式。

```java
// 读操作
String value = cache.get(key);
if (value == null) {
    value = database.get(key);
    cache.put(key, value, expireTime);
}
return value;

// 写操作
database.update(key, value);
cache.delete(key);
```

*图：Cache-Aside 读请求流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 200" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="30" y="78" width="110" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="85" y="105" text-anchor="middle" font-size="14" fill="#1e293b">客户端请求</text>
  <line x1="140" y1="100" x2="188" y2="100" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="78" width="110" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="245" y="105" text-anchor="middle" font-size="14" fill="#1e293b">缓存</text>
  <line x1="300" y1="100" x2="293" y2="100" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <polygon points="360,55 428,100 360,145 292,100" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="105" text-anchor="middle" font-size="13" fill="#1e293b">命中？</text>
  <line x1="422" y1="86" x2="468" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="440" y="62" text-anchor="start" font-size="12" fill="#475569">是</text>
  <line x1="422" y1="114" x2="468" y2="142" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="440" y="142" text-anchor="start" font-size="12" fill="#475569">否</text>
  <rect x="470" y="30" width="190" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="565" y="57" text-anchor="middle" font-size="14" fill="#1e293b">返回缓存数据</text>
  <rect x="470" y="130" width="190" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="565" y="157" text-anchor="middle" font-size="14" fill="#1e293b">查询数据库</text>
  <line x1="470" y1="152" x2="248" y2="124" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="356" y="152" text-anchor="middle" font-size="12" fill="#475569">回填缓存</text>
</svg>

### Write-Through Pattern

- 数据**同时写入缓存和数据库**，保证数据一致性。

```java
// 写操作
cache.put(key, value);
database.update(key, value);
```

### Write-Behind Pattern

- 先写缓存，**异步批量写入数据库**，提高写入性能。

```java
// 写操作
cache.put(key, value);
// 异步批量写入数据库
asyncWriteToDatabase(batch);
```

### Refresh-Ahead Pattern

- 在**缓存过期前主动刷新**，避免缓存失效时的性能抖动。

```java
// 定时刷新热点数据
scheduler.scheduleAtFixedRate(() -> {
    for (String key : hotKeys) {
        Object value = database.get(key);
        cache.put(key, value, expireTime);
    }
}, 0, refreshInterval, TimeUnit.SECONDS);
```

## 缓存淘汰策略

### 常见淘汰算法

#### LRU (Least Recently Used)

- 淘汰**最近最少使用**的数据
  - 实现简单
  - 符合局部性原理
  - 可能存在缓存污染

#### LFU (Least Frequently Used)

- 淘汰**访问频率最低**的数据
  - 考虑访问频率
  - 实现复杂
  - 可能淘汰新热点数据

#### FIFO (First In First Out)

- 淘汰**最早进入缓存**的数据
  - 实现简单
  - 不考虑访问模式
  - 性能较差

#### TTL (Time To Live)

- 按**过期时间**淘汰数据
  - 简单有效
  - 需要合理设置过期时间
  - 可能造成缓存雪崩

### Redis淘汰策略

| 策略 | 说明 |
|------|------|
| noeviction | 不淘汰数据，内存满时返回错误 |
| allkeys-lru | 从所有key中淘汰最近最少使用的 |
| allkeys-lfu | 从所有key中淘汰最不经常使用的 |
| allkeys-random | 从所有key中随机淘汰 |
| volatile-lru | 从设置了过期时间的key中淘汰最近最少使用的 |

## 缓存一致性

### 强一致性

- 保证缓存和数据库数据**完全一致**。
  - Write-Through模式
  - 双写一致性
  - 分布式事务

### 最终一致性

- 允许**短暂不一致**，但最终会达到一致状态。
  - Cache-Aside模式
  - 延迟双删
  - 异步更新

## 缓存常见问题

### 缓存雪崩

- **大量缓存同时失效**，导致数据库压力骤增
  - 设置不同的过期时间
  - 使用互斥锁重建缓存
  - 永不过期策略

### 缓存穿透

- **查询不存在的数据**，直接访问数据库
  - 布隆过滤器过滤无效请求
  - 缓存空值
  - 参数校验

### 缓存击穿

- **热点数据过期**时大量请求直接访问数据库
  - 热点数据永不过期
  - 互斥锁重建缓存
  - 预热热点数据

### 缓存预热

- **系统启动时**加载热点数据到缓存
  - 启动时加载热点数据
  - 定时刷新缓存
  - 手动触发预热

## 缓存监控与优化

### 关键监控指标

- **命中率**：缓存命中请求占总请求数的比例
- **平均响应时间**：缓存访问的平均耗时
- **内存使用率**：缓存内存占用情况
- **QPS**：每秒缓存请求数

### 性能优化建议

- 合理设置缓存大小和过期时间
- 选择合适的缓存淘汰策略
- 压缩大value
- 使用Pipeline批量操作
- 定期清理无用缓存

## 缓存策略最佳实践

- 根据业务特点选择合适的**缓存模式**
- 合理设计缓存**key命名规范**
- 设置合适的**过期时间和淘汰策略**
- 实施**监控和告警**机制
- 定期分析缓存使用情况
- 制定**缓存失效应急预案**
- 做好**缓存数据一致性**处理
