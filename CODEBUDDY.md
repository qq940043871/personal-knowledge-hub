# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

工作区目录名是 `personal-knowledge-hub`，仓库内的页面标题、`start.bat` 与历史链接仍沿用旧名 `personal-tech-knowledge`——同一个工程，勿擅自改名。

本仓库是**静态内容 + 轻量阅读器 + 一次性维护脚本**，没有构建系统、测试套件、linter 或包管理清单（`requirements.txt` 只有 Flask，仅服务 library 的 Flask 阅读器）。

## 常用命令

```bash
# 门户 + 静态阅读器（推荐）。启动前自动跑 build_tree.py 刷新 tree.json，
# 端口 3005 被占用时会询问是否结束占用进程；优先用缓存的 npx http-server，其次 python。
start.bat

# 仅重建侧边栏索引（新增/删除文档后手动跑）
python library/build_tree.py

# 不用 bat 时，任选一个静态服务器（文档必须是 HTTP 打开，file:// 下 fetch 会失败）
python -m http.server 3005 --bind 127.0.0.1
npx http-server -p 3005 -c-1 -a 127.0.0.1
```

```bash
# Flask 阅读器：只服务 library/ 目录（WORKSPACE_PATH = app.py 所在目录），端口 5000
pip install -r requirements.txt
python library/app.py          # GET /api/files | GET /api/file?path=<相对 library/ 的路径>
```

```bash
# 归档层质量扫描：死链/未闭合围栏/坏表格/乱码/过度转义/超短文件
node tools/archive-quality-scan.mjs library

# 质量修复器：默认 dry-run，加 --apply 才落盘（转义残渣、尾悬挂 ```、丢图占位、U+FFFD）
node tools/archive-quality-fix.mjs --apply

# 查重：md5 精确重复 + minhash 近似重复，参数为仓库根相对目录（可多个，跨目录比对）
python tools/content_dup_scan.py library/技术 --min 0.55 --top 40
```

```bash
# 博客离线种子数据：从 library/ 精选文章生成 meta.json + blocks.jsonl（改造标题/导语/截断）
python blog/_seed/gen_blocks.py
# 校验 blocks.jsonl 每块 b64 能否干净解码为 UTF-8
python blog/_seed/check_b64.py
```

```bash
# 文档格式转换（docx2md 依赖 python-docx，需自行安装，不在 requirements.txt）
python tools/docx2md.py <源目录> <输出目录>
# 语雀导出 JSON → Markdown 文件树 + CDN 图片本地化（可选 --skip-images）
node tools/yuque-export/build.mjs <rawDir> <outDir>
```

`tools/` 下其余脚本（`reorg4sources.py`、`reorg_relink.py`、`reorg_library_split.py`、`repair_stale_links.py`、`cleanup_tech_dups.py`、`feishu_stub_clean.py`、`tdoc_*.py`）是已完成使命的一次性重组/导出工具，多数带 `--plan`/`--apply` 或 dry-run 开关，运行前先读文件头的 DEPRECATED 说明与用法。

## 架构

### 一句话结构

一个暗色门户 `index.html` → 两条访问路径：`library/`（Markdown 知识库 + 静态阅读器）与 `blog/`（云后端 SPA）。`tools/` 是维护脚本，顶层 `agent/`、`output/` 是本地资产层（不入库）。

### 版本控制三层（改内容前必须确认自己改的是哪层）

| 层 | 内容 | 状态 |
|----|------|------|
| 公开成品 | 根 `index.html`、`library/` 未排除目录、`blog/`、`tools/`、`assets/` | 已跟踪（795 个文件） |
| 私有来源 | 六库中被逐目录排除的飞书/语雀/为知/腾讯导出、家庭库、`library/_备份元数据/` | `.gitignore` 排除，仅本地存在 |
| 本地资产层 | 顶层 `agent/`、`output/` | 整体排除，历史上从未入库 |

目录被整体排除后 Git 不再递归进入，`!` 否定规则无效——确需入库单个文件只能用 `git add -f <path>`。`build_tree.py` 的 `SKIP_DIRS` 常量是同一份私有目录名单的复制品，静态站点因此不会暴露私有内容；**新增私有目录时 `.gitignore` 与 `SKIP_DIRS` 两处都要改**。

唯一例外是 `library/技术/飞书·人工智能/`：2026-11-12 起已从 `SKIP_DIRS` 与 `.gitignore` 同时放行（AI 内容唯一归口，需在阅读器里可浏览、也要随站点发布）。它是「私有来源里被提升为公开成品」的唯一案例，其余飞书/语雀/为知导出目录仍为私有。

### library/：内容布局与索引管线

六库固定为 `技术/ 投资/ 工作/ 考证/ 家庭/ 创作/`，每库内区分「成品（公开）」与「私有来源」。成品目录遵循编号约定：`00-总览/`、`01-基础/`、`02-进阶/`、`99-参考速查.md`。

导航不硬编码：`build_tree.py` 扫描磁盘，只收录 `.md/.markdown/.pptx`，跳过隐藏目录与顶层元数据文件，输出 `tree.json`（生成产物，`start.bat` 每次启动重建，写临时文件后 `os.replace` 原子替换）。数据形态是三层嵌套：`{分类: [files] | {子目录: [files] | {子子目录: [files]}}}`，目录直属文件用特殊键 `_files` 承载；更深的层级被**折叠**进 `父/子` 标签键（`emit_deep`）。`library/index.html` 按这个形状硬编码三段循环渲染并 `fetch(path)` 取正文。

### 三套互不共享代码的阅读器

改渲染、导航或样式通常要改三处，不要假设有共享模块：

1. `library/index.html` + `library/tree.json`：纯静态，`marked` + `highlight.js`（CDN）。
2. `library/python.html` + `library/app.py`：Flask，前端走 `/api/files`、`/api/file`；后端用 `Path.resolve()` + `is_relative_to(root)` 阻断 `../` 逃逸。
3. `library/技术/17年技术经验总结/09-技术知识库/index.html` + `md-viewer.html?file=pages/...`：自包含站点（原 `hello_my_profile`），iframe 式导航。

三者的共同限制：Markdown 正文被渲染进阅读器页面本身，没有 `<base>` 或 URL 重写，因此正文里的**相对图片/链接按阅读器页面所在目录解析，而非按 .md 所在目录**——归档层里大量 `![](images/xxx.png)` 形式的相对图在静态阅读器中会裂图，成品库因此多用内联 SVG。

### blog/：云后端 SPA（无构建）

`blog/index.html` 是外壳与全部样式，`blog/app.js` 是唯一逻辑文件（约 1200 行），通过 CDN 引入 WorkBuddy Cloud SDK、marked、DOMPurify、highlight.js。

- **数据抽象**：所有读操作走 `postsQuery()`，非本地模式返回 `cloud.database.from("posts")`，本地模式返回手写的 `localPosts()`——后者用 thenable 查询器模拟 `eq/gt/lt/contains/or/order/limit/range/select/maybeSingle` 的**子集**。新增查询条件时必须同时扩展 `localPosts()`，否则 `?local=1` 会静默走偏。
- **离线种子链**：`_seed/meta.json`（元信息）+ `_seed/blocks.jsonl`（正文按 400 字符切块、逐块独立 base64）。解码是「每块独立 atob → 拼接字节 → TextDecoder」，**不能直接拼 b64 字符串**。`gen_seed.py` 是更早的迭代版本（读外部 `KB_ROOT`，产出 `post_*.b64`），`gen_blocks.py` 才是当前生成器（读本仓库 `library/`）。
- **认证**：邮箱三通道（密码登录 / OTP 验证码登录 / 注册设密码）+ 忘记密码两段式（`resetPasswordForEmail` 返回的对象上再调 `updateUser({nonce, password})`）。OTP 状态存在模块级 `pendingEmailOtp`，切换邮箱会校验 `verificationId` 是否对应当前邮箱。
- **云存储资源**：正文里用自定义协议 `cloudimg:<path>` / `cloudfile:<path>` 占位，渲染后由 `resolveCloudAssets()` 批量换签名 URL（`createSignedUrls`，600 秒）；未登录则降级为「登录后可查看」占位块。因此 DOMPurify 必须放行这两个协议（`ADD_URI_SAFE_ATTR`），否则 `src` 会被清掉。
- **路由**：`location.hash` 手写路由表（`#/`、`#/post/:id`、`#/tags`、`#/tag/:t`、`#/login`、`#/write|#/edit/:id`、`#/mine`、`#/search/:kw`，纯数字 hash 视作首页分页）。所有 HTML 都经 `escapeHtml`。

### tools/：一次性脚本的约定

绝大多数脚本用 `WS = Path(__file__).resolve().parent.parent` 定位仓库根，不依赖 cwd；路径口径是**仓库根相对（含 `library/` 前缀）**。重组管线有严格顺序：`reorg4sources.py --plan`（产出 `library/_备份元数据/reorg_manifest.json` 全文件级清单）→ `--apply` → `reorg_relink.py`（按 manifest 改写链接）→ `reorg_library_split.py`（成品拆进六库，先算新内容再搬目录）→ `repair_stale_links.py`（修"文件搬了链接没跟着改"的存量链接）。删除类脚本一律「先 grep 全库入链、有入链则记录并改写」再动手。

### 内嵌子项目：library/投资/08-fianace-console/

投资交易工作站静态原型，纯 CDN（Tailwind + Font Awesome + Chart.js），零构建。`index.html` 是外壳（顶栏 + 可折叠侧栏 + `<iframe id="mainFrame">`），子页用 `parent.loadPage('module/page.html')` 导航，Tab 容器页用 `switchTab()` 加**目录相对**路径加载内层 iframe。每个 `.html` 都配一份同名 `.md`（页面概述/功能需求/页面结构/技术实现）。组件自己的 `CLAUDE.md` 与 `start.bat`（端口 3004）在该目录内，改动前先读它。

**涨跌配色是 A 股口径：红涨 `#DC2626`、绿跌 `#10B981`**，与欧美相反。已知文件名怪癖（`mainipulation_process.html`、`tongce_medical.html`）不要顺手"修正"。

### 内容规范

- 中文写作，实用直给，结构走「场景 → 原因分析 → 解决」，第二人称「你」。
- 文档体系遵循 Divio 四象限（`library/技术/技术文档体系/DOC_SYSTEM.md`）：Tutorial / How-to / Reference / Explanation，一篇文档只承担一种用途。
- 分类导航入口是 `library/wiki.md`，库总说明是 `library/README.md`（其统计数字落后于根 `README.md`，以磁盘现状为准）。

## 已知待办与坑

- 根 `index.html` 有 4 处链接指向 `library/17年技术经验总结/09-技术知识库/...`，但实际路径是 `library/技术/17年技术经验总结/09-技术知识库/...`（成品拆分进六库后的残留死链）。
- `library/投资/08-fianace-console/`（107 个文件）与 `library/毕业十年.md` 未被忽略、也未 `git add`，属待入库项，不是待清理垃圾。
- `blog/_seed/post_*.b64`、`blocks.jsonl`、`seed_posts.jsonl` 是生成产物，`.gitignore` 已列规则但仍被跟踪（忽略规则对已跟踪文件无效）；当前刻意保留作离线兜底，要清理需先 `git rm --cached`。
- `library/tree.json` 是生成产物，不要手改；`build_tree.py` 只认 `.md/.markdown/.pptx`，新增其他类型不会出现在侧边栏。
