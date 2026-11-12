# Redis分布式缓存

> 模块：缓存框架
> 更新时间：2026-03-29

---

## 一、框架介绍

Redis（Remote Dictionary Server）是一个开源的、基于内存的键值存储数据库，支持多种数据结构：字符串、哈希、列表、集合、有序集合等。它广泛应用于缓存、消息队列、分布式锁、计数器等场景。

**官网**：[https://redis.io](https://redis.io)

**核心特点**：
- 内存存储，性能极高
- 支持多种数据结构
- 支持持久化（RDB/AOF）
- 主从复制、哨兵、集群
- 丰富的客户端支持

---

## 二、数据结构详解

### 1. String（字符串）

```java
// String操作
redisTemplate.opsForValue().set("user:1", user);
redisTemplate.opsForValue().get("user:1");

// 过期时间
redisTemplate.opsForValue().set("code", "123456", Duration.ofMinutes(5));

// 计数器
redisTemplate.opsForValue().increment("view:article:1");  // +1
redisTemplate.opsForValue().decrement("view:article:1"); // -1
```

### 2. Hash（哈希）

```java
// 存储对象
redisTemplate.opsForHash().put("user:1", "name", "张三");
redisTemplate.opsForHash().put("user:1", "age", "25");

// 购物车场景
redisTemplate.opsForHash().put("cart:user:1", "product:100", "2");
redisTemplate.opsForHash().increment("cart:user:1", "product:100", 1);
```

### 3. ZSet（有序集合）

```java
// 排行榜
redisTemplate.opsForZSet().add("rank:score", "user:1001", 8500);
redisTemplate.opsForZSet().add("rank:score", "user:1002", 9200);

// 获取排名前3
Set<Object> top3 = redisTemplate.opsForZSet().reverseRange("rank:score", 0, 2);
```

---

## 三、实际业务应用场景

### 场景1：缓存

```java
@Service
public class UserService {
    
    @Autowired
    private RedisTemplate<String, User> redisTemplate;
    
    private static final String USER_CACHE_KEY = "user:cache:";
    
    public User getUser(Long userId) {
        String key = USER_CACHE_KEY + userId;
        
        // 查询缓存
        User user = redisTemplate.opsForValue().get(key);
        if (user != null) {
            return user;
        }
        
        // 查询数据库
        user = userMapper.selectById(userId);
        
        // 写入缓存
        redisTemplate.opsForValue().set(key, user, Duration.ofMinutes(30));
        
        return user;
    }
}
```

*图：缓存查询——先查 Redis，未命中回源数据库并写回（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="40" width="120" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="80" y="67" text-anchor="middle" font-size="14" fill="#1e293b">客户端请求</text>
  <line x1="140" y1="62" x2="175" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="40" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="255" y="67" text-anchor="middle" font-size="14" fill="#1e293b">查询 Redis 缓存</text>
  <line x1="330" y1="62" x2="360" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="365" y="40" width="130" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="430" y="67" text-anchor="middle" font-size="14" fill="#1e293b">缓存命中？</text>
  <line x1="495" y1="62" x2="530" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="512" y="54" text-anchor="middle" font-size="12" fill="#475569">是</text>
  <rect x="535" y="40" width="160" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="615" y="67" text-anchor="middle" font-size="14" fill="#1e293b">直接返回缓存值</text>
  <line x1="430" y1="84" x2="430" y2="145" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="444" y="118" text-anchor="middle" font-size="12" fill="#475569">否</text>
  <rect x="365" y="150" width="130" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="430" y="177" text-anchor="middle" font-size="14" fill="#1e293b">查询数据库</text>
  <line x1="495" y1="172" x2="530" y2="172" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="535" y="150" width="160" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="615" y="177" text-anchor="middle" font-size="14" fill="#1e293b">写回缓存（30 分钟）</text>
  <text x="360" y="228" text-anchor="middle" font-size="13" fill="#475569">命中直接返回；未命中回源数据库，写回缓存后再返回</text>
</svg>

### 场景2：分布式锁

```java
@Component
public class RedisDistributedLock {
    
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    private static final String UNLOCK_SCRIPT = 
        "if redis.call('get', KEYS[1]) == ARGV[1] then " +
        "return redis.call('del', KEYS[1]) " +
        "else return 0 end";
    
    public boolean tryLock(String key, String value, long expireTime) {
        Boolean result = redisTemplate.opsForValue()
            .setIfAbsent(key, value, Duration.ofSeconds(expireTime));
        return Boolean.TRUE.equals(result);
    }
    
    public void unlock(String key, String value) {
        // 使用Lua脚本保证原子性
        redisTemplate.execute(
            new DefaultRedisScript<>(UNLOCK_SCRIPT, Long.class),
            Collections.singletonList(key),
            value
        );
    }
}

// 使用
@Service
public class OrderService {
    
    @Autowired
    private RedisDistributedLock lock;
    
    public void createOrder(Long productId) {
        String lockKey = "lock:product:" + productId;
        String lockValue = UUID.randomUUID().toString();
        
        try {
            if (lock.tryLock(lockKey, lockValue, 10)) {
                // 扣减库存
                productService.deductStock(productId);
            }
        } finally {
            lock.unlock(lockKey, lockValue);
        }
    }
}
```

### 场景3：验证码/Token

```java
// 发送验证码
public void sendVerifyCode(String phone) {
    String code = String.valueOf((int)((Math.random() * 9 + 1) * 100000));
    
    // 存储验证码，5分钟有效
    redisTemplate.opsForValue().set("code:" + phone, code, Duration.ofMinutes(5));
    
    // 发送短信（实际项目中调用短信服务）
    smsService.send(phone, code);
}

// 验证验证码
public boolean verifyCode(String phone, String code) {
    String cachedCode = redisTemplate.opsForValue().get("code:" + phone);
    return code.equals(cachedCode);
}

// Session管理
public void saveSession(String sessionId, User user) {
    redisTemplate.opsForHash().put("session:" + sessionId, "userId", user.getId().toString());
    redisTemplate.opsForHash().put("session:" + sessionId, "name", user.getName());
    redisTemplate.expire("session:" + sessionId, Duration.ofHours(24));
}
```

---

## 四、Spring Boot整合Redis

```yaml
spring:
  redis:
    host: localhost
    port: 6379
    password: ${REDIS_PASSWORD:}
    database: 0
    lettuce:
      pool:
        max-active: 8
        max-idle: 8
        min-idle: 0
        max-wait: -1ms
```

```java
@Configuration
public class RedisConfig {
    
    @Bean
    public RedisTemplate<String, Object> redisTemplate(
            RedisConnectionFactory factory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(factory);
        
        // JSON序列化
        Jackson2JsonRedisSerializer<Object> serializer = 
            new Jackson2JsonRedisSerializer<>(Object.class);
        template.setValueSerializer(serializer);
        template.setHashValueSerializer(serializer);
        
        // String序列化
        StringRedisSerializer stringSerializer = new StringRedisSerializer();
        template.setKeySerializer(stringSerializer);
        template.setHashKeySerializer(stringSerializer);
        
        template.afterPropertiesSet();
        return template;
    }
}
```

---

## 五、总结

**Redis是Java后端开发必备技能，是高性能系统架构的核心组件。**

**学习要点**：
1. 掌握5种数据结构的使用场景
2. 理解Redis持久化机制
3. 熟练使用Spring Data Redis
4. 掌握分布式锁实现
5. 了解Redis集群和哨兵模式

---

*下一步：RabbitMQ消息队列*
