## 📋 概述

LangChain 是一个用于构建 LLM 应用的开发框架，提供模块化组件，支持 Chains、Agents、Memory、Tools 等核心功能。

**定位对比：**

- Dify = "记忆管理的成品解决方案"（低代码）
- LangChain = "记忆管理的乐高积木"（高灵活度）

## 🏗️ 核心架构

```
<code>┌─────────────────────────────────────────────────────┐<br/>│                   LangChain 架构                      │<br/>├─────────────────────────────────────────────────────┤<br/>│  应用层: Agent │ Chain │ Tool │ Memory             │<br/>├─────────────────────────────────────────────────────┤<br/>│  模型层: ChatGPT │ Llama │ SiliconFlow │ Ollama   │<br/>├─────────────────────────────────────────────────────┤<br/>│  数据层: DocumentLoader │ VectorStore │ Embeddings │<br/>├─────────────────────────────────────────────────────┤<br/>│  工具层: Search │ API │ Database │ FileSystem      │<br/>└─────────────────────────────────────────────────────┘</code>
```

## 🚀 快速开始

### 1. 安装

```
<code>pip install langchain langchain-community langchain-core<br/>pip install langchain[openai]  # 如果使用 OpenAI</code>
```

### 2. 基本使用

```
<code>from langchain_core.messages import HumanMessage<br/>from langchain_openai import ChatOpenAI<br/><br/># 初始化聊天模型<br/>chat = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")<br/><br/># 发送消息（新版统一用 .invoke()）<br/>response = chat.invoke([HumanMessage(content="你好，请介绍一下自己")])<br/>print(response.content)</code>
```

## 📚 项目代码示例

项目中包含 `03_langchain` 目录下的多个完整示例。

### 1. SiliconFlow LLM 封装

```
<code>import requests<br/>from typing import Optional, List<br/>from langchain_core.llms import LLM<br/>from langchain_core.callbacks import CallbackManagerForLLMRun<br/><br/>class SiliconFlowLLM(LLM):<br/>    """SiliconFlow LLM 的 LangChain 集成（伪代码骨架）"""<br/><br/>    def __init__(self, api_key: str, model_id: str = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",<br/>                 temperature: float = 0.7, max_tokens: int = 512):<br/>        #   ★特殊点1 api_key 由调用方传入，只走 os.environ，不写死<br/>        self.api_key = api_key<br/>        self.model_id = model_id<br/>        self.temperature = temperature<br/>        self.max_tokens = max_tokens<br/>        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"<br/><br/>    def _call(<br/>        self,<br/>        prompt: str,<br/>        stop: Optional[List[str]] = None,<br/>        run_manager: Optional[CallbackManagerForLLMRun] = None<br/>    ) -&gt; str:<br/>        # 组装 OpenAI 兼容请求体（model / messages / temperature / max_tokens）<br/>        data = {"model": self.model_id, "messages": [{"role": "user", "content": prompt}]}<br/>        if stop:<br/>            data["stop"] = stop  #   ★特殊点2 停止词透传<br/>        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}<br/>        response = requests.post(self.api_url, headers=headers, json=data)<br/>        response.raise_for_status()<br/>        #   ★特殊点3 SiliconFlow 走 OpenAI 兼容协议，响应结构与 OpenAI 一致<br/>        return response.json()["choices"][0]["message"]["content"]<br/><br/>    @property<br/>    def _llm_type(self) -&gt; str:<br/>        return "siliconflow"</code>
```

### 2. SiliconFlow Embeddings 封装

```
<code>from langchain_core.embeddings import Embeddings<br/><br/>class SiliconFlowEmbeddings(Embeddings):<br/>    """SiliconFlow嵌入模型的LangChain集成"""<br/><br/>    def __init__(self, api_key: str, model_id: str = "BAAI/bge-large-en-v1.5"):<br/>        self.api_key = api_key<br/>        self.model_id = model_id<br/>        self.api_url = "https://api.siliconflow.cn/v1/embeddings"<br/><br/>    def embed_documents(self, texts: List[str]) -&gt; List[List[float]]:<br/>        headers = {<br/>            "Content-Type": "application/json",<br/>            "Authorization": f"Bearer {self.api_key}"<br/>        }<br/><br/>        data = {<br/>            "model": self.model_id,<br/>            "input": texts<br/>        }<br/><br/>        response = requests.post(self.api_url, headers=headers, json=data)<br/>        response.raise_for_status()<br/><br/>        return [item["embedding"] for item in response.json()["data"]]<br/><br/>    def embed_query(self, text: str) -&gt; List[float]:<br/>        return self.embed_documents([text])[0]</code>
```

### 3. 完整 RAG 服务实现

```
<code>import os<br/>from typing import List, Dict, Any<br/>from langchain_core.documents import Document<br/>from langchain_core.embeddings import Embeddings<br/>from langchain_core.llms import LLM<br/>from langchain_core.prompts import PromptTemplate<br/>from langchain_text_splitters import RecursiveCharacterTextSplitter<br/>from langchain_community.document_loaders import DirectoryLoader, TextLoader<br/>from langchain_community.vectorstores import Chroma<br/>from langchain.chains import RetrievalQA<br/><br/>class RAGService:<br/>    """使用 SiliconFlow 的 RAG 服务实现（伪代码骨架）"""<br/><br/>    def __init__(self, data_dir="./data", vector_db_dir="./vector_db", **config):<br/>        #   ★特殊点1 key 只走 os.environ，不写死在代码里<br/>        self.embeddings = SiliconFlowEmbeddings(api_key=os.environ["SILICONFLOW_API_KEY"])<br/>        self.llm = SiliconFlowLLM(api_key=os.environ["SILICONFLOW_API_KEY"])<br/><br/>    def load_and_split_documents(self) -&gt; List[Document]:<br/>        # DirectoryLoader(glob="*.txt", loader_cls=TextLoader, encoding="utf-8") 加载<br/>        # RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50) 切分<br/>        ...<br/><br/>    def create_vector_store(self, splits: List[Document]) -&gt; Chroma:<br/>        #   ★特殊点2 persist_directory 持久化到本地，重启免重建索引<br/>        ...<br/><br/>    def initialize_qa_chain(self):<br/>        # 已有持久化索引则直接加载，否则先走 load_and_split_documents 重建<br/>        ...<br/>        self.qa_chain = RetrievalQA.from_chain_type(<br/>            llm=self.llm,<br/>            chain_type="stuff",<br/>            retriever=self.vector_store.as_retriever(),<br/>            #   ★特殊点3 中文提示词模板（基于上下文回答 question）<br/>            chain_type_kwargs={"prompt": PromptTemplate(...)},<br/>        )<br/><br/>    def answer_query(self, query: str) -&gt; Dict[str, Any]:<br/>        #   ★特殊点4 新版统一 .invoke() 调用，替代旧的 chain({...}) 字典调用<br/>        result = self.qa_chain.invoke({"query": query})<br/>        return {"question": query, "answer": result["result"], "source_documents": ...}</code>
```

### 4. 多 Agent 系统

```
<code>from langchain.agents import AgentExecutor, create_openai_tools_agent<br/>from langchain_core.messages import BaseMessage, HumanMessage<br/>from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder<br/>from langchain.memory import ConversationBufferMemory<br/><br/>class MultiAgentSystem:<br/>    """多Agent协作系统"""<br/><br/>    def __init__(self):<br/>        self.agents = {}<br/>        self.memory = ConversationBufferMemory()<br/><br/>    def register_agent(self, name: str, tools: List[Tool], system_prompt: str):<br/>        """注册Agent"""<br/>        prompt = ChatPromptTemplate.from_messages([<br/>            ("system", system_prompt),<br/>            MessagesPlaceholder(variable_name="chat_history", optional=True),<br/>            ("human", "{input}"),<br/>            MessagesPlaceholder(variable_name="agent_scratchpad")<br/>        ])<br/><br/>        agent = create_openai_tools_agent(<br/>            llm=self.llm,<br/>            tools=tools,<br/>            prompt=prompt<br/>        )<br/><br/>        self.agents[name] = AgentExecutor.from_agent_and_tools(<br/>            agent=agent,<br/>            tools=tools,<br/>            memory=self.memory,<br/>            verbose=True<br/>        )<br/><br/>    def run(self, agent_name: str, input_text: str) -&gt; str:<br/>        """运行指定Agent"""<br/>        if agent_name not in self.agents:<br/>            raise ValueError(f"Agent {agent_name} 未注册")<br/><br/>        result = self.agents[agent_name].invoke({"input": input_text})<br/>        return result["output"]</code>
```

## 🔧 核心组件详解

### 1. Chains

| th | th |
| --- | --- |
| td | td |
| td | td |
| td | td |
| td | td |

### 2. Memory 类型

| th | th |
| --- | --- |
| td | td |
| td | td |
| td | td |
| td | td |

### 3. Embeddings 模型选择

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |

## 🐛 常见问题

### Q: 导入报错？

```
<code># 新版本 LangChain 导入路径变更<br/># 旧版本<br/>from langchain.document_loaders import TextLoader<br/>from langchain.vectorstores import Chroma<br/><br/># 新版本<br/>from langchain_community.document_loaders import TextLoader<br/>from langchain_community.vectorstores import Chroma</code>
```

### Q: 向量数据库选择？

```
<code># Chroma (轻量级，本地存储)<br/>from langchain_community.vectorstores import Chroma<br/><br/># Milvus (生产级，分布式)<br/>from langchain_community.vectorstores import Milvus<br/><br/># Pinecone (云服务)<br/>from langchain_community.vectorstores import Pinecone</code>
```

### Q: 如何提高检索质量？

```
<code># 1. 调整分割大小<br/>text_splitter = RecursiveCharacterTextSplitter(<br/>    chunk_size=500,  # 减小chunk提高精度<br/>    chunk_overlap=50<br/>)<br/><br/># 2. 优化检索数量<br/>retriever = vector_store.as_retriever(<br/>    search_kwargs={"k": 5}  # 检索更多相关文档<br/>)<br/><br/># 3. 使用 MMR 检索<br/>retriever = vector_store.as_retriever(<br/>    search_type="mmr",  # 最大边际相关<br/>    search_kwargs={"k": 5, "fetch_k": 20}<br/>)</code>
```

## 📚 相关资源

- 官方文档: [https://python.langchain.com/](https://python.langchain.com/)
- GitHub: [https://github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain)
- 示例代码: `03_langchain/` 目录