# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal knowledge base and technical documentation repository (`library/`, part of the `personal-tech-knowledge` workspace). It is organized as **six top-level knowledge bases** (技术/投资/工作/考证/家庭/创作) plus portal files. The git-tracked (public) content holds 651 Markdown files (608 under 技术, 10 under 考证, 8 under 投资, 9 under 工作, 16 under 创作); alongside them sit private source archives (Feishu/Yuque/WizNote/Tencent exports) kept locally and excluded from git, bringing the full local tree to 2600+ Markdown files. A Flask web app provides a browsable document viewer.

## Running the Document Viewer

```bash
pip install -r ../requirements.txt
python app.py
# Serves at http://localhost:5000 — browse all Markdown files via the web UI
```

Dependencies are pinned in the repo-root `requirements.txt` (Flask only).

**API Endpoints:**
- `GET /` — Serves the document viewer UI (`python.html`)
- `GET /api/files` — Returns JSON array of all Markdown files grouped by directory
- `GET /api/file?path=<relative_path>` — Returns JSON with `path` and `content` fields for a specific file. Paths are resolved and confined to this workspace; `../` traversal returns 404.

**HTML Files:**
- `python.html` — Markdown viewer served at `/` by Flask, uses marked.js for rendering
- `index.html` — Static viewer with left sidebar directory tree navigation; works without the Flask backend
- `build_tree.py` — Scans this directory and regenerates `tree.json` (the sidebar index consumed by `index.html`); run it after adding or removing documents
- `技术/17年技术经验总结/09-技术知识库/index.html` + `md-viewer.html` — self-contained knowledge-base portal with its own renderer

Note: the three viewers above are independent implementations that do not share code. A change to rendering or navigation usually has to be applied to each one separately.

`index.html` does not hard-code the directory tree. On load it fetches `tree.json`, which `build_tree.py` generates from the actual files on disk, so the sidebar can never link to a deleted file. Only `.md` / `.markdown` / `.pptx` are indexed; source code, hidden directories, and top-level metadata files are skipped. The viewer renders three levels (category → subdirectory → sub-subdirectory); anything deeper is folded into a `parent/child` label.

## Development Notes

This is a **documentation-only repository** with no build system, test suite, or linter. The only runnable code is the Flask web viewer plus the `build_tree.py` index generator.

- All content is in Markdown — no compilation or transpilation needed
- Hidden directories (starting with `.`) are excluded from the document viewer
- `tree.json` is a generated artifact; `start.bat` regenerates it on every launch, or run `python library/build_tree.py` manually

## Repository Structure

**Knowledge base directories** follow a consistent numbering convention (finished-product directories):
```
主题名/
├── 00-总览/          # Overview / index
├── 01-基础/          # Basics
├── 02-进阶/          # Advanced
└── 99-参考速查.md     # Quick reference cheat sheet
```

Top-level layout — six knowledge bases, each mixing public finished products (git-tracked) and private local source archives (git-ignored):

| Base | Public (git-tracked) | Private (local only) |
|------|----------------------|----------------------|
| `技术/` | 25 finished directories: `17年技术经验总结/`, `Java框架全景图/`, `Java避坑指南/`, learning guides (`Linux/`, `Nginx/`, `Redis/`, `Kafka/`, `Zookeeper/`, `MiniIO/`, `FFmpeg/`, `OpenCV学习指南/`), AI/LLM (`大模型工具全景图/`, `AI常用类库指南/`, `手写大模型/`, `ClaudeCode学习指南/`, `Openclaw学习指南/`), build-from-scratch series (`手写JVM/`, `手写Web容器/`, `手写操作系统/`, `手写数据库/`, `手写浏览器/`, `消息中间件设计/`, `手写游戏引擎/`), `OS_Tutorial/`, `技术文档体系/` | 12 source dirs: `飞书·Agent开发/`, `飞书·Java架构师/`, `飞书·LLM底层/`, `飞书·人工智能/`, `飞书·技术架构/`, `飞书·飞天闪客/`, `飞书·工程化/`, `从0到1设计计算机/`, `语雀·工作与计算机/`, `语雀·人工智能/`, `为知·技术专栏/`, `为知·运维/` |
| `投资/` | `README.md` + `00-七册MOC/` (7 MOC volumes) | `01-我的实盘与成长史/` ~ `07-新手学习路线/` source volumes |
| `工作/` | `README.md` + `实际工作项目/` — contains `摄像头视频方案/` and `智能体管理系统设计/` (with `ruoyi-agent/` code) | `客户跟踪/`, `技术方案/`, `腾讯项目文档/`, `飞书·项目经验/`, `求职与面试/`, `为知·工作记录/`, `飞书周报/` |
| `考证/` | `README.md` + `软考论文/` (9 essays) | `软考-架构师/`, `软考-管理师/`, `腾讯·职场进阶/`, `项目管理文章/`, `微权力下的项目管理/` |
| `家庭/` | (none) | entire base: `人生经历/`, `育儿/`, `个人成长/`, `少儿编程/` |
| `创作/` | `码农打怪升级小说/` | `自媒体与股林武侠/` |

Also private (git-ignored): `_备份元数据/` — relocation manifests, reconciliation notes, and pending-confirmation lists for the 2026-11-07 four-source archive reorganization.

## Embedded Project: ruoyi-agent

Located at `工作/实际工作项目/智能体管理系统设计/ruoyi-agent/`. A Spring Boot 3.x + Vue 3 application based on the RuoYi framework.

**Backend stack:** Spring Boot 3.x, MyBatis Plus 3.5.x, Sa-Token (auth), MySQL 8.0, Redis 6.0, MinIO

**Architecture layers:**
- `controller/` → REST API endpoints
- `service/` → Business logic
- `mapper/` → MyBatis Plus data access (XML mappings in `resources/mapper/`)
- `domain/entity/` → JPA/MyBatis entities

**Frontend:** Vue 3 + Vite + Element Plus at `ruoyi-ui/`
- `src/api/agent/` — API client modules
- `src/views/agent/` — Page components

**Database schema:** `sql/ruoyi_agent.sql`

## Documentation Standards

This repo follows the **Divio four-quadrant documentation system** (documented in `技术/技术文档体系/DOC_SYSTEM.md`):
- **Tutorial** — learning-oriented, hands-on
- **How-to Guide** — task-oriented, solve specific problems
- **Reference** — information-oriented, lookup manual
- **Explanation** — understanding-oriented, background context

One document = one purpose. Don't mix types.

## Document Writing Conventions

- Chinese language for all knowledge base content
- Practical, direct style with code examples
- Structure: scenario → cause analysis → solution
- Second-person voice (你)
