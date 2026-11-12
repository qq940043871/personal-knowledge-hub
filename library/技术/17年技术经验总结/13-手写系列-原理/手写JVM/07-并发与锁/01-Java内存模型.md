# Java内存模型

> 模块：手写JVM / 07-并发与锁
> 更新时间：2026-06-20

---

## 一、JMM概述：主内存与工作内存

**Java内存模型（JMM）定义了多线程程序中变量的访问规则**，保证内存可见性和有序性。

### 1.1 主内存与工作内存

```
主内存（Main Memory）
├── 变量A
├── 变量B
└── 变量C

工作内存1（线程1）    工作内存2（线程2）
├── 变量A副本          ├── 变量A副本
└── 变量B副本          └── 变量C副本
```

### 1.2 内存交互操作

| 操作 | 说明 |
|------|------|
| lock | 主内存变量加锁 |
| unlock | 主内存变量解锁 |
| read | 主内存读取变量 |
| load | 将read的变量加载到工作内存 |
| use | 将变量传递给执行引擎 |
| assign | 将执行结果赋值给变量 |
| store | 将工作内存变量传送到主内存 |
| write | 将store的变量写入主内存 |

*图：主内存与工作内存交互（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="250" y="18" width="220" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="40" text-anchor="middle" font-size="14" fill="#1e293b">主内存（Main Memory）</text>
  <text x="360" y="60" text-anchor="middle" font-size="12" fill="#475569">lock / unlock</text>
  <line x1="300" y1="70" x2="195" y2="166" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="150" y="115" text-anchor="middle" font-size="12" fill="#475569">read / load</text>
  <line x1="260" y1="170" x2="365" y2="70" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="360" y="120" text-anchor="middle" font-size="12" fill="#475569">store / write</text>
  <line x1="420" y1="70" x2="525" y2="166" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="570" y="115" text-anchor="middle" font-size="12" fill="#475569">read / load</text>
  <line x1="460" y1="170" x2="355" y2="70" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="560" y="120" text-anchor="middle" font-size="12" fill="#475569">store / write</text>
  <rect x="80" y="170" width="230" height="52" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="195" y="192" text-anchor="middle" font-size="14" fill="#1e293b">工作内存1（线程1）</text>
  <text x="195" y="212" text-anchor="middle" font-size="12" fill="#475569">use / assign</text>
  <rect x="410" y="170" width="230" height="52" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="525" y="192" text-anchor="middle" font-size="14" fill="#1e293b">工作内存2（线程2）</text>
  <text x="525" y="212" text-anchor="middle" font-size="12" fill="#475569">use / assign</text>
</svg>

---

## 二、volatile关键字

> volatile 保证可见性与有序性：写入立即可见于其他线程，并禁止指令重排序。

### 2.1 可见性

```java
// volatile保证可见性
volatile boolean running = true;

// 线程1
while (running) {
    // 执行任务
}

// 线程2
running = false; // 立即可见
```

### 2.2 有序性

```java
// 禁止指令重排序
volatile int a = 1;
int b = 2;

// 保证a=1在b=2之前执行
```

### 2.3 实现原理

```cpp
// 内存屏障
class VolatileVariable {
    int value;
    
    void store(int new_value) {
        value = new_value;
        // 写屏障：保证之前的写操作对其他线程可见
        store_barrier();
    }
    
    int load() {
        // 读屏障：保证读到最新值
        load_barrier();
        return value;
    }
};
```

---

## 三、happens-before规则

> happens-before 是保证内存可见性的核心规则集：程序顺序、监视器锁、volatile、线程启动/终止与传递性。

### 3.1 规则列表

| 规则 | 说明 |
|------|------|
| 程序顺序规则 | 同一线程内，前面的操作happens-before后面的操作 |
| 监视器锁规则 | unlock操作happens-before后续的lock操作 |
| volatile变量规则 | volatile写happens-before后续的volatile读 |
| 线程启动规则 | Thread.start()happens-before线程内所有操作 |
| 线程终止规则 | 线程内所有操作happens-before Thread.join() |
| 传递性 | A happens-before B，B happens-before C，则A happens-before C |

---

## 四、synchronized关键字

> 底层是 Monitor：owner 持有者 + EntryList 入口列表 + WaitSet 等待集合；未抢到锁的线程进入 EntryList 阻塞。

### 4.1 使用方式

```java
// 对象锁
synchronized (this) {
    // 临界区
}

// 方法锁
public synchronized void method() {
    // 临界区
}

// 类锁
public static synchronized void staticMethod() {
    // 临界区
}
```

### 4.2 实现原理

```cpp
// Monitor对象
class Monitor {
    Object* owner;          // 持有者
    WaitSet* wait_set;      // 等待集合
    EntryList* entry_list;  // 入口列表
    
    void enter(Thread* thread) {
        if (owner == nullptr) {
            owner = thread;
        } else {
            entry_list->add(thread);
            thread->block();
        }
    }
    
    void exit(Thread* thread) {
        owner = nullptr;
        if (!entry_list->empty()) {
            Thread* next = entry_list->remove_first();
            owner = next;
            next->unblock();
        }
    }
};
```

---

## 五、final关键字

> 构造函数结束后，final 字段对其他线程可见（构造写入后插入写屏障）。

### 5.1 语义保证

```java
// final字段初始化安全
final class Config {
    final int port;
    final String host;
    
    Config(int port, String host) {
        this.port = port;
        this.host = host;
    }
}

// 构造函数结束后，final字段对其他线程可见
```

### 5.2 内存屏障

```cpp
// final字段写入后插入写屏障
void constructor_end() {
    // 保证final字段在构造函数结束前初始化完成
    store_barrier();
}
```

---

## 六、原子操作

> CAS（Compare And Swap）依赖 CPU 原子指令，实现无锁的原子比较并交换。

### 6.1 CAS操作

```java
// Compare And Swap
AtomicInteger counter = new AtomicInteger(0);

// 原子递增
counter.incrementAndGet();

// 原子比较并交换
counter.compareAndSet(0, 1);
```

### 6.2 实现原理

```cpp
// CPU原子指令
bool cas(int* addr, int expected, int new_value) {
    return __sync_bool_compare_and_swap(addr, expected, new_value);
}
```

---

## 七、线程安全

> 不可变对象天然线程安全；并发场景优先使用线程安全集合。

### 7.1 不可变对象

```java
// 不可变对象天然线程安全
final class User {
    private final String name;
    private final int age;
    
    User(String name, int age) {
        this.name = name;
        this.age = age;
    }
}
```

### 7.2 线程安全类

```java
// 线程安全集合
ConcurrentHashMap<String, String> map = new ConcurrentHashMap<>();
CopyOnWriteArrayList<String> list = new CopyOnWriteArrayList<>();
```

---

## 八、最佳实践

1. **优先使用不可变对象** — 天然线程安全
2. **合理使用volatile** — 适用于一写多读场景
3. **避免过度同步** — 减少锁竞争
4. **使用并发工具类** — ConcurrentHashMap、AtomicInteger等
5. **理解happens-before** — 保证内存可见性

---

*理解JMM是编写正确并发程序的基础。*
