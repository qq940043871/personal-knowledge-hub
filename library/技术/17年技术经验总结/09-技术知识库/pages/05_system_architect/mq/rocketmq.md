# RocketMQ - 架构师学习笔记

## RocketMQ：阿里开源的分布式消息中间件

Apache RocketMQ是阿里巴巴开源的分布式消息中间件，具有**低延迟、高性能、高可靠性、万亿级容量**和灵活的可扩展性等特点。RocketMQ最初是为满足阿里巴巴集团内部大规模分布式系统的需求而开发的，后来成为Apache顶级项目。

## RocketMQ核心概念

### Topic（主题）

消息的逻辑分类，类似于数据库中的表。生产者将消息发送到特定的Topic，消费者从Topic订阅消息。

### Message Queue（消息队列）

Topic的物理分区，每个Topic包含多个Message Queue，用于实现并行处理和负载均衡。

### Message（消息）

消息是RocketMQ中最小的数据传输单位，包含消息头和消息体两部分。

### Consumer Group（消费者组）

消费者组是一组逻辑上相同的消费者实例，用于实现负载均衡和容错。

### NameServer（命名服务器）

提供轻量级的服务发现和路由功能，Broker向NameServer注册路由信息。

### Broker（代理）

消息存储和转发的核心组件，负责接收、存储和投递消息。

## RocketMQ架构

### 架构图

```
P (Producer)
  |
  v
+----------------+
|                |
|  NS1 (NameServer 1) |
|  NS2 (NameServer 2) |
|                |
+----------------+
  |
  v
+----------------+
|                |
|  B1 (Broker 1) |
|  B2 (Broker 2) |
|  B3 (Broker 3) |
|                |
+----------------+
  |
  v
+----------------+
|                |
|  Topic A: Q0, Q1 |
|  Topic B: Q0, Q1 |
|                |
+----------------+
  |
  v
C (Consumer)
```

## 消息类型：普通、延迟、顺序与事务

### 普通消息

最基本的消息类型，支持集群消费和广播消费模式。

```java
// Producer
DefaultMQProducer producer = new DefaultMQProducer("producer_group");
producer.setNamesrvAddr("localhost:9876");
producer.start();

Message msg = new Message("TopicTest", "TagA", "OrderID188", "Hello RocketMQ".getBytes());
SendResult sendResult = producer.send(msg);
producer.shutdown();

// Consumer
DefaultMQPushConsumer consumer = new DefaultMQPushConsumer("consumer_group");
consumer.setNamesrvAddr("localhost:9876");
consumer.subscribe("TopicTest", "*");

consumer.registerMessageListener((MessageListenerConcurrently) (msgs, context) -> {
    for (MessageExt msg : msgs) {
        System.out.println(new String(msg.getBody()));
    }
    return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
});
consumer.start();
```

### 延迟消息

消息发送后不会立即投递，而是在指定的延迟时间后才投递给消费者。

```java
Message msg = new Message("TopicTest", "TagA", "OrderID188", "Hello RocketMQ".getBytes());
// 设置延迟等级，1s 5s 10s 30s 1m 2m 3m 4m 5m 6m 7m 8m 9m 10m 20m 30m 1h 2h
msg.setDelayTimeLevel(3); // 10秒后投递
producer.send(msg);
```

### 顺序消息

保证消息按照发送顺序进行消费，适用于需要严格顺序处理的场景。

```java
// Producer - 选择队列发送
producer.send(msg, new MessageQueueSelector() {
    @Override
    public MessageQueue select(List<MessageQueue> mqs, Message msg, Object arg) {
        Integer id = (Integer) arg;
        int index = id % mqs.size();
        return mqs.get(index);
    }
}, orderId);

// Consumer - 顺序消费
DefaultMQPushConsumer consumer = new DefaultMQPushConsumer("consumer_group");
consumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_FIRST_OFFSET);
consumer.registerMessageListener((MessageListenerOrderly) (msgs, context) -> {
    for (MessageExt msg : msgs) {
        System.out.println(new String(msg.getBody()));
    }
    return ConsumeOrderlyStatus.SUCCESS;
});
```

### 事务消息

实现分布式事务，确保本地事务和消息发送的原子性。

```java
// Producer
TransactionMQProducer producer = new TransactionMQProducer("transaction_producer_group");
producer.setTransactionListener(new TransactionListener() {
    @Override
    public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
        // 执行本地事务
        return LocalTransactionState.COMMIT_MESSAGE;
    }
    
    @Override
    public LocalTransactionState checkLocalTransaction(MessageExt msg) {
        // 检查本地事务状态
        return LocalTransactionState.COMMIT_MESSAGE;
    }
});
producer.send(msg);
```

## 消费模式

### 集群消费模式

同一个Consumer Group中的消费者平均分配消息，每条消息只会被其中一个消费者消费。

- 负载均衡
- 容错性好
- 适用于大部分业务场景

### 广播消费模式

同一个Consumer Group中的每个消费者都会消费所有消息。

- 消息广播
- 每个消费者都收到完整消息
- 适用于配置更新等场景

## 存储机制

### CommitLog存储

RocketMQ采用混合存储结构，所有消息都存储在CommitLog中，提高了写入性能。

- **CommitLog**：实际存储消息数据的文件
- **ConsumeQueue**：消息消费的逻辑队列
- **IndexFile**：消息索引文件，支持按消息Key查询

*图：CommitLog 混合存储结构（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw1" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="40" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="90" y="67" text-anchor="middle" font-size="14" fill="#1e293b">生产者消息</text>
  <line x1="160" y1="62" x2="224" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <text x="192" y="52" text-anchor="middle" font-size="12" fill="#475569">顺序写入</text>
  <rect x="229" y="40" width="170" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="314" y="67" text-anchor="middle" font-size="14" fill="#1e293b">CommitLog</text>
  <line x1="314" y1="84" x2="314" y2="115" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="210" y1="115" x2="510" y2="115" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="210" y1="115" x2="210" y2="145" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <line x1="510" y1="115" x2="510" y2="145" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="110" y="150" width="200" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="210" y="173" text-anchor="middle" font-size="14" fill="#1e293b">ConsumeQueue</text>
  <text x="210" y="192" text-anchor="middle" font-size="12" fill="#475569">消费逻辑队列，加速检索</text>
  <rect x="410" y="150" width="200" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="510" y="173" text-anchor="middle" font-size="14" fill="#1e293b">IndexFile</text>
  <text x="510" y="192" text-anchor="middle" font-size="12" fill="#475569">按消息Key查询</text>
</svg>

### 存储特点

- 顺序写入CommitLog，提高写入性能
- ConsumeQueue作为索引，加速消息检索
- 支持消息过期清理和文件预分配
- 支持主从同步，保证数据可靠性

## 高可用与负载均衡

### 主从复制

Broker支持主从架构，主节点负责读写，从节点负责数据备份。

- **异步复制**：性能高但可能丢失数据
- **同步双写**：数据一致性好但性能较低

### 负载均衡

通过多个Broker节点和队列分片实现负载均衡。

- **Producer负载均衡**：轮询选择队列
- **Consumer负载均衡**：队列分配算法

## 监控与管理

### 监控指标

| 指标 | 说明 | 监控工具 |
|------|------|----------|
| TPS | 每秒处理的消息数量 | RocketMQ Console, Prometheus |
| 延迟 | 消息从生产到消费的时间 | RocketMQ Console |
| Broker状态 | Broker运行状态和资源使用情况 | RocketMQ Console |
| 消息堆积 | 未消费的消息数量 | RocketMQ Console |

### 管理工具

- RocketMQ Console：Web管理界面
- mqadmin命令：命令行管理工具
- 监控告警：集成Prometheus、Grafana等

## RocketMQ最佳实践

- 合理设计Topic和Tag，便于消息分类和检索
- 根据业务需求选择合适的消息类型
- 设置合适的消息过期时间和存储策略
- 实施监控和告警，及时发现和处理异常
- 合理配置Producer和Consumer参数以优化性能
- 使用集群模式提高可用性和容错能力
- 定期清理无用的Topic和Consumer Group
