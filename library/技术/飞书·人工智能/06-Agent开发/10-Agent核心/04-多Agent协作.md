# 多Agent协作

> 模块：Agent编排
> 更新时间：2026-11-15

---

## 一、协作模式

> 三种多 Agent 协作模式：主管-执行者、辩论、层级（Manager → Team Lead → Member）。

```text
多Agent模式：
  1. 主管-执行者
     - 主管分解任务
     - 执行者执行子任务

  2. 辩论
     - 多个Agent讨论
     - 投票决定

  3. 层级
     - Manager → Team Lead → Member
```

---

## 二、实现

> 编排器三步流程：① 规划（Manager.plan）→ ② 分配任务（为每个子任务选择 Agent 执行并回传结果）→ ③ 汇总（Manager.summarize）。工程要点：子任务**并发执行**（`asyncio.gather` + `return_exceptions=True` 隔离失败），任一子任务异常不再炸穿整个 run——失败项标注后随部分结果一起进入汇总。

```python
# 多Agent编排（伪代码：三种协作模式共用「规划 → 并发分配 → 汇总」骨架）
#   模式① 主管-执行者：Manager.plan 分解 → 执行者各跑子任务 → Manager.summarize
#   模式② 辩论：各 Agent 独立作答同一提案 → 互评/投票 → 裁决汇总
#   模式③ 层级：把「执行者」换成 Team Lead 编排器，递归复用本骨架
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SubTask:
    description: str
    agent: Optional[str] = None           # 期望执行者名（空 = 选择器推断）


@dataclass
class Plan:
    subtasks: List[SubTask] = field(default_factory=list)


class Agent:
    """最小 Agent 定义：生产实现复用 01-Agent架构.md 的有界主循环"""

    def __init__(self, name: str, role: str, llm):
        self.name, self.role, self.llm = name, role, llm

    async def execute(self, subtask: SubTask) -> str:
        ...    # 内部走有界主循环，从略


class Manager(Agent):
    """主管：plan 分解 → report 收汇报 → summarize 汇总"""

    async def plan(self, task: str, context: Dict) -> Plan:
        ...    # LLM 输出 JSON 子任务数组：解析失败重试一次，仍失败降级
        #   为单子任务（三层兜底同 02-任务规划.md）

    async def report(self, subtask: SubTask, result: str) -> None:
        ...    # 汇报留痕：写日志 / 共享黑板

    async def summarize(self, results: List[str]) -> str:
        ...    # 各子任务结果 → 最终报告
```

```python
class MultiAgentOrchestrator:  # （续）编排器：并发分配与失败隔离

    def __init__(self, max_concurrency: int = 3):
        self.agents: Dict[str, Agent] = {}
        self.manager: Optional[Manager] = None
        self._sem = asyncio.Semaphore(max_concurrency)   # 子任务并发上限

    async def run(self, task: str) -> str:
        if self.manager is None:
            raise ValueError("必须先 set_manager 设置主管")

        plan = await self.manager.plan(
            task, {"available_agents": list(self.agents.keys())})

        results = await asyncio.gather(              # ★特殊点1 并发隔离
            *[self._dispatch(s) for s in plan.subtasks],
            return_exceptions=True)
        #   return_exceptions=True 把异常「收编」为返回值：任一子任务
        #   失败都不会炸穿整个 run

        collected: List[str] = []
        for sub, res in zip(plan.subtasks, results):
            if isinstance(res, Exception):
                collected.append(f"[{sub.description}] 执行失败: {res}")
                #   ★特殊点2 失败子任务标注原因后随部分结果一起进汇总，
                #     不因个别失败丢掉整体产出
            else:
                collected.append(res)
                await self.manager.report(sub, res)  # 成功者正常汇报留痕
        return await self.manager.summarize(collected)

    async def _dispatch(self, sub: SubTask) -> str:
        agent = self._select_agent(sub)   # 一行带过：指定名优先，否则回退
        if agent is None:                 #   执行者不存在独立报错，不连坐
            raise LookupError(f"没有可用执行者处理: {sub.description}")
        async with self._sem:             # ★特殊点3 Semaphore 限流防打爆下游
            return await agent.execute(sub)

    def _select_agent(self, sub: SubTask) -> Optional[Agent]:
        return self.agents.get(sub.agent) or next(iter(self.agents.values()), None)
```

*完整实现见 ai-agent-harness 工程（`add_agent` / `set_manager` 注册入口与主循环实现）。*

*图：多 Agent 编排执行流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 150" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="10" y="45" width="145" height="60" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="82" y="70" text-anchor="middle" font-size="14" fill="#1e293b">接收任务</text>
  <text x="82" y="92" text-anchor="middle" font-size="13" fill="#475569">任务输入</text>
  <line x1="155" y1="75" x2="195" y2="75" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="195" y="45" width="145" height="60" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="267" y="70" text-anchor="middle" font-size="14" fill="#1e293b">主管规划</text>
  <text x="267" y="92" text-anchor="middle" font-size="13" fill="#475569">Manager.plan</text>
  <line x1="340" y1="75" x2="380" y2="75" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="380" y="45" width="145" height="60" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="452" y="70" text-anchor="middle" font-size="14" fill="#1e293b">分配子任务</text>
  <text x="452" y="92" text-anchor="middle" font-size="13" fill="#475569">执行并汇报</text>
  <line x1="525" y1="75" x2="565" y2="75" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="565" y="45" width="145" height="60" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="637" y="70" text-anchor="middle" font-size="14" fill="#1e293b">汇总输出</text>
  <text x="637" y="92" text-anchor="middle" font-size="13" fill="#475569">Manager.summarize</text>
  <text x="360" y="135" text-anchor="middle" font-size="13" fill="#475569">未设置 Manager 时直接抛出 ValueError</text>
</svg>

---

### 企业级升级要点

- **并发隔离**：`asyncio.gather(..., return_exceptions=True)` 把子任务异常收编为返回值，失败不炸 run、部分结果照常汇总——与 `ai-agent-harness/harness/main_loop.py` 的 `_execute_tools_parallel` 同一模式。
- **并发限流**：`asyncio.Semaphore` 控制子任务/工具最大并发，防止打爆下游——参考 `ai-agent-harness/harness/tools/registry.py` 的 `dispatch_parallel`。
- **规划解析兜底**：Manager.plan 的 JSON 解析失败重试一次、再失败降级单子任务——与 02-任务规划.md 及 `ai-agent-harness/harness/provider/` 的重试容错一致。
- **类型显式化**：`SubTask` / `Plan` 用 dataclass 定义，`_select_agent` 有明确回退策略——参考 `harness/multi_agent.py` 与 `harness/subagent.py` 的子代理编排。
- **汇报与汇总留痕**：每条汇报走 `manager.report` 并记录日志，便于事后审计——参考 `ai-agent-harness/harness/tracer.py`。

参考：[70-企业级工程基准](../70-企业级工程基准.md)

---

*下一步：模型量化*
