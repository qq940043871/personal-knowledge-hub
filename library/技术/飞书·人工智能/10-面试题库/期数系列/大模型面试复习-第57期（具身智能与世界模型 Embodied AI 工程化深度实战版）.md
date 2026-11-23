# 大模型面试复习-第57期（具身智能与世界模型 Embodied AI 工程化深度实战版）

> **本期主线**：具身智能与世界模型（Embodied AI / World Model）—— 把"看见—理解—规划—行动—感知反馈"闭环落到**物理世界**，让大模型从"会聊天"变成"会干活"的完整工程体系。  
> 它是 **VisionLLM（第40期，多模态理解）、Reasoning-RL（第37期，推理训练）、Agent Harness（第35/44/45/52期，智能体编排）、MemoryWeaver（第47期，长期记忆）** 之后，把"智能"真正**接入物理世界**的最后一公里；也是 VoiceWeaver（第56期）语音入口的"身体"。

---

---

前 56 期已覆盖：Agent Harness 编排与 SRE、RAG / GraphRAG 检索增强、FuncHub 函数调用、CodeWeaver 代码智能、EdgeLLM 端侧部署、LLMOps 可观测、Reasoning-RL 推理训练、ModelRouter 网关路由、ProtocolHub 协议互操作、MemoryWeaver 长期记忆、DataFoundry 合成数据、FlashAttention 算子优化、AIGC Studio 生成、VisionLLM 多模态理解、InterpLab 机制可解释性、ContextForge 上下文工程、VoiceWeaver 语音大模型。

**唯独缺"具身智能 / 世界模型"这一把智能落到物理世界的闭环**。2024–2026 年，RT-1/RT-2、OpenVLA、π0、Gemini Robotics、Figure、1X 把"机器人+大模型"推成新战场。纯对话 LLM 停在"语义空间"，而具身智能要跨越**感知—决策—动作—物理反馈**的鸿沟：连续动作、Sim-to-Real、高频闭环、长程规划、安全护栏都是对话模型从未遇到的硬骨头。本期以 **EmbodyWeaver** 为旗舰，呼应需求 #1（大模型相关项目核心亮点速览）。

---

---

### 2.1 全项目核心亮点速览矩阵

| th | th | th | th | th |
| --- | --- | --- | --- | --- |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |

> 上述 18 个项目全部可被具身平台调动：Agent Harness 做任务编排、VisionLLM 看世界、Reasoning-RL 训练策略、MemoryWeaver 记住环境、VoiceWeaver 收语音指令、ContextForge 组装上下文。**EmbodyWeaver 是它们"动手干活"的执行终端。**

### 2.2 旗舰项目：EmbodyWeaver 具身智能与世界模型平台

**六层架构（ASCII）**

```
<code>┌──────────────────────────────────────────────────────────────────┐<br/>│ L6  应用与评测层 │ 真实机器人/仿真器、任务评测(RLBench/手机)、安全护栏、人类回环 │<br/>├──────────────────────────────────────────────────────────────────┤<br/>│ L5  控制执行层   │ 阻抗/力控/WBC + 高频闭环(100–1000Hz) + 动作超时与安全门      │<br/>├──────────────────────────────────────────────────────────────────┤<br/>│ L4  策略与世界层 │ VLA 动作策略 + 世界模型(想象 rollout) + LLM 长程规划        │<br/>├──────────────────────────────────────────────────────────────────┤<br/>│ L3  感知理解层   │ VLM 视觉理解 + 指令解析 + 检测/分割 + 触觉/力觉融合          │<br/>├──────────────────────────────────────────────────────────────────┤<br/>│ L2  表征编码层   │ 多模态编码(视觉/触觉/本体觉) + 动作 tokenizer(离散/扩散)     │<br/>├──────────────────────────────────────────────────────────────────┤<br/>│ L1  数据引擎层   │ 遥操作 + 仿真合成(MimicGen) + 自博弈 + 视频学习(人类示范)     │<br/>├──────────────────────────────────────────────────────────────────┤<br/>│ L0  仿真接入层   │ Isaac/SAPIEN 仿真 + 域随机化(DR) + 系统辨识(校准到真实)       │<br/>└──────────────────────────────────────────────────────────────────┘<br/>      ▲ 上行（物理→模型）            ▼ 下行（模型→物理）<br/>   传感(视/触/本体) → 编码 → VLM理解 → LLM规划 → VLA动作 → 闭环控制 → 电机<br/>        └──────────── 世界模型预测未来状态，反哺规划与策略 ────────────┘</code>
```

**量化成果（一条真实抓取-放置链路）**

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

---

---

### 3.1 Sim-to-Real Gap：仿真训好、真机翻车

**根因**：仿真器与真实世界在①视觉纹理（光照/材质/背景）、②物理参数（摩擦/质量/关节间隙/传输延迟）、③传感器噪声（相机畸变/力矩漂移）、④动力学（柔性/接触形变）上存在系统性偏差。在仿真里收敛的策略，到真实机器人因"分布外"而失效——这是具身落地第一大坑。

**方案**：三板斧组合拳

1. **域随机化 DR（Domain Randomization）**：在仿真里随机化渲染与动力学参数，逼策略对分布鲁棒。
1. **系统辨识（System Identification）**：在真实机器人上实测物理参数，把仿真校准到真实分布（Sim-with-real-params），比纯 DR 更准。
1. **渐进式修正**：DAgger / 在线自适应，让人或仿真在真实轨迹上补标，缩小残差。

**数学视角**：设真实参数分布为 `P_real`，仿真随机化分布为 `p(ξ)`。策略目标是最小化真实期望风险，但只在仿真可采样的 `ξ` 上优化：

```
<code>min_θ  E_{ξ~p(ξ)} [ L(π_θ; ξ) ]      # 仿真期望风险</code>
```

当 `p(ξ)` 覆盖 `P_real` 时，真实风险有界：`R_real(θ) ≤ R_sim(θ) + gap(p, P_real)`，其中 `gap` 随两分布差异增大。DR 把 `gap` 压到策略鲁棒容差内；系统辨识则直接把 `P_real` 拉进 `p(ξ)` 的支撑集，更省样本。

**可运行代码：域随机化包装 + DAgger 聚合（简化版）**

```
<code>import numpy as np, random<br/><br/>class DomainRandomizer:<br/>    """在仿真里随机化动力学与渲染参数。"""<br/>    def __init__(self, rng_seed=0):<br/>        self.rng = random.Random(rng_seed)<br/>    def sample_sim_params(self):<br/>        # 物理参数在真实标称值附近大范围抖动<br/>        return {<br/>            "friction":   self.rng.uniform(0.3, 1.8),     # 真实≈0.8<br/>            "mass_scale": self.rng.uniform(0.6, 1.6),<br/>            "joint_damp": self.rng.uniform(0.1, 1.2),<br/>            "ctrl_delay": self.rng.randint(0, 3),          # 帧延迟<br/>            "light":      self.rng.uniform(0.2, 1.5),<br/>            "tex_noise":  self.rng.uniform(0.0, 0.4),<br/>        }<br/><br/>class DAgger:<br/>    """数据集聚合：让专家在策略走过的真实状态上补标。"""<br/>    def __init__(self, policy, expert):<br/>        self.policy, self.expert = policy, expert<br/>        self.D = []                      # (state, expert_action)<br/>    def collect(self, env, n_rollout=50):<br/>        for _ in range(n_rollout):<br/>            s, done = env.reset(), False<br/>            while not done:<br/>                a_pi = self.policy.act(s)              # 学生走<br/>                a_expert = self.expert.act(s)          # 专家标（真机/仿真最优）<br/>                self.D.append((s, a_expert))           # 用专家动作补标<br/>                s, _, done, _ = env.step(a_pi)         # 但按学生动作推进<br/>        return self.D</code>
```

> 关键权衡：**纯 DR** 不依赖真机参数、易扩展，但随机范围难定（太小→欠随机，太大→策略保守）；**系统辨识**精度高但要真机实测、难批量。工业做法是"辨识标定名义值 + DR 在其邻域抖动"，兼顾准与鲁棒。

### 3.2 VLA 模型：连续动作怎么喂给离散 LLM

**根因**：机器人动作是**连续高维向量**（7-DoF 关节角 / 末端 6D 位姿 / 力矩），与 LLM 的离散 token 自回归不天然兼容。直接回归一个向量又丢掉了 LLM 的"组合泛化"与"语义条件"能力。

**方案**：三种范式，各擅其场

1. **离散动作 token（RT-1 / RT-2 / OpenVLA）**：把每个动作维量化成 bins，像生成词一样自回归。简单、复用 LLM 栈，但连续极值/精细力控分辨率受限。
1. **连续动作流 / 扩散策略（π0 / Diffusion Policy / Octo）**：把动作建模为条件去噪过程，天然适配多峰、连续、高维动作分布。
1. **混合（分层）**：VLM 输出高层语义/子目标（离散），底层连续 policy 执行，兼顾语义与精度。

**数学视角**

- 离散动作：标准交叉熵 `L = -Σ_i log p_θ(a_i | o, l, a_{<i})`。
- 扩散动作（条件去噪）：`L_diff = E_{t,ε}[ || ε - ε_θ(a_t, o, l, t) ||² ]`，其中 `a_t` 是动作在第 `t` 步的噪声版本，`ε_θ` 在观测 `o` 与语言 `l` 条件下预测噪声。推理时从 `N(0,I)` 去噪采样得到连续动作。

**可运行代码：动作 tokenizer + 扩散策略草图**

```
<code>import torch, torch.nn as nn, torch.nn.functional as F<br/><br/>class ActionTokenizer:<br/>    """连续动作 → 离散 bins（类似 RT 系列）。"""<br/>    def __init__(self, low, high, bins=256):<br/>        self.low, self.high, self.bins = low, high, bins   # 各维同范围近似<br/>    def encode(self, a):   # a: (D,) 连续 → (D,) 离散 id<br/>        return ((a - self.low) / (self.high - self.low) * (self.bins - 1)).round().long().clamp(0, self.bins-1)<br/>    def decode(self, ids): # (D,) id → (D,) 连续（取 bin 中心）<br/>        return self.low + (ids.float() + 0.5) / self.bins * (self.high - self.low)<br/><br/>class DiffusionPolicy(nn.Module):<br/>    """条件扩散动作策略（草图：UNet 去噪）。"""<br/>    def __init__(self, obs_dim, lang_dim, act_dim, T=50):<br/>        super().__init__()<br/>        self.T = T<br/>        self.cond_enc = nn.Linear(obs_dim + lang_dim, 256)<br/>        self.unet = nn.Sequential(nn.Linear(256 + act_dim + 1, 512),<br/>                                  nn.ReLU(), nn.Linear(512, 512), nn.ReLU(),<br/>                                  nn.Linear(512, act_dim))<br/>    def loss(self, a0, cond, t):<br/>        noise = torch.randn_like(a0)<br/>        at = a0 + noise * t.view(-1,1)           # 简化的线性噪声调度<br/>        pred = self.unet(torch.cat([cond, at, t.view(-1,1)/self.T], -1))<br/>        return F.mse_loss(pred, noise)           # 预测加噪</code>
```

> 选型要点：**抓取/放置等动作维度低、精度要求中等的任务，离散 token 够用且易部署；插拔/装配/接触力控**等精细连续任务，扩散策略显著更稳（多峰分布不被 MSE 均值塌缩）。π0 的做法是 VLM 主干 + 流式扩散头（flow matching），是目前 SOTA 工程范式。

### 3.3 世界模型：让策略"想象"未来再行动

**根因**：真实交互采样极贵（机器人易损、慢、危险），且长程规划需要预判"这一步下去世界会变成啥样"来选最优动作。没有世界模型，策略只能"走一步看一步"。

**方案**：三类世界模型

1. **预测式 JEPA（I-JEPA / S-I-JEPA）**：在**表示空间**预测未来表示，不重建像素，高效、强泛化。
1. **生成式 DreamerV3**：RSSM 隐状态建模 `p(s',r|s,a)`，在**想象 rollout** 里用 actor-critic 训练，样本效率极高。
1. **扩散世界模型（Genie / UniSim）**：像素级未来帧预测，用于生成训练数据 / 视频仿真。

**数学视角（Dreamer 风格）**：世界模型由 encoder `q(s_t|o_t)`、动力学 `p(s_t|s_{t-1},a_{t-1})`、奖励 `p(r_t|s_t)` 组成。策略在 latent rollout 上优化：

```
<code>J(π) = E_{s_0~p, s_{t+1}~p(·|s_t,a_t), a_t~π(·|s_t)} [ Σ_t γ^t r_t ]</code>
```

想象 rollout 用学到的动力学替代真实环境，把"与环境交互"换成"与模型交互"，样本效率提升一个数量级。

**可运行代码：RSSM 风格 transition + JEPA 编码器草图**

```
<code>import torch, torch.nn as nn, torch.nn.functional as F<br/><br/>class RSSMTransition(nn.Module):<br/>    """Dreamer 风格：从 (隐状态, 动作) 预测下一隐状态（含随机性）。"""<br/>    def __init__(self, s_dim, a_dim, h_dim=256):<br/>        super().__init__()<br/>        self.rnn = nn.GRUCell(h_dim, h_dim)<br/>        self.mean = nn.Linear(h_dim + a_dim, s_dim)<br/>        self.std  = nn.Linear(h_dim + a_dim, s_dim)<br/>    def forward(self, h, s, a):<br/>        h2 = self.rnn(torch.cat([s, a], -1), h)<br/>        m  = self.mean(torch.cat([h2, a], -1))<br/>        l  = self.std(torch.cat([h2, a], -1)).clamp(-5, 5)<br/>        s2 = m + torch.exp(l) * torch.randn_like(m)   # 重参数化采样<br/>        return h2, s2, m, torch.exp(l)<br/><br/>class JEPAEncoder(nn.Module):<br/>    """S-I-JEPA：在表示空间预测，目标块用 EMA 教师，不重建像素。"""<br/>    def __init__(self, in_dim=3*16*16, d=256):<br/>        super().__init__()<br/>        self.student = nn.Linear(in_dim, d)<br/>        self.teacher = nn.Linear(in_dim, d)<br/>        for p in self.teacher.parameters(): p.requires_grad = False<br/>    def forward(self, x_ctx, x_target):<br/>        z_s = self.student(x_ctx)<br/>        with torch.no_grad():<br/>            z_t = self.teacher(x_target)          # EMA 目标（stop-grad）<br/>        # 预测器只预测上下文块对目标块的表示<br/>        pred = self.student(x_ctx)                # 简化：实际用 predictor head<br/>        return F.mse_loss(pred, z_t.detach())     # 表示空间回归损失</code>
```

> 工程取舍：**JEPA** 快、省算力、不生成像素，适合做"感知/表征预训练"；**Dreamer** 适合"在想象里练策略"（样本效率）；**扩散世界模型** 适合"造数据/做视频仿真"。EmbodyWeaver 用 JEPA 做视觉表征 + DreamerV3 做策略想象，两套互补。

### 3.4 长程任务规划与组合泛化

**根因**："做一顿饭"需几十步、稀疏奖励、长时序信用分配难，单策略难泛化；且"新任务=已知技能的新组合"，需要把技能当**可组合原语**。

**方案**

1. **LLM 作规划器（SayCan / Inner Monologue）**：LLM 把自然语言目标分解成子目标序列，每个子目标交底层 VLA 执行，并用**可行性**打分过滤不可行动作。
1. **层级 RL（HRL）**：高层 policy 选子目标，底层追子目标，缓解长时序。
1. **技能库组合**：把原子技能（抓取/推/旋）当 API，规划=原语组合，组合泛化。

**数学视角（SayCan 可行性×可达性）**：动作 `a` 被选中的分值 = 语言可行性 × 物理可达性：

```
<code>score(a) = P_LLM(a | 目标, 历史) · P_affordance(a | 当前状态)</code>
```

`P_LLM` 由 LLM 给"这一步是否有助达成目标"打分（语义），`P_affordance` 由价值函数给"这一步物理上能不能做"打分（感知），二者相乘避免"说得好听但做不到"。

**可运行代码：LLM 规划 + 技能检索**

```
<code>import re<br/><br/>def plan_with_skills(goal, state_desc, skill_lib, llm_call):<br/>    """LLM 把目标拆成可执行的技能序列。"""<br/>    prompt = (f"目标：{goal}\n当前状态：{state_desc}\n"<br/>              f"可用技能：{', '.join(skill_lib)}\n"<br/>              f"只输出技能名序列，用 '-&gt;' 连接：")<br/>    seq = llm_call(prompt).strip()<br/>    steps = [s.strip() for s in re.split(r'-&gt;', seq) if s.strip() in skill_lib]<br/>    return steps                 # 例：['抓取红块', '移动到盒子', '放下']<br/><br/>def saycan_score(action, goal, state, llm, value_fn):<br/>    p_llm = llm.prob_helpful(action, goal)        # 语义可行性 ∈[0,1]<br/>    p_aff = value_fn(state, action)               # 物理可达性 ∈[0,1]<br/>    return p_llm * p_aff</code>
```

### 3.5 闭环控制与实时性：大脑慢、手要快

**根因**：大脑（VLM/VLA）推理要 0.1–1s，但手（电机）要毫秒级（100–1000Hz）。开环执行易因扰动/建模误差漂移失败；纯高频控制又缺"语义智能"。二者必须解耦协同。

**方案**：分层异步架构

- **慢思考（1–10Hz）**：VLM 规划 + VLA 出高层目标（如"把壶移到杯口上方 5cm"）。
- **快控制（100–1000Hz）**：阻抗/力控 / 全身控制（WBC）跟踪目标，抗扰动。
- **安全门**：动作超时、力超限即急停；推理线程与执行线程解耦，避免"卡顿→撞物"。

**数学视角（阻抗控制律）**：把末端交互建模为弹簧-阻尼系统，期望交互力 `F` 与位置偏差 `e=x-x_d` 满足：

```
<code>F = M·ẍ + B·ẋ + K·e        # 阻抗 Z = M s² + B s + K</code>
```

`M/B/K` 决定"软硬"。接触任务（插拔/打磨）用低 `K` 高 `B` 顺应；精密定位用高 `K`。力控目标：`F → F_desired`，用 PD：`τ = Jᵀ(F_des - K_p e - K_d ė)`。

**可运行代码：阻抗控制 + 全身控制（简化）**

```
<code>import numpy as np<br/><br/>class ImpedanceController:<br/>    """末端阻抗控制：跟踪期望位姿 + 柔顺接触。"""<br/>    def __init__(self, M, B, K):<br/>        self.M, self.B, self.K = M, B, K       # 质量/阻尼/刚度对角阵<br/>    def step(self, x, x_des, x_dot, F_ext, dt):<br/>        e = x - x_des<br/>        # 期望交互力 = 刚度*偏差 + 阻尼*速度 + 外部力补偿<br/>        F_des = self.K @ e + self.B @ x_dot + F_ext<br/>        # 加速度（质量反解），用于 WBC 下一级<br/>        x_ddot = np.linalg.inv(self.M) @ F_des<br/>        return F_des, x_ddot<br/><br/>class WholeBodyControl:<br/>    """WBC：把任务空间力映射到关节力矩（雅可比转置）。"""<br/>    def __init__(self, J_fn):<br/>        self.J = J_fn                        # 雅可比 J(q): 任务空间←关节<br/>    def command_torque(self, q, F_task, null_ctrl=None):<br/>        J = self.J(q)<br/>        tau = J.T @ F_task                    # 主任务<br/>        if null_ctrl is not None:            # 零空间次级目标（平衡/避障）<br/>            tau += (np.eye(J.shape[1]) - J.T @ np.linalg.pinv(J.T)) @ null_ctrl(q)<br/>        return tau</code>
```

### 3.6 数据引擎：机器人数据稀缺怎么破

**根因**：机器人轨迹数据远少于文本/图像，且真机采集贵、慢、易损、难标注。

**方案**：四路数据供给，把"真机稀缺"变成"仿真/视频充裕"

1. **遥操作（Teleoperation）**：人戴手套/动捕采少量高质量真轨迹（种子）。
1. **仿真合成（MimicGen）**：用少量真轨迹做"目标条件"，在仿真里自动生成海量变体（不同物体/位姿/场景）。
1. **自博弈（RoboAgent）**：策略自我探索，扩覆盖面。
1. **视频学习（Video2Action）**：从人类演示视频学动作先验。
1. **蒸馏**：大模型（70B）动作分布 → 小模型（7B）蒸馏，降推理成本。

**数学视角（覆盖度与规模化）**：任务分布 `D` 的覆盖度随合成数据量 `N` 增长满足 `cover(N) ≥ 1 - δ·e^{-λN}`（指数收敛）；当 `N` 足够大，`δ→0` 即覆盖绝大多数真实场景。合成数据多样性直接决定 Sim2Real 泛化上界——这正是 MimicGen 把"5 条真轨迹 → 5 万条变体"的工程逻辑。

**可运行代码：MimicGen 风格变体生成**

```
<code>import numpy as np, random<br/><br/>def mimicgen_variants(seed_traj, n_variants=1000, rng=None):<br/>    """用一条种子真轨迹，在仿真里随机化物体/位姿/场景生成变体。"""<br/>    rng = rng or random.Random(0)<br/>    out = []<br/>    for _ in range(n_variants):<br/>        # 重置仿真，随机化初始条件但保留"任务结构"<br/>        env = reset_env_with_randomization(rng)<br/>        obj_pose = sample_valid_pose(env, rng)        # 物体在可达域随机<br/>        env.place(seed_traj["obj_name"], obj_pose)<br/>        # 复用种子轨迹的"相对运动"模式，重放到新初始条件<br/>        var_traj = replay_relative(seed_traj, env)<br/>        if is_valid(var_traj):<br/>            out.append(var_traj)<br/>    return out                      # 规模 ×1000，成本 ≈ 1 条真机采集</code>
```

---

---

### Q1：为什么用 LLM/VLM 做机器人，而不用纯 RL？

**答**：纯 RL 在**稀疏奖励 + 长程 +  unseen 物体**上训练极难、泛化差、不可解释。VLM 带来的三个增量：①**语义零样本泛化**——"抓那个蓝色杯子"无需重新训练，靠语言条件；②**先验知识**——互联网视觉/语言预训练迁移到物体识别与常识；③**可组合规划**——自然语言分解任务。本质是"用预训练压缩的世界知识替代从零试错"。但 VLM 不擅长毫秒级控制与精确力控，所以**VLM 负责"想"，RL/控制负责"做"**，二者分层才是工业正解。

### Q2：世界模型为什么必要？JEPA 和扩散世界模型怎么选？

**答**：必要性在三点：①**样本效率**——真实交互贵，用模型想象 rollout 练策略省真实采样；②**长程规划**——能预判"动作→未来状态"才能选最优；③**安全**——在模型里试错不摔机器人。JEPA 在**表示空间**预测、不生成像素，快、省、泛化强，适合表征预训练与感知；扩散世界模型生成**像素级未来帧**，适合造训练数据/视频仿真但算力重。EmbodyWeaver 用 JEPA 做视觉表征 + Dreamer 式 RSSM 做策略想象，扩散模型只用于离线数据扩增。

### Q3：Sim-to-Real 怎么解决？域随机化 vs 系统辨识怎么取舍？

**答**：见 §3.1。DR 不依赖真机、易扩展，但随机范围难定、过度随机会让策略保守；系统辨识精度高但要真机实测、难批量。**工业正解 = 辨识标定名义值 + 在其邻域做 DR**，既准又鲁棒。此外还有：真机微调（few-shot）、域自适应（GAN/CyCADA 对齐特征）、在线 DAgger 补标。

### Q4：连续动作怎么表示？离散 token 还是扩散 policy？

**答**：见 §3.2。离散 token 复用 LLM 栈、易部署，适合低维/中等精度任务（抓取、导航）；扩散 policy 天然多峰、连续、高维，适合精细力控/装配，避免 MSE 均值塌缩。π0 用"VLM 主干 + flow-matching 扩散头"是当前 SOTA：语义靠 VLM、动作靠流匹配。选型看**动作维度与精度要求**。

### Q5：长程任务做到一半失败了，怎么诊断？

**答**：按"感知→规划→执行"三层拆解：①**感知层**——目标检测/分割错了？物体识别漂移？用离线回放 + 真值标注查；②**规划层**——LLM 子目标分解错了（SayCan 可行性打分是否漏判）？技能组合顺序不合理？看规划日志与 `score` 分布；③**执行层**——VLA 动作偏差？力控超限急停？世界模型预测与真实偏差大？看关节轨迹与接触力曲线。定位后：感知问题加数据/校准，规划问题改 prompt/价值函数，执行问题加闭环/重训。

### Q6：触觉/力觉为什么重要？仅靠视觉够吗？

**答**：不够。视觉是**被动、外部、无接触信息**——"插不插得进""捏没捏碎""有没有打滑"视觉看不到或滞后。力觉提供**接触闭环**：插拔装配的插入力、抓取的成功反馈（是否滑落）、易碎物的力上限。工业精密任务（装配/打磨/拿蛋）几乎强制力控。EmbodyWeaver 把触觉编码进表征层（§2.2 L2），与视觉、本体觉三路融合，力控闭环在 L5 跑 100–1000Hz。

---

---

### 面试题 1：设计支持千万台机器人、日百万任务的具身智能平台（EmbodyWeaver）端到端架构

**考点**：把"采集—训练—部署—评测—安全"做成可规模化的闭环，而非单机 demo。  
**参考答案要点**：

- **采集层（L0/L1）**：真机遥操作（5%）+ 仿真合成（95%，MimicGen 风格），数据湖按"任务×物体×场景"分片，去重防污染。
- **训练层（L2–L4）**：VLM 感知基座（复用 VisionLLM）+ VLA 动作头（离散+扩散双头）+ 世界模型（JEPA 表征 + RSSM 想象）；用 Reasoning-RL（GRPO）做长程策略优化；70B 教师蒸馏 7B 学生降成本。
- **部署层（L5/L6）**：端云协同——云端跑 VLA 规划（EdgeLLM 式 INT4 量化），机器人端跑高频阻抗/WBC 控制（100–1000Hz）；ModelRouter 做模型路由与缓存。
- **评测与安全（L6）**：RLBench/真实基准自动化评测 + LLMOps 全链路 Trace + 力限/急停安全门 + 人类回环兜底。
- **规模化**：影子模式（新策略先在仿真/影子真机跑，指标达标再放量）、A/B 灰度、故障自动回滚（沿用第39期 LLMOps 机制）。

### 面试题 2：线上抓取成功率从 92% 突然跌到 40%，30 分钟止血复盘

**考点**：复合故障的分钟级定位 SOP（感知/策略/数据/硬件四路排查）。  
**参考答案要点**：

- **0–5min 止血**：先切影子/回退版本（最坏回退到固定脚本兜底），止住业务损失；同时拉 LLMOps Trace（第39期）看失败分布。
- **5–15min 定位**：①**硬件/传感**——相机脏了？力矩传感器漂移？力控 RMSE 是否暴涨（§3.5）；②**感知**——新批次物体外观变了？物体检测 mAP 掉？③**策略**——VLA 输出动作分布是否异常（奖励 hacking/分布漂移），世界模型预测误差是否突增；④**数据/环境**——光照/桌面换了？Sim2Real 失配？
- **15–30min 修复**：硬件→清洁/标定；感知→加少量真机微调；策略→回退 + 触发 DAgger 补标（§3.1）；环境→域随机化补强。最后灰度放量验证回升到 >90%。

### 面试题 3：7B VLA 经世界模型 + 合成数据追平 70B 教师方案

**考点**：小模型如何在"具身"域以低成本追平大模型（蒸馏 + 世界模型增强 + 合成规模化）。  
**参考答案要点**：

- **蒸馏**：70B VLA 教师输出动作分布/世界模型隐状态，7B 学生用 KL 蒸馏 + 动作 MSE 对齐；教师只在云端训，学生端侧跑。
- **世界模型增强**：学生用 JEPA 表征 + RSSM 想象 rollout 做"免费"数据增强，在想象里练长程策略，样本效率 ×10（§3.3）。
- **合成数据规模化**：MimicGen 把 5 条真轨迹 → 5 万变体（§3.6），覆盖度 `cover(N)→1`，把 Sim2Real 泛化推到 91%。
- **闭环补强**：端侧跑时，力控反馈（§3.5）+ MemoryWeaver（第47期）记环境，错误样本回传云端触发 DAgger 再蒸馏。
- **量化预期**：动作误差 ↓、长程完成率 18%→55%+，端侧延迟满足 100Hz 控制，成本 −85%。

---

---

```
<code>【具身智能 EmbodyWeaver 六层】 仿真/数据 → 表征编码 → 感知理解 → 策略世界 → 控制执行 → 应用评测<br/>【Sim2Real 三板斧】 域随机化 DR + 系统辨识 + DAgger 在线补标<br/>【动作表示三范式】 离散 token(RT/OpenVLA) / 扩散 policy(π0) / 分层混合<br/>【VLA 损失】 离散=-Σlog p(a_i) ；扩散=E_{t,ε}||ε-ε_θ(a_t,o,l,t)||²<br/>【世界模型三类】 JEPA(表示空间) / Dreamer(RSSM想象练策略) / 扩散(像素造数据)<br/>【Dreamer 目标】 J(π)=E[Σ γᵗ rₜ]，在 latent rollout 上优化<br/>【长程规划】 LLM 拆子目标 + SayCan 分值=P_LLM·P_affordance<br/>【快慢解耦】 慢(1-10Hz) VLA规划 ；快(100-1000Hz) 阻抗/WBC力控<br/>【阻抗律】 F = M ẍ + B ẋ + K e （顺应用低K高B，定位用高K）<br/>【数据四路】 遥操作 + MimicGen合成 + 自博弈 + 视频学习 ；覆盖度 1-δe^{-λN}<br/>【串联线】 VisionLLM(看) + Reasoning-RL(训) + Agent Harness(编排) + MemoryWeaver(记)<br/>         + VoiceWeaver(听令) + ContextForge(上下文) → EmbodyWeaver(动手干)</code>
```

> **本期选题说明**：用户指令标题写"1 个模拟面试问题"，但需求 #4 明确"生成 3 个针对性的模拟面试问题"，按 #4 生成 3 道（与近 16 期一致）。3 道模拟题均为具身智能专属角度（千万机器人平台架构 / 抓取成功率暴跌止血 / 7B 追平 70B），不与历史 82 题重复。

---

---