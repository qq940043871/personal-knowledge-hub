# Spring WebFlux响应式编程

> 模块：Java框架全景图 / 02-Web开发
> 更新时间：2026-06-20

---

## 一、概述：基于 Reactor 的响应式 Web 框架

Spring WebFlux是**Spring 5引入的响应式Web框架**，基于Reactor库实现非阻塞IO，适合高并发、低延迟的场景。

### 核心特性

- **非阻塞IO** — 基于Netty，少量线程处理大量并发连接
- **响应式流** — 支持背压（Backpressure）机制
- **函数式端点** — RouterFunction定义路由
- **SSE支持** — 服务器推送事件

---

## 二、核心概念

> **Mono 是 0 或 1 个元素，Flux 是 0 到 N 个元素。**

### 2.1 Mono与Flux

```java
// Mono: 0或1个元素
Mono<String> mono = Mono.just("Hello");

// Flux: 0到N个元素
Flux<Integer> flux = Flux.just(1, 2, 3, 4, 5);

// 异步创建
Mono<String> asyncMono = Mono.fromCallable(() -> {
    // 耗时操作
    return "result";
});
```

*图：Mono 与 Flux 响应式流（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 170" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <text x="20" y="47" font-size="14" font-weight="bold" fill="#1e293b">Mono：0 或 1 个元素</text>
  <rect x="230" y="24" width="60" height="36" rx="18" fill="#ffffff" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 3"/>
  <text x="260" y="47" text-anchor="middle" font-size="13" fill="#475569">空</text>
  <rect x="310" y="24" width="70" height="36" rx="18" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="345" y="47" text-anchor="middle" font-size="13" fill="#1e293b">元素</text>
  <line x1="382" y1="42" x2="426" y2="42" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="430" y="24" width="110" height="36" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="485" y="47" text-anchor="middle" font-size="13" fill="#1e293b">订阅者</text>
  <text x="20" y="127" font-size="14" font-weight="bold" fill="#1e293b">Flux：0 到 N 个元素</text>
  <rect x="170" y="104" width="50" height="36" rx="18" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="195" y="127" text-anchor="middle" font-size="13" fill="#1e293b">1</text>
  <rect x="234" y="104" width="50" height="36" rx="18" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="259" y="127" text-anchor="middle" font-size="13" fill="#1e293b">2</text>
  <rect x="298" y="104" width="50" height="36" rx="18" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="323" y="127" text-anchor="middle" font-size="13" fill="#1e293b">3</text>
  <rect x="362" y="104" width="50" height="36" rx="18" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="387" y="127" text-anchor="middle" font-size="13" fill="#1e293b">4</text>
  <rect x="426" y="104" width="50" height="36" rx="18" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="451" y="127" text-anchor="middle" font-size="13" fill="#1e293b">5</text>
  <line x1="478" y1="122" x2="516" y2="122" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="520" y="104" width="110" height="36" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="575" y="127" text-anchor="middle" font-size="13" fill="#1e293b">订阅者</text>
</svg>

### 2.2 操作符

```java
Flux.just(1, 2, 3, 4, 5)
    .filter(i -> i > 2)           // 过滤
    .map(i -> i * 10)             // 映射
    .flatMap(i -> Mono.just(i))   // 扁平化
    .collectList()                // 收集为List
    .subscribe();                 // 订阅
```

---

## 三、注解方式

```java
@RestController
@RequestMapping("/api/users")
public class UserWebFluxController {
    
    @Autowired
    private ReactiveUserRepository userRepository;
    
    @GetMapping("/{id}")
    public Mono<User> getUser(@PathVariable Long id) {
        return userRepository.findById(id);
    }
    
    @GetMapping
    public Flux<User> listUsers() {
        return userRepository.findAll();
    }
    
    @PostMapping
    public Mono<User> createUser(@RequestBody User user) {
        return userRepository.save(user);
    }
    
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<UserEvent> streamUsers() {
        return userRepository.findAll()
                .map(user -> new UserEvent(user))
                .delayElements(Duration.ofSeconds(1));
    }
}
```

---

## 四、函数式端点

> RouterFunction 定义路由，Handler 处理请求——函数式端点的两个角色。

```java
@Configuration
public class RouterConfig {
    
    @Bean
    public RouterFunction<ServerResponse> routes(UserHandler handler) {
        return RouterFunctions.route()
                .GET("/api/users", handler::listUsers)
                .GET("/api/users/{id}", handler::getUser)
                .POST("/api/users", handler::createUser)
                .build();
    }
}

@Component
public class UserHandler {
    
    public Mono<ServerResponse> listUsers(ServerRequest request) {
        Flux<User> users = userRepository.findAll();
        return ServerResponse.ok().body(users, User.class);
    }
    
    public Mono<ServerResponse> getUser(ServerRequest request) {
        Long id = Long.valueOf(request.pathVariable("id"));
        Mono<User> user = userRepository.findById(id);
        return ServerResponse.ok().body(user, User.class);
    }
}
```

---

## 五、WebClient

> WebClient 是 WebFlux 的响应式 HTTP 客户端，支持 Mono/Flux 返回值。

```java
@Service
public class ExternalApiService {
    
    private final WebClient webClient = WebClient.builder()
            .baseUrl("https://api.example.com")
            .build();
    
    public Mono<User> getUser(Long id) {
        return webClient.get()
                .uri("/users/{id}", id)
                .retrieve()
                .bodyToMono(User.class);
    }
    
    public Flux<User> listUsers() {
        return webClient.get()
                .uri("/users")
                .retrieve()
                .bodyToFlux(User.class);
    }
}
```

---

## 六、适用场景

| 场景 | 是否适合WebFlux |
|------|----------------|
| 高并发API服务 | ✅ 适合 |
| 实时数据推送（SSE） | ✅ 适合 |
| 微服务网关 | ✅ 适合 |
| 传统CRUD应用 | ❌ 不适合 |
| 阻塞IO操作多 | ❌ 不适合 |

---

## 七、与Spring MVC对比

| 特性 | Spring MVC | Spring WebFlux |
|------|-----------|----------------|
| 线程模型 | 每请求一线程 | 少量线程+事件循环 |
| IO模型 | 阻塞IO | 非阻塞IO |
| 并发能力 | 受线程数限制 | 可处理大量并发 |
| 学习曲线 | 低 | 高 |
| 生态支持 | 成熟 | 逐渐完善 |

---

*WebFlux适合高并发场景，传统应用建议使用Spring MVC。*
