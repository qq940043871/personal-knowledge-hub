# LangChain详解

> 模块：应用开发框架
> 更新时间：2026-11-15（代码口径：LangChain 1.x 分包架构 + LCEL）

---

## 一、框架介绍与核心价值

LangChain是一个用于构建基于大语言模型应用的开发框架，由Harrison Chase创建于2022年。它提供了一套抽象和工具，帮助开发者快速构建LLM应用。

**官网**：https://python.langchain.com
**GitHub**：https://github.com/langchain-ai/langchain

**核心价值**：
- 简化LLM应用开发
- 组件化和模块化设计
- 丰富的集成生态
- 支持多种LLM和工具

*图：LangChain 核心组件分层（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 280" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <text x="24" y="45" font-size="16" font-weight="bold" fill="#1e293b">应用场景</text>
  <rect x="120" y="20" width="130" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="185" y="45" text-anchor="middle" font-size="13" fill="#1e293b">RAG 问答系统</text>
  <rect x="270" y="20" width="130" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="335" y="45" text-anchor="middle" font-size="13" fill="#1e293b">多步骤 Agent</text>
  <rect x="420" y="20" width="130" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="485" y="45" text-anchor="middle" font-size="13" fill="#1e293b">对话式 Memory</text>
  <rect x="570" y="20" width="130" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="635" y="45" text-anchor="middle" font-size="13" fill="#1e293b">输出解析器</text>
  <line x1="185" y1="62" x2="185" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="335" y1="62" x2="335" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="485" y1="62" x2="485" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="635" y1="62" x2="635" y2="106" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="24" y="135" font-size="16" font-weight="bold" fill="#1e293b">核心抽象</text>
  <rect x="120" y="110" width="130" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="185" y="135" text-anchor="middle" font-size="13" fill="#1e293b">Prompt Template</text>
  <rect x="270" y="110" width="130" height="40" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="335" y="135" text-anchor="middle" font-size="13" fill="#1e293b">Chain 链式调用</text>
  <rect x="420" y="110" width="130" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="485" y="135" text-anchor="middle" font-size="13" fill="#1e293b">Memory 记忆</text>
  <rect x="570" y="110" width="130" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="635" y="135" text-anchor="middle" font-size="13" fill="#1e293b">Agent + Tool</text>
  <line x1="185" y1="152" x2="185" y2="196" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="335" y1="152" x2="335" y2="196" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="485" y1="152" x2="485" y2="196" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="635" y1="152" x2="635" y2="196" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="24" y="227" font-size="16" font-weight="bold" fill="#1e293b">模型与生态</text>
  <rect x="120" y="200" width="580" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="410" y="227" text-anchor="middle" font-size="13" fill="#1e293b">Model I/O（ChatOpenAI 等）· LCEL 表达式语言 · LangSmith 监控调试</text>
</svg>

---

## 二、核心概念：Model I/O、Prompt Template 与 Chain

### 1. Model I/O - 模型交互

```python
# 现行分包：langchain-core（基础抽象）+ langchain-openai（模型集成）
# pip install langchain-core langchain-openai
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# 初始化模型（API key 一律从环境变量读取，禁止硬编码进代码）
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.environ["OPENAI_API_KEY"],
)

# 简单对话：Runnable 接口统一用 .invoke()
response = llm.invoke("用Python写一个快速排序")
print(response.content)

# 带系统提示的对话
chat = llm.invoke([
    SystemMessage(content="你是一个Python编程助手"),
    HumanMessage(content="解释一下闭包")
])
print(chat.content)
```

### 2. Prompt Template - 提示模板

```python
# 提示模板全部来自 langchain_core.prompts
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)

# 创建提示模板
template = ChatPromptTemplate.from_messages([
    ("system", "你是一个{language}编程专家"),
    ("human", "教我如何实现{feature}功能")
])

# 使用模板：LCEL 管道 + .invoke() 传入 dict
chain = template | llm | StrOutputParser()
print(chain.invoke({
    "language": "Python",
    "feature": "装饰器"
}))

# 带示例的提示（few-shot）
examples = [
    {"input": "你好", "output": "你好！有什么可以帮助你的吗？"},
    {"input": "你是谁", "output": "我是一个AI助手。"}
]

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}")
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt
)

# few-shot 模板作为消息段拼进最终 prompt
final_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个简洁的对话助手"),
    few_shot_prompt,
    ("human", "{input}"),
])
few_shot_chain = final_prompt | llm | StrOutputParser()
print(few_shot_chain.invoke({"input": "用一句话介绍装饰器"}))
```

### 3. Chain - 链式调用

```python
# 现行写法：用 LCEL（| 运算符）组装链，取代已废弃的 LLMChain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

chain = (
    ChatPromptTemplate.from_messages([
        ("system", "你是一个{language}编程专家"),
        ("human", "教我如何实现{feature}功能"),
    ])
    | llm
    | StrOutputParser()
)

# 执行链：.invoke() 传入 dict，返回解析后的字符串
result = chain.invoke({
    "language": "Java",
    "feature": "单例模式"
})

print(result)
```

---

## 三、实际业务应用场景

### 场景1：RAG问答系统

RAG 是 LangChain 最典型的应用场景。这里给出现行 API 的**骨架代码**（示意），完整企业级实现见 [06-RAG系统实战](../../06-Agent开发/40-RAG与检索/06-RAG系统实战.md)。

```python
# 现行分包：加载器在 langchain-community，切分器在 langchain-text-splitters，
# Embedding 在 langchain-openai，Chroma 集成在 langchain-chroma
import os

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 加载文档并分块
documents = TextLoader("document.txt").load()
chunks = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
).split_documents(documents)

# 2. 创建向量存储与检索器
vectorstore = Chroma.from_documents(chunks, OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. LCEL 组装 RAG 问答链（取代已废弃的 RetrievalQA）
def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", "仅依据以下检索到的上下文回答问题，无依据时明确说明：\n\n{context}"),
    ("human", "{question}"),
])

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | rag_prompt
    | ChatOpenAI(model="gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"])
    | StrOutputParser()
)

# 4. 问答：.invoke() 传入 dict
question = "这篇文章的主要内容是什么？"
print(rag_chain.invoke({"question": question}))
```

### 场景2：多步骤Agent

Agent 编排在 `langchain` 包，现成工具在 `langchain-community`（这里是真实的 Wikipedia 查询工具，不是 mock）。

```python
# pip install langchain langchain-community wikipedia
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 真实工具：封装 Wikipedia API（langchain_community 提供）
wikipedia_tool = WikipediaQueryRun(
    api_wrapper=WikipediaAPIWrapper(
        top_k_results=2,
        doc_content_chars_max=2000,
        lang="zh",
    )
)
tools = [wikipedia_tool]

# 提示模板：工具调用 Agent 必须带 agent_scratchpad 占位（承接上文的 llm）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个乐于助人的研究助手，回答时注明信息来源"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

# 创建 Agent 与执行器
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 执行
result = agent_executor.invoke({
    "input": "介绍一下Python语言的历史"
})
print(result["output"])
```

> 说明：`AgentExecutor + create_tool_calling_agent` 是 langchain 包内的现行经典写法；更复杂的多智能体编排（状态图、检查点、人工介入）官方已指向 **LangGraph**，见下文 Legacy 对照。

### 场景3：对话式Memory

现行写法是**会话历史 + RunnableWithMessageHistory**（取代已废弃的 ConversationChain/ConversationBufferMemory）。

```python
# 会话历史抽象在 langchain-core，按 session_id 存取
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

# 会话存储：生产环境换成 Redis / SQL 等持久化实现（接口一致）
store: dict[str, InMemoryChatMessageHistory] = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 带 history 占位的对话链（承接上文的 llm）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的助手"),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])
chain = prompt | llm

# 用 RunnableWithMessageHistory 自动注入/回写历史
conversation = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# 同一 session 的两次对话能接上上下文
conversation.invoke(
    {"input": "我叫张三"},
    config={"configurable": {"session_id": "user-123"}},
)
response = conversation.invoke(
    {"input": "我叫什么名字？"},
    config={"configurable": {"session_id": "user-123"}},
)
print(response.content)  # 会记住"张三"
```

### 场景4：输出解析器

```python
# PydanticOutputParser 与 PromptTemplate 均在 langchain_core
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

# 定义输出格式
class Movie(BaseModel):
    title: str = Field(description="电影名称")
    year: int = Field(description="上映年份")
    rating: float = Field(description="评分")

class MovieList(BaseModel):
    movies: list[Movie] = Field(description="电影列表")

# 创建解析器
parser = PydanticOutputParser(pydantic_object=MovieList)

# 创建提示：format_instructions 由解析器生成（含 JSON Schema 说明），承接上文的 llm
prompt = PromptTemplate(
    template="列出三部经典科幻电影及其信息。\n{format_instructions}",
    input_variables=[],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# LCEL 执行（取代已废弃的 LLMChain）
chain = prompt | llm
result = chain.invoke({})

# 解析输出：AIMessage.content 是模型返回的文本
parsed = parser.invoke(result.content)
print(parsed.movies)
```

---

## 四、LangChain生态：LCEL 与 LangSmith

### LangChain表达式语言（LCEL）

```python
# LCEL 核心组件全部来自 langchain_core.runnables / langchain_core.output_parsers
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

# retriever 承接场景1的向量库；RunnableLambda 包装任意函数，
# RunnablePassthrough 原样透传输入，dict 写法实现并行分支
def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", "仅依据以下上下文回答问题，找不到依据时明确说明：\n{context}"),
    ("human", "{question}"),
])

chain = (
    {"context": retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}
    | rag_prompt
    | llm
    | StrOutputParser()
)

# 流式输出
for chunk in chain.stream({"question": "什么是机器学习"}):
    print(chunk, end="", flush=True)
```

### Legacy API 对照（已废弃，官方指向 LangGraph / LCEL）

旧版教程里的单链 API 已全部废弃，迁移只需改导入来源与组装方式，Prompt 与模型调用逻辑不变：

```
已废弃写法                                            现行替代
langchain.chat_models / langchain.schema             langchain-openai / langchain-core.messages
langchain.document_loaders / langchain.embeddings    langchain-community / langchain-openai
langchain.vectorstores.Chroma                        langchain-chroma.Chroma
langchain.text_splitter                              langchain-text-splitters
langchain.chains.LLMChain                            prompt | llm | StrOutputParser()
langchain.chains.RetrievalQA                         {"context": retriever|fmt} | prompt | llm（场景1）
langchain.chains.ConversationChain                   RunnableWithMessageHistory（场景3）
langchain.memory.ConversationBufferMemory            langchain_core.chat_history 会话历史
langchain.runnable.RunnablePassthrough（从未存在）     langchain_core.runnables.RunnablePassthrough
复杂多智能体编排（Agent/状态机/人工介入）               LangGraph（官方新一代 Agent 框架）
```

### LangSmith - 监控和调试

```python
# 设置LangSmith（开关写进代码，密钥只从部署环境注入，不入库）
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "my-project"
# LANGCHAIN_API_KEY 请在终端或部署环境中设置（export LANGCHAIN_API_KEY=...）

# 所有链调用都会自动追踪
# 可以在LangSmith平台上查看调用历史、成本、延迟等
```

---

## 五、总结与学习要点

LangChain是**大模型应用开发的首选框架**，掌握它能快速构建各种LLM应用。

**学习要点**：
1. 理解Model I/O和Prompt Template
2. 掌握Chain的构建方式
3. 熟练使用LCEL表达式语言
4. 理解Agent和Tool的使用
5. 了解Memory和Callback机制

---

### 企业级升级要点

教学示例和企业级 RAG 之间隔的是工程纪律，参考 ownrag 基准工程（D:\ai_person\personal-ai-engineering\ai-rag-self-engineering\ownrag）：

- **密钥与配置**：API key 只走环境变量、配置错误在启动期暴露（配置即代码），参考 `ownrag/config.py`——`OWNRAG_CHAT_API_KEY` 不落任何配置文件。
- **检索工程化**：单路向量检索只是起点，ownrag 用"先过滤后召回 → 向量+BM25 双路 → RRF 名次融合"，见 `ownrag/retrieve/hybrid.py`；重排 provider 可插拔、失败降级可见，见 `ownrag/retrieve/rerank.py`。
- **生成闸门**：候选不足不进模型（拒答是合法答案）、引用块必须在候选池内、数字/日期可在原文核验——两道纯代码闸门见 `ownrag/generate/gates.py`，把"模型会错"变成可测试规则。
- **入库前复核**：解析产物落盘给人看、人工通过才写索引（解析是 RAG 链路最不可控的一段），见 `ownrag/review.py` 与 `ownrag/core/pipeline.py`。
- **评测先行**：没有评测集不调参数，用 RAGAS 指标随回归跑（见本文对应篇目 08-评估测试）。

延伸阅读：[70-企业级工程基准](../../06-Agent开发/70-企业级工程基准.md)

---

*下一步：LlamaIndex专注RAG*
