# 提示词工程 Prompt Engineering

> 模块：提示词工程
> 更新时间：2026-03-29

---

## 一、提示词工程简介

提示词工程是优化与LLM交互的技术，通过设计高质量提示词获得更好的输出。

**核心原则**：

- 清晰具体
- 结构化输出
- 提供示例
- 角色设定
- 限制范围

---

## 二、核心技巧

### 1. 结构化提示词

```python
# 模板1：问答助手
TEMPLATE_QA = """
# 角色
你是一个专业的{domain}顾问。

# 任务
回答用户关于{domain}的问题。

# 要求
1. 回答要准确、简洁
2. 如有不确定，明确说明
3. 适当举例说明

# 问题
{question}

# 回答
"""

# 模板2：翻译助手
TEMPLATE_TRANSLATE = """
# 任务
将以下中文翻译成{target_lang}。

# 风格要求
{style}

# 内容
{content}

# 翻译
"""
```

### 2. Few-Shot提示

```python
# Few-Shot示例
FEW_SHOT_PROMPT = """
# 示例

示例1：
输入：今天很开心
输出：{"sentiment": "positive", "intensity": 0.8}

示例2：
输入：一般般
输出：{"sentiment": "neutral", "intensity": 0.5}

示例3：
输入：太糟糕了
输出：{"sentiment": "negative", "intensity": 0.9}

# 请完成以下转换：
输入：{input_text}
输出：
"""
```

### 3. CoT思维链

```python
# Zero-shot CoT
COT_ZERO_SHOT = """
问题：{question}

请逐步推理，最后给出答案。
"""

# Few-shot CoT
COT_FEW_SHOT = """
示例：
问题：小明有10个苹果，给了小红3个，又买了5个，现在有多少？
推理：
1. 小明原有10个苹果
2. 给了小红3个，10-3=7个
3. 又买了5个，7+5=12个
答案：12个

问题：{question}

推理：
"""
```

### 4. ReAct推理+行动

```python
REACT_PROMPT = """
你是一个智能助手，可以调用工具来回答问题。

可用工具：
- search(query): 搜索相关信息
- calculator(expression): 计算数学表达式
- look_up(entity): 查询实体信息

回答格式：
思考：{你的思考}
行动：{调用的工具}
观察：{工具返回结果}
...（重复以上步骤直到得到答案）
思考：现在我有足够信息来回答
行动：final_answer
观察：{最终答案}

问题：{question}

请开始：
"""
```

*图：提示词工程四大核心技巧（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 210" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="260" y="16" width="200" height="40" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="41" text-anchor="middle" font-size="15" fill="#1e293b">提示词工程核心技巧</text>
  <line x1="360" y1="56" x2="90" y2="118" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="56" x2="270" y2="118" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="56" x2="450" y2="118" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="56" x2="630" y2="118" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="20" y="122" width="140" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="90" y="148" text-anchor="middle" font-size="14" fill="#1e293b">结构化提示词</text>
  <text x="90" y="170" text-anchor="middle" font-size="13" fill="#475569">角色 / 任务 / 要求</text>
  <rect x="200" y="122" width="140" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="270" y="148" text-anchor="middle" font-size="14" fill="#1e293b">Few-Shot提示</text>
  <text x="270" y="170" text-anchor="middle" font-size="13" fill="#475569">提供示例</text>
  <rect x="380" y="122" width="140" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="450" y="148" text-anchor="middle" font-size="14" fill="#1e293b">CoT思维链</text>
  <text x="450" y="170" text-anchor="middle" font-size="13" fill="#475569">逐步推理给出答案</text>
  <rect x="560" y="122" width="140" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="630" y="148" text-anchor="middle" font-size="14" fill="#1e293b">ReAct推理+行动</text>
  <text x="630" y="170" text-anchor="middle" font-size="13" fill="#475569">思考 / 行动 / 观察</text>
</svg>

---

## 三、实际应用场景

### 场景1：结构化输出

```python
# 现行分包：parser 与 prompt 模板统一从 langchain_core 导入
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

class PersonInfo(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    occupation: str = Field(description="职业")
    skills: list[str] = Field(description="技能列表")

parser = PydanticOutputParser(pydantic_object=PersonInfo)

prompt = PromptTemplate(
    template="从以下文本中提取信息：\n{text}\n\n{format_instructions}",
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)
```

### 场景2：中文优化提示词

```python
# 中文提示词模板
CHINESE_PROMPT = """
# 角色设定
你是一位资深的{field}专家，有{years}年的从业经验。

# 回答风格
1. 语言简洁明了，避免冗长
2. 使用专业术语但要解释清楚
3. 适当使用比喻帮助理解
4. 结论要明确

# 输出格式
## 要点总结
[3-5个核心要点]

## 详细说明
[展开说明]

## 实用建议
[2-3条可操作的建议]

# 问题
{user_question}

请按上述格式回答：
"""
```

### 场景3：角色扮演

```python
ROLE_PLAY_PROMPT = """
# 角色
你扮演{role}，具有以下特点：
- 性格：{personality}
- 说话风格：{style}
- 专业领域：{expertise}

# 场景
{scenario}

# 限制
1. 保持角色一致性
2. 不要打破角色
3. 如果问题超出角色范围，礼貌说明

# 对话历史
{history}

# 当前消息
{current_message}

# 回复
{role}：
"""
```

---

## 四、提示词框架

### CRISP框架

```
C - Context（上下文）：提供背景信息
R - Role（角色）：设定AI角色
I - Instruction（指令）：明确任务
S - Style（风格）：指定输出风格
P - Pattern（模式）：提供示例
```

```python
CRISP_TEMPLATE = """
# 上下文
{context}

# 角色
你是一个{role}。

# 指令
{instruction}

# 风格
{style}

# 示例
{examples}

# 任务
{task}
"""
```

---

## 五、常见问题解决

### 1. 输出格式不稳定：更严格的格式定义 + 后处理

```python
# 解决方案：更严格的格式定义 + 后处理
import json
import logging
import re

logger = logging.getLogger(__name__)

def extract_json(text):
    # 尝试从输出中提取JSON
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            # JSON 解析失败时记录具体原因，便于排查模型输出问题
            logger.warning("模型输出 JSON 解析失败: %s，原文: %s", e, text[:200])
    return {"raw_text": text}
```

### 2. 幻觉问题：要求标注信息来源

```python
# 解决方案：要求标注信息来源
HALLUCINATION_PROMPT = """
你是一个严谨的问答助手。

要求：
1. 只回答有确切来源的信息
2. 如果不确定，明确说"我不确定"
3. 不要编造数据或引用

问题：{question}

来源：{source}

回答：
"""
```

### 3. 重复生成：限制输出长度+要求简洁

```python
# 解决方案：限制输出长度+要求简洁
CONCISE_PROMPT = """
用不超过3句话回答：
{question}

回答：
"""
```

---

## 六、总结

**提示词工程是使用LLM的核心技能**，需要不断实践和优化。

**学习要点**：

1. 理解结构化提示词
2. 掌握Few-Shot和CoT技巧
3. 学会角色扮演设定
4. 了解常见问题解决方案
5. 持续迭代优化提示词

### 企业级升级要点

- **提示词版本化**：生产提示词像代码一样纳入版本控制，变更走评审，避免口头传改
- **结构化输出兜底**：对 LLM 输出做 JSON Schema 校验与解析失败重试，不信任"裸"输出
- **评测驱动迭代**：建立提示词回归评测集，每次修改先跑分再上线，防止效果回退
- **导入规范**：LangChain 分包后统一从 langchain_core 导入模板与解析器，锁定版本
- **异常可观测**：解析失败、超长截断等异常要记录日志并统计失败率，而非静默吞掉

> 更多工程化实践（评测基准、灰度发布、成本控制）参见 [70-企业级工程基准](../../06-Agent开发/70-企业级工程基准.md)。

---

*下一步：RAG系统实战*
