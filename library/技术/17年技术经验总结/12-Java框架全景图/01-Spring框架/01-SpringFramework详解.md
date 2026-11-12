# Spring Framework

> 模块：基础核心框架
> 更新时间：2026-03-29

---

## 一、框架介绍

Spring Framework是Java企业级开发最核心的框架，由Rod Johnson创建于2002年。它是所有Spring生态系统的基石，提供了**依赖注入（DI）**和**面向切面编程（AOP）**两大核心功能。

**官网**：[https://spring.io/projects/spring-framework](https://spring.io/projects/spring-framework)

**当前最新版本**：Spring Framework 6.x

*图：Spring Framework 核心组成与典型场景（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 260" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="260" y="24" width="200" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="52" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Spring Framework</text>
  <path d="M300,68 L300,88 L180,88 L180,108" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <path d="M420,68 L420,88 L540,88 L540,108" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="95" y="110" width="170" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="180" y="137" text-anchor="middle" font-size="14" fill="#1e293b">IoC 容器（依赖注入）</text>
  <rect x="455" y="110" width="170" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="540" y="137" text-anchor="middle" font-size="14" fill="#1e293b">AOP 面向切面编程</text>
  <path d="M360,68 L360,170" fill="none" stroke="#94a3b8" stroke-width="1.5"/>
  <path d="M150,170 L565,170" fill="none" stroke="#94a3b8" stroke-width="1.5"/>
  <path d="M150,170 L150,196" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <path d="M360,170 L360,196" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <path d="M565,170 L565,196" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="60" y="200" width="180" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="150" y="227" text-anchor="middle" font-size="13" fill="#1e293b">事务管理 @Transactional</text>
  <rect x="275" y="200" width="170" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="227" text-anchor="middle" font-size="13" fill="#1e293b">权限校验 AOP</text>
  <rect x="480" y="200" width="170" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="565" y="227" text-anchor="middle" font-size="13" fill="#1e293b">操作日志 AOP</text>
</svg>

---

## 二、核心特性

> IoC 是 Spring 的核心；AOP 将业务逻辑与通用功能分离，提高代码的模块化。

### 1. IoC容器（控制反转）

IoC（Inversion of Control）是Spring的核心，它将对象的创建和依赖管理从应用代码中转移到框架容器。

```java
// 传统方式：对象由程序员创建
public class UserService {
    private UserDao userDao = new UserDaoImpl(); // 硬耦合
}

// Spring方式：由容器管理依赖
public class UserService {
    private UserDao userDao;
    
    // 通过构造器注入
    public UserService(UserDao userDao) {
        this.userDao = userDao;
    }
}
```

**配置方式**：

```xml
<!-- applicationContext.xml -->
<bean id="userDao" class="com.example.dao.UserDaoImpl"/>
<bean id="userService" class="com.example.service.UserService">
    <constructor-arg ref="userDao"/>
</bean>
```

**注解方式（现代推荐）**：

```java
@Repository
public class UserDaoImpl implements UserDao {
    // DAO实现
}

@Service
public class UserServiceImpl implements UserService {
    
    @Autowired
    private UserDao userDao;
    
    // 或者构造器注入（推荐）
    private final UserDao userDao;
    
    @Autowired
    public UserServiceImpl(UserDao userDao) {
        this.userDao = userDao;
    }
}
```

### 2. AOP（面向切面编程）

AOP将业务逻辑与通用功能分离，提高代码的模块化。

**核心概念**：

- **切面（Aspect）**：横切关注点的模块化
- **连接点（Join Point）**：程序执行的某个点
- **通知（Advice）**：切面在连接点执行的动作
- **切入点（Pointcut）**：匹配连接点的表达式

**AOP使用场景**：

```java
@Aspect
@Component
public class LoggingAspect {
    
    // 前置通知
    @Before("execution(* com.example.service.*.*(..))")
    public void before(JoinPoint joinPoint) {
        String methodName = joinPoint.getSignature().getName();
        System.out.println("执行方法: " + methodName);
    }
    
    // 后置通知
    @AfterReturning(pointcut = "execution(* com.example.service.*.*(..))", 
                   returning = "result")
    public void afterReturning(JoinPoint joinPoint, Object result) {
        System.out.println("方法返回: " + result);
    }
    
    // 异常通知
    @AfterThrowing(pointcut = "execution(* com.example.service.*.*(..))", 
                   throwing = "e")
    public void afterThrowing(JoinPoint joinPoint, Exception e) {
        System.out.println("方法异常: " + e.getMessage());
    }
    
    // 环绕通知
    @Around("execution(* com.example.service.*.*(..))")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed();
        long end = System.currentTimeMillis();
        System.out.println("执行耗时: " + (end - start) + "ms");
        return result;
    }
}
```

---

## 三、实际业务应用场景

> 典型场景：事务管理、权限校验、操作日志。

### 场景1：事务管理

```java
@Service
public class OrderServiceImpl implements OrderService {
    
    @Autowired
    private OrderDao orderDao;
    
    @Autowired
    private AccountDao accountDao;
    
    @Transactional(rollbackFor = Exception.class)
    public void createOrder(Order order) {
        // 创建订单
        orderDao.insert(order);
        
        // 扣减账户余额
        accountDao.deduct(order.getUserId(), order.getAmount());
        
        // 如果这里抛出异常，整个事务会回滚
    }
}
```

**业务场景**：电商下单系统，用户下单和扣款必须在同一个事务中完成。

### 场景2：权限校验

```java
@Aspect
@Component
public class SecurityAspect {
    
    @Autowired
    private AuthService authService;
    
    @Around("@annotation(requirePermission)")
    public Object checkPermission(ProceedingJoinPoint joinPoint, 
                                 RequirePermission requirePermission) throws Throwable {
        String[] permissions = requirePermission.value();
        
        if (!authService.hasPermissions(permissions)) {
            throw new BizException("没有访问权限");
        }
        
        return joinPoint.proceed();
    }
}

// 使用
@RequirePermission("USER_VIEW")
public User getUser(Long id) {
    return userDao.selectById(id);
}
```

### 场景3：操作日志

```java
@Aspect
@Component
public class OperateLogAspect {
    
    @Autowired
    private OperateLogDao logDao;
    
    @AfterReturning(pointcut = "@annotation(operateLog)", returning = "result")
    public void saveLog(JoinPoint joinPoint, OperateLog operateLog, Object result) {
        OperateLogEntity log = new OperateLogEntity();
        log.setOperator(getCurrentUser());
        log.setModule(operateLog.module());
        log.setContent(operateLog.content());
        log.setCreateTime(new Date());
        
        logDao.insert(log);
    }
}

@OperateLog(module = "用户管理", content = "编辑用户")
public void updateUser(User user) {
    userService.updateById(user);
}
```

---

## 四、常见配置与最佳实践

> **Bean 作用域、条件注解、外部配置绑定——三件常用配置武器。**

### 1. Bean作用域

```java
// 默认：单例（整个容器中只有一个实例）
@Component
@Scope("singleton")
public class UserService {
}

// 每次获取新实例
@Component
@Scope("prototype")
public class UserService {
}

// HTTP请求（每个请求一个实例，仅Web应用）
@Component
@Scope("request")
public class UserService {
}

// HTTP会话（每个会话一个实例，仅Web应用）
@Component
@Scope("session")
public class UserService {
}
```

### 2. 条件注解

```java
@Configuration
public class AutoConfiguration {
    
    @Bean
    @ConditionalOnClass(RedisTemplate.class)
    @ConditionalOnProperty(prefix = "app.cache", name = "enabled", havingValue = "true")
    public CacheService cacheService() {
        return new RedisCacheService();
    }
}
```

### 3. 外部配置绑定

```java
@Component
@ConfigurationProperties(prefix = "app.user")
public class UserProperties {
    private String name;
    private Integer age;
    private List<String> roles;
}
```

```yaml
# application.yml
app:
  user:
    name: admin
    age: 18
    roles:
      - admin
      - user
```

---

## 五、版本选择建议

> **新项目直接上 Spring 6.x（JDK 17+）；存量主流项目留在 5.3.x。**

| 版本 | JDK要求 | 推荐场景 |
|------|--------|---------|
| Spring 6.x | JDK 17+ | 新项目、微服务 |
| Spring 5.3.x | JDK 8-17 | 主流项目 |
| Spring 4.x | JDK 6-8 | 遗留系统 |

---

## 六、总结与学习要点

> **Spring Framework 是 Java 开发的基础，掌握 IoC 和 AOP 核心概念对理解整个 Spring 生态至关重要。**

**学习要点**：

1. 理解IoC容器和Bean生命周期
2. 掌握依赖注入的多种方式
3. 熟练使用AOP进行日志、事务、权限管理
4. 了解Spring扩展机制（BeanFactoryPostProcessor等）

---

*下一步：Spring Boot*
