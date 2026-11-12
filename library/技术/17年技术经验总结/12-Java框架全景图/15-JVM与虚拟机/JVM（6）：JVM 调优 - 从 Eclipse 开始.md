# JVM（6）：JVM 调优 - 从 Eclipse 开始

> ⚠️ 本篇为为知笔记导出存档，导出时丢失了部分数字，配置与命令不可直接复制执行，仅作思路与步骤参考。
>
> 来源：纯洁的微笑（ImportNew），原文：www.cnblogs.com/ityouknow/p/html
>
> 注：下文配置中残存的「>」为原参数值丢失后的痕迹。
>
> 2026-11-08：可推断项已修复并标注「修复值」（如 XXMaxPermSize 常规默认 256m、系列序号按本系列篇目推定）；无法推断的以「已丢失」或占位标注，未编造数值。

## 什么是 JVM 调优：从 GC 日志分析入手

什么是jvm调优呢？jvm调优就是根据gc日志分析jvm内存分配、回收的情况来调整各区域内存比例或者gc回收的策略；更深一层就是根据dump出来的内存结构和线程栈来分析代码中不合理的地方给予改进。eclipse优化主要涉及的是前者，通过gc日志来分析。本文主要是通过分析eclipse gc日志为例来示例如何根据gc日志来分析jvm内存而进行调优,像根据关闭eclipse启动项、关闭各种校验等措施来优化eclipse本文不再阐述，网上有很多，本次测试的eclipse已经进行了配置上面的优化。

## 准备环境

- eclipse版本：Release（版本号已丢失）.
- eclipse 默认配置：eclipse.ini

```ini
-startup
plugins/org.eclipse.equinox.launcher_<版本已丢失>.jar
--launcher.library
plugins/org.eclipse.equinox.launcher.winwinx_<版本已丢失>（版本号已丢失）
-product
org.eclipse.epp.package.jee.product
--launcher.defaultAction
openFile
--launcher.XXMaxPermSize
256m（修复值，原值丢失，eclipse.ini 常规默认）
-showsplash
org.eclipse.platform
--launcher.XXMaxPermSize
256m（修复值，原值丢失，eclipse.ini 常规默认）
--launcher.defaultAction
openFile
--launcher.appendVmargs
-vmargs
-Dosgi.requiredJavaVersion=<版本号已丢失>
-Xms<值丢失>
-Xmx<值丢失>
```

在配置的末尾处添加如下配置文件：

```ini
-XX:+PrintGCDetails    # 输出GC的详细日志
-XX:+PrintGCDateStamps # 输出GC的时间戳（以日期的形式）
-Xloggc:gc.log         # 输出GC的详细日志
```

- eclipse启动计时插件：<http://www.chendd.cn/information/viewInformation/experienceShare/a>
- GChisto.jar：gc日志分析工具jar包一个
- Visual GC：java自带的内存监控工具，通过visual gc可以实时的监控到各个内存区域的变化。

## 如何分析GC日志

摘录GC日志一部分（绿色为年轻代gc回收；蓝色为full gc回收；注：日志中的时间戳与内存数值均已丢失，仅保留结构）：

```text
<时间戳> [GC [PSYoungGen: <回收前>-><回收后>(<总量>)] <堆变化>, <耗时> secs] [Times: user=<耗时> sys=<耗时>, real=<耗时> secs]

<时间戳> [Full GC [PSYoungGen: <回收前>-><回收后>(<总量>)] [ParOldGen: <回收前>-><回收后>(<总量>)] <堆变化>(<总量>) [PSPermGen: <回收前>-><回收后>(<总量>)], <耗时> secs] [Times: user=<耗时> sys=<耗时>, real=<耗时> secs]
```

通过上面日志分析得出，PSYoungGen、ParOldGen、PSPermGen属于Parallel收集器。其中PSYoungGen表示gc回收前后年轻代的内存变化；ParOldGen表示gc回收前后老年代的内存变化；PSPermGen表示gc回收前后永久区的内存变化。young gc 主要是针对年轻代进行内存回收比较频繁，耗时短；full gc 会对整个堆内存进行回城，耗时长，**因此一般尽量减少full gc的次数**

通过两张图非常明显看出gc日志构成：

- young gc 日志
- Full GC日志

## 启动调优

启动eclipse查看默认配置下启动时间大概是 <N> 秒（原数值已丢失）。

根据GChisto分析gc日志看出来，启动过程中进行了一次full gc,<N>次minor gc（原数值已丢失）;full gc和young gc的时间差不多都是 <T> 秒左右（原数值已丢失）。

### 第一步优化

为了避免内存频繁的动态扩展，直接把-Xms配置和-Xmx一致，修改如下：

```ini
-Xms<值丢失，与-Xmx一致>
```

修改完毕，重新启动：

启动时间缩小到 <N> 秒（原数值已丢失），分析gc日志得出young gc <N>次（原数值已丢失），full gc没有了! 但是young gc增加了两次。

### 第二步优化

因为本机的内存（大小已丢失）,给eclipse分配还是有点小了，简单粗暴直接所有内存配置加倍。

配置如下：

```ini
–launcher.XXMaxPermSize
<值丢失>
–launcher.XXMaxPermSize
<值丢失>
-Xms<值丢失>
-Xmx<值丢失>
```

启动时间缩小到 <N> 秒（原数值已丢失），但是 young gc已经缩短到只有<N>次（原数值已丢失），说明因为gc回收导致eclipse 启动慢的问题已经初步解决

### 第三步优化

通过Visual GC看到在eclipse启动的时候classloader加载class的时间有一些，关闭字节码可能会优化一部分启动时间，加入如下参数：

```ini
-Xverify:none # 关闭Java字节码验证，从而加快了类装入的速度
```

重新启动测试,启动时间已经优化到了 <N> 秒（原数值已丢失）！

查看启动日志，young gc 的次数仅仅只有了一次！

至此优化结束，附最终的eclipse.ini文件

```ini
-startup
plugins/org.eclipse.equinox.launcher_<版本已丢失>.jar
--launcher.library
plugins/org.eclipse.equinox.launcher.winwinx_<版本已丢失>
-product
org.eclipse.epp.package.jee.product
--launcher.defaultAction
openFile
--launcher.XXMaxPermSize
256m（修复值，原值丢失，eclipse.ini 常规默认）
-showsplash
org.eclipse.platform
--launcher.XXMaxPermSize
256m（修复值，原值丢失，eclipse.ini 常规默认）
--launcher.defaultAction
openFile
--launcher.appendVmargs
-vmargs
-Dosgi.requiredJavaVersion=<版本号已丢失>
-Xms<值丢失>
-Xmx<值丢失>
-Xverify:none
-XX:+PrintGCDetails
-XX:+PrintGCDateStamps
-Xloggc:gc.log
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 520" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="320" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Eclipse 启动 GC 调优步骤</text>
  <rect x="160" y="58" width="320" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="86" text-anchor="middle" font-size="13" fill="#1e293b">打开 GC 日志，记录启动基线</text>
  <line x1="320" y1="104" x2="320" y2="132" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="160" y="134" width="320" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="162" text-anchor="middle" font-size="13" fill="#1e293b">分析日志：young GC 频繁、Full GC 慢</text>
  <line x1="320" y1="180" x2="320" y2="208" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="160" y="210" width="320" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="238" text-anchor="middle" font-size="13" fill="#1e293b">第一步：Xms 与 Xmx 设为一致</text>
  <line x1="320" y1="256" x2="320" y2="284" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="160" y="286" width="320" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="314" text-anchor="middle" font-size="13" fill="#1e293b">第二步：内存配置加倍，GC 次数下降</text>
  <line x1="320" y1="332" x2="320" y2="360" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="160" y="362" width="320" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="390" text-anchor="middle" font-size="13" fill="#1e293b">第三步：关闭字节码验证，加快类加载</text>
  <line x1="320" y1="408" x2="320" y2="436" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="160" y="438" width="320" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="320" y="466" text-anchor="middle" font-size="13" fill="#1e293b">重启验证：启动时间与 GC 次数对比</text>
</svg>

*图：Eclipse 启动 GC 调优步骤示意（据原文重绘）*

## 本系列

> 注：原导出序号缺失，以下序号按本系列实际篇目（与库内《JVM》目录一致）修复，此处为修复值。

- [JVM（1）：Java 类的加载机制](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=eefeecdfde&chksm=bdaaccfedeacfefadcdddfcc&scene=#wechat_redirect)
- [JVM（2）：JVM内存结构](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=eefcffbefa&chksm=bdacfddddffccdaaefcfa&scene=#wechat_redirect)
- [JVM（3）：Java GC算法 垃圾收集器](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=fecbdffedeec&chksm=bdacaffcdcecefafceec&scene=#wechat_redirect)
- [JVM（4）：Jvm调优-命令篇](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=acaedecddddc&chksm=bdcacacaeacfaaaaabdedade&scene=#wechat_redirect)
- [JVM（5）：tomcat性能调优和性能监控（visualvm）](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=dcbfdcabcdfde&chksm=bdacfadccdafefcfddffdea&scene=#wechat_redirect)
- JVM（6）：JVM调优-从eclipse开始（本篇）
