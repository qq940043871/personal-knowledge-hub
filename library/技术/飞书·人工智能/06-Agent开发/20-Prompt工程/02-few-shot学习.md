# few-shot学习

> 模块：Prompt工程  
> 更新时间：2026-11-15

---

---

核心思路：**提供 1~N 个「输入 → 输出」示例，让模型照着格式完成第 N+1 个输入**。示例要有代表性、格式要一致、3~5 个通常足够，并覆盖边界情况。

```
<code>Few-Shot示例：<br/>  提供1-N个示例帮助模型理解任务<br/><br/>示例格式：<br/>  输入 → 输出<br/>  输入 → 输出<br/>  输入 → ?<br/><br/>最佳实践：<br/>  1. 示例要有代表性<br/>  2. 格式要一致<br/>  3. 3-5个示例通常足够<br/>  4. 示例要覆盖边界情况<br/>  5. 查询收尾只给输入——不给「空输出」让模型模仿</code>
```

---

---

核心思路：**`build_prompt`****把示例格式化后拼接成一段文本提示，查询以「用户消息」形态收尾（不渲染输出槽位）；****`build_messages`****则把每对示例转成 user/assistant 消息交替的对话格式，查询是最后一条 user 消息**。

**为什么要「用户消息收尾」**：若把查询也套进示例模板并配 `output=''`，Prompt 尾巴上就挂着「输出：」后跟空串——模型会把「输出后是空」也当成要模仿的格式，倾向输出空内容。查询只给输入，输出由模型补全。

```
<code>from typing import Dict, List, Optional<br/><br/><br/>class FewShotManager:<br/>    """Few-Shot示例管理器"""<br/><br/>    MAX_EXAMPLES = 10  # 示例不是越多越好：挤占上下文预算，后例还会稀释前例信号<br/><br/>    def __init__(self, template: str):<br/>        self.template = template<br/>        self.examples: List[Dict] = []<br/><br/>    def add_example(self, input_text: str, output_text: str):<br/>        """添加示例"""<br/>        self.examples.append({<br/>            "input": input_text,<br/>            "output": output_text<br/>        })<br/><br/>    def _validate_n(self, n: Optional[int]) -&gt; int:<br/>        """示例数上限校验：超上限/非法值直接报可行动错误"""<br/>        if n is None:<br/>            n = len(self.examples)<br/>        if n &lt; 1:<br/>            raise ValueError(f"示例数 n={n} 必须 &gt;= 1")<br/>        if n &gt; self.MAX_EXAMPLES:<br/>            raise ValueError(<br/>                f"示例数 n={n} 超过上限 {self.MAX_EXAMPLES}：示例挤占上下文预算，"<br/>                f"精选而非堆量（3~5 个通常足够）"<br/>            )<br/>        return n<br/><br/>    def build_prompt(self, query: str, n: int = None) -&gt; str:<br/>        """构建Few-Shot提示：示例带完整输入输出，查询只带输入"""<br/>        n = self._validate_n(n)<br/><br/>        examples_text = []<br/>        for ex in self.examples[:n]:<br/>            examples_text.append(self.template.format(<br/>                input=ex["input"], output=ex["output"]<br/>            ))<br/><br/>        # 用户消息收尾形态：查询不渲染输出槽位，避免模型模仿「空输出」<br/>        return "\n\n".join(examples_text) + f"\n\n用户输入：{query}"<br/><br/>    def build_messages(self, query: str, n: int = None) -&gt; List[Dict]:<br/>        """构建消息格式：示例转 user/assistant 交替，查询是最后一条 user 消息"""<br/>        n = self._validate_n(n)<br/><br/>        messages = []<br/>        for ex in self.examples[:n]:<br/>            messages.append({"role": "user", "content": ex["input"]})<br/>            messages.append({"role": "assistant", "content": ex["output"]})<br/>        messages.append({"role": "user", "content": query})<br/>        return messages</code>
```

### 企业级升级要点

- **示例吃上下文预算**：示例条数与块数共享生成窗口——示例太多会挤掉检索证据（最坏先被截掉的是问题），预算口径见 `ai-rag-self-engineering/ownrag/ownrag/generate/budget.py`。
- **Few-Shot 教格式不教事实**：示例用于固定输出形态，事实必须来自检索证据并过引用校验——见 `ai-rag-self-engineering/ownrag/ownrag/generate/gates.py` 的 `citation_check`。
- **输出形态与解析器对齐**：模型照示例输出后，下游必须有解析/校验承接（如 JSON schema 校验），见 `ai-rag-self-engineering/ownrag/ownrag/generate/gates.py` 的 `schema_check`。
- **Prompt 版本化**：含示例的模板文件进 Git、随评测集回归——改示例 = 改行为，必须可回滚，见 `ai-rag-self-engineering/ownrag/ownrag/generate/prompts.py`。

70-企业级工程基准

---

---