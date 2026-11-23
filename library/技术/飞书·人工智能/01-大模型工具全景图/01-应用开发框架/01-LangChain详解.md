# LangChain详解

> 模块：应用开发框架  
> 更新时间：2026-11-15（代码口径：LangChain 1.x 分包架构 + LCEL）

---

---

LangChain是一个用于构建基于大语言模型应用的开发框架，由Harrison Chase创建于2022年。它提供了一套抽象和工具，帮助开发者快速构建LLM应用。

**官网**：https://python.langchain.com  
**GitHub**：https://github.com/langchain-ai/langchain

**核心价值**：

- 简化LLM应用开发
- 组件化和模块化设计
- 丰富的集成生态
- 支持多种LLM和工具

*图：LangChain 核心组件分层（示意）*

应用场景RAG 问答系统多步骤 Agent对话式 Memory输出解析器核心抽象Prompt TemplateChain 链式调用Memory 记忆Agent + Tool模型与生态Model I/O（ChatOpenAI 等）· LCEL 表达式语言 · LangSmith 监控调试

---

---

### 1. Model I/O - 模型交互

```
<code># 现行分包：langchain-core（基础抽象）+ langchain-openai（模型集成）<br/># pip install langchain-core langchain-openai<br/>import os<br/><br/>from langchain_core.messages import HumanMessage, SystemMessage<br/>from langchain_openai import ChatOpenAI<br/><br/># 初始化模型（API key 一律从环境变量读取，禁止硬编码进代码）<br/>llm = ChatOpenAI(<br/>    model="gpt-4o-mini",<br/>    temperature=0.7,<br/>    api_key=os.environ["OPENAI_API_KEY"],<br/>)<br/><br/># 简单对话：Runnable 接口统一用 .invoke()<br/>response = llm.invoke("用Python写一个快速排序")<br/>print(response.content)<br/><br/># 带系统提示的对话<br/>chat = llm.invoke([<br/>    SystemMessage(content="你是一个Python编程助手"),<br/>    HumanMessage(content="解释一下闭包")<br/>])<br/>print(chat.content)</code>
```

### 2. Prompt Template - 提示模板

```
<code># 提示模板全部来自 langchain_core.prompts<br/>from langchain_core.output_parsers import StrOutputParser<br/>from langchain_core.prompts import (<br/>    ChatPromptTemplate,<br/>    FewShotChatMessagePromptTemplate,<br/>)<br/><br/># 创建提示模板<br/>template = ChatPromptTemplate.from_messages([<br/>    ("system", "你是一个{language}编程专家"),<br/>    ("human", "教我如何实现{feature}功能")<br/>])<br/><br/># 使用模板：LCEL 管道 + .invoke() 传入 dict<br/>chain = template | llm | StrOutputParser()<br/>print(chain.invoke({<br/>    "language": "Python",<br/>    "feature": "装饰器"<br/>}))<br/><br/># 带示例的提示（few-shot）<br/>examples = [<br/>    {"input": "你好", "output": "你好！有什么可以帮助你的吗？"},<br/>    {"input": "你是谁", "output": "我是一个AI助手。"}<br/>]<br/><br/>example_prompt = ChatPromptTemplate.from_messages([<br/>    ("human", "{input}"),<br/>    ("ai", "{output}")<br/>])<br/><br/>few_shot_prompt = FewShotChatMessagePromptTemplate(<br/>    examples=examples,<br/>    example_prompt=example_prompt<br/>)<br/><br/># few-shot 模板作为消息段拼进最终 prompt<br/>final_prompt = ChatPromptTemplate.from_messages([<br/>    ("system", "你是一个简洁的对话助手"),<br/>    few_shot_prompt,<br/>    ("human", "{input}"),<br/>])<br/>few_shot_chain = final_prompt | llm | StrOutputParser()<br/>print(few_shot_chain.invoke({"input": "用一句话介绍装饰器"}))</code>
```

### 3. Chain - 链式调用

```
<code># 现行写法：用 LCEL（| 运算符）组装链，取代已废弃的 LLMChain<br/>from langchain_core.output_parsers import StrOutputParser<br/>from langchain_core.prompts import ChatPromptTemplate<br/><br/>chain = (<br/>    ChatPromptTemplate.from_messages([<br/>        ("system", "你是一个{language}编程专家"),<br/>        ("human", "教我如何实现{feature}功能"),<br/>    ])<br/>    | llm<br/>    | StrOutputParser()<br/>)<br/><br/># 执行链：.invoke() 传入 dict，返回解析后的字符串<br/>result = chain.invoke({<br/>    "language": "Java",<br/>    "feature": "单例模式"<br/>})<br/><br/>print(result)</code>
```

---

---

### 场景1：RAG问答系统

RAG 是 LangChain 最典型的应用场景。这里给出现行 API 的**骨架代码**（示意），完整企业级实现见 06-RAG系统实战。

```
<code># 现行分包：加载器在 langchain-community，切分器在 langchain-text-splitters，<br/># Embedding 在 langchain-openai，Chroma 集成在 langchain-chroma<br/>import os<br/><br/>from langchain_chroma import Chroma<br/>from langchain_community.document_loaders import TextLoader<br/>from langchain_core.output_parsers import StrOutputParser<br/>from langchain_core.prompts import ChatPromptTemplate<br/>from langchain_core.runnables import RunnablePassthrough<br/>from langchain_openai import ChatOpenAI, OpenAIEmbeddings<br/>from langchain_text_splitters import RecursiveCharacterTextSplitter<br/><br/># 1. 加载文档并分块<br/>documents = TextLoader("document.txt").load()<br/>chunks = RecursiveCharacterTextSplitter(<br/>    chunk_size=1000,<br/>    chunk_overlap=200<br/>).split_documents(documents)<br/><br/># 2. 创建向量存储与检索器<br/>vectorstore = Chroma.from_documents(chunks, OpenAIEmbeddings())<br/>retriever = vectorstore.as_retriever(search_kwargs={"k": 3})<br/><br/># 3. LCEL 组装 RAG 问答链（取代已废弃的 RetrievalQA）<br/>def format_docs(docs):<br/>    return "\n\n".join(d.page_content for d in docs)<br/><br/>rag_prompt = ChatPromptTemplate.from_messages([<br/>    ("system", "仅依据以下检索到的上下文回答问题，无依据时明确说明：\n\n{context}"),<br/>    ("human", "{question}"),<br/>])<br/><br/>rag_chain = (<br/>    {"context": retriever | format_docs, "question": RunnablePassthrough()}<br/>    | rag_prompt<br/>    | ChatOpenAI(model="gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"])<br/>    | StrOutputParser()<br/>)<br/><br/># 4. 问答：.invoke() 传入 dict<br/>question = "这篇文章的主要内容是什么？"<br/>print(rag_chain.invoke({"question": question}))</code>
```

### 场景2：多步骤Agent

Agent 编排在 `langchain` 包，现成工具在 `langchain-community`（这里是真实的 Wikipedia 查询工具，不是 mock）。

```
<code># pip install langchain langchain-community wikipedia<br/>from langchain.agents import AgentExecutor, create_tool_calling_agent<br/>from langchain_community.tools import WikipediaQueryRun<br/>from langchain_community.utilities import WikipediaAPIWrapper<br/>from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder<br/><br/># 真实工具：封装 Wikipedia API（langchain_community 提供）<br/>wikipedia_tool = WikipediaQueryRun(<br/>    api_wrapper=WikipediaAPIWrapper(<br/>        top_k_results=2,<br/>        doc_content_chars_max=2000,<br/>        lang="zh",<br/>    )<br/>)<br/>tools = [wikipedia_tool]<br/><br/># 提示模板：工具调用 Agent 必须带 agent_scratchpad 占位（承接上文的 llm）<br/>prompt = ChatPromptTemplate.from_messages([<br/>    ("system", "你是一个乐于助人的研究助手，回答时注明信息来源"),<br/>    ("human", "{input}"),<br/>    MessagesPlaceholder("agent_scratchpad"),<br/>])<br/><br/># 创建 Agent 与执行器<br/>agent = create_tool_calling_agent(llm, tools, prompt)<br/>agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)<br/><br/># 执行<br/>result = agent_executor.invoke({<br/>    "input": "介绍一下Python语言的历史"<br/>})<br/>print(result["output"])</code>
```

> 说明：`AgentExecutor + create_tool_calling_agent` 是 langchain 包内的现行经典写法；更复杂的多智能体编排（状态图、检查点、人工介入）官方已指向 **LangGraph**，见下文 Legacy 对照。

### 场景3：对话式Memory

现行写法是**会话历史 + RunnableWithMessageHistory**（取代已废弃的 ConversationChain/ConversationBufferMemory）。

```
<code># 会话历史抽象在 langchain-core，按 session_id 存取<br/>from langchain_core.chat_history import InMemoryChatMessageHistory<br/>from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder<br/>from langchain_core.runnables.history import RunnableWithMessageHistory<br/><br/># 会话存储：生产环境换成 Redis / SQL 等持久化实现（接口一致）<br/>store: dict[str, InMemoryChatMessageHistory] = {}<br/><br/>def get_session_history(session_id: str) -&gt; InMemoryChatMessageHistory:<br/>    if session_id not in store:<br/>        store[session_id] = InMemoryChatMessageHistory()<br/>    return store[session_id]<br/><br/># 带 history 占位的对话链（承接上文的 llm）<br/>prompt = ChatPromptTemplate.from_messages([<br/>    ("system", "你是一个友好的助手"),<br/>    MessagesPlaceholder("history"),<br/>    ("human", "{input}"),<br/>])<br/>chain = prompt | llm<br/><br/># 用 RunnableWithMessageHistory 自动注入/回写历史<br/>conversation = RunnableWithMessageHistory(<br/>    chain,<br/>    get_session_history,<br/>    input_messages_key="input",<br/>    history_messages_key="history",<br/>)<br/><br/># 同一 session 的两次对话能接上上下文<br/>conversation.invoke(<br/>    {"input": "我叫张三"},<br/>    config={"configurable": {"session_id": "user-123"}},<br/>)<br/>response = conversation.invoke(<br/>    {"input": "我叫什么名字？"},<br/>    config={"configurable": {"session_id": "user-123"}},<br/>)<br/>print(response.content)  # 会记住"张三"</code>
```

### 场景4：输出解析器

```
<code># PydanticOutputParser 与 PromptTemplate 均在 langchain_core<br/>from langchain_core.output_parsers import PydanticOutputParser<br/>from langchain_core.prompts import PromptTemplate<br/>from pydantic import BaseModel, Field<br/><br/># 定义输出格式<br/>class Movie(BaseModel):<br/>    title: str = Field(description="电影名称")<br/>    year: int = Field(description="上映年份")<br/>    rating: float = Field(description="评分")<br/><br/>class MovieList(BaseModel):<br/>    movies: list[Movie] = Field(description="电影列表")<br/><br/># 创建解析器<br/>parser = PydanticOutputParser(pydantic_object=MovieList)<br/><br/># 创建提示：format_instructions 由解析器生成（含 JSON Schema 说明），承接上文的 llm<br/>prompt = PromptTemplate(<br/>    template="列出三部经典科幻电影及其信息。\n{format_instructions}",<br/>    input_variables=[],<br/>    partial_variables={"format_instructions": parser.get_format_instructions()}<br/>)<br/><br/># LCEL 执行（取代已废弃的 LLMChain）<br/>chain = prompt | llm<br/>result = chain.invoke({})<br/><br/># 解析输出：AIMessage.content 是模型返回的文本<br/>parsed = parser.invoke(result.content)<br/>print(parsed.movies)</code>
```

---

---

### LangChain表达式语言（LCEL）

```
<code># LCEL 核心组件全部来自 langchain_core.runnables / langchain_core.output_parsers<br/>from langchain_core.output_parsers import StrOutputParser<br/>from langchain_core.prompts import ChatPromptTemplate<br/>from langchain_core.runnables import RunnableLambda, RunnablePassthrough<br/><br/># retriever 承接场景1的向量库；RunnableLambda 包装任意函数，<br/># RunnablePassthrough 原样透传输入，dict 写法实现并行分支<br/>def format_docs(docs):<br/>    return "\n\n".join(d.page_content for d in docs)<br/><br/>rag_prompt = ChatPromptTemplate.from_messages([<br/>    ("system", "仅依据以下上下文回答问题，找不到依据时明确说明：\n{context}"),<br/>    ("human", "{question}"),<br/>])<br/><br/>chain = (<br/>    {"context": retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}<br/>    | rag_prompt<br/>    | llm<br/>    | StrOutputParser()<br/>)<br/><br/># 流式输出<br/>for chunk in chain.stream({"question": "什么是机器学习"}):<br/>    print(chunk, end="", flush=True)</code>
```

### Legacy API 对照（已废弃，官方指向 LangGraph / LCEL）

旧版教程里的单链 API 已全部废弃，迁移只需改导入来源与组装方式，Prompt 与模型调用逻辑不变：

```
<code>已废弃写法                                            现行替代<br/>langchain.chat_models / langchain.schema             langchain-openai / langchain-core.messages<br/>langchain.document_loaders / langchain.embeddings    langchain-community / langchain-openai<br/>langchain.vectorstores.Chroma                        langchain-chroma.Chroma<br/>langchain.text_splitter                              langchain-text-splitters<br/>langchain.chains.LLMChain                            prompt | llm | StrOutputParser()<br/>langchain.chains.RetrievalQA                         {"context": retriever|fmt} | prompt | llm（场景1）<br/>langchain.chains.ConversationChain                   RunnableWithMessageHistory（场景3）<br/>langchain.memory.ConversationBufferMemory            langchain_core.chat_history 会话历史<br/>langchain.runnable.RunnablePassthrough（从未存在）     langchain_core.runnables.RunnablePassthrough<br/>复杂多智能体编排（Agent/状态机/人工介入）               LangGraph（官方新一代 Agent 框架）</code>
```

### LangSmith - 监控和调试

```
<code># 设置LangSmith（开关写进代码，密钥只从部署环境注入，不入库）<br/>import os<br/>os.environ["LANGCHAIN_TRACING_V2"] = "true"<br/>os.environ["LANGCHAIN_PROJECT"] = "my-project"<br/># LANGCHAIN_API_KEY 请在终端或部署环境中设置（export LANGCHAIN_API_KEY=...）<br/><br/># 所有链调用都会自动追踪<br/># 可以在LangSmith平台上查看调用历史、成本、延迟等</code>
```

---

---

LangChain是**大模型应用开发的首选框架**，掌握它能快速构建各种LLM应用。

**学习要点**：

1. 理解Model I/O和Prompt Template
1. 掌握Chain的构建方式
1. 熟练使用LCEL表达式语言
1. 理解Agent和Tool的使用
1. 了解Memory和Callback机制

---

---

教学示例和企业级 RAG 之间隔的是工程纪律，参考 ownrag 基准工程：

- **密钥与配置**：API key 只走环境变量、配置错误在启动期暴露（配置即代码），参考 `ownrag/config.py`——`OWNRAG_CHAT_API_KEY` 不落任何配置文件。
- **检索工程化**：单路向量检索只是起点，ownrag 用"先过滤后召回 → 向量+BM25 双路 → RRF 名次融合"，见 `ownrag/retrieve/hybrid.py`；重排 provider 可插拔、失败降级可见，见 `ownrag/retrieve/rerank.py`。
- **生成闸门**：候选不足不进模型（拒答是合法答案）、引用块必须在候选池内、数字/日期可在原文核验——两道纯代码闸门见 `ownrag/generate/gates.py`，把"模型会错"变成可测试规则。
- **入库前复核**：解析产物落盘给人看、人工通过才写索引（解析是 RAG 链路最不可控的一段），见 `ownrag/review.py` 与 `ownrag/core/pipeline.py`。
- **评测先行**：没有评测集不调参数，用 RAGAS 指标随回归跑（见本文对应篇目 08-评估测试）。

延伸阅读：70-企业级工程基准

---

---