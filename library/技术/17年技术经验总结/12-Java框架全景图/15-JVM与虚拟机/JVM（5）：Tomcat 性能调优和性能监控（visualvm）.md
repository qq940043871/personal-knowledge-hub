# JVM（5）：Tomcat 性能调优和性能监控（visualvm）

> ⚠️ 本篇为为知笔记导出存档，导出时丢失了部分数字（Tomcat 默认值、示例配置值等），配置不可直接复制执行，仅作思路与步骤参考。
> 2026-11-08：标题与系列序号、个别定义性数值（如 0=永不超时）已修复并标注；无法推断的以「已丢失」或 `<占位>` 标注，未编造数值（默认值请查对应版本 Tomcat 官方文档）。

_--_ ImportNew ImportNew

**ImportNew**

（点击上方公众号，可快速关注）

> 来源：纯洁的微笑，
>
> www.cnblogs.com/ityouknow/p/html
>
> [如有好文章投稿，请点击 → 这里了解详情](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=dbcfdcdfdfca&scene=#wechat_redirect)

**tomcat服务器优化**

**1、JDK内存优化**（注：原导出序号缺失，此处为修复值）

根据服务器物理内容情况配置相关参数优化tomcat性能。当应用程序需要的内存超出堆的最大值时虚拟机就会提示内存溢出，并且导致应用服务崩溃。因此一般建议堆的最大值设置为可用内存的最大值的一定比例（原数值已丢失）。 Tomcat默认可以使用的内存为较小的默认值（原数值已丢失），在较大型的应用项目中，这点内存是不够的，需要调大.

Tomcat默认可以使用的内存为较小的默认值（原数值已丢失）,Windows下,在文件/bin/catalina.bat，Unix下，在文件/bin/catalina.sh的前面，增加如下设置： JAVA_OPTS=’-Xms【初始化内存大小】 -Xmx【可以使用的最大内存】 -XX:PermSize=<值丢失> -XX:MaxPermSize=<值丢失>’ 需要把几个参数值调大。例如： JAVA_OPTS=’-Xms <A> -Xmx <B>’（A、B 为具体数值，已丢失） 表示初始化内存为 A，可以使用的最大内存为 B。

**参数详解**

> \-server  启用jdk 的 server 版；
>
> \-Xms    java虚拟机初始化时的最小内存；
>
> \-Xmx    java虚拟机可使用的最大内存；
>
> \-XX:PermSize    内存永久保留区域
>
> \-XX:MaxPermSize   内存最大永久保留区域
>
> \-Xmn    jvm最小内存

内存配置示例：

> JAVA_OPTS="$JAVA_OPTS  -Xms<值丢失> -Xmx<值丢失> -XX:PermSize=<值丢失> -XX:MaxPermSize=<值丢失> -Xshare:off -Xmn<值丢失>"（注：原导出数字缺失，<值丢失>为占位）

**2、tomcat线程优化**（注：原导出序号缺失，此处为修复值）

在tomcat配置文件server.xml中的配置中，和连接数相关的参数有：

maxThreads： Tomcat使用线程来处理接收的每个请求。这个值表示Tomcat可创建的最大的线程数。默认值为（原数值已丢失，请查对应版本 Tomcat 官方文档）。

acceptCount： 指定当所有可以使用的处理请求的线程数都被使用时，可以放到处理队列中的请求数，超过这个数的请求将不予处理。默认值为（原数值已丢失）。

minSpareThreads： Tomcat初始化时创建的线程数。默认值为（原数值已丢失）。

maxSpareThreads： 一旦创建的线程超过这个值，Tomcat就会关闭不再需要的socket线程。默认值为（原数值已丢失）。

enableLookups： 是否反查域名，默认值为true。为了提高处理能力，应设置为false

connnectionTimeout： 网络连接超时，默认值为（原数值已丢失），单位：毫秒。设置为0表示永不超时（注：0 即永不超时，此处为修复值），这样设置有隐患的。通常可设置为 <N> 毫秒（原数值已丢失）。

maxKeepAliveRequests： 保持请求数量，默认值为（原数值已丢失）。 bufferSize： 输入流缓冲大小，默认值为（原数值已丢失） bytes。

compression： 压缩传输，取值on/off/force，默认值off。 其中和最大连接数相关的参数为maxThreads和acceptCount。如果要加大并发连接数，应同时加大这两个参数。

内存配置示例：

> <Connector port="<端口占位>" protocol="HTTP/1.1"（注：protocol 常规值，此处为修复值）
>
> connectionTimeout="<值丢失>" maxThreads="<值丢失>" minSpareThreads="<值丢失>" maxSpareThreads="<值丢失>"  acceptCount="<值丢失>"
>
> redirectPort="<值丢失>" URIEncoding="utf-8"/>（注：utf-8 为标准字符集名，此处为修复值）

**使用visualvm性能监控**

**1、什么是VisualVM**（注：原导出序号缺失，此处为修复值）

visualvm是jdk自带的一款监控工具。它提供了一个可视界面，用于查看 Java 虚拟机上运行的基于 Java 技术的程序的详细信息。VisualVM 对 Java Development Kit (JDK) 工具所检索的 JVM 软件相关数据进行组织，并通过一种使您可以快速查看有关多个 Java 应用程序的数据的方式提供该信息。您可以查看本地应用程序以及远程主机上运行的应用程序的相关数据

**2、如何安装**（注：原导出序号缺失，此处为修复值）

在jkd bin目录下有一个jvisualvm.exe文件 双击就可以使用

**3、如何使用jvisualvm**（注：原导出序号缺失，此处为修复值）

1、配置JMX管理tomcat；（注：原导出序号缺失，此处为修复值）

> set JAVA_OPTS=-Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=<端口占位> -Dcom.sun.management.jmxremote.authenticate=false -    -Dcom.sun.management.jmxremote.ssl=false

2、重启tomcat即可；（注：原导出序号缺失，此处为修复值）

3、双击jvisualvm.exe 添加服务器IP地址，添加需要监控jmx端口即可。（注：原导出序号缺失，此处为修复值）

效果如下：

**本系列：**

> 注：原导出序号缺失，以下序号按本系列实际篇目（与库内《JVM》目录一致）修复，此处为修复值。

[JVM（1）：Java 类的加载机制](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=eefeecdfde&chksm=bdaaccfedeacfefadcdddfcc&scene=#wechat_redirect)

[JVM（2）：JVM内存结构](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=eefcffbefa&chksm=bdacfddddffccdaaefcfa&scene=#wechat_redirect)

[JVM（3）：Java GC算法 垃圾收集器](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=fecbdffedeec&chksm=bdacaffcdcecefafceec&scene=#wechat_redirect)

[JVM（4）：Jvm调优-命令篇](http://mp.weixin.qq.com/s?__biz=MjMNzMyMjAwMA==&mid=&idx=&sn=acaedecddddc&chksm=bdcacacaeacfaaaaabdedade&scene=#wechat_redirect)

JVM（5）：tomcat性能调优和性能监控（visualvm）（本篇）

看完本文有收获？请转发分享给更多人

关注「ImportNew」，提升Java技能

阅读原文

阅读

投诉

精选留言

该文章作者已设置需关注才可以留言

写留言

该文章作者已设置需关注才可以留言

写留言

 加载中

以上留言由公众号筛选后显示

[了解留言功能详情](http://kf.qq.com/touch/sappfaq/YfyMVjqmMbyi.html?scene_id=kf)

微信扫一扫
关注该公众号
