## 📋 概述

MinerU 是一款高效的文档智能解析工具，支持从 PDF、图片等文档中提取结构化信息，特别擅长表格识别和内容提取。

**项目代码位置：**`20_learn/modelscope/04_mineru_pdf_md.py`（HuggingFace 版占位脚本已清理，见文末「相关资源」）

> 注意：本文档及配套脚本中的 API 写法为早期推测性整理，未实测。生产使用请以 MinerU 官方 CLI / 服务端方式为准。

## 🏗️ 核心能力

```
<code>┌─────────────────────────────────────────┐<br/>│            MinerU 文档处理流程             │<br/>├─────────────────────────────────────────┤<br/>│  1. 文档输入 (PDF/图片/HTML)            │<br/>│           ↓                              │<br/>│  2. 布局分析 (标题/正文/表格/图片)        │<br/>│           ↓                              │<br/>│  3. 表格识别 (结构化表格提取)             │<br/>│           ↓                              │<br/>│  4. 文本提取 (Markdown/JSON输出)         │<br/>│           ↓                              │<br/>│  5. 向量化存储 (RAG知识库构建)           │<br/>└─────────────────────────────────────────┘</code>
```

## 🚀 快速开始

### 1. 安装

```
<code>pip install modelscope<br/>pip install transformers</code>
```

### 2. 模型下载

```
<code>from modelscope.hub.snapshot_download import snapshot_download<br/><br/># 下载 MinerU 模型<br/>model_dir = snapshot_download('OpenDataLab/MinerU2.0-2505-0.9B')<br/>print(f"模型已下载到: {model_dir}")</code>
```

### 3. 基本使用

```
<code>import torch<br/>from transformers import AutoModel, AutoTokenizer<br/><br/># 加载模型<br/>model_name = "OpenDataLab/MinerU2.0-2505-0.9B"<br/>tokenizer = AutoTokenizer.from_pretrained(model_name)<br/>model = AutoModel.from_pretrained(model_name)<br/><br/># 表格识别示例<br/>def recognize_table(image_path):<br/>    inputs = tokenizer(image_path, return_tensors="pt")<br/>    with torch.no_grad():<br/>        outputs = model(**inputs)<br/>    return outputs</code>
```

## 📚 项目代码示例

### 1. 表格转 Markdown

```
<code>import pandas as pd<br/><br/>def table_to_markdown(table_data):<br/>    """将表格数据转换为 Markdown 格式"""<br/>    if isinstance(table_data, pd.DataFrame):<br/>        return table_data.to_markdown()<br/><br/>    # 列表格式转换为 DataFrame 再转 Markdown<br/>    if not table_data or not all(isinstance(row, list) for row in table_data):<br/>        raise ValueError("表格数据格式不正确")<br/><br/>    df = pd.DataFrame(table_data[1:], columns=table_data[0])<br/>    return df.to_markdown()<br/><br/># 使用示例<br/>text_table = """<br/>| 姓名 | 年龄 | 职业 |<br/>|------|------|------|<br/>| 张三 | 25   | 工程师 |<br/>| 李四 | 30   | 设计师 |<br/>"""<br/><br/>md_content = table_to_markdown(text_table)<br/>print(md_content)</code>
```

### 2. PDF 表格识别（完整示例）

```
<code>from modelscope.models import Model<br/>from modelscope.pipelines import pipeline<br/>from modelscope.preprocessors import LoadImage<br/><br/>def recognize_table_to_markdown(image_path, model_dir, output_md_path):<br/>    """识别表格图像并转换为 Markdown 文件（伪代码骨架）"""<br/>    # 加载本地模型和 table-recognition 推理管道<br/>    model = Model.from_pretrained(model_dir)<br/>    table_pipeline = pipeline(task='table-recognition', model=model)<br/><br/>    # 读取图像 → 表格识别推理<br/>    image = LoadImage.convert_to_img(image_path)<br/>    result = table_pipeline(image)<br/><br/>    # 提取单元格 (text, row, col) → 按坐标回填二维表格<br/>    table_data = parse_model_output(result)<br/><br/>    # 二维表格转 Markdown 表头+分隔行+数据行，写出文件<br/>    markdown_table = convert_to_markdown(table_data)<br/>    with open(output_md_path, 'w', encoding='utf-8') as f:<br/>        f.write(markdown_table)<br/>    return markdown_table<br/><br/>def parse_model_output(model_output):<br/>    """解析模型输出为表格数据（伪代码骨架）"""<br/>    # 遍历 model_output['cells'] 收集 text/row/col<br/>    #   ★特殊点1 用 max(row)/max(col) 推断表格规模，None 初始化后按坐标回填<br/>    ...<br/><br/>def convert_to_markdown(table_data):<br/>    """将表格数据转换为 Markdown 格式（伪代码骨架）"""<br/>    #   ★特殊点2 空表返回占位行；首行为表头，第二行 "---" 分隔，空单元格补 ""<br/>    ...</code>
```

### 3. 处理不同类型输入

```
<code>def process_table_input(input_data, input_type="text"):<br/>    """处理不同类型的表格输入并转换为 Markdown"""<br/><br/>    if input_type == "text":<br/>        # 文本表格处理<br/>        inputs = tokenizer(f"识别表格并转换为Markdown:\n{input_data}", return_tensors="pt")<br/><br/>        with torch.no_grad():<br/>            outputs = model(**inputs)<br/><br/>        table_structure = parse_model_output(outputs)<br/>        return table_to_markdown(table_structure)<br/><br/>    elif input_type == "image":<br/>        # 图片表格处理<br/>        if isinstance(input_data, str):<br/>            # URL 下载<br/>            response = requests.get(input_data)<br/>            image = Image.open(BytesIO(response.content))<br/>        else:<br/>            image = input_data<br/><br/>        table_text = recognize_table_from_image(model, image)<br/>        return process_table_input(table_text, input_type="text")<br/><br/>    else:<br/>        raise ValueError("不支持的输入类型")</code>
```

## 🔧 高级配置

### 1. 模型参数调整

```
<code>from transformers import AutoModel, AutoTokenizer<br/><br/># 加载模型，指定设备<br/>model_name = "OpenDataLab/MinerU2.0-2505-0.9B"<br/>tokenizer = AutoTokenizer.from_pretrained(model_name)<br/><br/># GPU 配置<br/>model = AutoModel.from_pretrained(<br/>    model_name,<br/>    torch_dtype=torch.float16,  # 半精度<br/>    device_map="auto"           # 自动分配设备<br/>)</code>
```

### 2. 批处理配置

```
<code>from torch.utils.data import DataLoader<br/><br/>class TableDataset:<br/>    def __init__(self, image_paths):<br/>        self.image_paths = image_paths<br/><br/>    def __len__(self):<br/>        return len(self.image_paths)<br/><br/>    def __getitem__(self, idx):<br/>        return self.image_paths[idx]<br/><br/>dataset = TableDataset(["img1.jpg", "img2.jpg", "img3.jpg"])<br/>dataloader = DataLoader(dataset, batch_size=8, shuffle=True)<br/><br/>for batch in dataloader:<br/>    results = model(batch)</code>
```

### 3. 输出格式配置

```
<code># 支持多种输出格式<br/>output_formats = {<br/>    "markdown": ".md",<br/>    "json": ".json",<br/>    "html": ".html",<br/>    "excel": ".xlsx"<br/>}<br/><br/>def save_output(content, filename, format_type):<br/>    if format_type == "markdown":<br/>        with open(filename + ".md", "w", encoding="utf-8") as f:<br/>            f.write(content)<br/>    elif format_type == "json":<br/>        import json<br/>        with open(filename + ".json", "w", encoding="utf-8") as f:<br/>            json.dump(content, f, ensure_ascii=False, indent=2)</code>
```

## 📊 与其他工具对比

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

## 🐛 常见问题

### Q: 模型下载失败？

```
<code># 设置镜像源<br/>import modelscope<br/>modelscope.hub.set_dir("~/.cache/modelscope")<br/><br/># 手动下载<br/># 访问 https://modelscope.cn/models/OpenDataLab/MinerU2.0-2505-0.9B</code>
```

### Q: GPU 显存不足？

```
<code># 使用量化<br/>model = AutoModel.from_pretrained(<br/>    model_name,<br/>    load_in_8bit=True  # 8位量化<br/>)<br/><br/># 或者减小批次大小<br/>batch_size = 2  # 从 8 改为 2</code>
```

### Q: 输出格式不对？

```
<code># 检查输入格式<br/>print(f"输入类型: {type(input_data)}")<br/>print(f"输入内容: {input_data[:100]}")<br/><br/># 确保使用正确的解析函数<br/>result = parse_model_output(model_output)</code>
```

## 📚 相关资源

- 官方文档: [https://modelscope.cn/models/OpenDataLab/MinerU2.0-2505-0.9B](https://modelscope.cn/models/OpenDataLab/MinerU2.0-2505-0.9B)
- 项目代码: `01_huggingface/`, `01_modelscope/`
- 示例数据集: `01_huggingface/dataset/`