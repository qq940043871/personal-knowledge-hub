# Docker 学习笔记

## 隔离性

- Namespace
  - IPC：System V IPC 和 POSIX 消息队列
  - Network：网络设备、网络协议栈、网络端口等
  - PID：进程
  - Mount：挂载点
  - UTS：主机名和域名
  - USR：用户和用户组
- `lsns` 查看当前所有namspace
- 容器技术只是进程、没有完整的操作系统
- `nsenter -t pid -n ip a` 查看docker网络设置

## docker 如何建立本地仓库

（原笔记仅存此条目，未展开）

## linux对namespace操作方法

- clone
- setns
- unshare
- 同一主机ks现在是个
- 同一主机docker名义上没限制

## 可配额、可度量

- cgroups
  - 可以控制linux各进程cpu消耗的资源
  - memory子系统

## Union FS文件系统

- Docker文件系统
  - bootfs
  - rootfs
- `docker inspect`
- namespace做资源隔离、cgroup做资源控制

## Kubernetes的核心组件

（原笔记仅存此条目，未展开）

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 400" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <text x="430" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Docker 容器技术支柱</text>
  <line x1="515" y1="220" x2="570" y2="126" stroke="#64748b" stroke-width="1.5"/>
  <line x1="515" y1="220" x2="570" y2="213" stroke="#64748b" stroke-width="1.5"/>
  <line x1="515" y1="220" x2="570" y2="300" stroke="#64748b" stroke-width="1.5"/>
  <line x1="345" y1="220" x2="290" y2="169" stroke="#64748b" stroke-width="1.5"/>
  <line x1="345" y1="220" x2="290" y2="256" stroke="#64748b" stroke-width="1.5"/>
  <rect x="345" y="195" width="170" height="50" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
  <text x="430" y="225" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">Docker 容器技术</text>
  <rect x="570" y="100" width="250" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="695" y="121" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">Namespace 资源隔离</text>
  <text x="695" y="140" text-anchor="middle" font-size="11" fill="#475569">IPC·Network·PID·Mount·UTS·USR</text>
  <rect x="570" y="187" width="250" height="52" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="695" y="208" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">Cgroups 资源配额</text>
  <text x="695" y="227" text-anchor="middle" font-size="11" fill="#475569">CPU 消耗·memory 子系统</text>
  <rect x="570" y="274" width="250" height="52" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="695" y="295" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">Union FS 分层文件系统</text>
  <text x="695" y="314" text-anchor="middle" font-size="11" fill="#475569">bootfs·rootfs·docker inspect</text>
  <rect x="40" y="143" width="250" height="52" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="165" y="164" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">namespace 操作方法</text>
  <text x="165" y="183" text-anchor="middle" font-size="11" fill="#475569">clone·setns·unshare·lsns</text>
  <rect x="40" y="230" width="250" height="52" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="165" y="251" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">容器技术本质</text>
  <text x="165" y="270" text-anchor="middle" font-size="11" fill="#475569">只是进程，没有完整操作系统</text>
</svg>

*图：Docker 容器技术支柱示意（据原文重绘）*
