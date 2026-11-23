# Dify 意图识别实现

Dify 解决多轮对话意图识别，靠的是**分层意图识别+会话记忆+对话状态机+RAG增强+记忆锚点**这一套工程化组合拳，把“上下文连贯、意图不跑偏、槽位不丢失”做进了平台内核。

## 一、分层意图识别（从轻到重，兜底不漏）

Dify 把意图识别做成三级流水线，**先快后准、规则控风险、LLM保语义**：

1. **第一层：规则优先（关键词/正则）**
   - 高频固定意图（查订单、退款、报修）用关键词/正则直接命中，**快、稳、零幻觉**。
2. **第二层：LLM语义分类（Few-shot Prompt）**
   - 规则没命中时，用内置意图分类模板+少量示例，让LLM输出标准意图标签（如`query_logistics`/`apply_refund`）。
   - 支持**意图优先级**：紧急（投诉/退款）> 普通咨询 > 闲聊，避免被弱意图带偏。
3. **第三层：RAG增强召回（案例匹配）**
   - 复杂/模糊query，检索历史相似对话案例，把“历史提问+当前问题+意图标签”一起喂给LLM，**减少歧义、降低幻觉**。

## 二、会话记忆管理（上下文不丢、指代能解）

Dify 内置**三级记忆+智能压缩+记忆锚点**，保证多轮连贯：

1. **三级存储**：短期内存（当前会话）→ Redis（近期会话）→ MongoDB（长期会话）。
2. **智能窗口压缩**
   - 按token限制自动裁剪历史，优先保留**关键实体（订单号）、API调用、意图变更轮次**，无关闲聊压缩/丢弃。
   - 算法效果：电商场景压缩70%历史，仍保持96%任务完成率。
3. **记忆锚点（核心黑科技）**
   - 一旦识别到**关键槽位**（订单号、手机号、产品型号），自动把这些值**钉在每轮上下文最前面**，即使原始对话被压缩，也永远可见。
   - 解决：“它、这个、刚才的订单”等指代消解，**跨轮不丢关键信息**。

## 三、对话状态追踪（DST）：意图+槽位+阶段全跟踪

Dify 的 ChatFlow 内置**会话状态机**，每轮都维护3个核心状态，**骨架不塌、意图不飘**：

- **当前主意图**：锁定核心目标（退货/报修/咨询），中途改意图时**自动覆盖**。
- **槽位参数表**：结构化存储已抽取信息（订单号、时间、金额），缺则追问、错则修正。
- **对话阶段**：开场白→信息收集→确认→执行→收尾，**按阶段控制对话节奏**。

示例：

- 用户：我要退货 → 状态：意图=退货，槽位={}，阶段=收集信息
- 用户：订单12345 → 状态：意图=退货，槽位={订单号:12345}，阶段=确认
- 用户：对 → 执行退货流程

## 四、指代消解与省略补全（口语化理解）

- **代词绑定**：自动把“它、这个、那款”绑定到上文实体（如“刚才的订单”）。
- **省略补全**：用户说“金额多少”，自动补全为“查询订单12345的金额”。
- **修正识别**：遇到“不对、换一个、刚才不算”，**重置意图/槽位**，覆盖上一轮错误。

## 五、大模型+规则双保险（防幻觉、保可控）

- **LLM深度理解**：处理口语、方言、语序混乱、情绪化表达，**语义级识别**，不依赖关键词。
- **规则硬兜底**：核心意图、敏感词、固定指令用规则锁定，**防止LLM幻觉跑偏**。
- **指令约束**：预设意图清单、对话规范、多轮示例，**限制LLM只在业务范围内识别意图**。

## 六、RAG知识库增强（领域知识不跑偏）

- 每个业务场景绑定**专属知识库**（业务词典、流程、权限），**在业务框架内理解意图**，不产生脱离业务的解读。
- 支持**多RAG**：不同意图对应不同知识库，召回更精准。

## 七、完整工作流（每轮都走一遍）

*图：Dify 每轮对话的意图识别工作流循环（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="15" y="40" width="140" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="85" y="69" text-anchor="middle" font-size="14" fill="#1e293b">接收当前消息</text>
  <line x1="155" y1="64" x2="211" y2="64" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="215" y="40" width="190" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="310" y="61" text-anchor="middle" font-size="14" fill="#1e293b">拼接历史+状态+锚点</text>
  <text x="310" y="80" text-anchor="middle" font-size="12" fill="#475569">意图/槽位/记忆锚点</text>
  <line x1="405" y1="64" x2="461" y2="64" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="465" y="40" width="180" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="555" y="61" text-anchor="middle" font-size="14" fill="#1e293b">指代消解+省略补全</text>
  <text x="555" y="80" text-anchor="middle" font-size="12" fill="#475569">语义归一</text>
  <path d="M555,88 L555,120 L120,120 L120,156" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="30" y="160" width="180" height="48" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="120" y="181" text-anchor="middle" font-size="14" fill="#1e293b">三级判定：规则→LLM→RAG</text>
  <text x="120" y="200" text-anchor="middle" font-size="12" fill="#475569">输出主意图+槽位更新</text>
  <line x1="210" y1="184" x2="266" y2="184" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="270" y="160" width="170" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="355" y="181" text-anchor="middle" font-size="14" fill="#1e293b">更新会话状态</text>
  <text x="355" y="200" text-anchor="middle" font-size="12" fill="#475569">缺槽追问/改意图重置</text>
  <line x1="440" y1="184" x2="496" y2="184" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="500" y="160" width="180" height="48" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="590" y="181" text-anchor="middle" font-size="14" fill="#1e293b">生成应答/执行动作</text>
  <text x="590" y="200" text-anchor="middle" font-size="12" fill="#475569">进入下一轮循环</text>
  <path d="M590,156 L590,18 L85,18 L85,36" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arw)"/>
  <text x="320" y="33" font-size="12" fill="#475569">下一轮</text>
</svg>

1. 接收当前用户消息；
2. 拼接**历史对话+当前状态（意图/槽位）+记忆锚点**；
3. 指代消解、省略补全、语义归一；
4. 规则→LLM→RAG三级判定，输出**主意图+槽位更新**；
5. 更新会话状态，**缺槽则追问、改意图则重置**；
6. 生成应答/执行动作，进入下一轮循环。

## 总结：Dify多轮意图识别公式

**精准识别 = 分层意图流水线（规则+LLM+RAG） + 会话记忆（压缩+锚点） + 对话状态机（意图+槽位+阶段） + 指代消解 + 领域知识库约束**

这套方案解决了口语随意、省略、指代、中途改需求的问题，同时靠规则+领域知识避免大模型幻觉，**企业级落地稳定可靠**。

需要我给你一份可直接复制的 Dify 意图识别 Prompt 模板（含 Few-shot 示例与记忆锚点占位符）吗？
