# 大模型面试复习 - 第62期（GPU 算力调度与推理集群编排平台 ComputeOrch · 工程化深度实战版）

**生成时间**：2026-08-11 09:00  
**主线项目**：ComputeOrch（万台 GPU 推理集群调度与编排平台）  
**复习定位**：在「第27期推理服务（vLLM 单实例）」「第51期算子级优化」「第43期端侧」「第60期国产算力适配」基础上，下沉到**集群编排层**——单卡/单机之上、数十个模型共享万台 GPU 的调度、装箱、弹性、混部与成本控制。这是 Agent Harness / FuncHub / 各模型后端共同踩在脚下的"地基"。

---

---

### 1.1 全项目核心亮点速览矩阵（呼应需求 #1）

> 大模型相关项目的核心亮点，Agent Harness 为旗舰示例（用户点名），其余按"量化成果 + 标志性技术"横向对照，便于面试开口即报战绩。

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
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |
| td | td | td | td | td |

### 1.2 ComputeOrch 定位与量化成果

ComputeOrch 管理**万台级 GPU、数十个模型、日均千亿次推理调用**的集群。它不是 K8s 默认的"按卡数调度"（那只会把整卡分给 Pod），而是理解**显存拓扑、碎片、模型亲和、QoS 等级、碎片回收**的智能编排层。

**量化成果（生产数据）**：

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

### 1.3 六层架构

```
<code>┌──────────────────────────────────────────────────────────┐<br/>│  L6 计费与治理层  按租户/模型聚合 token·卡时·电价·分账       │<br/>├──────────────────────────────────────────────────────────┤<br/>│  L5 观测层      GPU 利用率·碎片率·排队·干扰检测·告警       │<br/>├──────────────────────────────────────────────────────────┤<br/>│  L4 弹性层      HPA·Spot 抢占安全回收·按优先级迁移         │<br/>├──────────────────────────────────────────────────────────┤<br/>│  L3 隔离层      MIG/MPS 切分·QoS 等级·反亲和放置           │<br/>├──────────────────────────────────────────────────────────┤<br/>│  L2 放置层      碎片感知装箱·分离式 P/D 配对·拓扑感知      │<br/>├──────────────────────────────────────────────────────────┤<br/>│  L1 资源感知层  实时采集显存·算力·NVLink·碎片·健康度      │<br/>└──────────────────────────────────────────────────────────┘<br/>         ↕ 向上：Agent Harness / FuncHub / ModelRouter 统一申请算力</code>
```

---

---

### 2.1 GPU 碎片与装箱（Fragmentation-aware Bin Packing）

**现象**：裸 K8s 按"整卡"分配，13B 模型实际只占 0.4 卡显存，却独占一整张 A100，剩余 60% 显存无法被别的模型用——集群"显存满了但利用率低"，碎片率高达 22%。

**根因**：调度器不理解模型的真实显存需求（含 KV Cache 弹性部分），只能整卡分配。

**解决方案**：把 GPU 切成"显存块 + 算力配额"二维资源，用碎片感知的 First-Fit-Decreasing（FFD）装箱，并定义碎片率指标。

```
<code>import heapq<br/><br/>@dataclass<br/>class GPU:<br/>    id: str<br/>    total_mem: int          # GB<br/>    free_mem: int<br/>    # 用"最大连续空闲块"评估碎片<br/>    def max_hole(self) -&gt; int:<br/>        return self.free_mem   # 简化：1D bin 不分碎片块<br/><br/>def frag_ratio(gpus: List[GPU]) -&gt; float:<br/>    # 碎片率 = 1 - 最大连续空闲块 / 总空闲<br/>    total_free = sum(g.free_mem for g in gpus)<br/>    max_hole  = max(g.max_hole() for g in gpus)<br/>    return 1 - max_hole / total_free if total_free else 0.0<br/><br/>def place_ffd(models: List[Tuple[str,int]], gpus: List[GPU]):<br/>    # 大需求先放（降碎片化）<br/>    for name, need in sorted(models, key=lambda x: -x[1]):<br/>        # First-Fit：第一个放得下的 GPU<br/>        for g in sorted(gpus, key=lambda g: -g.free_mem):<br/>            if g.free_mem &gt;= need:<br/>                g.free_mem -= need<br/>                yield (name, g.id)<br/>                break<br/>        else:<br/>            raise RuntimeError(f"{name} 无整块显存可放，需碎片整理/迁移")</code>
```

**面试要点**：碎片化不是"显存不够"，而是"连续空闲块不够大"。FFD 把大块需求先放，可显著降低碎片；配合 MIG 物理切分把一卡变 7 个硬隔离实例，碎片率从 22%→3%。

### 2.2 连续批处理长尾与迭代级抢占

**现象**：Static Batching 等最长请求，短请求被"拖死"；突发大请求占满显存，后续请求无限排队。

**根因**：批处理粒度是"序列级"，无法在生成中途插入/驱逐。

**解决方案**：Chunked Prefill（prefill 切成 chunk 与 decode 交织）+ Iteration-level 调度（每生成一个 token 重新组批）+ 优先级抢占（低优请求 checkpoint 到 CPU 让位）。

```
<code>class IterationScheduler:<br/>    def __init__(self): self.running, self.waiting, self.preempted = [], [], []<br/>    def step(self):<br/>        # 1) 优先把 waiting 中能塞进剩余显存的加进 running（连续批）<br/>        while self.waiting and self._has_room():<br/>            self.running.append(self.waiting.pop(0))<br/>        # 2) 优先级抢占：超出显存预算时，驱逐最低优先级<br/>        while not self._has_room() and self.running:<br/>            victim = min(self.running, key=lambda r: r.priority)<br/>            self.running.remove(victim)<br/>            victim.checkpoint_to_cpu()        # KV 落 CPU，保活<br/>            self.preempted.append(victim)<br/>    def _has_room(self) -&gt; bool:<br/>        return self._kv_used() &lt; self.kv_budget</code>
```

**面试要点**：连续批处理把吞吐×3、P99 -71%（呼应第27期），但引入"长尾"——要配合迭代级抢占 + 抢占优先级，否则低优流量饿死。

### 2.3 分离式 Prefill / Decode（Disaggregated P/D）

**现象**：同一批里 prefill（算力密集）和 decode（带宽密集）混合，互相拖累——prefill 占满算力让 decode 停摆，或 decode 占满带宽让 prefill 慢。

**根因**：prefill 与 decode 的算力/带宽画像相反，混部导致 GPU 永远"半忙"。

**解决方案**：P 实例（高算力卡）与 D 实例（高带宽卡）物理分离，KV Cache 走 RDMA 从 P 传到 D。

```
<code># 最优切分：让 P、D 两端时延对齐<br/># T_total ≈ T_prefill / N_p + T_decode / N_d  → 求 N_p : N_d 使两端均衡<br/>def optimal_pd_split(S, L, model, p_speed, d_speed):<br/>    # S: 总请求吞吐目标; 简化按比例分配实例数<br/>    # prefill 耗时 ∝ S·L / p_speed, decode 耗时 ∝ S / d_speed<br/>    np = int(round(S * L / p_speed / (S*L/p_speed + S/d_speed) * (p_speed+d_speed)))<br/>    nd = max(1, int(round(S / d_speed / (S*L/p_speed + S/d_speed) * (p_speed+d_speed))))<br/>    return np, nd   # 经验：长上下文(np↑)、短上下文(nd↑)</code>
```

**面试要点**：分离式 P/D 在长上下文场景把有效吞吐 +30~50%，但引入"KV 跨机传输"成本——短请求（<2K token）不建议拆，传输开销抵消收益。这是典型的"按负载画像决策"考点。

### 2.4 MIG / MPS 切分与 QoS 隔离

**现象**：多模型混部时，一个模型吃满算力，邻居模型时延抖动（noisy neighbor）。

**根因**：默认 MPS（多进程服务）共享 SM 但无硬隔离，某进程狂占 SM 就拖垮邻居。

**解决方案**：硬隔离用 **MIG**（A100/H100 把 1 卡物理切成 7 个实例，显存/算力硬切）；软隔离用 **MPS**（共享但按 client 限算力配额）。按 QoS 等级选：

```
<code>def choose_partition(qos, model_mem, model_flops):<br/>    if qos == "guaranteed":                 # 硬 SLA → MIG<br/>        return mig_alloc(slice_for(model_flops))   # 1/7~7/7 实例<br/>    else:                                   # 弹性/best-effort → MPS + 算力配额<br/>        return mps_alloc(cuda_limit=model_flops)   # 限制 SM 占用上限</code>
```

**面试要点**：MIG 隔离强但粒度粗（最小 1/7 卡）、切换贵；MPS 粒度细但会互相干扰。结论：**付费 SLA 走 MIG，免费/弹性走 MPS**。

### 2.5 弹性伸缩与 Spot 回收安全

**现象**：Spot（抢占式）GPU 便宜 70%，但随时被云厂商回收；直接杀 Pod 会丢在途请求。

**根因**：默认 HPA 只管"扩容"，回收时 SIGKILL 不做优雅排空。

**解决方案**：HPA 扩 + 优雅排空（drain）：收到回收信号后，停止接新请求、将在途请求迁移/重放、KV 落盘，再退出。

```
<code>def on_preempt_signal(scheduler):<br/>    scheduler.drain = True                  # 不再接新请求<br/>    for req in scheduler.running:<br/>        if req.checkpointable:<br/>            req.migrate_to_peer()           # 在途请求迁到邻居节点<br/>        else:<br/>            req.requeue_with_kv()           # 带 KV 重排队首，避免重算<br/>    while scheduler.running:<br/>        time.sleep(0.1)                     # 等清空<br/>    sys.exit(0)                             # 安全退出</code>
```

**面试要点**：Spot 省钱的前提是"请求可安全中断"——靠 KV checkpoint + 重放 + 迁移，把丢失率从 0.8% 压到 <0.01%（呼应量化成果）。

### 2.6 多模型混部干扰检测

**现象**：两个模型放同一卡（MPS），互相抢带宽，时延双双劣化却无明显报错。

**根因**：干扰是"软"的——SM/带宽争用，监控只看到"慢"，看不到"为什么慢"。

**解决方案**：放置反亲和（同类画像模型错开卡）+ 在线干扰检测（同卡多模型时延相关性 > 阈值则自动重排）。

```
<code>def interference_detect(pairs: List[Tuple[str,str]], lat:<br/>                         Dict[str,float], base: Dict[str,float]) -&gt; List[str]:<br/>    bad = []<br/>    for a, b in pairs:<br/>        # 同卡且两者时延都偏离基线 → 干扰<br/>        if lat[a] &gt; 1.3*base[a] and lat[b] &gt; 1.3*base[b]:<br/>            bad.append((a, b))<br/>    return bad   # 触发反亲和重排</code>
```

**面试要点**：混部提利用率但引入干扰——靠"画像感知放置 + 在线检测 + 自动重排"闭环，把干扰导致的时延劣化控制在 5% 内。

---

---

### Q1：ComputeOrch 和 K8s 默认调度（device-plugin）本质区别？

**答**：K8s 默认 `nvidia-device-plugin` 只按"整数卡"分配，不懂模型真实显存、拓扑、碎片。ComputeOrch 把 GPU 拆成"显存块 + 算力配额"二维资源，理解 KV Cache 弹性、NVLink 亲和、碎片率，做碎片感知装箱 + MIG/MPS 切分 + 分离式 P/D。一句话：**K8s 管"几张卡"，ComputeOrch 管"每张卡怎么榨干"。**

### Q2：GPU 碎片率怎么量化、怎么治理？

**答**：`碎片率 = 1 - 最大连续空闲块 / 总空闲`。治理三板斧：① FFD 大块先放（2.1）；② MIG 物理切分把 1 卡变 7 个硬实例，碎片天然消失；③ 碎片整理（低峰期把小模型迁移合并，腾出大块）。我们碎片率从 22%→3%。

### Q3：分离式 Prefill/Decode 为什么有效？什么时候不该用？

**答**：prefill 算力密集、decode 带宽密集，混部让 GPU 永远半忙；分离后 P 实例专攻算力、D 实例专攻带宽，两端都打满，长上下文有效吞吐 +30~50%。**不该用**：短请求（<2K token），KV 跨机传输开销抵消收益；以及集群规模小、P/D 实例难以均衡时。

### Q4：MIG 和 MPS 怎么选型？

**答**：MIG 是**物理硬隔离**（A100/H100 把 1 卡切 7 个实例，显存算力硬切，互不干扰），粒度粗（最小 1/7）、切换贵；MPS 是**共享 SM + 算力配额软隔离**，粒度细、开销小但会互相干扰。**规则**：付费 SLA/生产核心走 MIG，免费/弹性/best-effort 走 MPS。

### Q5：Spot 实例被回收，怎么做到请求不丢？

**答**：靠"请求可安全中断"三件套：① 收到回收信号先 `drain` 停止接新请求；② 在途请求 KV checkpoint 到 CPU/邻居（重放免重算）；③ 不可迁移的带 KV 重排队首。丢失率从 0.8%→<0.01%。核心认知：**省 70% 钱的前提是中断安全，否则省的成本抵不过一次丢请求的损失。**

### Q6：利用率和时延怎么权衡？会不会为提利用率把卡塞爆导致时延崩？

**答**：会——过度装箱（over-packing）把显存塞到 95%+，KV 稍涨就 OOM/抢占风暴。我们的做法是**利用率目标设上限（如 85%）+ 显存留 15% 安全垫 + 迭代级抢占保低优不饿死 + P99 时延红线自动降利用率目标**。即"在保证 SLA 前提下最大化利用率"，不是无脑塞。

---

---

### 🎯 模拟面试题 1：设计支撑千万 QPS、跨 Region 的 GPU 集群调度平台（端到端）

**参考答案要点（分层作答）**：

1. **资源感知层**：每卡实时上报显存/算力/NVLink/健康度/碎片，秒级刷新。
1. **放置层**：碎片感知 FFD 装箱（2.1）+ 拓扑感知（同 NUMA/NVLink 优先）+ 分离式 P/D 配对（2.3）。
1. **隔离层**：付费 SLA→MIG 硬隔离，弹性→MPS 软隔离 + 反亲和放置防干扰（2.4/2.6）。
1. **弹性层**：HPA 按排队时延扩容 + Spot 抢占安全回收（2.5）+ 跨 Region 流量调度（热点 Region 溢出到冷 Region）。
1. **观测层**：GPU 利用率/碎片率/排队/干扰检测实时看板 + P99 红线告警。
1. **计费层**：按租户聚合 token·卡时·电价，分账到业务线。
1. **容灾**：Region 级故障 DNS 60s 切换；单卡故障自动驱逐并重调度其上模型。

**加分项**：主动谈"利用率上限 + 安全垫 + 抢占优先级"的权衡（Q6），证明你懂"榨干"和"稳"的矛盾。

---

---

**参考答案要点（止血→定位→根治）**：

**0-5 分钟（止血）**：

- 监控发现利用率断崖 + 排队暴涨 → 立刻暂停非核心弹性负载（释放碎片），对核心流量开 MIG 硬隔离保 SLA。
- 若为某 Region 故障，DNS 切流到健康 Region。

**5-20 分钟（定位）**：

- 看是否"显存被占满但算力空闲"——典型是**碎片率飙升**（大量小模型各占整块显存，FFD 失效）→ 触发碎片整理。
- 还是"调度器卡死"——检查放置层是否出现**死锁/活锁**（所有模型都放不下又互不让步）。
- 对比变更：最近是否上了新大模型（显存需求远超预期）、是否 MIG 配置改错、是否 HPA 误判缩容。

**20-30 分钟（初步根因）**：常见三类：①新模型显存超预估导致大规模 OOM→碎片率↑ ②调度器 bug/限流误杀 ③基础设施（NVLink 故障导致拓扑感知失效，放置错乱）。

**根治 + 防复发**：

- 模型上线前强制"显存画像压测"（prefill/decode 峰值 KV 实测），不准凭 config 估算。
- 调度器加"死锁检测 + 自动碎片整理"兜底。
- 利用率/碎片率/排队三线联动告警，避免单看利用率误判。

**加分项**：强调"显存满≠利用率高"——利用率暴跌到 8% 恰恰是碎片把卡撑满但算力空转，这是 GPU 调度最有迷惑性的故障。

---

---

**参考答案要点（调度 + 编译 + 量化协同）**：

1. **连续批处理**：迭代级调度把吞吐 ×3（2.2），是最大单一杠杆。
1. **分离式 P/D**：本卡内逻辑分离 prefill/decode 队列，长上下文有效吞吐再 +30%（2.3）。
1. **INT4 量化 + 反量化内核**：7B 14GB→3.8GB，显存省出更多并发空间（呼应第24/43期），不掉点靠 AWQ 校准。
1. **投机解码**：小草稿模型替 7B 验 token，接受率 80%+ 时 decode ×1.8（呼应第22期）。
1. **算子融合 + Prefix Cache**：RMSNorm/RoPE/SwiGLU 融合减少 kernel 启动；相同 System Prompt 前缀共享 KV（呼应第51/55期）。
1. **MPS 切分 + 安全垫**：若需一卡多模型，按算力配额软隔离防干扰。

综合：连续批（×3）+ 投机（×1.8）+ INT4 并发空间（×1.5，非简单相乘，有重叠）≈ 单卡吞吐 ×4 量级，且 7B-INT4 输出质量经评测与 FP16 差异 <1%，性价比追平甚至超越 70B-FP16 单卡。

**加分项**：能指出"翻 3 倍"不是靠单一魔法，而是**调度（连续批）× 算法（投机）× 系统（量化/融合）三层叠加**，并主动谈质量验证（评测不掉点）才算闭环。

---

---

| th | th |
| --- | --- |
| td | td |
| td | td |
| td | td |
| td | td |
| td | td |
| td | td |
| td | td |
| td | td |

---

---