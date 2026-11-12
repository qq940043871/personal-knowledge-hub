# Transformer 架构

> 💡 Transformer 是由 Vaswani 等人在 2017 年论文 "Attention is All You Need" 中提出的革命性神经网络架构。它摒弃了传统的循环和卷积结构，完全基于注意力机制构建，在机器翻译任务上取得了突破性性能。如今，Transformer 已成为自然语言处理、计算机视觉、语音处理等领域的基础架构，支撑了 GPT、BERT、LLaMA 等一系列里程碑式的模型。

## 1. 整体架构

Transformer 采用经典的 **Encoder-Decoder** 结构，其中 Encoder 负责将输入序列编码为连续表示，Decoder 则基于编码结果自回归地生成输出序列。

**架构示意：**

输入序列 → [Encoder × N] → 编码表示 → [Decoder × N] → 输出序列

原论文中 N=6，即 Encoder 和 Decoder 各堆叠 6 层。每一层的结构如下：

- **Encoder 层**：Multi-Head Self-Attention → Add & Norm → Feed-Forward Network → Add & Norm
- **Decoder 层**：Masked Multi-Head Self-Attention → Add & Norm → Multi-Head Cross-Attention → Add & Norm → Feed-Forward Network → Add & Norm

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 500" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="360" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Transformer整体架构</text>
  <rect x="80" y="64" width="160" height="44" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="160" y="91" text-anchor="middle" font-size="13" fill="#1e293b">输入序列</text>
  <line x1="160" y1="108" x2="160" y2="132" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="60" y="136" width="260" height="224" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="74" y="160" text-anchor="start" font-size="13" fill="#1e293b">Encoder × N</text>
  <rect x="90" y="176" width="200" height="34" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="190" y="198" text-anchor="middle" font-size="12" fill="#1e293b">Multi-Head Self-Attention</text>
  <rect x="90" y="222" width="200" height="34" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="190" y="244" text-anchor="middle" font-size="12" fill="#1e293b">Add &amp; Norm</text>
  <rect x="90" y="268" width="200" height="34" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="190" y="290" text-anchor="middle" font-size="12" fill="#1e293b">Feed-Forward Network</text>
  <rect x="90" y="314" width="200" height="34" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1"/>
  <text x="190" y="336" text-anchor="middle" font-size="12" fill="#1e293b">Add &amp; Norm</text>
  <line x1="322" y1="248" x2="396" y2="248" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="360" y="239" text-anchor="middle" font-size="12" fill="#475569">编码表示</text>
  <rect x="400" y="136" width="260" height="224" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="414" y="160" text-anchor="start" font-size="13" fill="#1e293b">Decoder × N</text>
  <rect x="430" y="176" width="200" height="34" rx="6" fill="#ffffff" stroke="#7c3aed" stroke-width="1"/>
  <text x="530" y="198" text-anchor="middle" font-size="12" fill="#1e293b">Masked Self-Attention</text>
  <rect x="430" y="222" width="200" height="34" rx="6" fill="#ffffff" stroke="#7c3aed" stroke-width="1"/>
  <text x="530" y="244" text-anchor="middle" font-size="12" fill="#1e293b">Add &amp; Norm</text>
  <rect x="430" y="268" width="200" height="34" rx="6" fill="#ffffff" stroke="#7c3aed" stroke-width="1"/>
  <text x="530" y="290" text-anchor="middle" font-size="12" fill="#1e293b">Cross-Attention</text>
  <rect x="430" y="314" width="200" height="34" rx="6" fill="#ffffff" stroke="#7c3aed" stroke-width="1"/>
  <text x="530" y="336" text-anchor="middle" font-size="12" fill="#1e293b">Add &amp; Norm + FFN</text>
  <line x1="530" y1="360" x2="530" y2="392" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="490" y="396" width="160" height="44" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="570" y="423" text-anchor="middle" font-size="13" fill="#1e293b">输出序列</text>
  <text x="360" y="462" text-anchor="middle" font-size="13" fill="#475569">编码器双向注意力，解码器带Mask自回归生成</text>
  <text x="360" y="486" text-anchor="middle" font-size="13" fill="#475569">典型应用：BERT（Encoder）、GPT（Decoder）</text>
</svg>

*图：Transformer Encoder-Decoder架构示意（依正文整理）*

| 特性 | Encoder | Decoder |
|-|-|-|
| 注意力类型 | 双向 Self-Attention（可看到完整输入） | Masked Self-Attention（仅看左侧已生成内容）+ Cross-Attention |
| 注意力层数 | 1 层 Self-Attention | 2 层（Masked Self-Attention + Cross-Attention） |
| 输入处理 | 并行处理整个输入序列 | 自回归生成，逐步输出 token |
| 位置编码 | 正弦/余弦位置编码或可学习位置编码 | 正弦/余弦位置编码或可学习位置编码 |
| 典型应用 | BERT、RoBERTa | GPT 系列、LLaMA（仅 Decoder） |

## 2. 核心组件

### 2.1 多头自注意力 (Multi-Head Self-Attention)

自注意力机制是 Transformer 的核心创新，其计算公式为：

**Attention(Q, K, V) = softmax(QK^T / √d_k)V**

其中 Q、K、V 分别是查询、键、值矩阵，d_k 是键向量的维度。

**为什么除以 √d_k？**

当 d_k 较大时，QK^T 的点积结果会变得很大，导致 softmax 函数进入梯度极小的饱和区。除以 √d_k 可以将方差稳定在 1 附近，确保梯度正常传播，提升训练稳定性。

**多头的意义：**

多头注意力将 Q、K、V 分别线性投影到 h 个不同的子空间，在每个子空间独立计算注意力，最后拼接结果。这使得模型能够同时关注来自不同位置、不同表示子空间的信息，捕获更丰富的语义模式。

```python
# 多头注意力的 PyTorch 实现示意
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, Q, K, V, mask=None):
        batch_size = Q.size(0)
        Q = self.W_q(Q).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(K).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(V).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        attn = torch.softmax(scores, dim=-1)
        output = torch.matmul(attn, V)
        output = output.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        return self.W_o(output)

```

### 2.2 前馈网络 (Feed-Forward Network, FFN)

每一层 Transformer 中，自注意力之后都跟随一个位置逐点（position-wise）前馈网络。它由两层线性变换和一个激活函数组成：

**FFN(x) = max(0, xW_1 + b_1)W_2 + b_2**

关键设计要点：

- 第一层将模型维度 d_model 扩展到内部维度 d_ff（通常 d_ff = 4 × d_model，如 d_model=512 时 d_ff=2048）
- 第二层再投影回 d_model，保持维度一致性
- 原始论文使用 ReLU 激活函数，现代变体已广泛采用更平滑的替代方案

**现代变体对比：**

| 激活函数 | 公式 | 使用者 | 特点 |
|-|-|-|-|
| ReLU | max(0, x) | 原始 Transformer | 简单但有"死神经元"问题 |
| GELU | x · Φ(x) | GPT-2, BERT | 平滑近似，梯度更连续 |
| SwiGLU | Swish(xW_1) ⊙ (xW_3) | LLaMA, PaLM | 门控机制，引入第三个权重矩阵，性能更优 |
| GeGLU | GELU(xW_1) ⊙ (xW_3) | Gemma | GELU 门控变体 |

> 💡 SwiGLU 和 GeGLU 引入门控机制（Gated Linear Unit），使用两个并行线性分支分别产生"值"和"门控信号"，逐元素相乘后输出。这种门控结构在同等参数量下通常能获得更好的语言建模性能，但需注意参数量增加约 50%（三个权重矩阵 vs 两个），通常通过缩小 d_ff 来保持总参数量不变。

### 2.3 残差连接与层归一化

每个子层（Self-Attention、Cross-Attention、FFN）都配有**残差连接**（Residual Connection）和**层归一化**（Layer Normalization），这是 Transformer 能够训练深层网络的关键。

**残差连接**的数学表达：output = LayerNorm(x + Sublayer(x))

残差连接允许梯度直接跳过子层回传，有效缓解深层网络中的梯度消失问题。没有残差连接，超过 6 层的 Transformer 几乎无法正常训练。

**Post-Norm vs Pre-Norm：**

| 变体 | 公式 | 特点 | 使用者 |
|-|-|-|-|
| Post-Norm（原始） | LayerNorm(x + Sublayer(x)) | 理论上表达能力更强，但训练不稳定，需要学习率 warmup | 原始 Transformer, BERT |
| Pre-Norm | x + Sublayer(LayerNorm(x)) | 训练更稳定，无需 warmup，梯度流更顺畅，轻微损失表达能力 | GPT-2, LLaMA, PaLM |

**层归一化的演进：**

原始 LayerNorm 对每个样本在隐藏维度上计算均值和方差进行归一化：

LayerNorm(x) = γ · (x - μ) / √(σ² + ε) + β

现代变体 **RMSNorm**（Root Mean Square Normalization）省略了均值中心化步骤，仅保留缩放操作：

RMSNorm(x) = γ · x / √(mean(x²) + ε)

RMSNorm 的优势：计算量减少约 10-15%，去掉均值和偏置项不影响模型质量，已被 LLaMA、Mistral、Qwen 等主流模型采用。

## 3. 仅解码器架构 (Decoder-Only)

虽然原始 Transformer 采用 Encoder-Decoder 结构，但当前大语言模型（LLM）领域几乎被 **Decoder-Only** 架构主导。GPT 系列（GPT-1/2/3/4）、LLaMA、PaLM、Mistral、Qwen 等均采用此架构。

**Decoder-Only 的核心特征：**

- **因果注意力掩码**（Causal Attention Mask）：每个 token 只能注意到它自身及之前位置的 token，不能"偷看"未来信息。这通过上三角掩码矩阵实现，掩码位置的注意力权重设为 -∞
- 移除了 Cross-Attention 层（因为没有独立的 Encoder），每一层仅包含 Masked Self-Attention + FFN
- 采用自回归方式逐 token 生成：输入和输出共享同一个序列空间

**Decoder-Only vs Encoder-Decoder 对比：**

| 特性 | Decoder-Only (GPT) | Encoder-Decoder (T5) |
|-|-|-|
| 注意力模式 | 因果（单向）注意力 | Encoder 双向 + Decoder 因果 + Cross-Attention |
| 预训练目标 | 下一 token 预测（NTP） | Span Corruption / Prefix LM |
| 生成方式 | 自回归，输入输出同序列 | Encoder 编码输入，Decoder 生成输出 |
| 参数效率 | 全部参数用于每步生成 | Encoder 参数在生成时"闲置" |
| 零样本能力 | 自然涌现（In-Context Learning） | 需要明确任务格式转换 |
| 代表模型 | GPT-4, LLaMA, PaLM, Mistral | T5, Flan-T5, mT5, BART |

**为什么 Decoder-Only 成为主流？**

研究发现（Chung et al., 2022），在同等参数量和数据量下，Decoder-Only 架构在多数零样本和少样本任务上表现不输甚至优于 Encoder-Decoder 架构。其核心优势在于：参数全部用于每一步的生成计算（Encoder-Decoder 中 Encoder 参数在自回归生成时不再参与），训练效率更高；同时因果注意力掩码天然支持 In-Context Learning，使得模型可以通过 prompt 完成各种任务，无需微调。

## 4. 现代 Transformer 变体

自 2017 年原始论文发表以来，Transformer 架构经历了大量改进和优化。下表对比了主流大语言模型的关键架构差异：

| 特性 | GPT-3 (2020) | LLaMA-2 (2023) | PaLM (2022) | Mistral-7B (2023) |
|-|-|-|-|-|
| 参数量 | 175B | 7B / 13B / 70B | 540B | 7.3B |
| 层归一化 | LayerNorm (Pre-Norm) | RMSNorm (Pre-Norm) | LayerNorm (Pre-Norm) | RMSNorm (Pre-Norm) |
| 激活函数 | GELU | SwiGLU | SwiGLU | SwiGLU |
| 位置编码 | 可学习绝对位置编码 | RoPE (旋转位置编码) | RoPE | RoPE |
| 注意力变体 | 标准 MHA | GQA (分组查询注意力) | MQA (多查询注意力) | GQA + 滑动窗口注意力 |
| vocab size | 50,257 (BPE) | 32,000 (SentencePiece) | 256,000 (SentencePiece) | 32,000 (SentencePiece) |
| 上下文长度 | 2,048 | 4,096 | 2,048 | 32,768 (滑动窗口 4,096) |
| FFN 维度倍数 | 4× | 约 2.7× (SwiGLU 调整) | 4× | 约 2.7× (SwiGLU 调整) |

### 关键改进详解

**RMSNorm vs LayerNorm：**RMSNorm 去除了均值中心化和偏置项，仅保留方差缩放。实验表明在 Transformer 中效果相当，但计算效率提升约 10-15%。公式对比如下：

- LayerNorm: y = (x - E[x]) / √(Var[x] + ε) · γ + β
- RMSNorm: y = x / √(mean(x²) + ε) · γ

**SwiGLU vs GELU：**SwiGLU 通过门控机制引入更强的非线性。其公式为 SwiGLU(x) = Swish(xW_1) ⊙ (xW_3)，其中 Swish(x) = x · σ(x)。Google 的研究（Shazeer, 2020）表明，在控制参数量相同的条件下，SwiGLU 在多项基准上显著优于 ReLU 和 GELU。

**RoPE vs ALiBi：**

| 特性 | RoPE (旋转位置编码) | ALiBi (线性偏置注意力) |
|-|-|-|
| 原理 | 对 Q、K 向量施加旋转变换，将位置信息编码进注意力内积 | 直接在注意力分数上添加与距离成正比的线性衰减偏置 |
| 长度外推 | 需要 NTK-aware 缩放或 YaRN 等技术支持 | 天然支持一定程度的长度外推 |
| 训练成本 | 无额外参数，计算开销可忽略 | 无额外参数，计算开销可忽略 |
| 采用者 | LLaMA, PaLM, Qwen, Mistral | BLOOM, MPT |

**分组查询注意力 (GQA) 与多查询注意力 (MQA)：**标准多头注意力（MHA）中每个头都有独立的 Q、K、V 投影。MQA 让所有头共享同一组 K、V，大幅减少 KV Cache 的显存占用和推理延迟；GQA 是折中方案，将查询头分成若干组，每组共享一组 K、V。LLaMA-2 的 70B 模型和 Mistral 均采用 GQA，在推理速度和模型质量之间取得良好平衡。

## 5. 关键论文

以下论文是理解和追踪 Transformer 架构演进的必读文献：

1. **Attention Is All You Need** (Vaswani et al., 2017) — Transformer 的奠基之作，提出 Self-Attention、Multi-Head Attention、位置编码等核心组件，彻底改变了序列建模范式。
https://arxiv.org/abs/1706.03762
2. **Language Models are Few-Shot Learners (GPT-3)** (Brown et al., 2020) — 展示了大规模 Decoder-Only Transformer 的 In-Context Learning 能力，证明了"规模法则"（Scaling Laws）的有效性，175B 参数的 GPT-3 在无需微调的情况下完成了多种 NLP 任务。
https://arxiv.org/abs/2005.14165
3. **LLaMA: Open and Efficient Foundation Language Models** (Touvron et al., 2023) — Meta 发布的开源大模型系列，系统验证了 RMSNorm、SwiGLU、RoPE、GQA 等现代架构组件的有效组合，成为后续开源模型（Alpaca、Vicuna、Mistral 等）的技术基座。
https://arxiv.org/abs/2302.13971
4. **PaLM: Scaling Language Modeling with Pathways** (Chowdhery et al., 2022) — Google 的 540B 参数模型，深入探索了模型规模、数据规模和计算资源之间的缩放关系，并行训练技术（Pathways）以及大规模模型的涌现能力。
https://arxiv.org/abs/2204.02311
5. **Mistral 7B** (Jiang et al., 2023) — 证明了 7B 级别模型通过精心的架构设计（GQA + 滑动窗口注意力 + SwiGLU）可以匹敌甚至超越更大的模型，推动了高效推理的技术方向。
https://arxiv.org/abs/2310.06825

---

*本文档最后更新：2026年5月*
