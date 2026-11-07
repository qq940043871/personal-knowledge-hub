# 03 · Redis：为什么这么设计

> 来源课程：《Redis核心技术与实战》(53讲) + 《数据结构与算法之美》17/52讲 + 《Linux性能优化实战》29讲
> 主线：**Redis 是把"内存 + 单线程 + epoll"三张牌打到极致的典范。它的每个"怪设计"，都是对某条底层定律的正面回答。**
> 更新时间：2026-11-06

---

## 一、第一问：为什么敢用单线程？

### 1.1 推导过程（不是拍脑袋）

```
前提1：数据全在内存，一次操作 ~100ns（IO定律）
前提2：瓶颈不在 CPU，而在网络 IO —— 等包、收包（网络定律）
前提3：多线程要付出 —— 锁竞争、上下文切换、内存开销（CPU定律 CPU-1/3）

结论：单线程 + epoll 事件循环
  - 没有"并发修改共享数据"→ 不用加锁 → 实现简单、无死锁
  - 没有线程切换 → 每次操作都实打实花在数据上
  - 内核帮你盯着几万个连接，谁就绪叫谁（IO定律 3.3）
```

### 1.2 运行时全貌：其实不是一个线程在战斗

<svg style="max-width:100%;height:auto" width="960" height="480" viewBox="0 0 960 480" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">Redis 进程内部全景：命令执行单线程，其他各有分工</text>
  <rect x="40" y="50" width="880" height="400" rx="10" fill="#F9FAFB" stroke="#9CA3AF" stroke-width="2"/>
  <text x="480" y="78" text-anchor="middle" font-size="14" font-weight="bold" fill="#374151">redis-server 进程边界</text>
  <rect x="70" y="95" width="180" height="60" rx="8" fill="#DBEAFE" stroke="#3B82F6"/>
  <text x="160" y="120" text-anchor="middle" font-size="13" font-weight="bold" fill="#1D4ED8">客户端连接 ×N</text>
  <text x="160" y="140" text-anchor="middle" font-size="12" fill="#1E3A8A">RESP 协议 / pipeline</text>
  <rect x="290" y="95" width="180" height="60" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
  <text x="380" y="120" text-anchor="middle" font-size="13" font-weight="bold" fill="#065F46">IO 线程池 (6.0+)</text>
  <text x="380" y="140" text-anchor="middle" font-size="12" fill="#14532D">只做读包/写包，可开关</text>
  <rect x="510" y="95" width="180" height="60" rx="8" fill="#F5F3FF" stroke="#8B5CF6" stroke-width="2"/>
  <text x="600" y="120" text-anchor="middle" font-size="13" font-weight="bold" fill="#5B21B6">命令执行线程（唯一）</text>
  <text x="600" y="140" text-anchor="middle" font-size="12" fill="#4C1D95">事件循环 + 全部数据结构</text>
  <rect x="730" y="95" width="160" height="60" rx="8" fill="#FFFBEB" stroke="#F59E0B"/>
  <text x="810" y="120" text-anchor="middle" font-size="13" font-weight="bold" fill="#92400E">后台线程</text>
  <text x="810" y="140" text-anchor="middle" font-size="12" fill="#78350F">AOF fsync / 惰性释放</text>
  <line x1="220" y1="125" x2="285" y2="125" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="470" y1="125" x2="505" y2="125" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="690" y1="125" x2="725" y2="125" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="120" y="190" width="500" height="110" rx="8" fill="#FFFFFF" stroke="#8B5CF6"/>
  <text x="370" y="215" text-anchor="middle" font-size="13" font-weight="bold" fill="#5B21B6">内存数据结构（唯一共享区，单线程所以无锁）</text>
  <rect x="140" y="232" width="140" height="30" rx="5" fill="#F5F3FF" stroke="#C4B5FD"/><text x="210" y="252" text-anchor="middle" font-size="12" fill="#4C1D95">dict 渐进式rehash</text>
  <rect x="300" y="232" width="140" height="30" rx="5" fill="#F5F3FF" stroke="#C4B5FD"/><text x="370" y="252" text-anchor="middle" font-size="12" fill="#4C1D95">skiplist(ZSET)</text>
  <rect x="460" y="232" width="140" height="30" rx="5" fill="#F5F3FF" stroke="#C4B5FD"/><text x="530" y="252" text-anchor="middle" font-size="12" fill="#4C1D95">listpack/quicklist</text>
  <rect x="140" y="266" width="140" height="26" rx="5" fill="#F5F3FF" stroke="#C4B5FD"/><text x="210" y="284" text-anchor="middle" font-size="12" fill="#4C1D95">SDS 字符串</text>
  <rect x="300" y="266" width="140" height="26" rx="5" fill="#F5F3FF" stroke="#C4B5FD"/><text x="370" y="284" text-anchor="middle" font-size="12" fill="#4C1D95">过期字典(2个dict)</text>
  <rect x="460" y="266" width="140" height="26" rx="5" fill="#F5F3FF" stroke="#C4B5FD"/><text x="530" y="284" text-anchor="middle" font-size="12" fill="#4C1D95">近似LRU时钟字段</text>
  <rect x="120" y="330" width="250" height="95" rx="8" fill="#FEF2F2" stroke="#EF4444"/>
  <text x="245" y="355" text-anchor="middle" font-size="13" font-weight="bold" fill="#991B1B">持久化（借内核的力）</text>
  <text x="245" y="378" text-anchor="middle" font-size="12" fill="#7F1D1D">bgsave: fork 子进程 + COW</text>
  <text x="245" y="398" text-anchor="middle" font-size="12" fill="#7F1D1D">AOF: 缓冲 → everysec fsync</text>
  <text x="245" y="416" text-anchor="middle" font-size="12" fill="#7F1D1D">重写: 也是 fork + COW</text>
  <rect x="420" y="330" width="240" height="95" rx="8" fill="#EFF6FF" stroke="#3B82F6"/>
  <text x="540" y="355" text-anchor="middle" font-size="13" font-weight="bold" fill="#1D4ED8">主从复制</text>
  <text x="540" y="378" text-anchor="middle" font-size="12" fill="#1E3A8A">全量 = bgsave + 传 RDB</text>
  <text x="540" y="398" text-anchor="middle" font-size="12" fill="#1E3A8A">增量 = repl_backlog 环形缓冲</text>
  <text x="540" y="416" text-anchor="middle" font-size="12" fill="#1E3A8A">psync 断点续传</text>
  <rect x="700" y="330" width="230" height="95" rx="8" fill="#F0FDF4" stroke="#22C55E"/>
  <text x="815" y="355" text-anchor="middle" font-size="13" font-weight="bold" fill="#166534">运维红线（物理约束）</text>
  <text x="815" y="378" text-anchor="middle" font-size="12" fill="#14532D">实例 ≤10GB（fork页表成本）</text>
  <text x="815" y="398" text-anchor="middle" font-size="12" fill="#14532D">禁 THP · 防被换到 Swap</text>
  <text x="815" y="416" text-anchor="middle" font-size="12" fill="#14532D">KEYS/大key = 全员陪等</text>
</svg>

**为什么 6.0 的 IO 多线程是安全的：** IO 线程只搬字节，命令执行仍串行——
**共享数据永远只有一只手在碰**，锁就没有存在必要。这是"多线程收益"与"单线程一致性"的精确切割。

### 1.3 单线程的边界（知道边界才算懂设计）

```
边界1：单核 CPU 上限 ≈ 10万 QPS 级别 → 突破：多实例分片 / 集群
边界2：大 key、慢命令(DEL 大集合、KEYS)会阻塞所有人
       → hdel 分批、SCAN 代替 KEYS、UNLINK 惰性删除(丢给后台线程)
边界3：CPU 打满前，先到的往往是网卡/序列化瓶颈 → pipeline 攒批
       pipeline 一次发 N 条命令：省 N-1 次 RTT（0.5ms×N → 1 次），
       这就是《实战》里"Redis 慢，先看是不是没用 pipeline"的原因
```

## 二、第二问：为什么数据结构这么"花"？

《数据结构与算法之美》52讲专门剖析过 Redis 的结构选型，核心逻辑一句话：
**每种类型都是一个"编码体系"，小数据用省内存的紧凑编码，大了才换性能编码。**

| 类型 | 小数据编码 | 大数据编码 | 为什么要切换 |
|------|-----------|-----------|-------------|
| String | int / embstr | raw(SDS) | SDS 头部开销对短串不划算 |
| Hash | listpack(ziplist) | hashtable | 元素多了 O(n) 遍历扛不住 |
| List | listpack | quicklist(listpack 的双向链表) | 链表指针税 vs 数组搬家的折中 |
| Set | intset | hashtable | 纯整数数组最省 |
| ZSET | listpack | 跳表 + dict 双结构 | 见下 |

### 2.1 SDS（简单动态字符串）：一个 struct 的三个心机

```c
struct sdshdr {
    int len;      // ① O(1) 拿长度（C 字符串要 strlen 扫一遍）
    int alloc;    // ② 空间预分配 + 惰性释放，减少 realloc
    char buf[];   // ③ 二进制安全：按长度读，不怕 \0
};
```

### 2.2 跳表：为什么 ZSET 不用红黑树（《之美》17讲的官方答案）

```
ZSET 的日常操作：按 score 范围查询 + 排名
  跳表：底层链表顺序走，O(log n)，代码几十行
  红黑树：中序遍历实现范围查询，旋转复杂，范围操作代码难写对
加分项：跳表还存了 span（跨度），ZRANK 按排名 O(log n) 直接算出来
```

### 2.3 渐进式 rehash：把最坏 O(n) 拆碎

<svg style="max-width:100%;height:auto" width="960" height="330" viewBox="0 0 960 330" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">渐进式 rehash：两张表并存，搬家成本摊到每次操作</text>
  <rect x="70" y="60" width="260" height="200" rx="8" fill="#FEF2F2" stroke="#EF4444" stroke-width="2"/>
  <text x="200" y="88" text-anchor="middle" font-size="14" font-weight="bold" fill="#991B1B">ht[0] 旧表（正在清空）</text>
  <rect x="90" y="105" width="220" height="24" rx="4" fill="#FFFFFF" stroke="#FCA5A5"/><text x="200" y="122" text-anchor="middle" font-size="12" fill="#7F1D1D">bucket0 ▸ 已搬走</text>
  <rect x="90" y="135" width="220" height="24" rx="4" fill="#FFFFFF" stroke="#FCA5A5"/><text x="200" y="152" text-anchor="middle" font-size="12" fill="#7F1D1D">bucket1 ▸ 已搬走</text>
  <rect x="90" y="165" width="220" height="24" rx="4" fill="#FFF7ED" stroke="#F97316"/><text x="200" y="182" text-anchor="middle" font-size="12" fill="#7C2D12">bucket2 ◂ rehashidx 指针</text>
  <rect x="90" y="195" width="220" height="24" rx="4" fill="#FFFFFF" stroke="#FCA5A5"/><text x="200" y="212" text-anchor="middle" font-size="12" fill="#7F1D1D">bucket3 ▸ 还有数据</text>
  <rect x="90" y="225" width="220" height="24" rx="4" fill="#FFFFFF" stroke="#FCA5A5"/><text x="200" y="242" text-anchor="middle" font-size="12" fill="#7F1D1D">bucket4 ▸ 还有数据</text>
  <rect x="630" y="60" width="260" height="200" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
  <text x="760" y="88" text-anchor="middle" font-size="14" font-weight="bold" fill="#166534">ht[1] 新表（正在填入）</text>
  <rect x="650" y="105" width="220" height="24" rx="4" fill="#FFFFFF" stroke="#6EE7B7"/><text x="760" y="122" text-anchor="middle" font-size="12" fill="#14532D">新 bucket（扩容×2）</text>
  <rect x="650" y="135" width="220" height="24" rx="4" fill="#FFFFFF" stroke="#6EE7B7"/><text x="760" y="152" text-anchor="middle" font-size="12" fill="#14532D">…</text>
  <rect x="650" y="165" width="220" height="24" rx="4" fill="#D1FAE5" stroke="#10B981"/><text x="760" y="182" text-anchor="middle" font-size="12" fill="#14532D">新插入只进新表</text>
  <rect x="650" y="195" width="220" height="55" rx="4" fill="#FFFFFF" stroke="#6EE7B7"/>
  <text x="760" y="218" text-anchor="middle" font-size="12" fill="#14532D">搬迁规则：每次 CRUD 顺带搬一个桶</text>
  <text x="760" y="238" text-anchor="middle" font-size="12" fill="#14532D">定时任务 also 搬（serverCron 分片）</text>
  <line x1="330" y1="170" x2="620" y2="170" stroke="#F97316" stroke-width="2.5" stroke-dasharray="8,4" marker-end="url(#arr)"/>
  <text x="475" y="158" text-anchor="middle" font-size="13" font-weight="bold" fill="#C2410C">每次命令捎带搬一桶</text>
  <rect x="70" y="280" width="820" height="36" rx="6" fill="#FFFBEB" stroke="#F59E0B"/>
  <text x="480" y="303" text-anchor="middle" font-size="13" fill="#92400E">搬迁期间：读请求查两张表，写请求删旧插新 —— 最坏 O(n) 被拆成百万次 O(1)</text>
</svg>

**动机：单线程不能接受"一次 put 触发百万级搬迁"的最坏情况**——这是 02 篇"抹平最坏情况"工程推论的教科书实现。

## 三、第三问：持久化为什么长这样？——OS 在这里直接"定规矩"

这是**操作系统约束上层设计**最生动的一章。

### 3.1 RDB：fork + 写时复制，借内核的力做快照

<svg style="max-width:100%;height:auto" width="960" height="400" viewBox="0 0 960 400" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">bgsave 时序：fork+COW 让"秒级快照"与"持续服务"并存</text>
  <line x1="140" y1="60" x2="140" y2="360" stroke="#8B5CF6" stroke-width="2"/>
  <text x="140" y="52" text-anchor="middle" font-size="13" font-weight="bold" fill="#5B21B6">主进程（继续服务）</text>
  <line x1="480" y1="140" x2="480" y2="360" stroke="#10B981" stroke-width="2"/>
  <text x="480" y="132" text-anchor="middle" font-size="13" font-weight="bold" fill="#166534">子进程（只管落盘）</text>
  <line x1="820" y1="60" x2="820" y2="360" stroke="#EF4444" stroke-width="2"/>
  <text x="820" y="52" text-anchor="middle" font-size="13" font-weight="bold" fill="#991B1B">内核（页表/COW）</text>
  <line x1="140" y1="95" x2="475" y2="95" stroke="#8B5CF6" stroke-width="2"/>
  <text x="150" y="86" font-size="12" fill="#5B21B6">① 收到 BGSAVE：fork() —— 只复制页表，不复制物理页（几十ms）</text>
  <line x1="480" y1="140" x2="815" y2="140" stroke="#10B981" stroke-width="2"/>
  <text x="490" y="131" font-size="12" fill="#166534">② 子进程遍历虚拟页 → 触发缺页 → 内核建立真实映射 → 序列化写 RDB</text>
  <line x1="140" y1="200" x2="815" y2="200" stroke="#EF4444" stroke-width="2"/>
  <text x="150" y="191" font-size="12" fill="#991B1B">③ 主进程此刻起改数据：写某页 → 内核复制该页(COW) → 主进程改副本</text>
  <text x="150" y="222" font-size="12" fill="#7F1D1D">   子进程看到的永远是 fork 那一刻的"照片"</text>
  <line x1="480" y1="270" x2="140" y2="270" stroke="#10B981" stroke-width="2" marker-end="url(#arr)"/>
  <text x="300" y="261" font-size="12" fill="#166534">④ 子进程写完 → 临时文件原子替换 → 退出，通知主进程</text>
  <line x1="140" y1="320" x2="475" y2="320" stroke="#8B5CF6" stroke-width="2" marker-end="url(#arr)"/>
  <text x="150" y="311" font-size="12" fill="#5B21B6">⑤ 继续服务，全程只付"fork页表 + 被改页的复制"两笔账</text>
  <rect x="60" y="355" width="850" height="34" rx="6" fill="#FEF2F2" stroke="#EF4444"/>
  <text x="485" y="377" text-anchor="middle" font-size="13" font-weight="bold" fill="#991B1B">为什么实例要控制在 10GB 内：fork 时长 ∝ 页表大小，20GB 实例 fork 可能几百 ms——单线程世界里=所有请求卡几百ms</text>
</svg>

《Linux性能优化实战》29讲的 Redis 延迟案例，第一个要怀疑的就是这个；
第二个是 Swap（被换出的页在 fork 遍历时引发主缺页风暴）。

### 3.2 AOF：诚实税（fsync）的分期付款

```
写命令 → AOF 缓冲 → append 到文件 → 何时 fsync？
  always：每命令都刷，丢 0 数据，吞吐崩（磁盘串行瓶颈）
  everysec：后台线程每秒刷一次 ← 默认，最多丢 1 秒（OS page cache 的讨价还价）
  no：给内核，快但不可控
AOF 重写：也是 fork + COW，根据当前内存生成最小命令集
  重写期间的写命令同时进 "AOF缓冲 + 重写缓冲"，重写完一次性追加
```

> RDB vs AOF 的选择本质：**"恢复速度/文件大小" vs "数据丢失窗口"**——
> 4.0 之后混合持久化（RDB 头 + AOF 尾）= 两头都要，前提是内核提供了 fork/COW 和 page cache。

### 3.3 主从复制的底层联想

- 全量同步 = bgsave + 传输 RDB + repl_backlog 增量（环形缓冲区）
- 复制积压缓冲区太小 → 网络抖一下就全量重传 → **又是一笔"内存换网络容错"的账**
- 主从延迟的物理来源：主库执行是内存速度，从库要过网络 + 重放——**读写分离读旧数据的根**（10篇演进路径呼应）

## 四、第四问：过期删除和内存淘汰为什么这么"糙"？

```
过期删除：惰性删除(访问时查) + 定期抽样删除
  → 为什么不搞精确定时器？10亿 key 挂 10亿 timer，堆/时间轮也扛不住

内存淘汰：近似 LRU —— 每个对象存 24bit 时钟，淘汰时随机抽 5 个挑最久未用的
  → 为什么不用真 LRU？真 LRU 需要全局双向链表，锁竞争 + 额外 16B/key（02篇 LRU 改造清单）
  → 4.0 LFU：时钟字段复用为计数器 + 衰减 —— "最近使用"不如"使用频率"抗污染

Redis 的哲学：在单线程世界里，"够用的近似"永远胜过"昂贵的精确"。
```

## 五、集群：单机的天花板怎么破

```
为什么不客户端分片就够？
  客户端分片：扩容要重分配数据，运维自己做，故障转移自理
  集群方案：16384 个 slot 分片 + gossip 协议自动故障转移
    为什么是 16384：心跳包携带 slot 位图，16384 bit = 2KB，
    65536 会把心跳撑到 8KB——协议设计里全是带宽账

CAS 风格的坑：跨 slot 的多 key 操作/事务/Lua 不支持
  → 业务上要么 hash tag 强制同 slot（{user1000}.profile 与 {user1000}.orders），
    要么接受"关联数据同 slot"的设计约束
```

## 六、约束小结：Redis 被什么推着走

| 底层约束 | Redis 的回应 |
|---------|-------------|
| 网络IO等待 >> 内存计算 | 单线程 + epoll 事件循环（6.0 IO多线程补刀） |
| 上下文切换/锁昂贵 | 无锁化，命令执行永不多线程 |
| fork+COW 便宜、页表复制线性于内存 | RDB/AOF重写都借 fork；"实例别超过10GB"的经验值 |
| page cache + fsync 是诚实税 | AOF everysec 的"最多丢1秒" |
| 全局精确结构太贵 | 近似LRU、定期抽样过期 |
| 单机内存上限 + 成本 | 惰性/紧凑编码、分片集群(16384 slot) |
| 大 value = 一次大拷贝 | RESP 协议、客户端 pipeline 攒批、UNLINK 惰性删 |
| 跨机房/跨节点 RTT | hash tag 就近、读写分离就近访问 |

**反面清单（都是和底层对着干的用法，出事别冤枉 Redis）：**
KEYS *；10MB 的 String；把 Redis 当队列用还开 everysec；实例 30GB 还不管 fork；
容器里内存贴着 limit 跑 → 被 swap（Linux性能优化实战 19/20/29 讲连环案例）；开 THP。

---

> 下一篇：[04-MySQL](04-MySQL：为什么这么设计.md) —— 同样是 fsync 诚实税，为什么 MySQL 答得完全不同？
