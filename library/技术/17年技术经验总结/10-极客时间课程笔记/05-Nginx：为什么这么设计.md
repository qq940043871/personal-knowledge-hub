# 05 · Nginx：为什么这么设计

> 来源课程：《Nginx核心知识150讲》(155讲) + 《趣谈网络协议》 + 《Linux性能优化实战》35讲(C10K)
> 主线：**Nginx 是 C10K 问题的标准答案。它的一切设计都在回答：一台机器、一个进程，怎么同时伺候几万个连接？**
> 更新时间：2026-11-06

---

## 一、第一问：为什么是"多进程 + 单线程 worker"，而不是多线程或一连接一进程？

### 1.1 从历史包袱推起

```
Apache 1.x 时代：prefork（一连接一进程）/ worker（一连接一线程）
  → 万级连接 = 万级进程/线程
  → 内存：每线程 1MB 栈起步（CPU定律）；切换：10万连接 = 每秒几十万次切换
  → C10K 崩溃的本质：成本模型是 O(连接数) 的

Nginx 的答案：
  worker 数 = CPU 核数（worker_processes auto）
  每个 worker：单线程 + epoll 事件循环，伺候几万个连接
  → 成本模型变成 O(活跃事件数)，连接闲着不花钱
```

### 1.2 master-worker 架构与平滑重启

<svg style="max-width:100%;height:auto" width="960" height="430" viewBox="0 0 960 430" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">master-worker：管理面与数据面分离 + 平滑升级</text>
  <rect x="60" y="50" width="840" height="110" rx="10" fill="#EFF6FF" stroke="#3B82F6" stroke-width="2"/>
  <text x="480" y="78" text-anchor="middle" font-size="14" font-weight="bold" fill="#1D4ED8">master 进程（管理面：不碰业务）</text>
  <rect x="90" y="95" width="190" height="50" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="185" y="115" text-anchor="middle" font-size="12" fill="#1E3A8A">读取/校验配置</text><text x="185" y="133" text-anchor="middle" font-size="11" fill="#64748B">listen 80/443（先建好）</text>
  <rect x="310" y="95" width="190" height="50" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="405" y="115" text-anchor="middle" font-size="12" fill="#1E3A8A">fork worker 池</text><text x="405" y="133" text-anchor="middle" font-size="11" fill="#64748B">继承 listen fd（共享监听）</text>
  <rect x="530" y="95" width="180" height="50" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="620" y="115" text-anchor="middle" font-size="12" fill="#1E3A8A">信号处理</text><text x="620" y="133" text-anchor="middle" font-size="11" fill="#64748B">reload/quit/upgrade</text>
  <rect x="740" y="95" width="140" height="50" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="810" y="115" text-anchor="middle" font-size="12" fill="#1E3A8A">监控 worker</text><text x="810" y="133" text-anchor="middle" font-size="11" fill="#64748B">崩了拉起</text>
  <rect x="60" y="190" width="840" height="120" rx="10" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
  <text x="480" y="218" text-anchor="middle" font-size="14" font-weight="bold" fill="#166534">worker 进程 × N（数据面：N = CPU 核数，每个都是单线程 epoll）</text>
  <rect x="90" y="238" width="190" height="56" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/><text x="185" y="262" text-anchor="middle" font-size="12" fill="#14532D">worker-1</text><text x="185" y="280" text-anchor="middle" font-size="11" fill="#64748B">epoll + 状态机 + 内存池</text>
  <rect x="310" y="238" width="190" height="56" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/><text x="405" y="262" text-anchor="middle" font-size="12" fill="#14532D">worker-2</text><text x="405" y="280" text-anchor="middle" font-size="11" fill="#64748B">同构，无共享可变状态</text>
  <rect x="530" y="238" width="190" height="56" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/><text x="620" y="262" text-anchor="middle" font-size="12" fill="#14532D">worker-N</text><text x="620" y="280" text-anchor="middle" font-size="11" fill="#64748B">绑定 CPU 核 → 缓存亲和</text>
  <rect x="740" y="238" width="140" height="56" rx="6" fill="#FFFBEB" stroke="#F59E0B"/><text x="810" y="262" text-anchor="middle" font-size="12" fill="#92400E">共享内存</text><text x="810" y="280" text-anchor="middle" font-size="11" fill="#78350F">限流/统计/ ups状态</text>
  <rect x="60" y="330" width="840" height="84" rx="10" fill="#F5F3FF" stroke="#8B5CF6" stroke-width="2"/>
  <text x="480" y="356" text-anchor="middle" font-size="13" font-weight="bold" fill="#5B21B6">平滑重启（nginx -s reload）的时序：</text>
  <text x="90" y="378" font-size="12" fill="#4C1D95">master 读新配置并校验 → 失败则拒绝(旧配置继续服务) → fork 新 worker（用新配置，继承同一 listen fd）</text>
  <text x="90" y="398" font-size="12" fill="#4C1D95">→ 通知旧 worker：不再 accept，处理完存量连接后退出 → 全程端口不关、连接不掉</text>
  <text x="480" y="420" text-anchor="middle" font-size="12" fill="#7C3AED">对比 Redis(03篇)：数据在共享内存所以只能单进程；Nginx 连接无状态 → 进程可以随意换血</text>
</svg>

### 1.3 惊群问题：OS 给多进程出的难题

```
所有 worker 都 accept 同一个 listen fd → 新连接来时全部被唤醒，只有一个成功
  → 唤醒风暴（上下文切换白付）

Nginx 的演进：
  accept_mutex 锁：同一时刻只有一个 worker 在 accept（老方案）
  SO_REUSEPORT：内核按四元组把连接哈希到多个 listen fd，内核侧负载均衡
     —— 注意：这是内核能力外溢成应用架构的又一个例子
```

## 二、第二问：worker 内部怎么组织？——状态机 + 事件循环

<svg style="max-width:100%;height:auto" width="960" height="400" viewBox="0 0 960 400" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">worker 的一生：事件循环驱动状态机，永不阻塞</text>
  <rect x="70" y="60" width="200" height="70" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
  <text x="170" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#166534">epoll_wait()</text>
  <text x="170" y="110" text-anchor="middle" font-size="12" fill="#14532D">只返回就绪事件</text>
  <rect x="330" y="60" width="200" height="70" rx="8" fill="#EFF6FF" stroke="#3B82F6" stroke-width="2"/>
  <text x="430" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#1D4ED8">连接状态机</text>
  <text x="430" y="110" text-anchor="middle" font-size="12" fill="#1E3A8A">读请求头→解析→分发</text>
  <rect x="590" y="60" width="200" height="70" rx="8" fill="#FFFBEB" stroke="#F59E0B" stroke-width="2"/>
  <text x="690" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#92400E">上游/文件读取</text>
  <text x="690" y="110" text-anchor="middle" font-size="12" fill="#78350F">异步发起，绝不等待</text>
  <rect x="330" y="180" width="200" height="70" rx="8" fill="#FEF2F2" stroke="#EF4444" stroke-width="2"/>
  <text x="430" y="208" text-anchor="middle" font-size="13" font-weight="bold" fill="#991B1B">数据没到位？</text>
  <text x="430" y="230" text-anchor="middle" font-size="12" fill="#7F1D1D">注册事件 → 立即返回循环</text>
  <rect x="590" y="180" width="200" height="70" rx="8" fill="#F5F3FF" stroke="#8B5CF6" stroke-width="2"/>
  <text x="690" y="208" text-anchor="middle" font-size="13" font-weight="bold" fill="#5B21B6">写响应</text>
  <text x="690" y="230" text-anchor="middle" font-size="12" fill="#4C1D95">sendfile / proxy_buffering</text>
  <rect x="70" y="180" width="200" height="70" rx="8" fill="#FFF7ED" stroke="#F97316" stroke-width="2"/>
  <text x="170" y="208" text-anchor="middle" font-size="13" font-weight="bold" fill="#9A3412">三条铁律</text>
  <text x="170" y="230" text-anchor="middle" font-size="11" fill="#7C2D12">不阻塞·非阻塞fd·内存池</text>
  <line x1="270" y1="95" x2="325" y2="95" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="530" y1="95" x2="585" y2="95" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="690" y1="135" x2="530" y2="205" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="330" y1="215" x2="275" y2="215" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="530" y1="215" x2="585" y2="215" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="690" y1="255" x2="690" y2="140" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="70" y="290" width="860" height="90" rx="8" fill="#F9FAFB" stroke="#9CA3AF"/>
  <text x="480" y="316" text-anchor="middle" font-size="13" font-weight="bold" fill="#374151">三条铁律的物理出处</text>
  <text x="90" y="340" font-size="12" fill="#6B7280">铁律1 永不阻塞：阻塞 1ms = 几万连接陪等 1ms（成本模型 O(活跃事件) 的自杀行为）</text>
  <text x="90" y="360" font-size="12" fill="#6B7280">铁律2 非阻塞fd + ET/LT 触发模式：ET 只提醒一次，必须一口气读写到 EAGAIN</text>
  <text x="90" y="380" font-size="12" fill="#6B7280">铁律3 内存池：连接级预分配，请求结束整池回收 —— malloc/free 本身也是账单</text>
</svg>

## 三、第三问：静态资源为什么快？——零拷贝的组合拳

<svg style="max-width:100%;height:auto" width="960" height="330" viewBox="0 0 960 330" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">sendfile：从 4 拷贝 2 切换 到 1 拷贝 0 切换</text>
  <text x="160" y="56" text-anchor="middle" font-size="13" font-weight="bold" fill="#991B1B">传统 read+write</text>
  <rect x="40" y="70" width="120" height="46" rx="6" fill="#F9FAFB" stroke="#9CA3AF"/><text x="100" y="98" text-anchor="middle" font-size="12" fill="#374151">磁盘</text>
  <rect x="190" y="70" width="120" height="46" rx="6" fill="#EFF6FF" stroke="#3B82F6"/><text x="250" y="98" text-anchor="middle" font-size="12" fill="#1E3A8A">页缓存</text>
  <rect x="340" y="70" width="130" height="46" rx="6" fill="#FEF2F2" stroke="#EF4444"/><text x="405" y="98" text-anchor="middle" font-size="12" fill="#7F1D1D">用户缓冲区</text>
  <rect x="500" y="70" width="130" height="46" rx="6" fill="#EFF6FF" stroke="#3B82F6"/><text x="565" y="98" text-anchor="middle" font-size="12" fill="#1E3A8A">socket 缓冲区</text>
  <rect x="660" y="70" width="120" height="46" rx="6" fill="#F9FAFB" stroke="#9CA3AF"/><text x="720" y="98" text-anchor="middle" font-size="12" fill="#374151">网卡</text>
  <line x1="160" y1="93" x2="185" y2="93" stroke="#EF4444" stroke-width="2.5" marker-end="url(#arr)"/>
  <line x1="310" y1="93" x2="335" y2="93" stroke="#EF4444" stroke-width="2.5" marker-end="url(#arr)"/>
  <line x1="470" y1="93" x2="495" y2="93" stroke="#EF4444" stroke-width="2.5" marker-end="url(#arr)"/>
  <line x1="630" y1="93" x2="655" y2="93" stroke="#EF4444" stroke-width="2.5" marker-end="url(#arr)"/>
  <text x="405" y="134" text-anchor="middle" font-size="12" fill="#B91C1C">4 次拷贝（红）+ 2 次用户态/内核态切换</text>
  <text x="480" y="176" text-anchor="middle" font-size="13" font-weight="bold" fill="#166534">sendfile(+SG-DMA)</text>
  <rect x="40" y="190" width="120" height="46" rx="6" fill="#F9FAFB" stroke="#9CA3AF"/><text x="100" y="218" text-anchor="middle" font-size="12" fill="#374151">磁盘</text>
  <rect x="240" y="190" width="180" height="46" rx="6" fill="#ECFDF5" stroke="#10B981"/><text x="330" y="218" text-anchor="middle" font-size="12" fill="#14532D">页缓存（唯一中转）</text>
  <rect x="560" y="190" width="160" height="46" rx="6" fill="#F0FDF4" stroke="#22C55E"/><text x="640" y="218" text-anchor="middle" font-size="12" fill="#14532D">网卡（SG-DMA 直取）</text>
  <line x1="160" y1="213" x2="235" y2="213" stroke="#10B981" stroke-width="2.5" marker-end="url(#arr)"/>
  <line x1="420" y1="213" x2="555" y2="213" stroke="#10B981" stroke-width="2.5" marker-end="url(#arr)"/>
  <text x="480" y="254" text-anchor="middle" font-size="12" fill="#047857">2 次拷贝；带 SG-DMA 时页缓存→网卡也免 CPU 拷贝，共 1 次拷贝 0 次态切换</text>
  <rect x="60" y="274" width="840" height="42" rx="8" fill="#FFFBEB" stroke="#F59E0B"/>
  <text x="480" y="300" text-anchor="middle" font-size="13" fill="#92400E">配套开关：tcp_nopush(凑满MSS再发) + tcp_nodelay(keep-alive小包不等Nagle) + gzip(CPU换带宽)</text>
</svg>

代理模式则相反：`proxy_buffering` 把上游响应攒到本地缓冲再给客户端——
**上游和下游速度解耦，慢客户端不拖慢上游连接。**（缓冲区 = 背压阀门，网络定律 NET-1）

## 四、第四问：那些参数到底在调什么内核？

| Nginx 参数 | 内核真相 | 出事的症状 |
|-----------|---------|-----------|
| worker_connections | 每 worker 的 fd 数（受 ulimit -n 封顶） | too many open files |
| listen backlog | 全连接队列长度（受 somaxconn 封顶） | 突发高峰连接被 reset |
| keepalive_timeout | TIME_WAIT 治理（NET-3 定律） | 数万 TIME_WAIT 积压 |
| worker_processes | 绑核 → 缓存亲和、软中断分散 | si 高、worker 忙闲不均 |
| multi_accept | 一次唤醒 accept 尽量多连接 | 高频新建连接场景 |
| proxy_buffering | 用户态攒批解耦上下游 | 上游被慢客户端拖死 |

《Linux性能优化实战》35讲的结论在这验证：**C10K 不是调参调出来的，是事件驱动架构赢来的。**

## 五、约束小结

| 底层约束 | Nginx 的回应 |
|---------|-------------|
| 每连接一线程的成本 O(n) | epoll 事件循环，成本 O(活跃事件) |
| 线程切换/锁竞争 | 多进程 worker，worker 内单线程 |
| 惊群 | accept_mutex → SO_REUSEPORT |
| 拷贝贵 | sendfile + tcp_nopush |
| fd 是有限资源 | worker_connections + ulimit 配套 |
| 队列溢出 | backlog 与 somaxconn 对齐 |
| master 挂=全挂 | master 只做管理，业务全在 worker，崩溃自动拉起 |
| 配置变更要停服 | 新旧 worker 共享 listen fd 接班（平滑重启） |

---

> 下一篇：[06-JVM](06-JVM：为什么这么设计.md) —— 换个角度：一个"用软件模拟的计算机"，如何老老实实落在 Linux 进程模型上。
