## 📋 概述

Dify 是一款开源的大语言模型(LLM)应用开发平台，支持快速构建 AI 应用，提供可视化的工作流编排能力。

**定位对比：**

- Dify = "记忆管理的成品解决方案"（低代码，开箱即用）
- LangChain = "记忆管理的乐高积木"（高灵活度，需更多开发成本）

## 🏗️ 核心概念

```
<code>┌─────────────────────────────────────────────────────┐<br/>│                    Dify 架构                         │<br/>├─────────────────────────────────────────────────────┤<br/>│  应用层: 对话应用 │ Agent │ 工作流 │ Chatflow       │<br/>├─────────────────────────────────────────────────────┤<br/>│  能力层: RAG引擎 │ 提示词 │ 工具插件 │ 变量上下文   │<br/>├─────────────────────────────────────────────────────┤<br/>│  模型层: OpenAI │ Anthropic │ 本地模型 │ API网关    │<br/>├─────────────────────────────────────────────────────┤<br/>│  数据层: 文件上传 │ 知识库 │ 向量数据库              │<br/>└─────────────────────────────────────────────────────┘</code>
```

## 🚀 快速开始

### 1. 安装部署

```
<code># 使用 Docker 部署<br/>git clone https://github.com/langgenius/dify.git<br/>cd dify/docker<br/>cp .env.example .env<br/>docker-compose up -d<br/><br/># 访问 http://localhost:80</code>
```

### 2. API 调用

```
<code># 获取 API Key<br/># 设置 -&gt; API<br/><br/># 调用对话 API<br/>curl -X POST 'http://localhost:80/v1/chat-messages' \<br/>  -H 'Authorization: Bearer {api_key}' \<br/>  -H 'Content-Type: application/json' \<br/>  -d '{<br/>    "query": "什么是人工智能？",<br/>    "response_mode": "blocking",<br/>    "conversation_id": "",<br/>    "user": "user_123"<br/>  }'</code>
```

## 📚 项目代码示例

项目中包含 `02_dify` 目录下的完整示例代码。

### 1. Dify API 上传文档

```
<code>import requests<br/><br/>class DifyUploader:<br/>    def __init__(self, api_base_url, api_key):<br/>        self.api_base_url = api_base_url.rstrip('/')<br/>        self.api_key = api_key<br/><br/>    def create_document_by_text(self, dataset_id, name, text):<br/>        """通过文本创建文档"""<br/>        url = f"{self.api_base_url}/v1/datasets/{dataset_id}/document/create-by-text"<br/><br/>        headers = {<br/>            'Authorization': f'Bearer {self.api_key}',<br/>            'Content-Type': 'application/json'<br/>        }<br/><br/>        data = {<br/>            "name": name,<br/>            "text": text,<br/>            "indexing_technique": "high_quality",<br/>            "process_rule": {<br/>                "mode": "automatic"<br/>            }<br/>        }<br/><br/>        response = requests.post(url, headers=headers, json=data)<br/>        return response.json()<br/><br/>    def get_document_status(self, dataset_id, document_id):<br/>        """查询文档处理状态"""<br/>        url = f"{self.api_base_url}/v1/datasets/{dataset_id}/documents/{document_id}"<br/>        headers = {'Authorization': f'Bearer {self.api_key}'}<br/>        response = requests.get(url, headers=headers)<br/>        return response.json()</code>
```

### 2. RagFlow 文档上传器（类似实现）

```
<code>import requests<br/>import tempfile<br/>import uuid<br/><br/>class RagflowDocumentUploader:<br/>    def __init__(self, api_base_url, api_key):<br/>        self.api_base_url = api_base_url<br/>        self.api_key = api_key<br/><br/>    def upload_document(self, dataset_id, file_path, chunk_delimiter="@@"):<br/>        """上传文档到 RagFlow"""<br/><br/>        # 1. 创建空文档<br/>        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:<br/>            temp_file_name = f.name<br/><br/>        with open(temp_file_name, 'rb') as f:<br/>            files = {'file': (file_path, f, 'text/plain')}<br/>            headers = {'Authorization': f'Bearer {self.api_key}'}<br/><br/>            url = f"{self.api_base_url}/api/v1/datasets/{dataset_id}/documents"<br/>            response = requests.post(url, headers=headers, files=files)<br/><br/>        document_id = response.json()["data"][0]["id"]<br/><br/>        # 2. 上传文档内容<br/>        with open(file_path, 'r', encoding='utf-8') as f:<br/>            content = f.read()<br/><br/>        chunks = content.split(chunk_delimiter)<br/>        for i, chunk in enumerate(chunks):<br/>            self.upload_chunk(dataset_id, document_id, chunk, i)<br/><br/>        return document_id</code>
```

## 🔧 核心功能配置

### 1. 知识库配置

```
<code># 文档处理规则<br/>process_rule:<br/>  mode: "hierarchical"  # 层级模式<br/>  rules:<br/>    pre_processing_rules:<br/>      - id: "remove_extra_spaces"<br/>        enabled: true<br/>      - id: "remove_urls_emails"<br/>        enabled: false<br/>    segmentation:<br/>      separator: "**********page_ending**********"<br/>      max_tokens: 1024<br/>      chunk_overlap: 0<br/>    parent_mode: "paragraph"</code>
```

### 2. 应用类型

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |

### 3. 提示词模板

```
<code># 系统提示词<br/>你是一个专业的{{role}}，擅长回答{{domain}}相关问题。<br/>请用简洁清晰的语言回答用户的问题。<br/><br/># 用户问题<br/>{{query}}<br/><br/># 上下文<br/>{{context}}</code>
```

## 📊 Dify vs LangChain 对比

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |

### 选择建议

- ✅ **选 Dify**：快速搭建标准化应用、客服机器人、简单问答
- ✅ **选 LangChain**：深度定制、复杂记忆策略、医疗/法律等专业场景

## 🔗 连接 Ragflow 知识库

Ragflow 是一个开源的知识库管理系统，与 Dify 可以完美集成，提供更强大的文档管理能力。

### 1. Ragflow 部署

```
<code># 克隆仓库<br/>git clone https://github.com/infiniflow/ragflow.git<br/>cd ragflow<br/><br/># 配置环境<br/>cp .env.example .env<br/># 编辑 .env 文件，设置数据库等配置<br/><br/># 启动服务<br/>docker-compose up -d<br/><br/># 访问 http://localhost:30002</code>
```

### 2. 配置 Ragflow API

```
<code>class RagflowClient:<br/>    def __init__(self, api_base_url, api_key):<br/>        self.api_base_url = api_base_url.rstrip('/')<br/>        self.api_key = api_key<br/><br/>    def list_datasets(self):<br/>        """列出所有知识库"""<br/>        url = f"{self.api_base_url}/api/v1/datasets"<br/>        headers = {<br/>            'Authorization': f'Bearer {self.api_key}',<br/>            'Content-Type': 'application/json'<br/>        }<br/>        response = requests.get(url, headers=headers)<br/>        return response.json()<br/><br/>    def create_document(self, dataset_id, file_path):<br/>        """上传文档到知识库"""<br/>        url = f"{self.api_base_url}/api/v1/datasets/{dataset_id}/documents"<br/>        headers = {<br/>            'Authorization': f'Bearer {self.api_key}'<br/>        }<br/>        with open(file_path, 'rb') as f:<br/>            files = {'file': (os.path.basename(file_path), f)}<br/>            response = requests.post(url, headers=headers, files=files)<br/>        return response.json()</code>
```

### 3. 与 Dify 集成

```
<code>class DifyRagflowIntegration:<br/>    def __init__(self, dify_api_key, ragflow_api_key, ragflow_url="http://localhost:30002"):<br/>        self.dify_api_key = dify_api_key<br/>        self.ragflow_client = RagflowClient(ragflow_url, ragflow_api_key)<br/><br/>    def sync_ragflow_to_dify(self, ragflow_dataset_id, dify_app_id):<br/>        """同步 Ragflow 知识库到 Dify"""<br/>        # 1. 获取 Ragflow 文档<br/>        documents = self.ragflow_client.get_documents(ragflow_dataset_id)<br/><br/>        # 2. 同步到 Dify<br/>        for doc in documents:<br/>            self._sync_document_to_dify(doc, dify_app_id)<br/><br/>    def _sync_document_to_dify(self, document, dify_app_id):<br/>        """同步单个文档"""<br/>        # 实现文档同步逻辑<br/>        pass</code>
```

### 4. 完整的 Ragflow 上传工具

项目中包含完整的 Ragflow 上传工具：`02_dify/ragflow/ragflow_uploader.py`

**主要功能：**

- 可视化界面上传文档
- 支持文档分段上传
- 实时进度显示
- 错误处理和日志记录

**使用步骤：**

1. 启动 Ragflow 服务
1. 运行上传工具：`python ragflow_uploader.py`
1. 配置 API 地址、密钥和知识库 ID
1. 选择本地文件并上传

### 5. API 参考

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |

## ❓ 常见问题

### Q: 文档上传失败？

```
<code># 检查文件格式<br/># 支持: .txt, .markdown, .pdf, .docx, .html<br/><br/># 检查 API 配置<br/>print(f"API地址: {api_base_url}")<br/>print(f"知识库ID: {dataset_id}")</code>
```

### Q: 如何批量上传？

```
<code>import os<br/><br/>uploader = DifyUploader(api_base_url, api_key)<br/>dataset_id = "your_dataset_id"<br/><br/>for filename in os.listdir("./documents"):<br/>    with open(filename, 'r') as f:<br/>        content = f.read()<br/>    uploader.create_document_by_text(dataset_id, filename, content)</code>
```

### Q: 分块策略如何选择？

| th | th |
| --- | --- |
| td | td |
| td | td |
| td | td |

### Q: Ragflow 连接失败？

```
<code># 检查 Ragflow 服务状态<br/>import requests<br/><br/>try:<br/>    response = requests.get("http://localhost:30002/api/v1/health")<br/>    print(f"Ragflow 状态: {response.status_code}")<br/>except Exception as e:<br/>    print(f"Ragflow 连接失败: {e}")<br/><br/># 检查 API 密钥<br/>print(f"API 密钥: {api_key[:10]}...")</code>
```

## 📚 相关资源

- **Dify 资源**:官方文档: [https://docs.dify.ai/](https://docs.dify.ai/)
- GitHub: [https://github.com/langgenius/dify](https://github.com/langgenius/dify)
- 示例代码: `02_dify/` 目录
- **Ragflow 资源**:官方文档: [https://docs.ragflow.io/](https://docs.ragflow.io/)
- GitHub: [https://github.com/infiniflow/ragflow](https://github.com/infiniflow/ragflow)
- 上传工具: `02_dify/ragflow/ragflow_uploader.py`