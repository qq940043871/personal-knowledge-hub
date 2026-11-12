# JIT编译原理

> 模块：手写JVM / 09-JIT编译器
> 更新时间：2026-06-20

---

## 一、JIT概述

**JIT（Just-In-Time）编译器将热点字节码编译为本地机器码**，提升执行效率。

### 1.1 执行模式

```
字节码 → 解释执行 → 热点检测 → JIT编译 → 机器码执行
```

### 1.2 热点检测

```cpp
// 方法调用计数器
class Method {
    int invocation_count;
    int back_edge_count;
    
    bool is_hot() {
        return invocation_count > threshold ||
               back_edge_count > back_edge_threshold;
    }
};
```

---

## 二、编译器类型

> C1 编译速度快、优化程度低，适合客户端；C2 编译速度慢、优化程度高，适合服务器；**分层编译**兼顾两者。

### 2.1 C1编译器（Client Compiler）

- 编译速度快
- 优化程度低
- 适合客户端应用

### 2.2 C2编译器（Server Compiler）

- 编译速度慢
- 优化程度高
- 适合服务器应用

### 2.3 分层编译

```
Level 0: 解释执行
Level 1: C1编译，无性能监控
Level 2: C1编译，有限性能监控
Level 3: C1编译，完整性能监控
Level 4: C2编译
```

---

## 三、编译优化

> 四类基础优化：**方法内联**、**逃逸分析（标量替换）**、循环展开、死代码消除。

### 3.1 方法内联

```java
// 优化前
public int add(int a, int b) {
    return a + b;
}
public int calculate() {
    return add(1, 2);
}

// 优化后
public int calculate() {
    return 1 + 2; // 内联
}
```

### 3.2 逃逸分析

```java
// 对象不逃逸方法，可栈上分配
public void method() {
    Point p = new Point(1, 2); // 不逃逸
    System.out.println(p.x + p.y);
}

// 优化为
public void method() {
    int x = 1, y = 2; // 标量替换
    System.out.println(x + y);
}
```

### 3.3 循环优化

```java
// 循环展开
for (int i = 0; i < 100; i++) {
    sum += i;
}

// 优化为
for (int i = 0; i < 100; i += 4) {
    sum += i;
    sum += i + 1;
    sum += i + 2;
    sum += i + 3;
}
```

### 3.4 死代码消除

```java
// 优化前
int x = 10;
int y = 20;
int z = x + y; // z未使用

// 优化后
// z被消除
```

---

## 四、编译触发条件

> 方法调用计数达到阈值（Client 1500 / Server 10000）或回边计数达到 10700 时触发编译。

### 4.1 方法调用计数

```cpp
// Client模式
int threshold = 1500;

// Server模式
int threshold = 10000;
```

### 4.2 回边计数

```cpp
// 循环回边次数
int back_edge_threshold = 10700;
```

### 4.3 配置参数

```bash
# 设置编译阈值
-XX:CompileThreshold=10000

# 设置回边阈值
-XX:OnStackReplacePercentage=140

# 设置编译线程数
-XX:CICompilerCount=4
```

---

## 五、逆优化

> 乐观假设失效时触发**去优化（Deoptimization）**：恢复解释执行状态 → 重建栈帧 → 回到解释执行。

### 5.1 逆优化场景

- 类型假设失败
- 去优化（Deoptimization）
- 重编译

### 5.2 逆优化过程

```cpp
void deoptimize(Method* method) {
    // 1. 恢复解释执行状态
    method->set_not_compiled();
    
    // 2. 重建栈帧
    rebuild_stack_frame();
    
    // 3. 继续解释执行
    interpret(method);
}
```

*图：JIT 编译与逆优化的状态流转（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="30" y="60" width="160" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="110" y="81" text-anchor="middle" font-size="14" fill="#1e293b">解释执行</text>
  <text x="110" y="100" text-anchor="middle" font-size="12" fill="#475569">调用/回边计数器累积</text>
  <line x1="190" y1="86" x2="255" y2="86" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="222" y="76" text-anchor="middle" font-size="12" fill="#475569">超过阈值</text>
  <rect x="260" y="60" width="180" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="350" y="81" text-anchor="middle" font-size="14" fill="#1e293b">JIT 编译</text>
  <text x="350" y="100" text-anchor="middle" font-size="12" fill="#475569">C1 / C2，内联等优化</text>
  <line x1="440" y1="86" x2="505" y2="86" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="510" y="60" width="170" height="52" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="595" y="81" text-anchor="middle" font-size="14" fill="#1e293b">机器码执行</text>
  <text x="595" y="100" text-anchor="middle" font-size="12" fill="#475569">峰值性能高</text>
  <line x1="595" y1="112" x2="595" y2="158" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="607" y="140" text-anchor="start" font-size="12" fill="#475569">类型假设失效</text>
  <rect x="510" y="163" width="170" height="52" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="595" y="184" text-anchor="middle" font-size="14" fill="#1e293b">逆优化</text>
  <text x="595" y="203" text-anchor="middle" font-size="12" fill="#475569">Deoptimization</text>
  <path d="M510,189 H110 V117" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="310" y="180" text-anchor="middle" font-size="12" fill="#475569">重建栈帧，回到解释执行</text>
</svg>

---

## 六、编译日志

### 6.1 开启编译日志

```bash
-XX:+PrintCompilation
-XX:+UnlockDiagnosticVMOptions
-XX:+PrintInlining
```

### 6.2 日志解读

```
  78   1       3       java.lang.String::hashCode (55 bytes)
  78   2       4       java.lang.String::hashCode (55 bytes)
```

- `78` — 时间戳
- `1` — 编译ID
- `3` — 编译层级
- `java.lang.String::hashCode` — 编译的方法
- `(55 bytes)` — 字节码大小

---

## 七、最佳实践

1. **合理设置编译阈值** — 根据应用特点设置
2. **开启编译日志** — 监控编译情况
3. **避免频繁逆优化** — 保持类型稳定
4. **使用分层编译** — 平衡启动速度和峰值性能
5. **监控编译线程** — 避免编译线程不足

---

## 八、与AOT对比

| 特性 | JIT | AOT |
|------|-----|-----|
| 编译时机 | 运行时 | 编译时 |
| 启动速度 | 慢 | 快 |
| 峰值性能 | 高 | 中 |
| 优化能力 | 强 | 弱 |
| 适用场景 | 长期运行 | 启动敏感 |

---

*JIT编译是JVM性能优化的核心技术。*
