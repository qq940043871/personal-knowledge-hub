# KV-Cache

> 模块：Attention机制
> 更新时间：2026-03-29

---

## 一、Cache原理

```text
KV-Cache：
  - 缓存已计算的Key和Value
  - 避免重复计算
  - 加速自回归生成

标准attention：O(n²) 每次生成
KV-Cache：O(n) 每次生成

原理：
  生成第n个token时，只需要计算新的Q、K、V
  K、V可以复用之前缓存的结果
```

---

## 二、带KV-Cache的生成实现

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"   # 教学用小模型（公开仓库、无需申请权限）


def compare_kv_cache(prompt: str, max_new_tokens: int = 32) -> None:
    """对比：无缓存逐步 decode vs 有缓存单步 decode（真实 HF 写法）"""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.float16, device_map="auto")
    model.eval()

    input_ids = tokenizer(prompt, return_tensors="pt")["input_ids"].to(model.device)
    eos_token_id = tokenizer.eos_token_id     # 判停 token 从 tokenizer 获取

    # ── 方式一：无缓存——每步都把整个序列重新前向，总计算量 O(n²) ──
    ids_no_cache = input_ids.clone()
    for _ in range(max_new_tokens):
        with torch.no_grad():
            out = model(input_ids=ids_no_cache, use_cache=False)
        next_token = out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        ids_no_cache = torch.cat([ids_no_cache, next_token], dim=-1)
        if next_token.item() == eos_token_id:
            break

    # ── 方式二：KV-Cache——历史 K/V 复用，每步只前向最新的 1 个 token ──
    ids_cache = input_ids.clone()
    past_key_values = None
    cur = input_ids                           # 第一步喂整个 prompt
    for _ in range(max_new_tokens):
        with torch.no_grad():
            # model(...) 返回 CausalLMOutputWithPast：
            #   out.logits         — 词表 logits（取最后一位做采样）
            #   out.past_key_values — 各层缓存的 K/V，直接传回下一步
            out = model(input_ids=cur,
                        past_key_values=past_key_values,
                        use_cache=True)
        past_key_values = out.past_key_values  # 缓存滚动更新
        next_token = out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        ids_cache = torch.cat([ids_cache, next_token], dim=-1)
        if next_token.item() == eos_token_id:
            break
        cur = next_token                       # 之后每步只喂 1 个新 token

    print("无缓存:", tokenizer.decode(ids_no_cache[0]))
    print("有缓存:", tokenizer.decode(ids_cache[0]))


# 调用（示意）：compare_kv_cache("解释一下什么是注意力机制：")
```

两条路径输出一致（贪婪解码下逐 token 相同），但计算量差别巨大：无缓存第 t 步要重算前 t-1 个 token 的全部 K/V；有缓存第 t 步只算第 t 个 token 的 Q/K/V，历史 K/V 从 `past_key_values` 里直接读。这正是 02-批量推理 与 04-GPU推理 中生产引擎（vLLM 的 PagedAttention）的底层基础。

---

### 企业级升级要点

- **用真实 API 而非臆想接口**：演示代码直接跑得通（`CausalLMOutputWithPast` + `past_key_values`）——可运行、可验证是知识库代码的底线，对应 `ai-agent-harness/tests/` 的可测性约定。
- **判停条件显式初始化**：`eos_token_id` 从 tokenizer 获取再参与判停——不隐式假设全局状态，与 harness 构造器注入风格一致（`harness/provider/`）。
- **缓存语义清晰**：`cur` 只喂新 token、hidden 与 K/V 不混拼，状态更新全部经过显式变量——类比 Agent 循环中消息历史只通过 append/extend 维护（`harness/main_loop.py`）。
- **等价性可验证**：两条解码路径结果一致，是重构前的对照基线——参考 `harness/benchmark.py` 先建基准再优化的流程。
- **工程延伸**：显存中 K/V 随序列线性增长，长上下文服务需配额管理——对应 `harness/context_compactor.py` 的上下文预算思想（token 是稀缺资源）。

参考：[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：Flash-Attention*
