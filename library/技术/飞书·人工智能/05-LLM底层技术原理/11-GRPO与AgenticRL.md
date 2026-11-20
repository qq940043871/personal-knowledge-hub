# GRPO 与 Agentic RL

> 模块：LLM底层技术原理
> 更新时间：2026-11-15
> 来源：hello-agents（第 11 章）、self-llm（Qwen3 GRPO 实战）
> 定位：[08-微调技术](08-微调技术.md) 讲到 DPO 为止，本篇续讲 GRPO 与 Agentic RL

---

**衔接**：RLHF 三阶段流程（SFT→RM→PPO）、Bradley-Terry 奖励模型与 DPO 闭式推导都在 [08-微调技术](08-微调技术.md) 第 3/4 节，本篇不重复原理。续讲两件事：PPO 之后 LLM 强化学习的主力算法 **GRPO**（组内相对优势、免 critic），以及把「单轮回答打分」扩展成「多步任务完成」的 **Agentic RL**。

---

## 一、从 RLHF/DPO 到 Agentic RL：范式差在哪

四步演进的差别不在「用什么算法」，而在「监督信号从哪来、优化一步还是多步」：

| 阶段 | 监督信号 | 时间跨度 | 优化目标 |
| :--- | :--- | :--- | :--- |
| 预训练 | 文本自监督（下一词预测） | 单步 | 语言规律与世界知识 |
| SFT | 人工标注 (prompt, completion) 对 | 单步 | 模仿：学格式与基线能力 |
| RLHF/DPO | 人类偏好（奖励模型 or 隐式奖励） | 单步（T=1） | 单轮回答质量 |
| Agentic RL | 环境反馈（答案对错/工具成败/任务完成） | 多步（T≫1） | 累积折扣奖励 = 任务完成度 |

RLHF/DPO（学术口径 PBRFT）里状态只有 prompt、行动只有文本生成、答完即打分；Agentic RL 里状态随交互演化（s_t = prompt + 历史观察），行动扩展为 {生成文本, 调用工具}，中间步骤就能拿奖励（工具调用成功 +0.1），最终优化整条轨迹的 Σγ^t·r(s_t, a_t)。**SFT 只能模仿训练数据，RL 靠试错能发现标注里没有的解法**——DeepSeek R1-Zero 的「顿悟时刻」（无人工示范自发学会反思与延长思考）就是这句话的实证。

同一份数据要按训练方法转两种格式（GSM8K：7473 训练 / 1319 测试）：

```python
# GSM8K 的 SFT / RL 两种格式转换（伪代码；完整实现见 hello-agents 工程 code/chapter11/）
raw = {"question": "...48 只鸡卖蛋...", "answer": "48/2=24 ... #### 72"}  # 原始格式：含解题步骤

sft = {"prompt": apply_chat_template(raw["question"]),        # SFT 格式：completion 带完整解题过程
       "completion": "Step 1: ... Final Answer: 72"}          #   —— 教模型「怎么写」：格式、分步、标记

rl = {"prompt": apply_chat_template(raw["question"]),         # RL 格式：只留最终答案做 ground_truth
      "ground_truth": extract_after_hash(raw["answer"])}      #   —— 逼模型「自己想」：不给过程 = 不许抄答案
# ★特殊点1 RL 格式刻意删掉解题过程：奖励只能来自「模型输出 vs ground_truth」的比对——
#   这一刀切下去，才逼出自主推理而不是背诵
```

SFT 先行的原因：预训练模型连「Final Answer:」格式都不会，奖励函数提取不出答案就没有奖励信号，RL 无从谈起。SFT 教格式建立基线，GRPO 在其上优化策略。

---

## 二、GRPO：用组内相对优势替代 critic

PPO 在 LLM 上的痛点：要同时驻留 4 个模型（策略、参考、价值 critic、奖励），显存巨大、超参敏感、训练不稳。GRPO 的减法：**对同一问题采样 G 个答案组成「组」，组内均值当基线，r_i − r̄ 就是优势估计**——critic 网络整个省掉，常驻模型只剩策略 + 参考两个。

```python
# GRPO 单步训练循环（伪代码骨架；完整实现见 hello-agents 工程 code/chapter11/）
def grpo_step(model, ref_model, prompts, num_generations=4, kl_coef=0.05, clip=0.2):
    groups = [model.sample(p, k=num_generations, temperature=0.8) for p in prompts]  # 1) 组采样
    rewards = [[reward_fn(p, ans) for ans in g] for p, g in zip(prompts, groups)]    # 2) 规则奖励打分
    # ★特殊点1 组内基线是 GRPO 的全部精髓：advantage = r_i − r̄_group，均值即 baseline，
    #   组内比较同时压掉了奖励方差——不需要价值网络估计 V(s)
    advantages = [[r - mean(rs) for r in rs] for rs in rewards]
    # ★特殊点2 组内全对/全错 → 奖励全相等 → 优势全 0 → 这组贡献不了梯度。
    #   题目要卡在模型「有时对有时错」的难度带；全错的题跳过换下一道，别把采样预算烧在零信号组上
    loss = -clipped_ratio_objective(model, ref_model, groups, advantages, clip) \
           + kl_coef * kl_divergence(model, ref_model, groups)   # KL 惩罚防漂移（kl_coef 建议 0.05~0.1）
    loss.backward(); optimizer.step()
    # ★特殊点3 免 critic 省的不只是显存：4 模型 → 2 模型少一半驻留、少一个要同步训练的网络，
    #   超参面和崩溃面同时收窄；代价是优势估计粗（组均值当基线），靠加大 num_generations（4~8）换平滑
```

| 特性 | PPO | GRPO |
| :--- | :--- | :--- |
| 优势估计 | critic 网络：A = Q − V | 组内相对：r_i − r̄ |
| 常驻模型 | 策略+参考+价值+奖励 4 个 | 策略+参考 2 个（奖励用规则函数） |
| 显存/工程复杂度 | 高、超参敏感 | 低、更稳 |
| 训练信号 | 绝对奖励 | 「比组内平均更好」的相对信号 |

监控三个数的健康区间：KL 0.01~0.1（>0.5 策略跑飞、<0.001 几乎没学）；平均奖励应缓升（先升后崩 = 过拟合或奖励被 hack）；准确率是唯一诚实的指标。

---

## 三、奖励函数设计：RL 的「标注」

奖励函数就是 RL 里的标注员——写错一个正则，模型就把错误行为学到底。三类基础奖励 + 组合：

```python
# 组合奖励函数（伪代码骨架；完整实现见 hello-agents 工程 code/chapter11/，权重口径参考 self-llm Qwen3 GRPO）
SOLUTION_RE = re.compile(r"<SOLUTION>(.+?)</SOLUTION>")       # 结构化标签提取，别赌「最后一个数字」

def normalize(text: str) -> str:                              # 归一化契约：比对前先过这里
    # ★特殊点3 数值比较必须先归一化（精度/单位/分隔符/格式）再比——「72.0 vs 72」「1k vs 1000」
    #   判错会系统性错杀正确答案，奖励噪声直接进梯度
    t = text.strip().replace(",", "")                        # 千位分隔符：123,456 → 123456
    return {"1k": "1000", "1K": "1000"}.get(t, t)            # 单位简写展开；72.0 与 72 用 float 比对

def combined_reward(completions, ground_truths, gen_lengths, step_counts):
    scores = []
    for ans, truth, length, steps in zip(completions, ground_truths, gen_lengths, step_counts):
        match = SOLUTION_RE.search(ans)
        if match is None:
            scores.append(-2.0); continue        # ★特殊点1 提取失败给负奖励而不是 0——
                                                 #   给 0 等于默许「乱写一气」，负分才压得住格式
        try:
            acc = 1.0 if float(normalize(match.group(1))) == float(normalize(truth)) else 0.0
        except (ValueError, TypeError):      # ★特殊点4 禁裸 except：捕获具体类型并落日志——
            acc = 0.0                        #   解析失败率本身就是要监控的指标，吞掉它 = 吞掉第一个奖励欺骗信号
        # ★特殊点2 长度惩罚与步骤奖励只在答案正确时施加：r = r_acc − α·max(0, l−l_target) + β·s
        #   否则模型学出「答错的超短答案」/「狂堆 Step 标记的废话」来白拿惩罚减免和步骤分
        length_pen = 0.001 * max(0, length - 200) if acc else 0.0     # α=0.001，目标长度 200
        step_bonus  = min(0.1 * steps, 0.3) if acc else 0.0           # β=0.1，封顶防刷步数
        scores.append(1.0 * acc + 0.5 * (-length_pen) + 0.3 * step_bonus)  # 准确率权重主导
    return scores
```

### 奖励欺骗（reward hacking）：典型形态与防御

| 形态 | 模型怎么钻空子 | 防御 |
| :--- | :--- | :--- |
| 步骤刷分 | 狂堆「Step n:」标记骗步骤奖励 | 步骤分只在答案正确时给 + 封顶 |
| 提取投机 | 末尾塞一串数字，赌「取最后一个数字」的正则 | 结构化标签提取；提取失败给负奖励 |
| 格式分失衡 | 只输出标准格式不解题，靠格式分过活 | 格式权重 ≪ 正确权重（3 vs 5 量级） |
| 容差赌博 | ±10% 数值容差被拿来蒙答案 | 容差档位递减（+2.0/+1.5）且错太远倒扣 |

防御的兜底是监控口径：**奖励曲线涨而准确率曲线不涨 = 正在被 hack**——两条曲线分开画、差值挂报警， hack 一出现先审奖励函数再怀疑训练。

---

## 四、SFT→GRPO 实战：框架选型与两段式流程

| 框架 | 定位 | 适合谁 |
| :--- | :--- | :--- |
| TRL | HuggingFace 官方 RL 库，GRPOTrainer 开箱即用 | 通用首选，hello-agents 用它 |
| VeRL | 字节基于 ray 的大规模分布式 RL | 2 卡起步的集群场景，学习成本高 |
| Unsloth | 极致省资源：提速 2x、省显存 70% | 单卡党；self-llm 实测 8B 单卡可跑 GRPO |

```python
# SFT + LoRA → GRPO 两段式流程（伪代码骨架；完整实现见 self-llm models/Qwen3/10-Qwen3_8B_GRPO.ipynb）
import os
model, tokenizer = FastLanguageModel.from_pretrained(
    "Qwen/Qwen3-8B", max_seq_length=2048, lora_rank=32,
    fast_inference=True, gpu_memory_utilization=0.7)          # vLLM 快速推理；OOM 先调低此值

# 阶段一 SFT：自定义 CoT 标签（<start_working_out>…<end_working_out><SOLUTION>…）进 chat_template，
#   在带解题过程的数据上学格式（SFT lr≈2e-4，LoRA alpha=2r，目标模块含 attention+MLP）
# 阶段二 GRPO：换 RL 格式数据 + 规则奖励函数列表
trainer = GRPOTrainer(model=model, reward_funcs=[format_reward, answer_reward],
                      args=GRPOConfig(learning_rate=5e-6,      # ★特殊点1 GRPO 学习率比 SFT 低 1~2 个量级：
                                       num_generations=4,      #   RL 怕跑飞，SFT 怕不收敛，量级不同
                                       max_steps=100,
                                       report_to="swanlab"))   # API key 只走 os.environ["SWANLAB_API_KEY"]

# ★特殊点2 chat_template 的标签与奖励函数的正则必须同源——模板里定义 <SOLUTION>，奖励函数就按它提取；
#   两处各写一套，格式分和答案分全归零
# ★特殊点3 num_generations 越大组内基线越平滑，但生成显存按 G 线性涨——OOM 先砍它，再砍 batch，
#   最后砍 max_completion_length；有效 batch 必须能被 num_generations 整除（一组答案必须同步采样才共享同一个基线）
```

---

## 五、分布式与部署

- **方案选择**：单机 2-8 卡用 DDP；>7B 用 DeepSpeed ZeRO-2/ZeRO-3；多节点集群用 ZeRO-3 + Offload（优化器/参数卸载 CPU）。TRL + Accelerate 下训练代码不变，只换 launch 配置。
- **参数换算**：总 batch = per_device × 卡数 × gradient_accumulation——扩卡后按 sqrt(新 batch/旧 batch) 缩放学习率，保持有效 batch 不变则学习率不动。
- **部署**：LoRA 先 merge 回基座（merge_and_unload），再走 vLLM 服务或导出 GGUF（q4_k_m 平衡精度与速度、q8_0 精度敏感场景）；GRPO 的 LoRA 权重保存后要验证非全零（训练没生效的静默坑）。

### 企业级升级要点

- **奖励改一行，评测先回归**：奖励函数任何改动（权重/阈值/正则）先在固定评测集上重放历史生成、全判中才合入——与 [70-企业级工程基准](../06-Agent开发/70-企业级工程基准.md) RAG #15「评测先行回归门禁」同一纪律。
- **采样预算在代码里熔断**：GRPO 单步成本 ≈ prompt 数 × num_generations × max_new_tokens 个 token 的生成开销，G 与 max_steps 必须在配置里硬约束，不靠训练脚本自觉（公共约定 #5 预算硬约束）。
- **奖励与准确率分开监控**：reward 涨 / accuracy 不涨即报警并冻结训练，先审奖励函数再续跑——reward hacking 的最早信号在两条曲线的剪刀差里。
- **密钥与异常的公共纪律**：wandb/swanlab API key 只走 os.environ、缺失给可行动报错（公共约定 #1）；奖励函数的解析异常捕获具体类型并落日志，禁裸 except，提取失败率要可统计。
- **训练可复现**：固定 seed（采样与初始化都要）、奖励打分抽样进日志、checkpoint 按 save_steps 落盘——出问题时能回放到具体一步。

[70-企业级工程基准](../06-Agent开发/70-企业级工程基准.md)

---

*衔接：DDP/ZeRO 细节见 [10-分布式训练](10-分布式训练.md)，量化与推理优化见 [09-推理优化](09-推理优化.md)；SFT/LoRA/RLHF/DPO 基础见 [08-微调技术](08-微调技术.md)。*
