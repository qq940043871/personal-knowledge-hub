# CoT思维链

> 模块：Prompt工程
> 更新时间：2026-03-29

---

本文覆盖 CoT（Chain-of-Thought）的原理与三种实现方式：**Zero-shot CoT**、**Few-shot CoT**、**Self-Consistency**。

## 一、Chain-of-Thought原理

> CoT 让模型在给出答案前**展示推理过程**，显著提升复杂推理任务的准确率（2022 年 Google Brain 提出）。核心思想：传统 Prompt 是"问题 → 答案"，CoT Prompt 是"问题 → 推理步骤1 → 推理步骤2 → … → 答案"。适用场景：数学推理、逻辑推理、多步骤问题、常识推理。

*图：CoT 三种实现方式（示意）*

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="230" y="20" width="260" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="15" fill="#1e293b">CoT 思维链的三种实现</text>
  <line x1="330" y1="64" x2="130" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="64" x2="360" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="390" y1="64" x2="590" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="30" y="110" width="200" height="96" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="130" y="136" text-anchor="middle" font-size="14" fill="#1e293b">Zero-shot CoT</text>
  <text x="130" y="160" text-anchor="middle" font-size="13" fill="#475569">「让我们一步步思考」</text>
  <text x="130" y="180" text-anchor="middle" font-size="13" fill="#475569">直接触发推理</text>
  <rect x="260" y="110" width="200" height="96" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="136" text-anchor="middle" font-size="14" fill="#1e293b">Few-shot CoT</text>
  <text x="360" y="160" text-anchor="middle" font-size="13" fill="#475569">提供带推理过程的示例</text>
  <text x="360" y="180" text-anchor="middle" font-size="13" fill="#475569">问题→推理→答案</text>
  <rect x="490" y="110" width="200" height="96" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="590" y="136" text-anchor="middle" font-size="14" fill="#1e293b">Self-Consistency</text>
  <text x="590" y="160" text-anchor="middle" font-size="13" fill="#475569">多次采样推理路径</text>
  <text x="590" y="180" text-anchor="middle" font-size="13" fill="#475569">多数票选出答案</text>
</svg>
```

```
CoT（Chain-of-Thought）：
  - 让模型在给出答案前展示推理过程
  - 显著提升复杂推理任务的准确率
  - 2022年Google Brain提出

核心思想：
  传统Prompt：问题 → 答案
  CoT Prompt：问题 → 推理步骤1 → 推理步骤2 → ... → 答案

适用场景：
  - 数学推理
  - 逻辑推理
  - 多步骤问题
  - 常识推理
```

---

## 二、Zero-shot CoT

> **Zero-shot CoT**：不给示例，直接在问题后追加"让我们一步步思考："触发推理。示例中模型逐步算出 15 - 8 = 7、7 + 12 = 19，答案为 19 个苹果。

```python
class ZeroShotCoT:
    """零样本思维链：直接添加"让我们一步步思考"触发推理"""

    def __init__(self, llm):
        self.llm = llm

    async def solve(self, question: str) -> str:
        prompt = f"""{question}

让我们一步步思考："""

        reasoning = await self.llm.generate(prompt)
        return reasoning


# 使用示例
# 问题：一个商店有15个苹果，卖掉了8个，又进了12个，现在有多少？
# 模型输出：
# 让我们一步步思考：
# 1. 商店最初有15个苹果
# 2. 卖掉了8个：15 - 8 = 7个
# 3. 又进了12个：7 + 12 = 19个
# 答案：现在有19个苹果
```

---

## 三、Few-shot CoT

> **Few-shot CoT**：在 prompt 中给出若干"问题 / 推理过程 / 答案"示例（如苹果算术、火车行程两例），再让模型对新问题照此推理。

```python
class FewShotCoT:
    """少样本思维链：提供带推理过程的示例"""

    def __init__(self, llm):
        self.llm = llm

    async def solve(self, question: str, examples: list = None) -> str:
        if examples is None:
            examples = self._default_examples()

        # 构建few-shot prompt
        prompt_parts = []
        for ex in examples:
            prompt_parts.append(f"问题：{ex['question']}")
            prompt_parts.append(f"推理过程：{ex['reasoning']}")
            prompt_parts.append(f"答案：{ex['answer']}")
            prompt_parts.append("")

        prompt_parts.append(f"问题：{question}")
        prompt_parts.append("推理过程：")

        prompt = "\n".join(prompt_parts)
        return await self.llm.generate(prompt)

    def _default_examples(self) -> list:
        return [
            {
                "question": "小明有5个苹果，给了小红2个，又买了3个，现在有几个？",
                "reasoning": "小明最初有5个苹果，给了小红2个后剩5-2=3个，又买了3个后有3+3=6个。",
                "answer": "6个",
            },
            {
                "question": "一辆火车每小时60公里，行驶了2.5小时，走了多远？",
                "reasoning": "距离=速度×时间，60×2.5=150公里。",
                "answer": "150公里",
            },
        ]
```

---

## 四、Self-Consistency

> **Self-Consistency**：对同一问题采样 `n_samples` 条推理路径（默认 5），用 `Counter` 做**多数票投票**选出最终答案；`_extract_answer` 从推理文本的末行提取答案。

```python
from collections import Counter


class SelfConsistencyCoT:
    """自一致性CoT：多次采样取多数票"""

    def __init__(self, llm, n_samples: int = 5):
        self.llm = llm
        self.n_samples = n_samples

    async def solve(self, question: str) -> str:
        # 多次采样推理路径
        answers = []
        for _ in range(self.n_samples):
            prompt = f"""{question}

让我们一步步思考："""
            response = await self.llm.generate(prompt)
            # 提取最终答案
            answer = self._extract_answer(response)
            answers.append(answer)

        # 多数票投票
        vote = Counter(answers)
        best_answer = vote.most_common(1)[0][0]
        return best_answer

    def _extract_answer(self, response: str) -> str:
        """从推理过程中提取最终答案"""
        # 简化实现：取最后一行作为答案
        lines = response.strip().split("\n")
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith("推理") and not line.startswith("步骤"):
                return line
        return response.strip().split("\n")[-1]
```

---

*（本系列后续篇章未完成）*
