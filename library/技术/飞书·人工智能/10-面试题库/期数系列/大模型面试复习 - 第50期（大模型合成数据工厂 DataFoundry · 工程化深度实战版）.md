# 大模型面试复习 - 第50期（大模型合成数据工厂 DataFoundry · 工程化深度实战版）

> 日期：2026-07-24 ｜ 主题：大规模高质量训练数据合成与治理（Self-Instruct / Evol-Instruct / Self-Play / Rejection Sampling / 去重防污染 / 数据飞轮）  
> 旗舰项目：**DataFoundry** —— 把"训练数据供给"做成可观测、可治理、可闭环的工程平台  
> 里程碑：本期为**第 50 期**，是自动化复习以来的第 50 份材料。

---

---

前 49 期已覆盖：Agent Harness(35/44/45)、RAG(38)、GraphRAG(46)、FuncHub(41)、CodeWeaver(42)、EdgeLLM(43)、LLMOps(39)、Reasoning-RL(37)、MemoryWeaver(47)、ModelRouter(48)、ProtocolHub(49)、预训练(33)、微调(36)、量化(24)、安全对齐(25)、长上下文(26)、推理服务(27)、评估(28)、对齐(34)、归一化(23)、蒸馏压缩(31)、推理增强(32)、VLM(40)。

**本期补的缺口**：几乎所有 2025–2026 SOTA 模型（Llama 3.x、DeepSeek-V3/R1、Qwen2.5/3、Phi-4、Mistral）都依赖**海量合成数据**——真实高质量数据在 2026 年基本被"洗"完了，"数据工厂"是模型能力上限的真正上游。这条"种子任务 → 指令演化 → 合成 → 质量验证 → 去重防污染 → 数据飞轮"主线此前从未单点深挖；它是 **微调(36) / 对齐(34) / 预训练(33)** 的共同上游，把"数据飞轮、拒绝采样、self-instruct、指令演化、多轮 Agent 轨迹合成"全部工程化。

与已覆盖主题的边界（避免重复）：

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |

---

---

```
<code>┌──────────────────────────────────────────────────────────────────────┐<br/>│                      ⑥ 治理层（Governance &amp; Flywheel）                  │<br/>│   血缘追踪 │ 数据飞轮(指标→采样→重训) │ 成本计量 │ 合规审计 │ 看板      │<br/>└───────────────────────────────────┬──────────────────────────────────┘<br/>                                     │ 通过验证的数据回到飞轮<br/>┌───────────────────────────────────▼──────────────────────────────────┐<br/>│                      ⑤ 去重与防污染层（Dedup &amp; Contam）                 │<br/>│   MinHash(LSH) 近重 │ SimHash(汉明) │ 13-gram 跨集污染检测 │ 黑/白名单   │<br/>├──────────────────────────────────────────────────────────────────────┤<br/>│                      ④ 质量验证层（Verification）                      │<br/>│   事实校验(NLI+检索) │ 质量分类器(RM-as-Judge) │ 可执行性验证 │ 难度回归  │<br/>├──────────────────────────────────────────────────────────────────────┤<br/>│                      ③ 合成执行层（Synthesis）                         │<br/>│   Self-Instruct │ Evol-Instruct(深/广演化) │ Self-Play │ 拒绝采样 │ 蒸馏 │<br/>├──────────────────────────────────────────────────────────────────────┤<br/>│                      ② 指令演化层（Evolution）                         │<br/>│   广度演化(新技能) │ 深度演化(更难) │ 约束(多语/长链/工具) │ 难度打分    │<br/>├──────────────────────────────────────────────────────────────────────┤<br/>│                      ① 种子任务库（Seed Bank）                         │<br/>│   人工种子 │ 真实指令蒸馏 │ 覆盖度聚类(embedding) │ 多样性门控          │<br/>└──────────────────────────────────────────────────────────────────────┘<br/>        ↑                                               ↓<br/>   真实数据(人工/公开)                          训练集(飞轮持续产出)</code>
```

---

---

### 1.1 DataFoundry 六层架构（见上方 ASCII）

核心思想：**把"造数据"变成一条可观测、可治理、可闭环的流水线**。每一层都有明确的入/出口 schema 与质量门（gate），未通过的数据不进训练集、但进飞轮做归因。

### 1.2 大模型相关项目核心亮点速览（呼应需求 #1：总结核心亮点）

> 用户点名"如 Agent Harness 项目"。下表把已复习的主流大模型项目亮点与量化成果做一页速览，便于横向对照；本期旗舰详见下方 1.3+。

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

### 1.3 合成数据技术全景对比（含代码思路）

| th | th | th | th | th |
| --- | --- | --- | --- | --- |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |

**Self-Instruct 的核心闭合（含代码骨架）**：

```
<code>import json, random<br/>from openai import OpenAI<br/><br/>SEED_INSTRUCTIONS = [...]  # 175 条人工种子（class/instance 混合）<br/>client = OpenAI()<br/><br/>def generate_instruction(ins_pool: list[str], k=8) -&gt; str:<br/>    """用池子里的指令做 few-shot，让模型造一条新指令。"""<br/>    demo = random.sample(ins_pool, k)<br/>    prompt = ("你是任务生成器。给定以下已有指令，创造一条**不同且可行**的新指令。\n"<br/>              + "\n".join(f"{i+1}. {x}" for i, x in enumerate(demo)))<br/>    r = client.chat.completions.create(<br/>        model="teacher", messages=[{"role":"user","content":prompt}],<br/>        temperature=1.0, max_tokens=128, n=1)<br/>    return r.choices[0].message.content.strip()<br/><br/>def filter_novel(new_ins: str, pool: list[str], model) -&gt; bool:<br/>    """用模型判断是否与池子'语义重复'；也可换 embedding 余弦 &lt; 0.92。"""<br/>    judge = model.classify_similarity(new_ins, pool)<br/>    return judge == "novel"<br/><br/>def self_instruct(n_target=50000, seed=SEED_INSTRUCTIONS):<br/>    pool = list(seed); data = []<br/>    while len(data) &lt; n_target:<br/>        ins = generate_instruction(pool)<br/>        if not filter_novel(ins, pool, model):   # 多样性门控<br/>            continue<br/>        # 让模型再生成 (输入, 输出) 实例<br/>        out = client.chat.completions.create(<br/>            model="teacher",<br/>            messages=[{"role":"user","content": f"完成任务：{ins}\n给出输入与期望输出。"}],<br/>            temperature=0.7)<br/>        data.append({"instruction": ins, "completion": out.choices[0].message.content})<br/>        pool.append(ins)                          # 新指令回流池子<br/>    return data</code>
```

### 1.4 质量验证：RM-as-Judge + 规则（含代码）

事实正确性是合成数据最大坑。我们用"规则硬过滤 + RM 软打分 + 检索/NLI 事实校验"三道闸：

```
<code>def verify_sample(x: dict, rm, retriever, nli) -&gt; tuple[bool, float, str]:<br/>    # ① 规则硬过滤：长度/格式/注入词/PII<br/>    if not (16 &lt;= len(x["completion"]) &lt;= 2048): return False, 0.0, "len"<br/>    if has_injection(x["completion"]):           return False, 0.0, "inject"<br/>    if has_pii(x["completion"]):                 return False, 0.0, "pii"<br/>    # ② RM 软打分（helpfulness/correctness，0~10）<br/>    score = rm.score(x["instruction"], x["completion"])<br/>    if score &lt; 6.5:                              return False, score, "rm_low"<br/>    # ③ 事实校验：有可验证事实声明时，检索证据 + NLI 蕴含<br/>    claims = extract_claims(x["completion"])<br/>    if claims:<br/>        ev = retriever.search(x["instruction"])<br/>        if nli.contradicts(claims, ev):          return False, score, "fact"<br/>    return True, score, "ok"</code>
```

### 1.5 数据飞轮（含覆盖度公式）

飞轮把"线上指标"反向变成"下一批种子"，形成闭环：

```
<code>线上指标(准确率/拒答率/某类失败) → 聚类归因 → 生成补强种子 → 演化合成 → 验证去重 → 重训 → 指标回升</code>
```

覆盖度（防止偏科）用类别 PCA/聚类后的召回度量：  
  
飞轮每轮把低覆盖簇（\text{Coverage}_c ）定向补强。

### 📊 量化成果（本期项目）

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

---

---

### 2.1 种子任务多样性枯竭（diversity collapse）

**根因**：Self-Instruct 用"池内 few-shot"生成新指令，模型会收敛到高频模式（如"写一封邮件"反复出现），池子越滚越偏 —— 这是 **模型坍塌（model collapse）** 在指令层面的表现。  
**方案**：① embedding 聚类实时监控覆盖度（1.5 公式）；② 对抗式生成——专挑"低覆盖簇"做 seed；③ 分层抽样：每轮按簇配额抽取 few-shot，强制均衡。

```
<code>def balanced_sample(pool, clusters, quota):<br/>    """按簇配额抽 few-shot，避免模型只复读高频簇。"""<br/>    demo = []<br/>    for c, items in clusters.items():<br/>        take = min(quota, max(1, int(len(items)*0.1)))<br/>        demo += random.sample(items, take)<br/>    return demo</code>
```

**深度点**：模型坍塌的理论下界（Shumailov et al. 2023）——当训练数据递归来自模型自身、真实数据占比 r_{\text{real}} 过低时，分布方差按代指数收缩 \sigma_t^2 \propto (1-r_{\text{real}})^t。**经验阈值**：合成占比  且每代混入 \ge 10\% 真实数据可抑制坍塌（与本期 78% 占比 + 飞轮持续注入真实失败样本一致）。

### 2.2 指令演化质量退化（instruction inflation）

**根因**：Evol-Instruct 让"把指令变难"，模型可能变成"请非常非常详细地…"这类**空泛加重**而非真难（inflation），导致模型学会啰嗦而非真强。  
**方案**：① 深/广两种演化分别用不同 prompt；② **难度回归校验**——演化后用 RM 给难度打分，并要求难度分高于原指令且"信息密度"（实词比）不降；③ 拒绝"仅靠加'请详细'提难"的样本。

```
<code>DEEP_EVOL = "重写下面任务，使其**更专业/更约束/需要多步推理**，但不得改变任务本质、不得只加'请详细'。"<br/>BROAD_EVOL = "把下面任务改写为一个**不同技能类别**的新任务（如从写作变代码/数学），保持同等难度。"<br/><br/>def evol(instr, kind):<br/>    p = DEEP_EVOL if kind == "deep" else BROAD_EVOL<br/>    new = llm(f"{p}\n原任务：{instr}")<br/>    diff_old, diff_new = info_density(instr), info_density(new)   # 实词/总词<br/>    if kind == "deep" and (rm.difficulty(new) &lt;= rm.difficulty(instr) or diff_new &lt; diff_old*0.9):<br/>        return None  # 拒绝空泛演化<br/>    return new</code>
```

### 2.3 合成数据事实幻觉（faithfulness）

**根因**：教师模型在知识盲区会"自信编造"，合成数据把幻觉原样传给学生。  
**方案**：① 先**检索证据**再让模型基于证据写（RAG-style 合成）；② 写完后用 **NLI 蕴含模型**校验关键 claim 是否被证据蕴含；③ 多采样**自一致性**（self-consistency）投票，分歧大的丢弃；④ 知识类强制附引用。

```
<code>def faithful_synth(q, retriever, llm, nli, k=5):<br/>    ev = retriever.search(q, top_k=k)                 # 先拿证据<br/>    ans = llm(f"仅依据以下证据回答问题：\n{ev}\n问题：{q}")<br/>    claims = extract_claims(ans)<br/>    if any(nli.label(c, ev) == "contradiction" for c in claims):<br/>        return None                                   # 与证据矛盾 → 丢弃<br/>    return ans</code>
```

### 2.4 去重与训练-测试污染（dedup & contamination）

**根因**：① 同类合成会撞车（近重复）；② **更危险的是污染评测集**——合成数据与公开 benchmark（MMLU/GSM8K）重叠，导致"虚高"且无法泛化。  
**方案**：① **MinHash + LSH** 做近重复聚类（Jaccard 近似）；② **13-gram 文档哈希**跨训练/评测集做污染检测（Lee et al. 2021）；③ 命中评测集 13-gram 的样本直接剔除。

```
<code>import hashlib<br/>def shingles(text, n=5): return set(text[i:i+n] for i in range(len(text)-n+1))<br/><br/>def minhash(text, k=128, prime=2**31-1):<br/>    """k 个随机排列的最小哈希，Jaccard ≈ 相同桶占比。"""<br/>    h = []<br/>    for i in range(k):<br/>        seed = (i*1000003 + 12345) % prime<br/>        mn = prime<br/>        for s in shingles(text, 5):<br/>            v = (hashlib.md5(s.encode()).digest().__hash__() ^ seed) % prime<br/>            mn = min(mn, v)<br/>        h.append(mn)<br/>    return h<br/><br/>def jaccard_minhash(a, b): return sum(1 for x,y in zip(a,b) if x==y)/len(a)<br/><br/>def contamination_13gram(doc, bench_index):<br/>    """若文档任一 13-gram 命中 benchmark 索引 → 污染。"""<br/>    return any(g in bench_index for g in shingles(doc, 13))</code>
```

**深度点**：去重不是"越少重复越好"。适度重复（hard negative / 高频技能）对学习有益；关键是**去掉近重复但保留语义簇的代表性样本**，并用污染检测守住评测诚信。

### 2.5 多轮 Agent 轨迹合成（trajectory synthesis）

**根因**：单轮 SFT 数据训不出会"多步规划/工具调用/自我纠错"的 Agent；直接让模型编多轮对话，常出现**步骤不可执行、工具参数不符合环境 schema、提前给答案**。  
**方案**：① 在**真实/仿真环境**里跑（沙箱 + 工具），而非纯文本编；② 任务 → 环境初始化 → 模型 rollout → **执行验证**（工具返回是否合法、目标是否达成）→ 只保留成功轨迹；③ 失败轨迹做"纠错回放"（把错误返回喂回去让模型修正）生成困难正样本。

```
<code>def synth_trajectory(task, env, policy, max_step=8):<br/>    traj, obs = [], env.reset(task)<br/>    for _ in range(max_step):<br/>        act = policy(obs, traj)                       # 含工具调用<br/>        if not env.valid_action(act):                 # 参数不符合 schema → 失败样本<br/>            corrected = policy(obs, traj + [("bad", act)])   # 纠错回放<br/>            traj.append(("correction", act, corrected)); continue<br/>        obs, done = env.step(act)<br/>        traj.append(act)<br/>        if done and env.goal_met(): return traj        # 只保留成功轨迹<br/>    return None                                        # 未达成 → 丢弃</code>
```

### 2.6 成本与规模（含成本数学模型）

**根因**：全量用最强教师（如 GPT-4 级）合成 1.2M 条/天 → 成本爆炸；且 80% 样本是"简单可 cheap 模型搞定"的。  
**方案**：**分级合成**——用成本模型把样本按难度路由到不同档次模型；只在 \text{Cost} = \sum_{t\in\{\text{cheap,mid,exp}\}} N_t \cdot (L^{in}_t\cdot p^{in}_t + L^{out}_t\cdot p^{out}_t)

```
<code>def route_model(difficulty: float) -&gt; str:<br/>    # 难度门控：只有头部硬样本走贵模型，其余本地小模型<br/>    if difficulty &gt; 8.5: return "exp-teacher"      # &lt;5% 预算<br/>    if difficulty &gt; 6.0: return "mid-teacher"<br/>    return "local-7b"</code>
```

**量化**：分级后单位成本 −89%（见 1.5），且"贵模型只造难样本"反而提升了下游推理/代码指标（难例增益更大）。

---

---

**Q1：合成数据 vs 真实数据的核心风险是什么？怎么缓解"模型坍塌"？**

- 风险：① **模型坍塌 / 熵坍塌**——递归用模型自身数据训练，分布方差按代收缩 \sigma_t^2\propto(1-r_{\text{real}})^t，高概率模式被放大、长尾被碾碎，最终输出千篇一律；② **事实幻觉下传**；③ **偏差放大**（教师偏见被固化）。
- 缓解：① 控制合成占比（经验 < 80%）+ 每代混入 ≥10% 真实/失败样本；② 多样性门控（embedding 聚类 + 覆盖度公式）；③ 质量验证三道闸（2.4）；④ 飞轮持续注入真实线上失败样本，打破递归闭环。

**Q2：Self-Instruct、Evol-Instruct、Self-Play 的区别与各自适用？**

- **Self-Instruct**：池内 few-shot 生成**同类新指令**，目标=扩量补领域（1.3）；风险=多样性枯竭（2.1）。
- **Evol-Instruct**：把单条指令演化成**更难/更广**的指令（深/广两种，2.2），目标=推能力上限；风险=指令膨胀（2.2）。
- **Self-Play (SPIN)**：模型与自己博弈迭代——用上一轮模型当"负样本生成器"训本轮，目标=对齐/推理自我提升（如 SPIN、IPL）；风险=自我确认偏差（只信自己）。
- 选型：补量用 Self-Instruct，提难用 Evol-Instruct，对齐/推理自举用 Self-Play，质量门控都接拒绝采样。

**Q3：如何防止合成数据污染评测集（train-test contamination）？**

- ① **13-gram 文档哈希**：把评测 benchmark 切成 13-gram 建索引，任何训练样本若含任一 benchmark 13-gram 即剔除（2.4）；② **嵌入相似度**二次筛查（近义改写也能污染）；③ **留域评测**：用合成数据发布后才出现的内部私有 benchmark 做最终公证；④ **去重前置**：MinHash/LSH 先去近重，降低撞车概率。污染会让指标"虚高且不可泛化"，是红线。

**Q4：拒绝采样（Rejection Sampling）在数据合成中的数学原理？**

- 对每条采样 y\sim\pi_\theta(\cdot|x)，仅当质量 s(x,y)\ge\tau 时接受。接受率 \alpha = \int \mathbf{1}[s(x,y)\ge\tau]\,\pi(y|x)\,dy；要拿到 N 条合格样本，期望采样数 N/\alpha。
- 技巧：① **温度退火**——适当降温提高高质量尾部的相对概率，提升有效接受率；② **分级阈值**——先宽采再严筛，平衡成本；③ 与 RM 打分联用，s 用 RM 分数或规则组合。代价：阈值越高、接受率越低、越贵（2.6 成本模型）。

**Q5：多轮 Agent 轨迹合成如何保证"可用"而非"编出来的"？**

- 关键在**真环境验证**而非纯文本生成（2.5）：① 在沙箱/仿真环境 rollout；② 每步校验工具参数符合 schema（`env.valid_action`），非法即做纠错回放生成困难正样本；③ 只保留 `goal_met()` 的成功轨迹；④ 关键中间步（如检索召回、代码执行结果）必须真实，禁止模型"假装成功"。这样训出的 Agent 才会真执行、会纠错。

**Q6：小模型如何靠合成数据追平大模型？蒸馏 vs 合成数据，怎么选？**

- **蒸馏**：用强教师（GPT-4 级）的**输出分布**（软标签/logits）训学生，学生直接学"答案长什么样"；适合答案明确的任务（分类、短答）。
- **合成数据 + SFT**：用教师生成**高质量 (指令, 完成) 对**训学生，学生学"任务怎么做"；适合复杂/多步任务，配合 Evol-Instruct 提难。
- 组合拳（Phi / DeepSeek 小模型范式）：教师**生成 + 拒绝采样筛选**难样本 → 学生 SFT → 学生再自合成补量（飞轮）→ 仅在头部硬样本回教师。结果：7B 在数学/代码追平 70B，成本是 1/10。

---

---

### 🧪 题 1：设计支持「千亿 Token、1.2M 条/天」的合成数据工厂端到端架构

**考点**：六层流水线、分级合成、去重防污染、质量验证、成本规模、飞轮闭环、可观测。  
**参考答案要点**：

1. **种子层（①）**：人工种子 + 真实指令蒸馏 + embedding 聚类做覆盖度门控（1.5 公式）；低覆盖簇定向补强，防多样性枯竭（2.1）。
1. **演化层（②）**：深/广演化分 prompt，难度回归校验拒绝空泛演化（2.2）。
1. **合成层（③）：Self-Instruct/Evol/Self-Play/拒绝采样混合；分级路由**（2.6 公式）——仅 <5% 硬样本走贵教师，其余本地 7B，成本 −89%。
1. **验证层（④）**：规则硬过滤 + RM-as-Judge + 检索/NLI 事实校验三道闸（1.4 / 2.3），事实错误率压到 <3.5%。
1. **去重防污染层（⑤）**：MinHash+LSH 近重、13-gram 跨集污染检测剔除（2.4），污染率 12%→0.4%。
1. **治理/飞轮层（⑥）**：血缘追踪 + 指标→采样→重训飞轮（1.5）；覆盖度监控；成本计量；看板。
1. **工程**：流水线用 DAG（参考 Agent Harness 35）并逐级背压；验证/去重用分布式 Spark/Flink；吞吐靠水平扩展 + 分级省算力达成 1.2M 条/天。

### 🧪 题 2：合成数据上线后模型「看起来很会、但事实错误率翻倍」，请做 30 分钟止血复盘

**考点**：合成数据质量事故应急、根因定位、最小代价止血、根因修复。  
**参考答案要点**：

- **0–5 min 止血**：① 飞轮血缘（⑥）定位"哪一批合成数据"引入——按 batch 回滚训练集（移除最近 24h 合成数据），换回上一版混合集；② 临时收紧验证门（RM 阈值 6.5→8.0 + 强制事实校验）让新数据先不过线。
- **5–15 min 定位**：① 抽样看错误样本 → 集中在"知识类声明无引用"；② 复现：教师模型在知识盲区自信编造，且 2.3 的 NLI 校验被跳过（为省成本关了检索）；③ 根因=**关了事实校验 + 教师幻觉下传**。
- **15–30 min 修复**：① 恢复"RAG-style 合成"（先检索证据再写，2.3）；② 知识类强制附引用 + NLI 蕴含校验；③ 飞轮把"事实错误"类线上失败样本注入种子（打破递归闭环）；④ 加污染/事实看板告警。
- **根因**：成本优化误关了事实校验，且缺"教师幻觉下传"的兜底。止血后事实错误率回到 <3.5%。

### 🧪 题 3：用合成数据让 7B 在数学/代码追平 70B，给出训练 + 数据 + 评测方案

**考点**：小模型追平、数据配方、拒绝采样、蒸馏组合、评测防污染。  
**参考答案要点**：

1. **数据配方**：① 教师（70B+）生成数学/代码题解 → **拒绝采样**只留 RM/执行测试通过的高质样本（Q4）；② Evol-Instruct 把题**演化更难**（多步/约束）推上限（2.2）；③ 7B 自合成补量（飞轮），只在头部硬样本回教师（2.6 分级）；④ 代码类用**执行验证**（单测通过才留，2.5 思路）。
1. **训练**：SFT（合成对）+ 蒸馏（教师软标签，Q6）+ 可选 GRPO（参考 Reasoning-RL 37）强化推理；数据混合控真实占比 ≥15% 防坍塌（Q1）。
1. **评测防污染**：13-gram 跨集检测剔除污染（Q3）+ 留域私有 benchmark 公证；指标看 GSM8K/MATH/HumanEval 而非刷过的榜。
1. **量化目标**：7B 数学/代码追平 70B 的 95%+，成本 1/10；关键杠杆=**难样本拒绝采样 + 执行/事实验证 + 分级省算力**。

---

---

```
<code>DataFoundry 三句话：<br/>  · 是什么：把"训练数据供给"做成可观测/可治理/可闭环的工厂<br/>  · 为什么：2026 真实高质量数据被洗完，合成数据是能力上限的上游<br/>  · 六层：种子 → 演化 → 合成 → 验证 → 去重防污染 → 治理飞轮<br/><br/>三大风险：模型坍塌(σ²∝(1-r_real)^t) / 事实幻觉下传 / 评测污染<br/> mitigation：合成占比&lt;80% + 每代≥10%真实 + 多样性门控 + 三道验证闸<br/><br/>方法选型：<br/>  Self-Instruct=扩量 / Evol-Instruct=提难 / Self-Play=对齐自举 / Rejection=质量门<br/>  小模型追平 = 教师生成 + 拒绝采样 + Evol提难 + 自合成飞轮 + 头部分级回教师<br/><br/>拒绝采样：接受率 α=∫1[s≥τ]π(y|x)dy；拿 N 条需 N/α 次采样；降温提有效α<br/>去重：MinHash(LSH, Jaccard) 近重；13-gram 跨集检测防污染（红线）<br/>多轮轨迹：真环境 rollout + schema 校验 + 只留 goal_met + 失败做纠错回放<br/><br/>成本模型：Cost=Σ N_t·(L_in·p_in+L_out·p_out)；分级路由贵模型只造&lt;5%硬样本<br/>量化：合成占比 0→78% / 单条成本 −89% / 覆盖 61%→93% / 污染 12%→0.4% / 吞吐 ×600</code>
```

---

---

---

---