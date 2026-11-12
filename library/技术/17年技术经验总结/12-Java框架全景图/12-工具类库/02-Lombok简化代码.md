# Lombok

> 模块：工具类库
> 更新时间：2026-03-29

---

## 一、Lombok 是什么

**Lombok是一个Java库，通过注解自动生成样板代码（getter、setter、构造函数等）**，显著减少代码冗余。

**官网**：[https://projectlombok.org](https://projectlombok.org)

**核心注解**：
- @Getter/@Setter - 生成getter/setter
- @ToString - 生成toString
- @EqualsAndHashCode - 生成equals和hashCode
- @Data - 组合注解
- @NoArgsConstructor/@AllArgsConstructor - 构造函数
- @Builder - 建造者模式
- @Slf4j - 日志对象

*图：Lombok 常用注解与生成内容对照（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 290" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <rect x="140" y="20" width="250" height="28" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="265" y="39" text-anchor="middle" font-size="13" fill="#1e293b">@Getter / @Setter</text>
  <text x="420" y="39" text-anchor="start" font-size="13" fill="#475569">生成getter/setter</text>
  <rect x="140" y="54" width="250" height="28" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="265" y="73" text-anchor="middle" font-size="13" fill="#1e293b">@ToString</text>
  <text x="420" y="73" text-anchor="start" font-size="13" fill="#475569">生成toString</text>
  <rect x="140" y="88" width="250" height="28" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="265" y="107" text-anchor="middle" font-size="13" fill="#1e293b">@EqualsAndHashCode</text>
  <text x="420" y="107" text-anchor="start" font-size="13" fill="#475569">生成equals和hashCode</text>
  <rect x="140" y="122" width="250" height="28" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="265" y="141" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">@Data</text>
  <text x="420" y="141" text-anchor="start" font-size="13" fill="#475569">组合注解</text>
  <rect x="140" y="156" width="250" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="265" y="174" text-anchor="middle" font-size="13" fill="#1e293b">@NoArgsConstructor</text>
  <text x="265" y="191" text-anchor="middle" font-size="13" fill="#1e293b">@AllArgsConstructor</text>
  <text x="420" y="183" text-anchor="start" font-size="13" fill="#475569">构造函数</text>
  <rect x="140" y="208" width="250" height="28" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="265" y="227" text-anchor="middle" font-size="13" fill="#1e293b">@Builder</text>
  <text x="420" y="227" text-anchor="start" font-size="13" fill="#475569">建造者模式</text>
  <rect x="140" y="242" width="250" height="28" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="265" y="261" text-anchor="middle" font-size="13" fill="#1e293b">@Slf4j</text>
  <text x="420" y="261" text-anchor="start" font-size="13" fill="#475569">日志对象</text>
</svg>

---

## 二、常用注解

```java
// 1. @Data - 最常用
@Data
@Entity
@TableName("t_user")
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, length = 50)
    private String name;
    
    private Integer age;
    
    private String email;
    
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}

// 2. @Builder - 建造者模式
@Data
@Builder
public class CreateOrderRequest {
    private Long userId;
    private Long productId;
    private Integer quantity;
}

// 使用
CreateOrderRequest request = CreateOrderRequest.builder()
    .userId(1L)
    .productId(100L)
    .quantity(2)
    .build();

// 3. @Slf4j - 日志
@Slf4j
@Service
public class UserServiceImpl implements UserService {
    
    public void createUser(User user) {
        log.info("创建用户: {}", user.getName());
        // 业务逻辑
    }
}

// 4. @RequiredArgsConstructor - 构造器注入
@Service
@RequiredArgsConstructor
public class OrderService {
    
    private final UserService userService;
    private final ProductService productService;
    private final OrderMapper orderMapper;
    
    // 自动生成包含final字段的构造器
}

// 5. @NonNull - 空指针检查
@Data
public class User {
    @NonNull
    private String name;
    
    private String email;
}
```

---

## 三、IDE支持

需要在IDE中安装Lombok插件：
- IntelliJ IDEA：Marketplace搜索Lombok
- Eclipse：下载lombok.jar运行安装

---

## 四、总结与使用注意

**Lombok是提高开发效率的必备工具，让代码更简洁。**

**使用注意**：
1. IDE需要安装对应插件
2. 避免与手写方法冲突
3. @Data用于DTO/Entity，@Value用于不可变对象

---

*下一步：MySQL数据库*
