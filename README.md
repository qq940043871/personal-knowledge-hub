# personal-knowledge-hub

> 
个人 IT 技术知识库与创作资产工程。

---

## 一、目录地图

| 路径 | 定位 | 现状 |
|------|------|------|
| `index.html` | 门户入口：暗色粒子 landing，聚合「知识库 / 博客」双入口 | 静态页 |
| `library/` | 知识库：**四大公开库**（技术 / 投资 / 工作 / 考证）+ **两个私有库**（家庭 / 隐私）+ 门户文件 | 3315 个文件、1850 篇 Markdown（本地全量）；其中 **3058 个文件 / 1722 篇 md 已入 git**（2026-11-21 全部提交） |
| `blog/` | 技术博客「码潮 CodeTide」单页应用 | 20 个文件：云后端 + `?local=1` 离线种子兜底 |
| `tools/` | 30 个一次性维护脚本：重组 / 查重 / 修链 / 格式体检 / 腾讯文档导出等 | **整体不入库**（`.gitignore` 的 `tools/`），随用随跑，非运行时依赖 |
| `agent/` | AI 创作发布子项目 `media` + 读书拆解 `personal-read-book` | **本地资产层**：8138 文件 / 1.5G，不入库 |
| `output/` | 创作资产库：articles / books / coze / novels / photo / videos，按 `drafts → published` 流转 | **本地资产层**：6169 文件 / 4.1G，不入库 |
| `assets/` | 站点 favicon | 静态资源 |
| `start.bat` | 本地静态服务器，端口 3005 | 启动入口 |
| `requirements.txt` | 仅 `Flask>=3.0,<4.0`，只服务于 library 的 Flask 阅读器 | 不覆盖博客依赖 |

`library/` 各库现状（磁盘 / git 跟踪）：

| 库 | 定位 | 磁盘文件 | 磁盘 md | git 跟踪 |
|----|------|----------|---------|----------|
| `技术/` | 17年技术经验总结、从0到1设计计算机、飞书·飞天闪客、飞书·人工智能 | 1486 | 953 | 1486（全量） |
| `投资/` | 七册 MOC + 交易系统 + 投研工作站 `08-fianace-console`；`01-我的实盘与成长史/` 私有 | 1116 | 558 | 970 |
| `工作/` | 基础学习 / 技术方案 / 求职与面试 / 团队管理；`客户跟踪/` 私有 | 316 | 228 | 228 |
| `考证/` | 软考-架构师 / 管理师 / 论文、PMP、项目管理联盟 | 374 | 96 | 374（全量） |
| `家庭/` | 成长、育儿 | 15 | 15 | 0（整库私有） |
| `隐私/` | 从各库抽出的敏感单篇（客户环境、证件 OCR、账户信息等） | 7 | 7 | 0（整库私有） |

> 2026-11-13 变更：`创作/` 库已下线（小说与自媒体素材移入 `output/`）；新增顶层私有库 `隐私/`；`library/投资/08-fianace-console/`（107 个文件）已入库。
> 2026-11-15 变更：自 `D:\ai_person\personal-ai-engineering\ai-study-note` 迁入面试题库与快速学习手册——`library/技术/飞书·人工智能/` 新增 `10-面试题库/`（83 篇 + 平台架构图）与 `11-快速学习手册/`（11 篇），共 97 个文件，正文零改动、原目录名保留，与 01 模块重叠篇目按决策不去重；同日新增 4 篇企业级文章（40-RAG与检索/07-高级检索与查询优化、08-GraphRAG知识图谱检索、60-开发工具指南/04-ClaudeCode企业级实践、08-评估测试/02-评估体系全景，素材源自 D:\ai_llm 各 Datawhale 工程）；同日第二批多 agent 新增 4 篇（10-Agent核心/08-上下文工程、30-函数调用与MCP协议/03-A2A与ANP协议、05-LLM底层技术原理/11-GRPO与AgenticRL、05-部署推理/02-多推理引擎对比）；同日对 `10-面试题库/` 三线收敛去重 18 篇重复旧版（专项 9→1、综合 11→1，期数 63 篇保留为主干；备份于 `output/ai_cleanup_backup_2026-11-15_10面试题库/`，现存 65 篇）；磁盘计数已按 find 全量刷新。上述迁入与收敛、11-15 代码升级改动与 2026-11-20 三 agent 全库复查已于 2026-11-21 提交；提交后 git 口径为全仓 3087 文件 / md 1724 / library 3058。
> `output/README.md` 的标题沿用旧名 `assets/`，与实际目录名不符；它描述的就是本工程的 `output/`。

---

## 二、怎么跑

```bash
# 方式 1：门户 + 静态阅读器（推荐）
start.bat                       # http://127.0.0.1:3005/
# 启动时会执行 library/build_tree.py 重扫目录生成 tree.json；端口被占用时询问是否结束占用进程

# 方式 2：Flask 阅读器
pip install -r requirements.txt
python library/app.py           # http://localhost:5000/
# GET /api/files 列出文档；GET /api/file?path=<相对路径> 取正文（已做目录穿越防护）

# 博客
# 静态服务器下访问 /blog/；文章全部来自 blog/seed/（meta.json + blocks.jsonl），无后端
```

依赖说明：`requirements.txt` 只覆盖 Flask 阅读器。博客是纯静态 SPA，只依赖 CDN 的 marked / DOMPurify / highlight.js（2026-11-23 起云端后端与 WorkBuddy Cloud SDK 已移除）；静态门户和 `library/index.html` 无构建依赖。

---

## 三、版本控制边界

| 层 | 内容 | git 状态 |
|----|------|----------|
| 公开成品 | `index.html` / library 未排除目录 / `blog/` / `assets/` | 已跟踪，**3087 个文件**（其中 md 1724、library 3058） |
| 私有来源 | `library/家庭/`、`library/隐私/`、`library/投资/01-我的实盘与成长史/`、`library/工作/客户跟踪/`、`library/_备份元数据/` | `.gitignore` 排除，本地保留 |
| 本地资产层 | `agent/`、`output/` 两个顶层目录 | 显式整体排除，历史上从未入库 |

私有目录名单现在有**两道防线**：根 `.gitignore` 与 `library/.gitignore`（2026-11-13 新增，防止根文件被编辑器陈旧缓冲区回写覆盖后私有内容被 `git add -A` 推上去）。新增私有目录时**同步这两处即可**：`library/build_tree.py` 不再手抄名单，它运行时用 `git check-ignore` 判定，被忽略的目录自动不进公开站点树（git 不可用时退回 `FALLBACK_IGNORED_DIRS` 兜底）。

想放行本地资产层里的单个文件：目录被整体排除后 Git 不再递归进入，`!` 否定规则无效，用 `git add -f <path>`。

**已知待办 / 已知项**：

- `blog/seed/meta.json` + `blocks.jsonl` 由 `gen_blocks.py` 生成，2026-11-23 云端博客下线后成为站点唯一数据源，必须入库（原 `.gitignore` 忽略规则已删）。`library/` 内容变更后需重跑生成器，博客才会同步。
- 根 `index.html` 有 4 处链接指向 `library/17年技术经验总结/09-技术知识库/...`，实际路径是 `library/技术/17年技术经验总结/09-技术知识库/...`（成品拆库后的残留死链）。

---

## 四、实现注意事项

- library 内有**三套互不共享代码的阅读器**：`index.html`（静态 `tree.json`）、`python.html + app.py`（Flask）、`技术/17年技术经验总结/09-技术知识库/index.html`（自包含，`md-viewer.html?file=pages/...`）。改渲染或导航通常要改三处。
- `tree.json` 是生成产物，由 `library/build_tree.py` 扫描 `.md` / `.markdown` / `.pptx` 生成；`start.bat` 每次启动自动刷新（写临时文件后 `os.replace` 原子替换），新增或删除文档后不必手工维护侧边栏。
- 导航只渲染三级目录（分类 / 子目录 / 子子目录），更深的层级折叠为 `父/子` 标签；`build_tree.py` 用 `git check-ignore` 只跳过被 `.gitignore` 忽略的目录，当前 tree.json 含 `技术 / 投资 / 工作 / 考证` 四个公开库（家庭、隐私两个私有库被排除），共 1719 篇。
- 阅读器把 Markdown 渲染进自身页面，没有 `<base>` 或链接重写，正文里的**相对图片路径按阅读器页面所在目录解析**而非 `.md` 所在目录——成品库因此多用内联 SVG。

详细目录说明见 `library/README.md`（2026-11-13 已同步），分类导航见 `library/wiki.md`（**内容滞后，技术类链接仍是重构前旧路径**），AI 工作指引见 `CODEBUDDY.md` 与 `library/投资/08-fianace-console/CLAUDE.md`（后者只覆盖该子项目）。
