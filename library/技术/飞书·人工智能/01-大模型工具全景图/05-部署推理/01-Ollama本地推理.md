# Ollama本地推理

> 模块：部署推理
> 更新时间：2026-03-29

---

## 一、框架介绍与核心特点

Ollama是**本地运行大语言模型的工具**，让你无需云服务即可在本地运行各种开源模型。

**官网**：https://ollama.ai
**GitHub**：https://github.com/ollama/ollama

**核心特点**：
- 一键运行模型
- 支持多种开源模型
- 跨平台支持
- 简洁API
- 资源高效利用

*图：Ollama 本地推理链路（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 120" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="8" y="30" width="158" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="87" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">① 获取模型</text>
  <text x="87" y="73" text-anchor="middle" font-size="13" fill="#475569">ollama pull · GGUF 导入</text>
  <line x1="166" y1="58" x2="188" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="30" width="158" height="56" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="269" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">② Ollama 运行时</text>
  <text x="269" y="73" text-anchor="middle" font-size="13" fill="#475569">本地运行，无需云服务</text>
  <line x1="348" y1="58" x2="370" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="372" y="30" width="158" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="451" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">③ 两种调用方式</text>
  <text x="451" y="73" text-anchor="middle" font-size="13" fill="#475569">CLI：ollama run · API</text>
  <line x1="530" y1="58" x2="552" y2="58" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="554" y="30" width="158" height="56" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="633" y="53" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">④ 本地应用</text>
  <text x="633" y="73" text-anchor="middle" font-size="13" fill="#475569">本地对话 / RAG 问答</text>
</svg>

---

## 二、快速开始：安装、运行模型与 API 调用

### 1. 安装

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows（通过WSL或Docker）
docker pull ollama/ollama

# 验证安装
ollama --version
```

### 2. 运行模型

```bash
# 拉取并运行模型
ollama run llama3

# 其他可用模型
ollama run mistral        # 7B模型
ollama run mixtral        # 8x7B MoE
ollama run codellama      # 代码模型
ollama run phi            # 微软小模型
ollama run gemma          # Google模型
ollama run qwen           # 阿里模型
ollama run deepseek-llm   # 深度求索模型

# 指定参数
ollama run llama3:latest "解释什么是机器学习" --verbose
```

### 3. API使用

```python
import ollama

# 简单对话
response = ollama.chat(
    model='llama3',
    messages=[
        {'role': 'user', 'content': '用Python写一个快排'}
    ]
)
print(response['message']['content'])

# 流式输出
stream = ollama.chat(
    model='llama3',
    messages=[{'role': 'user', 'content': '写一首诗'}],
    stream=True
)
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
```

---

## 三、实际业务应用场景

### 场景1：本地RAG系统

```python
import ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA

# 使用Ollama模型
llm = Ollama(model="llama3")

# 使用Ollama Embedding
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 创建向量存储
from langchain_community.vectorstores import Chroma

vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# RAG问答
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)

result = qa.invoke("什么是Python？")
print(result["result"])
```

### 场景2：中文模型使用

```bash
# 拉取中文模型
ollama pull qwen:7b
ollama pull deepseek-coder:6.7b
ollama pull yi:6b

# 运行中文模型
ollama run qwen:7b "写一段关于春天的散文"
```

### 场景3：自定义模型

```bash
# 导入GGUF格式模型
ollama create my-model -f ./Modelfile

# Modelfile示例
FROM ./llama3-8b.Q4_K_M.gguf
PARAMETER temperature 0.7
PARAMETER top_p 0
```
