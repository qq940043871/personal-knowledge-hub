# RAG系统实战

> 模块：应用案例
> 更新时间：2026-11-15

---

## 一、RAG系统简介

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合知识检索和LLM生成的架构，让模型能够基于外部知识回答问题。

**核心价值**：

- 解决模型知识过时问题
- 减少幻觉
- 支持实时知识
- 可追溯可解释

---

## 二、系统架构

生产级 RAG 在「检索 → 生成」之间插入两道纯代码闸门（证据充分性闸门、引用校验闸门）和一道显式上下文预算——确定性的事交给代码，模型只负责生成。

```text
RAG系统流程：
┌─────────────┐
│   用户问题   │
└──────┬──────┘
       ▼
┌─────────────┐
│  问题改写    │  ← Query Rewrite（失败降级用原查询）
└──────┬──────┘
       ▼
┌─────────────┐
│  混合检索    │  ← 向量 + BM25 → RRF 名次融合
└──────┬──────┘
       ▼
┌─────────────┐
│  重排序      │  ← CrossEncoder Rerank
└──────┬──────┘
       ▼
┌─────────────┐
│ 充分性闸门   │  ← 候选不足直接拒答（零模型消耗）
└──────┬──────┘
       ▼
┌─────────────┐
│ 上下文预算   │  ← 按 token 装块，丢块清单可见
└──────┬──────┘
       ▼
┌─────────────┐
│  LLM生成    │  ← Generation
└──────┬──────┘
       ▼
┌─────────────┐
│ 引用校验闸门 │  ← 数字/日期必须能在所引块原文找到
└──────┬──────┘
       ▼
┌─────────────┐
│   最终答案   │  ← 附来源溯源
└─────────────┘
```

---

## 三、实际业务应用场景

### 场景1：基础RAG实现

2026-11 现行口径：各组件从分包导入（langchain-community / langchain-text-splitters / langchain-openai / langchain-chroma），QA 链用 LCEL 管道组装、统一 `.invoke()` 调用。

```python
import os

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# API key 一律 os.environ 读取；缺失时给可行动的报错，禁止硬编码
if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError(
        "缺少环境变量 OPENAI_API_KEY：请先 export OPENAI_API_KEY=<你的密钥> 再运行"
    )

# 1. 加载文档（顶级 langchain.document_loaders 已移除；PDFLoader 类从未存在——
#    PDF 用 PyPDFLoader，纯文本用 TextLoader）
loader = PyPDFLoader("document.pdf")
documents = loader.load()

# 2. 文档分块（切分器从 langchain-text-splitters 分包导入）
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", "。", "！", "？"],
)
chunks = text_splitter.split_documents(documents)

# 3. 创建向量存储（ada-002 已废弃；现行默认 text-embedding-3-small）
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./vector_db",
)

# 4. 创建检索器
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)

# 5. 创建LLM：显式超时与重试，网络抖动不直接失败
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60, max_retries=2)

# 6. 用 LCEL 组装 QA 链
prompt = ChatPromptTemplate.from_messages([
    ("system", "基于上下文回答问题；上下文中没有相关信息就直说，不要编造。"),
    ("human", "上下文：\n{context}\n\n问题：{question}"),
])


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


qa_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 7. 问答：统一 .invoke() 调用
result = qa_chain.invoke({"question": "文档的主要内容是什么？"})
print(result)

# ---- 对照：旧版 RetrievalQA 写法（legacy，仅存量代码可见，新项目不要再写）----
# from langchain.chains import RetrievalQA          # legacy：已停止演进
# qa_chain = RetrievalQA.from_chain_type(
#     llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True
# )
# result = qa_chain.invoke({"query": "..."})  # 旧字典调用已删除，只能 .invoke()
# print(result["result"])
```

### 场景2：高级RAG - 查询改写

`prompt | llm` 返回的是 `AIMessage`，直接 print 会带出消息包装、传给检索层也不是纯文本——必须接 `StrOutputParser` 拿到字符串。

```python
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# 环境变量检查同场景1（API key 一律 os.environ，禁止硬编码）

# 查询改写链：prompt | llm | 解析器，输出纯字符串
rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个查询改写专家。将用户问题改写成更适合检索的形式，只输出改写后的查询本身。"),
    ("human", "原问题：{question}\n\n改写后的问题："),
])

rewrite_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, timeout=60, max_retries=2)
rewrite_chain = rewrite_prompt | rewrite_llm | StrOutputParser()

# 场景自洽：本场景自己建一个最小向量库，不依赖场景1
raw_docs = [
    "Python 是一门通用编程语言，广泛用于数据分析和 AI 开发。",
    "Python 的 GIL 限制了多线程的并行执行效率。",
]
vectorstore = Chroma.from_documents(
    documents=[Document(page_content=t) for t in raw_docs],
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
)

# 改写问题（返回纯字符串）
rewritten = rewrite_chain.invoke({"question": "Python能干啥"})
print(rewritten)

# 用改写后的问题检索
docs = vectorstore.similarity_search(rewritten, k=2)
for doc in docs:
    print(doc.page_content)
```

### 场景3：多向量检索

父文档检索：小块做向量命中、命中后回取所属父块当上下文，兼顾精确度与完整语境。`SimpleDocumentStore` 从未存在——现行用 `langchain.storage.InMemoryStore`，父子关联靠 `id_key`。

```python
# 父文档检索器 - 平衡精确度和上下文
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 大块文档（用于最终上下文）
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)

# 小块文档（用于检索）
child_splitter = RecursiveCharacterTextSplitter(chunk_size=500)

# 父文档检索器
retriever = ParentDocumentRetriever(
    vectorstore=Chroma(embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")),
    docstore=InMemoryStore(),        # 存父块；生产可换 RedisStore / LocalFileStore
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
    id_key="source",                 # 父子关联键：metadata 里的同名字段（如文档路径）
    search_kwargs={"k": 5},
)

# 先建立父子关联：documents 的 metadata 必须带 id_key 对应的字段（示意，承接场景1）
retriever.add_documents(documents)

# 检索时返回包含小块的大块文档；0.3 起 Runnable 统一用 .invoke()
docs = retriever.invoke("关于Python的问题")
for doc in docs:
    print(doc.page_content[:100])
```

### 场景4：重排序

检索层永远能「捞回语义邻近的块」，真正区分相关与否靠交叉编码器对 query-doc 逐对打分。

```python
from sentence_transformers import CrossEncoder

# 交叉编码器重排序（本地模型，无需 API key；中文建议换 BAAI/bge-reranker-v2-m3）
reranker = CrossEncoder("cross-encoder/msmarco-MiniLM-L-6-v2")


def rerank_documents(query, documents, top_k=3):
    # 创建query-document对
    pairs = [(query, doc.page_content) for doc in documents]

    # 交叉编码器打分
    scores = reranker.predict(pairs)

    # 按分数排序
    scored_docs = list(zip(documents, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, _ in scored_docs[:top_k]]


# 使用重排序（示意：query 来自用户输入，vectorstore 承接场景1）
query = "关于Python的问题"
initial_docs = vectorstore.similarity_search(query, k=20)
final_docs = rerank_documents(query, initial_docs, top_k=5)
for doc in final_docs:
    print(doc.page_content[:60])
```

### 场景5：混合搜索

向量检索擅长语义、BM25 擅长精确词（型号、编号、术语），双路融合互为兜底。现行导入路径：`BM25Retriever` 在 langchain-community，`EnsembleRetriever` 在 langchain 主包。

```python
# 依赖：pip install rank-bm25（BM25Retriever 的底层实现）
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# BM25检索器：rank_bm25 默认按空格分词，中文需要自定义分词函数
# （示意按字符切分；生产环境换 jieba 分词，检索质量差距很大）
bm25_retriever = BM25Retriever.from_documents(
    chunks,
    preprocess_func=lambda text: list(text),
)

# 向量检索器
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# 融合检索：内部按加权名次融合两路结果
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.3, 0.7],  # BM25权重0.3，向量权重0.7
)

# 使用：0.3 起 Runnable 统一 .invoke()
query = "关于Python的问题"  # 示意：实际来自用户输入
docs = ensemble_retriever.invoke(query)
for doc in docs:
    print(doc.page_content[:60])
```

---

## 四、生产级RAG架构

按 ownrag 企业级模式组织主链路。核心认知：**闸门、预算、RRF 都是纯代码逻辑——确定性的事不交给模型，把「模型会错」变成可测试的规则集**。这里用伪代码突出六个特殊点；完整可运行实现见参考工程 ownrag（`ai-rag-self-engineering/ownrag/`）。

```python
# 生产级 RAG 主链路（伪代码：重点在特殊点，不在实现细节）
settings = RAGSettings.from_env()
#   ★特殊点1 配置即代码：全部配置启动期校验，缺 key / 非法值当场报可行动错误
#     ——带病运行到问答中途才失败，是最差的暴露时机

rewritten = rewrite_with_retry(query)
#   ★特殊点2 失败显式降级：改写重试 2 次（指数退避）仍失败 → 降级用原查询继续；
#     降级必须打日志可见，绝不静默吞错

cands = rrf_fuse(
    vector_search(rewritten, top_k=20),   # 向量路：语义邻近
    bm25_search(rewritten, top_k=20),     # 关键词路：精确词（型号/编号/术语）
)
#   ★特殊点3 混合检索按名次融合（RRF）：两路分数量纲不同，直接加权没有意义；
#     单路失败显式降级为另一路并打日志

cands = rerank(query, cands)[:rerank_top_k]
#     CrossEncoder 逐对打分——检索层只能捞回「语义邻近」，相关与否靠重排区分

if cands[0].score < settings.sufficiency_threshold:
    raise NoEvidence
#   ★特殊点4 证据充分性闸门（生成前）：候选为空或最高重排分低于阈值 → 直接拒答；
#     「未找到有效依据」是合法答案，拒答发生在进模型之前，零模型消耗

ctx, dropped = fit_context_budget(cands, settings.num_ctx - 1024)
#   ★特殊点5 上下文预算显式化：先算容量再装块（预留模板/问题/输出开销）；
#     超预算丢尾块，丢块清单随结果返回——不把截断权交给模型侧

answer = llm_generate(prompt(ctx, query))
#     生成时要求每个论断标注 [块N]；上下文没有依据就回答「未找到有效依据」

violations = citation_check(answer, cands)
#   ★特殊点6 引用校验闸门（生成后）：答案中的数字/日期必须能在所引块原文逐字找到；
#     违规 → 带违规清单反馈模型重答一次，仍不通过按规则拒答

return {"answer": answer,
        "sources": dedupe(c["source"] for c in ctx),   # 来源溯源
        "dropped_blocks": dropped}                     # 丢块也可见
```

---

## 五、RAG评估指标

ragas 0.2 起用 `EvaluationDataset` 显式构造评测集（`user_input / retrieved_contexts / response / reference` 四字段），`eval_dataset` 必须先定义再评估。

```python
from ragas import EvaluationDataset, evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

# 评测集：用真实问答日志补齐 20~50 条，指标才有置信度
eval_dataset = EvaluationDataset.from_dict([
    {
        "user_input": "公司的年假政策是什么？",
        "retrieved_contexts": ["员工每年享有 5 天带薪年假，工龄满 10 年增至 10 天。"],
        "response": "员工每年享有 5 天带薪年假，工龄满 10 年增至 10 天。[块1]",
        "reference": "每年 5 天带薪年假，工龄满 10 年增至 10 天。",
    },
])

# 评估RAG系统
result = evaluate(
    dataset=eval_dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ],
)

print(result)
```

---

## 六、总结与学习要点

RAG是**大模型应用的核心架构**，生产级RAG需要考虑**查询改写、重排序、混合搜索**等多个环节。

**学习要点**：

1. 理解RAG核心流程
2. 掌握文档分块策略
3. 熟练使用向量检索
4. 了解重排序技术
5. 掌握评估方法

### 企业级升级要点

- **配置即代码**：`RAGSettings.from_env()` 启动期校验全部配置，缺 key / 非法值当场报可行动错误——对齐 ownrag 的 `ai-rag-self-engineering/ownrag/ownrag/config.py`（环境变量优先、API key 只走环境变量）。
- **证据充分性闸门**：候选池为空或最高重排分低于阈值直接拒答，零模型消耗——「未找到有效依据」是合法答案，见 `ai-rag-self-engineering/ownrag/ownrag/generate/gates.py` 的 `sufficiency_check`。
- **引用校验闸门**：答案中的数字/日期必须能在所引块原文找到，防数字幻觉，见同文件 `citation_check`；规则进 Git、随评测集回归。
- **上下文预算显式化**：按 token 估算装块、丢块清单随结果返回可见——不把截断权交给模型侧，见 `ai-rag-self-engineering/ownrag/ownrag/generate/budget.py` 的 `fit_candidates`。
- **混合检索 RRF 融合**：向量 + BM25 只按名次融合、不比原始分，等权起步——没有评测集之前调权重都是猜，见 `ai-rag-self-engineering/ownrag/ownrag/retrieve/hybrid.py` 的 `rrf_fuse`。
- **失败显式降级不静默**：向量路、改写、重排失败都打 `[RAG]` 日志并降级继续，绝不静默吞错——对齐 ownrag 重排降级模式 `ai-rag-self-engineering/ownrag/ownrag/retrieve/rerank.py`。

[70-企业级工程基准](../70-企业级工程基准.md)
