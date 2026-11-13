# Linux 性能排查命令

下面给你一套**体系化、可实战的 Linux 性能排查命令与组合**。内容按**排查维度 → 常用命令 → 典型组合 → 结论指向**来组织，适合线上故障、性能抖动、CPU 飙高、IO 卡顿、系统“无响应”等场景。

---

## 一、性能排查总体方法论（先看这个）
**顺序原则（非常重要）**

> **负载 → CPU → 内存 → IO → 网络 → 进程/线程 → 内核**
>

避免一上来就 `strace / perf`，那是最后一步。

---

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 380" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="430" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Linux 性能排查总体顺序</text>
  <rect x="24" y="70" width="104" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="76" y="98" text-anchor="middle" font-size="13" fill="#1e293b">整体负载</text>
  <line x1="129" y1="93" x2="139" y2="93" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="142" y="70" width="104" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="194" y="98" text-anchor="middle" font-size="13" fill="#1e293b">CPU</text>
  <line x1="247" y1="93" x2="257" y2="93" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="260" y="70" width="104" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="312" y="98" text-anchor="middle" font-size="13" fill="#1e293b">内存</text>
  <line x1="365" y1="93" x2="375" y2="93" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="378" y="70" width="104" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="430" y="98" text-anchor="middle" font-size="13" fill="#1e293b">磁盘 IO</text>
  <line x1="483" y1="93" x2="493" y2="93" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="496" y="70" width="104" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="548" y="98" text-anchor="middle" font-size="13" fill="#1e293b">网络</text>
  <line x1="601" y1="93" x2="611" y2="93" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="614" y="70" width="104" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="666" y="98" text-anchor="middle" font-size="13" fill="#1e293b">进程/线程</text>
  <line x1="719" y1="93" x2="729" y2="93" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="732" y="70" width="104" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="784" y="98" text-anchor="middle" font-size="13" fill="#1e293b">内核</text>
  <text x="76" y="140" text-anchor="middle" font-size="11" fill="#475569">uptime / vmstat</text>
  <text x="194" y="140" text-anchor="middle" font-size="11" fill="#475569">top / mpstat</text>
  <text x="312" y="140" text-anchor="middle" font-size="11" fill="#475569">free / vmstat</text>
  <text x="430" y="140" text-anchor="middle" font-size="11" fill="#475569">iostat / iotop</text>
  <text x="548" y="140" text-anchor="middle" font-size="11" fill="#475569">ss / sar</text>
  <text x="666" y="140" text-anchor="middle" font-size="11" fill="#475569">ps / top -H</text>
  <text x="784" y="140" text-anchor="middle" font-size="11" fill="#475569">perf / strace</text>
  <text x="430" y="184" text-anchor="middle" font-size="12" fill="#475569">先看整体态势，再逐层下钻，避免一上来就用 perf / strace</text>
  <rect x="24" y="210" width="812" height="130" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="430" y="240" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">现象 → 90% 原因（经验总结）</text>
  <text x="430" y="268" text-anchor="middle" font-size="13" fill="#1e293b">Load 高 CPU 不高 → IO / 锁；系统卡但 CPU 空 → IO Hang</text>
  <text x="430" y="294" text-anchor="middle" font-size="13" fill="#1e293b">wa 高 → 磁盘 / NFS；sy 高 → 内核态调用多</text>
  <text x="430" y="320" text-anchor="middle" font-size="13" fill="#1e293b">ssh 都慢 → swap 或 IO</text>
</svg>

*图：Linux 性能排查总体顺序示意（依正文整理）*

## 二、整体负载与系统态势（第一步）
### 1️⃣ `uptime` / `top`
```bash
uptime
```

关注：

+ Load Average（1/5/15）
+ 是否持续高于 CPU 核心数

判断方向：

+ **Load 高 + CPU 不高** → IO / 锁 / D 状态
+ **Load 高 + CPU 高** → 计算密集或死循环

---

### 2️⃣ `vmstat`（强烈推荐）
```bash
vmstat 1 5
```

关键列：

| 列 | 含义 | 异常判断 |
| --- | --- | --- |
| r | 运行队列 | > CPU 核心数 |
| b | 阻塞 | IO 问题 |
| us sy | 用户 / 内核 CPU | sy 高 → 系统调用多 |
| wa | IO 等待 | >20% 明显 IO 卡 |
| si so | swap | 非 0 即异常 |

---

## 三、CPU 性能排查
### 3️⃣ `top / htop`
```bash
top -H
```

+ 找 **CPU 占用高的线程**
+ 线程 ID（TID）可用于 jstack / pstack

---

### 4️⃣ `mpstat`
```bash
mpstat -P ALL 1
```

用途：

+ 看是否 **单核被打满**
+ `%irq / %soft` 高 → 中断风暴
+ `%steal` 高 → 虚拟化资源被抢

---

### 5️⃣ CPU 组合技（非常实用）
```bash
uptime
vmstat 1
mpstat -P ALL 1
top -H
```

结论指向：

+ us 高 → 业务逻辑
+ sy 高 → 内核 / syscall / 锁
+ wa 高 → IO

---

## 四、内存与 OOM 排查
### 6️⃣ `free`
```bash
free -h
```

重点：

+ available ≠ free
+ available 很小 → 内存压力

---

### 7️⃣ `vmstat`（再次强调）
```bash
vmstat 1
```

+ `si/so` ≠ 0 → 发生 swap
+ swap 会导致 **系统假死**

---

### 8️⃣ `top` 按内存排序
```bash
top
Shift + M
```

---

### 9️⃣ 内存组合
```bash
free -h
vmstat 1
top
dmesg | grep -i oom
```

---

## 五、磁盘 IO 排查（最常见卡顿原因）
### 🔟 `iostat`
```bash
iostat -x 1
```

关键字段：

| 字段 | 判断 |
| --- | --- |
| %util | >80% IO 打满 |
| await | >20ms（SSD >5ms） |
| svctm | 高 → 磁盘慢 |
| r/s w/s | IO 频率 |

---

### 11️⃣ `iotop`
```bash
iotop -oPa
```

+ 找 **真实 IO 大户**
+ 比 `top` 更可信

---

### IO 组合
```bash
vmstat 1
iostat -x 1
iotop -o
```

典型结论：

+ wa 高 + util 高 → 磁盘瓶颈
+ wa 高 + util 不高 → 文件系统 / 锁 / 网络盘

---

## 六、进程 / 线程阻塞排查
### 12️⃣ `ps`
```bash
ps -eo pid,ppid,stat,cmd,%cpu,%mem --sort=-%cpu | head
```

STAT：

+ `D` → 不可中断 IO（最危险）
+ `Z` → 僵尸
+ `R` → 运行

---

### 13️⃣ 线程级别
```bash
ps -eLo pid,tid,stat,pcpu,cmd --sort=-pcpu
```

---

## 七、网络性能排查
### 14️⃣ `ss`
```bash
ss -s
ss -antp
```

关注：

+ ESTAB 数量
+ SYN-SENT / CLOSE-WAIT

---

### 15️⃣ `sar`
```bash
sar -n DEV 1
sar -n TCP,ETCP 1
```

---

### 网络组合
```bash
ss -s
sar -n DEV 1
netstat -ant | awk '{print $6}' | sort | uniq -c
```

---

## 八、系统“无响应”/ 卡死专项排查
### 16️⃣ 快速判断是否 IO Hang
```bash
ps aux | awk '$8=="D"'
```

---

### 17️⃣ 是否内核锁死
```bash
dmesg -T | tail
cat /proc/locks
```

---

### 18️⃣ 火焰图 / perf（终极）
```bash
perf top
perf record -F 99 -p <pid> -g -- sleep 30
```

---

## 九、经典“一条命令搞清楚方向”组合
### ✅ 线上性能排查黄金组合
```bash
uptime
vmstat 1
iostat -x 1
mpstat -P ALL 1
top
```

### ✅ 系统假死（ssh 慢）
```bash
vmstat 1
ps aux | awk '$8=="D"'
iostat -x 1
```

### ✅ CPU 100%
```bash
top -H
mpstat -P ALL 1
perf top
```

---

## 十、经验总结（非常重要）
| 现象 | 90% 原因 |
| --- | --- |
| Load 高 CPU 不高 | IO / 锁 |
| 系统卡但 CPU 空 | IO Hang |
| sy 高 | 内核态调用多 |
| wa 高 | 磁盘 / NFS |
| ssh 都慢 | swap 或 IO |

---

## 十一、我可以继续帮你的方向
如果你愿意，我可以进一步给你：

+ 一份 **“线上排障速查表（PDF级别）”**
+ **JVM + Linux 联合排查流程**（结合你之前的 JVM 无响应问题）
+ **生产环境禁止/慎用命令清单**
+ **真实事故案例拆解（Load 高但 CPU 低）**

你可以直接说：
👉「结合 JVM 再来一套」 or 「做成一页速查表」
