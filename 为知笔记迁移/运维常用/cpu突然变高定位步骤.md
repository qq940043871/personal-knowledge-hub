# cpu突然变高定位步骤

> ⚠️ 本篇为为知笔记导出存档，导出时丢失了部分数字，命令不可直接复制执行，仅作思路与步骤参考。

## 处理思路

```bash
# top 定位cpu高进程，记下 pid
top

# top -Hp pid 定位cpu高线程，记下 tpid
top -Hp pid

# printf "%x \n" tpid 转化为进制，记下 tpid_
printf "%x \n" tpid

# jstack pid | grep -A tpid_ 显示此线程的后续行
jstack pid | grep -A tpid_

# 抓取多次线程栈
for ((i=;i<;i++)); do jstack pid |grep -A tpid_;sleep ;done >> pid.jstack
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 520" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="320" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">CPU 突然变高定位思路</text>
  <rect x="170" y="58" width="300" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="86" text-anchor="middle" font-size="13" fill="#1e293b">系统负载告警，确认 CPU 异常升高</text>
  <line x1="320" y1="104" x2="320" y2="132" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="134" width="300" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="162" text-anchor="middle" font-size="13" fill="#1e293b">top 锁定最耗 CPU 的进程，记下 PID</text>
  <line x1="320" y1="180" x2="320" y2="208" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="210" width="300" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="238" text-anchor="middle" font-size="13" fill="#1e293b">top -Hp 锁定进程内高 CPU 线程 TID</text>
  <line x1="320" y1="256" x2="320" y2="284" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="286" width="300" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="314" text-anchor="middle" font-size="13" fill="#1e293b">线程号 TID 转十六进制便于检索</text>
  <line x1="320" y1="332" x2="320" y2="360" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="362" width="300" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="390" text-anchor="middle" font-size="13" fill="#1e293b">jstack 抓栈，按 TID 定位执行代码</text>
  <line x1="320" y1="408" x2="320" y2="436" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="438" width="300" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="320" y="466" text-anchor="middle" font-size="13" fill="#1e293b">循环抓取多次栈，对比归档定热点</text>
</svg>
*图：CPU 突然变高排查流程示意（据原文重绘）*

## top小技巧

| 目的 | 操作 |
| --- | --- |
| top按照cpu排序 | top界面按键大写P |
| top按照内存排序 | top界面按键大写M |
| top查看交换分区 | top界面按键小写f |
