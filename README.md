# personal-tech-knowledge

> 工作区目录名是 `personal-knowledge-hub`，仓库内页标题与启动脚本沿用旧名 `personal-tech-knowledge`——两者指同一份工程，暂不改名（改名会牵动 `index.html` / `start.bat` / 历史链接）。
> 更新日期：2026-11-13 ｜ 数字口径：以磁盘现状与 `git ls-files` 为准

个人 IT 技术知识库与创作资产工程。自 `p000_0000_it` 拆分而来，历史经 `git-filter-repo` 路径过滤保留。主体是**静态内容 + 轻量阅读器**，没有构建系统、测试套件或打包流程。

---

## 一、目录地图

| 路径 | 定位 | 现状 |
|------|------|------|
| `index.html` | 门户入口：暗色粒子 landing，聚合「知识库 / 博客」双入口 | 静态页 |
| `library/` | 知识库：**四大公开库**（技术 / 投资 / 工作 / 考证）+ **两个私有库**（家庭 / 隐私）+ 门户文件 | 3231 个文件、1768 篇 Markdown（本地全量）；其中 **2981 个文件 / 1646 篇 md 已入 git** |
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
| `技术/` | 17年技术经验总结、从0到1设计计算机、飞书·飞天闪客、飞书·人工智能 | 1390 | 858 | 1390（全量） |
| `投资/` | 七册 MOC + 交易系统 + 投研工作站 `08-fianace-console`；`01-我的实盘与成长史/` 私有 | 1116 | 558 | 970 |
| `工作/` | 基础学习 / 技术方案 / 求职与面试 / 团队管理；`客户跟踪/` 私有 | 319 | 231 | 237 |
| `考证/` | 软考-架构师 / 管理师 / 论文、PMP、项目管理联盟 | 374 | 96 | 374（全量） |
| `家庭/` | 成长、育儿 | 15 | 15 | 0（整库私有） |
| `隐私/` | 从各库抽出的敏感单篇（客户环境、证件 OCR、账户信息等） | 7 | 7 | 0（整库私有） |

> 2026-11-13 变更：`创作/` 库已下线（小说与自媒体素材移入 `output/`）；新增顶层私有库 `隐私/`；`library/投资/08-fianace-console/`（107 个文件）已入库。
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
# 静态服务器下访问 /blog/；文章默认读云端 posts 表，云端不可达或 ?local=1 时
# 回落 _seed/meta.json + blocks.jsonl + post_*.b64
```

依赖说明：`requirements.txt` 只覆盖 Flask 阅读器。博客依赖 WorkBuddy Cloud SDK（endpoint 与 publishableKey 写在 `blog/app.js`）与 CDN 的 highlight.js；静态门户和 `library/index.html` 无构建依赖。

---

## 三、版本控制边界

| 层 | 内容 | git 状态 |
|----|------|----------|
| 公开成品 | `index.html` / library 未排除目录 / `blog/` / `assets/` | 已跟踪，**3039 个文件**（其中 md 1650、library 2981） |
| 私有来源 | `library/家庭/`、`library/隐私/`、`library/投资/01-我的实盘与成长史/`、`library/工作/客户跟踪/`、`library/_备份元数据/` | `.gitignore` 排除，本地保留 |
| 本地资产层 | `agent/`、`output/` 两个顶层目录 | 显式整体排除，历史上从未入库 |

私有目录名单现在有**两道防线**：根 `.gitignore` 与 `library/.gitignore`（2026-11-13 新增，防止根文件被编辑器陈旧缓冲区回写覆盖后私有内容被 `git add -A` 推上去）。新增私有目录时**同步这两处即可**：`library/build_tree.py` 不再手抄名单，它运行时用 `git check-ignore` 判定，被忽略的目录自动不进公开站点树（git 不可用时退回 `FALLBACK_IGNORED_DIRS` 兜底）。

想放行本地资产层里的单个文件：目录被整体排除后 Git 不再递归进入，`!` 否定规则无效，用 `git add -f <path>`。

**已知待办 / 已知项**：

- `blog/_seed/` 下 `post_*.b64` / `blocks.jsonl` / `seed_posts.jsonl` 是生成产物，`.gitignore` 已列规则，但目前仍被 git 跟踪。忽略规则对已跟踪文件不生效；当前刻意保留，作为博客离线兜底数据。要改成只留生成脚本，需先执行 `git rm --cached ...`（见 `.gitignore` 注释）。
- 根 `index.html` 有 4 处链接指向 `library/17年技术经验总结/09-技术知识库/...`，实际路径是 `library/技术/17年技术经验总结/09-技术知识库/...`（成品拆库后的残留死链）。

---

## 四、实现注意事项

- library 内有**三套互不共享代码的阅读器**：`index.html`（静态 `tree.json`）、`python.html + app.py`（Flask）、`技术/17年技术经验总结/09-技术知识库/index.html`（自包含，`md-viewer.html?file=pages/...`）。改渲染或导航通常要改三处。
- `tree.json` 是生成产物，由 `library/build_tree.py` 扫描 `.md` / `.markdown` / `.pptx` 生成；`start.bat` 每次启动自动刷新（写临时文件后 `os.replace` 原子替换），新增或删除文档后不必手工维护侧边栏。
- 导航只渲染三级目录（分类 / 子目录 / 子子目录），更深的层级折叠为 `父/子` 标签；`build_tree.py` 用 `git check-ignore` 只跳过被 `.gitignore` 忽略的目录，当前 tree.json 含 `技术 / 投资 / 工作 / 考证` 四个公开库（家庭、隐私两个私有库被排除），共 1643 篇。
- 阅读器把 Markdown 渲染进自身页面，没有 `<base>` 或链接重写，正文里的**相对图片路径按阅读器页面所在目录解析**而非 `.md` 所在目录——成品库因此多用内联 SVG。

详细目录说明见 `library/README.md`（2026-11-13 已同步），分类导航见 `library/wiki.md`（**内容滞后，技术类链接仍是重构前旧路径**），AI 工作指引见 `CODEBUDDY.md` 与 `library/投资/08-fianace-console/CLAUDE.md`（后者只覆盖该子项目）。
