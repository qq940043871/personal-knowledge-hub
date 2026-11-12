# Kafka消息系统

> 模块：消息中间件
> 更新时间：2026-03-29

---

## 一、框架介绍

Kafka是LinkedIn开源的分布式流处理平台，用于构建实时数据管道和流应用。它具有高吞吐量、低延迟的特点，适合日志收集、消息队列、实时分析等场景。

**官网**：[https://kafka.apache.org](https://kafka.apache.org)

**核心概念**：
- **Topic（主题）**：消息的分类
- **Partition（分区）**：实现并行处理
- **Producer（生产者）**：发送消息
- **Consumer（消费者）**：接收消息
- **Consumer Group（消费者组）**：消费组内消息被负载均衡

*图：Kafka 消息流转与消费组（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 200" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="56" width="130" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="85" y="78" text-anchor="middle" font-size="14" fill="#1e293b">Producer 生产者</text>
  <text x="85" y="98" text-anchor="middle" font-size="12" fill="#475569">发送消息</text>
  <line x1="150" y1="82" x2="185" y2="82" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="56" width="150" height="52" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="265" y="78" text-anchor="middle" font-size="14" fill="#1e293b">Topic 主题</text>
  <text x="265" y="98" text-anchor="middle" font-size="12" fill="#475569">Partition 分区</text>
  <line x1="340" y1="82" x2="375" y2="82" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="380" y="56" width="170" height="52" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="465" y="78" text-anchor="middle" font-size="14" fill="#1e293b">Consumer Group</text>
  <text x="465" y="98" text-anchor="middle" font-size="12" fill="#475569">消费者组接收消息</text>
  <text x="360" y="160" text-anchor="middle" font-size="13" fill="#475569">消息按主题分类，分区实现并行处理，消费组内消息被负载均衡</text>
</svg>

---

## 二、实际业务应用场景

### 场景1：日志收集

```java
// 1. 配置
spring:
  kafka:
    bootstrap-servers: localhost:9092
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.apache.kafka.common.serialization.StringSerializer
    consumer:
      group-id: my-group
      auto-offset-reset: earliest
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.apache.kafka.common.serialization.StringDeserializer

// 2. 发送消息
@Service
public class LogProducer {
    
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;
    
    public void sendLog(String log) {
        kafkaTemplate.send("app-logs", log);
    }
}

// 3. 消费消息
@Component
public class LogConsumer {
    
    @KafkaListener(topics = "app-logs", groupId = "log-processor")
    public void consume(String message) {
        // 保存到ES或HDFS
        logService.save(message);
    }
}
```

### 场景2：实时数据同步

```java
// 订单数据同步到数据分析系统
@Service
public class OrderSyncProducer {
    
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;
    
    public void syncOrder(Order order) {
        ObjectMapper mapper = new ObjectMapper();
        try {
            String json = mapper.writeValueAsString(order);
            kafkaTemplate.send("order-sync", order.getOrderNo(), json);
        } catch (Exception e) {
            log.error("订单同步失败", e);
        }
    }
}

@Component
public class OrderSyncConsumer {
    
    @KafkaListener(topics = "order-sync")
    public void handleOrderSync(ConsumerRecord<String, String> record) {
        // 处理订单数据
        analyticsService.processOrder(record.value());
    }
}
```

---

## 三、总结

**Kafka适合高吞吐量场景，是大数据生态的核心组件。**

**学习要点**：
1. Topic和Partition机制
2. 消费者组和负载均衡
3. 消息可靠性保证
4. 事务语义

---

*下一步：Docker容器化*
