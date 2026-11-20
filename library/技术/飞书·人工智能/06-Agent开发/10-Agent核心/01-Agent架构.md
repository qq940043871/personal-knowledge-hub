# Agent架构

> 模块：Agent编排
> 更新时间：2026-11-15

---

## 一、Agent定义

> Agent 由三部分组成：**LLM 门面**（统一封装模型调用）、**工具注册表**（ToolRegistry：装饰器注册 + 从函数签名自动推断 JSON Schema）、**有界主循环**（MainLoop：Think → Act → Observe）。工程上必须保证循环**有界**（不会无限烧钱）、**失败可恢复**（工具异常转消息回传模型自愈，而不是崩溃）、**可观测**（轨迹日志 + 轮次/工具调用统计）。

### 1.1 组件层：LLM 门面 + 工具注册表

```python
# 组件层（伪代码：突出特殊点，完整实现见 ai-agent-harness）
class LLM:
    """LLM 门面：所有模型调用走这一个口"""
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.environ["LLM_API_KEY"],   # ★特殊点1 密钥只走环境变量
            timeout=60,                          #          显式超时，不裸奔
        )

class ToolRegistry:
    """工具注册表：注册一次，全循环复用"""
    def tool(self, fn):                          # ★特殊点2 装饰器注册：
        schema = infer_schema(fn)                #          JSON Schema 从函数签名
        self._tools[fn.__name__] = (fn, schema)  #          自动推断，无需手写

    async def dispatch_safe(self, name, args):
        """工具执行统一入口：返回 (success, result_or_error) 二元组"""
        async with self._sem:                    # ★特殊点3 Semaphore 并发限流
            result = await wait_for(run(name, args), timeout=30)
            return True, result                  # ★特殊点4 单工具强制超时
        # except 分支：任何异常捕获为 (False, "工具 xx 失败: 原因")
        #   ——工具失败也是「结果」，不是崩溃
```

### 1.2 有界主循环：Think → Act → Observe

主循环是 Agent 的「心脏」，全部特殊点都围绕**让循环永远有出口、永远可观测**：

```text
┌──────────────────── Agent 有界主循环 ────────────────────┐
│                                                          │
│   for turn in 1..MAX_TURNS:          ← 有界循环 ①        │
│   ┌────────────────────────────────────────────────┐     │
│   │ Think    LLM(messages, tool_definitions)       │     │
│   │ Budget   usage.total_tokens 累计 → 超限熔断 ②   │     │
│   │ Finish   无 tool_calls → 返回 AgentResult      │     │
│   │ Act      gather + Semaphore 并发执行工具 ③      │     │
│   │ Observe  成功/失败都转为 tool message 回传 ④    │     │
│   └────────────────────────────────────────────────┘     │
│                                                          │
│   出口：completed / max_turns_reached / budget_exhausted  │
└──────────────────────────────────────────────────────────┘
```

```python
# 有界主循环（伪代码：重点在特殊点）
class Agent:
    MAX_TURNS = 10               # ★特殊点5 轮次上限——防死循环的第一道墙
    TOKEN_BUDGET = 50_000        # ★特殊点6 token 预算熔断——第二道墙，
                                 #          预算在代码里硬约束，不靠模型自觉

    async def run(self, task) -> AgentResult:
        messages = [system_prompt(self.role), user(task)]
        for turn in range(1, self.MAX_TURNS + 1):
            resp = await self.llm.chat(messages,
                                       tools=self.registry.definitions())
            total_tokens += resp.usage.total_tokens
            self.emit("llm_call", turn=turn, tokens=total_tokens)
            #   ★特殊点7 事件上报：每轮轨迹可回放，出问题能复盘

            if total_tokens > self.TOKEN_BUDGET:
                return self.result("budget_exhausted")   # 超限强制终止

            if not resp.tool_calls:
                return self.result("completed", resp.content)
                #          无工具调用 = 任务完成（自然出口）

            messages.append(assistant(resp))
            results = await gather(                      # ★特殊点8 并发执行：
                dispatch_safe(c) for c in resp.tool_calls)
            #   本轮全部独立工具并行跑，单工具异常不炸整轮

            for call, (ok, out) in zip(resp.tool_calls, results):
                messages.append(tool_msg(call.id,
                                         out if ok else f"错误：{out}"))
                #   ★特殊点9 工具失败也是消息：错误回传模型自愈——
                #     模型读到「工具失败了、为什么失败」会自己调整策略

        return self.result("max_turns_reached")
        #   每个出口都返回带 turns / tool_calls / tokens 统计的 AgentResult
```

---

## 二、ReAct模式

> ReAct Agent：推理（Thought）与行动（Action）交替循环。生产环境推荐用 function calling 驱动循环（见 1.2 节）；当模型只能输出纯文本时，需要额外的**动作解析层**，并且必须**为解析失败准备兜底**——把「输出格式不合法」作为观察结果回传模型重新作答，而不是直接抛异常终止。

```python
# ReAct 文本输出的解析兜底（伪代码）
action = parse_action(text)          # 解析 {"action": ..., "input": {...}}
if action is None:
    #   ★特殊点 解析失败不抛异常：纠错提示回传模型重新作答一次
    action = retry_with_correction(text)
if action is None:
    action = {"action": "finish"}    #   仍失败 → 降级 finish，循环永远有出口
```

关键点：`parse_action` 失败不抛异常，而是进入「纠错重试」分支；重试后仍失败则降级为 `finish`，保证循环永远有界、永远有出口。

---

### 企业级升级要点

- **有界主循环**：max_turns + token 预算熔断 + 协作式停止，终止时返回带轮次/工具调用统计的 Result——完整实现在 `ai-agent-harness/harness/main_loop.py`（`LoopStats` / `LoopResult` / `_build_budget_exceeded_message`）。
- **工具注册与安全分发**：`@registry.tool` 装饰器 + `inspect` 签名推断 JSON Schema；`dispatch_safe` 返回 `(success, result_or_error)`——参考 `ai-agent-harness/harness/tools/registry.py` 与 `base.py`（`infer_schema`）。
- **工具失败也是结果**：异常不炸循环，转 tool message 回传模型自愈——参考 `main_loop.py` 的 `_execute_tools_parallel`（`asyncio.gather(..., return_exceptions=True)`）。
- **并发限流**：gather + `asyncio.Semaphore` 控制工具最大并发数——参考 `registry.py` 的 `dispatch_parallel`。
- **事件回调解耦**：`on_tool_call` / `on_llm_call` 事件系统，回调自身异常被 `_emit` 兜底——参考 `main_loop.py` 的 `on/emit` 事件机制。
- **成本与上下文治理**：token 级预算追踪与阶梯压缩是主循环的天然配件——参考 `ai-agent-harness/harness/cost_tracker.py` 与 `ai-agent-harness/harness/context_compactor.py`。

参考：[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：任务规划*
