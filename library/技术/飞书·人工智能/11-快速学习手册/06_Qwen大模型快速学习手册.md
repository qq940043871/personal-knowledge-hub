## 📋 概述

Qwen（通义千问）是阿里云开发的大语言模型系列，支持多种参数规模，可本地部署或通过 API 调用。

## 🏗️ 模型系列

```
<code>┌─────────────────────────────────────────────────────┐<br/>│                  Qwen 模型家族                        │<br/>├─────────────────────────────────────────────────────┤<br/>│  Qwen2.5      │  最新一代，支持超长上下文            │<br/>│  Qwen2        │  高性能，支持128K上下文             │<br/>│  Qwen1.5      │  轻量级，适合本地部署               │<br/>│  Qwen-Max     │  超大规模，云端专用                 │<br/>├─────────────────────────────────────────────────────┤<br/>│  参数规模: 0.5B / 1.5B / 7B / 14B / 72B / 110B    │<br/>└─────────────────────────────────────────────────────┘</code>
```

## 🚀 快速开始

### 1. Ollama 本地部署

```
<code># 安装 Ollama<br/># macOS/Linux: brew install ollama<br/># Windows: 下载安装包<br/><br/># 拉取 Qwen 模型<br/>ollama pull qwen2.5:0.5b<br/>ollama pull qwen2.5:7b<br/>ollama pull qwen2.5:14b<br/><br/># 运行模型<br/>ollama run qwen2.5:7b</code>
```

### 2. API 调用

```
<code>import requests<br/><br/>response = requests.post(<br/>    "http://localhost:11434/api/generate",<br/>    json={<br/>        "model": "qwen2.5:7b",<br/>        "prompt": "你好，请介绍一下自己",<br/>        "stream": False<br/>    }<br/>)<br/><br/>print(response.json()["response"])</code>
```

## 📚 项目代码示例

### 1. LangChain + Ollama + Qwen

```
<code>from langchain_community.llms import Ollama<br/>from langchain.chains import RetrievalQA<br/>from langchain_community.vectorstores import Chroma<br/>from langchain_community.embeddings import HuggingFaceEmbeddings<br/><br/># 初始化 Qwen 模型<br/>ollama = Ollama(model="qwen2.5:0.5b")<br/><br/># 创建 RAG 问答链<br/>qa_chain = RetrievalQA.from_chain_type(<br/>    llm=ollama,<br/>    chain_type="stuff",<br/>    retriever=vector_store.as_retriever()<br/>)<br/><br/># 查询<br/>result = qa_chain({"query": "什么是人工智能？"})<br/>print(result["result"])</code>
```

### 2. SiliconFlow API 调用 Qwen

```
<code>import requests<br/><br/>def chat_with_qwen(prompt, model_id="Qwen/Qwen2.5-7B-Instruct"):<br/>    """通过 SiliconFlow API 调用 Qwen"""<br/><br/>    response = requests.post(<br/>        "https://api.siliconflow.cn/v1/chat/completions",<br/>        headers={<br/>            "Authorization": f"Bearer {api_key}",<br/>            "Content-Type": "application/json"<br/>        },<br/>        json={<br/>            "model": model_id,<br/>            "messages": [<br/>                {"role": "user", "content": prompt}<br/>            ],<br/>            "temperature": 0.7,<br/>            "max_tokens": 1024<br/>        }<br/>    )<br/><br/>    return response.json()["choices"][0]["message"]["content"]<br/><br/># 使用示例<br/>result = chat_with_qwen("用Python写一个快速排序")<br/>print(result)</code>
```

### 3. 本地部署 Qwen + Ollama RAG

```
<code>from langchain_community.document_loaders import TextLoader<br/>from langchain_text_splitters import CharacterTextSplitter<br/>from langchain_community.embeddings import HuggingFaceEmbeddings<br/>from langchain_community.vectorstores import Chroma<br/>from langchain_community.llms import Ollama<br/>from langchain.chains import RetrievalQA<br/>from langchain_core.prompts import PromptTemplate<br/><br/># 1. 加载文档<br/>documents = TextLoader('dataset/example.txt', encoding='utf-8').load()<br/><br/># 2. 分割文档<br/>docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0).split_documents(documents)<br/><br/># 3. Embeddings（使用中文模型）<br/>embeddings = HuggingFaceEmbeddings(<br/>    model_name="damo/nlp_corom_sentence-embedding_chinese-base"<br/>)<br/><br/># 4. 创建向量数据库<br/>db = Chroma.from_documents(docs, embeddings)<br/><br/># 5. 初始化 Qwen 模型（本地 Ollama 部署）<br/>ollama = Ollama(model="qwen2.5:0.5b")<br/><br/># 6. 创建 QA 链<br/>prompt_template = """基于以下文档内容回答问题：<br/>{context}<br/><br/>问题：{question}<br/>请根据上述内容回答。"""<br/><br/>PROMPT = PromptTemplate(<br/>    template=prompt_template,<br/>    input_variables=["context", "question"]<br/>)<br/><br/>qa_chain = RetrievalQA.from_chain_type(<br/>    llm=ollama,<br/>    chain_type="stuff",<br/>    retriever=db.as_retriever(),<br/>    chain_type_kwargs={"prompt": PROMPT}<br/>)<br/><br/># 7. 查询（新版统一用 .invoke()）<br/>result = qa_chain.invoke({"query": "文档主要内容是什么？"})<br/>print(result["result"])</code>
```

### 4. 多轮对话

```
<code># 使用 Ollama 进行多轮对话<br/>ollama = Ollama(model="qwen2.5:7b")<br/><br/>messages = [<br/>    {"role": "system", "content": "你是一个有帮助的AI助手。"},<br/>    {"role": "user", "content": "什么是机器学习？"},<br/>]<br/><br/># 第一轮对话<br/>response1 = ollama.invoke(messages)<br/>messages.append({"role": "assistant", "content": response1})<br/><br/># 第二轮对话（带上下文）<br/>messages.append({"role": "user", "content": "它和深度学习有什么区别？"})<br/>response2 = ollama.invoke(messages)<br/><br/>print(response2)</code>
```

## 🔧 模型配置参数

### 1. 生成参数

```
<code>config = {<br/>    "temperature": 0.7,        # 创造性（0-2）<br/>    "top_p": 0.9,              # 核采样<br/>    "top_k": 40,              # Top-K 采样<br/>    "repeat_penalty": 1.1,    # 重复惩罚<br/>    "seed": 42,               # 随机种子<br/>    "num_predict": 256,        # 最大生成长度<br/>    "stop": ["\n\n", "用户："]  # 停止序列<br/>}<br/><br/>response = ollama.generate(model="qwen2.5:7b", prompt="你好", options=config)</code>
```

### 2. GPU 配置

```
<code># 查看 GPU 使用情况<br/>nvidia-smi<br/><br/># 设置 GPU 设备<br/>export CUDA_VISIBLE_DEVICES=0,1<br/><br/># 量化模型（减少显存）<br/>ollama pull qwen2.5:7b-q4_0   # 4位量化<br/>ollama pull qwen2.5:7b-q8_0   # 8位量化</code>
```

### 3. Ollama 配置文件

```
<code># ~/.ollama/config.json<br/>{<br/>  "gpu": true,<br/>  "num_gpu": 1,<br/>  "fallback": ["cpu"],<br/>  "keep_alive": "5m",<br/>  "timeout": "120s"<br/>}</code>
```

## 📊 Qwen vs 其他模型对比

| th | th | th | th | th |
| --- | --- | --- | --- | --- |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |

## 🐛 常见问题

### Q: 模型选择哪个版本？

```
<code># 资源有限（CPU推理）<br/>ollama pull qwen2.5:0.5b<br/><br/># 资源一般（GPU 8GB+）<br/>ollama pull qwen2.5:3b<br/><br/># 资源充足（GPU 16GB+）<br/>ollama pull qwen2.5:7b<br/><br/># 高质量输出（GPU 24GB+）<br/>ollama pull qwen2.5:14b</code>
```

### Q: 如何提高生成质量？

```
<code># 1. 使用更长的上下文<br/>ollama = Ollama(model="qwen2.5:7b", num_ctx=8192)<br/><br/># 2. 调整 temperature<br/>ollama = Ollama(model="qwen2.5:7b", temperature=0.3)  # 更确定性<br/><br/># 3. 使用few-shot提示<br/>prompt = """示例：<br/>问题：1+1=?<br/>答案：2<br/><br/>问题：2+2=?<br/>答案：4<br/><br/>问题：3+3=?<br/>答案："""</code>
```

### Q: Ollama 服务无法启动？

```
<code># 检查服务状态<br/>ollama serve<br/><br/># 查看日志<br/>journalctl -u ollama<br/><br/># 重启服务<br/>sudo systemctl restart ollama</code>
```

## 📚 相关资源

- 通义千问官网: [https://tongyi.aliyun.com/](https://tongyi.aliyun.com/)
- Ollama 官网: [https://ollama.com/](https://ollama.com/)
- Qwen GitHub: [https://github.com/QwenLM/Qwen](https://github.com/QwenLM/Qwen)
- 模型下载: [https://ollama.com/library/qwen2.5](https://ollama.com/library/qwen2.5)