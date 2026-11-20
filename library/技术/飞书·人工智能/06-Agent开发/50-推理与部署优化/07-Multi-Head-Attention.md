# Multi-Head-Attention

> 模块：Attention机制
> 更新时间：2026-03-29

---

## 一、多头注意力

```python
import math
from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

Tensor = torch.Tensor


class MultiHeadAttention(nn.Module):
    """多头注意力"""

    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        assert embed_dim % num_heads == 0

        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        # QKV线性变换
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)

        self.dropout = nn.Dropout(dropout)

    def split_heads(self, x: Tensor, batch_size: int) -> Tensor:
        """分多头"""
        x = x.view(batch_size, -1, self.num_heads, self.head_dim)
        return x.transpose(1, 2)

    def forward(self, x: Tensor, mask: Tensor = None) -> Tuple[Tensor, Tensor]:
        batch_size = x.size(0)

        # QKV投影
        Q = self.q_proj(x)
        K = self.k_proj(x)
        V = self.v_proj(x)

        # 分多头
        Q = self.split_heads(Q, batch_size)
        K = self.split_heads(K, batch_size)
        V = self.split_heads(V, batch_size)

        # 缩放点积注意力
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)

        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # 聚合
        context = torch.matmul(attn_weights, V)
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.embed_dim)
        output = self.out_proj(context)

        return output, attn_weights
```

---

### 企业级升级要点

- **依赖显式声明**：`import math / torch / nn / F / typing` 齐全，代码块独立可读可跑——知识库代码的最小标准，对应 `ai-agent-harness/tests/` 可执行验证的约定。
- **实现对照生产**：本篇是教学实现；生产应直接用 `nn.MultiheadAttention` / SDPA（`torch.nn.functional.scaled_dot_product_attention`），或 FlashAttention（见下一篇）。
- **张量形状即契约**：`split_heads` 的 view/transpose 链路形状明确——与 harness「签名即 schema」的显式契约思想一致（`ai-agent-harness/harness/tools/base.py`）。
- **mask 语义可扩展**：`masked_fill(mask == 0, -1e9)` 支持任意 0/1 掩码，因果掩码在 KV-Cache 篇与下一篇中体现。

参考：[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：KV-Cache*
