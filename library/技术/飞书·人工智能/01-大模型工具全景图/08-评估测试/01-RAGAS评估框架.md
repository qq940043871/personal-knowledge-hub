# RAGAS评估框架

> 模块：评估测试  
> 更新时间：2026-11-15（代码口径：ragas 0.2+ EvaluationDataset / LangchainLLMWrapper）

---

---

> RAGAS 是专注 RAG 系统质量评估的开源框架，无需人工标注即可评估 RAG 管道，提供 4 个核心评估指标。

```
<code>RAGAS（Retrieval Augmented Generation Assessment）：<br/>  - 专注RAG系统质量评估的开源框架<br/>  - 无需人工标注即可评估RAG管道<br/>  - 提供4个核心评估指标<br/><br/>核心指标：<br/>  1. Faithfulness（忠实度）<br/>     - 回答是否基于检索到的上下文<br/>     - 检测幻觉（hallucination）<br/><br/>  2. Answer Relevance（答案相关性）<br/>     - 回答是否与问题相关<br/>     - 评估回答质量<br/><br/>  3. Context Precision（上下文精确度）<br/>     - 检索到的上下文中相关部分的排名<br/>     - 评估检索排序质量<br/><br/>  4. Context Recall（上下文召回率）<br/>     - 是否检索到了回答问题所需的所有信息<br/>     - 评估检索覆盖度</code>
```

---

---

```
<code># 安装<br/># pip install ragas langchain-openai<br/><br/>import os<br/><br/>from langchain_openai import ChatOpenAI<br/>from ragas import EvaluationDataset, evaluate<br/>from ragas.llms import LangchainLLMWrapper<br/>from ragas.metrics import (<br/>    answer_relevancy,<br/>    context_precision,<br/>    context_recall,<br/>    faithfulness,<br/>)<br/><br/>def quick_evaluate():<br/>    """快速评估示例（ragas 0.2+ 现行写法）"""<br/>    # 准备评估数据：ragas 0.2+ 用 EvaluationDataset，<br/>    # 单轮样本字段为 user_input / response / retrieved_contexts / reference<br/>    eval_samples = [<br/>        {<br/>            "user_input": "什么是RAG？",<br/>            "response": "RAG是检索增强生成，通过检索外部知识来增强大模型的回答质量。",<br/>            "retrieved_contexts": [<br/>                "RAG（Retrieval Augmented Generation）是一种结合检索和生成的技术，"<br/>                "通过从外部知识库检索相关文档，将其作为上下文输入给大模型，"<br/>                "从而提升回答的准确性和时效性。"<br/>            ],<br/>            "reference": "RAG是检索增强生成技术，通过检索外部知识库来增强大模型输出。",<br/>        },<br/>    ]<br/>    dataset = EvaluationDataset.from_dict(eval_samples)<br/><br/>    # 评估用 LLM：用 LangchainLLMWrapper 包装现行 LangChain 模型<br/>    #（API key 从环境变量读取，禁止硬编码）<br/>    evaluator_llm = LangchainLLMWrapper(<br/>        ChatOpenAI(model="gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"])<br/>    )<br/><br/>    # 执行评估<br/>    result = evaluate(<br/>        dataset=dataset,<br/>        metrics=[faithfulness, answer_relevancy,<br/>                 context_precision, context_recall],<br/>        llm=evaluator_llm,<br/>    )<br/><br/>    print(result)<br/>    # {'faithfulness': 1.0, 'answer_relevancy': 0.95,<br/>    #  'context_precision': 1.0, 'context_recall': 0.9}<br/>    return result</code>
```

---

---

生产环境优先使用 ragas 内置指标（配合上文 LangchainLLMWrapper）。下面两个自定义类是**教学示意**，用来说明指标背后的实现原理——接口改用现行 LangChain 写法（`llm.invoke()`，不再依赖非标准的 `llm.generate()`），判定也从"全文子串计数"改为按行末标注逐条统计：

```
<code>import re<br/>from typing import List<br/><br/>from langchain_core.messages import HumanMessage<br/><br/>class FaithfulnessEvaluator:<br/>    """忠实度评估（教学示意，生产用 ragas 内置 faithfulness 指标）：<br/>    检查回答中的每个声明是否有上下文支持。"""<br/><br/>    def __init__(self, llm):<br/>        self.llm = llm               # 现行 LangChain 聊天模型（llm.invoke 接口）<br/><br/>    def evaluate(self, question: str, answer: str, contexts: List[str]) -&gt; float:<br/>        context_text = "\n".join(contexts)<br/>        # 让 LLM 逐条列出声明并在行末标注 支持/不支持；判定按行末标注逐条统计——<br/>        # 比全文子串计数更稳（能区分"支持"出现在声明内容里的情况）<br/>        prompt = (<br/>            f"基于以下上下文，判断回答中的每个声明是否有依据。\n"<br/>            f"上下文：{context_text}\n问题：{question}\n回答：{answer}\n"<br/>            "请逐条列出回答中的声明，并在每行末尾标注 支持 或 不支持。\n"<br/>            "格式：声明内容 | 支持/不支持")<br/>        result = self.llm.invoke([HumanMessage(content=prompt)])   # 返回 AIMessage<br/>        text = result.content<br/>        supported = len(re.findall(r"\|\s*支持\s*$", text, flags=re.MULTILINE))<br/>        unsupported = len(re.findall(r"\|\s*不支持\s*$", text, flags=re.MULTILINE))<br/>        total = supported + unsupported<br/>        return supported / total if total &gt; 0 else 0.0<br/><br/>class AnswerRelevanceEvaluator:<br/>    """答案相关性评估（教学示意，生产用 ragas 内置 answer_relevancy 指标）：<br/>    根据答案反向生成问题，再算与原问题的语义相似度；<br/>    embedder 需提供 encode(texts) -&gt; 向量矩阵 接口（如 sentence-transformers）。"""<br/><br/>    def __init__(self, llm, embedder):<br/>        self.llm, self.embedder = llm, embedder<br/><br/>    def evaluate(self, question: str, answer: str) -&gt; float:<br/>        # 伪代码：1) llm.invoke 反向生成 3 个问题；2) embedder.encode([question] + 生成问题)<br/>        #         一次批量编码；3) 与原问题余弦相似度取均值（numpy 向量化；无生成问题返回 0.0）<br/>        ...</code>
```

---

---

> 选型建议：纯 RAG 系统评估 → RAGAS；LangChain 生态 + 需要全面监控 → LangSmith；两者结合使用效果最佳。

```
<code>RAGAS vs LangSmith Evals：<br/>  ┌──────────────┬─────────────────┬─────────────────┐<br/>  │ 维度          │ RAGAS           │ LangSmith Evals  │<br/>  ├──────────────┼─────────────────┼─────────────────┤<br/>  │ 专注领域      │ RAG系统专项评估  │ 通用LLM评估      │<br/>  │ 指标类型      │ 4个RAG专用指标   │ 自定义指标       │<br/>  │ 人工标注      │ 不需要（reference│ 可选            │<br/>  │              │ free）          │                 │<br/>  │ 集成方式      │ Python SDK      │ LangChain深度集成│<br/>  │ 评估速度      │ 中等            │ 快（云端）       │<br/>  │ 可视化        │ 基础            │ 完善的Dashboard  │<br/>  │ 适用场景      │ RAG管道质量监控  │ 全链路LLM监控    │<br/>  └──────────────┴─────────────────┴─────────────────┘<br/><br/>推荐：<br/>  - 纯RAG系统评估 → RAGAS<br/>  - LangChain生态 + 需要全面监控 → LangSmith<br/>  - 两者结合使用效果最佳</code>
```

---

---

评估不是跑一次看个分数，而是要进回归门禁，参考 ownrag 基准工程：

- **评测先行**：没有评测集之前调检索权重、换模型都是猜——ownrag 的检索融合明确写着"RRF 等权起步，评测先行"，见 `ownrag/retrieve/hybrid.py`。
- **指标对齐闸门**：Faithfulness 检测的幻觉问题，ownrag 在生成后用纯代码闸门兜底（引用块必须在候选池内、数字/日期能在原文核验），规则可测试、进 Git 随评测集回归，见 `ownrag/generate/gates.py`。
- **拒答语义校准**：向量检索永远"捞得到"语义邻近块，拒答标准要从"零召回"迁移到"重排分不足"，阈值随评测集校准，见 `ownrag/generate/gates.py` 的 `_MIN_RERANK_SCORE`。
- **解析质量进评测**：错在解析在问答阶段几乎无法回溯，ownrag 在入库前设人工复核闸（解析产物落盘给人确认），见 `ownrag/review.py`。
- **评估成本控制**：LLM-as-judge 按 token 计费，抽样评估 + 预算控制思路参考 `ownrag/generate/budget.py`。

延伸阅读：70-企业级工程基准

---

---