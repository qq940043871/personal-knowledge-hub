# 大模型面试复习 · 第53期（多模态生成大模型 AIGC 平台工程化 · 深度实战版）

> **本期定位**：前 52 期已覆盖 Agent Harness / RAG / FuncHub / CodeWeaver / EdgeLLM / LLMOps / Reasoning-RL / ModelRouter / ProtocolHub / MemoryWeaver / DataFoundry / 算子级优化（FlashAttention）等。本期补齐最大的一块空白——**多模态「生成」大模型（AIGC：文生图 / 文生视频 Diffusion 平台）**，与第 40 期 VLM「理解」形成「感知—生成」闭环。**需求 #1（项目亮点）**以一张全项目亮点速览矩阵开篇（含 Agent Harness），随后以 **AIGC Studio** 为新旗舰深度剖析。

---

---

### 1.1 全项目核心亮点速览矩阵（呼应需求 #1）

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

> 串联建议：AIGC Studio 的「文生图」可作为 Agent Harness 的一个**多模态工具**（第35/44期），由 FuncHub（第41期）统一路由、经 ModelRouter（第48期）做成本治理、用 LLMOps（第39期）做质量可观测——构成「生成式 Agent 全栈」。

### 1.2 AIGC Studio 六层架构

```
<code>┌─────────────────────────────────────────────────────────────┐<br/>│  应用层 (Application)  文生图/文生视频/风格化/LoRA 广场/编辑     │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  服务层 (Serving)   请求排队·优先级·多卡并行·显存复用·批处理bucketing·成本闸门 │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  采样与加速层 (Sampling&amp;Accel)  DPM-Solver++ / LCM / SDXL-Turbo / CFG蒸馏 │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  主干层 (Backbone)  VAE(编码/解码) + Text Encoder(CLIP/T5) + DiT(去噪U-Net) │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  噪声调度与训练层 (Schedule&amp;Train)  DDPM/EDM/SNR加权·v/ε预测·潜在蒸馏·ControlNet │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  数据层 (Data)  数据飞轮·美学打分·NSFW过滤·caption增强·去重防污染   │<br/>└─────────────────────────────────────────────────────────────┘</code>
```

**核心量化成果**（线上实测，A100 80G，1024×1024 文生图）：

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

**三大标志性能力**：

1. **可控生成**：ControlNet（边缘/深度/姿态）、IP-Adapter（身份保持）、T2I-Adapter（轻量条件）——解耦训练、即插即用。
1. **风格化与个性化**：LoRA/DoRA 微调 + 权重融合（merge），单张参考图即可萃取风格。
1. **高分辨率与视频**：AnyRes 分块（tiling）+ 潜空间放大；视频用 3D VAE + 时域注意力保证帧间一致性。

---

---

### 2.1 扩散过程的数学本质（前向 / 反向 / 训练目标）

**前向加噪（闭式）**：给定真实样本 x_0，按方差调度 \bar\alpha_t 逐步加高斯噪声，任意时刻可直接采样：

```
<code>x_t = sqrt(ᾱ_t) · x_0 + sqrt(1 - ᾱ_t) · ε,   ε ~ N(0, I)</code>
```

**反向去噪**：模型学习 p_\theta(x_{t-1}|x_t) = N(x_{t-1}; \mu_\theta(x_t,t), \Sigma_\theta)。训练目标可由 ELBO 化简为**噪声预测（ε-prediction）**的简化 MSE 损失：

```
<code>L_simple = E_{t, x_0, ε} [ || ε - ε_θ( sqrt(ᾱ_t)x_0 + sqrt(1-ᾱ_t)ε , t ) ||² ]</code>
```

**SNR 加权（EDM 视角）**：不同时间步信噪比差异巨大，最优加权为 `weight = SNR(t) + 1`（EDM），简单 MSE 在高低噪声区会失衡——这是高分辨率训练不稳定的根因之一。

**ε-prediction vs v-prediction**：

- ε 预测直接拟合噪声；
- v 预测拟合 v = \sqrt{\bar\alpha_t}\,\varepsilon - \sqrt{1-\bar\alpha_t}\,x_0，在高频噪声区数值更稳，SDXL / EDM 系列常用。
- 二者可互相转换：x_0 = \frac{x_t - \sqrt{1-\bar\alpha_t}\,\varepsilon_\theta}{\sqrt{\bar\alpha_t}}。

**根因 → 方案**：高分辨率（1024+）训练 loss 震荡，往往不是 lr 问题，而是 **SNR 加权失衡 + 大尺度潜变量方差爆炸**；方案是换 v-prediction + EDM 的 `c_skip/c_out/c_in` 归一化，并对 latent 做 `1/σ` 缩放。

### 2.2 采样器演进与「步数压缩」

DDIM（确定性、可跳步）→ DPM-Solver++（高阶 ODE 求解、20 步）→ LCM / SDXL-Turbo（1–4 步一致性/对抗蒸馏）。

**DDIM 单步**（由 x_0 预测反推）：

```
<code>x_{t-1} = sqrt(ᾱ_{t-1})·x̂_0 + sqrt(1-ᾱ_{t-1}-σ_t²)·ε_θ(x_t,t) + σ_t·z</code>
```

**一致性模型（Consistency Model）损失**（一步出图的关键）：

```
<code>L_CM = E[ λ(t) · d( f_θ(x_t, t), f_θ(x_{t+1}, t+1) ) ],   t ∈ {t_i}</code>
```

即「同一轨迹上任意两时刻的去噪结果必须一致」，于是 f_\theta(x_T, T) \to x_0 可一步完成。

**工程权衡**：步数越少延迟越低，但细粒度结构与文本对齐度下降；LCM 4 步 ≈ SD 25 步质量，是「质量-延迟 Pareto 前沿」的甜点。

### 2.3 DiT 为何取代 U-Net

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |

**DiT 核心 forward（概念代码）**：

```
<code>class DiTBlock(nn.Module):<br/>    def forward(self, x, t, y):            # x: [B, N, D]; t:时间; y:文本条件<br/>        adaln = self.adaLN(t, y)           # 由时间+文本生成调制参数<br/>        shift, scale, gate = adaln.chunk(3, dim=-1)<br/>        x = x + gate * attn( (x+shift)*scale )   # 自注意力(含cfg)<br/>        x = x + gate2 * mlp( (x+shift2)*scale2 )<br/>        return x</code>
```

### 2.4 显存墙工程（生成模型比 LLM 更吃显存）

文生图一次前向要保存全部中间激活（U-Net/DiT 各层），1024×1024 在 fp16 下峰值显存：

```
<code>峰值 ≈ 2·(模型权重 + 优化器状态) + 激活 ≈ 2·(W + 2W) + A    # 训练<br/>推理 ≈ W + A_decode(VAE解码最大)</code>
```

**六板斧**：

1. VAE tiling：解码时分块（如 512×512）避免整图 activation；
1. Attention slicing：注意力按 query 分片计算；
1. CPU offload：非活跃子模块临时移到内存；
1. xFormers / FlashAttention：显存 O(N²)→O(N)；
1. 模型分片（FSDP/device_map）：跨卡切权重；
1. bf16 + 梯度检查点（训练）。

### 2.5 可控生成：条件注入三件套

- **ControlNet**：复制 backbone 权重为 trainable copy，前端加 **零卷积（zero conv）**——初始化为 0 保证训练初期不破坏预训练分布；条件图（边缘/深度）经小编码器注入。
- **IP-Adapter**：解耦交叉注意力，把「图像条件」走独立 K/V 分支，文本分支不变，故**不改原模型权重的条件下**做身份保持。
- **T2I-Adapter**：极轻量（~70M）中间特征适配器，训练成本仅为 ControlNet 的 1/10。

```
<code># ControlNet 零卷积思想（简化）<br/>self.zero_conv = nn.Conv2d(..., bias=False); nn.init.zeros_(self.zero_conv.weight)<br/>h = backbone(x) + self.zero_conv(control_branch(cond))   # 初始贡献=0</code>
```

### 2.6 推理加速：从 50 步到 4 步

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

**CFG（Classifier-Free Guidance）公式**（质量提升的核心，也降低多样性）：

```
<code>x̂_0 = (1 + w)·ε_cond(x_t, c) − w·ε_uncond(x_t)</code>
```

w=1 退化为无条件；w 越大越贴合 prompt 但越「过度饱和/模式收缩」。

### 2.7 视频生成的时域一致性

图像模型逐帧独立→抖动。视频解法：

1. **3D VAE**：用因果 3D 卷积把 (T,H,W) 压到 (T',h,w)，时间维也进入潜空间；
1. **时域注意力**：DiT 中加 temporal attention，让帧间交换信息；
1. **先验约束**：光流 / 深度一致性 loss 作为训练正则；
1. **帧间潜变量传播**：前一帧 latent 作下一帧 context，缓解漂移。

### 2.8 服务化难点

- **请求排队与优先级**：生图耗时长（秒级），用优先级队列 + 抢占式超时避免长尾饿死；
- **显存多卡并行**：多 prompt 共享同一权重（device_map），按 batch bucketing 组相似分辨率；
- **成本闸门**：单用户日配额 + 预算熔断（参考第 48 期 ModelRouter 成本模型）。

---

---

### Q1：Diffusion 为什么比 GAN 更适合文本生成图像？

- **训练稳定性**：GAN 是 min-max 对抗，易 mode collapse / 梯度消失；Diffusion 是回归噪声的 MSE，训练极稳。
- **多样性**：GAN 判别器压低生成分布，易丢模式；Diffusion 建模全数据分布，采样多样性好。
- **可组合性**：可在潜空间做插值、inpainting、超分，且天然支持 CFG 精确控强度。
- **代价**：GAN 单步出图，Diffusion 需多步去噪（靠 2.2/2.6 的蒸馏弥补）。

### Q2：DDPM 与 DDIM 核心区别？

- DDPM 反向是**随机**马尔可夫链（每步加噪 z），必须走满 T 步；
- DDIM 是**确定性**非马尔可夫过程，等价边界分布下可「跳步」采样（50→20 步几乎无损），是可逆 ODE 的离散化；
- 本质：DDPM 采样方差大、慢；DDIM 用同训练权重即可加速，是后续所有快速采样器的基石。

### Q3：ε-prediction 与 v-prediction 怎么选？

- ε 预测最直观，但高噪声步（t 大）目标幅度大、低噪声步目标小，加权失衡；
- v 预测在高低噪声区量级更均匀，配合 EDM 的 `c_*` 归一化，高分辨率训练更稳定；
- 选 v 当：分辨率 ≥1024、用 EDM 调度、出现 loss 平台震荡；否则 ε 足够。

### Q4：CFG 为什么提升质量却降低多样性？能否避免？

- 公式 x̂=(1+w)ε_{cond}-w·ε_{uncond} 本质是「沿条件方向拉伸、远离无条件中心」，所以贴合 prompt（质量↑），但把分布推向条件流形边缘（多样性↓、过饱和）。
- 缓解：① 动态 w（按步衰减）；② CFG 蒸馏把 w 烘焙进权重，推理无需双路；③ 引入无分类器温度 sampling。

### Q5：如何把 50 步压到 4 步且质量不崩？

- **一致性蒸馏（LCM）**：训练约束「同轨迹任意两时刻输出一致」，一步出图；
- **对抗蒸馏（SDXL-Turbo）**：用判别器补细节，掩盖少步高频损失；
- **轨迹分段**：把 50 步 ODE 轨迹切 k 段，每段由子网络一步预测，段越多越稳；
- 实操：先 LCM 4 步打底，再 CFG 蒸馏去双路，最后用 TRT 量化，P50 可从 30s→3s。

### Q6：DiT 相对 U-Net 的真正优势是什么？

- 不是「质量上限」而是**可扩展性**：DiT 遵循 Transformer scaling law，参数量/数据量↑质量单调↑，U-Net 受卷积归纳偏置天花板限制；
- 条件注入更干净（adaLN 比 adain 可控），且天然适配 FlashAttention；
- 代价：更吃显存带宽，需 2.4 显存墙工程兜底。

---

---

### 模拟题 1：设计亿级用户文生图/视频生成平台的端到端架构

**考察点**：从数据→训练→采样→服务→可控→风格化的全链路闭环，而非单点。

**参考答案要点**：

1. **数据层**：数据飞轮（用户反馈→美学打分模型→回流优选）+ NSFW 过滤 + caption 增强（用 VLM 重写 prompt）+ MinHash 去重防污染（见第 50 期 DataFoundry）。
1. **训练层**：EDM 调度 + v-prediction + SNR 加权；可控生成用 ControlNet/IP-Adapter 解耦训练；风格化用 LoRA/DoRA 多基座并行蒸馏。
1. **主干**：VAE + Text Encoder(CLIP/T5) + DiT；视频用 3D VAE + 时域注意力。
1. **采样加速**：默认 LCM 4 步 + CFG 蒸馏；高质模式走 DPM-Solver++ 20 步。
1. **服务层**：优先级队列 + 多卡权重共享 + batch bucketing + 显存复用（VAE tiling）；成本闸门限流（接第 48 期 ModelRouter）。
1. **可观测**：Trace 每步耗时/显存/质量分（接第 39 期 LLMOps）；质量门禁自动回滚。
1. **应用层**：把生成能力包装成 Agent 工具，经 FuncHub 路由、ProtocolHub 暴露，接入 Agent Harness 做多模态 Agent。

### 模拟题 2：线上首图延迟突然从 3s 涨到 30s，30 分钟内止血，你怎么排查？

**考察点**：生成服务的故障定位 SOP（与第 44 期「复合故障止血」同思路）。

**参考答案要点（5 分钟定界 → 30 分钟止血）**：

1. **看队列**：请求是否堆积（调度层）→ 若有，是上游流量突增还是 worker 缩容（HPA 误判）。
1. **看单步耗时**：Trace 拆解 VAE 编码/DiT 去噪/VAE 解码三段，定位瓶颈段。
1. **常见根因**：加速开关被回退（LCM→DDIM 50 步）→ 恢复配置；
1. VAE tiling 关闭导致整图 activation 爆显存触发 CPU offload → 重开 tiling；
1. 未量化/精度回退 fp32 → 恢复 bf16；
1. 高分辨率请求占比突变（有人刷 2048）→ 加分辨率限流 + 降档。
1. **止血**：先熔断异常流量 + 限流，恢复 LCM/bf16/tiling 三件套，灰度放量验证 P50 回到 3s。
1. **复盘**：把「加速开关」「精度」「tiling」纳入质量门禁（第 39 期），防止再回退。

### 模拟题 3：用 7B 级小模型追平 SDXL 风格化质量，给出训练 + 推理方案

**考察点**：生成模型侧的「小模型追平大模型」（对应第 35/52 期「7B 追平 GPT-4o」思路在生成域的迁移）。

**参考答案要点**：

1. **潜在空间蒸馏**：用 SDXL 做 teacher，小 DiT 学其去噪轨迹（一致性 + 特征匹配 loss），避免从零学分布。
1. **CFG 蒸馏**：把 guidance 烘焙进权重，小模型推理无需双路（省一半算力）。
1. **LoRA 风格库**：把风格做成可插拔 LoRA，推理时 merge 权重，不用为每个风格训全模型。
1. **数据杠杆**：用 DataFoundry（第 50 期）合成高质量 caption + 风格对，小模型靠数据质量补参数量差距。
1. **推理加速**：LCM 4 步 + bf16 + VAE tiling + 设备内缓存，单图成本可压到 SDXL 的 1/8。
1. **评估**：用 FID/Clip-Score + 人工风格契合度双指标，确保「质量不崩、风格对齐」。

---

---

```
<code>【扩散公式】 x_t = √ᾱ_t·x0 + √(1-ᾱ_t)·ε ;  L = ||ε - εθ(x_t,t)||²<br/>【采样器】  DDPM(1000) → DDIM(50,确定性) → DPM-Solver++(20) → LCM/Turbo(4)<br/>【一致性】  L_CM = d(f(x_t,t), f(x_{t+1},t+1)) 同一轨迹输出一致→一步出图<br/>【CFG】     x̂ = (1+w)·εcond - w·εuncond ; w=1 即无条件, w↑质量↑多样性↓<br/>【DiT】     Patchify + ViT + adaLN ; 强 scaling law 取代 U-Net<br/>【可控】    ControlNet(零卷积) / IP-Adapter(解耦XAttn) / T2I-Adapter(轻量)<br/>【显存墙】  VAE tiling + Attn slicing + xFormers + CPU offload + 分片 + bf16<br/>【视频】    3D VAE + 时域注意力 + 光流/深度正则 + 帧间潜变量传播<br/>【成本】    首图 30s→3s(-90%) ; 单图 -87% ; 接 ModelRouter 做成本治理<br/>【串联】    AIGC Studio 作 Agent 多模态工具: FuncHub路由→ModelRouter成本→LLMOps质量</code>
```

---

---