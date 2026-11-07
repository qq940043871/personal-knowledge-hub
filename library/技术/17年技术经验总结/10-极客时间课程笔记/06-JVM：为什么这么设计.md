# 06 · JVM：为什么这么设计

> 来源课程：《深入拆解Java虚拟机》(45讲) + 《趣谈Linux操作系统》 + 《Java性能调优实战》
> 主线：**JVM 是"用 C++ 写的一个 Linux 进程"，对外模拟出一台计算机。它的每个模块——线程、内存、GC、类加载——都是把 OS 能力"翻译"或"改造"一遍。看懂 JVM 的钥匙是随时问一句：这一层下面，内核在干什么？**
> 更新时间：2026-11-06

---

## 一、JVM 到底是什么？（先钉死定位）

```
你的 Java 进程在内核眼里：
  就是一个普通 C++ 进程：/usr/bin/java
  拥有一块大内存（malloc/mmap 出来的）、若干线程（clone 出来的）、
  打开一堆文件（jar/class/日志/socket）、注册了信号处理器

JVM 的工作：在这个进程里，模拟出一台"看不见内核"的计算机
  - 模拟 CPU   → 字节码执行引擎（解释器 + JIT 编译的本地代码）
  - 模拟内存   → 运行时数据区（堆/栈/方法区/程序计数器）
  - 模拟调度   → java.lang.Thread（其实是内核线程的壳）
  - 模拟文件系统 → 类加载器 + JarFile
```

**"为什么这么设计"的第一层答案：JVM 的每个模拟件，都受真实 OS 的对应约束。**

## 二、进程内存全景：每一块都对应一种内核分配方式

<svg style="max-width:100%;height:auto" width="960" height="500" viewBox="0 0 960 500" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">java 进程的虚拟地址空间：JVM 的"全部家当"</text>
  <rect x="60" y="50" width="430" height="420" rx="10" fill="#F5F3FF" stroke="#8B5CF6" stroke-width="2"/>
  <text x="275" y="78" text-anchor="middle" font-size="15" font-weight="bold" fill="#5B21B6">JVM 内部视角</text>
  <rect x="80" y="95" width="390" height="66" rx="6" fill="#FFFFFF" stroke="#C4B5FD"/>
  <text x="275" y="120" text-anchor="middle" font-size="13" font-weight="bold" fill="#4C1D95">Java 堆（-Xms/-Xmx）</text>
  <text x="275" y="142" text-anchor="middle" font-size="12" fill="#6B7280">新生代(Eden+S0/S1) + 老年代 · GC 主战场</text>
  <rect x="80" y="175" width="190" height="60" rx="6" fill="#FFFFFF" stroke="#C4B5FD"/>
  <text x="175" y="200" text-anchor="middle" font-size="13" fill="#4C1D95">元空间 Metaspace</text>
  <text x="175" y="220" text-anchor="middle" font-size="11" fill="#6B7280">类元数据（取代永久代）</text>
  <rect x="280" y="175" width="190" height="60" rx="6" fill="#FFFFFF" stroke="#C4B5FD"/>
  <text x="375" y="200" text-anchor="middle" font-size="13" fill="#4C1D95">线程栈 × N（-Xss）</text>
  <text x="375" y="220" text-anchor="middle" font-size="11" fill="#6B7280">每线程一段，默认约1M</text>
  <rect x="80" y="249" width="390" height="60" rx="6" fill="#FFFFFF" stroke="#C4B5FD"/>
  <text x="275" y="274" text-anchor="middle" font-size="13" fill="#4C1D95">直接内存 Direct Memory</text>
  <text x="275" y="294" text-anchor="middle" font-size="11" fill="#6B7280">NIO DirectByteBuffer / mmap 映射文件</text>
  <rect x="80" y="323" width="390" height="60" rx="6" fill="#FFF7ED" stroke="#F97316"/>
  <text x="275" y="348" text-anchor="middle" font-size="13" fill="#7C2D12">GC 辅助结构</text>
  <text x="275" y="368" text-anchor="middle" font-size="11" fill="#9A3412">卡表(卡页bitmap) / 标记位图 / 记忆集</text>
  <rect x="80" y="397" width="390" height="56" rx="6" fill="#FFFFFF" stroke="#C4B5FD"/>
  <text x="275" y="420" text-anchor="middle" font-size="13" fill="#4C1D95">JVM 自身（C++ 堆、JIT 代码缓存）</text>
  <text x="275" y="440" text-anchor="middle" font-size="11" fill="#6B7280">CodeCache：JIT 编译出的本地机器码放这</text>
  <rect x="560" y="50" width="340" height="420" rx="10" fill="#F9FAFB" stroke="#9CA3AF" stroke-width="2"/>
  <text x="730" y="78" text-anchor="middle" font-size="15" font-weight="bold" fill="#374151">内核视角（每块的真实来源）</text>
  <rect x="580" y="95" width="300" height="66" rx="6" fill="#FFFFFF" stroke="#D1D5DB"/>
  <text x="730" y="120" text-anchor="middle" font-size="12" fill="#374151">mmap 大段保留(Reserved) → 分批提交(Commit)</text>
  <text x="730" y="140" text-anchor="middle" font-size="11" fill="#6B7280">MEM-2：commit 不等于物理内存，写才兑现</text>
  <rect x="580" y="175" width="300" height="60" rx="6" fill="#FFFFFF" stroke="#D1D5DB"/>
  <text x="730" y="200" text-anchor="middle" font-size="12" fill="#374151">malloc/mmap 本地内存</text>
  <text x="730" y="220" text-anchor="middle" font-size="11" fill="#6B7280">卸载类 = free，可归还 OS（永久代不能）</text>
  <rect x="580" y="249" width="300" height="60" rx="6" fill="#FFFFFF" stroke="#D1D5DB"/>
  <text x="730" y="274" text-anchor="middle" font-size="12" fill="#374151">pthread_create 时 mmap 栈段</text>
  <text x="730" y="294" text-anchor="middle" font-size="11" fill="#6B7280">1万线程 ≈ 10GB 虚拟 + 真实内核开销</text>
  <rect x="580" y="323" width="300" height="60" rx="6" fill="#FFF7ED" stroke="#F97316"/>
  <text x="730" y="348" text-anchor="middle" font-size="12" fill="#7C2D12">malloc 或 mmap 文件直连</text>
  <text x="730" y="368" text-anchor="middle" font-size="11" fill="#9A3412">mmap 读文件 = 页缓存直达，零拷贝</text>
  <rect x="580" y="397" width="300" height="56" rx="6" fill="#FFF7ED" stroke="#F97316"/>
  <text x="730" y="420" text-anchor="middle" font-size="12" fill="#7C2D12">也是 mmap 来的一小段</text>
  <text x="730" y="440" text-anchor="middle" font-size="11" fill="#9A3412">占用小但常被 OOM 排查忽视</text>
  <line x1="450" y1="128" x2="575" y2="128" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="450" y1="205" x2="575" y2="205" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="450" y1="279" x2="575" y2="279" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="450" y1="353" x2="575" y2="353" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="450" y1="425" x2="575" y2="425" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="60" y="478" width="840" height="16" rx="0" fill="none" stroke="none"/>
  <text x="480" y="478" text-anchor="middle" font-size="0" fill="none"> </text>
</svg>

三个"为什么"：

```
1. 为什么 -Xmx 别超过物理内存 70%？
   堆 + 元空间 + 线程栈×N + 直接内存 + Page Cache 都要真内存；
   挤过头 → Swap（MEM-3）→ GC 扫堆时页被换出 → 一次 FullGC = 磁盘随机读一遍 = 事故
   （《Linux性能优化实战》19/20讲 Swap 案例的 JVM 版）

2. 为什么有 Direct Memory？
   堆外内存绕开"堆内对象 → 拷贝到 C 缓冲区 → socket"的固定开销，
   mmap 文件（MappedByteBuffer）更是直接把页缓存映射进来（MEM-4）。
   Netty 的零拷贝、Kafka 传输层都在这层发力。
   陷阱：DirectMemory 不归 GC 直接管，靠 Cleaner 回收 + -XX:MaxDirectMemorySize 封顶，
   忘了封顶就是"堆很健康、进程 OOM killed"的经典死法。

3. 为什么 TLAB 能加速分配？
   每个线程在 Eden 里预租一小块，分配=指针碰撞（无锁）。
   —— 又是"把全局争用变成线程私有"（CPU定律），和 Redis 单线程、Nginx 内存池同源。
```

## 三、线程：Java 线程就是内核线程（1:1 映射）

```
new Thread().start()
  → JVM 调 pthread_create（HotSpot 在 Linux 上）
  → 内核 clone() 出一个真实的调度实体（task_struct）
  → 被 CFS 和所有 Java 线程一起公平调度
```

直接推论（调优经验的物理出处）：

| 经验法则 | 底层真因 |
|---------|---------|
| 线程池大小 ≈ 核数/(1-等待比) | CPU定律 CPU-3：核数是并行上限，等 IO 的线程不占 CPU 但占栈 |
| -Xss 默认 512KB~1M | 线程栈要预留虚拟地址空间；1万线程 ≈ 10GB 虚拟内存 + 真实内核开销 |
| 线程数上千后吞吐不升反降 | 上下文切换 + 调度噪声（vmstat cs 列验证） |
| 虚拟线程(JDK21+) | 把"线程"改造成用户态可切换实体，绕开 1:1 映射的切换成本——JVM 开始自己写调度器，本质是把 Nginx/Go 的事件驱动思想搬进 JVM |

## 四、GC：对着"STW"这个约束的逐次突围

GC 的根本矛盾：**标记/整理需要"世界静止"，而业务要求"永远不停"。**

<svg style="max-width:100%;height:auto" width="960" height="300" viewBox="0 0 960 300" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">GC 演进史 = 对 STW 的逐次突围（纵轴：停顿感受）</text>
  <line x1="80" y1="250" x2="900" y2="250" stroke="#9CA3AF" stroke-width="2"/>
  <line x1="80" y1="60" x2="80" y2="250" stroke="#9CA3AF" stroke-width="2"/>
  <text x="60" y="150" font-size="12" fill="#6B7280" transform="rotate(-90 60 150)" text-anchor="start">停顿时间</text>
  <rect x="110" y="80" width="110" height="170" fill="#FECACA" stroke="#EF4444"/>
  <text x="165" y="105" text-anchor="middle" font-size="13" font-weight="bold" fill="#991B1B">Serial</text>
  <text x="165" y="128" text-anchor="middle" font-size="12" fill="#7F1D1D">单线程全程停</text>
  <text x="165" y="148" text-anchor="middle" font-size="12" fill="#7F1D1D">秒级 STW</text>
  <rect x="250" y="120" width="110" height="130" fill="#FED7AA" stroke="#F97316"/>
  <text x="305" y="145" text-anchor="middle" font-size="13" font-weight="bold" fill="#7C2D12">Parallel</text>
  <text x="305" y="168" text-anchor="middle" font-size="12" fill="#7C2D12">多线程并行</text>
  <text x="305" y="188" text-anchor="middle" font-size="12" fill="#7C2D12">吞吐优先</text>
  <rect x="390" y="160" width="110" height="90" fill="#FEF3C7" stroke="#F59E0B"/>
  <text x="445" y="185" text-anchor="middle" font-size="13" font-weight="bold" fill="#92400E">CMS</text>
  <text x="445" y="208" text-anchor="middle" font-size="12" fill="#92400E">并发标记清除</text>
  <text x="445" y="226" text-anchor="middle" font-size="11" fill="#A16207">几十ms，有碎片</text>
  <rect x="515" y="190" width="140" height="60" fill="#D1FAE5" stroke="#10B981"/>
  <text x="585" y="215" text-anchor="middle" font-size="13" font-weight="bold" fill="#166534">G1</text>
  <text x="585" y="235" text-anchor="middle" font-size="11" fill="#047857">Region 化+停顿目标</text>
  <rect x="670" y="215" width="110" height="35" fill="#A7F3D0" stroke="#10B981"/>
  <text x="725" y="238" text-anchor="middle" font-size="12" font-weight="bold" fill="#065F46">ZGC</text>
  <rect x="800" y="225" width="90" height="25" fill="#6EE7B7" stroke="#10B981"/>
  <text x="845" y="243" text-anchor="middle" font-size="10" fill="#065F46">&lt;1ms</text>
  <text x="165" y="272" text-anchor="middle" font-size="11" fill="#6B7280">简单</text>
  <text x="305" y="272" text-anchor="middle" font-size="11" fill="#6B7280">并行</text>
  <text x="445" y="272" text-anchor="middle" font-size="11" fill="#6B7280">并发</text>
  <text x="585" y="272" text-anchor="middle" font-size="11" fill="#6B7280">可预期</text>
  <text x="725" y="272" text-anchor="middle" font-size="11" fill="#6B7280">着色指针</text>
  <text x="845" y="272" text-anchor="middle" font-size="11" fill="#6B7280">与堆大小无关</text>
</svg>

```
分代假说（统计规律，不是物理定律）：绝大多数对象朝生夕死
  → 新生代/老年代分开对待：Eden 复制算法快进快出，老年代 Mark-(Compact/Sweep)
  → 记忆依据： replicated in 03篇(近似LRU) / 04篇(young-old LRU)——"分级对待"无处不在

对象分配全流程（对上图 TLAB 的展开）：
  new → 尝试 TLAB 指针碰撞(无锁,最快) → 不够则申请新 TLAB(轻锁) → Eden 满 → MinorGC
  → 存活对象年龄+1，超阈值(-XX:MaxTenuringThreshold)晋升老年代
  → 大对象直接进老年代(-XX:PretenureSizeThreshold)——避免来回复制

支撑"并发"的两个底层机关：
safepoint（安全点）：
  线程跑到特定位置才愿意停 → JIT 在分支处插"轮询页"（一个故意触发 SIGSEGV 的只读页）
  → 用内核的缺页中断实现"举手报告"！OS 机制变成 JVM 控制器
  （新 JDK 逐步引入 thread-local handshake 替代全局轮询页，思想不变：借内核的通知机制）
  长循环不进安全点 = Time To Safepoint 停顿（疑难杂症排查点）

写屏障 + 卡表（跨代引用）：
  老年代引用新生代怎么发现？给所有"老→新"引用写操作挂个钩子（编译器插入的指令）
  → 标记新生代时只扫卡表标记的脏卡，不用全堆扫描
  —— 本质是"增量维护索引"，和 MySQL change buffer 同一思想
```

**GC 调优的本质翻译：**
`-Xms=-Xmx`（避免动态扩缩容 = 避免一次 mmap + 搬迁）、
`-XX:+UseG1GC -XX:MaxGCPauseMillis=200`（告诉 GC 你的 SLA）——
**这些参数不是咒语，是在向 GC 描述你的"物理资源"和"业务约束"。**

## 五、类加载：一次"动态链接"的全套服务

```
加载(.class 文件 = 文件IO) → 验证 → 准备(分配内存) → 解析(符号引用→直接引用=动态链接)
→ 初始化(<clinit>，加锁保证只跑一次)

双亲委派：App → Platform → Bootstrap 逐级上问
为什么：核心类库只有一份、安全（自定义 java.lang.String 撞车核心类时被顶回）
打破它的场景（Tomcat WebAppClassLoader，07篇展开）：应用间隔离 + JSP 热替换
```

## 六、约束小结

| 底层约束 | JVM 的回应 |
|---------|-------------|
| 线程=内核实体，切换贵 | 线程池 /（正在演进中）虚拟线程用户态调度 |
| 物理内存有限 + Swap 毒性 | Xmx 经验法则、GC 扫堆尽量少碰页 |
| 分配要快 | TLAB 指针碰撞、逃逸分析栈上分配 |
| STW 与业务矛盾 | 分代 → 并发(CMS/G1) → 着色指针(ZGC) |
| 跨代/跨 Region 引用发现 | 写屏障 + 卡表 |
| "举手报告" | safepoint 轮询页（借缺页中断） |
| 类的唯一性与隔离性 | 双亲委派 + 可打破的类加载器体系 |
| 堆外内存不可控 | MaxDirectMemorySize 封顶 + Cleaner 回收 |

---

> 下一篇：[07-Tomcat](07-Tomcat：为什么这么设计.md) —— JVM 之上，一个"一连接一线程"血泪史改写成的 NIO 故事。
