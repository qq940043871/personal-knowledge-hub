# RAGAS评估框架

> 模块：评估测试
> 更新时间：2026-11-15（代码口径：ragas 0.2+ EvaluationDataset / LangchainLLMWrapper）

---

## 一、RAGAS框架介绍

> RAGAS 是专注 RAG 系统质量评估的开源框架，无需人工标注即可评估 RAG 管道，提供 4 个核心评估指标。

```
RAGAS（Retrieval Augmented Generation Assessment）：
  - 专注RAG系统质量评估的开源框架
  - 无需人工标注即可评估RAG管道
  - 提供4个核心评估指标

核心指标：
  1. Faithfulness（忠实度）
     - 回答是否基于检索到的上下文
     - 检测幻觉（hallucination）

  2. Answer Relevance（答案相关性）
     - 回答是否与问题相关
     - 评估回答质量

  3. Context Precision（上下文精确度）
     - 检索到的上下文中相关部分的排名
     - 评估检索排序质量

  4. Context Recall（上下文召回率）
     - 是否检索到了回答问题所需的所有信息
     - 评估检索覆盖度
```

---

## 二、安装与快速上手

```python
# 安装
# pip install ragas langchain-openai

import os

from langchain_openai import ChatOpenAI
from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

def quick_evaluate():
    """快速评估示例（ragas 0.2+ 现行写法）"""
    # 准备评估数据：ragas 0.2+ 用 EvaluationDataset，
    # 单轮样本字段为 user_input / response / retrieved_contexts / reference
    eval_samples = [
        {
            "user_input": "什么是RAG？",
            "response": "RAG是检索增强生成，通过检索外部知识来增强大模型的回答质量。",
            "retrieved_contexts": [
                "RAG（Retrieval Augmented Generation）是一种结合检索和生成的技术，"
                "通过从外部知识库检索相关文档，将其作为上下文输入给大模型，"
                "从而提升回答的准确性和时效性。"
            ],
            "reference": "RAG是检索增强生成技术，通过检索外部知识库来增强大模型输出。",
        },
    ]
    dataset = EvaluationDataset.from_dict(eval_samples)

    # 评估用 LLM：用 LangchainLLMWrapper 包装现行 LangChain 模型
    #（API key 从环境变量读取，禁止硬编码）
    evaluator_llm = LangchainLLMWrapper(
        ChatOpenAI(model="gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"])
    )

    # 执行评估
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy,
                 context_precision, context_recall],
        llm=evaluator_llm,
    )

    print(result)
    # {'faithfulness': 1.0, 'answer_relevancy': 0.95,
    #  'context_precision': 1.0, 'context_recall': 0.9}
    return result
```

---

## 三、评估指标详解

生产环境优先使用 ragas 内置指标（配合上文 LangchainLLMWrapper）。下面两个自定义类是**教学示意**，用来说明指标背后的实现原理——接口改用现行 LangChain 写法（`llm.invoke()`，不再依赖非标准的 `llm.generate()`），判定也从"全文子串计数"改为按行末标注逐条统计：

```python
import re
from typing import List

from langchain_core.messages import HumanMessage

class FaithfulnessEvaluator:
    """忠实度评估（教学示意，生产用 ragas 内置 faithfulness 指标）：
    检查回答中的每个声明是否有上下文支持。"""

    def __init__(self, llm):
        self.llm = llm               # 现行 LangChain 聊天模型（llm.invoke 接口）

    def evaluate(self, question: str, answer: str, contexts: List[str]) -> float:
        context_text = "\n".join(contexts)
        # 让 LLM 逐条列出声明并在行末标注 支持/不支持；判定按行末标注逐条统计——
        # 比全文子串计数更稳（能区分"支持"出现在声明内容里的情况）
        prompt = (
            f"基于以下上下文，判断回答中的每个声明是否有依据。\n"
            f"上下文：{context_text}\n问题：{question}\n回答：{answer}\n"
            "请逐条列出回答中的声明，并在每行末尾标注 支持 或 不支持。\n"
            "格式：声明内容 | 支持/不支持")
        result = self.llm.invoke([HumanMessage(content=prompt)])   # 返回 AIMessage
        text = result.content
        supported = len(re.findall(r"\|\s*支持\s*$", text, flags=re.MULTILINE))
        unsupported = len(re.findall(r"\|\s*不支持\s*$", text, flags=re.MULTILINE))
        total = supported + unsupported
        return supported / total if total > 0 else 0.0

class AnswerRelevanceEvaluator:
    """答案相关性评估（教学示意，生产用 ragas 内置 answer_relevancy 指标）：
    根据答案反向生成问题，再算与原问题的语义相似度；
    embedder 需提供 encode(texts) -> 向量矩阵 接口（如 sentence-transformers）。"""

    def __init__(self, llm, embedder):
        self.llm, self.embedder = llm, embedder

    def evaluate(self, question: str, answer: str) -> float:
        # 伪代码：1) llm.invoke 反向生成 3 个问题；2) embedder.encode([question] + 生成问题)
        #         一次批量编码；3) 与原问题余弦相似度取均值（numpy 向量化；无生成问题返回 0.0）
        ...
```

---

## 四、与LangSmith Evals对比

> 选型建议：纯 RAG 系统评估 → RAGAS；LangChain 生态 + 需要全面监控 → LangSmith；两者结合使用效果最佳。

```
RAGAS vs LangSmith Evals：
  ┌──────────────┬─────────────────┬─────────────────┐
  │ 维度          │ RAGAS           │ LangSmith Evals  │
  ├──────────────┼─────────────────┼─────────────────┤
  │ 专注领域      │ RAG系统专项评估  │ 通用LLM评估      │
  │ 指标类型      │ 4个RAG专用指标   │ 自定义指标       │
  │ 人工标注      │ 不需要（reference│ 可选            │
  │              │ free）          │                 │
  │ 集成方式      │ Python SDK      │ LangChain深度集成│
  │ 评估速度      │ 中等            │ 快（云端）       │
  │ 可视化        │ 基础            │ 完善的Dashboard  │
  │ 适用场景      │ RAG管道质量监控  │ 全链路LLM监控    │
  └──────────────┴─────────────────┴─────────────────┘

推荐：
  - 纯RAG系统评估 → RAGAS
  - LangChain生态 + 需要全面监控 → LangSmith
  - 两者结合使用效果最佳
```

---

### 企业级升级要点

评估不是跑一次看个分数，而是要进回归门禁，参考 ownrag 基准工程（D:\ai_person\personal-ai-engineering\ai-rag-self-engineering\ownrag）：

- **评测先行**：没有评测集之前调检索权重、换模型都是猜——ownrag 的检索融合明确写着"RRF 等权起步，评测先行"，见 `ownrag/retrieve/hybrid.py`。
- **指标对齐闸门**：Faithfulness 检测的幻觉问题，ownrag 在生成后用纯代码闸门兜底（引用块必须在候选池内、数字/日期能在原文核验），规则可测试、进 Git 随评测集回归，见 `ownrag/generate/gates.py`。
- **拒答语义校准**：向量检索永远"捞得到"语义邻近块，拒答标准要从"零召回"迁移到"重排分不足"，阈值随评测集校准，见 `ownrag/generate/gates.py` 的 `_MIN_RERANK_SCORE`。
- **解析质量进评测**：错在解析在问答阶段几乎无法回溯，ownrag 在入库前设人工复核闸（解析产物落盘给人确认），见 `ownrag/review.py`。
- **评估成本控制**：LLM-as-judge 按 token 计费，抽样评估 + 预算控制思路参考 `ownrag/generate/budget.py`。

延伸阅读：[70-企业级工程基准](../../06-Agent开发/70-企业级工程基准.md)

---

*下一步：评估体系全景*
