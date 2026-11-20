# Label Studio标注平台

> 模块：数据处理
> 更新时间：2026-03-29

---

## 一、框架介绍

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

## 二、快速开始

### 1. 安装

```bash
# pip安装
pip install label-studio

# 启动
label-studio

# 访问 http://localhost:8080
# 首次访问需要创建账号
```

### 2. Docker部署

```bash
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/label_studio_data:/label-studio/data \
  heartexlabs/label-studio:latest
```

---

## 三、文本标注配置

### 1. 情感分类

```xml
<!-- labeling_config.xml -->
<View>
  <Text name="text" value="$text"/>
  
  <Choices name="sentiment" toName="text">
    <Choice value="正面"/>
    <Choice value="中性"/>
    <Choice value="负面"/>
  </Choices>
  
  <Text name="meta" value="$meta"/>
</View>
```

### 2. 命名实体识别

```xml
<Text name="text" value="$text"/>

<Labels name="entities" toName="text">
  <Label value="人名"/>
  <Label value="地名"/>
  <Label value="机构"/>
  <Label value="时间"/>
</Labels>
```

### 3. 文本相似度

```xml
<View>
  <Text name="text1" value="$text1"/>
  <Text name="text2" value="$text2"/>
  
  <Number name="similarity" toName="text1,text2"
          min="0" max="1" step="0.1"/>
</View>
```

### 4. 问答标注

```xml
<View>
  <Header>请根据上下文回答问题</Header>
  <Text name="context" value="$context"/>
  <Text name="question" value="$question"/>
  <TextArea name="answer" toName="context" 
            showSublabels="true"/>
</View>
```

---

## 四、Python SDK使用

```python
import os

from label_studio_sdk import Client

# 连接（API Key 从环境变量读取，勿硬编码）
ls = Client(
    url="http://localhost:8080",
    api_key=os.environ["LABEL_STUDIO_API_KEY"]
)

# 获取项目
project = ls.get_project(1)

# 导入数据
project.import_data([
    {"text": "这是一个好产品", "id": 1},
    {"text": "质量一般", "id": 2},
    {"text": "非常好用", "id": 3},
])

# 导出数据（不同 SDK 版本接口有差异：1.x 为 export_tasks，2.x 起为 project.exports.*，以所用版本文档为准）
exported = project.export_tasks(export_type="JSON")
print(exported)

# 获取标注结果
tasks = project.get_tasks()
for task in tasks:
    print(task["data"], task["annotations"])
```

---

## 五、API导入数据

```python
import os

import requests

# 导入JSON格式数据
data = {
    "data": [
        {"text": "样本文本1", "source": "微博"},
        {"text": "样本文本2", "source": "知乎"},
        {"text": "样本文本3", "source": "小红书"}
    ]
}

response = requests.post(
    "http://localhost:8080/api/projects/1/import",
    json=data,
    headers={"Authorization": f"Token {os.environ['LABEL_STUDIO_API_KEY']}"}
)

print(response.json())
```

---

## 六、导出格式

```python
# 常用导出格式：JSON / JSON_MIN / CSV（不存在 "CODEC" 这种格式）
project.export(export_type="JSON")

# 导出为CSV
project.export(export_type="CSV")

# 导出为JSON_MIN（仅导出标注结果的最小 JSON）
project.export(export_type="JSON_MIN")
```

---

## 七、机器学习集成

自定义 ML 后端通过 `label-studio-ml` 启动独立服务（默认 9090 端口），再在 Label Studio 项目设置（Model 页面）中连接，不依赖本地 `.labelstudiorc` 之类的配置文件。

```python
# 自定义ML后端
from label_studio_ml.model import LabelStudioMLBase

class MyModel(LabelStudioMLBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 最小示意模型：固定词表的情感分类器，实际项目替换为训练好的模型
        self.positive_words = {"好", "好用", "喜欢", "满意"}
        self.negative_words = {"差", "不满", "失望"}

    def _predict_sentiment(self, text: str) -> str:
        if any(w in text for w in self.negative_words):
            return "负面"
        if any(w in text for w in self.positive_words):
            return "正面"
        return "中性"

    def predict(self, tasks, **kwargs):
        predictions = []
        for task in tasks:
            text = task["data"]["text"]
            sentiment = self._predict_sentiment(text)
            predictions.append({
                "result": [{
                    "from_name": "sentiment",
                    "to_name": "text",
                    "type": "choices",
                    "choices": [sentiment]
                }]
            })
        return predictions
```

---

## 八、总结

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

> 更多工程化实践（评测基准、灰度发布、成本控制）参见 [70-企业级工程基准](../../06-Agent开发/70-企业级工程基准.md)。

---

*下一步：LangChain核心概念*
