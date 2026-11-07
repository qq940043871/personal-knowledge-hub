# Linux查看硬件配置命令

> ⚠️ 本篇为为知笔记导出存档，导出时丢失了部分数字，命令不可直接复制执行，仅作思路与步骤参考。

## 资源

| 命令 | 说明 |
| --- | --- |
| `du -ah --max-depth=` | 查看文件大小 |
| `for i in /*; do echo $i;find $i\|wc -l;done` | 目录下文件个数 |
| `df -i` | 磁盘inode节点数量 |
| `lsof\| grep delete\|more` | 僵尸文件 |
| `du -s /usr/* \|sort -nr` | 查看文件大小并排序 |
| `free -m` | 查看内存使用量和交换区使用量 |
| `df -h` | 查看各分区使用情况 |
| `du -sh <目录名>` | 查看指定目录的大小 |
| `uptime` | 查看系统运行时间、用户数、负载 |
| `cat /proc/loadavg` | 查看系统负载 |

## 网络

| 命令 | 说明 |
| --- | --- |
| `ifconfig` | 查看所有网络接口的属性 |
| `iptables -L` | 查看防火墙设置 |
| `route -n` | 查看路由表 |
| `netstat -lntp` | 查看所有监听端口 |
| `netstat -antp` | 查看所有已经建立的连接 |
| `netstat -s` | 查看网络统计信息 |

## 进程

| 命令 | 说明 |
| --- | --- |
| `ps -ef` | 查看所有进程 |
| `top` | 实时显示进程状态 |
| `/proc/pid` | 查看进程所在路径 |

## 系统

| 命令 | 说明 |
| --- | --- |
| `uname -a` | 查看内核/操作系统/CPU信息 |
| `head -n /etc/issue` | 查看操作系统版本 |
| `cat /proc/cpuinfo` | 查看CPU信息 |
| `hostname` | 查看计算机名 |
| `lspci -tv` | 列出所有PCI设备 |
| `lsusb -tv` | 列出所有USB设备 |
| `lsmod` | 列出加载的内核模块 |
| `env` | 查看环境变量 |

## 磁盘和分区

| 命令 | 说明 |
| --- | --- |
| `mount \| column -t` | 查看挂接的分区状态 |
| `fdisk -l` | 查看所有分区 |
| `swapon -s` | 查看所有交换分区 |
| `hdparm -i /dev/hda` | 查看磁盘参数(仅适用于IDE设备) |
| `dmesg \| grep IDE` | 查看启动时IDE设备检测状况 |

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 470" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="320" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Linux 硬件与系统排查路径</text>
  <rect x="160" y="58" width="320" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="78" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">系统变慢，先查资源</text>
  <text x="320" y="97" text-anchor="middle" font-size="12" fill="#475569">负载、内存、文件大小与目录占用</text>
  <line x1="320" y1="110" x2="320" y2="134" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="160" y="138" width="320" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="158" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">负载偏高，再查进程</text>
  <text x="320" y="177" text-anchor="middle" font-size="12" fill="#475569">进程状态、实时排行与所在路径</text>
  <line x1="320" y1="190" x2="320" y2="214" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="160" y="218" width="320" height="52" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="238" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">网络异常，接着查网络</text>
  <text x="320" y="257" text-anchor="middle" font-size="12" fill="#475569">接口属性、监听端口、连接与防火墙</text>
  <line x1="320" y1="270" x2="320" y2="294" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="160" y="298" width="320" height="52" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="320" y="318" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">磁盘告警，深入磁盘</text>
  <text x="320" y="337" text-anchor="middle" font-size="12" fill="#475569">分区状态、inode 与交换分区</text>
  <line x1="320" y1="350" x2="320" y2="374" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="160" y="378" width="320" height="52" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="320" y="398" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">环境基线不明，查系统</text>
  <text x="320" y="417" text-anchor="middle" font-size="12" fill="#475569">内核版本、CPU 信息与硬件设备</text>
</svg>
*图：Linux 硬件与性能排查思路示意（据原文重绘）*

来源：[http://www.lian.com/edu//-/html](http://www.lian.com/edu//-/html)
