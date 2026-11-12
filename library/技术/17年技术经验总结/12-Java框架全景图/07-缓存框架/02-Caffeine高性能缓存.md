# Caffeine高性能缓存

> 模块：Java框架全景图 / 07-缓存框架
> 更新时间：2026-06-20

---

## 一、框架概述与核心特性

Caffeine是Java 8+的高性能本地缓存库，由Google Guava Cache的作者开发，性能比Guava Cache提升显著。

### 核心特性

- **高性能** — Window-TinyLFU淘汰算法，接近最优命中率
- **自动加载** — 支持异步刷新和自动加载
- **统计** — 内置缓存命中率统计
- **轻量** — 无外部依赖

---

## 二、基本使用

### 2.1 Maven依赖

```xml
<dependency>
    <groupId>com.github.ben-manes.caffeine</groupId>
    <artifactId>caffeine</artifactId>
    <version>3.1.8</version>
</dependency>
```

### 2.2 同步缓存

```java
Cache<String, User> cache = Caffeine.newBuilder()
    .maximumSize(10_000)                    // 最大10000条
    .expireAfterWrite(Duration.ofMinutes(5)) // 写入后5分钟过期
    .expireAfterAccess(Duration.ofMinutes(10)) // 访问后10分钟过期
    .recordStats()                          // 开启统计
    .build();

// 放入缓存
cache.put("user:1", new User("Alice", 25));

// 获取缓存，不存在时返回null
User user = cache.getIfPresent("user:1");

// 获取缓存，不存在时加载
User user = cache.get("user:1", key -> loadUserFromDB(key));

// 删除缓存
cache.invalidate("user:1");
```

### 2.3 异步缓存

```java
AsyncCache<String, User> asyncCache = Caffeine.newBuilder()
    .maximumSize(10_000)
    .expireAfterWrite(Duration.ofMinutes(5))
    .buildAsync();

// 异步获取
CompletableFuture<User> future = asyncCache.get("user:1", key -> loadUserFromDB(key));
```

---

## 三、Spring Cache集成

### 3.1 配置

```java
@Configuration
@EnableCaching
public class CacheConfig {
    
    @Bean
    public CacheManager cacheManager() {
        CaffeineCacheManager cacheManager = new CaffeineCacheManager();
        cacheManager.setCaffeine(Caffeine.newBuilder()
            .maximumSize(10_000)
            .expireAfterWrite(Duration.ofMinutes(5))
            .recordStats());
        return cacheManager;
    }
}
```

### 3.2 使用注解

```java
@Service
public class UserService {
    
    @Cacheable(value = "users", key = "#id")
    public User getUserById(Long id) {
        return userRepository.findById(id).orElse(null);
    }
    
    @CachePut(value = "users", key = "#user.id")
    public User updateUser(User user) {
        return userRepository.save(user);
    }
    
    @CacheEvict(value = "users", key = "#id")
    public void deleteUser(Long id) {
        userRepository.deleteById(id);
    }
}
```

---

## 四、高级特性

### 4.1 刷新策略

```java
Cache<String, User> cache = Caffeine.newBuilder()
    .maximumSize(10_000)
    .refreshAfterWrite(Duration.ofMinutes(1)) // 写入后1分钟刷新
    .build(key -> loadUserFromDB(key));        // 刷新时的加载器
```

### 4.2 引用类型

```java
// 软引用 - 内存不足时回收
Caffeine.newBuilder()
    .softValues()
    .build();

// 弱引用 - GC时回收
Caffeine.newBuilder()
    .weakValues()
    .build();
```

### 4.3 监听器

```java
Cache<String, User> cache = Caffeine.newBuilder()
    .maximumSize(10_000)
    .removalListener((key, value, cause) -> {
        log.info("Cache entry removed: key={}, cause={}", key, cause);
    })
    .build();
```

---

## 五、性能对比

| 操作 | Caffeine | Guava Cache | ConcurrentHashMap |
|------|----------|-------------|-------------------|
| 读 | 60ns | 100ns | 50ns |
| 写 | 80ns | 150ns | 60ns |
| 命中率 | 99% | 95% | N/A |

*图：Caffeine 与 Guava Cache、ConcurrentHashMap 读写延迟对比（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <text x="20" y="28" font-size="15" font-weight="bold" fill="#1e293b">读延迟（ns）</text>
  <text x="20" y="49" font-size="13" fill="#475569">Caffeine</text>
  <rect x="145" y="38" width="210" height="14" rx="3" fill="#16a34a"/>
  <text x="363" y="49" font-size="13" fill="#475569">60</text>
  <text x="20" y="73" font-size="13" fill="#475569">Guava Cache</text>
  <rect x="145" y="62" width="350" height="14" rx="3" fill="#94a3b8"/>
  <text x="503" y="73" font-size="13" fill="#475569">100</text>
  <text x="20" y="97" font-size="13" fill="#475569">ConcurrentHashMap</text>
  <rect x="145" y="86" width="175" height="14" rx="3" fill="#2563eb"/>
  <text x="328" y="97" font-size="13" fill="#475569">50</text>
  <text x="20" y="126" font-size="15" font-weight="bold" fill="#1e293b">写延迟（ns）</text>
  <text x="20" y="147" font-size="13" fill="#475569">Caffeine</text>
  <rect x="145" y="136" width="280" height="14" rx="3" fill="#16a34a"/>
  <text x="433" y="147" font-size="13" fill="#475569">80</text>
  <text x="20" y="171" font-size="13" fill="#475569">Guava Cache</text>
  <rect x="145" y="160" width="525" height="14" rx="3" fill="#94a3b8"/>
  <text x="678" y="171" font-size="13" fill="#475569">150</text>
  <text x="20" y="195" font-size="13" fill="#475569">ConcurrentHashMap</text>
  <rect x="145" y="184" width="210" height="14" rx="3" fill="#2563eb"/>
  <text x="363" y="195" font-size="13" fill="#475569">60</text>
  <text x="360" y="226" text-anchor="middle" font-size="13" fill="#475569">命中率：Caffeine 99%、Guava Cache 95%、ConcurrentHashMap N/A</text>
</svg>

---

## 六、最佳实践

1. **设置合理的maximumSize** — 根据内存和访问模式设置
2. **使用refreshAfterWrite** — 避免缓存失效时的延迟
3. **开启recordStats** — 监控缓存命中率
4. **避免缓存大对象** — 考虑使用软引用或分布式缓存

---

## 七、与Ehcache对比

| 特性 | Caffeine | Ehcache |
|------|----------|---------|
| 性能 | 更高 | 高 |
| 内存占用 | 更低 | 较高 |
| 磁盘存储 | 不支持 | 支持 |
| 分布式 | 不支持 | 支持 |
| 使用场景 | 纯内存缓存 | 多级缓存 |

---

*纯内存缓存场景推荐Caffeine，需要磁盘或分布式缓存选Ehcache。*
