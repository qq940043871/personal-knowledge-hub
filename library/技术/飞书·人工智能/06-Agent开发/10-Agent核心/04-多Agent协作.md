# 多Agent协作

> 模块：Agent编排
> 更新时间：2026-03-29

---

## 一、协作模式

> 三种多 Agent 协作模式：主管-执行者、辩论、层级（Manager → Team Lead → Member）。

```
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

> 编排器三步流程：① 规划（Manager.plan）→ ② 分配任务（为每个子任务选择 Agent 执行并回传结果）→ ③ 汇总（Manager.summarize）。

```python
class MultiAgentOrchestrator:
    """多Agent编排"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.manager = None

    def add_agent(self, agent: Agent):
        self.agents[agent.name] = agent

    def set_manager(self, agent: Agent):
        self.manager = agent

    async def run(self, task: str) -> str:
        """运行协作"""
        if not self.manager:
            raise ValueError("No manager set")

        # 1. 规划
        plan = await self.manager.plan(task, {
            "available_agents": list(self.agents.keys())
        })

        # 2. 分配任务
        for subtask in plan.subtasks:
            agent = self._select_agent(subtask)
            result = await agent.execute(subtask)
            await self.manager.report(result)

        # 3. 汇总
        return await self.manager.summarize()
```

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

*下一步：模型量化*
