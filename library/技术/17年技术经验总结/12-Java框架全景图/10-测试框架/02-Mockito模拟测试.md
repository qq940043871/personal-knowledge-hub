# Mockito模拟测试

> 模块：Java框架全景图 / 10-测试框架
> 更新时间：2026-06-20

---

## 一、Mockito 是什么

**Mockito是Java领域最流行的Mock框架**，用于模拟依赖对象的行为，实现**单元测试的隔离**。

### 核心特性

- **简洁API** — 链式调用，易于使用
- **注解支持** — `@Mock`、`@InjectMocks`、`@Spy`
- **验证机制** — 验证方法调用次数和参数
- **行为定义** — `when...thenReturn`、`doThrow`

*图：Mockito 单元测试工作流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 160" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="55" width="150" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="76" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">创建 Mock 对象</text>
  <text x="95" y="94" text-anchor="middle" font-size="12" fill="#475569">@Mock、mock()</text>
  <line x1="170" y1="80" x2="208" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="210" y="55" width="150" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="285" y="76" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">定义行为</text>
  <text x="285" y="94" text-anchor="middle" font-size="12" fill="#475569">when...thenReturn</text>
  <line x1="360" y1="80" x2="398" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="400" y="55" width="150" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="475" y="76" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">执行测试</text>
  <text x="475" y="94" text-anchor="middle" font-size="12" fill="#475569">调用被测方法</text>
  <line x1="550" y1="80" x2="588" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="590" y="55" width="110" height="50" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="645" y="76" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">验证调用</text>
  <text x="645" y="94" text-anchor="middle" font-size="12" fill="#475569">verify() / times()</text>
</svg>

---

## 二、基本使用

### 2.1 Maven依赖

```xml
<dependency>
    <groupId>org.mockito</groupId>
    <artifactId>mockito-core</artifactId>
    <version>5.8.0</version>
    <scope>test</scope>
</dependency>
```

### 2.2 创建Mock对象

```java
// 方式1：注解
@Mock
private UserRepository userRepository;

@InjectMocks
private UserService userService;

@BeforeEach
void setUp() {
    MockitoAnnotations.openMocks(this);
}

// 方式2：静态方法
UserRepository userRepository = mock(UserRepository.class);

// 方式3：@ExtendWith
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository userRepository;
    
    @InjectMocks
    private UserService userService;
}
```

---

## 三、行为定义

```java
// 基本用法
when(userRepository.findById(1L))
    .thenReturn(Optional.of(new User("Alice", 25)));

// 链式调用
when(userRepository.findById(any()))
    .thenReturn(Optional.empty());

// 抛出异常
when(userRepository.findById(1L))
    .thenThrow(new RuntimeException("Database error"));

// 多次调用不同返回
when(userRepository.findById(1L))
    .thenReturn(Optional.of(new User("Alice", 25)))
    .thenReturn(Optional.empty());

// void方法
doThrow(new RuntimeException("error"))
    .when(userRepository).deleteById(1L);

// 调用真实方法
when(userRepository.findById(1L))
    .thenCallRealMethod();
```

---

## 四、参数匹配

```java
// 任意参数
when(userRepository.findById(any())).thenReturn(Optional.empty());

// 特定类型
when(userRepository.save(any(User.class))).thenReturn(new User());

// 空值
when(userRepository.findById(isNull())).thenReturn(Optional.empty());

// 自定义匹配
when(userRepository.findByName(argThat(name -> name.startsWith("A"))))
    .thenReturn(Arrays.asList(new User("Alice"), new User("Amy")));
```

---

## 五、验证调用

```java
// 验证方法调用
verify(userRepository).findById(1L);

// 验证调用次数
verify(userRepository, times(2)).findById(1L);
verify(userRepository, never()).deleteById(1L);
verify(userRepository, atLeastOnce()).save(any());

// 验证调用顺序
InOrder inOrder = inOrder(userRepository);
inOrder.verify(userRepository).findById(1L);
inOrder.verify(userRepository).save(any());

// 验证没有更多交互
verifyNoMoreInteractions(userRepository);
```

---

## 六、Spy对象

```java
// Spy - 部分模拟
@Spy
private UserService userService;

// 部分mock
doReturn(Optional.of(new User("Alice")))
    .when(userService).getById(1L);

// 调用真实方法
userService.processUser(1L); // 调用真实实现
```

---

## 七、Spring Boot集成

```java
@SpringBootTest
class UserServiceTest {
    
    @MockBean
    private UserRepository userRepository;
    
    @Autowired
    private UserService userService;
    
    @Test
    void testGetUser() {
        when(userRepository.findById(1L))
            .thenReturn(Optional.of(new User("Alice", 25)));
        
        User user = userService.getById(1L);
        assertEquals("Alice", user.getName());
        verify(userRepository).findById(1L);
    }
}
```

---

## 八、最佳实践

1. **只Mock依赖** — 不Mock被测试的类
2. **验证关键交互** — 验证重要的方法调用
3. **避免过度Mock** — 保持测试的可读性
4. **使用@MockBean** — Spring Boot测试中使用
5. **清理资源** — 使用`Mockito.framework().clearInlineMocks()`

---

## 九、与JUnit 5集成

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    
    @Mock
    private UserRepository userRepository;
    
    @InjectMocks
    private UserService userService;
    
    @Test
    void testGetUser() {
        when(userRepository.findById(1L))
            .thenReturn(Optional.of(new User("Alice")));
        
        User user = userService.getById(1L);
        assertNotNull(user);
    }
}
```

---

*Mockito是单元测试隔离依赖的标准工具。*
