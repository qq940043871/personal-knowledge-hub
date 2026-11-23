# Prompt模板

> 模块：Prompt工程  
> 更新时间：2026-11-15

---

---

核心思路：**模板里用****`{变量}`****占位，****`format()`****时注入实际值（缺参时给出可行动的报错）；****`from_file`****用正则****`\{(\w+)\}`****自动提取变量名并去重**。内置 QA、摘要两个常用模板。

**字面花括号必须转义**：模板里要输出 JSON（如 `{"action": "search"}`）时，`str.format` 会把花括号当占位符解析，直接炸 `KeyError`——字面花括号必须双写 `{{ }}` 转义。不想处理转义就改自定义占位符（如 `>` + 正则替换）。

```
<code>import re<br/>from typing import List<br/><br/><br/>class PromptTemplate:<br/>    """Prompt模板"""<br/><br/>    def __init__(self, template: str, input_variables: List[str]):<br/>        self.template = template<br/>        # 去重保序：from_file 扫出来的变量名可能重复<br/>        self.input_variables = list(dict.fromkeys(input_variables))<br/><br/>    def format(self, **kwargs) -&gt; str:<br/>        """格式化模板：缺参时给可行动的报错（缺哪些、模板需要哪些）。<br/><br/>        注意：模板里的字面 JSON 花括号必须双写 {{ }} 转义，<br/>        否则 str.format 把它当占位符解析，会炸 KeyError/IndexError。<br/>        """<br/>        missing = [var for var in self.input_variables if var not in kwargs]<br/>        if missing:<br/>            raise ValueError(<br/>                f"模板缺少变量：{missing}（模板需要 {self.input_variables}，"<br/>                f"已提供 {sorted(kwargs)}）"<br/>            )<br/>        return self.template.format(**kwargs)<br/><br/>    @classmethod<br/>    def from_file(cls, path: str) -&gt; "PromptTemplate":<br/>        """从文件加载：提取变量名并去重"""<br/>        with open(path, "r", encoding="utf-8") as f:<br/>            content = f.read()<br/><br/>        # 提取变量名，去重且保序<br/>        variables = list(dict.fromkeys(re.findall(r"\{(\w+)\}", content)))<br/><br/>        return cls(content, variables)<br/><br/><br/># 内置模板<br/>class BuiltinTemplates:<br/>    """内置模板"""<br/><br/>    QA_TEMPLATE = PromptTemplate(<br/>        template="""基于以下上下文回答问题。<br/><br/>上下文：<br/>{context}<br/><br/>问题：{question}<br/><br/>回答：""",<br/>        input_variables=["context", "question"]<br/>    )<br/><br/>    SUMMARIZE_TEMPLATE = PromptTemplate(<br/>        template="""请总结以下内容的要点：<br/><br/>{content}<br/><br/>摘要：""",<br/>        input_variables=["content"]<br/>    )</code>
```

---

---

核心思路：**引擎持有模板注册表，启动时注册内置模板；****`render`****按名字查表渲染，查不到直接抛****`ValueError`****，缺参错误由****`PromptTemplate.format`****统一给出友好信息**。

```
<code>from typing import Dict<br/><br/><br/>class PromptEngine:<br/>    """Prompt引擎"""<br/><br/>    def __init__(self):<br/>        self.templates: Dict[str, PromptTemplate] = {}<br/>        self._register_builtins()<br/><br/>    def _register_builtins(self):<br/>        """注册内置模板"""<br/>        self.templates["qa"] = BuiltinTemplates.QA_TEMPLATE<br/>        self.templates["summarize"] = BuiltinTemplates.SUMMARIZE_TEMPLATE<br/><br/>    def register(self, name: str, template: PromptTemplate):<br/>        self.templates[name] = template<br/><br/>    def render(self, name: str, **kwargs) -&gt; str:<br/>        template = self.templates.get(name)<br/>        if not template:<br/>            raise ValueError(f"Template not found: {name}（已注册：{sorted(self.templates)}）")<br/>        return template.format(**kwargs)  # 缺参时 PromptTemplate 给出可行动报错<br/><br/>    def render_string(self, template: str, **kwargs) -&gt; str:<br/>        """渲染字符串模板（同样注意：字面花括号要 {{ }} 转义）"""<br/>        return template.format(**kwargs)</code>
```

### 企业级升级要点

- **Prompt 版本化：配置即代码**——模板文件进 Git，历史与回滚免费送，AB = 两份模板 + 固定评测集对比，见 `ai-rag-self-engineering/ownrag/ownrag/generate/prompts.py`（yaml 模板 + lru_cache 加载）。
- **渲染后残留校验**：占位符没填全在渲染期就爆（`渲染后仍有未填占位符`），配置错误不进运行期——见同文件 `render` 的 leftover 检查。
- **自定义占位符绕开 str.format 转义坑**：ownrag 用 `{key}` 逐个 replace 而不是 `str.format`，模板里写字面 JSON 花括号不炸——见同文件 `render` 的替换实现。
- **模板内容受闸门约束**：严格引用版 system prompt 规定「违反任何一条都会被校验程序拒绝」——提示词规则与代码闸门联动，见 `ai-rag-self-engineering/ownrag/ownrag/configs/prompts/policy_strict_v1.yaml` 与 `ai-rag-self-engineering/ownrag/ownrag/generate/gates.py`。

70-企业级工程基准

---

---