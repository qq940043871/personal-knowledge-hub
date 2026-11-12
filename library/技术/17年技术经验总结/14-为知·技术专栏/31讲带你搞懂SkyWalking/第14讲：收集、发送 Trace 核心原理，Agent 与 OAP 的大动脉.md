# 第14讲：收集、发送 Trace 核心原理，Agent 与 OAP 的大动脉

在前面的课时中，我们深入介绍了 SkyWalking 对 Trace 基本概念的实现。本课时我们将继续深入学习 Trace 相关的 BootService 接口实现类以及 Trace 收集和发送的核心逻辑。Trace 相关的 BootService 接口实现类如下图所示：

## ContextManager

ContextManager 的主要职责就是管理前文介绍的 TracingContext，它会通过 ThreadLocal 将 TracingContext 对象与当前线程进行绑定，这样就实现了 TraceSegment、TracingContext 和 线程三方之间的关联。

ContextManager 有三个核心字段：

- **CONTEXT（ThreadLocal 类型）**：通过该字段可以将一个 TracingContext 对象与一个线程进行关联。
- **RUNTIME_CONTEXT（ThreadLocal 类型）**：RuntimeContext 底层封装了一个 ConcurrentHashMap 集合，可以为当前 TracingContext 记录一些附加信息。
- **EXTEND_SERVICE（ContextManagerExtendService 类型）**：ContextManagerExtendService 也实现了 BootService 接口，它主要负责创建 TracingContext 对象。

虽然 ContextManager 实现了 BootService 接口，但是其 prepare()、boot()、onComplete() 方法都为空实现。ContextManager 提供了与 TracingContext 对应的几乎所有方法，基本实现都是委托给当前线程绑定的 TracingContext 对象，这里以 createEntrySpan() 方法为例进行介绍：

```
public static AbstractSpan createEntrySpan(String operationName,
         ContextCarrier carrier) {
    SamplingService samplingService = ServiceManager.INSTANCE
            .findService(SamplingService.class);     // 采样相关
    AbstractSpan span;
    AbstractTracerContext context;
    // 检测ContextCarrier是否合法，其实就是检查它的核心字段是否已填充好
    if (carrier != null && carrier.isValid()) {
        samplingService.forceSampled();
        // 获取当前线程绑定的TracingContext
        context = getOrCreate(operationName, true);
        // 委托给当前线程绑定的TracingContext来创建EntrySpan
        span = context.createEntrySpan(operationName);
        // 从ContextCarrier提取上游服务传播过来的Trace信息
        context.extract(carrier);
    } else { // 没有上游服务的场景
        context = getOrCreate(operationName, false);
        span = context.createEntrySpan(operationName);
    }
    return span;
}
```

getOrCreate() 方法会从 CONTEXT 字段中获取当前线程绑定的 TracingContext 对象，如果当前线程没有关联 TracingContext 上下文，则会通过 ContextManagerExtendService 新建并绑定。

stopSpan() 方法在关闭 Span 的同时，还会检查当前 TraceSegment 是否结束，TraceSegment 结束时会将存储在 CONTEXT 中的 TracingContext 对象以及 RUNTIME_CONTEXT 中的附加信息一并清除，这也是为了防止内存泄露的一步重要操作。

## Context 生成与采样

如果不做任何限制，每个请求都应该生成一条完整的 Trace。在面对海量请求时如果也同时产生海量 Trace，就会给网络和存储带来双倍的压力，浪费很多资源。为了解决这个问题，**几乎所有的 Trace 系统都会支持采样的功能**。SamplingService 就是用来实现采样功能的 BootService 实现。

SamplingService 的采样逻辑依赖 samplingFactorHolder 字段（AtomicInteger 类型）的自增。ContextManagerExtendService 是负责创建 TracingContext 的 BootService 实现，在 ContextManagerExtendService 创建 TracingContext 时，会调用 SamplingService 的 trySampling() 方法递增 samplingFactorHolder 字段（CAS 操作），当增加到阈值（默认值为 ，可以通过 agent.sample_n_per__secs 配置进行修改）时会返回 false，表示采样失败，这时 ContextManagerExtendService 就会生成 IgnoredTracerContext，IgnoredTracerContext 是个空 Context 实现，不会记录 Trace 信息。

另外，SamplingService 中会启动一个定时任务，每秒都会将 samplingFactorHolder 字段清零，这样就实现了每秒采样指定条数的 Trace 数据，如下图所示：

## Trace 的收集

这里我们先来回顾一个知识点，当 TracingContext 通过 stopSpan() 方法关闭最后一个 Span 时，会调用 finish() 方法关闭相应的 TraceSegment，与此同时，还会调用 TracingContext.ListenerManager.notifyFinish() 方法通知所有监听 TracingContext 关闭事件的监听器 —— TracingContextListener。TracingContext.finish() 方法的相关实现如下：

```
private void finish() {
    TraceSegment finishedSegment =
          segment.finish(isLimitMechanismWorking());
    TracingContext.ListenerManager.notifyFinish(finishedSegment);
}
```

TraceSegmentServiceClient 是 TracingContextListener 接口的唯一实现，其主要功能就是在 TraceSegment 结束时对其进行收集，并发送到后端的 OAP 集群。

下图展示了 TraceSegmentServiceClient 的核心结构：

TraceSegmentServiceClient 底层维护了一个 DataCarrier 对象，其底层 Channels 默认有多个 Buffer，每个 Buffer 有一定长度，使用的是 IF_POSSIBLE 阻塞写入策略，底层会启动一个 ConsumerThread 线程。

TraceSegmentServiceClient 作为一个 TracingContextListener 接口的实现，会在 notifyFinish() 方法中，将刚刚结束的 TraceSegment 写入到 DataCarrier 中缓存。同时，TraceSegmentServiceClient 实现了前面介绍的 IConsumer 接口，封装了消费 Channels 中数据的逻辑，在 consume() 方法中会首先将消费到的 TraceSegment 对象序列化，然后通过 gRPC 请求发送到后端 OAP 集群。该过程涉及的 gRPC 接口定义如下：

```
service TraceSegmentReportService {
    rpc collect (stream UpstreamSegment) returns (Commands) {
    }
}
```

该 gRPC 请求中用到的 UpstreamSegment 结构体包含了 Trace ID 以及 TraceSegment 序列化之后的字节数组，定义如下所示：

```
message UpstreamSegment {
    repeated UniqueId globalTraceIds = 1; // 注：原导出字段编号缺失，此处为修复值
    bytes segment = 2; // TraceSegment信息（编号为修复值）
}
```

这个过程中，TraceSegment 对象会转换成相应的 proto 结构体实例，下图展示了 UpstreamSegment 中包含的具体信息：

既然要发送 gRPC 请求，就必然要依赖网络连接，TraceSegmentServiceClient 实现了 GRPCChannelListener 接口，可以监听底层网络连接的变化情况。在 prepare() 方法中可将其作为 Listener 注册到前文介绍的 GRPCChannelManager 中。

明确了发送 Trace 时的具体数据，以及其涉及的 gRPC 请求和接口定义，我们再来看 consume() 方法的具体实现：

```
public void consume(List<TraceSegment> data) {
    if (CONNECTED.equals(status)) { // 根据底层网络连接的状态决定是否发送
        // 创建GRPCStreamServiceStatus对象
        final GRPCStreamServiceStatus status =
             new GRPCStreamServiceStatus(false);
        StreamObserver<UpstreamSegment> upstreamSegmentStreamObserver
               = serviceStub.collect(new StreamObserver<Commands>() {
            public void onNext(Commands commands) {}
            public void onError(Throwable throwable) {
                // 发生异常会调用 finished()方法，停止等待
                status.finished();
                // 通知GRPCChannelManager重新创建网络连接
                ServiceManager.INSTANCE.findService(
                   GRPCChannelManager.class).reportError(throwable);
            }
            public void onCompleted() {
                // 发送成功之后，会调用finished()方法结束等待
                status.finished();
            }
        });
        for (TraceSegment segment : data) {
            // 将TraceSegment转换成UpstreamSegment对象，然后才能进行序列化以
            // 及发送操作transform()方法实现的转换逻辑并不复杂，填充字段而已
            UpstreamSegment upstreamSegment = segment.transform();
            upstreamSegmentStreamObserver.onNext(upstreamSegment);
        }
        upstreamSegmentStreamObserver.onCompleted();
        status.waitFinish(); // 等待全部TraceSegment数据发送结束
        segmentUplinkedCounter += data.size(); // 统计发送的数据量
    } else { // 网络连接断开时，只进行简单统计，数据将被直接抛弃
        segmentAbandonedCounter += data.size();
    }
    printUplinkStatus(); // 每隔 s打印一下发送日志
}
```

注意，TraceSegmentServiceClient 在批量发送完 UpstreamSegment 数据之后，会通过 GRPCStreamServiceStatus 进行自旋等待，直至该批 UpstreamSegment 全部发送完毕。

最后总结一下，TraceSegmentServiceClient 同时实现了 BootService、IConsumer、GRPCChannelListener、TracingContextListener 四个接口，如下图所示，这四个接口的实现相互依赖，共同完成 Trace 数据的收集和发送：

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 600" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="320" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Trace 收集与发送链路示意</text>
  <rect x="130" y="58" width="380" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="86" text-anchor="middle" font-size="13" fill="#1e293b">stopSpan() 关闭最后一个 Span</text>
  <line x1="320" y1="104" x2="320" y2="132" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="130" y="134" width="380" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="162" text-anchor="middle" font-size="13" fill="#1e293b">TraceSegment.finish() 结束 TraceSegment</text>
  <line x1="320" y1="180" x2="320" y2="208" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="130" y="210" width="380" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="238" text-anchor="middle" font-size="13" fill="#1e293b">notifyFinish() 通知 TracingContextListener</text>
  <line x1="320" y1="256" x2="320" y2="284" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="130" y="286" width="380" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="320" y="314" text-anchor="middle" font-size="13" fill="#1e293b">TraceSegmentServiceClient 写入 DataCarrier</text>
  <line x1="320" y1="332" x2="320" y2="360" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="330" y="350" text-anchor="start" font-size="12" fill="#475569">生产者-消费者模式</text>
  <rect x="130" y="362" width="380" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="320" y="390" text-anchor="middle" font-size="13" fill="#1e293b">ConsumerThread 消费者线程批量消费</text>
  <line x1="320" y1="408" x2="320" y2="436" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="130" y="438" width="380" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="466" text-anchor="middle" font-size="13" fill="#1e293b">segment.transform() 转成 UpstreamSegment</text>
  <line x1="320" y1="484" x2="320" y2="512" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="130" y="514" width="380" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="542" text-anchor="middle" font-size="13" fill="#1e293b">gRPC collect 流式上报 OAP 集群</text>
</svg>

*图：TraceSegment 从收集到 gRPC 上报的链路（据原文重绘）*

## 总结：Trace 收集与发送核心逻辑

本课时我们重点介绍了 Trace 相关的 BootService 接口实现。首先介绍了 ContextManager 的核心实现，理清了它是如何将 TracingContext 与当前线程关联起来的。接下来介绍了 SamplingService 实现客户端 Trace 采样的逻辑。最后介绍了上报 Trace 的 gRPC 接口，深入分析了 TraceSegmentServiceClient 收集和上报 Trace 数据的核心逻辑。
