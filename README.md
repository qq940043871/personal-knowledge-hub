# personal-tech-knowledge

> 工作区目录名是 `personal-knowledge-hub`，仓库内页标题与启动脚本沿用旧名 `personal-tech-knowledge`——两者指同一份工程，暂不改名（改名会牵动 `index.html` / `start.bat` / 历史链接）。
> 更新日期：2026-11-10 ｜ 数字口径：以磁盘现状与 `git ls-files` 为准

个人 IT 技术知识库与创作资产工程。自 `p000_0000_it` 拆分而来，历史经 `git-filter-repo` 路径过滤保留。主体是**静态内容 + 轻量阅读器**，没有构建系统、测试套件或打包流程。

---

## 一、目录地图

| 路径 | 定位 | 现状 |
|------|------|------|
| `index.html` | 门户入口：暗色粒子 landing，聚合「知识库 / 博客」双入口 | 静态页 |
| `library/` | 六大知识库：技术 / 投资 / 工作 / 考证 / 家庭 / 创作，外加门户文件 | 3782 个文件、2279 篇 Markdown（本地全量）；其中 **651 篇成品已入 git** |
| `blog/` | 技术博客「码潮 CodeTide」单页应用 | 云后端 + `?local=1` 离线种子兜底 |
| `tools/` | 15 个一次性维护脚本：重组 / 查重 / 修链 / 腾讯文档导出等 | 随用随跑，非运行时依赖 |
| `agent/` | AI 创作发布子项目 `media` + 读书拆解 `personal-read-book` | **本地资产层**：8138 文件 / 1.6G，不入库 |
| `output/` | 创作资产库：articles / books / coze / novels / photo / videos / wikis，按 `drafts → published` 流转 | **本地资产层**：6131 文件 / 4.1G，不入库 |
| `assets/` | 站点 favicon | 静态资源 |
| `start.bat` | 本地静态服务器，端口 3005 | 启动入口 |
| `requirements.txt` | 仅 `Flask>=3.0,<4.0`，只服务于 library 的 Flask 阅读器 | 不覆盖博客依赖 |

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
| 公开成品 | `index.html` / library 未排除目录 / `blog/` / `tools/` / `assets/` | 已跟踪，795 个文件（含 651 篇 md） |
| 私有来源 | 六库中逐目录排除的飞书 / 语雀 / 为知导出、家庭库、`_备份元数据/` | `.gitignore` 排除，本地保留 |
| 本地资产层 | `agent/`、`output/` 两个顶层目录 | 2026-11-10 显式整体排除，历史上从未入库 |

想放行本地资产层里的单个文件：目录被整体排除后 Git 不再递归进入，`!` 否定规则无效，用 `git add -f <path>`。

两处**待办 / 已知项**：

- `library/投资/08-fianace-console/`（投研控制台，107 个文件）与 `library/毕业十年.md` 是 2026-11-10 新增的成品，**未被忽略、也尚未 `git add`**——属于待入库项，不是待清理的垃圾。
- `blog/_seed/` 下 `post_*.b64` / `blocks.jsonl` / `seed_posts.jsonl` 是生成产物，`.gitignore` 已列规则，但目前仍被 git 跟踪。忽略规则对已跟踪文件不生效；当前刻意保留，作为博客离线兜底数据。要改成只留生成脚本，需先执行 `git rm --cached ...`（见 `.gitignore` 注释）。

---

## 四、实现注意事项

- library 内有**三套互不共享代码的阅读器**：`index.html`（静态 `tree.json`）、`python.html + app.py`（Flask）、`技术/17年技术经验总结/09-技术知识库/index.html`（自包含）。改渲染或导航通常要改三处。
- `tree.json` 是生成产物，由 `library/build_tree.py` 扫描 `.md` / `.markdown` / `.pptx` 生成；`start.bat` 每次启动自动刷新，新增或删除文档后不必手工维护侧边栏。
- 阅读器只渲染三级目录（分类 / 子目录 / 子子目录），更深的层级折叠为 `父/子` 标签。

详细目录说明见 `library/README.md`，分类导航见 `library/wiki.md`，AI 工作指引见 `library/CLAUDE.md`。
