# Linux是怎样工作的？ - 架构师学习笔记

How Linux Works - 深入理解Linux操作系统的工作原理。

## Linux系统架构

```text
用户空间 (User Space)
        ↓
系统调用接口 (System Call Interface)
        ↓
内核空间 (Kernel Space)
        ↓
硬件 (Hardware)
```

## Linux内核的核心功能

### 进程管理

管理系统中的进程，包括进程的创建、调度和终止。

- 进程调度
- 进程同步
- 进程通信
- 进程信号

### 内存管理

管理系统内存，包括内存分配、回收和虚拟内存。

- 物理内存管理
- 虚拟内存管理
- 内存分页
- 内存映射

### 文件系统

管理文件和目录，提供文件系统接口。

- 文件系统抽象层
- 各种文件系统支持
- 文件权限管理
- 文件操作

### 设备管理

管理硬件设备，提供设备驱动接口。

- 设备驱动
- 设备文件
- 设备分类
- 设备管理

## Linux启动过程

### 1. BIOS/UEFI初始化

计算机加电后，BIOS/UEFI执行加电自检(POST)，然后从启动设备加载引导程序。

### 2. 引导加载程序

GRUB或其他引导加载程序加载Linux内核到内存：

- 显示启动菜单
- 加载内核镜像
- 加载初始RAM磁盘(initrd)
- 将控制权转移给内核

### 3. 内核初始化

Linux内核初始化系统：

- 初始化内存管理
- 检测硬件设备
- 加载设备驱动
- 挂载根文件系统
- 启动init进程

### 4. 系统初始化

init进程或systemd初始化系统：

- 启动系统服务
- 挂载其他文件系统
- 初始化网络
- 启动登录服务

*图：Linux 启动流程：从 BIOS/UEFI 自检到系统服务就绪（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 140" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="45" width="150" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="65" text-anchor="middle" font-size="14" fill="#1e293b">BIOS/UEFI初始化</text>
  <text x="95" y="84" text-anchor="middle" font-size="13" fill="#475569">加电自检，加载引导程序</text>
  <line x1="170" y1="70" x2="190" y2="70" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="195" y="45" width="150" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="270" y="65" text-anchor="middle" font-size="14" fill="#1e293b">引导加载程序</text>
  <text x="270" y="84" text-anchor="middle" font-size="13" fill="#475569">GRUB 加载内核到内存</text>
  <line x1="345" y1="70" x2="365" y2="70" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="370" y="45" width="150" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="445" y="65" text-anchor="middle" font-size="14" fill="#1e293b">内核初始化</text>
  <text x="445" y="84" text-anchor="middle" font-size="13" fill="#475569">启动 init 进程</text>
  <line x1="520" y1="70" x2="540" y2="70" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="545" y="45" width="150" height="50" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="620" y="65" text-anchor="middle" font-size="14" fill="#1e293b">系统初始化</text>
  <text x="620" y="84" text-anchor="middle" font-size="13" fill="#475569">systemd 启动系统服务</text>
</svg>

## Linux文件系统

Linux使用树形结构的文件系统：

- `/` - 根目录
- `/bin` - 基本命令
- `/sbin` - 系统命令
- `/etc` - 配置文件
- `/home` - 用户主目录
- `/var` - 可变数据
- `/tmp` - 临时文件
- `/usr` - 用户程序
- `/dev` - 设备文件
- `/proc` - 进程信息

## Linux进程管理

### 进程状态

Linux进程有以下几种状态：

- R - 运行态
- S - 睡眠态
- D - 不可中断睡眠态
- Z - 僵尸态
- T - 停止态

### 进程调度

Linux使用CFS (Completely Fair Scheduler) 调度器：

- 基于时间片的调度
- 考虑进程优先级
- 公平分配CPU时间
- 支持实时进程

## Linux网络栈

```text
应用层
  ↓
传输层 (TCP/UDP)
  ↓
网络层 (IP)
  ↓
数据链路层 (Ethernet)
```

## 总结：分层架构与模块化设计

- Linux是一个强大的操作系统，通过分层架构和模块化设计，实现了高效的资源管理和系统运行。
- 理解Linux的工作原理，有助于我们更好地使用和管理Linux系统，也为学习更高级的系统管理和开发打下基础。
