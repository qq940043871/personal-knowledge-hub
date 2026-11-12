# Prompt模板

> 模块：Prompt工程
> 更新时间：2026-03-29

---

## 模板系统：变量占位、格式化与内置模板

核心思路：**模板里用 `{变量}` 占位，`format()` 时注入实际值；`from_file` 用正则 `\{(\w+)\}` 自动提取变量名**。内置 QA、摘要两个常用模板。

```python
class PromptTemplate:
    """Prompt模板"""

    def __init__(self, template: str, input_variables: List[str]):
        self.template = template
        self.input_variables = input_variables

    def format(self, **kwargs) -> str:
        """格式化模板"""
        return self.template.format(**kwargs)

    @classmethod
    def from_file(cls, path: str) -> "PromptTemplate":
        """从文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取变量名
        import re
        variables = re.findall(r'\{(\w+)\}', content)

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

核心思路：**引擎持有模板注册表，启动时注册内置模板；`render` 按名字查表渲染，查不到直接抛 `ValueError`**。

```python
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
            raise ValueError(f"Template not found: {name}")
        return template.format(**kwargs)

    def render_string(self, template: str, **kwargs) -> str:
        """渲染字符串模板"""
        return template.format(**kwargs)
```

---

*下一步：few-shot学习*
