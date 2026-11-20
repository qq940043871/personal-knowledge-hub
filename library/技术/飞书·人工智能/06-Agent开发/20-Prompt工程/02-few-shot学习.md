# few-shot学习

> 模块：Prompt工程
> 更新时间：2026-11-15

---

## Few-Shot策略：用示例教会模型任务格式

核心思路：**提供 1~N 个「输入 → 输出」示例，让模型照着格式完成第 N+1 个输入**。示例要有代表性、格式要一致、3~5 个通常足够，并覆盖边界情况。

```text
Few-Shot示例：
  提供1-N个示例帮助模型理解任务

示例格式：
  输入 → 输出
  输入 → 输出
  输入 → ?

最佳实践：
  1. 示例要有代表性
  2. 格式要一致
  3. 3-5个示例通常足够
  4. 示例要覆盖边界情况
  5. 查询收尾只给输入——不给「空输出」让模型模仿
```

---

## 示例管理器：拼装示例的两种 Prompt 形态

核心思路：**`build_prompt` 把示例格式化后拼接成一段文本提示，查询以「用户消息」形态收尾（不渲染输出槽位）；`build_messages` 则把每对示例转成 user/assistant 消息交替的对话格式，查询是最后一条 user 消息**。

**为什么要「用户消息收尾」**：若把查询也套进示例模板并配 `output=''`，Prompt 尾巴上就挂着「输出：」后跟空串——模型会把「输出后是空」也当成要模仿的格式，倾向输出空内容。查询只给输入，输出由模型补全。

```python
from typing import Dict, List, Optional


class FewShotManager:
    """Few-Shot示例管理器"""

    MAX_EXAMPLES = 10  # 示例不是越多越好：挤占上下文预算，后例还会稀释前例信号

    def __init__(self, template: str):
        self.template = template
        self.examples: List[Dict] = []

    def add_example(self, input_text: str, output_text: str):
        """添加示例"""
        self.examples.append({
            "input": input_text,
            "output": output_text
        })

    def _validate_n(self, n: Optional[int]) -> int:
        """示例数上限校验：超上限/非法值直接报可行动错误"""
        if n is None:
            n = len(self.examples)
        if n < 1:
            raise ValueError(f"示例数 n={n} 必须 >= 1")
        if n > self.MAX_EXAMPLES:
            raise ValueError(
                f"示例数 n={n} 超过上限 {self.MAX_EXAMPLES}：示例挤占上下文预算，"
                f"精选而非堆量（3~5 个通常足够）"
            )
        return n

    def build_prompt(self, query: str, n: int = None) -> str:
        """构建Few-Shot提示：示例带完整输入输出，查询只带输入"""
        n = self._validate_n(n)

        examples_text = []
        for ex in self.examples[:n]:
            examples_text.append(self.template.format(
                input=ex["input"], output=ex["output"]
            ))

        # 用户消息收尾形态：查询不渲染输出槽位，避免模型模仿「空输出」
        return "\n\n".join(examples_text) + f"\n\n用户输入：{query}"

    def build_messages(self, query: str, n: int = None) -> List[Dict]:
        """构建消息格式：示例转 user/assistant 交替，查询是最后一条 user 消息"""
        n = self._validate_n(n)

        messages = []
        for ex in self.examples[:n]:
            messages.append({"role": "user", "content": ex["input"]})
            messages.append({"role": "assistant", "content": ex["output"]})
        messages.append({"role": "user", "content": query})
        return messages
```

### 企业级升级要点

- **示例吃上下文预算**：示例条数与块数共享生成窗口——示例太多会挤掉检索证据（最坏先被截掉的是问题），预算口径见 `ai-rag-self-engineering/ownrag/ownrag/generate/budget.py`。
- **Few-Shot 教格式不教事实**：示例用于固定输出形态，事实必须来自检索证据并过引用校验——见 `ai-rag-self-engineering/ownrag/ownrag/generate/gates.py` 的 `citation_check`。
- **输出形态与解析器对齐**：模型照示例输出后，下游必须有解析/校验承接（如 JSON schema 校验），见 `ai-rag-self-engineering/ownrag/ownrag/generate/gates.py` 的 `schema_check`。
- **Prompt 版本化**：含示例的模板文件进 Git、随评测集回归——改示例 = 改行为，必须可回滚，见 `ai-rag-self-engineering/ownrag/ownrag/generate/prompts.py`。

[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：CoT思维链*
