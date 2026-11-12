# 高并发架构 - 架构师学习笔记

高并发架构是指系统能够**同时处理大量并发请求**的能力。随着互联网应用用户规模的快速增长，高并发已成为现代系统架构设计中的重要挑战。构建高并发系统需要从多个维度进行优化，包括**负载均衡、缓存策略、数据库优化、异步处理**等。

## 高并发系统特点

- **高性能**：系统需要在短时间内处理大量请求，响应时间要尽可能短。
- **高可用**：系统需要具备容错能力，即使部分组件故障也能正常提供服务。
- **可扩展**：系统能够根据业务需求灵活扩展，支持水平和垂直扩展。

## 高并发设计原则

- **缓存优先**：合理使用缓存减少数据库压力
- **异步处理**：将耗时操作异步化，提高响应速度
- **负载均衡**：分散请求压力，提高系统吞吐量
- **限流降级**：保护系统不被突发流量冲垮
- **数据库优化**：合理设计数据库和SQL语句
- **无状态设计**：便于水平扩展和故障恢复

## 核心优化策略

### 负载均衡

- 通过负载均衡器将请求分发到多个服务器实例，提高系统处理能力和可用性。
  - [查看详情](load-balancing.md)

### 缓存策略

- 利用缓存减少数据库访问，提高响应速度和系统吞吐量。
  - [查看详情](caching-strategy.md)

### 数据库分片

- 将数据分散到多个数据库实例，解决单库性能瓶颈。
  - [查看详情](../database/database-sharding.md)

### CDN加速

- 利用CDN分发静态资源，减少网络延迟，提高用户访问速度。
  - [查看详情](cdn.md)

*图：高并发系统核心优化链路（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 180" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="30" y="30" width="120" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="90" y="57" text-anchor="middle" font-size="14" fill="#1e293b">用户请求</text>
  <line x1="150" y1="52" x2="218" y2="52" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="220" y="30" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="290" y="57" text-anchor="middle" font-size="14" fill="#1e293b">CDN加速</text>
  <line x1="360" y1="52" x2="428" y2="52" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="430" y="30" width="140" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="500" y="57" text-anchor="middle" font-size="14" fill="#1e293b">负载均衡</text>
  <line x1="500" y1="74" x2="320" y2="102" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="104" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="250" y="131" text-anchor="middle" font-size="14" fill="#1e293b">应用服务</text>
  <line x1="320" y1="126" x2="368" y2="126" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="370" y="104" width="120" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="430" y="131" text-anchor="middle" font-size="14" fill="#1e293b">缓存</text>
  <line x1="490" y1="126" x2="538" y2="126" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="514" y="116" text-anchor="middle" font-size="12" fill="#475569">未命中</text>
  <rect x="540" y="104" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="615" y="131" text-anchor="middle" font-size="14" fill="#1e293b">数据库分片</text>
</svg>

## 性能指标

| 指标 | 说明 | 优化目标 |
|------|------|----------|
| QPS（每秒查询数） | 系统每秒处理的请求数量 | 根据业务需求确定 |
| RT（响应时间） | 系统处理请求的平均时间 | 通常要求在毫秒级 |
| 并发用户数 | 系统同时能处理的用户请求数 | 根据业务峰值确定 |
| 吞吐量 | 单位时间内处理的请求数量 | 越大越好 |

## 常见问题与解决方案

### 缓存雪崩

- **大量缓存同时失效**，导致数据库压力骤增
  - 设置不同的过期时间
  - 使用互斥锁重建缓存

### 缓存穿透

- **查询不存在的数据**，直接访问数据库
  - 布隆过滤器过滤无效请求
  - 缓存空值

### 缓存击穿

- **热点数据过期**时大量请求直接访问数据库
  - 热点数据永不过期
  - 互斥锁重建缓存

### 限流策略

- 控制请求流量，保护系统稳定性
  - 令牌桶算法
  - 漏桶算法
  - 计数器算法

## 高并发架构最佳实践

- **分层设计**，职责分离
- **无状态服务**，便于扩展
- 合理使用**缓存**，减少数据库压力
- **异步处理**，提高响应速度
- 实施**监控和告警**机制
- 定期进行**压力测试**和性能优化
- 制定完善的**容灾和恢复**方案
