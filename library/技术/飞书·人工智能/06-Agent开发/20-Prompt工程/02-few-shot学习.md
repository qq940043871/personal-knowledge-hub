# few-shot学习

> 模块：Prompt工程
> 更新时间：2026-03-29

---

## Few-Shot策略：用示例教会模型任务格式

核心思路：**提供 1~N 个「输入 → 输出」示例，让模型照着格式完成第 N+1 个输入**。示例要有代表性、格式要一致、3~5 个通常足够，并覆盖边界情况。

```
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
```

---

## 示例管理器：拼装示例的两种 Prompt 形态

核心思路：**`build_prompt` 把示例格式化后拼接成一段文本提示；`build_messages` 则把每对示例转成 user/assistant 消息交替的对话格式**。

```python
class FewShotManager:
    """Few-Shot示例管理器"""

    def __init__(self, template: str):
        self.template = template
        self.examples: List[Dict] = []

    def add_example(self, input_text: str, output_text: str):
        """添加示例"""
        self.examples.append({
            "input": input_text,
            "output": output_text
        })

    def build_prompt(self, query: str, n: int = None) -> str:
        """构建Few-Shot提示"""
        if n is None:
            n = len(self.examples)

        examples_text = []
        for ex in self.examples[:n]:
            examples_text.append(self.template.format(
                input=ex["input"], output=ex["output"]
            ))

        return "\n\n".join(examples_text) + f"\n\n{self.template.format(input=query, output='')}"

    def build_messages(self, query: str, n: int = None) -> List[Dict]:
        """构建消息格式"""
        messages = []
        for ex in self.examples[:n or len(self.examples)]:
            messages.append({"role": "user", "content": ex["input"]})
            messages.append({"role": "assistant", "content": ex["output"]})
        messages.append({"role": "user", "content": query})
        return messages
```

---

*下一步：CoT思维链*
