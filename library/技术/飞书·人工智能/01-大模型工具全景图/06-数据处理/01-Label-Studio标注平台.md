# Label Studio标注平台

> 模块：数据处理  
> 更新时间：2026-03-29

---

---

Label Studio是一个开源的数据标注平台，支持多种数据类型（文本、图像、音频、视频等）。

**官网**：https://labelstudio.io  
**GitHub**：https://github.com/HumanSignal/label-studio

**核心特点**：

- 多数据类型支持
- 灵活的标注配置
- 团队协作
- 机器学习集成
- 多种导出格式

---

---

### 1. 安装

```
<code># pip安装<br/>pip install label-studio<br/><br/># 启动<br/>label-studio<br/><br/># 访问 http://localhost:8080<br/># 首次访问需要创建账号</code>
```

### 2. Docker部署

```
<code>docker run -d \<br/>  -p 8080:8080 \<br/>  -v $(pwd)/label_studio_data:/label-studio/data \<br/>  heartexlabs/label-studio:latest</code>
```

---

---

### 1. 情感分类

```
<code>&lt;!-- labeling_config.xml --&gt;<br/>&lt;View&gt;<br/>  &lt;Text name="text" value="$text"/&gt;<br/><br/>  &lt;Choices name="sentiment" toName="text"&gt;<br/>    &lt;Choice value="正面"/&gt;<br/>    &lt;Choice value="中性"/&gt;<br/>    &lt;Choice value="负面"/&gt;<br/>  &lt;/Choices&gt;<br/><br/>  &lt;Text name="meta" value="$meta"/&gt;<br/>&lt;/View&gt;</code>
```

### 2. 命名实体识别

```
<code>&lt;Text name="text" value="$text"/&gt;<br/><br/>&lt;Labels name="entities" toName="text"&gt;<br/>  &lt;Label value="人名"/&gt;<br/>  &lt;Label value="地名"/&gt;<br/>  &lt;Label value="机构"/&gt;<br/>  &lt;Label value="时间"/&gt;<br/>&lt;/Labels&gt;</code>
```

### 3. 文本相似度

```
<code>&lt;View&gt;<br/>  &lt;Text name="text1" value="$text1"/&gt;<br/>  &lt;Text name="text2" value="$text2"/&gt;<br/><br/>  &lt;Number name="similarity" toName="text1,text2"<br/>          min="0" max="1" step="0.1"/&gt;<br/>&lt;/View&gt;</code>
```

### 4. 问答标注

```
<code>&lt;View&gt;<br/>  &lt;Header&gt;请根据上下文回答问题&lt;/Header&gt;<br/>  &lt;Text name="context" value="$context"/&gt;<br/>  &lt;Text name="question" value="$question"/&gt;<br/>  &lt;TextArea name="answer" toName="context" <br/>            showSublabels="true"/&gt;<br/>&lt;/View&gt;</code>
```

---

---

```
<code>import os<br/><br/>from label_studio_sdk import Client<br/><br/># 连接（API Key 从环境变量读取，勿硬编码）<br/>ls = Client(<br/>    url="http://localhost:8080",<br/>    api_key=os.environ["LABEL_STUDIO_API_KEY"]<br/>)<br/><br/># 获取项目<br/>project = ls.get_project(1)<br/><br/># 导入数据<br/>project.import_data([<br/>    {"text": "这是一个好产品", "id": 1},<br/>    {"text": "质量一般", "id": 2},<br/>    {"text": "非常好用", "id": 3},<br/>])<br/><br/># 导出数据（不同 SDK 版本接口有差异：1.x 为 export_tasks，2.x 起为 project.exports.*，以所用版本文档为准）<br/>exported = project.export_tasks(export_type="JSON")<br/>print(exported)<br/><br/># 获取标注结果<br/>tasks = project.get_tasks()<br/>for task in tasks:<br/>    print(task["data"], task["annotations"])</code>
```

---

---

```
<code>import os<br/><br/>import requests<br/><br/># 导入JSON格式数据<br/>data = {<br/>    "data": [<br/>        {"text": "样本文本1", "source": "微博"},<br/>        {"text": "样本文本2", "source": "知乎"},<br/>        {"text": "样本文本3", "source": "小红书"}<br/>    ]<br/>}<br/><br/>response = requests.post(<br/>    "http://localhost:8080/api/projects/1/import",<br/>    json=data,<br/>    headers={"Authorization": f"Token {os.environ['LABEL_STUDIO_API_KEY']}"}<br/>)<br/><br/>print(response.json())</code>
```

---

---

```
<code># 常用导出格式：JSON / JSON_MIN / CSV（不存在 "CODEC" 这种格式）<br/>project.export(export_type="JSON")<br/><br/># 导出为CSV<br/>project.export(export_type="CSV")<br/><br/># 导出为JSON_MIN（仅导出标注结果的最小 JSON）<br/>project.export(export_type="JSON_MIN")</code>
```

---

---

自定义 ML 后端通过 `label-studio-ml` 启动独立服务（默认 9090 端口），再在 Label Studio 项目设置（Model 页面）中连接，不依赖本地 `.labelstudiorc` 之类的配置文件。

```
<code># 自定义ML后端<br/>from label_studio_ml.model import LabelStudioMLBase<br/><br/>class MyModel(LabelStudioMLBase):<br/>    def __init__(self, *args, **kwargs):<br/>        super().__init__(*args, **kwargs)<br/>        # 最小示意模型：固定词表的情感分类器，实际项目替换为训练好的模型<br/>        self.positive_words = {"好", "好用", "喜欢", "满意"}<br/>        self.negative_words = {"差", "不满", "失望"}<br/><br/>    def _predict_sentiment(self, text: str) -&gt; str:<br/>        if any(w in text for w in self.negative_words):<br/>            return "负面"<br/>        if any(w in text for w in self.positive_words):<br/>            return "正面"<br/>        return "中性"<br/><br/>    def predict(self, tasks, **kwargs):<br/>        predictions = []<br/>        for task in tasks:<br/>            text = task["data"]["text"]<br/>            sentiment = self._predict_sentiment(text)<br/>            predictions.append({<br/>                "result": [{<br/>                    "from_name": "sentiment",<br/>                    "to_name": "text",<br/>                    "type": "choices",<br/>                    "choices": [sentiment]<br/>                }]<br/>            })<br/>        return predictions</code>
```

---

---

**Label Studio是企业级数据标注的首选工具**，支持复杂标注任务和团队协作。

**适用场景**：

- 训练数据标注
- 模型评估数据标注
- 团队协作标注
- 半自动化标注

### 企业级升级要点

- **标注规范先行**：上线前固化标注指南与边界用例，标注一致性（IAA）不达标不进训练集
- **质检闭环**：抽样复审 + 标注员间一致性统计，分歧样本回流澄清而不是直接丢弃
- **密钥与访问控制**：API Key 从环境变量读取，按项目/角色分配最小权限
- **版本对齐**：SDK 接口随版本变化较快（如 1.x 与 2.x 导出 API 不同），锁定版本并跟进官方迁移说明
- **预标注提效**：接入 ML 后端做预标注，人工只做修正，显著降低单条标注成本

> 更多工程化实践（评测基准、灰度发布、成本控制）参见 70-企业级工程基准。

---

---