# Spring Cloud - 架构师学习笔记

Spring Cloud为开发者提供了在分布式系统（如配置管理、服务发现、断路器、智能路由、微代理、控制总线、一次性令牌、全局锁、领导选举、分布式会话、集群状态）操作的开发工具。使用**Spring Boot开发风格**，使分布式系统中的协调变得更容易。

## Spring Cloud核心组件

| 组件 | 功能 | 实现方案 |
|------|------|----------|
| 服务注册与发现 | 服务实例的自动注册和发现 | Eureka, Consul, Nacos |
| 客户端负载均衡 | 在客户端实现负载均衡算法 | Ribbon, Spring Cloud LoadBalancer |
| 服务调用 | 简化服务间的调用 | OpenFeign |
| 熔断器 | 提供服务降级和熔断机制 | Hystrix, Resilience4j |
| API网关 | 统一服务入口，提供路由、过滤等功能 | Zuul, Spring Cloud Gateway |
| 配置管理 | 集中管理分布式系统的配置 | Spring Cloud Config, Nacos |
| 消息总线 | 用于传播集群状态变化 | Spring Cloud Bus |
| 安全控制 | 提供安全控制和认证授权 | Spring Cloud Security |

*图：Spring Cloud 核心组件分层（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="60" y="24" width="600" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="42" text-anchor="middle" font-size="14" fill="#1e293b">API网关：统一服务入口</text>
  <text x="360" y="60" text-anchor="middle" font-size="12" fill="#475569">Zuul / Spring Cloud Gateway</text>
  <line x1="360" y1="68" x2="360" y2="96" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="30" y="98" width="210" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="135" y="116" text-anchor="middle" font-size="14" fill="#1e293b">客户端负载均衡</text>
  <text x="135" y="134" text-anchor="middle" font-size="12" fill="#475569">Ribbon / LoadBalancer</text>
  <rect x="255" y="98" width="210" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="116" text-anchor="middle" font-size="14" fill="#1e293b">服务调用</text>
  <text x="360" y="134" text-anchor="middle" font-size="12" fill="#475569">OpenFeign</text>
  <rect x="480" y="98" width="210" height="44" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="585" y="116" text-anchor="middle" font-size="14" fill="#1e293b">熔断器（降级）</text>
  <text x="585" y="134" text-anchor="middle" font-size="12" fill="#475569">Hystrix / Resilience4j</text>
  <line x1="360" y1="142" x2="360" y2="170" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="60" y="172" width="300" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="210" y="190" text-anchor="middle" font-size="14" fill="#1e293b">服务注册与发现</text>
  <text x="210" y="208" text-anchor="middle" font-size="12" fill="#475569">Eureka · Consul · Nacos</text>
  <rect x="360" y="172" width="300" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="510" y="190" text-anchor="middle" font-size="14" fill="#1e293b">配置管理</text>
  <text x="510" y="208" text-anchor="middle" font-size="12" fill="#475569">Spring Cloud Config · Nacos</text>
</svg>

## 服务注册与发现

### Eureka

Netflix开源的服务发现组件，是Spring Cloud Netflix的核心组件之一。

```java
// Eureka Server配置
@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}

// Eureka Client配置
@SpringBootApplication
@EnableEurekaClient
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
```

### Nacos

Alibaba开源的动态服务发现、配置管理和服务管理平台。

```java
// Nacos配置
@SpringBootApplication
@EnableDiscoveryClient
public class OrderServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }
}
```

## 服务调用

### OpenFeign

**声明式的Web服务客户端**，使得编写Web服务客户端变得更加简单。

```java
// 定义Feign客户端
@FeignClient(name = "user-service")
public interface UserServiceClient {
    
    @GetMapping("/users/{id}")
    User getUserById(@PathVariable("id") Long id);
    
    @PostMapping("/users")
    User createUser(@RequestBody User user);
}

// 使用Feign客户端
@RestController
public class OrderController {
    
    @Autowired
    private UserServiceClient userServiceClient;
    
    @GetMapping("/orders/{id}")
    public Order getOrder(@PathVariable("id") Long id) {
        // 调用用户服务
        User user = userServiceClient.getUserById(1L);
        // 处理订单逻辑
        return orderService.getOrder(id);
    }
}
```

## 熔断器

### Hystrix

Netflix开源的容错库，通过添加**延迟容忍和容错逻辑**来帮助控制分布式服务之间的交互。

```java
// 使用HystrixCommand注解
@RestController
public class UserController {
    
    @HystrixCommand(fallbackMethod = "getUserFallback")
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable("id") Long id) {
        // 调用用户服务
        return userService.getUserById(id);
    }
    
    // 降级方法
    public User getUserFallback(Long id) {
        return new User(id, "默认用户", "default@example.com");
    }
}
```

### Resilience4j

**轻量级的容错库**，专为Java 8和函数式编程设计。

```java
// 使用Resilience4j注解
@RestController
public class ProductController {
    
    @Retry(name = "product-service")
    @CircuitBreaker(name = "product-service", fallbackMethod = "getProductFallback")
    @GetMapping("/products/{id}")
    public Product getProduct(@PathVariable("id") Long id) {
        return productService.getProductById(id);
    }
    
    public Product getProductFallback(Long id, Exception ex) {
        return new Product(id, "默认产品", 0.0);
    }
}
```

## API网关

### Spring Cloud Gateway

基于Spring Framework 5、Project Reactor和Spring Boot 2.0构建的API网关。

```java
// Gateway配置
@Configuration
public class GatewayConfig {
    
    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("user-service", r -> r.path("/users/**")
                .uri("lb://user-service"))
            .route("order-service", r -> r.path("/orders/**")
                .uri("lb://order-service"))
            .build();
    }
}
```

```yaml
// application.yml配置
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/users/**
          filters:
            - StripPrefix=1
```

## 配置管理

### Spring Cloud Config

为分布式系统中的**外部化配置**提供服务器端和客户端支持。

```java
// Config Server配置
@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }
}

// Config Client配置
@RestController
@RefreshScope
public class ConfigController {
    
    @Value("${config.info}")
    private String configInfo;
    
    @GetMapping("/config")
    public String getConfigInfo() {
        return configInfo;
    }
}
```

```yaml
// bootstrap.yml配置
spring:
  application:
    name: user-service
  cloud:
    config:
      uri: http://localhost:8888
      profile: dev
```

## Spring Cloud最佳实践

- 合理选择Spring Cloud版本，注意**组件间的兼容性**
- 使用**Spring Cloud Alibaba**替代部分Netflix组件，提高稳定性
- 实施**健康检查和心跳机制**，确保服务可用性
- 配置合理的**超时时间和重试机制**
- 建立完善的**监控体系**，使用Spring Boot Admin等工具
- 实施**蓝绿部署和金丝雀发布**，降低发布风险
- 使用**分布式链路追踪**工具（如Sleuth + Zipkin）定位问题
