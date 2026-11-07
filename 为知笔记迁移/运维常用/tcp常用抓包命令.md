# tcp常用抓包命令

> ⚠️ 本篇为为知笔记导出存档，导出时丢失了部分数字（IP、端口等），命令不可直接复制执行，仅作思路与步骤参考。

## 抓包存取

抓取所有经过网卡，目的主机为.的端口的网络数据并存储：

```bash
tcpdump -i eth host . and port -w /tmp/xxx.cap
```

## 过滤主机ip

抓取所有经过网卡，目的IP为.的网络数据：

```bash
tcpdump -i eth host .
```

## 过滤端口

抓取所有经过网卡，目的端口为的网络数据：

```bash
tcpdump -i eth dst port
```

## 过滤特定协议

抓取所有经过网卡，协议类型为UDP的网络数据：

```bash
tcpdump -i eth udp
```

## 抓取特定类型的数据包

抓取所有经过网卡的SYN类型数据包：

```bash
tcpdump -i eth 'tcp[tcpflags] = tcp-syn'
```

## 逻辑语句过滤

抓取所有经过网卡，目的网络是，但目的主机不是.的TCP数据：

```bash
tcpdump -i eth '((tcp) and ((dst net ) and (not dst host .)))'
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 520" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="320" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">tcpdump 抓包排查思路</text>
  <rect x="170" y="58" width="300" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="86" text-anchor="middle" font-size="13" fill="#1e293b">网络异常，先抓包看真实收发</text>
  <line x1="320" y1="104" x2="320" y2="132" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="134" width="300" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="162" text-anchor="middle" font-size="13" fill="#1e293b">按主机过滤：锁定来源与目的 IP</text>
  <line x1="320" y1="180" x2="320" y2="208" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="210" width="300" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="238" text-anchor="middle" font-size="13" fill="#1e293b">按端口过滤：聚焦具体服务</text>
  <line x1="320" y1="256" x2="320" y2="284" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="286" width="300" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="314" text-anchor="middle" font-size="13" fill="#1e293b">按协议过滤：区分 TCP 与 UDP</text>
  <line x1="320" y1="332" x2="320" y2="360" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="362" width="300" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="320" y="390" text-anchor="middle" font-size="13" fill="#1e293b">抓 SYN 等标志位：观察握手过程</text>
  <line x1="320" y1="408" x2="320" y2="436" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="170" y="438" width="300" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="320" y="466" text-anchor="middle" font-size="13" fill="#1e293b">组合逻辑条件，或存 cap 文件分析</text>
</svg>
*图：tcpdump 抓包排查思路示意（据原文重绘）*
