# GPU推理

> 模块：部署优化  
> 更新时间：2026-03-29

---

---

```
<code># GPU 推理（伪代码：重点在加载与生成参数的特殊点；完整实现见 ownrag/harness 工程）<br/>import torch<br/>from transformers import AutoModelForCausalLM, AutoTokenizer<br/><br/><br/>class GPUInference:<br/>    """GPU 推理：cuda 不可用时回退 CPU，代码路径保持一致"""<br/><br/>    def __init__(self, model_path: str):<br/>        self.device = "cuda" if torch.cuda.is_available() else "cpu"<br/>        #   ★特殊点1 加载即定型：torch_dtype=float16（显存约减半）+ device_map="auto"<br/>        #     由 accelerate 自动分布到可用 GPU（此时无需再 .to(device)）；<br/>        #     显存不足可叠加 03-模型量化 的 4bit 配置<br/>        self.model = AutoModelForCausalLM.from_pretrained(<br/>            model_path, torch_dtype=torch.float16, device_map="auto")<br/>        self.tokenizer = AutoTokenizer.from_pretrained(model_path)<br/><br/>    def generate(self, input_ids, max_new_tokens: int = 128,<br/>                 temperature: float = 1.0, do_sample: bool = True):<br/>        #   ★特殊点2 参数显式签名：替代 **kwargs 任意透传，<br/>        #     非法配置在接入期就报错，而不是运行时才暴露<br/>        with torch.no_grad():<br/>            return self.model.generate(<br/>                input_ids.to(self.model.device),<br/>                max_new_tokens=max_new_tokens,<br/>                temperature=temperature,<br/>                do_sample=do_sample,<br/>                pad_token_id=self.tokenizer.eos_token_id,  # 开采样时 HF 必需，eos 兜底<br/>            )</code>
```

---

---

```
<code>from vllm import LLM, SamplingParams<br/><br/>#   ★特殊点3 硬件拓扑可配置：tensor_parallel_size（张量并行度 = GPU 数）走构造参数<br/>#     下发而非写死，取值取决于模型大小、单卡显存与机器拓扑<br/>llm = LLM(model=model_path, tensor_parallel_size=tensor_parallel_size)<br/><br/># 采样参数显式声明（一行示例）：**kwargs 任意透传会把非法键名藏到运行时，<br/># 显式签名让配置错误在接入期就暴露<br/>sampling_params = SamplingParams(max_tokens=128, temperature=0.7, top_p=0.9)<br/>outputs = llm.generate(prompts, sampling_params)<br/>texts = [o.outputs[0].text for o in outputs]</code>
```

---

---

- **参数显式签名**：生成/采样参数用显式形参替代 `**kwargs` 透传，非法配置在接入期即报错——与 harness 工具注册「签名即契约」的思想一致（`ai-agent-harness/harness/tools/base.py` 的 `infer_schema`）。
- **硬件拓扑可配置**：`tensor_parallel_size` 走构造参数/配置下发而非硬编码——对应 `ai-agent-harness/config/config.yaml.example` 的外置配置模式。
- **设备选择有回退**：`cuda` 不可用时回退 CPU 并保持代码路径一致；`device_map="auto"` 让多卡分配交给 accelerate——生产部署同样应声明最小依赖假设。
- **判停与截断有界**：`max_new_tokens` 上限对应 Agent 主循环的 max_turns 预算思想——一切生成/执行都要有上界（`ai-agent-harness/harness/main_loop.py`）。
- **离线验证**：接入 vLLM 前后用同一批 prompt 做输出对比，参考 `ai-agent-harness/harness/benchmark.py` 的基准流程。

参考：70-企业级工程基准

---

---