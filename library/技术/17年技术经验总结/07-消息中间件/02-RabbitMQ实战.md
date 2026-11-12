# RabbitMQ实战

> 模块：消息中间件
> 更新时间：2026-03-28

---

## 一、核心概念：架构、Exchange类型与常用命令

### 1. 架构

```
┌──────────┐     ┌──────────────────┐     ┌────────────┐
│ Producer │ ──► │ RabbitMQ Server  │ ◄── │ Consumer   │
│          │     │                  │     │            │
│          │     │  ┌────────────┐ │     │            │
│          │     │  │  Exchange  │ │     │            │
│          │     │  └─────┬──────┘ │     │            │
│          │     │        │        │     │            │
│          │     │ ┌──────▼──────┐ │     │            │
│          │     │ │   Queue    │ │     │            │
└──────────┘     │ └────────────┘ │     └────────────┘
                 └────────────────┘

Exchange类型：
  direct：完全匹配Routing Key
  fanout：广播到所有绑定队列
  topic：通配符匹配（*.info, log.#）
  headers：按消息头匹配（不常用）
```

### 2. 常用命令

```bash
# 基础操作
rabbitmqctl list_queues     # 列出队列
rabbitmqctl list_exchanges  # 列出交换机
rabbitmqctl list_bindings   # 列出绑定

# 用户管理
rabbitmqctl add_user admin password
rabbitmqctl set_permissions admin ".*" ".*" ".*"
rabbitmqctl set_user_tags admin administrator

# 集群
rabbitmqctl join_cluster rabbit@node1
rabbitmqctl cluster_status

# 启用插件
rabbitmqctl enable_plugins
rabbitmq-plugins list
rabbitmq-plugins enable rabbitmq_management
```

---

## 二、Spring Boot集成：配置、生产者与消费者

### 1. 配置

```yaml
spring:
  rabbitmq:
    host: localhost
    port: 5672
    username: guest
    password: guest
    virtual-host: /
    # 确认模式
    publisher-confirm-type: correlated
    # 失败回调
    publisher-returns: true
    # 消费者并发数
    listener:
      simple:
        concurrency: 5
        max-concurrency: 10
        prefetch: 10
        acknowledge-mode: auto
```

### 2. 生产者

```java
@Service
public class OrderService {
    
    @Autowired
    private RabbitTemplate rabbitTemplate;
    
    public void sendOrder(Order order) {
        // 确认回调
        rabbitTemplate.setConfirmCallback((data, ack, cause) -> {
            if (!ack) {
                System.out.println("消息发送失败: " + cause);
                // 重试或记录
            }
        });
        
        // 失败回调
        rabbitTemplate.setReturnsCallback(returned -> {
            System.out.println("消息路由失败: " + returned.getMessage());
        });
        
        // 发送消息
        rabbitTemplate.convertAndSend(
            "order.exchange",    // 交换机
            "order.create",      // routing key
            order,               // 消息体
            msg -> {
                msg.getMessageProperties().setDeliveryMode(MessageDeliveryMode.PERSISTENT);
                return msg;
            }
        );
    }
}
```

### 3. 消费者

```java
@Component
public class OrderConsumer {
    
    @RabbitListener(queues = "order.queue")
    public void handleOrder(Order order, Message msg, Channel channel) {
        long deliveryTag = msg.getMessageProperties().getDeliveryTag();
        try {
            // 处理订单
            processOrder(order);
            
            // 确认消息
            channel.basicAck(deliveryTag, false);
        } catch (Exception e) {
            // 拒绝消息，重新入队
            channel.basicNack(deliveryTag, false, true);
        }
    }
    
    @RabbitListener(bindings = @QueueBinding(
        value = @Queue("order.delay.queue"),
        exchange = @Exchange("order.delay.exchange"),
        key = "order.delay"
    ))
    public void handleDelayOrder(Order order) {
        // 处理延迟订单
    }
}
```

---

## 三、常见问题：消息丢失与消息重复

> **消息丢失分三个环节：生产者丢失用 Confirm 确认，MQ 丢失用持久化 + Mirror 队列，消费者丢失用手动 ACK。**

### 1. 消息丢失

*图：消息丢失的三个环节与对应解决方案（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 200" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="40" y="30" width="180" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="130" y="57" text-anchor="middle" font-size="14" fill="#1e293b">生产者 Producer</text>
  <line x1="220" y1="52" x2="265" y2="52" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="242" y="44" text-anchor="middle" font-size="12" fill="#475569">发送</text>
  <rect x="270" y="30" width="180" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="57" text-anchor="middle" font-size="14" fill="#1e293b">RabbitMQ</text>
  <line x1="450" y1="52" x2="495" y2="52" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="472" y="44" text-anchor="middle" font-size="12" fill="#475569">投递</text>
  <rect x="500" y="30" width="180" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="590" y="57" text-anchor="middle" font-size="14" fill="#1e293b">消费者 Consumer</text>

  <line x1="130" y1="74" x2="130" y2="126" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="155" y="105" font-size="12" fill="#dc2626">场景1：生产者丢失</text>
  <line x1="360" y1="74" x2="360" y2="126" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="385" y="105" font-size="12" fill="#dc2626">场景2：MQ丢失</text>
  <line x1="590" y1="74" x2="590" y2="126" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="615" y="105" font-size="12" fill="#dc2626">场景3：消费者丢失</text>

  <rect x="40" y="130" width="180" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="130" y="157" text-anchor="middle" font-size="14" fill="#1e293b">Confirm确认机制</text>
  <rect x="270" y="130" width="180" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="157" text-anchor="middle" font-size="14" fill="#1e293b">持久化 + Mirror队列</text>
  <rect x="500" y="130" width="180" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="590" y="157" text-anchor="middle" font-size="14" fill="#1e293b">手动ACK</text>
</svg>

```java
// 场景1：生产者丢失
// 解决：Confirm确认机制

// 场景2：MQ丢失
// 解决：持久化 + Mirror队列
spring:
  rabbitmq:
    publisher-confirm-type: correlated
    publisher-returns: true

// 场景3：消费者丢失
// 解决：手动ACK
listener:
  simple:
    acknowledge-mode: manual

@RabbitListener(queues = "order.queue")
public void handle(Message msg, Channel channel) {
    try {
        process(msg);
        channel.basicAck(msg.getMessageProperties().getDeliveryTag(), false);
    } catch (Exception e) {
        channel.basicNack(msg.getMessageProperties().getDeliveryTag(), false, true);
    }
}
```

### 2. 消息重复

**解决：业务幂等。**

```java
// 解决：业务幂等
@Service
public class OrderService {
    
    @Autowired
    private RedisTemplate redisTemplate;
    
    public void processOrder(Order order) {
        // 幂等key
        String key = "order:idempotent:" + order.getId();
        
        // 尝试设置，如果已存在则跳过
        Boolean success = redisTemplate.opsForValue()
            .setIfAbsent(key, "1", Duration.ofDays(7));
        
        if (!success) {
            return; // 已处理过
        }
        
        // 正常处理订单
        saveOrder(order);
    }
}
```

---

*下一步：Kafka实战*
