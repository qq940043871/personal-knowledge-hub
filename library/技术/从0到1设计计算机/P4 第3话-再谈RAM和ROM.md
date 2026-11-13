# 计算机存储器与CPU基础

## 一、课程引言

### 1. 课程定位与学习目标

本课程是**数字电路**或**计算机组成原理**系列课程的自然延伸。在前面的课程中，我们学习了逻辑门、组合电路和时序电路等基础原理，而本课程将把这些基础知识应用到计算机核心部件的构建与理解中。

**学习目标：**

- 掌握存储器（ROM与RAM）的**基本工作原理**与**外部接口**使用方法。
- 建立对**存储器在计算机系统中角色**的初步认知。
- 理解**CPU作为系统核心**的地位，并为后续深入学习打下基础。

### 2. 前置知识回顾（简略）

在学习本课程前，建议对第二季《数字电路》课程中涉及的**基本电气原理**（如电平、高低电平、脉冲信号、边沿触发等）有基本了解。即使您对这些概念有些生疏，也不必过分担心，本课程将侧重于应用层面的理解。

## 二、存储器的核心概念

为了直观地理解存储器，我们可以从一个简单的比喻开始。

### 1. 模型建立：存储器作为“抽屉”阵列

我们可以将一块存储器想象成一个由许多小格子组成的柜子，每个格子就是一个**抽屉**。

- **比喻：** 存储器就是一组有编号的“抽屉”阵列。
- **举例：** 一个容量为**256字节**的存储器，就包含了从**0号到255号**共256个抽屉。
- **容量与地址：** 每个抽屉（即**存储单元**）的容量是**1字节**。每个抽屉唯一的编号，就称为这个存储单元的**地址**。

因此，对存储器的访问，本质上就是通过“地址”这个编号，去找到对应的“抽屉”，并从中取出（读）或放入（写）数据。

## 三、存储器的外部接口

存储器并非孤立存在，它需要与计算机的其他部分（如CPU）交换信息。这种交换是通过其**外部接口**（即引出的线路）实现的。

### 1. 地址线

- **功能：** 地址线用于**指定要访问的“抽屉”编号（地址）**。当我们想要操作某个特定存储单元时，就必须在地址线上设置好该单元的地址码。
- **位数与容量的关系：** 地址线的根数直接决定了存储器能访问的最大范围。

  - 对于一个**256字节**的存储器，其地址范围是0-255。要表示256个不同的编号，需要 `log2(256) = 8` 位二进制数。因此，它需要**8位地址线**。
  - 同理，一个**512字节**的存储器，地址范围为0-511，需要 `log2(512) = 9` 位地址线。
- **图示简化：** 在电路图中，为了简洁，通常不画出所有并行的单根线，而是**用一根更粗的线条**来表示由多根线组成的**总线**，并在旁边标注线宽，如 `A[7:0]` 表示8位地址总线。

### 2. 数据线

- **功能：** 数据线用于**传输从存储器读出或写入的数据**。它是信息进出存储器的通道。
- **位数：** 数据线的根数通常与**存储单元的位宽**一致。如果每个存储单元存储1字节（8位）的数据，那么就会有**8根数据线**，共同构成一个8位的数据总线。

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 250" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
    <marker id="arwl" markerWidth="8" markerHeight="8" refX="0" refY="3" orient="auto">
      <path d="M7,0 L0,3 L7,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="90" width="130" height="110" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="85" y="135" text-anchor="middle" font-size="15" fill="#1e293b" font-weight="bold">CPU</text>
  <text x="85" y="160" text-anchor="middle" font-size="13" fill="#475569">读取指令 · 执行计算</text>
  <text x="85" y="180" text-anchor="middle" font-size="13" fill="#475569">控制其他部件</text>
  <rect x="560" y="70" width="140" height="150" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="630" y="100" text-anchor="middle" font-size="15" fill="#1e293b" font-weight="bold">存储器</text>
  <text x="630" y="125" text-anchor="middle" font-size="13" fill="#475569">256个“抽屉”</text>
  <text x="630" y="148" text-anchor="middle" font-size="13" fill="#475569">编号 0 ~ 255</text>
  <text x="630" y="171" text-anchor="middle" font-size="13" fill="#475569">每格 1 字节</text>
  <text x="630" y="194" text-anchor="middle" font-size="13" fill="#475569">（ROM / RAM）</text>
  <line x1="150" y1="105" x2="558" y2="105" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="350" y="95" text-anchor="middle" font-size="13" fill="#475569">地址总线 A[7:0]（指定抽屉编号）</text>
  <line x1="152" y1="132" x2="556" y2="132" stroke="#94a3b8" stroke-width="1.5" marker-start="url(#arwl)" marker-end="url(#arw)"/>
  <text x="350" y="122" text-anchor="middle" font-size="13" fill="#475569">数据总线 D[7:0]（双向：读出/写入）</text>
  <line x1="150" y1="159" x2="558" y2="159" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="350" y="149" text-anchor="middle" font-size="13" fill="#475569">读写控制线（0=读，1=写）</text>
  <line x1="150" y1="186" x2="558" y2="186" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="350" y="176" text-anchor="middle" font-size="13" fill="#475569">写脉冲线 WE#（边沿触发写入）</text>
  <text x="360" y="235" text-anchor="middle" font-size="13" fill="#475569">先设置地址与控制信号，再在脉冲边沿将数据锁存入指定单元</text>
</svg>

*图：存储器与CPU的外部接口（示意）*

## 四、ROM（只读存储器）的工作原理

ROM，即**只读存储器**，其特点是数据在制造时或编程后固定，一般用于存储需要长期保存且不需要修改的数据，如计算机的启动固件（BIOS）。

### 1. 读取操作

ROM的操作非常简单，主要就是**读取**：

1. **设置地址：** 将想要读取的数据单元的地址，加载到**地址线**上。
2. **输出数据：** 几乎在地址稳定的同时，该地址单元中存储的数据就会自动出现在**数据线**上，供CPU或其他部件读取。

- **特点：** ROM具有**非易失性**，断电后数据不会丢失。

## 五、RAM（随机存取存储器）的工作原理

RAM，即**随机存取存储器**，是计算机中最常用的主存储器（内存）。它最大的特点是**数据可读可写**，但断电后数据会丢失。

### 1. 相较于ROM的扩展

- **核心区别：** RAM在ROM只读的基础上，增加了**写入数据**的能力。
- **新增接口：** 为了实现读写控制，RAM至少新增了一根**读写控制线**。

### 2. 读取操作

RAM的读取操作与ROM完全相同：

1. 在地址线上设置目标地址。
2. 将**读写控制线置为低电平（逻辑0）**，表示当前操作为“读”。
3. 目标地址单元的数据便会出现在数据线上。

### 3. 写入操作

写入操作比读取要复杂一些，需要精确的时序配合：

1. **设置地址：** 在地址线上设置要写入的目标地址。
2. **设置控制信号：** 将**读写控制线置为高电平（逻辑1）**，表示当前操作为“写”。
3. **准备数据：** 将要写入的数据放置在**写数据线**上（对于简单的RAM模型，有时复用数据线，但需有控制信号区分方向）。
4. **产生脉冲（关键步骤）：** 产生一个短促的、**边沿触发的脉冲信号**（连接到RAM的**脉冲线**，常标记为 `WE#` 或 `WR`）。这个脉冲就像一个“确认”或“执行”指令，它的边沿（上升沿或下降沿）会触发RAM内部电路，将当前写数据线上的数据，锁存（存入）到指定地址的单元中。

- **特点：** RAM具有**易失性**，断电后存储的数据会立即丢失。它非常适合需要频繁高速读写数据的场景，如作为CPU的工作缓存和程序运行空间。

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 740 300" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar3" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <text x="370" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">ROM 与 RAM 工作原理对比</text>
  <rect x="20" y="50" width="340" height="230" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="190" y="76" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">ROM（只读存储器）</text>
  <rect x="60" y="90" width="260" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="190" y="117" text-anchor="middle" font-size="13" fill="#1e293b">地址线 → 选中目标单元</text>
  <line x1="190" y1="134" x2="190" y2="156" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#ar3)"/>
  <rect x="60" y="160" width="260" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="190" y="187" text-anchor="middle" font-size="13" fill="#1e293b">数据线 ← 数据自动输出</text>
  <text x="190" y="224" text-anchor="middle" font-size="13" fill="#475569">操作：仅支持读取</text>
  <text x="190" y="244" text-anchor="middle" font-size="13" fill="#475569">特性：非易失性，断电不丢失</text>
  <text x="190" y="264" text-anchor="middle" font-size="13" fill="#475569">用途：固件、启动程序等</text>
  <rect x="380" y="50" width="340" height="230" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="550" y="76" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">RAM（随机存取存储器）</text>
  <rect x="420" y="90" width="260" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="550" y="115" text-anchor="middle" font-size="13" fill="#1e293b">地址线 → 选中目标单元</text>
  <line x1="550" y1="130" x2="550" y2="150" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#ar3)"/>
  <rect x="420" y="154" width="260" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="550" y="179" text-anchor="middle" font-size="13" fill="#1e293b">数据线 ← 读出数据（读操作）</text>
  <line x1="550" y1="194" x2="550" y2="214" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#ar3)"/>
  <rect x="420" y="218" width="260" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="550" y="243" text-anchor="middle" font-size="13" fill="#1e293b">数据线 → 写入数据（写操作）</text>
  <text x="550" y="272" text-anchor="middle" font-size="13" fill="#475569">特性：易失性，断电即丢失</text>
  <text x="550" y="288" text-anchor="middle" font-size="13" fill="#475569">用途：工作缓存、程序运行空间</text>
</svg>

*图：ROM与RAM工作原理对比（示意）*

## 六、CPU（中央处理器）简介

### 1. 角色定位

在计算机系统的众多部件中，CPU（Central Processing Unit）是**最活跃、运作最复杂**的部件。它负责从内存（RAM）中读取指令、执行计算、处理数据，并控制其他所有部件协同工作，是整个计算机系统的“大脑”和指挥中心。

### 2. 课程衔接

了解存储器是理解计算机工作原理的第一步。CPU如何与存储器交互？它内部又是如何执行指令的？在接下来的课程中，我们将**“掀开CPU的外壳”**，初步探讨其内部的核心组成（如寄存器、算术逻辑单元ALU、控制单元）与工作方式。

## 七、总结与展望

### 1. 本节核心知识点回顾

- **存储器模型：** 可视为一个由“地址”编号的“抽屉”阵列，每个“抽屉”存储一个基本单位（如字节）的数据。
- **关键接口：** **地址线**用于选择单元，**数据线**用于传输信息。
- **ROM原理：** 只支持读取操作，通过地址线选中单元，数据即输出。
- **RAM原理：** 在ROM读取的基础上，增加了**读写控制线**和**脉冲线**，实现了受控的数据写入。

### 2. 引出后续主题

掌握了存储器的基础知识，我们就拥有了构建计算机记忆与存储模块的能力。下一步，我们将聚焦于那个指挥这一切的**核心——CPU**，探索其内部机制，以及CPU、存储器等部件如何协同工作，构成一个完整的计算机系统。
