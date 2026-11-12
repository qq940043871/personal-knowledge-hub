# JVM原理 - 架构师学习笔记

Java虚拟机（JVM）是Java平台的核心组件，它负责执行Java字节码，提供内存管理、垃圾回收、即时编译等核心功能。**深入理解JVM原理对于Java性能调优和故障排查至关重要**。

## JVM架构

### JVM组成

| 组件 | 功能 |
|------|------|
| 类加载器（Class Loader） | 负责加载.class文件到内存 |
| 运行时数据区（Runtime Data Area） | 管理JVM运行时的内存区域 |
| 执行引擎（Execution Engine） | 执行字节码指令 |
| 本地方法接口（JNI） | 与本地方法库交互 |
| 本地方法库（Native Method Libraries） | 本地方法的实现 |

*图：JVM 组成与运行时数据区（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 360" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="70" y="16" width="220" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="180" y="41" text-anchor="middle" font-size="14" fill="#1e293b">类加载器（Class Loader）</text>
  <rect x="430" y="16" width="220" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="540" y="41" text-anchor="middle" font-size="14" fill="#1e293b">执行引擎（Execution Engine）</text>
  <line x1="180" y1="56" x2="180" y2="86" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="540" y1="56" x2="540" y2="86" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="40" y="90" width="640" height="180" rx="10" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5"/>
  <text x="360" y="114" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">运行时数据区（Runtime Data Area）</text>
  <rect x="70" y="122" width="280" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="210" y="141" text-anchor="middle" font-size="13" fill="#1e293b">方法区（Method Area）</text>
  <text x="210" y="160" text-anchor="middle" font-size="11" fill="#475569">线程共享</text>
  <rect x="370" y="122" width="280" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="510" y="141" text-anchor="middle" font-size="13" fill="#1e293b">堆（Heap）</text>
  <text x="510" y="160" text-anchor="middle" font-size="11" fill="#475569">线程共享 · 垃圾回收主要区域</text>
  <rect x="70" y="196" width="190" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="165" y="215" text-anchor="middle" font-size="13" fill="#1e293b">虚拟机栈（VM Stack）</text>
  <text x="165" y="234" text-anchor="middle" font-size="11" fill="#475569">线程私有</text>
  <rect x="275" y="196" width="190" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="370" y="215" text-anchor="middle" font-size="13" fill="#1e293b">本地方法栈</text>
  <text x="370" y="234" text-anchor="middle" font-size="11" fill="#475569">线程私有</text>
  <rect x="480" y="196" width="190" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="575" y="215" text-anchor="middle" font-size="13" fill="#1e293b">程序计数器（PC Register）</text>
  <text x="575" y="234" text-anchor="middle" font-size="11" fill="#475569">线程私有</text>
  <rect x="70" y="300" width="220" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="180" y="325" text-anchor="middle" font-size="14" fill="#1e293b">本地方法接口（JNI）</text>
  <rect x="430" y="300" width="220" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="540" y="325" text-anchor="middle" font-size="14" fill="#1e293b">本地方法库（Native Libraries）</text>
</svg>

## 运行时数据区

### 方法区（Method Area）

- 存储类信息、常量、静态变量等
- 被所有线程共享
- 在JDK 8中被元空间（Metaspace）替代

### 堆（Heap）

- 存储对象实例和数组
- 被所有线程共享
- **是垃圾回收的主要区域**

### 虚拟机栈（VM Stack）

- 存储局部变量表、操作数栈等
- 每个线程私有
- StackOverflowError异常发生地

### 本地方法栈（Native Method Stack）

- 为本地方法服务
- 每个线程私有
- 与虚拟机栈类似但为Native方法服务

### 程序计数器（Program Counter Register）

- 记录当前线程执行的字节码指令地址
- 每个线程私有
- **是唯一不会出现OutOfMemoryError的区域**

## 垃圾回收机制

### 垃圾回收算法

- 标记-清除算法：标记所有需要回收的对象，统一回收
- 复制算法：将存活对象复制到另一块内存区域
- 标记-整理算法：标记后将存活对象向一端移动
- 分代收集算法：根据对象存活周期将内存分为几块

### 垃圾收集器

- Serial收集器：单线程收集器
- ParNew收集器：Serial收集器的多线程版本
- Parallel Scavenge收集器：关注吞吐量的收集器
- CMS收集器：以最短回收停顿时间为目标
- G1收集器：面向服务端应用的收集器

## 类加载机制

### 双亲委派模型

类加载器之间的层次关系，保证Java程序的稳定运行。

| 类加载器 | 加载类的范围 |
|---------|------------|
| 启动类加载器（Bootstrap ClassLoader） | 加载%JAVA_HOME%/lib目录下的类库 |
| 扩展类加载器（Extension ClassLoader） | 加载%JAVA_HOME%/lib/ext目录下的类库 |
| 应用程序类加载器（Application ClassLoader） | 加载用户类路径上指定的类库 |

### 工作原理

- 类加载器收到类加载请求时，不会自己去加载，而是委派给父类加载器
- 父类加载器无法加载时，才会尝试自己加载
- **保证核心类库的安全性和一致性**

## JVM性能调优

### 内存调优参数

- -Xms：设置堆的初始大小
- -Xmx：设置堆的最大大小
- -Xmn：设置新生代大小
- -XX:NewRatio：设置老年代与新生代的比例
- -XX:SurvivorRatio：设置Eden区与Survivor区的比例

### 垃圾收集器调优

- -XX:+UseSerialGC：使用Serial+Serial Old收集器
- -XX:+UseParNewGC：使用ParNew+Serial Old收集器
- -XX:+UseParallelGC：使用Parallel Scavenge+Parallel Old收集器
- -XX:+UseConcMarkSweepGC：使用ParNew+CMS+Serial Old收集器
- -XX:+UseG1GC：使用G1收集器

## 常见问题诊断

### 常见JVM异常

- OutOfMemoryError：内存不足，需要调整内存参数或优化代码
- StackOverflowError：栈溢出，通常是递归调用过深
- ClassNotFoundException：类未找到，检查类路径配置
- NoClassDefFoundError：编译时能找到类，运行时找不到

### 诊断工具

- jps：查看Java进程
- jstat：监控JVM统计信息
- jmap：生成堆转储快照
- jstack：生成线程快照
- VisualVM：可视化监控工具
