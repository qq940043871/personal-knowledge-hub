# 07 · Tomcat：为什么这么设计

> 来源课程：《深入拆解Tomcat & Jetty》(45讲) + 《Java性能调优实战》 + 《高并发系统设计40问》
> 主线：**Tomcat 的整个架构史，就是一部"线程是稀缺资源"的认知进化史。Connector 层把 IO 模型换了几代，Container 层几乎没动——因为协议接入被 OS 约束推着变，而 Servlet 语义要稳定。**
> 更新时间：2026-11-06

---

## 一、分层设计：Connector 与 Container 为什么分开？

<svg style="max-width:100%;height:auto" width="960" height="450" viewBox="0 0 960 450" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">Tomcat 架构：把"被 OS 推着变的"与"业务语义要稳的"切开</text>
  <rect x="40" y="50" width="880" height="150" rx="10" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
  <text x="480" y="76" text-anchor="middle" font-size="14" font-weight="bold" fill="#166534">Connector 层（协议接入 · 换血频繁：BIO → NIO → APR）</text>
  <rect x="70" y="96" width="250" height="80" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/>
  <text x="195" y="122" text-anchor="middle" font-size="12" font-weight="bold" fill="#14532D">Acceptor（1线程）</text>
  <text x="195" y="142" text-anchor="middle" font-size="11" fill="#64748B">只管 accept，拿到 socket</text>
  <text x="195" y="158" text-anchor="middle" font-size="11" fill="#64748B">包装成 NioChannel 丢给 Poller</text>
  <rect x="355" y="96" width="250" height="80" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/>
  <text x="480" y="122" text-anchor="middle" font-size="12" font-weight="bold" fill="#14532D">Poller（1线程）</text>
  <text x="480" y="142" text-anchor="middle" font-size="11" fill="#64748B">epoll_wait 盯所有连接的读写事件</text>
  <text x="480" y="158" text-anchor="middle" font-size="11" fill="#64748B">就绪 → 封装成任务投给线程池</text>
  <rect x="640" y="96" width="250" height="80" rx="6" fill="#FFFFFF" stroke="#6EE7B7"/>
  <text x="765" y="122" text-anchor="middle" font-size="12" font-weight="bold" fill="#14532D">Executor（线程池）</text>
  <text x="765" y="142" text-anchor="middle" font-size="11" fill="#64748B">真正干活的线程：读体/跑Servlet/写响应</text>
  <text x="765" y="158" text-anchor="middle" font-size="11" fill="#64748B">maxThreads=200 默认</text>
  <line x1="320" y1="136" x2="350" y2="136" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="605" y1="136" x2="635" y2="136" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="40" y="220" width="880" height="140" rx="10" fill="#EFF6FF" stroke="#3B82F6" stroke-width="2"/>
  <text x="480" y="246" text-anchor="middle" font-size="14" font-weight="bold" fill="#1D4ED8">Container 层（业务容器 · 多年未变：Servlet 规范）</text>
  <rect x="70" y="266" width="200" height="70" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="170" y="296" text-anchor="middle" font-size="13" fill="#1E3A8A">Engine</text><text x="170" y="316" text-anchor="middle" font-size="11" fill="#64748B">虚拟主机路由</text>
  <rect x="290" y="266" width="200" height="70" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="390" y="296" text-anchor="middle" font-size="13" fill="#1E3A8A">Host</text><text x="390" y="316" text-anchor="middle" font-size="11" fill="#64748B">域名 → 应用</text>
  <rect x="510" y="266" width="200" height="70" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="610" y="296" text-anchor="middle" font-size="13" fill="#1E3A8A">Context</text><text x="610" y="316" text-anchor="middle" font-size="11" fill="#64748B">一个 WebApp + 类加载器</text>
  <rect x="730" y="266" width="160" height="70" rx="6" fill="#FFFFFF" stroke="#93C5FD"/><text x="810" y="296" text-anchor="middle" font-size="13" fill="#1E3A8A">Wrapper</text><text x="810" y="316" text-anchor="middle" font-size="11" fill="#64748B">一个 Servlet</text>
  <line x1="270" y1="301" x2="285" y2="301" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="490" y1="301" x2="505" y2="301" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="710" y1="301" x2="725" y2="301" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="480" y1="176" x2="480" y2="215" stroke="#6B7280" stroke-width="2.5" marker-end="url(#arr)"/>
  <text x="560" y="200" font-size="12" fill="#6B7280" text-anchor="start">适配成 Request/Response（对象池回收复用）</text>
  <rect x="40" y="374" width="880" height="56" rx="8" fill="#F9FAFB" stroke="#9CA3AF"/>
  <text x="480" y="398" text-anchor="middle" font-size="13" font-weight="bold" fill="#374151">这是所有"分层"的通用公式：把"被底层约束推着变的部分"和"业务语义要稳定的部分"切开</text>
  <text x="480" y="420" text-anchor="middle" font-size="12" fill="#6B7280">对照 MySQL：Server 层与 InnoDB 层分开，理由一模一样（04篇 binlog/redo 两本日志的根源）</text>
</svg>

## 二、IO 模型演进：一部线程血泪史

### 2.1 BIO（Tomcat 7 及以前默认）：一连接一线程

```
accept() → 每个连接 new 一个线程 → 阻塞 read
约束正对 CPU定律：
  1000 连接 = 1000 线程 = 1GB 栈内存 + 沉重的上下文切换
  连接闲着，线程也占着 —— 成本模型 O(连接数)
  keep-alive 让"闲连接"更多 → 线程池打满 → 新请求排队 → 超时雪崩
```

### 2.2 NIO（Tomcat 8+ 默认）：epoll + Poller + 线程池

<svg style="max-width:100%;height:auto" width="960" height="400" viewBox="0 0 960 400" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif">
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L9,3 L0,6 Z" fill="#6B7280"/></marker>
  </defs>
  <text x="480" y="26" text-anchor="middle" font-size="18" font-weight="bold" fill="#1F2937">BIO vs NIO：成本模型从 O(连接数) 变成 O(活跃请求数)</text>
  <rect x="40" y="60" width="420" height="180" rx="10" fill="#FEF2F2" stroke="#EF4444" stroke-width="2"/>
  <text x="250" y="88" text-anchor="middle" font-size="14" font-weight="bold" fill="#991B1B">BIO：一连接一线程</text>
  <rect x="60" y="105" width="90" height="34" rx="5" fill="#FFFFFF" stroke="#FCA5A5"/><text x="105" y="127" text-anchor="middle" font-size="11" fill="#7F1D1D">连接1/线程1</text>
  <rect x="160" y="105" width="90" height="34" rx="5" fill="#FFFFFF" stroke="#FCA5A5"/><text x="205" y="127" text-anchor="middle" font-size="11" fill="#7F1D1D">连接2/线程2</text>
  <rect x="260" y="105" width="90" height="34" rx="5" fill="#FFFFFF" stroke="#FCA5A5"/><text x="305" y="127" text-anchor="middle" font-size="11" fill="#7F1D1D">连接3/线程3</text>
  <rect x="60" y="150" width="90" height="34" rx="5" fill="#FFF7ED" stroke="#FDBA74"/><text x="105" y="172" text-anchor="middle" font-size="11" fill="#7C2D12">连接4/线程4(闲)</text>
  <rect x="160" y="150" width="90" height="34" rx="5" fill="#FFF7ED" stroke="#FDBA74"/><text x="205" y="172" text-anchor="middle" font-size="11" fill="#7C2D12">连接5/线程5(闲)</text>
  <rect x="260" y="150" width="90" height="34" rx="5" fill="#FFF7ED" stroke="#FDBA74"/><text x="305" y="172" text-anchor="middle" font-size="11" fill="#7C2D12">…线程N</text>
  <text x="250" y="222" text-anchor="middle" font-size="12" fill="#7F1D1D">橙色=keep-alive 闲连接：连接闲着，线程也占着</text>
  <rect x="500" y="60" width="420" height="180" rx="10" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
  <text x="710" y="88" text-anchor="middle" font-size="14" font-weight="bold" fill="#166534">NIO：epoll 盯连接，线程只管活跃请求</text>
  <rect x="520" y="105" width="120" height="34" rx="5" fill="#FFFFFF" stroke="#6EE7B7"/><text x="580" y="127" text-anchor="middle" font-size="11" fill="#14532D">连接1~N 挂 epoll</text>
  <rect x="520" y="150" width="120" height="34" rx="5" fill="#D1FAE5" stroke="#10B981"/><text x="580" y="172" text-anchor="middle" font-size="11" fill="#065F46">就绪事件(少)</text>
  <rect x="700" y="105" width="200" height="34" rx="5" fill="#FFFFFF" stroke="#6EE7B7"/><text x="800" y="127" text-anchor="middle" font-size="11" fill="#14532D">Poller 转发就绪请求</text>
  <rect x="700" y="150" width="200" height="34" rx="5" fill="#D1FAE5" stroke="#10B981"/><text x="800" y="172" text-anchor="middle" font-size="11" fill="#065F46">Executor 线程池(200)</text>
  <text x="710" y="222" text-anchor="middle" font-size="12" fill="#14532D">万级连接挂着没关系，线程只服务"正在干活"的</text>
  <line x1="460" y1="150" x2="495" y2="150" stroke="#6B7280" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="40" y="260" width="880" height="120" rx="10" fill="#F5F3FF" stroke="#8B5CF6" stroke-width="2"/>
  <text x="480" y="286" text-anchor="middle" font-size="13" font-weight="bold" fill="#5B21B6">Nginx 对照（05篇）：同样是事件驱动，为什么 Nginx 连线程池都没有？</text>
  <text x="70" y="312" font-size="12" fill="#4C1D95" text-anchor="start">Nginx 不执行业务，"处理"就是搬字节 → 单线程状态机足矣</text>
  <text x="70" y="332" font-size="12" fill="#4C1D95" text-anchor="start">Tomcat 要执行业务（Servlet 是阻塞语义）→ 保留线程池，但把"等 IO"全部交给 epoll</text>
  <text x="70" y="352" font-size="12" fill="#4C1D95" text-anchor="start">Netty（《Netty源码剖析与实战》）= 同一思想的通用引擎：主从 Reactor + 线程池，Spring WebFlux/gRPC 底层都是它</text>
  <text x="480" y="376" text-anchor="middle" font-size="12" fill="#7C3AED">同一个约束（线程贵），两种业务前提，两种答案 —— 这就是"为什么这么设计"的标准思考路径</text>
</svg>

### 2.3 三个参数的内核真相（调优=对内核说话）

| Tomcat 参数 | 内核对应 | 推导 |
|------------|---------|------|
| maxConnections | epoll 里能挂的连接数 | 上限受 fd 数限制（ulimit） |
| acceptCount | listen 的 backlog（全连接队列） | 内核 somaxconn 封顶；满了新连接被拒/重置 |
| maxThreads | 真正干活的内核线程数 | 超过核数×等待比后只付切换不付吞吐；每线程还吃 1MB 栈 |

**默认 8.0 NIO: maxConnections=8192, maxThreads=200, acceptCount=100 ——
这三个数字的相对大小本身就是设计：连接远多于线程，线程略多于核数能吃的量。**

## 三、为什么每个 Web 应用一个类加载器？

```
WebAppClassLoader：每个 Context 一个，先自己加载（打破双亲委派）
动机1 隔离：两个 Spring 版本、两个不同版本 jar 共存于一个 JVM
动机2 热部署：扔掉 ClassLoader = 扔掉它加载的所有类 = 重新加载新版本 JSP/应用
代价：Metaspace 泄漏的经典来源——旧 ClassLoader 被静态字段/线程引用住 → 无法回收
     （06篇 Metaspace = mmap 本地内存，泄了就溢出 OOM: Metaspace）

排查套路：MAT 里查 ClassLoader 泄漏链 → 常见元凶：ThreadLocal 忘清理、
驱动注册在 Common 类路径、ShutdownHook 持有应用对象
```

## 四、请求处理链：Pipeline-Valve 与 Filter 的分层

```
Container 用责任链（Pipeline + Valve）组织拦截逻辑；
Servlet 规范的 Filter 是同一思想的接口化。
02篇决策树里的"关系/依赖 → 责任链"：这类结构好扩展、好插拔，
代价是长链路栈深、每层都有包装对象 → Tomcat 用 Request/Response 回收池对冲高频分配

微内核思想（09篇）：Engine/Host/Context/Wrapper 各自挂 Pipeline，
"核心只管流转，功能全是插件" —— 与 Netty 的 ChannelPipeline 完全同构
```

## 五、约束小结

| 底层约束 | Tomcat 的回应 |
|---------|-------------|
| 线程贵（内存+切换） | BIO → NIO：成本模型 O(连接数) → O(活跃数) |
| fd 有限 | maxConnections ≤ ulimit |
| 内核 backlog 有限 | acceptCount 与 somaxconn 对齐 |
| 业务要稳定、协议在变 | Connector/Container 分层 |
| 一个 JVM 多应用共存 + 热加载 | 独立类加载器（打破双亲委派） |
| 长链路对象开销 | 对象池、BufferPool |
| 高频小对象分配 | Request/Response 回收池 |

**和 Nginx 摆在一起看（05篇）：Nginx 选择"不执行业务"所以敢把线程干掉；
Tomcat 必须执行业务（Servlet 阻塞语义）所以保留线程池但把等 IO 的部分全部异步化。
同一个约束（线程贵），两种业务前提，两种答案。**

---

> 下一篇：[08-总图](08-总图：底层如何约束上层设计.md) —— 把五栋"房子"放回同一张"地质图"上。
