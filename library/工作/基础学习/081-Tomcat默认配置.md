# Tomcat默认配置

Tomcat默认的分配的前往虚拟机的内存大小是多少？

**Tomcat 本身不自带固定默认内存值**，它直接沿用你当前 JDK/JRE 的默认堆内存规则。

## 一、JVM 默认堆内存（Tomcat 未改时）
+ **初始堆 **`-Xms`：物理内存的 **1/64**
+ **最大堆 **`-Xmx`：物理内存的 **1/4**

**常见机器示例（64位 JDK8+）**：

+ 8G 内存 → `-Xms` ≈ **128MB**，`-Xmx` ≈ **2GB**
+ 16G 内存 → `-Xms` ≈ **256MB**，`-Xmx` ≈ **4GB**
+ 32G 内存 → `-Xms` ≈ **512MB**，`-Xmx` ≈ **8GB**

## 二、为什么网上常说“Tomcat 默认 128MB”？
+ 早期 32 位 JDK + 小内存机器，`1/64` 常落在 **64~128MB**
+ 很多教程/旧文档直接把 **128MB** 当成“默认值”讲
+ 现在 64 位大内存服务器，默认 `Xmx` 往往是 **几GB**

## 三、生产环境标准配置（必改）
```bash
# setenv.sh 或 catalina.sh
JAVA_OPTS="-server -Xms2g -Xmx2g -XX:MetaspaceSize=256m -XX:MaxMetaspaceSize=512m"
```

+ `-Xms`** = **`-Xmx`：避免运行时扩容、GC抖动
+ 建议设为 **物理内存的 50%~70%**（给系统留足）

## 四、怎么看当前 Tomcat 实际内存？
```bash
# 找到进程
ps -ef | grep tomcat

# 看 JVM 参数
jinfo -flags <pid>
# 或
jmap -heap <pid>
```

## 如何避免就是full GC？

先说结论：
**完全避免 Full GC 几乎做不到，但可以做到：极少触发、极短停顿、甚至不影响业务。**
下面给你一套**生产级、可直接落地**的避 Full GC 方案，按重要程度排序。

---

## 一、先搞懂：Full GC 一般为啥来？
1. **老年代满了**（对象太多、存活太久）
2. **元空间（Metaspace）满了**
3. **显式调用 **`System.gc()`
4. **并发 GC 跟不上**（CMS / G1  concurrent mode failure）
5. **大对象直接进老年代**
6. **内存设置不合理**（Xms/Xmx/新生代比例）

你要避免的，就是**不让老年代被撑爆**。

---

## 二、最有效、最优先的 6 条硬规则
### 1. 禁止显式 GC（最容易忽略）
很多框架、工具会主动调用 `System.gc()` 触发 Full GC
加 JVM 参数：

```plain
-XX:+DisableExplicitGC
```

**这条能直接干掉一半莫名其妙的 Full GC。**

### 2. 大对象必须消灭（直接进老年代的元凶）
+ 超大集合、超大 JSON、超大字节数组、超大字符串
+ 一次查询几万条数据到内存

原则：
**单次内存占用 > 新生代 50% 的对象，基本必触发 Full GC**

### 3. 内存配置：Xms = Xmx
不要让 JVM 动态扩容，一扩就容易伴随 GC 抖动

```plain
-Xms4g -Xmx4g
```

生产上**必须相等**。

### 4. 新生代不能太小
新生代太小 → 对象很快进入老年代 → Full GC 频发
常规比例：

+ **新生代 : 老年代 = 1 : 2 或 1 : 3**
JDK8 默认比例已经比较合理，不用乱改。

### 5. 尽早升级到 G1 / ZGC（JDK11+）
+ **CMS** 很容易 Full GC
+ **G1** 基本能做到**几乎不 Full GC**
+ **ZGC / Shenandoah** 毫秒级停顿，几乎无感

推荐参数（G1，4G 堆）：

```plain
-Xms4g -Xmx4g
-XX:+UseG1GC
-XX:MaxGCPauseMillis=20
-XX:+DisableExplicitGC
```

### 6. 元空间设够，防止溢出触发 Full GC
```plain
-XX:MetaspaceSize=256m
-XX:MaxMetaspaceSize=512m
```

SpringBoot 项目很容易吃元空间。

---

## 三、代码层面：真正能“防住”Full GC 的写法
### 1. 短生命周期对象，不要变长存活
+ 局部变量、循环内对象，**不要被静态集合持有**
+ 不要把 request、session、DTO 塞进 static map/list

只要对象**熬过 1~2 次 Young GC**，就会进老年代。

### 2. 池化要适度，不要无限制缓存
+ 本地缓存（Caffeine、Guava、自建 Map）
+ 连接池、线程池队列无界
这些都会**悄悄把老年代塞满**

### 3. 避免内存泄漏（终极杀手）
典型泄漏场景：

+ 静态集合只加不删
+ 线程池用完不关闭
+ 第三方框架资源未释放
+ OOM 后异常捕获导致对象逃逸

内存泄漏 → 老年代只增不减 → **必然频繁 Full GC**

### 4. 批量查询必须分页
一次 `select * from 大表` 直接 OOM + Full GC

---

## 四、GC 日志怎么看是不是快 Full GC 了？
开启 GC 日志：

```plain
-Xlog:gc*:file=gc.log:time,level,tags
```

出现这些信号，说明马上要 Full GC：

1. Young GC 后存活对象**越来越多**
2. 老年代使用率**持续上涨不下降**
3. 并发 GC 失败：`concurrent mode failure`
4. 元空间接近上限

---

## 五、给你一套“几乎不 Full GC”的最终参数（JDK8 + G1）
```plain
-server
-Xms4g -Xmx4g
-XX:+UseG1GC
-XX:MaxGCPauseMillis=20
-XX:MetaspaceSize=256m
-XX:MaxMetaspaceSize=512m
-XX:+DisableExplicitGC
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/tmp/
```

---

## 六、一句话总结
想**尽量避免 Full GC**，就抓 4 件事：

1. **用 G1/ZGC**
2. **禁止显式 GC**
3. **消灭大对象 & 内存泄漏**
4. **不让对象过早进入老年代**

只要做到这四条，你的服务**可以做到几天甚至几个月不一次 Full GC**。

你可以告诉我：

+ JDK 版本
+ 堆大小
+ 现在用的 GC 算法
我可以直接给你**定制一套最稳的 JVM 参数**。
