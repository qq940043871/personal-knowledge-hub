# JUnit 5单元测试

> 模块：Java框架全景图 / 10-测试框架
> 更新时间：2026-06-20

---

## 一、JUnit 5 是什么

**JUnit 5是Java领域最主流的单元测试框架**，由JUnit Platform、JUnit Jupiter、JUnit Vintage三部分组成。

### 核心特性

- **注解驱动** — `@Test`、`@BeforeEach`、`@AfterEach`等
- **断言增强** — 支持lambda表达式和消息Supplier
- **参数化测试** — `@ParameterizedTest`
- **嵌套测试** — `@Nested`
- **扩展模型** — `@ExtendWith`

---

## 二、基本使用

### 2.1 Maven依赖

```xml
<dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <version>5.10.1</version>
    <scope>test</scope>
</dependency>
```

### 2.2 基本测试

```java
class CalculatorTest {
    
    private Calculator calculator;
    
    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }
    
    @Test
    void testAdd() {
        int result = calculator.add(2, 3);
        assertEquals(5, result);
    }
    
    @Test
    void testDivide() {
        assertThrows(ArithmeticException.class, () -> {
            calculator.divide(1, 0);
        });
    }
    
    @AfterEach
    void tearDown() {
        // 清理资源
    }
}
```

---

## 三、核心注解

| 注解 | 说明 |
|------|------|
| `@Test` | 标记测试方法 |
| `@BeforeEach` | 每个测试方法前执行 |
| `@AfterEach` | 每个测试方法后执行 |
| `@BeforeAll` | 所有测试前执行（静态方法） |
| `@AfterAll` | 所有测试后执行（静态方法） |
| `@Disabled` | 禁用测试 |
| `@DisplayName` | 自定义显示名称 |
| `@Tag` | 测试标签 |
| `@Timeout` | 超时设置 |

*图：JUnit 5 核心注解执行顺序（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 160" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="55" width="120" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="80" y="76" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">@BeforeAll</text>
  <text x="80" y="94" text-anchor="middle" font-size="12" fill="#475569">所有测试前执行</text>
  <line x1="140" y1="80" x2="168" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="170" y="55" width="120" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="230" y="76" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">@BeforeEach</text>
  <text x="230" y="94" text-anchor="middle" font-size="12" fill="#475569">每个测试方法前执行</text>
  <line x1="290" y1="80" x2="318" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="320" y="55" width="120" height="50" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="380" y="76" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">@Test</text>
  <text x="380" y="94" text-anchor="middle" font-size="12" fill="#475569">标记测试方法</text>
  <line x1="440" y1="80" x2="468" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="470" y="55" width="120" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="530" y="76" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">@AfterEach</text>
  <text x="530" y="94" text-anchor="middle" font-size="12" fill="#475569">每个测试方法后执行</text>
  <line x1="590" y1="80" x2="618" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="620" y="55" width="80" height="50" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="660" y="76" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">@AfterAll</text>
  <text x="660" y="94" text-anchor="middle" font-size="12" fill="#475569">所有测试后执行</text>
</svg>

---

## 四、断言

```java
// 基本断言
assertEquals(5, result);
assertTrue(result > 0);
assertNotNull(user);
assertNull(result);

// 带消息的断言
assertEquals(5, result, "计算结果应为5");
assertEquals(5, result, () -> "计算结果应为5，实际为" + result);

// 批量断言
assertAll("user",
    () -> assertEquals("Alice", user.getName()),
    () -> assertEquals(25, user.getAge()),
    () -> assertNotNull(user.getEmail())
);

// 异常断言
ArithmeticException exception = assertThrows(
    ArithmeticException.class,
    () -> calculator.divide(1, 0)
);
assertEquals("/ by zero", exception.getMessage());
```

---

## 五、参数化测试

```java
@ParameterizedTest
@ValueSource(ints = {1, 2, 3, 4, 5})
void testPositive(int number) {
    assertTrue(number > 0);
}

@ParameterizedTest
@CsvSource({
    "1, 1, 2",
    "2, 3, 5",
    "3, 4, 7"
})
void testAdd(int a, int b, int expected) {
    assertEquals(expected, calculator.add(a, b));
}

@ParameterizedTest
@MethodSource("provideNumbers")
void testWithMethodSource(int number) {
    assertTrue(number > 0);
}

static Stream<Integer> provideNumbers() {
    return Stream.of(1, 2, 3, 4, 5);
}
```

---

## 六、嵌套测试

```java
class UserServiceTest {
    
    private UserService userService;
    
    @BeforeEach
    void setUp() {
        userService = new UserService();
    }
    
    @Nested
    class WhenUserExists {
        
        @Test
        void shouldReturnUser() {
            User user = userService.getById(1L);
            assertNotNull(user);
        }
    }
    
    @Nested
    class WhenUserNotExists {
        
        @Test
        void shouldReturnNull() {
            User user = userService.getById(999L);
            assertNull(user);
        }
    }
}
```

---

## 七、Spring Boot测试

```java
@SpringBootTest
class UserServiceIntegrationTest {
    
    @Autowired
    private UserService userService;
    
    @MockBean
    private UserRepository userRepository;
    
    @Test
    void testGetUser() {
        when(userRepository.findById(1L))
            .thenReturn(Optional.of(new User("Alice", 25)));
        
        User user = userService.getById(1L);
        assertEquals("Alice", user.getName());
    }
}
```

---

## 八、最佳实践

1. **测试命名** — 使用`@DisplayName`描述测试意图
2. **单一职责** — 每个测试方法只测一个场景
3. **独立性** — 测试之间不应有依赖
4. **快速执行** — 单元测试应快速执行
5. **覆盖率** — 关注核心业务逻辑的测试覆盖

---

*JUnit 5是Java单元测试的标准，建议结合Mockito使用。*
