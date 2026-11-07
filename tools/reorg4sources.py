# -*- coding: utf-8 -*-
"""四源备份文件级打乱重组 → 六主题知识库（投资/工作/技术/考证/家庭/创作）。

用法:
  python tools/reorg4sources.py --plan    # 构建分类清单 → _备份元数据/reorg_manifest.json + 控制台报告
  python tools/reorg4sources.py --apply   # 按 manifest 执行: 全量 rename + 共享图 copy + 空目录清理 + 校验

设计: manifest 为全文件级（每个文件的源/目标路径显式列出，含图片分流），apply 只做
rename/copy，无隐式目录搬移，便于对账与回滚。投资四库复用 gen_invest_moc.py 的 RULES。
"""
import json
import re
import shutil
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WS / "tools"))
import gen_invest_moc as GIM  # RULES / EMPTY_DOCS / MOCS（main 有 __main__ 保护，导入安全）

SRC = {
    "yuque": WS / "语雀备份",
    "feishu": WS / "飞书备份",
    "tdoc": WS / "腾讯文档导出",
    "wiz": WS / "为知笔记迁移",
}
META = WS / "library" / "_备份元数据"  # 2026-11-07 晚六库已并入 library/（链接层级见 reorg_relink 后续 shift）

# 投资七册目标目录（目录名 = MOC 文件名去 .md，与 library/投资与交易 七册一一对应）
BOOK_DIR = {k: f"投资/{v['file'][:-3]}" for k, v in GIM.MOCS.items()}

YUQUE_INVEST_LIBS = ["爬坑笔记", "底层逻辑", "交易系统", "八位数花园"]
YUQUE_WHOLE_LIBS = {
    "客户跟踪": "工作/客户跟踪",
    "技术方案": "工作/技术方案",
    "工作-计算机": "技术/语雀·工作与计算机",
    "人工智能": "技术/语雀·人工智能",
    "考试-架构师": "考证/软考-架构师",
    "考试-管理师": "考证/软考-管理师",
    "自媒体学习": "创作/自媒体与股林武侠",
}
YUQUE_SPLIT_LIBS = YUQUE_INVEST_LIBS + ["从零开始"]

FEISHU_WHOLE_SPACES = {
    "Agent开发": "技术/飞书·Agent开发",
    "Java架构师": "技术/飞书·Java架构师",
    "LLM 底层技术原理": "技术/飞书·LLM底层",
    "人工智能": "技术/飞书·人工智能",
    "技术架构": "技术/飞书·技术架构",
    "飞天闪客": "技术/飞书·飞天闪客",
    "从0到1设计一台计算机": "技术/从0到1设计计算机",
    "工程化": "技术/飞书·工程化",
    "人生经历": "家庭/人生经历",
    "项目经验": "工作/飞书·项目经验",
}
# 同名套娃层（搬移后拍掉一层冗余目录）
FLATTEN_SPACES = {"Agent开发", "人生经历", "项目经验"}

WIZ_WHOLE_DIRS = {
    "运维常用": "技术/为知·运维",
    "技术专栏笔记": "技术/为知·技术专栏",
    "微权力下的项目管理": "考证/微权力下的项目管理",
    "项目管理": "考证/项目管理文章",
    "育儿与家庭": "家庭/育儿",
    "个人成长规划": "家庭/个人成长",
    "工作记录": "工作/为知·工作记录",
}
WIZ_INVEST_FILES_01 = [
    "投资笔记.md", "股票账户.md", "书籍学习消费.md", "极客时间消费.md",
    "不可思议的456天-寄正通往监狱大门的外包服务商们.md",
]
WIZ_INVEST_FILES_05 = [
    "50个不同行业企业的发展规划.md", "中国未来商业模式的30个大胆思考.md",
]
WIZ_INTERVIEW_DIR = "面试基础整理"  # 7 篇平铺进 工作/求职与面试/

# ---- 云盘根散件规则（按顺序 first-match）----
CLOUDDISK_MD_RULES = [
    (r"三个认清|五碗面|大势研判", "投资/07-新手学习路线", None),
    (r"JVM|字节码", "技术/飞书·Java架构师", None),
    (r"涨粉10万", "创作/自媒体与股林武侠", "自媒体增长文"),
    (r"Function Calling|MCP 协议", "技术/飞书·Agent开发", None),
    (r"Transformer|蒸馏|大模型|机器学习", "技术/飞书·人工智能", None),
    (r"P11|P12|程序计数器|图像IO", "技术/从0到1设计计算机", None),
    (r"网络|集线器|路由器|阳谋", "技术/从0到1设计计算机", None),
    (r"Kiro|Agent 操作软件", "技术/飞书·Agent开发", None),
    (r"飞书 CLI", "技术/飞书·工程化", None),
    (r"视频与内容平台", "创作/自媒体与股林武侠", "内容平台清单，拿不准"),
]
CLOUDDISK_XLSX_RULES = [
    (r"炒股教程库|搞笑炒股", "投资/01-我的实盘与成长史/账本", None),
    (r"散户5大难", "投资/02-交易心理与悟道", None),
    (r"矿石大宗交易", "投资/01-我的实盘与成长史/账本", "大宗交易学习记录，拿不准"),
    (r"deepseek|批量数据翻译", "技术/飞书·Agent开发", "AI 脚本配套表，拿不准"),
    (r"学习路线", "投资/07-新手学习路线", "学习路线.docx，拿不准"),
]
PERSONAL_DOC_RULES = [
    (r"^交易系统\.md$", BOOK_DIR["03"], None),
    (r"AGI|AI领导力", "技术/飞书·人工智能", None),
    (r"AI Agent 知识库|^知识问答", "技术/飞书·Agent开发", "知识问答.md 拿不准"),
    (r"软件开发行业股票", "投资/05-宏观与行业底层逻辑/行业数据", None),
]
CONG_LING_RULES = [  # 语雀·从零开始（求职备考时期混装）
    (r"^002-基本信息", "家庭/个人成长", "个人基本信息"),
    (r"^003-业务学习|^004-郑州30家公司|^005-面试顺序|^006-|^007-郑州|^013-思路切换",
     "工作/求职与面试", "003 业务学习归类拿不准"),
    (r"^008-|^009-|^010-|^011-|^012-", "技术/从0到1设计计算机", None),
]

# 图片引用扫描（md 内 images/ 相对引用，含 <img src>）
IMG_REF_RE = re.compile(r'\]\((?:\./)?(?:images/[^)\s]+)\)|src="(images/[^"]+)"')
IMG_PATH_RE = re.compile(r"(?:\./)?images/[^)\s\"]+")


def classify_cms_file(rel):  # rel: "云盘/xxx.md" 相对 飞书备份/
    name = rel.rsplit("/", 1)[-1]
    table = CLOUDDISK_MD_RULES if name.endswith(".md") else CLOUDDISK_XLSX_RULES
    for pat, dst, note in table:
        if re.search(pat, name):
            return dst + "/" + name, note
    return None, None


def classify_personal_doc(name):
    for pat, dst, note in PERSONAL_DOC_RULES:
        if re.search(pat, name):
            return dst + "/" + name, note
    return None, None


def classify_congling(name):
    for pat, dst, note in CONG_LING_RULES:
        if re.search(pat, name):
            return dst + "/" + name, note
    return None, None


def rule_key(lib, fname):
    """gen_invest_moc.RULES 的 first-match 匹配器。"""
    for moc_key, matchers in GIM.RULES[lib]:
        for m in matchers:
            if m.startswith("re:"):
                if re.search(m[3:], fname):
                    return moc_key
            elif fname.startswith(m):
                return moc_key
    return None


def scan_md_image_refs(md_path):
    text = md_path.read_text(encoding="utf-8")
    out = []
    for m in IMG_REF_RE.finditer(text):
        seg = IMG_PATH_RE.search(m.group(0))
        if seg:
            out.append(seg.group(0).split("/", 1)[1])
    return out


def _md5(p):
    import hashlib
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def build_plan():
    moves, copies, review, unmatched = [], [], [], []
    seen_dst = {}

    def add(src_rel, dst_rel, note=None, kind="move"):
        if kind == "move" and dst_rel in seen_dst:
            owner = seen_dst[dst_rel]
            if _md5(WS / src_rel) == _md5(WS / owner):
                # 内容完全相同的重复 → 归档留证，不占正位
                dup_dst = "_备份元数据/飞书重复对/" + src_rel.replace("/", "_")
                add(src_rel, dup_dst, note="与 " + owner + " 内容重复（md5 一致）")
                return
            # 同名不同内容 → 加来源路径后缀保留双方
            parts = src_rel.split("/")
            tail = "-".join(parts[-3:-1]) or parts[0]
            dst2 = dst_rel.rsplit(".", 1)[0] + "__" + tail + "." + dst_rel.rsplit(".", 1)[1]
            add(src_rel, dst2, note="与 " + owner + " 同名但内容不同，双保留")
            return
        seen_dst.setdefault(dst_rel, src_rel)
        entry = {"src": src_rel, "dst": dst_rel}
        if note:
            entry["review"] = note
            review.append({"src": src_rel, "dst": dst_rel, "note": note})
        (copies if kind == "copy" else moves).append(entry)

    # ---------- 语雀 ----------
    yq = SRC["yuque"]
    libs = sorted(p.name for p in yq.iterdir() if p.is_dir() and p.name != "_raw")
    for lib in libs:
        lib_dir = yq / lib
        if lib in YUQUE_WHOLE_LIBS:
            dst_root = YUQUE_WHOLE_LIBS[lib]
            for f in lib_dir.rglob("*"):
                if f.is_file():
                    add(f"语雀备份/{lib}/{f.relative_to(lib_dir).as_posix()}",
                        f"{dst_root}/{f.relative_to(lib_dir).as_posix()}")
            continue
        if lib not in YUQUE_SPLIT_LIBS:
            unmatched.append(f"[语雀] 未知库: {lib}")
            continue
        # 拆分库：md 逐篇分类；images 按引用分流；README 进元数据
        img_dest = {}  # image name -> set(dst dir)
        md_entries = []
        for f in sorted(lib_dir.glob("*.md")):
            if f.name == "README.md":
                add(f"语雀备份/{lib}/README.md", f"_备份元数据/语雀库README/{lib}-README.md")
                continue
            if lib in YUQUE_INVEST_LIBS:
                key = rule_key(lib, f.name)
                if key is None:
                    unmatched.append(f"[语雀/{lib}] 未匹配: {f.name}")
                    continue
                dst_dir = BOOK_DIR[key]
            else:  # 从零开始
                dst, note = classify_congling(f.name)
                if dst is None:
                    unmatched.append(f"[语雀/从零开始] 未匹配: {f.name}")
                    continue
                dst_dir = dst.rsplit("/", 1)[0]
                md_note = note
            md_entries.append((f, dst_dir))
            for img in scan_md_image_refs(f):
                img_dest.setdefault(img, set()).add(dst_dir)
        for f, dst_dir in md_entries:
            note = md_note if lib == "从零开始" else None
            add(f"语雀备份/{lib}/{f.name}", f"{dst_dir}/{f.name}", note)
        img_dir = lib_dir / "images"
        if img_dir.is_dir():
            for img in sorted(img_dir.iterdir()):
                if not img.is_file():
                    continue
                dests = img_dest.get(img.name, set())
                if len(dests) == 1:
                    d = next(iter(dests))
                    add(f"语雀备份/{lib}/images/{img.name}", f"{d}/images/{img.name}")
                elif len(dests) > 1:
                    for d in sorted(dests):
                        add(f"语雀备份/{lib}/images/{img.name}", f"{d}/images/{img.name}", kind="copy")
                else:
                    add(f"语雀备份/{lib}/images/{img.name}",
                        f"_备份元数据/未引用图片/{lib}/{img.name}",
                        note="无 md 引用")
    for f in yq.iterdir():
        if f.is_file():
            add(f"语雀备份/{f.name}", f"_备份元数据/语雀-{f.name}")
        elif f.name == "_raw":
            for x in f.rglob("*"):
                if x.is_file():
                    add(f"语雀备份/_raw/{x.relative_to(f).as_posix()}",
                        f"_备份元数据/语雀_raw/{x.relative_to(f).as_posix()}")

    # ---------- 飞书 ----------
    fs = SRC["feishu"]
    cd = fs / "云盘"
    for f in sorted(cd.iterdir()):
        if f.is_file():
            dst, note = classify_cms_file(f"云盘/{f.name}")
            if dst is None:
                unmatched.append(f"[云盘根] 未匹配: {f.name}")
            else:
                add(f"飞书备份/云盘/{f.name}", dst, note)
        elif f.name in ("职业交易员养成之路", "像证券交易员一样思考"):
            dst_root = f"投资/07-新手学习路线/{f.name}"
            for x in f.rglob("*"):
                if x.is_file():
                    add(f"飞书备份/云盘/{f.name}/{x.relative_to(f).as_posix()}",
                        f"{dst_root}/{x.relative_to(f).as_posix()}")
        elif f.name == "散户五大难":
            for x in f.rglob("*"):
                if x.is_file():
                    if x.suffix == ".xlsx":
                        add(f"飞书备份/云盘/散户五大难/{x.name}",
                            f"投资/01-我的实盘与成长史/账本/{x.name}")
                    else:
                        add(f"飞书备份/云盘/散户五大难/{x.name}",
                            f"投资/02-交易心理与悟道/{x.name}")
        elif f.name == "飞书 aily":
            for x in f.rglob("*.md"):
                add(f"飞书备份/云盘/飞书 aily/{x.relative_to(f).as_posix()}",
                    f"工作/飞书周报/{x.name}")
        else:
            unmatched.append(f"[云盘] 未知条目: {f.name}")
    kb = fs / "知识库"
    for space in sorted(p.name for p in kb.iterdir() if p.is_dir()):
        space_dir = kb / space
        if space in FEISHU_WHOLE_SPACES:
            dst_root = FEISHU_WHOLE_SPACES[space]
            for f in space_dir.rglob("*"):
                if not f.is_file():
                    continue
                rel = f.relative_to(space_dir).as_posix()
                if space in FLATTEN_SPACES:
                    parts = rel.split("/", 1)
                    if len(parts) == 2 and parts[0] == space:
                        rel = parts[1]  # 拍掉同名冗余层
                add(f"飞书备份/知识库/{space}/{f.relative_to(space_dir).as_posix()}",
                    f"{dst_root}/{rel}")
        elif space == "个人文档库":
            for f in sorted(space_dir.iterdir()):
                if f.is_file():
                    dst, note = classify_personal_doc(f.name)
                    if dst is None:
                        unmatched.append(f"[个人文档库] 未匹配: {f.name}")
                    else:
                        add(f"飞书备份/知识库/个人文档库/{f.name}", dst, note)
        elif space == "底层逻辑":
            add(f"飞书备份/知识库/底层逻辑/首页.md",
                "_备份元数据/飞书空壳/底层逻辑-首页.md",
                note="空间仅剩首页壳")
        elif space == "少儿编程":
            for f in space_dir.rglob("*"):
                if f.is_file():
                    add(f"飞书备份/知识库/少儿编程/{f.relative_to(space_dir).as_posix()}",
                        f"家庭/少儿编程/{f.name}")
        else:
            unmatched.append(f"[飞书知识库] 未知空间: {space}")
    for f in fs.iterdir():
        if f.is_file():
            add(f"飞书备份/{f.name}", f"_备份元数据/飞书-{f.name}")

    # ---------- 腾讯 ----------
    td = SRC["tdoc"]
    for top in sorted(p.name for p in td.iterdir() if p.is_dir()):
        if top == "1工作记录":
            for f in (td / top).rglob("*"):
                if f.is_file():
                    add(f"腾讯文档导出/{top}/{f.relative_to(td / top).as_posix()}",
                        f"工作/腾讯项目文档/{f.relative_to(td / top).as_posix()}")
        elif top == "3职场进阶":
            for f in (td / top).rglob("*"):
                if f.is_file():
                    add(f"腾讯文档导出/{top}/{f.relative_to(td / top).as_posix()}",
                        f"考证/腾讯·职场进阶/{f.relative_to(td / top).as_posix()}")
        elif top == "2炒股养家":
            for f in (td / top).rglob("*"):
                if f.is_file():
                    add(f"腾讯文档导出/{top}/{f.name}", f"投资/01-我的实盘与成长史/账本/{f.name}")
        else:
            unmatched.append(f"[腾讯] 未知目录: {top}")
    for f in td.iterdir():
        if f.is_file():
            add(f"腾讯文档导出/{f.name}", f"_备份元数据/腾讯-{f.name}")

    # ---------- 为知 ----------
    wz = SRC["wiz"]
    for top in sorted(p.name for p in wz.iterdir() if p.is_dir()):
        if top == "投资与理财":
            for f in sorted((wz / top).glob("*.md")):
                if f.name in WIZ_INVEST_FILES_01:
                    add(f"为知笔记迁移/{top}/{f.name}", f"{BOOK_DIR['01']}/{f.name}")
                elif f.name in WIZ_INVEST_FILES_05:
                    add(f"为知笔记迁移/{top}/{f.name}", f"{BOOK_DIR['05']}/{f.name}")
                else:
                    unmatched.append(f"[为知/投资与理财] 未匹配: {f.name}")
        elif top == WIZ_INTERVIEW_DIR:
            for f in sorted((wz / top).rglob("*.md")):
                add(f"为知笔记迁移/{top}/{f.name}", f"工作/求职与面试/{f.name}")
        elif top in WIZ_WHOLE_DIRS:
            dst_root = WIZ_WHOLE_DIRS[top]
            for f in (wz / top).rglob("*"):
                if f.is_file():
                    add(f"为知笔记迁移/{top}/{f.relative_to(wz / top).as_posix()}",
                        f"{dst_root}/{f.relative_to(wz / top).as_posix()}")
        else:
            unmatched.append(f"[为知] 未知目录: {top}")
    for f in wz.iterdir():
        if f.is_file():
            add(f"为知笔记迁移/{f.name}", f"_备份元数据/为知-{f.name}")

    return moves, copies, review, unmatched


def report(moves, copies, review, unmatched):
    n_move = len(moves)
    n_copy = len(copies)
    print(f"move 条目: {n_move}  copy(共享图) 条目: {n_copy}  待人工确认: {len(review)}  未匹配: {len(unmatched)}")
    by_root = {}
    for e in moves:
        root = e["dst"].split("/", 1)[0]
        by_root[root] = by_root.get(root, 0) + 1
    for k in sorted(by_root):
        print(f"  → {k}: {by_root[k]}")
    if review:
        print("\n-- 待人工确认（已给最优猜测）--")
        for r in review:
            print(f"  {r['src']}  →  {r['dst']}   # {r['note']}")
    if unmatched:
        print("\n-- 未匹配（必须清零才能 apply）--")
        for u in unmatched:
            print("  " + u)
    return not unmatched


def check_dst_collision_with_existing(moves):
    """目标路径不得与六库/现有目录已有文件冲突。"""
    bad = []
    for e in moves:
        p = WS / e["dst"]
        if p.exists():
            bad.append(f"{e['dst']} 已存在")
    return bad


def apply(moves, copies):
    n_ok = 0
    for e in moves:
        src, dst = WS / e["src"], WS / e["dst"]
        if not src.is_file():
            raise SystemExit(f"[中止] 源缺失: {e['src']}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise SystemExit(f"[中止] 目标已存在: {e['dst']}")
        src.rename(dst)
        n_ok += 1
    for e in copies:
        src, dst = WS / e["src"], WS / e["dst"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)
        n_ok += 1
    print(f"已执行 move+copy {n_ok} 条")

    # 清理四源空目录（只删空目录，防误删）
    removed = 0
    for root in SRC.values():
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in list(os_walk_bottomup(root)):
            if not any(dirpath.iterdir()):
                dirpath.rmdir()
                removed += 1
        if root.exists() and any(root.iterdir()):
            leftover = [str(p) for p in root.rglob("*") if p.is_file()]
            raise SystemExit(f"[中止] {root.name} 仍有残留文件: {leftover[:5]}")
        if root.exists():
            root.rmdir()
    print(f"清理空目录 {removed} 个，四源目录已移除")


def os_walk_bottomup(root):
    dirs = [d for d in root.rglob("*") if d.is_dir()]
    dirs.sort(key=lambda p: -len(p.parts))
    return [(d, [], []) for d in dirs]


def verify(moves, copies):
    # 2026-11-07 晚六库已并入 library/，manifest 记录的是当时仓库根口径
    miss = [e["dst"] for e in moves if not (WS / "library" / e["dst"]).is_file()]
    dup = [e for e in copies if not (WS / "library" / e["dst"]).is_file()]
    if miss:
        raise SystemExit(f"[校验失败] 目标缺失 {len(miss)}: {miss[:5]}")
    if dup:
        raise SystemExit(f"[校验失败] 复制目标缺失: {dup[:5]}")
    # 图片引用完整性：六库内所有 md 的 images/ 引用必须命中同目录
    img_re = re.compile(r"!\[[^\]]*\]\(((?:\.{1,2}/)?images/[^)\s]+)\)|src=\"((?:\.{1,2}/)?images/[^\"]+)\"")
    bad = []
    for kb in ["library/投资", "library/工作", "library/技术", "library/考证", "library/家庭", "library/创作"]:
        for md in (WS / kb).rglob("*.md"):
            text = md.read_text(encoding="utf-8")
            for m in img_re.finditer(text):
                ref = m.group(1) or m.group(2)
                if not (md.parent / ref).is_file():
                    bad.append(f"{md.relative_to(WS)} → {ref}")
    if bad:
        raise SystemExit(f"[校验失败] 断图 {len(bad)}:\n  " + "\n  ".join(bad[:10]))
    print(f"[校验通过] {len(moves)} move + {len(copies)} copy 全部就位；六库图片引用零断链")


def main():
    plan_path = META / "reorg_manifest.json"
    if "--plan" in sys.argv:
        META.mkdir(exist_ok=True)
        moves, copies, review, unmatched = build_plan()
        ok = report(moves, copies, review, unmatched)
        existing = check_dst_collision_with_existing(moves)
        if existing:
            ok = False
            print("\n-- 目标已存在冲突 --")
            for b in existing[:10]:
                print("  " + b)
        if ok:
            plan_path.write_text(json.dumps(
                {"moves": moves, "copies": copies, "review": review},
                ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"\nmanifest 已写入 {plan_path}")
        sys.exit(0 if ok else 1)
    if "--verify" in sys.argv:
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        verify(data["moves"], data["copies"])
        return
    if "--apply" in sys.argv:
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        apply(data["moves"], data["copies"])
        verify(data["moves"], data["copies"])
        return
    print(__doc__)


if __name__ == "__main__":
    main()
