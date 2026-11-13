# 4位计算机-logisim

好！你用 **Logisim Evolution 4.1.0** + 已有 **4位ALU**，我直接给你一套**可立即照做、能跑指令的4位计算机完整搭建步骤**（Evolution 专用，连线一次成功）。

![](images/1775376527435-5b524cda-a66d-4828-acb4-d63b8d7f048c-fee426a3.png)

## 一、先确认你的 4位ALU 接口（必须有）

- `A[3:0]`、`B[3:0]`（4位输入）
- `F[3:0]`（结果）
- `op[1:0]` 或 `op[2:0]`（运算选择）
- `Carry-out`（可选）

没有的话我可以先帮你补完。

## 二、计算机整体结构（Evolution 4.1.0 标准）

我们做 **极简4位CPU（能跑4条指令）**：

1. **PC（程序计数器）**：`Counter` 4位
2. **ROM**：`16×8bit`（存指令）
3. **指令寄存器 IR**：`Register` 8bit
4. **寄存器 A、B**：各4位
5. **你的ALU**
6. **控制单元（最简）**：少量门/`MUX`
7. **时钟、LED、开关**

*图：4位计算机整体结构框图（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 360" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw2" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <!-- Clock -->
  <rect x="30" y="20" width="100" height="44" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="80" y="47" text-anchor="middle" font-size="14" fill="#1e293b" font-weight="bold">Clock</text>
  <text x="80" y="65" text-anchor="middle" font-size="12" fill="#475569">全局时钟</text>
  <!-- PC -->
  <rect x="180" y="20" width="110" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="235" y="47" text-anchor="middle" font-size="14" fill="#1e293b" font-weight="bold">PC</text>
  <text x="235" y="65" text-anchor="middle" font-size="12" fill="#475569">程序计数器 4位</text>
  <!-- ROM -->
  <rect x="330" y="20" width="110" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="385" y="47" text-anchor="middle" font-size="14" fill="#1e293b" font-weight="bold">ROM</text>
  <text x="385" y="65" text-anchor="middle" font-size="12" fill="#475569">16×8bit</text>
  <!-- IR -->
  <rect x="480" y="20" width="110" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="535" y="47" text-anchor="middle" font-size="14" fill="#1e293b" font-weight="bold">IR</text>
  <text x="535" y="65" text-anchor="middle" font-size="12" fill="#475569">指令寄存器 8位</text>
  <!-- Clock to PC/IR -->
  <line x1="130" y1="42" x2="180" y2="42" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <line x1="130" y1="42" x2="130" y2="80" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="130" y1="80" x2="480" y2="42" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="230" y="78" text-anchor="middle" font-size="11" fill="#475569">Clock</text>
  <!-- PC to ROM -->
  <line x1="290" y1="42" x2="330" y2="42" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="310" y="32" text-anchor="middle" font-size="11" fill="#475569">地址</text>
  <!-- ROM to IR -->
  <line x1="440" y1="42" x2="480" y2="42" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="460" y="32" text-anchor="middle" font-size="11" fill="#475569">指令</text>
  <!-- Register A -->
  <rect x="180" y="140" width="110" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="235" y="160" text-anchor="middle" font-size="14" fill="#1e293b" font-weight="bold">寄存器 A</text>
  <text x="235" y="178" text-anchor="middle" font-size="12" fill="#475569">4位</text>
  <!-- Register B -->
  <rect x="180" y="220" width="110" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="235" y="240" text-anchor="middle" font-size="14" fill="#1e293b" font-weight="bold">寄存器 B</text>
  <text x="235" y="258" text-anchor="middle" font-size="12" fill="#475569">4位</text>
  <!-- ALU -->
  <rect x="370" y="160" width="120" height="64" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="430" y="187" text-anchor="middle" font-size="14" fill="#1e293b" font-weight="bold">ALU</text>
  <text x="430" y="205" text-anchor="middle" font-size="12" fill="#475569">4位运算器</text>
  <!-- A to ALU -->
  <line x1="290" y1="162" x2="370" y2="170" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="310" y="158" text-anchor="middle" font-size="11" fill="#475569">A</text>
  <!-- B to ALU -->
  <line x1="290" y1="242" x2="370" y2="214" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="310" y="262" text-anchor="middle" font-size="11" fill="#475569">B</text>
  <!-- ALU result to A -->
  <polyline points="430,224 430,250 290,250 290,184" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="360" y="246" text-anchor="middle" font-size="11" fill="#475569">F → 写回 A</text>
  <!-- ALU to LED -->
  <rect x="540" y="170" width="90" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="585" y="190" text-anchor="middle" font-size="14" fill="#1e293b" font-weight="bold">LED</text>
  <text x="585" y="208" text-anchor="middle" font-size="11" fill="#475569">4位显示</text>
  <line x1="490" y1="192" x2="540" y2="192" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="515" y="182" text-anchor="middle" font-size="11" fill="#475569">F</text>
  <!-- Control Unit -->
  <rect x="330" y="280" width="160" height="50" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="410" y="303" text-anchor="middle" font-size="14" fill="#1e293b" font-weight="bold">控制单元</text>
  <text x="410" y="322" text-anchor="middle" font-size="12" fill="#475569">门/MUX（最简）</text>
  <!-- IR to Control -->
  <line x1="480" y1="64" x2="480" y2="120" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="480" y1="120" x2="410" y2="120" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="410" y1="120" x2="410" y2="280" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="425" y="115" text-anchor="middle" font-size="11" fill="#475569">opcode</text>
  <!-- Control to A/B -->
  <line x1="330" y1="295" x2="290" y2="295" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="290" y1="295" x2="290" y2="264" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="270" y="285" text-anchor="middle" font-size="11" fill="#475569">WE</text>
  <!-- MUX for B input -->
  <rect x="540" y="220" width="90" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="585" y="240" text-anchor="middle" font-size="12" fill="#1e293b" font-weight="bold">MUX</text>
  <text x="585" y="258" text-anchor="middle" font-size="11" fill="#475569">2选1</text>
  <line x1="530" y1="242" x2="540" y2="242" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="535" y="234" text-anchor="middle" font-size="10" fill="#475569">IR/开关</text>
  <line x1="630" y1="242" x2="290" y2="242" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <text x="460" y="236" text-anchor="middle" font-size="11" fill="#475569">→ B</text>
  <text x="380" y="350" text-anchor="middle" font-size="13" fill="#475569">取指：PC → ROM → IR　|　执行：A/B → ALU → 写回A / LED　|　控制：IR[7:4] → 控制单元</text>
</svg>

## 三、Step 1：取指周期（PC + ROM + IR）

### 组件（从左侧库拖）

- `Memory` → **`Counter` (4位)** → PC
- `Memory` → **`ROM` (16×8bit)**
- `Memory` → **`Register` (8bit)** → IR
- `Wiring` → **`Clock`**
- `Wiring` → **`Splitter` (8→4+4)**

### 连线（严格照做）

1. **`Clock`** → PC 的 Clock
2. PC 输出 `[3:0]` → ROM 的 **`Address[3:0]`**
3. ROM 输出 `[7:0]` → **IR (`Register` 8位) 的 D 端**
4. **`Clock`** → IR 的 Clock（指令锁存）

作用：**每拍：PC+1 → 读ROM → 指令存入IR**

## 四、Step 2：数据通路（A、B、ALU）

### 组件清单

- `Memory` → **`Register` (4位)** ×2 → A、B
- 你的 **4位ALU**
- `Input/Output` → **`LED` 4位**（显示结果）
- `Plexers` → **`MUX` 2选1 (4位)**

### 连线（核心）

1. **A 寄存器 Q → ALU-A**
2. **B 寄存器 Q → ALU-B**
3. **ALU-F → A寄存器 D**（结果写回A）
4. ALU-F → **`LED` 4位**
5. IR 低4位（`IR[3:0]`）→ **MUX 输入0**
6. 4位开关 → **MUX 输入1**
7. MUX 输出 → **B寄存器 D**

## 五、Step 3：控制单元（让CPU“懂指令”）

### 指令格式（8位）

```plaintext
IR[7:4] = 操作码（opcode）
IR[3:0] = 立即数/数据
```

### 4条最简指令（直接用）

- `0000 xxxx` → **LOAD B**（B=立即数）
- `0001 xxxx` → **ADD**（A=A+B）
- `0010 xxxx` → **SUB**（A=A−B）
- `0011 xxxx` → **HALT**（暂停）

### 控制信号（Evolution 直接连线）

1. **`IR[7:4]` → ALU-op**（直接连）

   - `0001` → ADD
   - `0010` → SUB

2. **`IR[7:5]` 或简单门** → 控制：

   - `LOAD (0000)` → B寄存器 **`WriteEnable=1`**
   - `ADD/SUB (0001/0010)` → A寄存器 **`WriteEnable=1`**
   - `HALT (0011)` → PC **`Enable=0`**（停止）

> **Evolution 小技巧**：寄存器的 **`Enable/Write`** 直接接高/低，或用 `opcode` 经简单门控制。

## 六、Step 4：全局时钟（同步）

**一个 `Clock` 同时接：**

- PC Clock
- IR Clock
- A Clock
- B Clock

全部**同拍工作**（标准CPU时序）。

## 七、Step 5：测试程序（直接写入ROM）

在 ROM 地址 0~3 填入：

1. `0000 0001` → B=1
2. `0000 0010` → B=2
3. `0001 0000` → A=A+B
4. `0011 0000` → HALT

运行：

- 第1拍：B=1
- 第2拍：B=2
- 第3拍：A=1+2=**3（LED亮 0011）**
- 第4拍：停机

**你的计算机真正计算 1+2=3 成功！**

## 八、Evolution 4.1.0 常见坑（避坑）

- **位宽不匹配**：用 `Splitter` 严格 4/8位分开
- **时钟没全连**：PC/IR/A/B 必须同时钟
- **寄存器没使能**：`Write Enable` 必须为1才写入
- **ALU的op连错**：`opcode` 直接连 ALU 操作选择
