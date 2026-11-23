# 大模型面试复习-第55期（上下文工程 Context Engineering 深度实战版）

> **本期主线**：上下文工程 Context Engineering —— 把"对的信息、在对的时机、以对的结构、塞进对的窗口"交给 LLM 的完整工程体系。  
> 它是 **Agent Harness（第35/44/45/52期）、FuncHub 工具调用（第41期）、RAG（第38期）、GraphRAG（第46期）、MemoryWeaver 记忆（第47期）** 的共同内核，也是"大模型相关项目核心亮点"被反复提及却从未单点深挖的那一层。

---

---

前 54 期已覆盖：Agent Harness 编排与 SRE、RAG / GraphRAG 检索增强、FuncHub 函数调用、CodeWeaver 代码智能、EdgeLLM 端侧部署、LLMOps 可观测、Reasoning-RL 推理训练、ModelRouter 网关路由、ProtocolHub 协议互操作、MemoryWeaver 长期记忆、DataFoundry 合成数据、FlashAttention 算子优化、AIGC Studio 生成、VisionLLM 多模态理解、InterpLab 机制可解释性。

**唯独缺"上下文工程"这一横切层**。2025–2026 年，"Prompt Engineering 已死，Context Engineering 当立"成为共识：当模型能力趋于同质化，决定 Agent 成败的 70% 在"喂给模型的上下文质量"。本期以 **ContextForge** 为旗舰，串联前 15 个项目，直接回应需求 #1（大模型相关项目核心亮点速览）。

---

---

### 2.1 全项目核心亮点速览矩阵

| th | th | th | th | th |
| --- | --- | --- | --- | --- |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |

> 上述 16 个项目全部依赖"上下文工程"把信息组织进窗口：Agent Harness 拼装工具结果、RAG 拼装检索片段、MemoryWeaver 拼装记忆、FuncHub 拼装函数签名。**ContextForge 是它们的公共底座。**

### 2.2 旗舰项目：ContextForge 上下文工程平台

**六层架构（ASCII）**

```
<code>┌─────────────────────────────────────────────────────────────┐<br/>│  L6  可观测与治理层  │ 上下文命中率 / 污染率 / 成本 / 回放审计   │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  L5  缓存与压缩层  │ Prefix Cache 命中 / 语义压缩 / 预算闸门    │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  L4  模板注入层    │ 类型安全模板引擎 / 变量校验 / 占位渲染     │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  L3  压缩裁剪层    │ 预算分配 / 相关性衰减 / 冲突裁决 / 截断    │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  L2  记忆融合层    │ 工作/情景/语义记忆三因子检索 + 矛盾裁决    │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  L1  检索编排层    │ RAG 检索 + 工具结果 + 系统提示 三源归一     │<br/>├─────────────────────────────────────────────────────────────┤<br/>│  L0  采集接入层    │ 多模态输入 / 高斯去噪 / 结构化解析          │<br/>└─────────────────────────────────────────────────────────────┘<br/>         ↑ 上下文沿 L0→L6 逐层收敛，最终注入模型窗口</code>
```

**量化成果（线上 6 个月，覆盖 Agent Harness + RAG 两条业务线）**

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

---

---

### 难点 1：长上下文窗口与 KV 显存压力

**根因**：窗口 token 数 L 增长，KV Cache 显存线性膨胀。KV 显存公式：

```
<code>KV_size = 2 × L × n_layers × n_kv_heads × head_dim × bytes_per_elem</code>
```

以 7B（32 层、GQA 8 KV heads、head_dim 128、FP16）为例：单条 128K 上下文 KV ≈ 2×128K×32×8×128×2 ≈ **16.8 GB**，已超单卡可用显存。

**方案**：①预算分配（把有限 token 留给高价值源）；②分层摘要（超长历史先压缩再入窗）；③GQA/MQA 降 KV 头数；④KV 量化（K INT8 / V INT4）。

**预算分配代码（权重×相关性 双因子）**

```
<code>from dataclasses import dataclass<br/><br/>@dataclass<br/>class ContextSource:<br/>    name: str<br/>    weight: float      # 静态优先级权重（系统提示 &gt; 工具结果 &gt; 检索 &gt; 记忆 &gt; 历史）<br/>    tokens: int        # 该源原始 token 数<br/>    relevance: float   # 动态相关性 0~1<br/><br/>def allocate_budget(sources, total_budget):<br/>    """按 权重×相关性 占比分配 token 预算；超过源真实容量则截断，溢出回收补偿"""<br/>    scores = [s.weight * s.relevance for s in sources]<br/>    s_sum = sum(scores) or 1.0<br/>    plan, used = [], 0<br/>    for s, sc in zip(sources, scores):<br/>        alloc = min(int(total_budget * sc / s_sum), s.tokens)  # 不超过源真实容量<br/>        plan.append([s.name, alloc]); used += alloc<br/>    spare = total_budget - used<br/>    for i, (name, alloc) in enumerate(plan):                  # 溢出回收：补足预算<br/>        add = min(spare, sources[i].tokens - alloc)<br/>        plan[i][1] += add; spare -= add<br/>        if spare &lt;= 0: break<br/>    return plan  # 例：[(system,2000),(tool,1500),(retrieved,3000),(memory,1500),(history,2000)]</code>
```

### 难点 2：动态上下文组装（检索 + 记忆 + 工具结果三源融合）

**根因**：三类来源语义粒度、新鲜度、权威度完全不同，简单拼接会互相挤占、把高价值工具实时结果埋没在历史里。

**方案**：统一"相关性 × 新鲜度 × 权威度"打分排序，工具实时结果权威度最高（置顶），预算触顶即截断。

```
<code>import math<br/><br/>def relevance_score(item, query_emb, alpha=0.6, beta=0.3, gamma=0.1, half_life=20):<br/>    sim = cosine(item.emb, query_emb)                  # 语义相关性 0~1<br/>    fresh = 0.5 ** (item.age_hours / half_life)        # 时间指数衰减<br/>    auth = item.authority                             # 来源权威度（系统1.0/工具1.0/检索0.9/记忆0.7）<br/>    return alpha * sim + beta * fresh + gamma * auth<br/><br/>def assemble_context(query_emb, retrieved, memory, tool_results, budget):<br/>    cands = []<br/>    for r in retrieved:  cands.append((r.text, relevance_score(r, query_emb, auth=0.9)))<br/>    for m in memory:     cands.append((m.text, relevance_score(m, query_emb, auth=0.7, fresh=m.recency)))<br/>    for t in tool_results: cands.append((t.text, relevance_score(t, query_emb, auth=1.0, fresh=1.0)))<br/>    cands.sort(key=lambda x: x[1], reverse=True)       # 工具结果天然靠前<br/>    chosen, used = [], 0<br/>    for text, _ in cands:<br/>        t = estimate_tokens(text)<br/>        if used + t &gt; budget:                          # 触顶截断（可再对末块做句级压缩）<br/>            tail = truncate_to_budget(text, budget - used)<br/>            if tail: chosen.append(tail)<br/>            break<br/>        chosen.append(text); used += t<br/>    return "\n\n".join(chosen)</code>
```

### 难点 3：上下文污染与优先级冲突

**根因**：多源上下文互相矛盾（如记忆说"用户在上海"，检索说"总部在北京"），或低价值噪声挤占窗口，导致模型被"带偏"。

**方案**：①三因子打分（难点2）天然降权噪声；②矛盾裁决——对实体/数值类信息做一致性校验，冲突时按权威度+新鲜度仲裁；③滑动窗口淘汰最旧最低分块。

```
<code>def resolve_conflict(a, b):<br/>    """同一槽位两路信息冲突：权威度优先，其次新鲜度，返回胜者 + 置信"""<br/>    if a.authority != b.authority:<br/>        return (a, b) if a.authority &gt; b.authority else (b, a)<br/>    return (a, b) if a.age_hours &lt; b.age_hours else (b, a)<br/><br/>def prune_by_decay(items, window=10, keep_top=0.7):<br/>    """保留最近 window 个块中相关性前 keep_top 比例，其余淘汰"""<br/>    recent = items[-window:]<br/>    recent.sort(key=lambda x: x.score, reverse=True)<br/>    keep_n = max(1, int(len(recent) * keep_top))<br/>    return recent[:keep_n]</code>
```

### 难点 4：Prompt 模板工程与变量注入

**根因**：手写字符串拼接易漏变量、注入错位、长文本与标量混排导致占位混乱，且难以在 16 个项目间复用。

**方案**：类型安全模板引擎——解析占位符、缺变量即报错（不静默留空）、长文本与标量分通道注入。

```
<code>from string import Formatter<br/><br/>def render_template(tpl: str, **vars):<br/>    needed = {fn for _, fn, _, _ in Formatter().parse(tpl) if fn}<br/>    missing = needed - set(vars)<br/>    if missing:<br/>        raise KeyError(f"模板缺变量: {missing}")        # 缺变量直接失败，避免喂空上下文<br/>    # 长文本走 &lt;context&gt; 占位（单独裁剪），标量走 {var} 内联<br/>    return tpl.format(**vars)</code>
```

### 难点 5：上下文缓存（Prefix Cache / 语义压缩）

**根因**：每请求重复编码相同系统提示 + few-shot，浪费算力；长上下文整体重算成本高。

**方案**：①Prefix Cache——系统提示 + 示例必须稳定且前置，命中即跳过前缀 prefill；②语义压缩——按重要性保留 top-k 句。

**Prefix Cache 命中率公式**：

```
<code>H = Σ(cached_prefix_tokens) / Σ(total_prompt_tokens)   # 跨请求共享前缀占比</code>
```

命中前提：前缀内容 + 模型 + 版本完全一致且位于 prompt 最前。故系统提示必须版本化、稳定化。

```
<code>import hashlib<br/><br/>def prefix_cache_key(system_prompt, few_shot, model, version):<br/>    canonical = f"{model}|{version}|{system_prompt}|{few_shot}"   # 必须稳定前置<br/>    return hashlib.sha256(canonical.encode()).hexdigest()<br/><br/>def compress_context(sentences, budget, importance_fn):<br/>    """类 LLMLingua：按重要性保留 top-k 句直到预算（重要性=与query相似度+关键词命中）"""<br/>    ranked = sorted(sentences, key=importance_fn, reverse=True)<br/>    out, used = [], 0<br/>    for s in ranked:<br/>        t = estimate_tokens(s)<br/>        if used + t &gt; budget: break<br/>        out.append(s); used += t<br/>    return sorted(out, key=lambda x: sentences.index(x))   # 还原原文顺序</code>
```

### 难点 6：多模态上下文融合

**根因**：图像/表格 token 数与文本不在同一量级（一张图经 ViT 展开可达数百~数千 token），盲目塞入会挤垮文本窗口，且交错顺序影响注意力。

**方案**：①视觉 token 预算单独划拨（如总窗 128K 中给视觉 24K）；②交错布局（interleaved）而非尾部堆叠，让图文就近对齐；③高分辨率切图（AnyRes）按需分配。

```
<code>def multimodal_budget(total, text_ratio=0.8, vision_ratio=0.15, reserve=0.05):<br/>    return {<br/>        "text": int(total * text_ratio),<br/>        "vision": int(total * vision_ratio),   # 视觉独立配额，避免挤垮文本<br/>        "reserve": int(total * reserve),       # 留给工具/系统<br/>    }<br/><br/>def interleave(text_segments, image_tokens):<br/>    """图文交错：每段文本后紧跟其相关图像 token，就近对齐"""<br/>    blocks = []<br/>    for i, seg in enumerate(text_segments):<br/>        blocks.append(seg)<br/>        if i &lt; len(image_tokens):<br/>            blocks.append(image_tokens[i])<br/>    return blocks</code>
```

---

---

### Q1. Context Engineering 与 Prompt Engineering 本质区别？

**答**：Prompt Engineering 关注"单条指令怎么写"（措辞、few-shot、角色），对象是**静态模板**；Context Engineering 关注"动态地把哪些信息、以什么结构、在什么时候组装进窗口"，对象是**多源信息的运行时编排**。一句话：Prompt 是"一句话怎么说"，Context 是"把什么样的证据包递给模型"。当模型能力同质化后，胜负在上下文质量——这也是为何 Agent Harness 等 16 个项目都把上下文编排做成独立底座。

### Q2. 上下文窗口有限时，如何保证关键信息不丢？

**答**：三层保障。①**预算分配**（难点1）：按"权重×相关性"把有限 token 优先分给工具实时结果、系统约束、高相关检索；②**分层摘要**：超长历史先摘要再入窗，保留骨架；③**缓存+压缩**（难点5）：Prefix Cache 跳过稳定前缀，语义压缩保留 top-k 关键句。核心是"宁缺毋滥 + 宁新毋旧"——新工具结果 > 旧记忆。

### Q3. 多源上下文冲突（记忆 vs 检索 vs 工具）怎么裁决？

**答**：统一权威度+新鲜度仲裁（难点3 `resolve_conflict`）。优先级：**工具实时结果（权威1.0，新鲜1.0）> 系统约束 > 高相关检索 > 长期记忆**。冲突时不简单拼接，而是对实体/数值槽位做一致性校验，胜者入窗并打"置信标签"，冲突信息可降级为"待确认"提示而非直接给答案。

### Q4. 怎么最大化 Prefix Cache 命中率？

**答**：命中率 H = 共享前缀 token / 总 prompt token。三要点：①**前缀稳定前置**——系统提示、few-shot 必须版本化、内容不变且位于最前；②**避免随机内容前置**（如把时间戳/用户ID 放末尾）；③**共享模板**——同一业务线复用同一 system prompt，使跨请求前缀重合。ContextForge 把命中率从 12% 拉到 63%，直接省掉前缀 prefill 算力。

### Q5. 长对话历史怎么压缩不丢关键信息？

**答**：①**句级语义压缩**（难点5 `compress_context`）：按重要性保留 top-k 句；②**分层记忆下沉**（MemoryWeaver 思路）：把稳定事实从工作记忆沉淀到语义记忆，窗口只留指针；③**衰减淘汰**（难点3 `prune_by_decay`）：旧低分块滑出窗口；④**关键事件锚定**：把"用户偏好变更""任务状态"等锚点句强制保留。压缩不是删，而是"降冗余+提密度"。

### Q6. 上下文工程如何防"中间遗忘"（lost in the middle）与污染？

**答**：①**位置优化**：关键信息放首尾（首是系统约束，尾是当前 query + 最新工具结果），中间放次要检索；②**交错而非堆叠**：多模态图文就近对齐（难点6）；③**污染抑制**：相关性打分 + 冲突裁决（难点2/3）把噪声降权；④**可观测回放**（L6）：记录每段上下文来源与命中，上线后监控"污染率"指标，异常即定位是哪一路源在带偏。

---

---

### 模拟题 1：千万用户 Agent 平台——上下文工程端到端设计

**场景**：为 Agent Harness 设计支撑千万用户的上下文工程子系统（动态组装 + 缓存 + 压缩 + 多租户隔离）。

**参考答案要点**：

1. **架构**：复用 ContextForge 六层（采集→检索编排→记忆融合→压缩裁剪→模板注入→缓存治理），每层无状态、水平扩展。
1. **动态组装**：三源（检索/记忆/工具）统一"相关性×新鲜度×权威度"打分（代码难点2），工具实时结果置顶，预算触顶截断。
1. **预算分配**：按"权重×相关性"双因子分配（代码难点1），系统约束与工具结果高权重，长历史低权重。
1. **缓存**：版本化系统提示前置 + Prefix Cache（命中率目标 >60%），语义压缩降冗余（难点5）。
1. **多租户隔离**：每租户独立缓存命名空间 + 预算配额，防跨租户上下文泄露（呼应 ProtocolHub 权限边界）。
1. **可观测**：监控命中率/污染率/成本（L6），异常回放定位。
1. **量化目标**：有效上下文利用率 >85%、token 成本 −60%、答非所问率 <5%。

### 模拟题 2：某天"答非所问率"翻倍——30 分钟止血复盘

**场景**：线上监控发现答非所问率从 4.3% 飙到 9%，P99 首 token 微涨，要求 30 分钟内定位止血。

**参考答案要点**（SOP）：

1. **0–5min 定界**：看 L6 可观测——是全局还是单租户？单业务线？确认"污染率"与"检索命中率"哪个异常。
1. **5–15min 归因**（按概率排序）：①**检索源退化**：RAG 召回@10 骤降（索引更新失败/embedding 服务抖动）→ 工具实时结果占比被动上升但内容错；
1. ②**预算分配失衡**：某新功能把系统提示撑爆，挤掉检索片段 → 调高检索权重；
1. ③**模板变量缺失**：`render_template` 新模板漏变量，静默留空导致上下文空洞（应改为报错拦截）；
1. ④**Prefix Cache 失效**：系统提示被改但未升版本，命中率从 63% 跌到 10%，prefill 成本涨、时延涨。
1. **15–25min 止血**：回滚最近一次系统提示/模板版本（一致性哈希染色 + 影子 A-B，呼应 LLMOps）；临时提权检索源；开启更激进语义压缩兜底。
1. **25–30min 验证**：灰度 5% 流量确认答非所问率回落，再全量。
1. **根因**：八成是"前缀版本未升导致缓存失效 + 检索退化"复合，需加"缓存命中率跌阈值自动告警"。

### 模拟题 3：7B 经上下文工程追平 GPT-4o（检索增强 + 记忆 + 压缩一体化）

**场景**：成本敏感场景，用 7B 小模型通过上下文工程达到 GPT-4o 级回答质量，成本降 90%。

**参考答案要点**：

1. **检索增强**：RAG + GraphRAG 双模，把领域知识以高相关片段注入（替代模型参数记忆），弥补 7B 参数不足。
1. **记忆个性化**：MemoryWeaver 分层记忆，沉淀用户偏好/历史，使回答"像了解你"。
1. **精准压缩**：语义压缩保留 top-k 关键句，把"信息密度"拉满，小窗口塞进大价值。
1. **约束生成**：FuncHub 约束解码保证输出结构合法，减少小模型格式翻车。
1. **路由兜底**：ModelRouter 把高难 query 路由给大模型，简单 query 走 7B，整体质量不掉、成本 −90%。
1. **评测闭环**：LLMOps 在线评测监控质量，发现 7B 吃力的长推理 query 自动升级。
1. **结论**：上下文工程让"模型能力"≈"基础模型 + 外部知识 + 个性化记忆 + 精准编排"，7B 在知识密集型任务追平大模型可行。

---

---

```
<code>【一句话】上下文工程 = 把对的信息在对的时机以对的结构塞进对的窗口<br/>【六层】采集→检索编排→记忆融合→压缩裁剪→模板注入→缓存治理<br/>【预算】alloc = B × (w×r) / Σ(w×r)，超源容量截断，溢出回收<br/>【KV】KV_size = 2·L·n_layers·n_kv_heads·head_dim·bytes<br/>【打分】score = α·sim + β·0.5^(age/half) + γ·authority<br/>【缓存】H = 共享前缀token / 总prompt token；前提=前缀稳定前置<br/>【优先级】工具实时 &gt; 系统约束 &gt; 检索 &gt; 记忆 &gt; 历史<br/>【防丢】预算分配 + 分层摘要 + Prefix Cache + 语义压缩<br/>【防污染】相关性打分 + 冲突裁决(权威/新鲜) + 可观测回放<br/>【多模态】视觉独立配额(总窗15%) + 图文交错对齐<br/>【项目底座】Agent Harness/RAG/GraphRAG/FuncHub/MemoryWeaver 都依赖它</code>
```

---

---