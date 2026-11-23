# Flash-Attention

> 模块：Attention机制  
> 更新时间：2026-03-29

---

---

```
<code>Flash Attention：<br/>  - IO感知注意力算法<br/>  - 将注意力计算分块<br/>  - 减少HBM读写<br/>  - 加速2-4倍，显存减少10-20倍<br/><br/>核心思想：<br/>  1. 分块计算，避免一次性加载大矩阵<br/>  2. 在线计算softmax<br/>  3. 反向传播时可重新计算</code>
```

---

---

```
<code>import math<br/>import torch<br/>import torch.nn.functional as F<br/><br/>def flash_attention(Q: torch.Tensor, K: torch.Tensor, V: torch.Tensor,<br/>                    block_size: int = 128) -&gt; torch.Tensor:<br/>    """分块注意力：在线 softmax + 因果掩码（前向）；Q/K/V: (batch, heads, seq, dim)。"""<br/>    batch_size, num_heads, seq_len, head_dim = Q.shape<br/>    scale = 1.0 / math.sqrt(head_dim)<br/>    O = torch.zeros_like(Q)<br/>    l = torch.zeros(batch_size, num_heads, seq_len, 1, device=Q.device, dtype=Q.dtype)  # softmax 归一化因子<br/>    m = torch.full((batch_size, num_heads, seq_len, 1), -float("inf"), device=Q.device, dtype=Q.dtype)  # 逐行 running max<br/><br/>    # 外循环：K、V 分块；内循环：Q 分块<br/>    for j in range(0, seq_len, block_size):<br/>        for i in range(0, seq_len, block_size):<br/>            Q_block = Q[..., i:i + block_size, :]<br/>            K_block = K[..., j:j + block_size, :]<br/>            V_block = V[..., j:j + block_size, :]<br/>            qi, kj = Q_block.size(-2), K_block.size(-2)<br/>            if j &gt; i + qi - 1:      # 因果：该 KV 块对当前 Q 块整体不可见，跳过<br/>                continue<br/>            # S = QK^T / sqrt(d)<br/>            S_block = torch.matmul(Q_block, K_block.transpose(-2, -1)) * scale<br/><br/>            # 因果掩码：query 全局位置 i+t 只能看到 key 全局位置 &lt;= i+t<br/>            q_pos = torch.arange(i, i + qi, device=Q.device)<br/>            k_pos = torch.arange(j, j + kj, device=Q.device)<br/>            S_block = S_block.masked_fill(<br/>                k_pos[None, :] &gt; q_pos[:, None], -float("inf"))<br/><br/>            # ── 在线 softmax（★特殊点1 统计量口径统一：新旧统计量统一到同一 max 口径）──<br/>            m_new = torch.maximum(<br/>                m[..., i:i + qi, :],                      # 旧 running max<br/>                S_block.amax(dim=-1, keepdim=True))       # 当前块 max<br/><br/>            # 旧累积量按 exp(旧max-新max) 重缩放<br/>            alpha = torch.exp(m[..., i:i + qi, :] - m_new)<br/>            # 新块概率直接以 m_new 归一——已经在新口径下，不能再乘 alpha<br/>            P_block = torch.exp(S_block - m_new)<br/><br/>            # 分子分母同口径：l 与 O 都用「旧量×alpha + 新量」<br/>            l[..., i:i + qi, :] = alpha * l[..., i:i + qi, :] \<br/>                + P_block.sum(dim=-1, keepdim=True)<br/>            O[..., i:i + qi, :] = alpha * O[..., i:i + qi, :] \<br/>                + torch.matmul(P_block, V_block)<br/><br/>            m[..., i:i + qi, :] = m_new<br/><br/>    #   ★特殊点2 边界防御：分母加 eps 防全掩码行（l=0）产生 NaN；<br/>    #     因果掩码 + 全掩码块跳过，避免 inf - inf 产生 NaN<br/>    return O / (l + 1e-12)<br/><br/>def reference_attention(Q, K, V, scale):<br/>    """朴素全量对照基准（★特殊点3 数值算法必须带对照基准）：误差 &lt;1e-6 才算通过。"""<br/>    scores = torch.matmul(Q, K.transpose(-2, -1)) * scale<br/>    causal = torch.triu(torch.ones(scores.size(-1), scores.size(-1),<br/>                                   dtype=torch.bool, device=Q.device), diagonal=1)<br/>    return F.softmax(scores.masked_fill(causal, -float("inf")), dim=-1) @ V<br/><br/># 与朴素实现对拍误差 &lt;1e-6（内置种子验证从略；完整实现见 ownrag/harness 工程）</code>
```

---

---

- **数值算法必须带对照基准**：`reference_attention` 朴素实现做正确性锚点，误差 ~1e-6 才算通过——与 `ai-agent-harness/harness/benchmark.py`「先建基准再优化」的流程一致。
- **统计量口径统一**：l 与 O 的分子分母必须同口径（旧量×alpha + 新量），重缩放系数 alpha 只作用一次——数值 bug 属于「静默错误结果」，比崩溃更危险，测试兜底是底线。
- **边界防御**：因果掩码 + 全掩码块跳过 + 分母 eps，三重防护避免 `inf - inf` 产生 NaN——对应 harness 中显式超时/预算的边界处理思想。
- **教学实现 vs 生产内核**：真实加速请用 `F.scaled_dot_product_attention` / `flash-attn` 库；理解分块-在线 softmax 的结构是读懂 PagedAttention / 06-KV-Cache 的前提。
- **实现可离线验证**：`reference_attention` 对照基准即可在 CPU 上做数值对拍（误差 <1e-6），无需 GPU——参考 `ai-agent-harness/tests/` 的最小验证思路。

参考：70-企业级工程基准