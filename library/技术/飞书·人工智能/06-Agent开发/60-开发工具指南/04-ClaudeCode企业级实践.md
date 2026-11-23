# ClaudeCode企业级实践

> 模块：开发工具指南  
> 更新时间：2026-11-15  
> 来源：claude-howto 工程（v2.1.160，2026-06 同步，特性带版本号）  
> 定位：01-ClaudeCode学习指南 是概念总览；本篇讲六种扩展机制的**组合用法**——AI 编码 Agent 的工程化模式，同类 CLI Agent 工具（ZCode 等）机制同构，模式可平移

---

---

机制选错载体是一切混乱的根源。先用一张表定位：

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

**关键分工原则**：能写成代码检查的（Hook）绝不写进提示词；需要模型判断的（Skill/Subagent）不要硬塞 Hook；跨会话复用的组合（命令+子代理+hook+MCP）打成 Plugin。

## 二、Subagent 编排

### 2.1 上下文隔离是第一价值

子代理的本质不是「多个帮手」，而是**上下文预算的隔离墙**：子任务的所有中间输出（几千行搜索结果、构建日志）留在子代理上下文里，只有结论回到主对话。

```
<code># 子代理委派契约（伪代码骨架；对应 ai-agent-harness 基准 Agent #13）<br/>delegate(<br/>    task="审查 auth 模块的安全性",<br/>    model="cheap-model",          # ★特殊点1 规划/搜索用便宜模型，审查结论才回主对话<br/>    allowed_tools=["Read", "Grep"],   # 按职责裁剪工具集：审查者不该有写权限<br/>    timeout=300, max_cost=0.5,    # 预算硬约束：超限熔断，不靠子代理自觉<br/>    isolation="worktree",         # ★特殊点2 worktree 隔离：子代理在独立 git worktree<br/>                                  #   实验，无改动自动清理，有改动返回路径——<br/>                                  #   主分支永远不被并发实验污染<br/>)</code>
```

**干净上下文 vs 继承上下文（fork）**：默认干净上下文（只带任务描述）；当子任务需要「主对话的完整讨论史」才能做时（如「按我们刚才的结论重构」）才用 fork 继承——继承省去背景同步，但吃双倍上下文预算，且父对话的噪声会干扰子代理。

### 2.2 后台与并行

独立子任务后台并行（各自通知完成），派发后主对话继续做自己的事；有依赖关系的任务串行。多实例协作的实验性形态（共享任务列表 + 信箱互发消息 + 依赖自动管理）适合真正需要「协商」的场景，多数编排用「主代理派发 + 结果汇总」就够。

## 三、Skill 渐进式披露

Skill 解决「领域知识放哪」的问题：全部塞 System Prompt 上下文爆炸，全部外置模型又看不见。

三层加载模型：

| th | th | th | th |
| --- | --- | --- | --- |
| td | td | td | td |
| td | td | td | td |
| td | td | td | td |

```
<code>---<br/>name: code-review-specialist<br/>description: 代码审查时使用。触发词：review、审查、检查代码   # ★特殊点1 description<br/>disable-model-invocation: false                              #   是模型的路由依据——写清<br/>allowed-tools: Read, Grep, Bash                              #   「什么时候用」比写「是什么」重要<br/>---<br/>（L2 正文：审查清单与步骤；脚本与模板放同目录，正文里引用路径即 L3）</code>
```

- **优先级**：enterprise > personal > project，同名技能就近覆盖——团队规范放项目级，个人偏好放用户级；
- **描述预算**：所有技能的 L1 元数据共享约 1% 上下文预算，技能数量失控时先砍冗余 description。

## 四、Hook：确定性质量闸门

Hook 是把「提示词里的祈祷」变成「代码里的检查」的机制——与本库 RAG 双闸门（70-企业级工程基准 RAG #11）同一设计哲学。

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |

```
<code>{<br/>  "hooks": {<br/>    "PreToolUse": [{<br/>      "matcher": "Bash",                     // 第一层：按工具名匹配<br/>      "if": "Bash(git push *)",              // ★特殊点1 第二层 if 按调用参数过滤：<br/>      "hooks": [{"type": "command",          //   权限规则语法（Edit(src/**) 等），<br/>                "command": "./deny-force-push.sh"}]  //   同一事件不同参数不同策略<br/>    }]<br/>  }<br/>}</code>
```

- **拦截协议**：hook 脚本经 stdin 收 JSON（工具名/参数），退出码与 stdout JSON 决定放行/阻断/反馈给模型修正；
- **组件级 hooks**：hook 可写在 SKILL.md / 子代理定义的 frontmatter 里——技能自带质量闸门，随技能分发。

## 五、MCP 与上下文治理

MCP 三种传输（HTTP 推荐/stdio 本地/SSE 废弃）、三档作用域（local/project/user）与去重规则之外，企业级重点在**上下文成本**：

- 每个工具的描述常驻上下文，单服务器描述有上限（约 2KB/工具）；接入 10 个 MCP 服务器 × 20 工具，未做治理时上下文被工具描述吃掉一大块；
- **Tool Search**：工具描述总预算超阈值时自动降级为「按需搜索工具」（`ENABLE_TOOL_SEARCH=auto`），特定必须常驻的服务器用 `alwaysLoad: true` 豁免；
- **MCP vs Memory 决策**：高频变化的数据（构建状态、任务列表）走 MCP 实时拉取；低频稳定的知识（团队规范、架构说明）走 CLAUDE.md/记忆文件——决策依据是数据变化频率。

## 六、Headless 与 CI

```
<code># 非交互模式（print mode）+ JSON schema 校验输出——Agent 可编程化<br/>claude -p "审查 PR #42 的安全性" \<br/>  --output-format json \            # 结构化输出：结果+用量+会话 id<br/>  --permission-mode plan \          # ★特殊点1 CI 里用 plan/受限模式：<br/>  --append-system-prompt "只审查不改代码"   #   最小权限原则，自动审查不开写权限</code>
```

- 典型组合：GitHub Actions 定时跑 `claude -p` 做代码审查/文档过期检测，schema 校验保证输出可机读可告警；
- 配套命令：`--agents` JSON 内联定义子代理（CLI > 项目 > 用户级优先级）、会话 resume/fork 支持断点重跑。

## 七、安全与权限

- **六种权限模式**：default / acceptEdits / plan / auto / dontAsk / bypassPermissions——生产与 CI 只用 plan 或显式白名单，bypassPermissions 仅限一次性沙箱；
- **Auto Mode 决策序**：显式规则 → 只读放行 → 分类器判断 → 默认拒绝；`hard_deny` 无条件封杀（如 `rm -rf`），`allow/soft_deny` 支持从默认值追加——封杀清单不进提示词，进配置；
- **Checkpoints 与 git 分工**：检查点每条用户提示自动建、保留 30 天，适合「对话级回退」（恢复代码+对话/仅对话/仅代码）；但它**不追踪 bash 的 rm/mv/cp 和外部编辑器改动**，不能替代 git——边界：checkpoints 管会话内试错，git 管版本历史；
- **记忆层级**：企业策略 > 项目 CLAUDE.md > `.claude/rules/`（可按 `paths:` glob 限定生效目录）> 用户级 > local——规范下沉到离代码最近的层级。

### 企业级升级要点

- **预算硬约束贯穿**：子代理 timeout/max_cost（Agent #13）、Skill 描述预算（1% 上下文）、MCP 工具描述上限——CLI Agent 与业务 Agent 的上下文治理是同一门学问，见 70-企业级工程基准 Agent #9/#13。
- **确定性优先**：Hook 管格式/安全/卡点（代码判断），Skill 管知识/流程（模型判断），别反过来——把 lint 写进提示词等于每轮重算一遍且不可靠。
- **降级与可见性**：Hook 失败要显式报错而不是静默放行；CI 集成的每次运行有会话 id 可回放（对应公共约定 #6 可回放）。
- **版本敏感**：CLI Agent 迭代极快（本篇特性对应 v2.1.x 系列），配置写法以官方文档当前版本为准——无版本号的教程配置很容易失效。

---

---