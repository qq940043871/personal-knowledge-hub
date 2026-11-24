# personal-knowledge-hub

> 个人 IT 技术知识库与创作资产工程。

---

## 一、目录地图

| 路径 | 定位 | 现状 |
|------|------|------|
| `index.html` | 门户入口：暗色粒子 landing，六入口 3×2 网格（站内 2 个：技术知识库 / 码潮 CodeTide；站外 4 个新标签打开：OwnRAG、飞书 AI 笔记、面试工作台、AI 学习系统） | 静态页 |
| `library/` | 知识库：**四大公开库**（技术 / 投资 / 工作 / 考证）+ **两个私有库**（家庭 / 隐私）+ 门户文件 | 3369 个文件、1906 篇 Markdown（本地全量）；其中 **3106 个文件 / 1778 篇 md 已入 git** |
| `blog/` | 技术博客「码潮 CodeTide」单页应用 | 7 个文件：`index.html` + `app.js` + `favicon.svg` + `seed/`（`meta.json`、`blocks.jsonl`、`gen_blocks.py`、`check_b64.py`）；2026-11-23 起纯静态、无后端 |
| `tools/` | 96 个文件（49 个脚本：45 个 `.py` + 4 个 `.mjs`，其余为扫描报告与 JSON 中间产物）：重组 / 查重 / 修链 / 格式体检 / 腾讯文档导出等 | **整体不入库**（`.gitignore` 的 `tools/`），随用随跑，非运行时依赖 |
| `agent/` | AI 创作发布子项目 `media` + 读书拆解 `personal-read-book` | **本地资产层**：8474 文件 / 1.47 G，不入库 |
| `output/` | 创作资产库：articles / books / coze / novels / photo / videos，按 `drafts → published` 流转 | **本地资产层**：7059 文件 / 3.65 G，不入库 |
| `assets/` | 站点 favicon | 静态资源 |
| `start.bat` | 本地静态服务器，端口 3005 | 启动入口 |
| `requirements.txt` | 仅 `Flask>=3.0,<4.0`，只服务于 library 的 Flask 阅读器 | 不覆盖博客依赖 |

`library/` 各库现状（磁盘 / git 跟踪，2026-11-23 复核）：

| 库 | 定位 | 磁盘文件 | 磁盘 md | git 文件 | git md |
|----|------|---------:|--------:|---------:|-------:|
| `技术/` | 17年技术经验总结（621 篇，主干）、从0到1设计计算机、飞书·飞天闪客、飞书·人工智能（295 篇） | 1524 | 999 | 1524（全量） | 999 |
| `投资/` | 七册 MOC + 交易系统 + 投研工作站 `08-fianace-console`；`01-我的实盘与成长史/` 私有 | 1116 | 558 | 970 | 511 |
| `工作/` | 基础学习 / 技术方案 / 求职与面试 / 团队管理；`客户跟踪/` 私有 | 322 | 228 | 228 | 169 |
| `考证/` | 软考-架构师 / 管理师 / 论文、PMP、项目管理联盟 | 374 | 96 | 374（全量） | 96 |
| `家庭/` | 成长、育儿 | 15 | 15 | 0（整库私有） | 0 |
| `隐私/` | 从各库抽出的敏感单篇（客户环境、证件 OCR、账户信息等） | 7 | 7 | 0（整库私有） | 0 |
| 门户文件 | README / wiki / 毕业十年 / index.html / python.html / app.py / build_tree.py / tree.json / favicon / .gitignore | 10（另有 1 个 `__pycache__` 产物计入磁盘总数） | 3 | 10 | 3 |

合计：**3369 个文件 / 1906 篇 md**（本地全量），其中 **3106 个文件 / 1778 篇 md 已入 git**。

近期变更：

- **2026-11-24**：门户改六入口 3×2 网格——新增三个站外入口（`OwnRAG` 自研 RAG、飞书 AI 笔记、面试工作台）与 `AI 学习系统`，均 `target="_blank"`；头部品牌改为「我的知识宇宙」。博客首页删除阅读量（数据层 `views`、卡片、详情页、Hero 统计共 4 处）并连带移除「最热」排序；分页重做（此前容器缺 `.pager` 类导致 CSS 全部失效）。同时修复门户 4 处缺 `技术/` 一级的死链。
- **2026-11-23**：博客彻底下线云端——删除 WorkBuddy Cloud SDK、云数据库 posts 表、邮箱认证（密码 / OTP / 注册 / 重置）、云存储（图片与附件上传、签名 URL）、写文章 / 编辑 / 我的文章 / 删除 / 阅读计数，数据层收敛为 `blog/seed/` 唯一来源（正文按 400 字符切块、逐块独立 base64）。`_seed/` 目录改名为 `seed/`（绕开 Jekyll 的 `_` 前缀排除规则），仓库根新增 `.nojekyll`，GitHub Pages 上 `/blog/` 可直接打开。
- **2026-11-23**：全库发布前体检，P0 凭据清零、死链 113 → 0，发布清单定稿。
- **2026-11-23**：`技术/飞书·人工智能/` 内容扩充与重组，清理早期编号单篇、`10-面试题库/` 结构重整（现存 129 篇），单次提交 225 个文件。
- **2026-11-21**：11-15 自 `ai-study-note` 迁入的题库与手册、11-20 三 agent 全库复查改动全部提交。
- **2026-11-15**：自 `D:\ai_person\personal-ai-engineering\ai-study-note` 迁入 `技术/飞书·人工智能/10-面试题库/` 与 `11-快速学习手册/`（97 个文件，正文零改动）；同日新增 8 篇企业级与多 agent 文章；`10-面试题库/` 三线收敛去重 18 篇（备份于 `output/ai_cleanup_backup_2026-11-15_10面试题库/`）。
- **2026-11-13**：`创作/` 库下线（小说与自媒体素材移入 `output/`）；新增顶层私有库 `隐私/`；`技术/` 重整为四个顶层目录（**老路径如 `技术/Linux学习指南/` 已不存在**）；`_备份元数据/` 清理移除，历史搬迁记录只留在 git 历史里。

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

# 维护脚本
python library/build_tree.py          # 新增/删除文档后重建侧边栏索引
python blog/seed/gen_blocks.py        # library/ 内容变更后重跑，刷新博客数据
```

依赖说明：`requirements.txt` 只覆盖 Flask 阅读器。博客是纯静态 SPA，只依赖 CDN 的 marked / DOMPurify / highlight.js；静态门户和 `library/index.html` 无构建依赖。文档必须经 HTTP 打开，`file://` 下 `fetch('tree.json')` 会失败。

---

## 三、版本控制边界

| 层 | 内容 | git 状态 |
|----|------|----------|
| 公开成品 | `index.html` / library 未排除目录 / `blog/` / `assets/` | 已跟踪，**3122 个文件**（其中 md 1780、library 3106） |
| 私有来源 | `library/家庭/`、`library/隐私/`、`library/投资/01-我的实盘与成长史/`、`library/工作/客户跟踪/` | `.gitignore` 排除，本地保留 |
| 本地资产层 | `agent/`、`output/` 两个顶层目录 | 显式整体排除，历史上从未入库 |
| 本地工具 | `tools/` | 2026-11-13 起整体排除（已 `git rm -r --cached`） |

私有目录名单现在有**两道防线**：根 `.gitignore` 与 `library/.gitignore`（2026-11-13 新增，防止根文件被编辑器陈旧缓冲区回写覆盖后被 `git add -A` 推上去）。新增私有目录时**同步这两处即可**：`library/build_tree.py` 不再手抄名单，它运行时用 `git check-ignore` 判定，被忽略的目录自动不进公开站点树（git 不可用时退回 `FALLBACK_IGNORED_DIRS` 兜底）。

想放行本地资产层里的单个文件：目录被整体排除后 Git 不再递归进入，`!` 否定规则无效，用 `git add -f <path>`。

**已知待办 / 已知项**：

- `blog/seed/meta.json` + `blocks.jsonl` 由 `gen_blocks.py` 生成，是站点唯一数据源，必须入库（原 `.gitignore` 忽略规则已删）。`library/` 内容变更后需重跑生成器，博客才会同步。
- 根 `index.html` 有 5 处链接（3 个目标页面）指向 `library/17年技术经验总结/09-技术知识库/...`，实际路径是 `library/技术/17年技术经验总结/09-技术知识库/...`（成品拆库后的残留死链）。
- `library/README.md` 的统计表仍是 2026-11-15 口径（技术 1486 / 953 等旧数），与磁盘现状有偏差，以本文件与磁盘复核结果为准。

---

## 四、实现注意事项

- library 内有**三套互不共享代码的阅读器**：`index.html`（静态 `tree.json`）、`python.html + app.py`（Flask）、`技术/17年技术经验总结/09-技术知识库/index.html`（自包含，`md-viewer.html?file=pages/...`）。改渲染或导航通常要改三处。
- `tree.json` 是生成产物，由 `library/build_tree.py` 扫描 `.md` / `.markdown` / `.pptx` 生成；`start.bat` 每次启动自动刷新（写临时文件后 `os.replace` 原子替换），新增或删除文档后不必手工维护侧边栏。
- 导航只渲染三级目录（分类 / 子目录 / 子子目录），更深的层级折叠为 `父/子` 标签；`build_tree.py` 用 `git check-ignore` 只跳过被 `.gitignore` 忽略的目录，当前 tree.json 含 `技术 / 投资 / 工作 / 考证` 四个公开库（家庭、隐私两个私有库被排除），共 **1775 篇**。
- 阅读器把 Markdown 渲染进自身页面，没有 `<base>` 或链接重写，正文里的**相对图片路径按阅读器页面所在目录解析**而非 `.md` 所在目录——成品库因此多用内联 SVG。
- 博客路由是 `location.hash` 手写路由表（`#/`、`#/post/:id`、`#/tags`、`#/tag/:t`、`#/about`、`#/search/:kw`），全部列表 / 筛选 / 搜索都在内存数组 `__posts` 上完成，没有查询器抽象。
- 博客展示用的发布时间与阅读数由种子索引推导生成（刷新不跳动），**不要改成随机数**。

详细目录说明见 `library/README.md`（结构说明有效、统计数字滞后），分类导航见 `library/wiki.md`（**内容滞后，技术类链接仍是重构前旧路径**），AI 工作指引见 `CODEBUDDY.md` 与 `library/投资/08-fianace-console/CLAUDE.md`（后者只覆盖该子项目）。
