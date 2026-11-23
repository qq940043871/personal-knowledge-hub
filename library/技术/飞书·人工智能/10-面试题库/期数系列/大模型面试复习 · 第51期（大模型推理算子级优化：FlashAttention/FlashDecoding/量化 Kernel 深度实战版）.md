# 大模型面试复习 · 第51期（大模型推理算子级优化：FlashAttention / FlashDecoding / 量化 Kernel 深度实战版）

> **日期**：2026-07-25 ｜ **期数**：第51期（累计生成 51 个 MD 文件）｜ **定位**：工程化项目复盘系列 + 算子底层深挖  
> **与历史选题的关系**：第27期从「调度器/PagedAttention/Continuous Batching」讲**推理服务工程**；本期下沉一层，从 **CUDA Kernel / 显存层次 / 算子融合** 讲**推理算子级优化**——这是成本 `-71%` 故事的最底层杠杆（再往上是 ModelRouter 网关路由、Agent Harness 编排）。  
> **旗舰项目**：本期「项目亮点」以 **Agent Harness** 为旗舰示例（用户点名），并给出 12 项目核心亮点矩阵，呼应需求#1「总结大模型相关项目核心亮点」。

---

---

### 1.1 旗舰示例 —— Agent Harness（六层架构 + 调度 + 记忆 + 成本）

Agent Harness 是贯穿本复习体系的旗舰工程化项目，定位为「多智能体编排与运行时」。

- **六层架构**：`Client（接入/协议）` → `Agent（规划/ReAct）` → `Execution（工具执行/DAG）` → `Provider（模型网关）` → `Gateway（路由/限流）` → `Infra（KV/向量/缓存）`
- **DAG 动态调度器**：支持运行时拓扑展开、环检测（白灰黑三色标记）、分层并行（按入度为 0 的节点分批）、熔断降级（子图失败不影响主链路）。
- **三层记忆系统**：短期（Working）：会话内上下文窗口 + KV Cache 直挂；
- 中期（Episodic）：对话历史 + 向量检索（混合 RAG）；
- 长期（Semantic）：用户画像 + 领域知识库（MemoryWeaver 风格，参见第47期）。
- **可观测性与成本工程**：全链路 Trace + LLM-as-Judge 在线评测 + 语义缓存，推理成本 **-71%**、接入周期 **-92%**、P99 首 token **-68%**、工具调用首次成功率 **55% → 92%**。

### 1.2 大模型相关项目核心亮点矩阵（12 个项目）

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

> **速记**：从「模型能力（预训练33/对齐34/微调36/推理37）」→「知识（RAG38/GraphRAG46）」→「执行（FuncHub41/CodeWeaver42/ProtocolHub49）」→「运行时（Agent Harness35/44）」→「底座（EdgeLLM43/ModelRouter48/LLMOps39/DataFoundry50/MemoryWeaver47）」形成生产级全栈能力图谱。

---

---

> 本节的深度层级：从「为什么标准 Attention OOM」→「FlashAttention 在线 Softmax + Tiling」→「FlashDecoding 解码并行」→「量化 GEMM Kernel」→「算子融合」→「Roofline 瓶颈定位」，全程含可运行示意代码与数学推导。

### 难点 1：标准 Attention 的显存带宽瓶颈与 OOM 根因

标准自注意力：  
O = \mathrm{softmax}\left(\frac{QK^\top}{\sqrt{d}}\right)V,\quad Q,K,V\in\mathbb{R}^{N\times d}

朴素实现的致命问题：中间的 S=QK^\top \in \mathbb{R}^{N\times N} 必须**物化（materialize）到 HBM** 才能算 softmax 和反向传播。

- **显存**：标准实现需 O(N^2) 存 S；序列 8k 时 S 已占 8k\times8k\times2(\text{bf16})\approx 128\,\text{MB}，1M 上下文时 S\approx 2\,\text{TB} —— 直接 OOM。
- **计算强度（Arithmetic Intensity, AI）**：AI = \frac{\text{FLOPs}}{\text{Bytes}}。Attention 的 FLOPs \sim 2N^2d，但要读写 N^2 的 S，AI 很低，被 **HBM 带宽** 卡死而非算力。

**朴素实现（演示瓶颈）**：

```
<code>import torch<br/><br/>def naive_attention(q, k, v):  # q,k,v: [B, H, N, d]<br/>    # 1) 物化 N×N 分数矩阵到 HBM —— O(N^2) 显存，且一次 HBM 大矩阵读写<br/>    scores = (q @ k.transpose(-2, -1)) / (q.size(-1) ** 0.5)   # [B,H,N,N]<br/>    # 2) softmax 需要对整行做归约，但此时 S 已在 HBM<br/>    attn = torch.softmax(scores, dim=-1)<br/>    out = attn @ v<br/>    return out  # 反向时还需重算/重读 S → 二次 HBM 压力</code>
```

> 根因一句话：**把**N\times N**的中间矩阵落到 HBM 既爆显存又浪费带宽**。FlashAttention 的核心就是「永不在 HBM 物化 S」。

### 难点 2：FlashAttention —— 在线 Softmax + Tiling + 重计算

FlashAttention 的三板斧：**分块（Tiling）** 把 Q/K/V 切成能放进 SRAM 的块；**在线 Softmax（Online Softmax）** 在流式扫描 K/V 块时增量更新最大值与归一化分母，从而无需完整 S；**重计算（Recomputation）** 反向时重算 forward 的注意力权重，而非存 S，用算力换显存。

#### 2.1 数学：Online Softmax（安全增量归一化）

设对第 j 块（block）的向量 x^{(j)}\in\mathbb{R}^{B_k}（B_k 为块大小），维护运行最大值 m 与运行分母 \ell。扫描到第 b 块时：

m^{(b)} = \max\big(m^{(b-1)},\;\max_i x_i^{(b)}\big)

\ell^{(b)} = e^{m^{(b-1)}-m^{(b)}}\cdot \ell^{(b-1)} + \sum_i e^{x_i^{(b)}-m^{(b)}}

输出累加需对**历史块**加权修正（因全局最大值更新，旧值要按 e^{m^{(b-1)}-m^{(b)}} 缩放）：

O^{(b)} = e^{m^{(b-1)}-m^{(b)}}\cdot O^{(b-1)} + \mathrm{diag}\big(e^{x^{(b)}-m^{(b)}}\big)\,V^{(b)}

最终 softmax 输出 = O^{(\text{last})}/\ell^{(\text{last})}。**关键点：每个块只需要在 SRAM 内持有当前块与运行统计量，从不拼出完整**N\times N**矩阵。**

#### 2.2 内层循环（Triton 风格示意）

```
<code>@triton.jit<br/>def flash_attention_fwd(Q, K, V, O, L, M, sm_scale, BLOCK_Q, BLOCK_KV):<br/>    # 每个 program 处理一个 (batch, head, Q-block)<br/>    offs_q = tl.arange(0, BLOCK_Q)<br/>    offs_kv = tl.arange(0, BLOCK_KV)<br/>    q = tl.load(Q)                          # [BLOCK_Q, d] 载入 SRAM<br/>    m_i = tl.full([BLOCK_Q], -float('inf')) # 运行最大值<br/>    l_i = tl.zeros([BLOCK_Q])               # 运行分母<br/>    o_i = tl.zeros([BLOCK_Q, d])<br/>    for kv_start in range(0, N, BLOCK_KV):  # 外层循环：KV 块<br/>        k = tl.load(K + kv_start)           # [BLOCK_KV, d]<br/>        v = tl.load(V + kv_start)<br/>        s = tl.dot(q, k.T) * sm_scale       # [BLOCK_Q, BLOCK_KV] 仅在 SRAM<br/>        m_ij = tl.max(s, axis=1)            # 本块最大值<br/>        p = tl.exp(s - m_ij[:, None])       # 本块未归一化<br/>        m_new = tl.maximum(m_i, m_ij)<br/>        alpha = tl.exp(m_i - m_new)         # 旧输出缩放因子<br/>        l_i = alpha * l_i + tl.sum(p, axis=1)<br/>        o_i = alpha[:, None] * o_i + tl.dot(p, v)   # 增量累加输出<br/>        m_i = m_new<br/>    o_i = o_i / l_i[:, None]<br/>    tl.store(O, o_i); tl.store(M, m_i); tl.store(L, l_i)</code>
```

#### 2.3 收益与版本演进

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |

> 面试点：**为什么 FA 能既省显存又快？** 省显存=不物化 S；快=把 HBM 大矩阵乘换成 SRAM 内的小块乘，且 AI 提高后更贴近算力上限；反向靠重算 S（而非存 S）用 FLOPs 换显存。

### 难点 3：FlashDecoding —— 解码阶段长上下文的并行

解码（decode）与 prefill 的瓶颈**形状相反**：decode 时 Query 只有 **1 个（或少数）新 token**，而 KV Cache 可能长达 1M。若用 FlashAttention（按 Q 行并行），只有 1 个 block，无法并行 → 退化成串行扫 1M 的 KV，GPU 利用率极低。

**FlashDecoding 的解法：把并行维度换到 KV 上。** 将 KV 切成多块，每块独立算局部 softmax 统计量 (m_b, \ell_b, o_b)，最后跨块做一次 **softmax 归约**：

m^* = \max_b m_b,\quad \ell^* = \sum_b e^{m_b-m^*}\ell_b,\quad o^* = \frac{\sum_b e^{m_b-m^*} \ell_b\, o_b}{\ell^*}

```
<code>def flash_decoding(q_vec, K_blocks, V_blocks):   # q_vec: [d], K_blocks: List[[Bk,d]]<br/>    ms, ls, os = [], [], []<br/>    for kb, vb in zip(K_blocks, V_blocks):<br/>        s = q_vec @ kb.T / d**0.5             # [Bk]<br/>        mb = s.max(); pb = (s - mb).exp()<br/>        ms.append(mb); ls.append(pb.sum()); os.append(pb @ vb)<br/>    m_star = max(ms)<br/>    ls_star = sum(math.exp(mb - m_star) * lb for mb, lb in zip(ms, ls))<br/>    o_star = sum(math.exp(mb - m_star) * lb * ob for mb, lb, ob in zip(ms, ls, os)) / ls_star<br/>    return o_star</code>
```

> **FA vs FD 对照**：FA 在 **prefill/训练**（Q 长）时按 Q 并行；FD 在 **decode**（KV 长、Q 短）时按 KV 并行。两者都依赖 online softmax + 分块，只是并行轴不同。  
> **与 PagedAttention 的关系**：PagedAttention（vLLM）解决的是「KV Cache 物理分页、逻辑连续」的**内存管理**；真正算注意力时，底层仍用 FA/FD 风格的 kernel 去扫这些 **paged KV block**。即：PagedAttention = 分页内存管理 +（FlashDecoding 式）分块注意力计算。

### 难点 4：量化 GEMM Kernel（INT4/INT8）—— 反量化与 GEMM 融合

推理成本 `-71%` 的底层算力支点之一，是把权重量化到 INT4/INT8 并用 Tensor Core 加速。难点在「**如何反量化又不把 FP16 权重物化出来**」。

**量化映射**：  
W_{\text{int}} = \mathrm{round}\!\left(\frac{W}{s}\right) + z,\quad \hat W = W_{\text{int}}\cdot s + z  
INT4 采用 **group-wise**（每组 g 个权重共享 scale，g=128 常见），以抑制异常值（outlier）导致的精度崩。

**融合反量化 GEMM（AWQ 风格，Triton 示意）**：

```
<code>@triton.jit<br/>def int4_gemm(Q, W_int, Scales, Zeros, Out, g: tl.constexpr):<br/>    # W_int 以 packed INT4 存（两元素/字节），On-the-fly 反量化进 Tensor Core<br/>    w = unpack_int4(tl.load(W_int))               # [K] packed→[2K]<br/>    w = (w - tl.load(Zeros)) * tl.load(Scales)    # 反量化到 FP16，不落 HBM<br/>    acc = tl.dot(tl.load(Q), w.T)                 # Tensor Core FP16/INT8 累加<br/>    tl.store(Out, acc)</code>
```

- **数学/吞吐**：A100 上 INT8 Tensor Core 吞吐 ≈ 2× BF16；INT4 再打包 2×，理论 ~4×。实测 GEMM 密集层常达 **2–3×** 端到端吞吐提升。
- **为何 on-the-fly 反量化关键**：若先反量化出完整 FP16 权重再算，显存与带宽回到原点；融合后权重始终以 INT4 停留 HBM，仅在 SRAM/寄存器内还原。
- **精度护栏**：group-wise scale + 异常值保留（AWQ 的 salient weight 保护）+ 校准（GPTQ/ AWQ calibration）三件套，使 INT4 在 7B–70B 上掉点 <1%。

### 难点 5：算子融合（RMSNorm / RoPE / SwiGLU）—— 砍掉 HBM 往返

大模型单层里 RMSNorm、RoPE、SwiGLU 都是「读写远超计算」的 **memory-bound** 小算子。逐个 launch kernel 会让每个算子都做一次 HBM 读写往返 → 带宽浪费。融合后只进出一次 HBM。

**Fused RMSNorm（Triton 示意）**：

```
<code>@triton.jit<br/>def fused_rmsnorm(X, W, Y, eps, BLOCK):<br/>    x = tl.load(X, mask=...)                     # 一次读入<br/>    var = tl.sum(x * x, axis=-1) / N             # 方差<br/>    x = x * tl.rsqrt(var + eps)                  # 归一化<br/>    y = x * tl.load(W, mask=...)                 # 乘增益<br/>    tl.store(Y, y, mask=...)                     # 一次写出</code>
```

**融合收益量化**（A100，7B/13B 实测量级）：

- RMSNorm 融合：单算子 ~2–3× 加速，且减少 kernel launch 开销；
- RoPE + QKV 投影融合：prefill 阶段 ~10–15% 端到端提速；
- SwiGLU 融合（gate/up/down 三段合一）：~5–10% 提速。
- 综合：融合使「小算子带宽税」从显著变为可忽略，配合 FA/FD，显存带宽利用率从 ~60% 提到 ~85%+。

### 难点 6：Roofline 瓶颈定位 —— 何时该融合、何时该 Tiling

**算术强度**：AI = \frac{\text{FLOPs}}{\text{Bytes}}。与硬件两个上限比较：

- 带宽上限 \pi_{\text{mem}}（A100 ~1.5–2 TB/s）
- 算力上限 \pi_{\text{compute}}（A100 BF16 ~312 TFLOPS）

拐点 AI^* = \pi_{\text{compute}}/\pi_{\text{mem}} \approx 312\text{e12}/1.5\text{e12} \approx 200（FLOPs/Byte）。

| th | th | th | th | th |
| --- | --- | --- | --- | --- |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |

> 推论：decode 时 GPU 算力大量闲置，瓶颈在「把权重从 HBM 搬到计算单元」——所以 **EdgeLLM(43)/量化(24)** 的权重量化对 decode 提速最显著；prefill/train 才是 FA Tiling 的主场。这是端到端成本 `-71%` 的**底层物理依据**。

---

---

### Q1. FlashAttention 为什么能既省显存又提速？本质是什么？

**答**：两件事是同一个优化的两面。

- 省显存：标准 Attention 要在 HBM 物化 N\times N 分数矩阵 S（O(N^2)）；FA 用 Tiling 把 K/V 切成 SRAM 块，配合 **online softmax** 增量更新 (m,\ell)，**从不拼出完整**S，显存降到 O(N)。
- 提速：把「HBM 上一次大矩阵乘 + 一次大 softmax 归约」换成「SRAM 内多个小块乘」，AI（FLOPs/Byte）大幅提升，从带宽瓶颈逼近算力上限；反向用**重计算**S 替代存储 S，用算力换显存。
- 本质：**用分块 + 增量归约消除中间张量的 HBM 物化**，是「以算力换带宽/显存」的经典 kernel 优化。

### Q2. FlashAttention 和 FlashDecoding 区别？何时用哪个？

**答**：核心区别在**并行轴**。

- **FA**：并行维度在 **Q（序列）**。prefill/train 时 Q 很长，把 Q 切成多 block 分给不同 thread block 并行，每个 block 内部再串行扫 KV。
- **FD**：并行维度在 **KV**。decode 时 Q 仅 1 个新 token、KV 极长，按 Q 并行无意义；FD 把 KV 切块，每块算局部 softmax 统计量，再跨块归约。
- 选择：**prefill/训练用 FA，decode 用 FD**。两者底层都是 online softmax + 分块，只是谁被并行展开。

### Q3. PagedAttention 和 FlashAttention 什么关系？vLLM 如何结合？

**答**：**解决不同层次的问题**。

- PagedAttention 管**内存管理**：KV Cache 按固定 size 分页（block），逻辑连续、物理离散，配合注意力计算时按页表拼回。解决「长上下文 KV 显存碎片 + 无法共享前缀」问题。
- FlashAttention/Decoding 管**计算**：真正算注意力时仍用分块 kernel 扫 KV block。
- vLLM 结合方式：PagedAttention 提供「分页 KV + 页表寻址」，底层注意力 kernel 用 FlashDecoding 风格的分块扫这些 paged block，结合 prefix caching 复用整页 KV。即 **PagedAttention = 分页内存管理 + FD 式分块计算**。

### Q4. 为什么大模型推理是 memory-bound、训练是 compute-bound？给 Roofline 推导。

**答**：由算术强度 AI 决定。

- decode 阶段主导算子是 **GEMV**（输出 1 行，权重矩阵整块读取），FLOPs \sim 2Nd，但需读 Nd 权重到计算单元，AI \sim 2 FLOPs/Byte，远低于 A100 拐点 ~200 → **memory-bound**（GPU 算力闲置，卡在带宽）。
- prefill/train 主导算子是 **GEMM**（大 M），AI 随 M 增大远超拐点 → **compute-bound**。
- 推论：decode 提速靠「减少从 HBM 搬权重的量」= 权重量化(INT4) + KV 量化 + 算子融合；prefill/train 提速靠「提高算力利用率」= FA Tiling + 并行。这解释了量化对**推理**收益最大。

### Q5. INT4 量化 GEMM 如何做到不掉点？

**答**：三件套。

1. **group-wise scale**（每组 g=128 权重一个 scale/zero）：把异常值（outlier，常见于少数通道）的影响限制在组内，避免「一损俱损」整体偏移。
1. **salient weight 保护**（AWQ 思路）：权重对激活的重要性不均，按比例保留/放大重要通道的精度。
1. **校准 + 轻量微调**：用少量校准集确定 scale（AWQ/GPTQ），必要时 QAT 回补；推理端 **on-the-fly 反量化**（权重始终 INT4 存 HBM，仅在 SRAM 还原后送入 Tensor Core），不物化 FP16 权重。实测 7B–70B INT4 掉点 <1%。

### Q6. 算子融合的收益上限在哪？什么算子适合融合？

**答**：

- 适合融合：**memory-bound 的小 element-wise / reduction 算子**（RMSNorm、RoPE、SwiGLU、激活、bias add、dropout）。它们 FLOPs 小但读写多，逐个 kernel 的 HBM 往返是纯浪费。
- 收益上限：受限于「融合后仍需至少一次读输入、一次写输出」的下界，即单算子不可能快过「1 次 HBM 读 + 1 次 HBM 写」；融合的价值是把 N 个小算子的 N 次往返压成 1 次，故**算子链越长收益越大**，但也要权衡寄存器/SMEM 占用与编译复杂度（Triton 比手写 CUDA 更易写但偶有边界开销）。
- 不适合融合：大 GEMM（本身已 compute-bound，融合反而干扰 Tensor Core 排布）、跨 layer 的依赖算子（需中间结果做控制流）。

---

---

> 注：本期标题写「1 个模拟面试问题」，但需求#4 明确要求「生成 3 个针对性的模拟面试问题」，按详细需求生成 **3 道**；与近 16 期一致。

### 🎯 模拟题 1：从零设计支持 1M 上下文的推理引擎 Attention Kernel（prefill + decode 双阶段）

**业务背景**：要上线一个支持 1M token 上下文的对话引擎，必须显存 O(N)、延迟可控、能在单卡 80GB 上跑 7B/13B。

**参考答案要点**：

1. **显存预算（KV Cache 公式）**：|\text{KV}| = 2 \cdot L \cdot n_{kv} \cdot T \cdot h_d \cdot 2\,\text{Byte}（GQA 下 n_{kv}）。1M×13B(GQA, n_kv=8)：约 2\cdot8\cdot10^6\cdot128\cdot2 \approx 4\,\text{GB}/seq —— 必须**分页 + 前缀共享**，否则多用户炸显存。
1. **Prefill 阶段**：用 **FlashAttention-2/3**（按 Q 并行 + Tiling），绝不物化 N\times N；配合 **Ring/Sequence Parallelism** 把 1M 切到多卡做分块注意力（参考第26期 Ring Attention）。
1. **Decode 阶段**：用 **FlashDecoding**（按 KV 并行），把 1M KV 切块分摊到多个 thread block；KV 量化（K INT8 / V INT4）再砍 ~4× 显存与带宽。
1. **内存管理**：PagedAttention 分页 + Radix Tree 前缀缓存（复用 system prompt / 多轮历史整页）。
1. **可观测护栏**：KV 显存水位监控 + 自动 evict（LRU）；P99 解码延迟告警。

- **速记公式**：显存 O(N)（FA/FD 不物化 S）+ 分页复用 + KV 量化 = 1M 可落地。

### 🎯 模拟题 2：线上 P99 解码延迟 80ms → 400ms 的 30 分钟止血复盘

**业务背景**：某 Agent 服务（日均亿级调用）突然出现解码延迟暴涨 5×，成功率下降，需 30 分钟内止血。

**参考答案要点（结构化 SRE 思路）**：

1. **5 分钟定界**：看 trace 分层（第39期 LLMOps）——是「模型计算」还是「KV 读写」还是「调度排队」？延迟涨在 decode 的 attention 段 → 指向 KV 相关。
1. **根因假设树**：长上下文用户占比突增 → **KV Cache 分页碎片 + 命中率下降**，FlashDecoding 分块数暴涨；
1. 某批请求上下文从 8k 涨到 200k（用户行为/恶意刷长文）→ KV 显存压力 → **显存交换到 CPU（PCIe 瓶颈）**；
1. KV 量化被误关 / 新模型 scale 配置错误 → 单 seq KV 变大。
1. **止血动作（分级）**：一级：对超长上下文请求限流/降级（切到短上下文模型或裁剪历史）；
1. 二级：开启 **KV 量化** + 提高 prefix caching 命中（复用热点前缀）；
1. 三级：扩容 decode 专享卡 + 调大 FlashDecoding 分块并行度。
1. **根治**：长短上下文**分离部署**（第43期端云/第48期路由思路），长上下文走独立高显存池；KV 显存水位自动 evict。

- **速记**：decode 延迟暴涨 → 90% 是 KV 显存/带宽（非算力）→ 限流长上下文 + KV 量化 + 分页复用。

### 🎯 模拟题 3：7B 模型 INT4 量化把推理吞吐提升 3× 且不掉点（kernel + 调度双层方案）

**业务背景**：成本压不动，要求在不换大模型的前提下把 7B 在线推理吞吐翻 3 倍、质量不掉。

**参考答案要点**：

1. **Kernel 层（底层算力）**：权重量化 INT4 + **group-wise scale(g=128)** + AWQ salient 保护，HBM 占用 -75%；
1. **on-the-fly 反量化 GEMM**：权重始终 INT4 留 HBM，SRAM 内还原进 Tensor Core（A100 INT8 2×、INT4 打包 ~4× 理论）；
1. **KV 量化**（K INT8 / V INT4）降低 decode 带宽（decode 是 memory-bound，收益最大）；
1. **算子融合**（RMSNorm/RoPE/SwiGLU）砍 HBM 往返。
1. **调度层（上层杠杆，呼应 Agent Harness/ModelRouter）**：**Continuous Batching**（第27期）提升 batch 利用率；
1. **语义缓存 + prefix caching**（第48期/第27期）砍重复 prefill；
1. **路由**（第48期）：简单请求走 7B-INT4，复杂走大模型，整体调用降本。
1. **不掉点保障**：校准集 + 轻量 QAT 回补；上线前用 MT-Bench/业务集做 **diff 评测**（第39期在线评测去偏），掉点 <1% 才放量。

- **速记**：吞吐 3× = 量化(权重 INT4 + KV 量化) × 融合 × 批/缓存调度；不掉点 = group-wise + 校准 + diff 评测。

---

---

```
<code>【显存公式】<br/>|KV| = 2 · L · n_kv · T · h_d · 2 Byte   (GQA 下 n_kv&lt;n_h)<br/>标准 Attention S = QK^T ∈ R^{N×N} → O(N²) 物化到 HBM → OOM<br/>FA/FD：不物化 S → O(N)<br/><br/>【FlashAttention 三板斧】<br/>Tiling(切 SRAM 块) + Online Softmax(增量 m,ℓ) + Recomputation(反向重算 S)<br/>FA 并行轴=Q(prefill/train)  FD 并行轴=KV(decode)<br/><br/>【Online Softmax 递推】<br/>m_b=max(m_{b-1}, max x^{(b)}) ; ℓ_b=e^{m_{b-1}-m_b}ℓ_{b-1}+Σe^{x-m_b}<br/>O_b = e^{m_{b-1}-m_b}O_{b-1} + diag(e^{x-m_b})V^{(b)}<br/><br/>【Roofline / 瓶颈】<br/>AI=FLOPs/Byte ; A100 拐点≈200<br/>decode(GEMV) AI≈2 → memory-bound → 量化+融合<br/>prefill/train(GEMM) AI≫200 → compute-bound → FA Tiling+并行<br/><br/>【量化 GEMM】<br/>W_int=round(W/s)+z ; Ŵ=W_int·s+z<br/>group-wise(g=128)+AWQ salient+calibration → INT4 掉点&lt;1%<br/>on-the-fly 反量化(key: 不物化 FP16 权重)<br/><br/>【算子融合对象】<br/>memory-bound 小算子: RMSNorm/RoPE/SwiGLU/激活/bias → 融合砍 HBM 往返<br/><br/>【成本 -71% 的底层链】<br/>量化(权重/ KV) × 算子融合 × PagedAttention复用 × 路由/缓存(上层)<br/><br/>【本期 vs 历史】<br/>27 推理服务(调度/PagedAttention) → 51 推理算子(FA/FD/量化Kernel/融合): 下沉一层</code>
```

> 本期核心结论：**推理成本****`-71%`****的最底层杠杆是「算子级优化」**——FlashAttention/Decoding 消除 O(N^2) 显存物化、INT4 量化把权重带宽砍 75%、算子融合砍 HBM 往返；上层再由 PagedAttention 复用、ModelRouter 路由、Agent Harness 编排逐级放大。理解这一条物理链，能从「调参数」升级到「讲清为什么省」。