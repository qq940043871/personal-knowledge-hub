# Java应用CPU飙升案例

> 模块：实战案例
> 更新时间：2026-03-29

---

## 问题描述

> **服务器 CPU 使用率突然飙升到 100%，应用响应变慢，部分接口超时。**

```
服务器CPU使用率突然飙升到100%
应用响应变慢,部分接口超时
```

---

## 排查过程

> **五步走：确定进程 → 定位线程 → 获取堆栈 → 分析结果 → 代码审查。**

### 第一步：确定进程

```bash
# top查看整体
top
# 发现java进程CPU 980%

# 按CPU排序进程
ps aux --sort=-%cpu | head -10
# PID 12345 java进程CPU 980%
```

### 第二步：定位线程

```bash
# 查看java进程的线程
top -H -p 12345

# 发现线程12346 CPU 450%
#       线程12347 CPU 450%
#       线程12348 CPU 80%
```

### 第三步：获取堆栈

```bash
# 导出堆栈
jstack 12345 > /tmp/jstack.log

# 线程ID转16进制
printf "%x\n" 12346
# 输出: 303a

printf "%x\n" 12347
# 输出: 303b

# 查找对应堆栈
grep -A 50 "nid=0x303a" /tmp/jstack.log
grep -A 50 "nid=0x303b" /tmp/jstack.log
```

### 第四步：分析结果

```
发现两个热点线程:
1. nid=0x303a: 
   java.lang.Thread.sleep(Native Method)
   com.example.Utils.parseData()

2. nid=0x303b:
   java.util.regex.Pattern$Slice.match(Pattern.java:...)
   com.example.Parser.process()
```

### 第五步：代码审查

```java
// 发现问题代码
public class Parser {
    // 问题: 正则表达式每次调用都编译
    public boolean parse(String input) {
        Pattern pattern = Pattern.compile("^(\\w+)-(\\d+)-(\\w+)$");
        // 每次调用都创建Pattern对象
        return pattern.matcher(input).matches();
    }
}
```

*图：CPU 飙升五步排查流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 195" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="18" width="180" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="110" y="45" text-anchor="middle" font-size="14" fill="#1e293b">1.确定进程</text>
  <text x="110" y="80" text-anchor="middle" font-size="12" fill="#475569">top / ps --sort=-%cpu</text>
  <line x1="200" y1="40" x2="265" y2="40" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="270" y="18" width="180" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="45" text-anchor="middle" font-size="14" fill="#1e293b">2.定位线程</text>
  <text x="360" y="80" text-anchor="middle" font-size="12" fill="#475569">top -H -p PID</text>
  <line x1="450" y1="40" x2="515" y2="40" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="520" y="18" width="180" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="610" y="45" text-anchor="middle" font-size="14" fill="#1e293b">3.获取堆栈</text>
  <text x="610" y="80" text-anchor="middle" font-size="12" fill="#475569">jstack + printf "%x"</text>
  <line x1="610" y1="62" x2="610" y2="107" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="520" y="112" width="180" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="610" y="139" text-anchor="middle" font-size="14" fill="#1e293b">4.分析结果</text>
  <text x="610" y="174" text-anchor="middle" font-size="12" fill="#475569">grep nid=0x…</text>
  <line x1="520" y1="134" x2="455" y2="134" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="270" y="112" width="180" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="139" text-anchor="middle" font-size="14" fill="#1e293b">5.代码审查</text>
  <text x="360" y="174" text-anchor="middle" font-size="12" fill="#475569">定位 Pattern.compile</text>
  <line x1="270" y1="134" x2="205" y2="134" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="20" y="112" width="180" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="110" y="139" text-anchor="middle" font-size="14" fill="#1e293b">预编译修复</text>
  <text x="110" y="174" text-anchor="middle" font-size="12" fill="#475569">static final Pattern</text>
</svg>

---

## 解决方案

> **修复方式：把 Pattern 提为 `static final` 预编译对象，每次调用只复用，不再重复编译。**

```java
// 修复后
public class Parser {
    // 预编译正则表达式
    private static final Pattern PATTERN = 
        Pattern.compile("^(\\w+)-(\\d+)-(\\w+)$");
    
    public boolean parse(String input) {
        // 复用预编译对象
        return PATTERN.matcher(input).matches();
    }
}
```

---

## 根因分析

> **根因：正则表达式在循环中被重复编译——每次编译约 1ms，循环 1 亿次 = 100 秒 CPU 时间；修复即预编译，消除重复编译开销。**

```
根因: 正则表达式在循环中被重复编译
影响: 每次编译耗时约1ms,循环1亿次=100秒CPU时间
修复: 预编译正则,消除重复编译开销
```

---

## 预防措施

> **三条防线：代码规范禁止循环内 Pattern.compile、SpotBugs/FindBugs 静态检测、APM 监控兜底。**

```bash
# 1. 添加正则检查到代码规范
# 禁止在循环/高频方法中调用Pattern.compile()

# 2. 使用SpotBugs/FindBugs检测
<plugin>
    <groupId>com.github.spotbugs</groupId>
    <artifactId>spotbugs-maven-plugin</artifactId>
</plugin>

# 3. 添加APM监控
# Pinpoint/SkyWalking/Zipkin
```

---

## 总结

```
排查工具: top → jstack → grep → 代码审查
关键命令:
- top -H -p PID
- jstack PID
- printf "%x\n" TID
```

---

*案例完成*
