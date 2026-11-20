# Prompt模板

> 模块：Prompt工程
> 更新时间：2026-11-15

---

## 模板系统：变量占位、格式化与内置模板

核心思路：**模板里用 `{变量}` 占位，`format()` 时注入实际值（缺参时给出可行动的报错）；`from_file` 用正则 `\{(\w+)\}` 自动提取变量名并去重**。内置 QA、摘要两个常用模板。

**字面花括号必须转义**：模板里要输出 JSON（如 `{"action": "search"}`）时，`str.format` 会把花括号当占位符解析，直接炸 `KeyError`——字面花括号必须双写 `{{ }}` 转义。不想处理转义就改自定义占位符（如 `<<变量>>` + 正则替换）。

```python
import re
from typing import List


class PromptTemplate:
    """Prompt模板"""

    def __init__(self, template: str, input_variables: List[str]):
        self.template = template
        # 去重保序：from_file 扫出来的变量名可能重复
        self.input_variables = list(dict.fromkeys(input_variables))

    def format(self, **kwargs) -> str:
        """格式化模板：缺参时给可行动的报错（缺哪些、模板需要哪些）。

        注意：模板里的字面 JSON 花括号必须双写 {{ }} 转义，
        否则 str.format 把它当占位符解析，会炸 KeyError/IndexError。
        """
        missing = [var for var in self.input_variables if var not in kwargs]
        if missing:
            raise ValueError(
                f"模板缺少变量：{missing}（模板需要 {self.input_variables}，"
                f"已提供 {sorted(kwargs)}）"
            )
        return self.template.format(**kwargs)

    @classmethod
    def from_file(cls, path: str) -> "PromptTemplate":
        """从文件加载：提取变量名并去重"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取变量名，去重且保序
        variables = list(dict.fromkeys(re.findall(r"\{(\w+)\}", content)))

        return cls(content, variables)


# 内置模板
class BuiltinTemplates:
    """内置模板"""

    QA_TEMPLATE = PromptTemplate(
        template="""基于以下上下文回答问题。

上下文：
{context}

问题：{question}

回答：""",
        input_variables=["context", "question"]
    )

    SUMMARIZE_TEMPLATE = PromptTemplate(
        template="""请总结以下内容的要点：

{content}

摘要：""",
        input_variables=["content"]
    )
```

---

## 模板引擎：注册模板并按名渲染

核心思路：**引擎持有模板注册表，启动时注册内置模板；`render` 按名字查表渲染，查不到直接抛 `ValueError`，缺参错误由 `PromptTemplate.format` 统一给出友好信息**。

```python
from typing import Dict


class PromptEngine:
    """Prompt引擎"""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._register_builtins()

    def _register_builtins(self):
        """注册内置模板"""
        self.templates["qa"] = BuiltinTemplates.QA_TEMPLATE
        self.templates["summarize"] = BuiltinTemplates.SUMMARIZE_TEMPLATE

    def register(self, name: str, template: PromptTemplate):
        self.templates[name] = template

    def render(self, name: str, **kwargs) -> str:
        template = self.templates.get(name)
        if not template:
            raise ValueError(f"Template not found: {name}（已注册：{sorted(self.templates)}）")
        return template.format(**kwargs)  # 缺参时 PromptTemplate 给出可行动报错

    def render_string(self, template: str, **kwargs) -> str:
        """渲染字符串模板（同样注意：字面花括号要 {{ }} 转义）"""
        return template.format(**kwargs)
```

### 企业级升级要点

- **Prompt 版本化：配置即代码**——模板文件进 Git，历史与回滚免费送，AB = 两份模板 + 固定评测集对比，见 `ai-rag-self-engineering/ownrag/ownrag/generate/prompts.py`（yaml 模板 + lru_cache 加载）。
- **渲染后残留校验**：占位符没填全在渲染期就爆（`渲染后仍有未填占位符`），配置错误不进运行期——见同文件 `render` 的 leftover 检查。
- **自定义占位符绕开 str.format 转义坑**：ownrag 用 `{key}` 逐个 replace 而不是 `str.format`，模板里写字面 JSON 花括号不炸——见同文件 `render` 的替换实现。
- **模板内容受闸门约束**：严格引用版 system prompt 规定「违反任何一条都会被校验程序拒绝」——提示词规则与代码闸门联动，见 `ai-rag-self-engineering/ownrag/ownrag/configs/prompts/policy_strict_v1.yaml` 与 `ai-rag-self-engineering/ownrag/ownrag/generate/gates.py`。

[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：few-shot学习*
