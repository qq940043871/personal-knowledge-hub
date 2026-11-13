# 特殊token

> 模块：Tokenizer分词器
> 更新时间：2026-03-29

## 特殊 token 类型：BOS / EOS / PAD / UNK / MASK / SEP 六类

> 六类特殊 token 各司其职：**BOS 标记开始、EOS 触发停止、PAD 对齐长度、UNK 兜底未知词、MASK 服务 MLM 预训练、SEP 分隔段落**。

```
特殊token体系：
  1. BOS（Beginning of Sequence）
     - 序列开始标记
     - 告诉模型"从此开始生成"

  2. EOS（End of Sequence）
     - 序列结束标记
     - 生成到此token时停止

  3. PAD（Padding）
     - 填充标记
     - 将不同长度的序列对齐到相同长度

  4. UNK（Unknown）
     - 未知token
     - 词表中不存在的token用此替代

  5. MASK
     - 掩码标记
     - BERT等MLM预训练任务使用

  6. SEP（Separator）
     - 分隔标记
     - 分隔不同段落或对话角色
```

*图：六类特殊 token 及其用途（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 280" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <rect x="15" y="20" width="220" height="104" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="125" y="47" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">BOS</text>
  <text x="125" y="67" text-anchor="middle" font-size="12" fill="#475569">Beginning of Sequence</text>
  <text x="125" y="92" text-anchor="middle" font-size="13" fill="#1e293b">序列开始标记</text>
  <text x="125" y="112" text-anchor="middle" font-size="12" fill="#475569">告诉模型"从此开始生成"</text>
  <rect x="250" y="20" width="220" height="104" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">EOS</text>
  <text x="360" y="67" text-anchor="middle" font-size="12" fill="#475569">End of Sequence</text>
  <text x="360" y="92" text-anchor="middle" font-size="13" fill="#1e293b">序列结束标记</text>
  <text x="360" y="112" text-anchor="middle" font-size="12" fill="#475569">生成到此token时停止</text>
  <rect x="485" y="20" width="220" height="104" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="595" y="47" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">PAD</text>
  <text x="595" y="67" text-anchor="middle" font-size="12" fill="#475569">Padding</text>
  <text x="595" y="92" text-anchor="middle" font-size="13" fill="#1e293b">填充标记</text>
  <text x="595" y="112" text-anchor="middle" font-size="12" fill="#475569">将不同长度的序列对齐到相同长度</text>
  <rect x="15" y="148" width="220" height="104" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="125" y="175" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">UNK</text>
  <text x="125" y="195" text-anchor="middle" font-size="12" fill="#475569">Unknown</text>
  <text x="125" y="220" text-anchor="middle" font-size="13" fill="#1e293b">未知token</text>
  <text x="125" y="240" text-anchor="middle" font-size="12" fill="#475569">词表中不存在的token用此替代</text>
  <rect x="250" y="148" width="220" height="104" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="175" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">MASK</text>
  <text x="360" y="220" text-anchor="middle" font-size="13" fill="#1e293b">掩码标记</text>
  <text x="360" y="240" text-anchor="middle" font-size="12" fill="#475569">BERT等MLM预训练任务使用</text>
  <rect x="485" y="148" width="220" height="104" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="595" y="175" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">SEP</text>
  <text x="595" y="195" text-anchor="middle" font-size="12" fill="#475569">Separator</text>
  <text x="595" y="220" text-anchor="middle" font-size="13" fill="#1e293b">分隔标记</text>
  <text x="595" y="240" text-anchor="middle" font-size="12" fill="#475569">分隔不同段落或对话角色</text>
</svg>

## Chat Template 设计：把消息列表拼成模型输入串

> `ChatTemplate` 持有 bos/eos 与 Llama 风格的 `<<SYS>>`、`[INST]` 包裹符；`apply()` 把 system prompt 放进第一轮 user 消息，再按 user/assistant 交替拼接，最后返回以 `<s>` 开头的完整输入串。

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ChatMessage:
    """对话消息"""
    role: str        # system / user / assistant / tool
    content: str


@dataclass
class ChatTemplate:
    """Chat Template定义"""
    bos_token: str = "<s>"
    eos_token: str = "</s>"
    system_prefix: str = "<<SYS>>\n"
    system_suffix: str = "\n<</SYS>>\n\n"
    user_prefix: str = "[INST] "
    user_suffix: str = " [/INST] "
    assistant_suffix: str = " "
    default_system: str = "You are a helpful assistant."

    def apply(self, messages: List[ChatMessage]) -> str:
        """将消息列表转换为模型输入字符串"""
        parts = [self.bos_token]

        # 处理system prompt
        system_msgs = [m for m in messages if m.role == "system"]
        system_text = (system_msgs[0].content
                       if system_msgs else self.default_system)

        # 处理user/assistant对话
        dialog_msgs = [m for m in messages if m.role != "system"]
        for i, msg in enumerate(dialog_msgs):
            if msg.role == "user":
                content = msg.content
                if i == 0:
                    # 第一轮对话包含system prompt
                    content = (f"{self.system_prefix}{system_text}"
                               f"{self.system_suffix}{content}")
                parts.append(f"{self.user_prefix}{content}{self.user_suffix}")
            elif msg.role == "assistant":
                parts.append(f"{msg.content}{self.assistant_suffix}")

        return "".join(parts)


# 使用示例
template = ChatTemplate()
messages = [
    ChatMessage(role="system", system="你是一个Python专家"),
    ChatMessage(role="user", content="什么是装饰器？"),
]
prompt = template.apply(messages)
# <s><<SYS>>
# 你是一个Python专家
# <</SYS>>
#
# 什么是装饰器？ [/INST]
```

## 特殊 token 与训练：注册管理与 MLM 掩码

- `SpecialTokenManager` 维护 **name↔id 双向映射**（special_tokens / token_names），bos/eos/pad 提供 `get_bos_id()` 等默认值（1 / 2 / 0）；
- `is_special_token()` 按 id 判断是否为特殊 token；
- `mask_non_special()` 把序列中的**非特殊 token 替换为 MASK**（默认 id=4），用于 MLM 预训练。

```python
class SpecialTokenManager:
    """特殊token管理器"""

    def __init__(self):
        self.special_tokens: Dict[str, int] = {}
        self.token_names: Dict[int, str] = {}

    def add_special_token(self, name: str, token_str: str,
                          token_id: int):
        """注册特殊token"""
        self.special_tokens[name] = token_id
        self.token_names[token_id] = name

    def get_bos_id(self) -> int:
        return self.special_tokens.get("bos", 1)

    def get_eos_id(self) -> int:
        return self.special_tokens.get("eos", 2)

    def get_pad_id(self) -> int:
        return self.special_tokens.get("pad", 0)

    def is_special_token(self, token_id: int) -> bool:
        """判断是否为特殊token"""
        return token_id in self.token_names

    def mask_non_special(self, token_ids: List[int]) -> List[int]:
        """将非特殊token替换为MASK，用于MLM预训练"""
        mask_id = self.special_tokens.get("mask", 4)
        return [tid if self.is_special_token(tid) else mask_id
                for tid in token_ids]
```

*下一步：Skill架构*
