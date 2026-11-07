# 04 · MySQL：为什么这么设计

> 来源课程：《MySQL实战45讲》(49讲) + 《数据结构与算法之美》48/50讲 + 《Linux性能优化实战》28讲
> 主线：**MySQL 生在磁盘时代，它的整个架构就是一份"如何与磁盘慢十万倍共存"的详细施工图——顺带回答"既要快、又不能丢数据"这个矛盾。**
> 更新时间：2026-11-06

---

## 一、InnoDB 全景：一条 SQL 的完整旅程

<svg style="max-width:100%;height:auto" width="960" height="520" viewBox="0 0 960 520" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">一条 UPDATE 的旅程：Server 层与 InnoDB 层的接力</text>
  <rect x="40" y="50" width="880" height="120" rx="10" fill="#EFF6FF" stroke="#3B82F6" stroke-width="2"/>
  <text x="480" y="76" text-anchor="middle" font-size="14" font-weight="bold" fill="#1D4ED8">Server 层（跨存储引擎，管 SQL 语义与 binlog）</text>
  <rect x="60" y="92" width="130" height="56" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="125" y="114" text-anchor="middle" font-size="12" fill="#1E3A8A">连接器</text><text x="125" y="132" text-anchor="middle" font-size="11" fill="#64748B">认证/连接池</text>
  <rect x="210" y="92" width="130" height="56" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="275" y="114" text-anchor="middle" font-size="12" fill="#1E3A8A">分析器/优化器</text><text x="275" y="132" text-anchor="middle" font-size="11" fill="#64748B">选索引/改写SQL</text>
  <rect x="360" y="92" width="130" height="56" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="425" y="114" text-anchor="middle" font-size="12" fill="#1E3A8A">执行器</text><text x="425" y="132" text-anchor="middle" font-size="11" fill="#64748B">调引擎接口</text>
  <rect x="510" y="92" width="190" height="56" rx="6" fill="#FFF7ED" stroke="#F97316"/><text x="605" y="114" text-anchor="middle" font-size="12" font-weight="bold" fill="#9A3412">binlog（Server 层日志）</text><text x="605" y="132" text-anchor="middle" font-size="11" fill="#9A3412">归档/复制，逻辑日志</text>
  <rect x="720" y="92" width="180" height="56" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="810" y="114" text-anchor="middle" font-size="12" fill="#1E3A8A">两阶段提交协调</text><text x="810" y="132" text-anchor="middle" font-size="11" fill="#64748B">见下方时序</text>
  <line x1="190" y1="120" x2="205" y2="120" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="340" y1="120" x2="355" y2="120" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="490" y1="120" x2="505" y2="120" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="40" y="200" width="640" height="200" rx="10" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
  <text x="360" y="226" text-anchor="middle" font-size="14" font-weight="bold" fill="#166534">InnoDB 层（管数据与崩溃恢复）</text>
  <rect x="60" y="242" width="180" height="60" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/><text x="150" y="266" text-anchor="middle" font-size="12" fill="#14532D">Buffer Pool</text><text x="150" y="284" text-anchor="middle" font-size="11" fill="#64748B">数据页缓存+改良LRU</text>
  <rect x="60" y="316" width="180" height="60" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/><text x="150" y="340" text-anchor="middle" font-size="12" fill="#14532D">redo log buffer</text><text x="150" y="358" text-anchor="middle" font-size="11" fill="#64748B">物理日志，顺序写</text>
  <rect x="270" y="242" width="180" height="60" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/><text x="360" y="266" text-anchor="middle" font-size="12" fill="#14532D">undo log + 版本链</text><text x="360" y="284" text-anchor="middle" font-size="11" fill="#64748B">MVCC 读旧版本</text>
  <rect x="270" y="316" width="180" height="60" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/><text x="360" y="340" text-anchor="middle" font-size="12" fill="#14532D">change buffer</text><text x="360" y="358" text-anchor="middle" font-size="11" fill="#64748B">二级索引写攒批</text>
  <rect x="480" y="242" width="180" height="60" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/><text x="570" y="266" text-anchor="middle" font-size="12" fill="#14532D">主键 B+ 树（聚簇）</text><text x="570" y="284" text-anchor="middle" font-size="11" fill="#64748B">数据即索引</text>
  <rect x="480" y="316" width="180" height="60" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/><text x="570" y="340" text-anchor="middle" font-size="12" fill="#14532D">二级 B+ 树 ×N</text><text x="570" y="358" text-anchor="middle" font-size="11" fill="#64748B">叶子存主键，回表</text>
  <rect x="720" y="200" width="200" height="200" rx="10" fill="#FEF2F2" stroke="#EF4444" stroke-width="2"/>
  <text x="820" y="228" text-anchor="middle" font-size="14" font-weight="bold" fill="#991B1B">磁盘（真贵）</text>
  <rect x="740" y="244" width="160" height="42" rx="6" fill="#FFFFFF" stroke="#FCA5A5"/><text x="820" y="262" text-anchor="middle" font-size="12" fill="#7F1D1D">redo log 文件</text><text x="820" y="278" text-anchor="middle" font-size="11" fill="#B91C1C">顺序写 + fsync</text>
  <rect x="740" y="296" width="160" height="42" rx="6" fill="#FFFFFF" stroke="#FCA5A5"/><text x="820" y="314" text-anchor="middle" font-size="12" fill="#7F1D1D">binlog 文件</text><text x="820" y="330" text-anchor="middle" font-size="11" fill="#B91C1C">顺序写 + fsync</text>
  <rect x="740" y="348" width="160" height="42" rx="6" fill="#FFF7ED" stroke="#F97316"/><text x="820" y="366" text-anchor="middle" font-size="12" fill="#7C2D12">表空间 .ibd</text><text x="820" y="382" text-anchor="middle" font-size="11" fill="#9A3412">脏页回写（随机！）</text>
  <line x1="240" y1="272" x2="265" y2="272" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="450" y1="272" x2="475" y2="272" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="150" y1="302" x2="150" y2="311" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="240" y1="346" x2="265" y2="346" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="700" y1="130" x2="740" y2="258" stroke="#F97316" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="240" y1="376" x2="735" y2="270" stroke="#EF4444" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="40" y="420" width="880" height="80" rx="8" fill="#FFFBEB" stroke="#F59E0B"/>
  <text x="480" y="446" text-anchor="middle" font-size="13" font-weight="bold" fill="#92400E">设计重心：脏页留在内存慢慢刷（右侧唯一的随机写），提交只付两笔顺序写的钱（redo + binlog）</text>
  <text x="480" y="472" text-anchor="middle" font-size="12" fill="#A16207">WAL = Write-Ahead Logging：先写日志再写数据页 —— 把"随机写页"换成了"顺序写日志 + 后台异步刷页"</text>
</svg>

## 二、第一问：索引为什么是 B+ 树？

### 2.1 从物理约束推出来（不是背结论）

```
目标：在一亿行数据上，尽快找到/扫过一段数据
介质：磁盘，随机 IO ~10ms(HDD)/100μs(SSD)，顺序读飞快（IO定律）

逐个排除：
  散列表    → 无范围查询能力，pass（02篇）
  红黑树    → 二叉，1亿数据树高 ~27 层 = 27 次随机 IO，pass
  跳表      → 每一"跳"都是一次随机IO、层数随数据涨，pass
  B 树      → 非叶子也存数据 → 扇出小、范围查询要回旋，次优
  B+ 树     → ✔ 非叶子只存键 → 扇出 ~1000+
              ✔ 一个节点 = 一个 16KB 页，树高 3 层 ≈ 2000 万行
              ✔ 叶子节点双向链表 → 范围扫描顺链走，全是顺序 IO
              ✔ 树高 = 磁盘 IO 次数，3 次即可定位（根节点还常驻内存）
```

**聚簇索引 vs 二级索引：**
数据本身就按主键 B+ 树组织（聚簇），二级索引叶子存主键值 → 回表 = 再走一棵树。
所以有了：覆盖索引（不回表）、最左前缀（少建树）、索引下推（引擎层先过滤）——
**所有索引规范，翻译过来都是"少一次随机 IO"。**

### 2.2 change buffer：二级索引写的"攒批"

写多读少的二级索引，先记到 change buffer，等读到来时再合并——
又是一个"把随机写攒成合并操作"的折中，代价是读性能和崩溃恢复复杂度。

## 三、第二问：为什么先改内存、再写日志、最后落盘？

### 3.1 Buffer Pool：把磁盘装进内存（改良版 LRU）

<svg style="max-width:100%;height:auto" width="960" height="330" viewBox="0 0 960 330" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">InnoDB 改良版 LRU：防"一次全表扫描冲垮全部缓存"</text>
  <rect x="60" y="60" width="840" height="90" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
  <text x="480" y="86" text-anchor="middle" font-size="13" font-weight="bold" fill="#166534">young 区（5/8）· 真热点区，命中率主要靠它</text>
  <rect x="80" y="100" width="120" height="30" rx="5" fill="#FFFFFF" stroke="#6EE7B7"/><text x="140" y="120" text-anchor="middle" font-size="11" fill="#14532D">热点页A</text>
  <rect x="210" y="100" width="120" height="30" rx="5" fill="#FFFFFF" stroke="#6EE7B7"/><text x="270" y="120" text-anchor="middle" font-size="11" fill="#14532D">热点页B</text>
  <rect x="340" y="100" width="120" height="30" rx="5" fill="#FFFFFF" stroke="#6EE7B7"/><text x="400" y="120" text-anchor="middle" font-size="11" fill="#14532D">…</text>
  <rect x="700" y="100" width="180" height="30" rx="5" fill="#D1FAE5" stroke="#10B981"/><text x="790" y="120" text-anchor="middle" font-size="11" fill="#065F46">young 头部（新晋热点）</text>
  <rect x="60" y="170" width="840" height="90" rx="8" fill="#FFF7ED" stroke="#F97316" stroke-width="2"/>
  <text x="480" y="196" text-anchor="middle" font-size="13" font-weight="bold" fill="#9A3412">old 区（3/8）· 新页先从这里过安检</text>
  <rect x="700" y="210" width="180" height="30" rx="5" fill="#FFEDD5" stroke="#F97316"/><text x="790" y="230" text-anchor="middle" font-size="11" fill="#7C2D12">old 头部（新读入页）</text>
  <rect x="80" y="210" width="120" height="30" rx="5" fill="#FFFFFF" stroke="#FDBA74"/><text x="140" y="230" text-anchor="middle" font-size="11" fill="#7C2D12">快淘汰页</text>
  <rect x="210" y="210" width="120" height="30" rx="5" fill="#FFFFFF" stroke="#FDBA74"/><text x="270" y="230" text-anchor="middle" font-size="11" fill="#7C2D12">…</text>
  <rect x="340" y="210" width="120" height="30" rx="5" fill="#FFFFFF" stroke="#FDBA74"/><text x="400" y="230" text-anchor="middle" font-size="11" fill="#7C2D12">…</text>
  <line x1="790" y1="196" x2="790" y2="206" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="60" y="272" width="840" height="44" rx="8" fill="#F9FAFB" stroke="#9CA3AF"/>
  <text x="480" y="292" text-anchor="middle" font-size="13" fill="#374151">规则：新页只进 old 头部；在 old 区停留满 1s(innodb_old_blocks_time) 后再次被访问，才晋升 young</text>
  <text x="480" y="310" text-anchor="middle" font-size="12" fill="#6B7280">全表扫描：每页只被访问一次、又即刻滚出 old 区 → 污染被限制在 3/8 内，真热点安然无恙</text>
</svg>

朴素 LRU 的问题：备份/全表扫描这类"一次性扫过千万页"的操作，会把真热点全部挤出缓存（缓存污染）。
Redis 的"近似 LRU"（03篇）是同一问题的另一份答卷——**同一约束，两种预算，两种方案**。

### 3.2 redo log：WAL，把随机写换成顺序写（全文最重要的一页）

```
没有 redo log：每次事务把改过的页刷回磁盘 = 随机写 = 慢 + 无法保证原子
有 redo log：
  事务提交 → 顺序写 redo log(磁盘上的追加文件) → 返回成功
  脏页留到以后慢慢刷（顺序化、攒批化）
崩溃恢复：重启时重放 redo log，把没刷完的脏页补出来 → crash-safe
```

```
innodb_flush_log_at_trx_commit：
  =1  每次提交 fsync → 不丢（双1配置之一）
  =2  写到内核 page cache，每秒 fsync → 崩机器丢1秒（同 Redis AOF everysec）
  =0  每秒写+刷 → 崩进程也可能丢1秒
组提交：多个事务的 fsync 合并成一次 —— "贵的账单批量付"（01篇账单思想）
```

### 3.3 两阶段提交：为什么这么绕？

<svg style="max-width:100%;height:auto" width="1000" height="360" viewBox="0 0 1000 360" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="500" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">UPDATE 的七步 + 两阶段提交：两本日志的原子绑定</text>
  <line x1="120" y1="70" x2="120" y2="320" stroke="#8B5CF6" stroke-width="2"/>
  <text x="120" y="62" text-anchor="middle" font-size="13" font-weight="bold" fill="#5B21B6">执行路径</text>
  <line x1="480" y1="70" x2="480" y2="320" stroke="#EF4444" stroke-width="2"/>
  <text x="480" y="62" text-anchor="middle" font-size="13" font-weight="bold" fill="#991B1B">崩溃恢复的两条规则</text>
  <line x1="820" y1="70" x2="820" y2="320" stroke="#3B82F6" stroke-width="2"/>
  <text x="820" y="62" text-anchor="middle" font-size="13" font-weight="bold" fill="#1D4ED8">为什么必须两阶段</text>
  <line x1="120" y1="95" x2="115" y2="95" stroke="#8B5CF6" stroke-width="2"/>
  <text x="60" y="100" text-anchor="middle" font-size="12" fill="#4C1D95">① 读入页到</text>
  <text x="60" y="118" text-anchor="middle" font-size="12" fill="#4C1D95">Buffer Pool</text>
  <line x1="120" y1="140" x2="115" y2="140" stroke="#8B5CF6" stroke-width="2"/>
  <text x="60" y="145" text-anchor="middle" font-size="12" fill="#4C1D95">② 写 undo log</text>
  <text x="60" y="163" text-anchor="middle" font-size="12" fill="#4C1D95">(回滚/MVCC)</text>
  <line x1="120" y1="185" x2="115" y2="185" stroke="#8B5CF6" stroke-width="2"/>
  <text x="60" y="190" text-anchor="middle" font-size="12" fill="#4C1D95">③ 改内存页</text>
  <text x="60" y="208" text-anchor="middle" font-size="12" fill="#4C1D95">成脏页</text>
  <line x1="120" y1="230" x2="115" y2="230" stroke="#EF4444" stroke-width="2"/>
  <text x="42" y="235" text-anchor="middle" font-size="12" fill="#991B1B">④ redo log</text>
  <text x="42" y="253" text-anchor="middle" font-size="12" fill="#991B1B">prepare 状态</text>
  <line x1="120" y1="275" x2="115" y2="275" stroke="#F97316" stroke-width="2"/>
  <text x="42" y="280" text-anchor="middle" font-size="12" fill="#9A3412">⑤ 写 binlog</text>
  <text x="42" y="298" text-anchor="middle" font-size="12" fill="#9A3412">并 fsync</text>
  <line x1="120" y1="318" x2="115" y2="318" stroke="#10B981" stroke-width="2"/>
  <text x="42" y="323" text-anchor="middle" font-size="12" fill="#166534">⑥ redo log</text>
  <text x="42" y="341" text-anchor="middle" font-size="12" fill="#166534">commit ✓</text>
  <text x="500" y="110" text-anchor="middle" font-size="13" fill="#7F1D1D">崩溃点A：redo=prepare，binlog=无</text>
  <text x="500" y="132" text-anchor="middle" font-size="12" fill="#6B7280">恢复规则①：binlog 不完整 → 回滚（主库从库都没发生）</text>
  <text x="500" y="190" text-anchor="middle" font-size="13" fill="#7F1D1D">崩溃点B：redo=prepare，binlog=完整</text>
  <text x="500" y="212" text-anchor="middle" font-size="12" fill="#6B7280">恢复规则②：binlog 完整 → 提交（从库已经拿到，不能少）</text>
  <text x="860" y="110" text-anchor="middle" font-size="12" fill="#1E3A8A">反证：若先写 binlog 后写 redo，</text>
  <text x="860" y="130" text-anchor="middle" font-size="12" fill="#1E3A8A">redo 失败 → 从库有主库无 → 不一致</text>
  <text x="860" y="170" text-anchor="middle" font-size="12" fill="#1E3A8A">若先写 redo(commit) 后 binlog，</text>
  <text x="860" y="190" text-anchor="middle" font-size="12" fill="#1E3A8A">binlog 失败 → 主库有从库无 → 主从不一致</text>
  <text x="860" y="230" text-anchor="middle" font-size="12" fill="#1D4ED8">prepare/commit 把两个独立日志</text>
  <text x="860" y="250" text-anchor="middle" font-size="12" fill="#1D4ED8">绑成一个原子语义 = 内部XA</text>
  <text x="860" y="290" text-anchor="middle" font-size="12" fill="#6B7280">binlog 是 Server 层逻辑日志(复制/归档)</text>
  <text x="860" y="310" text-anchor="middle" font-size="12" fill="#6B7280">redo 是 InnoDB 物理日志(崩溃恢复)</text>
  <text x="860" y="330" text-anchor="middle" font-size="12" fill="#6B7280">两模块各自要日志，两阶段是它们的握手</text>
</svg>

**组提交的加成：⑤⑥ 的 fsync 可以把同时提交的多个事务合并成一次磁盘操作——
高并发时"组员"越多，摊到每个事务的 fsync 成本越低，这就是压测时 TPS 反而上升的物理原因。**

### 3.4 MVCC + undo log：读不加锁

```
每行带隐藏列：trx_id(最后修改事务) + roll_pointer(指向 undo log 版本链)
ReadView：活跃事务列表的快照
  可见性规则：版本的 trx_id 在活跃列表里 → 不可见，沿 roll_pointer 找上一版
  RR：事务第一条查询时拍 ReadView，整个事务复用 → 可重复读
  RC：每条语句拍新 ReadView → 读到已提交最新
长事务 = 老 ReadView 一直被引用 = undo 版本链无法回收 = 膨胀 + 回表变慢
  → "为什么 DBA 天天喊别用长事务"的物理原因
```

## 四、第三问：为什么 MySQL 会"抖"？

把底层账单对上就一目了然：

```
MySQL 的"抖" = 后台线程突然开始还账：
  1. 刷脏页（四种触发）：
     ① redo log 写满 → 全系统暂停等刷盘（最凶险）
     ② Buffer Pool 不够 → 淘汰页是脏的要先落盘
     ③ 系统空闲 → 后台主动刷
     ④ 正常关闭 → 全量刷
     → innodb_io_capacity 设成磁盘真实 IOPS：设低了刷得畏手畏脚，设高了挤占业务IO
  2. redo 组提交排队
  3. Buffer Pool 缺页加载（冷启动/扫描冷数据）
观测（《Linux性能优化实战》28讲的 SQL 15秒案例）：
  iostat -x 1 → %util 打满、await 飙高 → 磁盘瓶颈
  show engine innodb status → checkpoint age
```

**经验法则从物理约束长出来：**
- 单表别超过 2000 万行（树高要控制在 3 层；扇出按 1000 估算：1000² × 每页15行 ≈ 2000万）
- `innodb_flush_method=O_DIRECT` 绕过 OS page cache（自己有 Buffer Pool，避免双缓存）
- 双 1 配置（sync_binlog=1, innodb_flush_log_at_trx_commit=1）换不丢数据；
  性能敏感的从库/日志库可放松到 2/2（崩机器丢 1 秒）
- 长事务、大事务 = 版本链 + 大 binlog + 锁持有时间，能拆就拆

## 五、约束小结

| 底层约束 | MySQL 的回应 |
|---------|-------------|
| 随机 IO >> 顺序 IO | B+ 树矮胖化、redo log 顺序写、change buffer |
| 一次 fsync 100μs~10ms | WAL + 组提交 + 双1/放松的档位选择 |
| 内存 >> 磁盘 | Buffer Pool + 改良 LRU + O_DIRECT 防双缓存 |
| 断电/崩溃不可预报 | redo/undo/binlog + 两阶段提交 → crash-safe |
| 并发读写冲突 | MVCC 版本链（读不阻塞写） |
| 树高=IO次数 | 单表 2000 万行的经验值 |
| 两个日志模块各自为政 | 两阶段提交的原子握手 |

**一句话总结：MySQL 的每一层都是"磁盘很慢、崩溃很可怕"这两个物理事实的直接推论。**

---

> 下一篇：[05-Nginx](05-Nginx：为什么这么设计.md) —— 从磁盘时代跳到网络时代，看 C10K 怎么破。
