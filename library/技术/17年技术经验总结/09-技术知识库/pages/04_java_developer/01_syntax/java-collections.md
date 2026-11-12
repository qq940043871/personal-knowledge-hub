# Java集合框架 - 架构师学习笔记

## 集合框架体系结构

Java集合框架是Java编程语言中用来表示和操作集合的统一架构。**所有的集合框架都包含在java.util包中**，它提供了许多接口和实现类，用于存储和操作对象组。

### 核心接口

| 接口 | 描述 | 主要实现类 |
|------|------|------------|
| Collection | 集合层次结构的根接口 | List, Set, Queue |
| List | 有序集合，允许重复元素 | ArrayList, LinkedList, Vector |
| Set | 不允许重复元素的集合 | HashSet, TreeSet, LinkedHashSet |
| Queue | 队列，通常以FIFO方式操作元素 | LinkedList, PriorityQueue |
| Map | 键值对映射，键唯一 | HashMap, TreeMap, LinkedHashMap |

*图：Java 集合框架主要接口与实现类一览（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 280" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <rect x="15" y="16" width="150" height="38" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="90" y="40" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">List</text>
  <rect x="195" y="16" width="150" height="38" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="270" y="40" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">Set</text>
  <rect x="375" y="16" width="150" height="38" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="450" y="40" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">Queue</text>
  <rect x="555" y="16" width="150" height="38" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="630" y="40" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">Map</text>
  <line x1="90" y1="54" x2="90" y2="88" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="90" y1="126" x2="90" y2="132" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="90" y1="170" x2="90" y2="176" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="270" y1="54" x2="270" y2="88" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="270" y1="126" x2="270" y2="132" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="270" y1="170" x2="270" y2="176" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="450" y1="54" x2="450" y2="88" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="450" y1="126" x2="450" y2="132" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="630" y1="54" x2="630" y2="88" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="630" y1="126" x2="630" y2="132" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="630" y1="170" x2="630" y2="176" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="630" y1="214" x2="630" y2="220" stroke="#94a3b8" stroke-width="1.5"/>
  <rect x="15" y="90" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="90" y="104" text-anchor="middle" font-size="13" fill="#1e293b">ArrayList</text>
  <text x="90" y="119" text-anchor="middle" font-size="11" fill="#475569">查询快，增删慢</text>
  <rect x="15" y="134" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="90" y="148" text-anchor="middle" font-size="13" fill="#1e293b">LinkedList</text>
  <text x="90" y="163" text-anchor="middle" font-size="11" fill="#475569">增删快，查询慢</text>
  <rect x="15" y="178" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="90" y="192" text-anchor="middle" font-size="13" fill="#1e293b">Vector</text>
  <text x="90" y="207" text-anchor="middle" font-size="11" fill="#475569">线程安全</text>
  <rect x="195" y="90" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="270" y="104" text-anchor="middle" font-size="13" fill="#1e293b">HashSet</text>
  <text x="270" y="119" text-anchor="middle" font-size="11" fill="#475569">无序，查询快</text>
  <rect x="195" y="134" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="270" y="148" text-anchor="middle" font-size="13" fill="#1e293b">LinkedHashSet</text>
  <text x="270" y="163" text-anchor="middle" font-size="11" fill="#475569">有序，查询快</text>
  <rect x="195" y="178" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="270" y="192" text-anchor="middle" font-size="13" fill="#1e293b">TreeSet</text>
  <text x="270" y="207" text-anchor="middle" font-size="11" fill="#475569">红黑树，排序存储</text>
  <rect x="375" y="90" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="450" y="113" text-anchor="middle" font-size="13" fill="#1e293b">LinkedList</text>
  <rect x="375" y="134" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="450" y="157" text-anchor="middle" font-size="13" fill="#1e293b">PriorityQueue</text>
  <rect x="555" y="90" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="630" y="104" text-anchor="middle" font-size="13" fill="#1e293b">HashMap</text>
  <text x="630" y="119" text-anchor="middle" font-size="11" fill="#475569">无序，查询快</text>
  <rect x="555" y="134" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="630" y="148" text-anchor="middle" font-size="13" fill="#1e293b">LinkedHashMap</text>
  <text x="630" y="163" text-anchor="middle" font-size="11" fill="#475569">有序，查询快</text>
  <rect x="555" y="178" width="150" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="630" y="192" text-anchor="middle" font-size="13" fill="#1e293b">TreeMap</text>
  <text x="630" y="207" text-anchor="middle" font-size="11" fill="#475569">红黑树，排序存储</text>
  <rect x="555" y="222" width="150" height="36" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="630" y="236" text-anchor="middle" font-size="13" fill="#1e293b">Hashtable</text>
  <text x="630" y="251" text-anchor="middle" font-size="11" fill="#475569">线程安全</text>
</svg>

## 常用集合类对比

### List实现类

| 实现类 | 底层结构 | 特点 |
|--------|----------|------|
| ArrayList | 动态数组 | 查询快，增删慢 |
| LinkedList | 双向链表 | 增删快，查询慢 |
| Vector | 动态数组 | 线程安全 |

### Set实现类

| 实现类 | 底层结构 | 特点 |
|--------|----------|------|
| HashSet | 哈希表 | 无序，查询快 |
| LinkedHashSet | 哈希表+链表 | 有序，查询快 |
| TreeSet | 红黑树 | 有序，排序存储 |

### Map实现类对比

| 实现类 | 底层结构 | 特点 | 适用场景 |
|--------|----------|------|----------|
| HashMap | 哈希表 | 无序，查询快 | 一般场景 |
| LinkedHashMap | 哈希表+链表 | 有序，查询快 | 需要保持插入顺序 |
| TreeMap | 红黑树 | 有序，排序存储 | 需要排序的场景 |
| Hashtable | 哈希表 | 线程安全 | 线程安全场景 |

## 使用示例

```java
// ArrayList示例
List<String> arrayList = new ArrayList<>();
arrayList.add("Apple");
arrayList.add("Banana");
arrayList.add("Orange");

// LinkedList示例
List<String> linkedList = new LinkedList<>();
linkedList.add("Dog");
linkedList.add("Cat");
linkedList.add("Bird");

// HashSet示例
Set<String> hashSet = new HashSet<>();
hashSet.add("Red");
hashSet.add("Green");
hashSet.add("Blue");

// HashMap示例
Map<String, Integer> hashMap = new HashMap<>();
hashMap.put("Apple", 5);
hashMap.put("Banana", 3);
hashMap.put("Orange", 8);

// 遍历示例
System.out.println("ArrayList:");
for (String fruit : arrayList) {
    System.out.println(fruit);
}

System.out.println("\nHashMap:");
for (Map.Entry<String, Integer> entry : hashMap.entrySet()) {
    System.out.println(entry.getKey() + ": " + entry.getValue());
}
```

## 性能优化建议

- 根据使用场景选择合适的集合类
- **预估集合大小时设置初始容量，避免频繁扩容**
- **注意集合的线程安全性，在并发环境下使用线程安全的集合类**
- 合理使用迭代器遍历集合
- **避免在遍历集合时修改集合结构**
- 使用泛型避免类型转换错误
