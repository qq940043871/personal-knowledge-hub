# 大模型面试复习 · 第39期（LLMOps 可观测性与质量运营平台 · 深度实战版）

> **日期**：2026-07-13 ｜ **主线项目**：LLMObserver —— 企业级大模型应用可观测与质量运营平台  
> **定位**：区别于第27期（推理服务工程化）、第28期（评估方法论）、第35期（Agent 框架），本期从 **"平台工程 + 线上运营"** 视角，复盘一个把 Tracing / 在线评测 / Prompt Ops / 成本治理 串成闭环的生产系统。  
> **深度要求**：含可运行代码、数学推导、架构图、量化数据、速记卡。

---

---

| th | th |
| --- | --- |
| td | td |
| td | td |
| td | td |
| td | td |

**为什么这个项目值得讲**：推理服务（第27期）解决"跑得动"，Agent 框架（第35期）解决"编排得动"，而 **LLMOps 平台解决"上线后看得清、控得住、改得对"**——这是大模型从 Demo 到 Production 最容易被低估、面试最加分的一层。

---

---

```
<code>┌──────────────────────────────────────────────────────────────────────┐<br/>│  L6  运营看板 / 告警 / 数据飞轮（成本·质量·延迟三维 + 智能根因定位）      │<br/>├──────────────────────────────────────────────────────────────────────┤<br/>│  L5  Prompt Ops（版本管理 / 灰度 / A-B / 回滚 / 效果归因）                │<br/>├──────────────────────────────────────────────────────────────────────┤<br/>│  L4  在线评测 Online-Eval（LLM-as-Judge 实时打分 / 影子评测 / 规则校验）  │<br/>├──────────────────────────────────────────────────────────────────────┤<br/>│  L3  异常拦截（幻觉·偏置·越权·Prompt注入 实时检测 + 降级）                │<br/>├──────────────────────────────────────────────────────────────────────┤<br/>│  L2  Tracing（Span 模型 / 跨 Agent-Tool-LLM 透传 / 结构化解析 / Token计量）│<br/>├──────────────────────────────────────────────────────────────────────┤<br/>│  L1  接入层（OpenAI 兼容网关 / SDK 无侵入埋点 / W3C TraceContext 注入）    │<br/>└──────────────────────────────────────────────────────────────────────┘<br/>         存储：列式 Span Store（ClickHouse）+ 倒排索引（ES）+ 对象存原始日志</code>
```

### 亮点 1：全链路 Tracing —— 把一次"用户提问"拆成可观测的树

传统 APM 的 Span 是"一次 HTTP 调用"，而 LLM 应用的一次请求内部是 **Agent→Tool→LLM→Tool→LLM** 的树状多跳调用，且伴随 **流式输出、异步任务、子 Agent 跨进程**。我们定义了统一 Span 模型：

```
<code>Span {<br/>  trace_id          // 一次用户请求全局唯一<br/>  span_id / parent_id<br/>  kind: LLM | TOOL | AGENT | RETRIEVAL | CHAIN | EMBEDDING<br/>  model / prompt_hash / tool_name<br/>  input_tokens / output_tokens / cost_usd<br/>  latency_ms / ttft_ms / tpot_ms(每token延迟)<br/>  status / error_type<br/>  attributes: { user_id, scene, prompt_version, judge_score, ... }<br/>}</code>
```

关键设计：**SDK 无侵入埋点**——业务方只需把 `openai.ChatCompletion` 换成我们的 `llmobserver.ChatCompletion`，其余（Trace 注入、Token 计量、Judge 评测）全自动。

### 亮点 2：生产环境在线评测（Online-Eval）—— 让"质量"变成实时指标

离线评测（第28期）回答"发版前好不好"，在线评测回答"线上现在还行不行"。我们做了三件事：

- **采样评测**：对 1%~5% 流量异步调用 LLM-as-Judge 打质量分（相关性/有用性/安全性/幻觉），不打分的不影响主链路延迟。
- **影子评测（Shadow）**：新 Prompt/新模型对 100% 流量"双跑"但不返回给用户，只对比 Judge 分与成本，作为灰度放行依据。
- **规则校验**：正则/分类器做确定性强约束（如"必须含引用"、"禁止泄露 PII"、"输出长度∈[50,800]"）。

### 亮点 3：Prompt 全生命周期管理（Prompt Ops）

Prompt 是大模型应用的"代码"，但天然难版本化。我们提供：

- **版本化 + Git 式 diff**：每次 Prompt 变更留痕、可对比、可回滚。
- **灰度发布**：按 user_id 一致性哈希或 scene 染色分流（如 5% 流量试新 Prompt）。
- **A-B 实验**：同一流量复制多份分别走不同 Prompt，Judge 分与业务指标自动归因。
- **自动回滚**：当灰度 Prompt 的线上核心指标（质量分 / 满意度 / 转化率）相对 baseline 跌超阈值，自动切回。

### 亮点 4：成本-质量-延迟三维看板 + 智能告警

不止"QPS/延迟"传统指标，新增 LLM 专属维度：

- **成本**：按模型/场景/用户聚合 `cost_usd = (in_tok×price_in + out_tok×price_out) / 1000`，下钻到"哪个 Agent 最烧钱"。
- **质量**：在线 Judge 分、幻觉率、拒答率、人工投诉率。
- **延迟**：TTFT（首 token）、TPOT（每 token）、E2E。
- **智能告警**：基于历史同环比 + 统计过程控制（SPC，3σ）触发，避免固定阈值在流量波峰误报。

### 亮点 5：数据回流与标注飞轮

线上 Trace（含 Judge 分、用户反馈 👍/👎、人工修正）自动回流到训练/评测库，成为第36期（微调）和第28期（评测集）的"燃料"，形成 **线上问题 → 数据 → 再训练/再评测 → 新 Prompt/新模型 → 灰度 → 线上** 的闭环。

### 亮点 6：异常实时拦截（Guardrail-in-Ops）

在第25期"模型层安全对齐"之上，在平台层补一道 **运行时 Guardrail**：对输入输出做低延迟（<8ms）的幻觉/偏置/越权/Prompt 注入检测，命中则降级（兜底话术 / 转人工），并把事件作为高优 Trace 上报。

---

---

### 难点 1：分布式链路透传 —— 跨异步/多线程/子 Agent 不断链

**问题**：Agent 调 Tool，Tool 内部又起线程/协程去查 DB、再回调 LLM；或子 Agent 跨进程/跨服务。传统 `threading.local()` 在异步切换、线程池复用、跨进程 RPC 时 **Trace Context 丢失**，Span 树断裂。

**方案**：采用 **W3C Trace Context**（`traceparent` 头：`version-trace_id-span_id-flags`），并实现一个 **Context 载体** 在以下边界显式传递：

1. 同步调用：透传 `traceparent` HTTP 头；
1. 线程池/协程：把 `Context` 作为闭包变量捕获进任务；
1. 消息队列：把 `traceparent` 塞进消息头；
1. 跨进程 RPC：注入到请求 metadata。

```
<code>import contextvars, uuid, threading<br/><br/>_ctx = contextvars.ContextVar("llmobs_ctx")  # 隔离于线程/协程<br/><br/>class SpanContext:<br/>    def __init__(self, trace_id=None, parent_id=None):<br/>        self.trace_id = trace_id or uuid.uuid4().hex<br/>        self.span_id = uuid.uuid4().hex<br/>        self.parent_id = parent_id<br/><br/>def current_ctx():<br/>    return _ctx.get(None)<br/><br/>def start_span(name, kind):<br/>    parent = current_ctx()<br/>    ctx = SpanContext(trace_id=parent.trace_id if parent else None,<br/>                      parent_id=parent.span_id if parent else None)<br/>    token = _ctx.set(ctx)            # 绑定到当前执行上下文<br/>    span = Span(name, kind, ctx)<br/>    return span, token<br/><br/># 异步/线程边界：必须显式把 ctx 带过去，否则断链<br/>def submit_task(fn):<br/>    parent_ctx = current_ctx()<br/>    def wrapped():<br/>        _ctx.set(parent_ctx)         # 在子执行单元恢复 context<br/>        return fn()<br/>    return thread_pool.submit(wrapped)<br/><br/># 跨进程：序列化为 traceparent<br/>def to_traceparent(ctx):<br/>    return f"00-{ctx.trace_id}-{ctx.span_id}-01"<br/><br/>def from_traceparent(hdr):<br/>    _, tid, sid, _ = hdr.split("-")<br/>    c = SpanContext(trace_id=tid, parent_id=sid)<br/>    return c</code>
```

**坑**：`contextvars` 在 `asyncio` 下天然随 Task 隔离（✅），但在 `concurrent.futures.ThreadPoolExecutor` 里 **不会** 自动传播（❌），必须如上手动 `set`。否则子线程 Span 的 `parent_id` 为 None，树断裂。

### 难点 2：流式响应 Token 精算 —— SSE 不能只数"字符"

**问题**：LLM 用 SSE 流式返回，业务侧拿到的只是一串 `data: {...}` 增量。要精确计量 `input_tokens/output_tokens`、TTFT、TPOT，必须：

1. 在请求侧用 tokenizer 数 input（但业务传的是 messages，需重建后数）；
1. 在响应侧从首个 chunk 算 TTFT，从相邻 chunk 时间戳算 TPOT；
1. 把 usage（部分厂商只在 `finish_reason` 的最后一个 chunk 给 `usage`）对齐到 Span。

```
<code>import time, tiktoken<br/><br/>enc = tiktoken.get_encoding("cl100k_base")<br/><br/>class StreamMeter:<br/>    def __init__(self, messages):<br/>        self.input_tokens = sum(len(enc.encode(m["content"])) for m in messages)<br/>        self.first_chunk_ts = None<br/>        self.last_chunk_ts = None<br/>        self.output_tokens = 0<br/>        self.ttft = None<br/><br/>    def on_chunk(self, chunk):<br/>        now = time.perf_counter()<br/>        if self.first_chunk_ts is None:<br/>            self.first_chunk_ts = now<br/>            self.ttft = now - self.start_ts<br/>        # chunk.choices[0].delta.content 可能是 None（仅 usage）<br/>        delta = chunk.choices[0].delta.content or ""<br/>        if delta:<br/>            self.output_tokens += max(1, len(enc.encode(delta)))<br/>            if self.last_chunk_ts:<br/>                self.tpot = (now - self.last_chunk_ts) * 1000  # ms/token<br/>            self.last_chunk_ts = now<br/>        if chunk.usage:                 # 少数厂商流式也带 usage<br/>            self.input_tokens = chunk.usage.prompt_tokens<br/>            self.output_tokens = chunk.usage.completion_tokens<br/><br/>    def cost_usd(self, p_in, p_out):<br/>        return (self.input_tokens * p_in + self.output_tokens * p_out) / 1000.0</code>
```

**坑**：`len(text)`（字符数）≠ token 数；中文 1 字 ≈ 12 token，英文 1 token ≈ 4 字符。用字符估算成本会 **系统性低估中文场景 23 倍**。必须用 tokenizer 或厂商返回的 `usage`。

### 难点 3：在线评测的低延迟与去偏 —— Judge 不能拖垮主链路

**问题**：每次请求都调一次 LLM-as-Judge，延迟 +1~3s、成本翻倍、且 Judge 自身有 Position/Length/Self-Preference 偏差（第28期详述）。

**方案**：

- **异步 + 采样**：Judge 走独立队列，仅对采样流量（默认 3%）评测，结果写回 Span 的 `judge_score`，**绝不阻塞主链路**。
- **偏差校正**：对 Length/Position bias 做归一化。Self-Preference 通过对抗采样（同时评"被评输出 vs 参考输出"各一次取对称分）抑制。
- **一致性**：同一条样本用 Temperature=0 固定 seed，保证 Judge 可复现。

```
<code>def judge_async(span, sample_rate=0.03):<br/>    if random() &gt; sample_rate:<br/>        return                       # 采样：绝大多数不评，零成本<br/>    prompt = f"""你是严格的质量评审。从[相关性,有用性,安全性,幻觉]四维度给回答打分(1-5)，<br/>仅输出JSON: {{"score":&lt;float&gt;, "hallucination":&lt;bool&gt;, "reason":&lt;str&gt;}}<br/>[问题]{span.question}<br/>[回答]{span.answer}"""<br/>    # 异步、temperature=0、独立 budget，不进主链路<br/>    result = judge_llm(prompt, temperature=0, timeout=3.0)<br/>    span.judge_score = result["score"]<br/>    span.hallucination = result["hallucination"]<br/><br/># 长度偏差校正：对过短/过长输出做线性惩罚后归一<br/>def debias(score, length, lo=50, hi=800):<br/>    if length &lt; lo:   return score * (0.6 + 0.4 * length / lo)<br/>    if length &gt; hi:   return score * (1.0 - 0.2 * min(1, (length - hi) / hi))<br/>    return score</code>
```

**量化**：采样 3% 评测，使在线评测成本仅为"全量评测"的 3%，却能覆盖 100% 的 **分布**；异常检测靠"离群 + 同比骤降"而非单条精度。

### 难点 4：海量 Span 的存储与查询 —— 10 亿 Span/天怎么存

**问题**：10 亿 Span/天 ≈ 11500 Span/s，单 Span 含嵌套 JSON，`SELECT * WHERE trace_id=?` 要能秒级拉出一棵树。

**方案（分层存储）**：

- **热数据（近 7 天）**：ClickHouse 列式存储，按 `(date, trace_id)` 分区 + 物化视图预聚合（按 scene/model 的 cost、延迟、质量分），看板查询走预聚合，毫秒级。
- **温数据（7~90 天）**：ES 倒排索引，支持 `attributes.user_id` / `prompt_version` 全文检索与下钻。
- **冷数据（>90 天）**：原始 JSON 压缩落对象存储，仅审计/复盘时取。

```
<code>-- ClickHouse 物化视图：按场景预聚合，看板直接读它<br/>CREATE MATERIALIZED VIEW span_hourly<br/>ENGINE = SummingMergeTree<br/>PARTITION BY toYYYYMMDD(ts)<br/>ORDER BY (scene, model, toStartOfHour(ts)) AS<br/>SELECT scene, model, toStartOfHour(ts) AS hour,<br/>       count() AS cnt,<br/>       sum(input_tokens) AS in_tok, sum(output_tokens) AS out_tok,<br/>       sum(cost_usd) AS cost,<br/>       quantile(0.99)(latency_ms) AS p99_lat,<br/>       avg(judge_score) AS avg_quality<br/>FROM spans<br/>GROUP BY scene, model, hour;</code>
```

### 难点 5：Prompt 灰度与回滚的流量治理 —— 既分流又不串味

**问题**：新 Prompt 不能影响全部用户；灰度期间要能"同一条请求同时跑新旧两版做 A-B"；一旦新版本核心指标劣化要 **无损回滚**。

**方案**：

- **一致性哈希染色**：`bucket = hash(user_id) % 100`，`bucket < 5` 走新 Prompt，保证同一用户始终命中同一版本（体验一致）。
- **影子复制（A-B）：对灰度流量，后台额外用旧 Prompt 跑一份（shadow），Judge 对比分差，作为是否全量的依据，用户无感**。
- **自动回滚**：滑动窗口统计灰度组 vs 基线组的 `quality_score / satisfaction / cost`，若 `Δquality < -threshold` 持续 N 分钟，触发回滚（配置中心下发 `prompt_version=baseline`，秒级生效）。

```
<code>def route_prompt(user_id, new_version, baseline_version, roll_pct=5):<br/>    bucket = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100<br/>    if bucket &lt; roll_pct:<br/>        if shadow_enabled(user_id):          # 同时跑 baseline 做 A-B<br/>            submit_shadow(user_id, baseline_version)<br/>        return new_version<br/>    return baseline_version<br/><br/># 自动回滚判定（滑动窗口）<br/>def should_rollback(gray, base, thr=-0.05, mins=10):<br/>    delta = mean(gray.quality[-mins:]) - mean(base.quality[-mins:])<br/>    return delta &lt; thr                        # 质量跌超 5% 持续 10 分钟</code>
```

### 难点 6：线上质量实时监控与根因定位 —— 分数跌了怎么 30 分钟定责

**问题**：某天"用户满意度"从 4.2 跌到 3.1，但 QPS/延迟都正常。传统 APM 看不到"质量"，得靠人工刷样本。

**方案**：

- **质量指标化**：把在线 Judge 分、👎率、幻觉率、拒答率做成时间序列；
- **异常检测**：对质量序列做 STL 分解（趋势/周期/残差）+ 3σ 判异，结合同环比；
- **根因下钻**：质量跌 → 按 `model / scene / prompt_version / tool / 时间窗` 切片，定位是"某模型退化"还是"某 Prompt 改坏"还是"某工具超时导致降级"。

```
<code>质量跌 → 切片下钻：<br/>  by model      : 仅 model=B 跌 → 模型侧问题（联系厂商/切备用模型）<br/>  by scene      : 仅 "售后" 场景跌 → 该场景 Prompt/知识库问题<br/>  by prompt_ver : 仅 v3 跌 → Prompt 改坏，触发回滚<br/>  by tool       : 仅 retriever 超时↑ → 工具故障导致降级</code>
```

---

---

### Q1：LLMOps 可观测性 与 传统 APM（如 SkyWalking/Jaeger）的本质区别？

**答（深）**：

1. **Span 语义不同**：APM 的 Span 是"一次 RPC/SQL"；LLMOps 的 Span 多了 `LLM/TOOL/AGENT/RETRIEVAL` 等种类，并携带 **token 数、cost、prompt_version、judge_score** 等 LLM 专属属性。APM 无法表达"这一次调用烧了多少钱、质量几分"。
1. **质量维度是新增的一轴**：APM 关心可用性与延迟，LLMOps 必须关心 **输出质量**（幻觉/相关性/安全），而这需要 LLM-as-Judge 或规则校验，是 APM 没有的能力。
1. **成本可观测性**：token 级成本核算是 LLM 独有，传统 APM 没有"按模型/场景聚合美元"的诉求。
1. **Prompt/Trace 耦合**：Prompt 版本是 LLM 应用的"代码版本"，质量问题常与 Prompt 版本强相关，需把 Prompt Ops 与 Trace 打通做归因——这是 APM 的"代码版本"概念在 LLM 领域的特化。
1. **非确定性**：同输入可能不同输出，导致评测与回放必须用采样+Judge 而非精确断言。

**一句话**：APM 解决"系统通不通、快不快"，LLMOps 额外解决"输出对不对、贵不贵、改了 Prompt 会不会更差"。

### Q2：生产环境怎么做低成本的在线评测（避免每月烧一大笔钱）？

**答（深）**：

- **采样评测**：仅对 1%5% 流量调 Judge，成本线性降到 1/201/100，但统计上足以覆盖分布异常。
- **影子评测替代全量**：新版本对比只在灰度/影子流量做，不发全量。
- **规则校验优先**：能用正则/分类器/长度约束判定的（如"含引用""无 PII"），**不调 LLM**，把昂贵的 LLM-Judge 留给真正需要语义判断的样本。
- **Judge 模型选小模型**：评审用 7B~14B 小模型 + 严格 rubric，成本是大模型的 1/10，相关性判断上已够用（研究显示小 Judge 与大 Judge 一致性 >0.85）。
- **缓存与去重**：相同 (question_hash, answer_hash) 不重复评；历史样本复用。
- **异步 + 批处理**：Judge 请求攒批（batch）调 API，摊薄固定开销，且绝不进主链路。  
**量化**：以上组合使在线评测成本从"全量×大模型"降至约 **3%~8%**，同时质量监控覆盖率达 100%。

### Q3：Agent 多跳调用下，Trace 如何保证上下文连续（不断链）？

**答（深）**：核心是 **Trace Context 在执行上下文切换边界显式传播**（见难点1）：

- 同步 RPC：注入 `traceparent` 头（W3C 标准）；
- 异步/线程池：`contextvars` 在 asyncio 下自动隔离，但在 `ThreadPoolExecutor` 需手动 `_ctx.set(parent_ctx)`；
- 消息队列/定时任务：把 traceparent 塞进消息头；
- 跨进程/跨服务：注入到 gRPC metadata 或 HTTP 头，下游 `from_traceparent` 恢复。  
**断链根因**：① 线程池未传播 context；② 子 Agent 通过消息队列异步触发但未带 traceparent；③ `parent_id` 在 retry/重试时复用了新 span。  
**验证**：故意制造跨线程+跨进程调用，断言 `SELECT span WHERE trace_id=X` 能还原完整树。

### Q4：如何防止 LLM-as-Judge 自身引入偏差、沦为"摆设"？

**答（深）**（详见第28期，这里给工程落点）：

- **Position bias**：双次序评分取平均（A vs B 与 B vs A 各一次）。
- **Length bias**：对过长/过短输出做长度惩罚校正（见难点3 `debias`）。
- **Self-Preference**：用 **非被评模型** 做 Judge（避免"自家模型偏袒自家输出"），或对抗采样。
- **Rubric 锁定**：评分维度与档位固定为 JSON schema，temperature=0 保证可复现。
- **人体校准**：每周抽 200 条人工标注，算 Judge 与人工的 Cohen's κ，**κ<0.6 视为失效** 并复盘 rubric。
- **离群而非绝对**：线上用 Judge 做"趋势/异常"检测，不拿单条绝对分当真理。

### Q5：Prompt 版本灰度如何实现无损回滚与效果归因？

**答（深）**（见难点5）：

- **无损回滚**：Prompt 版本由配置中心下发，运行时读 `prompt_version`；回滚=改配置值，秒级生效，**无需发版**。
- **一致性体验**：按 `hash(user_id)%100` 染色，同一用户全程命中同一版本，避免"同一人时好时坏"的割裂感。
- **效果归因**：灰度组与基线组用 **相同 Judge 口径 + 相同业务指标**（满意度/转化率）对比；A-B 影子模式让新旧同输入同评，消除输入分布差异带来的归因噪声。
- **自动触发**：滑动窗口 `Δquality < -5%` 持续 10 分钟自动回滚，把"人发现→人回滚"的小时级压缩到分钟级。

### Q6：LLM 应用的成本治理（FinOps）有哪些工程抓手？

**答（深）**：

1. **量化可见**：token 级成本下钻到 模型/场景/用户/Agent，先看清"谁在烧钱"（亮点4）。
1. **模型分级路由**：简单任务用小模型（如 7B/14B 本地），复杂任务才上大模型；用路由器+置信度阈值切换，**成本可降 40%~70%**。
1. **Prompt 压缩**：精简 system prompt、去冗余 few-shot，输入 token 直接下降（见第26期上下文压缩）。
1. **KV Cache 复用**：相同前缀（如 system prompt、固定工具描述）走 Prefix Caching（第27期），重复请求不计费重算。
1. **Speculative Decoding / 量化**：推理侧降本（第22、24期）。
1. **预算护栏**：按用户/场景设日预算上限，超阈值降级到小模型或兜底，防"一个用户刷爆账单"。
1. **超时与重试上限**：无限流/无上限重试会在故障期产生雪崩式费用。

---

---

### 🎯 模拟题 1：从零设计企业级 LLM 应用可观测平台（10 亿调用/天）

**场景**：你是平台负责人，公司 20 个业务线、每天 10 亿次 LLM 调用，当前"出问题只能靠用户投诉"，老板要你建一套能看清成本/质量/延迟、能灰度、能回滚的可观测平台。请设计架构。

**参考答案要点**：

1. **分层架构**（对齐本期 L1~L6）：接入层（OpenAI 兼容网关 + 无侵入 SDK）→ Tracing（Span 模型 + W3C TraceContext 跨异步/跨进程透传）→ Guardrail 拦截 → Online-Eval（采样 Judge + 规则）→ Prompt Ops（版本/灰度/回滚）→ 看板/告警/飞轮。
1. **Trace 透传机制**：`contextvars` + 线程池手动传播 + 消息队列带 `traceparent`，保证 Agent 多跳不断链（难点1）。
1. **存储分层**：热（ClickHouse 列式 + 物化视图预聚合，看板毫秒级）、温（ES 倒排检索）、冷（对象存储）。1 亿 Span/天用 ClickHouse 单表分区即可扛（难点4）。
1. **成本精算**：token 级计量（**必须 tokenizer 而非字符数**，中文字符估算低估 2~3 倍），下钻到 model/scene/user（难点2）。
1. **在线评测降本**：采样 3% + 规则优先 + 小 Judge 模型 + 异步批处理，成本压到全量的 3%~8%，覆盖率 100%（难点3、Q2）。
1. **Prompt 灰度+自动回滚**：一致性哈希染色 + 影子 A-B + 滑动窗口 `Δquality<-5%` 自动回滚（难点5）。
1. **智能告警**：质量序列 STL 分解 + 3σ + 同环比，按 model/scene/prompt_version/tool 切片根因下钻（难点6）。
1. **数据飞轮**：线上 Trace + 反馈回流训练/评测库，闭环（亮点5）。  
**加分项**：提到 SLA 分级（核心链路同步 Judge、非核心异步）、多租户隔离、隐私合规（PII 脱敏后再存储/评测）、与推理服务（第27期）的 Prefix Cache 联动降本。

---

---

**场景**：今早 9 点，监控发现全站"Judge 平均分"从 4.2 跌到 2.9，但 QPS、延迟、错误率都正常。你是 oncall，怎么处理？

**参考答案要点**：

1. **先止血（<5 分钟）**：确认是否某 Prompt/模型版本刚发布 → 若是，立即回滚到上一稳定版本（配置中心改 `prompt_version`，秒级生效；见难点5）。同时开"质量降级"：对低分输出自动转人工/兜底，防用户持续受损。
1. **切片下钻（5~15 分钟）**：按 `model / scene / prompt_version / tool / 时间窗` 切片质量序列（难点6 的树）：仅 model=B 跌 → 模型侧退化（厂商更新/限流降级）→ 切备用模型；
1. 仅某 scene 跌 → 该场景知识库/工具故障（如 retriever 超时导致空检索）→ 查工具 SLA；
1. 仅 prompt_v3 跌 → Prompt 改坏 → 回滚；
1. 全量跌但模型/scene 都正常 → 可能是 **Judge 自身故障/版本变了**（Judge 模型被换/ rubric 改）→ 校验 Judge 管线。
1. **验证假设（15~25 分钟）**：取跌前/跌后同批样本，人工抽 20 条确认根因；查对应组件的变更记录（发版单/配置单）。
1. **根因修复 + 防复发（25~30 分钟+）**：修复后灰度验证；补"质量异动自动回滚 + 变更关联告警"（发版即比对质量基线），把"人发现"变"系统自动拦"。  
**加分项**：提到"Judge 偏差导致假跌"的可能性（如 Judge 模型升级后打分变严）——需要对比"人工标注"而非只看 Judge 绝对值；以及"质量指标要做同环比基线，不能拍阈值"。

---

---

**场景**：算法同学每周改几次 Prompt，每次发版都怕"改坏"。请你设计一套系统：新 Prompt 先小流量试，有问题自动回滚，且能说清"到底有没有变好"。

**参考答案要点**：

1. **版本化底座**：Prompt 入库即 `prompt_version`，每次变更留 diff、可回滚（亮点3）。
1. **一致性灰度**：`bucket=hash(user_id)%100`，`bucket<5` 走新版本，保证用户体验连续（难点5）。
1. **影子 A-B**：对灰度流量后台用 baseline 再跑一份，Judge 同口径对比，**消除输入分布差异带来的归因噪声**。
1. **多指标评估**：不只看 Judge 分，还要看 **业务指标**（满意度 👍/👎、转化率、任务完成率）与 **成本**（新 Prompt 是否更费 token）。
1. **自动回滚**：滑动窗口统计 `Δquality` 与 `Δcost`，`Δquality  +20%` 且无质量收益）持续 10 分钟 → 配置中心下发回滚，秒级生效，**无需发版**。
1. **放行标准**：灰度组在质量不劣化（Δquality ≥ 0）、成本可控前提下，跑满 24h/覆盖足够样本 → 自动全量。
1. **可解释报告**：每次变更产出"质量 Δ / 成本 Δ / 典型优劣样本"报告，供算法同学决策。  
**加分项**：提到"辛普森悖论"——整体质量涨但某子场景跌，需 **分场景** 评估而非只看全局均值；以及"回滚后要保留现场 Trace 供复盘"。

---

---

```
<code>LLMOps 六层：接入埋点 → Tracing → Guardrail → Online-Eval → Prompt-Ops → 看板飞轮<br/>Trace 不断链：W3C traceparent + contextvars + 线程池手动 set + MQ 带头<br/>Token 精算：必须用 tokenizer 数，字符数中文低估 2~3 倍<br/>在线评测降本：采样3% + 规则优先 + 小Judge + 异步批；成本压到 3%~8%，覆盖100%<br/>存储分层：热 ClickHouse(物化视图) / 温 ES / 冷 对象存储<br/>Prompt 灰度：hash(user)%100 染色 + 影子A-B + Δquality&lt;-5%自动回滚<br/>质量异常定位：STL分解+3σ → 按 model/scene/prompt_ver/tool 切片下钻<br/>FinOps 抓手：模型分级路由 + Prompt压缩 + Prefix Cache + 预算护栏 + 量化<br/>Judge 去偏：Position双序 + Length惩罚 + 非自评模型 + κ&gt;0.6校准<br/>LLMOps vs APM：多 Span种类(token/cost/judge) + 质量轴 + Prompt版本归因 + 非确定性</code>
```

## 六、量化成果（项目复盘口径）

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