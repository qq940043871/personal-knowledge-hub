# Multi-Head-Attention

> 模块：Attention机制  
> 更新时间：2026-03-29

---

---

```
<code>import math<br/>from typing import Tuple<br/><br/>import torch<br/>import torch.nn as nn<br/>import torch.nn.functional as F<br/><br/>Tensor = torch.Tensor<br/><br/><br/>class MultiHeadAttention(nn.Module):<br/>    """多头注意力"""<br/><br/>    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.1):<br/>        super().__init__()<br/>        assert embed_dim % num_heads == 0<br/><br/>        self.embed_dim = embed_dim<br/>        self.num_heads = num_heads<br/>        self.head_dim = embed_dim // num_heads<br/><br/>        # QKV线性变换<br/>        self.q_proj = nn.Linear(embed_dim, embed_dim)<br/>        self.k_proj = nn.Linear(embed_dim, embed_dim)<br/>        self.v_proj = nn.Linear(embed_dim, embed_dim)<br/>        self.out_proj = nn.Linear(embed_dim, embed_dim)<br/><br/>        self.dropout = nn.Dropout(dropout)<br/><br/>    def split_heads(self, x: Tensor, batch_size: int) -&gt; Tensor:<br/>        """分多头"""<br/>        x = x.view(batch_size, -1, self.num_heads, self.head_dim)<br/>        return x.transpose(1, 2)<br/><br/>    def forward(self, x: Tensor, mask: Tensor = None) -&gt; Tuple[Tensor, Tensor]:<br/>        batch_size = x.size(0)<br/><br/>        # QKV投影<br/>        Q = self.q_proj(x)<br/>        K = self.k_proj(x)<br/>        V = self.v_proj(x)<br/><br/>        # 分多头<br/>        Q = self.split_heads(Q, batch_size)<br/>        K = self.split_heads(K, batch_size)<br/>        V = self.split_heads(V, batch_size)<br/><br/>        # 缩放点积注意力<br/>        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)<br/><br/>        if mask is not None:<br/>            scores = scores.masked_fill(mask == 0, -1e9)<br/><br/>        attn_weights = F.softmax(scores, dim=-1)<br/>        attn_weights = self.dropout(attn_weights)<br/><br/>        # 聚合<br/>        context = torch.matmul(attn_weights, V)<br/>        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.embed_dim)<br/>        output = self.out_proj(context)<br/><br/>        return output, attn_weights</code>
```

---

---

- **依赖显式声明**：`import math / torch / nn / F / typing` 齐全，代码块独立可读可跑——知识库代码的最小标准，对应 `ai-agent-harness/tests/` 可执行验证的约定。
- **实现对照生产**：本篇是教学实现；生产应直接用 `nn.MultiheadAttention` / SDPA（`torch.nn.functional.scaled_dot_product_attention`），或 FlashAttention（见下一篇）。
- **张量形状即契约**：`split_heads` 的 view/transpose 链路形状明确——与 harness「签名即 schema」的显式契约思想一致（`ai-agent-harness/harness/tools/base.py`）。
- **mask 语义可扩展**：`masked_fill(mask == 0, -1e9)` 支持任意 0/1 掩码，因果掩码在 KV-Cache 篇与下一篇中体现。

参考：70-企业级工程基准

---

---