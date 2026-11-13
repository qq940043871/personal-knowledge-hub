# 玩转Linux操作系统

## 应用软件
```plain
# 断点续传下载文件
wget -c $url
# 下载整站
wget -r -p -np -k $url
# 发送网络连接（常用)
curl -XGET $url
# 传输文件
scp
sftp
# 数据镜像备份
rsync
```

## 检测工具
```plain
# 连通性检测
ping google.com
# 到对端路由检测
tracepath google.com
# 域名检测
dig google.com
nslookup google.com
# 网络扫描工具
nmap
# 压力测试
iperf
# 全方位监控工具（好东西)
nmon
```

## 配置工具
```plain
# 停止某个网卡
ifdown
# 开启某个网卡
ifup
# 多功能管理工具 
ethtool
```

## 压力测试
```plain
wrk
ab
webbench
http_load
```

## 多功能工具
```plain
# 远程登录
telnet
ssh
nc
# 防火墙
iptables -L
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 480" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="400" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Linux 常用工具五类</text>
  <rect x="305" y="215" width="190" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="400" y="245" text-anchor="middle" font-size="13" fill="#1e293b">Linux 常用工具</text>
  <rect x="60" y="80" width="220" height="52" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="170" y="102" text-anchor="middle" font-size="13" fill="#1e293b">应用软件</text>
  <text x="170" y="122" text-anchor="middle" font-size="11" fill="#475569">wget·curl·scp·rsync</text>
  <rect x="60" y="224" width="220" height="52" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="170" y="246" text-anchor="middle" font-size="13" fill="#1e293b">检测工具</text>
  <text x="170" y="266" text-anchor="middle" font-size="11" fill="#475569">ping·dig·nmap·nmon</text>
  <rect x="60" y="360" width="220" height="52" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="170" y="382" text-anchor="middle" font-size="13" fill="#1e293b">配置工具</text>
  <text x="170" y="402" text-anchor="middle" font-size="11" fill="#475569">ifup·ifdown·ethtool</text>
  <rect x="520" y="140" width="220" height="52" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="630" y="162" text-anchor="middle" font-size="13" fill="#1e293b">压力测试</text>
  <text x="630" y="182" text-anchor="middle" font-size="11" fill="#475569">wrk·ab·webbench</text>
  <rect x="520" y="330" width="220" height="52" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="630" y="352" text-anchor="middle" font-size="13" fill="#1e293b">多功能工具</text>
  <text x="630" y="372" text-anchor="middle" font-size="11" fill="#475569">ssh·nc·iptables</text>
  <line x1="305" y1="228" x2="284" y2="112" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="305" y1="240" x2="284" y2="250" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="305" y1="252" x2="284" y2="380" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="495" y1="228" x2="516" y2="172" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="495" y1="252" x2="516" y2="350" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
</svg>

*图：Linux 常用工具五类导图示意（依正文整理）*
