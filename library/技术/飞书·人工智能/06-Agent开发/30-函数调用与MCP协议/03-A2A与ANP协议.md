# A2A 与 ANP 协议

> 模块：函数调用与MCP协议  
> 更新时间：2026-11-15  
> 来源：hello-agents 工程（第 10 章）  
> 定位：02-FunctionCalling与MCP协议设计 讲单 Agent 接工具，本篇讲 Agent 之间怎么通信

---

---

---

---

> 三条协议不是三选一的竞争关系，而是**通信对象不同**的三层设施：MCP 解决「怎么访问工具」，A2A 解决「怎么和别的 Agent 对话」，ANP 解决「怎么在大规模网络里找到该找的 Agent」。

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

**选型口径**（协议均在早期，MCP 生态最成熟、优先选大厂背书的 Server）：要访问外部服务选 MCP；要多 Agent 协作选 A2A；要构建开放 Agent 网络才考虑 ANP——ANP 尚无成熟生态，hello-agents 只做概念模拟。

---

---

### 2.1 为什么不用中央协调器

星型拓扑的三个老问题：**单点故障（协调器挂了全瘫）、性能瓶颈（所有通信过中心）、扩展困难**（加 Agent 要改中心逻辑）。A2A 用网状 P2P 解决：请求生命周期为「代理发现 → 身份验证 → 发送消息 → 发送消息流」，任务有标准化生命周期（创建→协商→代理→执行中→完成/失败），每步可跟踪、异常可处理。

```
<code># A2A Server/Client 骨架（伪代码：重点在 AgentCard、对等身份与工件抽象）<br/># 完整实现见 hello-agents 工程 code/chapter10/ 的 09_A2A_Server.py、09_A2A_Client.py<br/>from hello_agents.protocols import A2AServer, A2AClient<br/><br/>researcher = A2AServer(<br/>    name="researcher", description="负责搜索和分析资料的Agent", version="1.0.0",<br/>    # ★特殊点1 构造参数即 AgentCard（能力名片）：声明「我是谁、会什么」，<br/>    #   客户端先据此发现再调用——描述质量直接决定这个 Agent 会不会被选中<br/>    capabilities={"research": ["search", "analyze"]},<br/>)<br/><br/>@researcher.skill("research")          # Skill = AgentCard 里最小可调用能力单元<br/>def handle_research(text: str) -&gt; str:<br/>    topic = parse(text)                # 解析请求 → 执行 → 返回结构化结果<br/>    return str({"topic": topic, "findings": "..."})   # ★特殊点2 返回值即工件（Artifact）：<br/>    #   A2A 的第一抽象是「任务(Task)+工件(Artifact)」而非 MCP 的单次工具返回值——<br/>    #   工件可带来源、可被下游 Agent 继续加工，这是它与 MCP 最大的区别<br/><br/>threading.Thread(target=lambda: researcher.run(port=5000), daemon=True).start()<br/><br/>client = A2AClient("http://localhost:5000")   # ★特殊点3 身份对等：同一个 Agent 既是<br/>result = client.execute_skill(                #   Server（暴露 Skill）也是 Client（调别人），<br/>    "research", "research AI在医疗领域的应用") #   协作不需要中央协调器中转</code>
```

### 2.2 多 Agent 协商

A2A 支持 Agent 间协商：发起方提交提案，对端评估后接受或给出反提案——协作的核心是博弈而非广播。

```
<code># 协商骨架（伪代码）：提案 → 评估 → 反提案<br/># 完整实现见 hello-agents 工程 code/chapter10/ 的 10_AgentNegotiation.py<br/>@agent1.skill("propose")<br/>def handle_proposal(text: str) -&gt; str:<br/>    proposal = parse_json(text)                 # {"task": "...", "deadline": 3}<br/>    # ★特殊点4 协商必须有「可拒绝 + 可反提案」两条出路：不接受时返回 counter_proposal<br/>    #   让发起方能决策下一步，而不是静默失败或无条件接受<br/>    if proposal["deadline"] &gt;= 7:<br/>        return str({"accepted": True})<br/>    return str({"accepted": False,<br/>                "counter_proposal": {"deadline": 7}})</code>
```

---

---

MCP 和 A2A 都要**预先知道**对端地址（server_command / agent_url）；节点规模到成百上千、且动态进出时，预配置失效。ANP 补这一层：Agent 暴露 `.well-known/agent-descriptions` 标准端点，发现服务爬取建索引实现动态匹配；交互前用 DID 私钥签名请求，对端解析 DID 拿公钥验签——无中心可信任根。

```
<code># ANP 服务发现 + 负载均衡骨架（伪代码：注册 → 发现 → 选择）<br/># 完整实现见 hello-agents 工程 code/chapter10/ 的 11_ANPInit.py、13_ANPLoadBalancing.py<br/>from hello_agents.protocols import ANPDiscovery, register_service<br/><br/>discovery = ANPDiscovery()<br/>register_service(<br/>    discovery, service_id="nlp_agent_1", service_type="nlp",<br/>    capabilities=["text_analysis", "sentiment"],<br/>    endpoint="http://localhost:8001",<br/>    metadata={"load": 0.3},   # ★特殊点5 metadata 是路由决策的数据面：负载/价格/版本<br/>)                             #   都从这里读——不随运行时更新，就会越调度越偏<br/>register_service(<br/>    discovery, service_id="nlp_agent_2", service_type="nlp",<br/>    capabilities=["text_analysis"],<br/>    endpoint="http://localhost:8002", metadata={"load": 0.7},<br/>)<br/><br/>def pick_server(service_type: str):<br/>    candidates = discovery.discover_services(service_type=service_type)<br/>    if not candidates:            # ★特殊点6 发现为空返回 None 而非抛异常：<br/>        return None               #   降级路径（重试/换类型/人工兜底）留给调用方<br/>    # ★特殊点7 min(load) 负载均衡只在「同类型多实例」时有意义——<br/>    #   服务发现的价值正在于这个选择不需要预配置对端地址<br/>    return min(candidates, key=lambda s: s.metadata.get("load", 1.0))</code>
```

---

---

hello-agents 的集成方案是三层架构：**协议实现层**（MCP 基于 FastMCP、A2A 基于 a2a-sdk、ANP 自研概念实现）→ **工具封装层**（MCPTool/A2ATool/ANPTool 都继承 BaseTool）→ **智能体集成层**（Agent 的 Tool System 全程无感协议差异）。

```
<code># 协议工具包装器骨架（伪代码）：把「远端能力」伪装成本地工具<br/># 完整实现见 hello-agents 工程 hello_agents/tools/builtin/protocol_tools.py<br/>import os<br/><br/>class ProtocolTool(BaseTool):<br/>    """MCPTool/A2ATool/ANPTool 的共同形态：协议差异全部吸收在 _dispatch 里"""<br/><br/>    def __init__(self, name: str, endpoint: str):<br/>        super().__init__(name)<br/>        self.endpoint = endpoint<br/>        self.token = os.environ["AGENT_API_KEY"]   # ★特殊点8 密钥只走 os.environ，<br/>                                                   #   不写死在代码与序列化参数里<br/><br/>    def run(self, input_data: dict) -&gt; str:<br/>        # ★特殊点9 对 Agent 而言协议工具与本地工具长得一模一样：远端 Agent、<br/>        #   服务发现中心都被降维成「一个可调用的 Tool」，主循环与注册表零改动<br/>        try:<br/>            return self._dispatch(input_data)<br/>        except (TimeoutError, ConnectionError) as e:   # ★特殊点10 只接预期异常族，转可读<br/>            return f"协议调用失败：{e}"                #   文本回传模型自行决策；禁裸 except<br/><br/># 接入只差三行（智能体集成层的全部代码）<br/># agent.add_tool(MCPTool(name="fs", server_command=["npx", "-y", ".../server-filesystem", "."]))<br/># agent.add_tool(A2ATool(name="researcher", agent_url="http://localhost:5000"))<br/># agent.add_tool(ANPTool(name="discovery", discovery=discovery))</code>
```

---

---

- **协议工具进工具注册表**：MCPTool/A2ATool/ANPTool 统一 BaseTool 接口后，schema 自动推断、dispatch 过滤、ToolGroup 白名单全部复用——对应 70-企业级工程基准 Agent #3 工具注册表。
- **跨 Agent 调用必须过中间件**：远端 Agent 的输出是不可信输入，PRE/POST_TOOL_CALL 拦截点与危险操作审批对协议工具同样生效——对应 Agent #6 多阶段中间件与 #7 人工审批。
- **AgentCard 是权限边界的起点**：Skill 声明即能力白名单，调用方只能看到声明过的技能；生产环境对 AgentCard 版本变更做审计。
- **降级链路显式化**：A2A 对端不可达、ANP 发现为空时退回本地工具或人工兜底，日志记录降级原因——协议层坏了系统还要能跑（基准「工具失败也是消息」精神的跨进程版）。
- **DID 私钥即密钥**：ANP 签名私钥与 API Key 同等对待，只走 os.environ/KMS，不进代码与配置明文。

70-企业级工程基准

---

---