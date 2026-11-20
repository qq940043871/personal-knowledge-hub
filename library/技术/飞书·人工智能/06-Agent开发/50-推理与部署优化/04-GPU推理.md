# GPU推理

> 模块：部署优化
> 更新时间：2026-03-29

---

## 一、CUDA加速

```python
# GPU 推理（伪代码：重点在加载与生成参数的特殊点；完整实现见 ownrag/harness 工程）
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class GPUInference:
    """GPU 推理：cuda 不可用时回退 CPU，代码路径保持一致"""

    def __init__(self, model_path: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        #   ★特殊点1 加载即定型：torch_dtype=float16（显存约减半）+ device_map="auto"
        #     由 accelerate 自动分布到可用 GPU（此时无需再 .to(device)）；
        #     显存不足可叠加 03-模型量化 的 4bit 配置
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype=torch.float16, device_map="auto")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

    def generate(self, input_ids, max_new_tokens: int = 128,
                 temperature: float = 1.0, do_sample: bool = True):
        #   ★特殊点2 参数显式签名：替代 **kwargs 任意透传，
        #     非法配置在接入期就报错，而不是运行时才暴露
        with torch.no_grad():
            return self.model.generate(
                input_ids.to(self.model.device),
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id,  # 开采样时 HF 必需，eos 兜底
            )
```

---

## 二、vLLM

```python
from vllm import LLM, SamplingParams

#   ★特殊点3 硬件拓扑可配置：tensor_parallel_size（张量并行度 = GPU 数）走构造参数
#     下发而非写死，取值取决于模型大小、单卡显存与机器拓扑
llm = LLM(model=model_path, tensor_parallel_size=tensor_parallel_size)

# 采样参数显式声明（一行示例）：**kwargs 任意透传会把非法键名藏到运行时，
# 显式签名让配置错误在接入期就暴露
sampling_params = SamplingParams(max_tokens=128, temperature=0.7, top_p=0.9)
outputs = llm.generate(prompts, sampling_params)
texts = [o.outputs[0].text for o in outputs]
```

---

### 企业级升级要点

- **参数显式签名**：生成/采样参数用显式形参替代 `**kwargs` 透传，非法配置在接入期即报错——与 harness 工具注册「签名即契约」的思想一致（`ai-agent-harness/harness/tools/base.py` 的 `infer_schema`）。
- **硬件拓扑可配置**：`tensor_parallel_size` 走构造参数/配置下发而非硬编码——对应 `ai-agent-harness/config/config.yaml.example` 的外置配置模式。
- **设备选择有回退**：`cuda` 不可用时回退 CPU 并保持代码路径一致；`device_map="auto"` 让多卡分配交给 accelerate——生产部署同样应声明最小依赖假设。
- **判停与截断有界**：`max_new_tokens` 上限对应 Agent 主循环的 max_turns 预算思想——一切生成/执行都要有上界（`ai-agent-harness/harness/main_loop.py`）。
- **离线验证**：接入 vLLM 前后用同一批 prompt 做输出对比，参考 `ai-agent-harness/harness/benchmark.py` 的基准流程。

参考：[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：分布式部署*
