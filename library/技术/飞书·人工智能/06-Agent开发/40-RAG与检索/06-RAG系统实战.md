# RAG系统实战

> 模块：应用案例  
> 更新时间：2026-11-15

---

---

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合知识检索和LLM生成的架构，让模型能够基于外部知识回答问题。

**核心价值**：

- 解决模型知识过时问题
- 减少幻觉
- 支持实时知识
- 可追溯可解释

---

---

生产级 RAG 在「检索 → 生成」之间插入两道纯代码闸门（证据充分性闸门、引用校验闸门）和一道显式上下文预算——确定性的事交给代码，模型只负责生成。

```
<code>RAG系统流程：<br/>┌─────────────┐<br/>│   用户问题   │<br/>└──────┬──────┘<br/>       ▼<br/>┌─────────────┐<br/>│  问题改写    │  ← Query Rewrite（失败降级用原查询）<br/>└──────┬──────┘<br/>       ▼<br/>┌─────────────┐<br/>│  混合检索    │  ← 向量 + BM25 → RRF 名次融合<br/>└──────┬──────┘<br/>       ▼<br/>┌─────────────┐<br/>│  重排序      │  ← CrossEncoder Rerank<br/>└──────┬──────┘<br/>       ▼<br/>┌─────────────┐<br/>│ 充分性闸门   │  ← 候选不足直接拒答（零模型消耗）<br/>└──────┬──────┘<br/>       ▼<br/>┌─────────────┐<br/>│ 上下文预算   │  ← 按 token 装块，丢块清单可见<br/>└──────┬──────┘<br/>       ▼<br/>┌─────────────┐<br/>│  LLM生成    │  ← Generation<br/>└──────┬──────┘<br/>       ▼<br/>┌─────────────┐<br/>│ 引用校验闸门 │  ← 数字/日期必须能在所引块原文找到<br/>└──────┬──────┘<br/>       ▼<br/>┌─────────────┐<br/>│   最终答案   │  ← 附来源溯源<br/>└─────────────┘</code>
```

---

---

### 场景1：基础RAG实现

2026-11 现行口径：各组件从分包导入（langchain-community / langchain-text-splitters / langchain-openai / langchain-chroma），QA 链用 LCEL 管道组装、统一 `.invoke()` 调用。

```
<code>import os<br/><br/>from langchain_chroma import Chroma<br/>from langchain_community.document_loaders import PyPDFLoader, TextLoader<br/>from langchain_core.output_parsers import StrOutputParser<br/>from langchain_core.prompts import ChatPromptTemplate<br/>from langchain_core.runnables import RunnablePassthrough<br/>from langchain_openai import ChatOpenAI, OpenAIEmbeddings<br/>from langchain_text_splitters import RecursiveCharacterTextSplitter<br/><br/># API key 一律 os.environ 读取；缺失时给可行动的报错，禁止硬编码<br/>if not os.environ.get("OPENAI_API_KEY"):<br/>    raise RuntimeError(<br/>        "缺少环境变量 OPENAI_API_KEY：请先 export OPENAI_API_KEY=&lt;你的密钥&gt; 再运行"<br/>    )<br/><br/># 1. 加载文档（顶级 langchain.document_loaders 已移除；PDFLoader 类从未存在——<br/>#    PDF 用 PyPDFLoader，纯文本用 TextLoader）<br/>loader = PyPDFLoader("document.pdf")<br/>documents = loader.load()<br/><br/># 2. 文档分块（切分器从 langchain-text-splitters 分包导入）<br/>text_splitter = RecursiveCharacterTextSplitter(<br/>    chunk_size=1000,<br/>    chunk_overlap=200,<br/>    separators=["\n\n", "\n", "。", "！", "？"],<br/>)<br/>chunks = text_splitter.split_documents(documents)<br/><br/># 3. 创建向量存储（ada-002 已废弃；现行默认 text-embedding-3-small）<br/>embeddings = OpenAIEmbeddings(model="text-embedding-3-small")<br/>vectorstore = Chroma.from_documents(<br/>    documents=chunks,<br/>    embedding=embeddings,<br/>    persist_directory="./vector_db",<br/>)<br/><br/># 4. 创建检索器<br/>retriever = vectorstore.as_retriever(<br/>    search_type="similarity",<br/>    search_kwargs={"k": 5},<br/>)<br/><br/># 5. 创建LLM：显式超时与重试，网络抖动不直接失败<br/>llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60, max_retries=2)<br/><br/># 6. 用 LCEL 组装 QA 链<br/>prompt = ChatPromptTemplate.from_messages([<br/>    ("system", "基于上下文回答问题；上下文中没有相关信息就直说，不要编造。"),<br/>    ("human", "上下文：\n{context}\n\n问题：{question}"),<br/>])<br/><br/><br/>def format_docs(docs):<br/>    return "\n\n".join(doc.page_content for doc in docs)<br/><br/><br/>qa_chain = (<br/>    {"context": retriever | format_docs, "question": RunnablePassthrough()}<br/>    | prompt<br/>    | llm<br/>    | StrOutputParser()<br/>)<br/><br/># 7. 问答：统一 .invoke() 调用<br/>result = qa_chain.invoke({"question": "文档的主要内容是什么？"})<br/>print(result)<br/><br/># ---- 对照：旧版 RetrievalQA 写法（legacy，仅存量代码可见，新项目不要再写）----<br/># from langchain.chains import RetrievalQA          # legacy：已停止演进<br/># qa_chain = RetrievalQA.from_chain_type(<br/>#     llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True<br/># )<br/># result = qa_chain.invoke({"query": "..."})  # 旧字典调用已删除，只能 .invoke()<br/># print(result["result"])</code>
```

### 场景2：高级RAG - 查询改写

`prompt | llm` 返回的是 `AIMessage`，直接 print 会带出消息包装、传给检索层也不是纯文本——必须接 `StrOutputParser` 拿到字符串。

```
<code>from langchain_chroma import Chroma<br/>from langchain_core.documents import Document<br/>from langchain_core.output_parsers import StrOutputParser<br/>from langchain_core.prompts import ChatPromptTemplate<br/>from langchain_openai import ChatOpenAI, OpenAIEmbeddings<br/><br/># 环境变量检查同场景1（API key 一律 os.environ，禁止硬编码）<br/><br/># 查询改写链：prompt | llm | 解析器，输出纯字符串<br/>rewrite_prompt = ChatPromptTemplate.from_messages([<br/>    ("system", "你是一个查询改写专家。将用户问题改写成更适合检索的形式，只输出改写后的查询本身。"),<br/>    ("human", "原问题：{question}\n\n改写后的问题："),<br/>])<br/><br/>rewrite_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, timeout=60, max_retries=2)<br/>rewrite_chain = rewrite_prompt | rewrite_llm | StrOutputParser()<br/><br/># 场景自洽：本场景自己建一个最小向量库，不依赖场景1<br/>raw_docs = [<br/>    "Python 是一门通用编程语言，广泛用于数据分析和 AI 开发。",<br/>    "Python 的 GIL 限制了多线程的并行执行效率。",<br/>]<br/>vectorstore = Chroma.from_documents(<br/>    documents=[Document(page_content=t) for t in raw_docs],<br/>    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),<br/>)<br/><br/># 改写问题（返回纯字符串）<br/>rewritten = rewrite_chain.invoke({"question": "Python能干啥"})<br/>print(rewritten)<br/><br/># 用改写后的问题检索<br/>docs = vectorstore.similarity_search(rewritten, k=2)<br/>for doc in docs:<br/>    print(doc.page_content)</code>
```

### 场景3：多向量检索

父文档检索：小块做向量命中、命中后回取所属父块当上下文，兼顾精确度与完整语境。`SimpleDocumentStore` 从未存在——现行用 `langchain.storage.InMemoryStore`，父子关联靠 `id_key`。

```
<code># 父文档检索器 - 平衡精确度和上下文<br/>from langchain.retrievers import ParentDocumentRetriever<br/>from langchain.storage import InMemoryStore<br/>from langchain_chroma import Chroma<br/>from langchain_openai import OpenAIEmbeddings<br/>from langchain_text_splitters import RecursiveCharacterTextSplitter<br/><br/># 大块文档（用于最终上下文）<br/>parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)<br/><br/># 小块文档（用于检索）<br/>child_splitter = RecursiveCharacterTextSplitter(chunk_size=500)<br/><br/># 父文档检索器<br/>retriever = ParentDocumentRetriever(<br/>    vectorstore=Chroma(embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")),<br/>    docstore=InMemoryStore(),        # 存父块；生产可换 RedisStore / LocalFileStore<br/>    child_splitter=child_splitter,<br/>    parent_splitter=parent_splitter,<br/>    id_key="source",                 # 父子关联键：metadata 里的同名字段（如文档路径）<br/>    search_kwargs={"k": 5},<br/>)<br/><br/># 先建立父子关联：documents 的 metadata 必须带 id_key 对应的字段（示意，承接场景1）<br/>retriever.add_documents(documents)<br/><br/># 检索时返回包含小块的大块文档；0.3 起 Runnable 统一用 .invoke()<br/>docs = retriever.invoke("关于Python的问题")<br/>for doc in docs:<br/>    print(doc.page_content[:100])</code>
```

### 场景4：重排序

检索层永远能「捞回语义邻近的块」，真正区分相关与否靠交叉编码器对 query-doc 逐对打分。

```
<code>from sentence_transformers import CrossEncoder<br/><br/># 交叉编码器重排序（本地模型，无需 API key；中文建议换 BAAI/bge-reranker-v2-m3）<br/>reranker = CrossEncoder("cross-encoder/msmarco-MiniLM-L-6-v2")<br/><br/><br/>def rerank_documents(query, documents, top_k=3):<br/>    # 创建query-document对<br/>    pairs = [(query, doc.page_content) for doc in documents]<br/><br/>    # 交叉编码器打分<br/>    scores = reranker.predict(pairs)<br/><br/>    # 按分数排序<br/>    scored_docs = list(zip(documents, scores))<br/>    scored_docs.sort(key=lambda x: x[1], reverse=True)<br/><br/>    return [doc for doc, _ in scored_docs[:top_k]]<br/><br/><br/># 使用重排序（示意：query 来自用户输入，vectorstore 承接场景1）<br/>query = "关于Python的问题"<br/>initial_docs = vectorstore.similarity_search(query, k=20)<br/>final_docs = rerank_documents(query, initial_docs, top_k=5)<br/>for doc in final_docs:<br/>    print(doc.page_content[:60])</code>
```

### 场景5：混合搜索

向量检索擅长语义、BM25 擅长精确词（型号、编号、术语），双路融合互为兜底。现行导入路径：`BM25Retriever` 在 langchain-community，`EnsembleRetriever` 在 langchain 主包。

```
<code># 依赖：pip install rank-bm25（BM25Retriever 的底层实现）<br/>from langchain.retrievers import EnsembleRetriever<br/>from langchain_community.retrievers import BM25Retriever<br/><br/># BM25检索器：rank_bm25 默认按空格分词，中文需要自定义分词函数<br/># （示意按字符切分；生产环境换 jieba 分词，检索质量差距很大）<br/>bm25_retriever = BM25Retriever.from_documents(<br/>    chunks,<br/>    preprocess_func=lambda text: list(text),<br/>)<br/><br/># 向量检索器<br/>vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})<br/><br/># 融合检索：内部按加权名次融合两路结果<br/>ensemble_retriever = EnsembleRetriever(<br/>    retrievers=[bm25_retriever, vector_retriever],<br/>    weights=[0.3, 0.7],  # BM25权重0.3，向量权重0.7<br/>)<br/><br/># 使用：0.3 起 Runnable 统一 .invoke()<br/>query = "关于Python的问题"  # 示意：实际来自用户输入<br/>docs = ensemble_retriever.invoke(query)<br/>for doc in docs:<br/>    print(doc.page_content[:60])</code>
```

---

---

按 ownrag 企业级模式组织主链路。核心认知：**闸门、预算、RRF 都是纯代码逻辑——确定性的事不交给模型，把「模型会错」变成可测试的规则集**。这里用伪代码突出六个特殊点；完整可运行实现见参考工程 ownrag（`ai-rag-self-engineering/ownrag/`）。

```
<code># 生产级 RAG 主链路（伪代码：重点在特殊点，不在实现细节）<br/>settings = RAGSettings.from_env()<br/>#   ★特殊点1 配置即代码：全部配置启动期校验，缺 key / 非法值当场报可行动错误<br/>#     ——带病运行到问答中途才失败，是最差的暴露时机<br/><br/>rewritten = rewrite_with_retry(query)<br/>#   ★特殊点2 失败显式降级：改写重试 2 次（指数退避）仍失败 → 降级用原查询继续；<br/>#     降级必须打日志可见，绝不静默吞错<br/><br/>cands = rrf_fuse(<br/>    vector_search(rewritten, top_k=20),   # 向量路：语义邻近<br/>    bm25_search(rewritten, top_k=20),     # 关键词路：精确词（型号/编号/术语）<br/>)<br/>#   ★特殊点3 混合检索按名次融合（RRF）：两路分数量纲不同，直接加权没有意义；<br/>#     单路失败显式降级为另一路并打日志<br/><br/>cands = rerank(query, cands)[:rerank_top_k]<br/>#     CrossEncoder 逐对打分——检索层只能捞回「语义邻近」，相关与否靠重排区分<br/><br/>if cands[0].score &lt; settings.sufficiency_threshold:<br/>    raise NoEvidence<br/>#   ★特殊点4 证据充分性闸门（生成前）：候选为空或最高重排分低于阈值 → 直接拒答；<br/>#     「未找到有效依据」是合法答案，拒答发生在进模型之前，零模型消耗<br/><br/>ctx, dropped = fit_context_budget(cands, settings.num_ctx - 1024)<br/>#   ★特殊点5 上下文预算显式化：先算容量再装块（预留模板/问题/输出开销）；<br/>#     超预算丢尾块，丢块清单随结果返回——不把截断权交给模型侧<br/><br/>answer = llm_generate(prompt(ctx, query))<br/>#     生成时要求每个论断标注 [块N]；上下文没有依据就回答「未找到有效依据」<br/><br/>violations = citation_check(answer, cands)<br/>#   ★特殊点6 引用校验闸门（生成后）：答案中的数字/日期必须能在所引块原文逐字找到；<br/>#     违规 → 带违规清单反馈模型重答一次，仍不通过按规则拒答<br/><br/>return {"answer": answer,<br/>        "sources": dedupe(c["source"] for c in ctx),   # 来源溯源<br/>        "dropped_blocks": dropped}                     # 丢块也可见</code>
```

---

---

ragas 0.2 起用 `EvaluationDataset` 显式构造评测集（`user_input / retrieved_contexts / response / reference` 四字段），`eval_dataset` 必须先定义再评估。

```
<code>from ragas import EvaluationDataset, evaluate<br/>from ragas.metrics import (<br/>    answer_relevancy,<br/>    context_precision,<br/>    context_recall,<br/>    faithfulness,<br/>)<br/><br/># 评测集：用真实问答日志补齐 20~50 条，指标才有置信度<br/>eval_dataset = EvaluationDataset.from_dict([<br/>    {<br/>        "user_input": "公司的年假政策是什么？",<br/>        "retrieved_contexts": ["员工每年享有 5 天带薪年假，工龄满 10 年增至 10 天。"],<br/>        "response": "员工每年享有 5 天带薪年假，工龄满 10 年增至 10 天。[块1]",<br/>        "reference": "每年 5 天带薪年假，工龄满 10 年增至 10 天。",<br/>    },<br/>])<br/><br/># 评估RAG系统<br/>result = evaluate(<br/>    dataset=eval_dataset,<br/>    metrics=[<br/>        faithfulness,<br/>        answer_relevancy,<br/>        context_precision,<br/>        context_recall,<br/>    ],<br/>)<br/><br/>print(result)</code>
```

---

---

RAG是**大模型应用的核心架构**，生产级RAG需要考虑**查询改写、重排序、混合搜索**等多个环节。

**学习要点**：

1. 理解RAG核心流程
1. 掌握文档分块策略
1. 熟练使用向量检索
1. 了解重排序技术
1. 掌握评估方法

### 企业级升级要点

- **配置即代码**：`RAGSettings.from_env()` 启动期校验全部配置，缺 key / 非法值当场报可行动错误——对齐 ownrag 的 `ai-rag-self-engineering/ownrag/ownrag/config.py`（环境变量优先、API key 只走环境变量）。
- **证据充分性闸门**：候选池为空或最高重排分低于阈值直接拒答，零模型消耗——「未找到有效依据」是合法答案，见 `ai-rag-self-engineering/ownrag/ownrag/generate/gates.py` 的 `sufficiency_check`。
- **引用校验闸门**：答案中的数字/日期必须能在所引块原文找到，防数字幻觉，见同文件 `citation_check`；规则进 Git、随评测集回归。
- **上下文预算显式化**：按 token 估算装块、丢块清单随结果返回可见——不把截断权交给模型侧，见 `ai-rag-self-engineering/ownrag/ownrag/generate/budget.py` 的 `fit_candidates`。
- **混合检索 RRF 融合**：向量 + BM25 只按名次融合、不比原始分，等权起步——没有评测集之前调权重都是猜，见 `ai-rag-self-engineering/ownrag/ownrag/retrieve/hybrid.py` 的 `rrf_fuse`。
- **失败显式降级不静默**：向量路、改写、重排失败都打 `[RAG]` 日志并降级继续，绝不静默吞错——对齐 ownrag 重排降级模式 `ai-rag-self-engineering/ownrag/ownrag/retrieve/rerank.py`。

70-企业级工程基准