# LangChain 快速学习手册

## 📋 概述

LangChain 是一个用于构建 LLM 应用的开发框架，提供模块化组件，支持 Chains、Agents、Memory、Tools 等核心功能。

**定位对比：**
- Dify = "记忆管理的成品解决方案"（低代码）
- LangChain = "记忆管理的乐高积木"（高灵活度）

## 🏗️ 核心架构

```
┌─────────────────────────────────────────────────────┐
│                   LangChain 架构                      │
├─────────────────────────────────────────────────────┤
│  应用层: Agent │ Chain │ Tool │ Memory             │
├─────────────────────────────────────────────────────┤
│  模型层: ChatGPT │ Llama │ SiliconFlow │ Ollama   │
├─────────────────────────────────────────────────────┤
│  数据层: DocumentLoader │ VectorStore │ Embeddings │
├─────────────────────────────────────────────────────┤
│  工具层: Search │ API │ Database │ FileSystem      │
└─────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 安装

```bash
pip install langchain langchain-community langchain-core
pip install langchain[openai]  # 如果使用 OpenAI
```

### 2. 基本使用

```python
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# 初始化聊天模型
chat = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

# 发送消息（新版统一用 .invoke()）
response = chat.invoke([HumanMessage(content="你好，请介绍一下自己")])
print(response.content)
```

## 📚 项目代码示例

项目中包含 `03_langchain` 目录下的多个完整示例。

### 1. SiliconFlow LLM 封装

```python
import requests
from typing import Optional, List
from langchain_core.llms import LLM
from langchain_core.callbacks import CallbackManagerForLLMRun

class SiliconFlowLLM(LLM):
    """SiliconFlow LLM 的 LangChain 集成（伪代码骨架）"""

    def __init__(self, api_key: str, model_id: str = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
                 temperature: float = 0.7, max_tokens: int = 512):
        #   ★特殊点1 api_key 由调用方传入，只走 os.environ，不写死
        self.api_key = api_key
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None
    ) -> str:
        # 组装 OpenAI 兼容请求体（model / messages / temperature / max_tokens）
        data = {"model": self.model_id, "messages": [{"role": "user", "content": prompt}]}
        if stop:
            data["stop"] = stop  #   ★特殊点2 停止词透传
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        #   ★特殊点3 SiliconFlow 走 OpenAI 兼容协议，响应结构与 OpenAI 一致
        return response.json()["choices"][0]["message"]["content"]

    @property
    def _llm_type(self) -> str:
        return "siliconflow"
```

### 2. SiliconFlow Embeddings 封装

```python
from langchain_core.embeddings import Embeddings

class SiliconFlowEmbeddings(Embeddings):
    """SiliconFlow嵌入模型的LangChain集成"""

    def __init__(self, api_key: str, model_id: str = "BAAI/bge-large-en-v1.5"):
        self.api_key = api_key
        self.model_id = model_id
        self.api_url = "https://api.siliconflow.cn/v1/embeddings"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model_id,
            "input": texts
        }

        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()

        return [item["embedding"] for item in response.json()["data"]]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]
```

### 3. 完整 RAG 服务实现

```python
import os
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.llms import LLM
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

class RAGService:
    """使用 SiliconFlow 的 RAG 服务实现（伪代码骨架）"""

    def __init__(self, data_dir="./data", vector_db_dir="./vector_db", **config):
        #   ★特殊点1 key 只走 os.environ，不写死在代码里
        self.embeddings = SiliconFlowEmbeddings(api_key=os.environ["SILICONFLOW_API_KEY"])
        self.llm = SiliconFlowLLM(api_key=os.environ["SILICONFLOW_API_KEY"])

    def load_and_split_documents(self) -> List[Document]:
        # DirectoryLoader(glob="*.txt", loader_cls=TextLoader, encoding="utf-8") 加载
        # RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50) 切分
        ...

    def create_vector_store(self, splits: List[Document]) -> Chroma:
        #   ★特殊点2 persist_directory 持久化到本地，重启免重建索引
        ...

    def initialize_qa_chain(self):
        # 已有持久化索引则直接加载，否则先走 load_and_split_documents 重建
        ...
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(),
            #   ★特殊点3 中文提示词模板（基于上下文回答 question）
            chain_type_kwargs={"prompt": PromptTemplate(...)},
        )

    def answer_query(self, query: str) -> Dict[str, Any]:
        #   ★特殊点4 新版统一 .invoke() 调用，替代旧的 chain({...}) 字典调用
        result = self.qa_chain.invoke({"query": query})
        return {"question": query, "answer": result["result"], "source_documents": ...}
```

### 4. 多 Agent 系统

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

class MultiAgentSystem:
    """多Agent协作系统"""

    def __init__(self):
        self.agents = {}
        self.memory = ConversationBufferMemory()

    def register_agent(self, name: str, tools: List[Tool], system_prompt: str):
        """注册Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )

        self.agents[name] = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            memory=self.memory,
            verbose=True
        )

    def run(self, agent_name: str, input_text: str) -> str:
        """运行指定Agent"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} 未注册")

        result = self.agents[agent_name].invoke({"input": input_text})
        return result["output"]
```

## 🔧 核心组件详解

### 1. Chains

| Chain 类型 | 用途 |
|-----------|------|
| LLMChain | 简单 Prompt + LLM |
| RetrievalQA | RAG 问答 |
| ConversationChain | 对话 |
| SQLDatabaseChain | SQL 查询 |

### 2. Memory 类型

| Memory 类型 | 特点 |
|-------------|------|
| BufferMemory | 完整保留对话 |
| SummaryMemory | 生成摘要 |
| EntityMemory | 实体跟踪 |
| VectorStoreMemory | 向量检索历史 |

### 3. Embeddings 模型选择

| 模型 | 维度 | 适用语言 |
|------|------|---------|
| BAAI/bge-large-zh | 1024 | 中文 |
| BAAI/bge-large-en | 1024 | 英文 |
| sentence-transformers | 可变 | 多语言 |

## 🐛 常见问题

### Q: 导入报错？

```python
# 新版本 LangChain 导入路径变更
# 旧版本
from langchain.document_loaders import TextLoader
from langchain.vectorstores import Chroma

# 新版本
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
```

### Q: 向量数据库选择？

```python
# Chroma (轻量级，本地存储)
from langchain_community.vectorstores import Chroma

# Milvus (生产级，分布式)
from langchain_community.vectorstores import Milvus

# Pinecone (云服务)
from langchain_community.vectorstores import Pinecone
```

### Q: 如何提高检索质量？

```python
# 1. 调整分割大小
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # 减小chunk提高精度
    chunk_overlap=50
)

# 2. 优化检索数量
retriever = vector_store.as_retriever(
    search_kwargs={"k": 5}  # 检索更多相关文档
)

# 3. 使用 MMR 检索
retriever = vector_store.as_retriever(
    search_type="mmr",  # 最大边际相关
    search_kwargs={"k": 5, "fetch_k": 20}
)
```

## 📚 相关资源

- 官方文档: https://python.langchain.com/
- GitHub: https://github.com/langchain-ai/langchain
- 示例代码: `03_langchain/` 目录
