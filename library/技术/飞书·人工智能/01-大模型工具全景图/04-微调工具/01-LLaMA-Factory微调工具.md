# LLaMA-Factory微调工具

> 模块：微调工具
> 更新时间：2026-03-29

---

## 一、框架介绍与核心特点

LLaMA-Factory是一个**一站式大模型微调平台**，支持多种模型的LoRA、QLoRA等高效微调方法。

**官网**：https://github.com/hiyouga/LLaMA-Factory
**GitHub**：https://github.com/hiyouga/LLaMA-Factory

**核心特点**：
- 支持多种模型（Llama、LLaMA、Qwen、Bloom等）
- 支持多种微调方法（LoRA、QLoRA、Full-tuning）
- Web界面操作
- 命令行工具
- 预置训练模板

---

## 二、快速开始：安装、数据准备与训练

### 1. 安装

```bash
git clone https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e .
```

### 2. 准备数据

LLaMA-Factory 支持两类常用数据格式。**格式1：Alpaca 指令格式**（注意文件内容必须是 JSON 数组，即使只有一条样本）：

```json
[
  {
    "instruction": "将以下中文翻译成英文",
    "input": "今天天气真好",
    "output": "The weather is nice today."
  }
]
```

**格式2：ShareGPT 对话格式**：

```json
{
  "conversations": [
    {"from": "human", "value": "什么是Python？"},
    {"from": "gpt", "value": "Python是一种高级编程语言..."}
  ]
}
```

### 3. Web界面微调

```bash
# 启动Web界面
llamafactory-cli webchat

# 访问 http://localhost:7860
# 选择模型、配置参数、开始训练
```

### 4. 命令行微调

```bash
llamafactory-cli train \
    --stage sft \
    --model_name_or_path meta-llama/Llama-3-8b-Instruct \
    --dataset alpaca_gpt4_zh \
    --template llama3 \
    --finetuning_type lora \
    --lora_target q_proj,v_proj \
    --output_dir ./output/llama3_lora \
    --per_device_train_batch_size 4 \
    --gradient_accumulation_steps 4 \
    --lr_scheduler_type cosine \
    --learning_rate 5e-5 \
    --num_train_epochs 3 \
    --fp16
```

---

## 三、微调方法详解：LoRA / QLoRA / 全参数

### 1. LoRA微调

```yaml
# lora_config.yaml
finetuning_type: lora
lora_alpha: 16
lora_dropout: 0.05
lora_target: all  # 或指定层: [q_proj, k_proj, v_proj, o_proj]
```

### 2. QLoRA微调（量化+LoRA）

```bash
# QLoRA适合显存有限的场景：LoRA + 量化只需 --quantization_bit，无需额外 flag
llamafactory-cli train \
    --stage sft \
    --model_name_or_path meta-llama/Llama-3-8b-Instruct \
    --dataset alpaca_gpt4_zh \
    --template llama3 \
    --finetuning_type lora \
    --quantization_bit 4 \
    --output_dir ./output/llama3_qlora
```

### 3. 全参数微调

```bash
# 全参数微调需要更多显存
llamafactory-cli train \
    --stage sft \
    --model_name_or_path meta-llama/Llama-3-8b-Instruct \
    --dataset alpaca_gpt4_zh \
    --template llama3 \
    --finetuning_type full \
    --output_dir ./output/llama3_full \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 16
```

*图：三种微调方法与显存需求对比（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 280" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="80" y="20" width="560" height="60" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="44" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">QLoRA 微调（量化 + LoRA）</text>
  <text x="360" y="66" text-anchor="middle" font-size="13" fill="#475569">--quantization_bit 4 · 显存需求低，适合显存有限的场景</text>
  <line x1="360" y1="82" x2="360" y2="104" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="80" y="106" width="560" height="60" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="130" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">LoRA 微调</text>
  <text x="360" y="152" text-anchor="middle" font-size="13" fill="#475569">--finetuning_type lora · lora_target: q_proj,v_proj 或 all · 显存需求中等</text>
  <line x1="360" y1="168" x2="360" y2="190" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="80" y="192" width="560" height="60" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="360" y="216" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">全参数微调（Full-tuning）</text>
  <text x="360" y="238" text-anchor="middle" font-size="13" fill="#475569">--finetuning_type full · 显存需求高，需要更多显存</text>
  <text x="40" y="197" text-anchor="middle" font-size="13" fill="#475569">显存</text>
  <text x="40" y="216" text-anchor="middle" font-size="13" fill="#475569">递增</text>
</svg>

---

## 四、训练数据配置：dataset_info.json

在数据目录下的 `dataset_info.json` 中注册自定义数据集：

```json
{
  "my_dataset": {
    "file_name": "my_data.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "conversations",
      "system": "system",
      "tools": "tools"
    }
  }
}
```

```bash
# 使用自定义数据集
llamafactory-cli train \
    --dataset my_dataset \
    --dataset_dir ./data
```

---

## 五、模型推理：导出 LoRA 权重与推理

```bash
# 导出LoRA权重
llamafactory-cli export \
    --model_name_or_path meta-llama/Llama-3-8b-Instruct \
    --adapter_name_or_path ./output/llama3_lora \
    --template llama3 \
    --finetuning_type lora

# Web聊天
llamafactory-cli webchat \
    --model_name_or_path meta-llama/Llama-3-8b-Instruct \
    --adapter_name_or_path ./output/llama3_lora

# 命令行推理：实际子命令是 chat，启动后在交互输入框中输入问题
llamafactory-cli chat \
    --model_name_or_path meta-llama/Llama-3-8b-Instruct \
    --adapter_name_or_path ./output/llama3_lora \
    --template llama3
# 启动后输入：写一首关于春天的诗
```

---

## 六、常见问题：显存不足与训练效果调优

### 显存不足？

```bash
# 使用QLoRA（LoRA + 量化位宽，即上一节的写法）
--finetuning_type lora --quantization_bit 4

# 减小batch_size
--per_device_train_batch_size 2

# 使用更小的模型
--model_name_or_path meta-llama/Llama-3-8b-Instruct
```

### 训练效果不好？

```bash
# 调整学习率
--learning_rate 1e-4  # 通常1e-4到1e-5

# 增加训练轮数
--num_train_epochs 5

# 调整LoRA alpha
--lora_alpha 32
```

---

## 七、总结与学习要点

LLaMA-Factory是**中文开源社区最活跃的微调工具**，Web界面友好，适合快速实验。

**学习要点**：
1. 理解LoRA和QLoRA原理
2. 掌握数据准备格式
3. 熟练使用Web界面
4. 理解训练参数调优
5. 掌握模型导出和推理

### 企业级升级要点

- **数据质量优先**：训练数据先做清洗与去重，指令覆盖度比数量更重要；数据格式必须为合法 JSON（Alpaca 格式是数组）
- **参数即配置**：训练命令用 YAML 配置文件管理并纳入版本控制，避免口口相传的命令行；不使用虚构或不存在的 CLI 参数
- **可复现性**：固定随机种子、记录基座模型版本与 adapter 版本，评估集与训练集严格隔离
- **评测闸门**：微调后先过自动化评测（如 LLaMA-Factory eval 或外部基准），达标才能进入部署流程
- **量化与显存**：显存不足时用 `--quantization_bit 4`（QLoRA），而不是更换不可用的参数；导出前核对 adapter 与基座匹配

> 更多工程化实践（评测基准、灰度发布、成本控制）参见 [70-企业级工程基准](../../06-Agent开发/70-企业级工程基准.md)。

---

*下一步：LangSmith评估平台*
