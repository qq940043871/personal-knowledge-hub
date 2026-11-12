# CDN加速 - 架构师学习笔记

CDN（Content Delivery Network，内容分发网络）是一种**分布式网络架构**，通过将内容分发到全球各地的边缘节点，使用户能够从**最近的节点**获取所需内容，从而显著提高网站访问速度和用户体验。

## CDN工作原理

### 工作流程

1. **用户请求**：用户访问网站资源
2. **DNS解析**：智能DNS返回最近节点IP
3. **节点响应**：边缘节点返回缓存内容
4. **回源获取**：节点缺失时回源站获取

### 核心组件

- **边缘节点**：分布在全球各地的缓存服务器
- **源站服务器**：内容源站，存储原始内容
- **负载均衡系统**：智能调度用户请求到最优节点
- **DNS系统**：将域名解析到最近的CDN节点
- **监控系统**：实时监控CDN节点状态和性能

*图：CDN 请求处理流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 210" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="30" y="83" width="100" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="80" y="110" text-anchor="middle" font-size="14" fill="#1e293b">用户请求</text>
  <line x1="130" y1="105" x2="173" y2="105" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="152" y="95" text-anchor="middle" font-size="12" fill="#475569">DNS解析</text>
  <rect x="175" y="83" width="120" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="235" y="110" text-anchor="middle" font-size="14" fill="#1e293b">智能DNS</text>
  <line x1="295" y1="105" x2="338" y2="105" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="317" y="95" text-anchor="middle" font-size="12" fill="#475569">最近节点IP</text>
  <rect x="340" y="83" width="130" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="405" y="110" text-anchor="middle" font-size="14" fill="#1e293b">边缘节点</text>
  <line x1="470" y1="93" x2="518" y2="66" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="492" y="70" text-anchor="middle" font-size="12" fill="#475569">命中</text>
  <line x1="470" y1="117" x2="518" y2="146" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="492" y="146" text-anchor="middle" font-size="12" fill="#475569">未命中</text>
  <rect x="520" y="40" width="170" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="605" y="67" text-anchor="middle" font-size="14" fill="#1e293b">返回缓存内容</text>
  <rect x="520" y="130" width="170" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="605" y="157" text-anchor="middle" font-size="14" fill="#1e293b">回源站获取</text>
</svg>

## CDN优势

- **提高访问速度**：用户从就近节点获取内容，大幅减少网络延迟。
- **增强可靠性**：分布式架构提供冗余，单点故障不影响整体服务。
- **降低源站负载**：大部分请求由CDN节点处理，减轻源站压力。
- **全球覆盖**：节点遍布全球，为世界各地用户提供优质服务。
- **安全防护**：提供DDoS防护、WAF等安全功能。
- **节省带宽成本**：减少源站带宽消耗，降低运营成本。

## CDN缓存策略

### 缓存控制

#### HTTP头部控制

- 通过HTTP响应头控制缓存行为

```http
Cache-Control: max-age=3600
Expires: Wed, 21 Oct 2023 07:28:00 GMT
ETag: "33a64df551425fcc55e4d42a148795d5f8b7c6"
```

#### CDN控制台配置

- 通过CDN服务商控制台配置缓存规则
  - 目录刷新
  - URL预热
  - 缓存过期时间设置

### 缓存更新策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 主动刷新 | 手动触发CDN节点缓存更新 | 紧急更新、BUG修复 |
| URL预热 | 提前将资源缓存到CDN节点 | 热点资源、大促活动 |
| 智能缓存 | 根据访问模式自动调整缓存策略 | 动态内容、个性化资源 |

## 主流CDN服务商

### 阿里云CDN

- 阿里巴巴集团旗下的CDN服务，覆盖**全球2800+节点**。
  - 智能调度
  - 安全防护
  - 实时监控

### 腾讯云CDN

- 腾讯云提供的CDN服务，拥有**1200+国内外节点**。
  - 动态加速
  - 视频直播
  - HTTPS优化

### Cloudflare

- 国际知名CDN服务商，提供**免费和付费服务**。
  - DDoS防护
  - WAF防火墙
  - 全球Anycast网络

## CDN应用场景

### 静态资源加速

- 图片、CSS、JavaScript文件
- 网站Logo和图标
- 字体文件
- 文档和压缩包

### 音视频加速

- 在线视频点播
- 直播流媒体
- 音频文件
- 短视频平台

### 大文件下载

- 软件安装包
- 游戏客户端
- 系统镜像
- 应用更新包

### 移动应用加速

- APP内容分发
- 移动游戏资源
- OTA更新
- 移动网站优化

## CDN配置优化

### 性能优化

#### 压缩优化

- Gzip压缩静态资源
- 图片格式优化（WebP、AVIF）
- 资源合并减少请求数

#### 缓存优化

- 合理设置缓存时间
- 版本号控制缓存更新
- 条件请求减少传输

### 安全配置

#### 防盗链

- 限制资源引用来源，防止盗用

#### HTTPS

- 启用HTTPS加密传输

#### 访问控制

- IP黑白名单、频率限制

## 监控与分析

### 关键指标

- **命中率**：CDN节点缓存命中比例
- **响应时间**：用户访问资源的平均时间
- **带宽使用**：CDN节点的带宽消耗情况
- **请求数**：CDN节点处理的请求数量

### 常见问题排查

- **缓存未更新**：检查缓存时间设置
- **资源404**：检查源站资源是否存在
- **访问缓慢**：检查节点分布和网络状况
- **安全攻击**：启用防护功能

## CDN最佳实践

- 合理规划**CDN节点分布**
- 设置合适的**缓存策略和过期时间**
- 启用**压缩和HTTPS**优化
- 实施**安全防护**措施
- 建立完善的**监控和告警**机制
- 定期分析**访问日志和性能数据**
- 制定**应急预案**和故障处理流程
