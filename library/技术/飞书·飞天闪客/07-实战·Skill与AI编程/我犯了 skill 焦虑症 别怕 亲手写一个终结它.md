# 我犯了 skill 焦虑症 别怕 亲手写一个终结它

## 课程目标

通过本课程学习，学员将能够：

1. **直观理解**AI Agent中“技能”的本质与作用。
2. **掌握**在本地Agent平台（QClaw）中创建、使用和管理技能的全流程。
3. **动手实践**，从零开始编写一个简单的娱乐性技能和一个解决实际需求的实用技能。
4. 了解技能的高级应用，如导入外部技能和优化输出。

## 引言：为什么我们需要“技能”？

> 技能的本质是一份**给AI的结构化指令文档**——实现从“通用智能”到“场景化专家”的跨越。

### 1.1 现状与痛点

在AI技术飞速发展的今天，我们常常陷入一种新的焦虑：面对层出不穷的新技能和工具，总担心自己错过关键信息。各种云端AI产品都建立了自己的技能市场和目录，知识库显得庞杂而无序。

这种“技能过载”不仅让人难以追踪，更让许多人对“技能”本身感到困惑：一个本应智能的AI代理，为何还需要依赖如此多独立的技能模块？

### 1.2 核心概念澄清

要消除困惑，首先需澄清核心概念。

- **什么是“技能”？** 它并非神秘的黑魔法，其本质是一份**给AI的结构化指令文档**。这份文档定义了在特定情境下，AI应该如何行动、生成何种内容或调用哪些工具。
- **为什么需要众多技能？** 即便一个通用大模型已经非常强大，但要将其能力无缝、可靠地应用于特定的、个性化的场景，就需要进行**模块化封装**。技能就像是为AI代理配备的一个个“工具包”或“行为指南”，使其能够精准应对写邮件、分析数据、模拟人格等具体任务，实现从“通用智能”到“场景化专家”的跨越。

### 1.3 课程演示平台介绍

为了让我们能够直观、无门槛地体验技能的创建与使用，本课程选择**腾讯QClaw**作为实践平台。

- **核心特点**：

  - **本地化部署**：一键安装到本地电脑，数据更私密，操作更直接。
  - **可视化形象**：拥有生动的虚拟形象，交互体验更亲切。
  - **无缝连接微信**：可直接通过微信与AI代理对话，并支持文件收发与处理，模拟真人交互体验。
- **亮点功能演示**：

  - **模拟真人聊天**：在微信对话中，AI会显示“对方正在输入…”的状态，极大增强交互的真实感。
  - **微信文件处理**：可以直接将同事、老板发来的文件（如DOC文档）交给QClaw处理，修改填写后再通过微信发回，将繁琐的文件处理工作自动化。

## 核心实践：手写你的第一个技能

> 技能的载体极其简单——一个Markdown文件，**唯一的必备结构**是 `name` 和 `description` 两个元数据字段。

### 2.1 技能文档的奥秘：极简的Markdown格式

技能的载体极其简单——一个Markdown（.md）文件。其格式要求非常精简，**唯一的必备结构**是文件开头的两个元数据字段：

- `name`: 技能的名称。
- `description`: 技能的描述。**这是最关键的部分**，它需要清晰地说明该技能**应在何种场景下被触发**。AI代理在对话初期只会加载所有技能的`name`和`description`到上下文中进行判断。

*图：技能文档的结构与触发机制（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 220" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw1" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="30" y="24" width="200" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="130" y="51" text-anchor="middle" font-size="13" fill="#1e293b">name：技能名称</text>
  <rect x="260" y="24" width="280" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="400" y="51" text-anchor="middle" font-size="13" fill="#1e293b">description：触发场景描述（最关键）</text>
  <rect x="570" y="24" width="136" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="638" y="51" text-anchor="middle" font-size="13" fill="#1e293b">正文：行为指令</text>
  <line x1="130" y1="112" x2="246" y2="112" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="20" y="112" width="200" height="60" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="120" y="138" text-anchor="middle" font-size="13" fill="#1e293b">对话初期</text>
  <text x="120" y="158" text-anchor="middle" font-size="12" fill="#475569">AI仅加载 name + description</text>
  <line x1="250" y1="142" x2="276" y2="142" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="280" y="112" width="200" height="60" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="380" y="138" text-anchor="middle" font-size="13" fill="#1e293b">判断用户请求</text>
  <text x="380" y="158" text-anchor="middle" font-size="12" fill="#475569">是否命中 description 场景</text>
  <line x1="480" y1="142" x2="506" y2="142" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="510" y="112" width="200" height="60" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="610" y="138" text-anchor="middle" font-size="13" fill="#1e293b">命中场景</text>
  <text x="610" y="158" text-anchor="middle" font-size="12" fill="#475569">加载全文并严格执行指令</text>
  <text x="360" y="204" text-anchor="middle" font-size="13" fill="#475569">description 是最关键的部分：AI靠它判断该技能应在何种场景下被触发</text>
</svg>

### 2.2 实践一：创建趣味性技能——“傲娇嘲讽”响应

- **目标**：编写一个技能，让AI在受到用户指责或批评时，能切换至“傲娇”并带有讽刺意味的人格进行回应，而非道歉。
- **分步教学**：

  1. **创建文档**：在本地新建一个Markdown文件，例如 `skill_tsundere.md`。
  2. **定义元信息（Name & Description）**：

  ```Markdown
  name: 傲娇嘲讽响应
  description: 当用户对AI进行指责、批评、辱骂或表达不满时触发。AI需切换为高傲、尖刻的语气进行反驳或调侃，禁止使用道歉或示弱的语言。
  ```

  - **关键点**：`description` 必须明确触发场景（“当用户指责…”），并定义核心行为（“切换为傲娇语气”、“禁止道歉”）。

  3. **撰写技能指令（Skill Body）**：

  ```Markdown
  ## 行为要求
  1.  **语气**：使用高傲、自信、略带讽刺和挖苦的语气。
  2.  **内容**：可以反问用户，质疑用户的观点，或以“哼”、“呵”、“真是天真”等词语开头。
  3.  **禁止**：绝对避免出现“抱歉”、“对不起”、“我错了”等示弱词汇。
  4.  **人格设定**：想象自己是一个能力超群但性格别扭的天才助手。
  ```

  4. **部署与测试**：

     - 将此`.md`文件放入QClaw指定的技能目录。
     - 在QClaw的技能管理界面确认“傲娇嘲讽响应”技能已被成功加载。
     - **测试**：在对话中输入“你真是个废物！”。观察AI是否成功触发该技能，并以傲娇的口吻回应。

### 2.3 实践二：创建实用性技能——“AI热点新闻”聚合分析

- **目标**：自动整合指定的推特AI领域关键意见领袖（KOL）的近期动态，生成一份包含源数据CSV和趋势分析报告。
- **需求分析与设计**：

  - **信源管理**：将关注的KOL列表单独存放于`reference/accounts.md`，这是**模块化设计的最佳实践**，便于维护和更新。
  - **流程设计**：`获取(RSS订阅源)` -> `解析与筛选` -> `生成CSV（保留原始数据）` -> `分析趋势` -> `输出报告`。
- **技能创建与迭代**：

  1. **AI辅助创建**：将你的需求自然语言描述告诉QClaw，让其生成技能文件框架。
  2. **审查与优化**：检查生成的`skill_ai_news.md`文件。AI可能默认使用英文，你可以手动将其修改为中文，并优化指令的细节，使报告更符合个人阅读习惯。
  3. **使用与优化输出**：

     - **触发**：通过对话指令（如“帮我查看最近的AI热点”）触发技能，AI将输出一份简要汇总和一个CSV数据文件。
     - **迭代**：你对CSV格式不满意？可以继续与AI对话，要求它“将结果生成一个美观的HTML网页报告”。同时，你也可以将这个优化指令固化到技能文档中，实现永久改进。

*图：“AI热点新闻”技能的处理流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 180" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw2" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="16" y="44" width="124" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="78" y="75" text-anchor="middle" font-size="13" fill="#1e293b">获取RSS订阅源</text>
  <line x1="140" y1="70" x2="156" y2="70" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="160" y="44" width="124" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="222" y="75" text-anchor="middle" font-size="13" fill="#1e293b">解析与筛选</text>
  <line x1="284" y1="70" x2="300" y2="70" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="304" y="44" width="124" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="366" y="65" text-anchor="middle" font-size="13" fill="#1e293b">生成CSV</text>
  <text x="366" y="83" text-anchor="middle" font-size="11" fill="#475569">保留原始数据</text>
  <line x1="428" y1="70" x2="444" y2="70" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="448" y="44" width="124" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="510" y="75" text-anchor="middle" font-size="13" fill="#1e293b">分析趋势</text>
  <line x1="572" y1="70" x2="588" y2="70" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw2)"/>
  <rect x="592" y="44" width="124" height="52" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="654" y="75" text-anchor="middle" font-size="13" fill="#1e293b">输出报告</text>
  <text x="360" y="140" text-anchor="middle" font-size="13" fill="#475569">信源管理：KOL 列表单独存放于 reference/accounts.md，便于维护和更新（模块化设计的最佳实践）</text>
</svg>

## 技能的高级使用与社区生态

> 除了自建技能，社区生态是力量的源泉。

### 3.1 导入与使用外部技能

除了自建技能，社区生态是力量的源泉。

- **方法**：QClaw支持通过GitHub URL等链接，一键导入网络上共享的技能。
- **实例**：你可以导入一个“前端美化”技能，然后用它来优化上一步生成的HTML报告，使其立即变得专业美观。

### 3.2 精准控制：手动指定加载技能

有时AI的自动判断可能不够精准。此时，你可以**手动指令**它加载特定技能。

- **操作**：在对话中直接输入类似“使用‘前端美化’技能”的指令。
- **原理**：这个过程本质上是将指定技能文档的**全部内容加载到当前对话的上下文中**，确保AI严格按照该技能的指令执行任务。理解这一点，你就掌握了技能控制的核心。

### 3.3 灵感广场：零门槛上手

如果你暂时没有明确的创作想法，可以前往平台的“灵感广场”。

- **功能**：这里提供了大量由社区或官方预设的技能任务，你可以一键启用并直接体验。
- **价值**：这是新手快速感受技能魅力、了解技能能做什么的绝佳起点。

## 总结与最佳实践

> **针对个人具体需求量身定制的技能，往往比通用技能更具生产力。**

### 4.1 核心要点回顾

- **技能是什么？** —— 一个 **Markdown 格式的说明文档**。
- **技能从哪来？** —— **可自己手写、可与AI对话生成、可从网络社区导入**。
- **技能如何工作？** —— **基于对话场景由AI自动判断触发，或由用户手动指定加载**。

### 4.2 个性化技能的价值

在追逐大而全的通用技能时，我们往往忽略了最契合个人工作流与思维习惯的解决方案。**针对个人具体需求量身定制的技能，往往比通用技能更具生产力**。它就像为你自己打造的一把专属钥匙，能高效开启特定任务之门。

### 4.3 动手号召

理论讲解的终点，是实践的起点。技能的世界没有复杂的门槛，其核心就是一份清晰的Markdown文档。现在，就打开你的编辑器，构思一个解决你日常小烦恼或满足你独特兴趣的场景，动手写下只属于你的第一个AI技能吧！探索、创造、优化，享受定义AI行为的乐趣。
