# 性能排查常用Linux命令

## 排序
grep -a MIDREQ midservice.1|awk -F '[' '{print $4}'|sort|uniq -c|sort -rn

## 资源
1. du -ah --max-depth=1 查看文件大小
2. for i in /*; do echo i;findi|wc -l;done 目录下文件个数
3. df -i 磁盘inode节点数量
4. lsof| grep delete|more 僵尸文件
5. du -s /usr/* |sort -nr #查看文件大小并排序
6. free -m # 查看内存使用量和交换区使用量
7. df -h # 查看各分区使用情况
8. du -sh <目录名> # 查看指定目录的大小
9. uptime # 查看系统运行时间、用户数、负载
10. cat /proc/loadavg # 查看系统负载

## 网络
1. ifconfig # 查看所有网络接口的属性
2. iptables -L # 查看防火墙设置
3. route -n # 查看路由表
4. netstat -lntp # 查看所有监听端口
5. netstat -antp # 查看所有已经建立的连接
6. netstat -s # 查看网络统计信息
7. traceroute 跟踪路由

## 进程
1. ps -ef # 查看所有进程
2. top # 实时显示进程状态
3. /proc/pid #查看进程所在路径

## 系统
1. uname -a # 查看内核/操作系统/CPU信息
2. head -n 1 /etc/issue # 查看操作系统版本
3. cat /proc/cpuinfo # 查看CPU信息
4. hostname # 查看计算机名
5. lspci -tv # 列出所有PCI设备
6. lsusb -tv # 列出所有USB设备
7. lsmod # 列出加载的内核模块
8. env # 查看环境变量
9. lscpu 查看cpu信息

## 磁盘和分区
1. mount | column -t # 查看挂接的分区状态
2. fdisk -l # 查看所有分区
3. swapon -s # 查看所有交换分区
4. hdparm -i /dev/hda # 查看磁盘参数(仅适用于IDE设备)
5. dmesg | grep IDE # 查看启动时IDE设备检测状况

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 480" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="400" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">性能排查常用 Linux 命令分类</text>
  <rect x="305" y="215" width="190" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="400" y="245" text-anchor="middle" font-size="13" fill="#1e293b">Linux 排查命令</text>
  <rect x="60" y="80" width="200" height="52" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="160" y="102" text-anchor="middle" font-size="13" fill="#1e293b">资源</text>
  <text x="160" y="122" text-anchor="middle" font-size="11" fill="#475569">du·df·free·uptime</text>
  <rect x="60" y="220" width="200" height="52" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="160" y="242" text-anchor="middle" font-size="13" fill="#1e293b">网络</text>
  <text x="160" y="262" text-anchor="middle" font-size="11" fill="#475569">ifconfig·netstat·route</text>
  <rect x="60" y="360" width="200" height="52" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="160" y="382" text-anchor="middle" font-size="13" fill="#1e293b">进程</text>
  <text x="160" y="402" text-anchor="middle" font-size="11" fill="#475569">ps·top·/proc</text>
  <rect x="540" y="150" width="200" height="52" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="640" y="172" text-anchor="middle" font-size="13" fill="#1e293b">系统</text>
  <text x="640" y="192" text-anchor="middle" font-size="11" fill="#475569">uname·cpuinfo·env</text>
  <rect x="540" y="290" width="200" height="52" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="640" y="312" text-anchor="middle" font-size="13" fill="#1e293b">磁盘和分区</text>
  <text x="640" y="332" text-anchor="middle" font-size="11" fill="#475569">mount·fdisk·swapon</text>
  <line x1="305" y1="228" x2="264" y2="112" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="305" y1="240" x2="264" y2="246" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="305" y1="252" x2="264" y2="380" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="495" y1="228" x2="536" y2="182" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="495" y1="252" x2="536" y2="310" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
</svg>

*图：性能排查常用 Linux 命令五类导图示意（依正文整理）*
