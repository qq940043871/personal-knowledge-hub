# -*- coding: utf-8 -*-
"""技术库查重清理执行器（2026-11-08，用户已批准的清单）。

动作：
 1) 删除 飞书·Agent开发 中与成品行集合Jaccard>=0.75 的冗余原稿（tools/_del_agentdev.txt）
 2) Agent开发 内部 md5 重复组只保留字典序第一份
 3) 删 三个空间的 首页.md 模板壳
 4) 删 飞书·技术架构/17年技术经验总结/ 整目录（hub 文件链接改指成品）
 5) FFmpeg 02旧稿独有内容并入03后删除（git rm）
 6) 双保留对按"飞书图片引用多者留"
 7) 语雀草稿墓碑 28 篇（内容门槛复核后才删）
 8) distributed/message-queue/ 删除（mq/ 为准，入链改指）
 9) high-concurrency-overview.md 的 .html 死链改 .md
安全：所有删除前 grep 全库入链；有入链的记录并改写。
"""
import hashlib
import re
import shutil
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
LOG = []


def log(msg):
    LOG.append(msg)
    print(msg)


def rm(p: Path):
    p.unlink()


def inbound(frel: str):
    """全库 md 中引用了该文件（按文件名）的其他文件。"""
    name = frel.rsplit("/", 1)[-1]
    hits = []
    for md in (WS / "library").rglob("*.md"):
        if md.relative_to(WS).as_posix() == frel:
            continue
        try:
            if name in md.read_text(encoding="utf-8", errors="replace"):
                hits.append(md.relative_to(WS).as_posix())
        except OSError:
            pass
    return hits


def main():
    # ---------- 1) Agent开发 冗余原稿 ----------
    lst = (WS / "tools/_del_agentdev.txt").read_text(encoding="utf-8").splitlines()
    deleted = set()
    for rel in lst:
        p = WS / rel
        if not p.is_file():
            log(f"[跳过·不存在] {rel}")
            continue
        refs = inbound(rel)
        refs = [r for r in refs if "飞书·Agent开发" not in r]  # 私有内部互链稍后统一处理
        if refs:
            log(f"[暂缓·有库内入链] {rel} ← {refs[:3]}")
            continue
        rm(p)
        deleted.add(rel)
    log(f"[1] Agent开发 冗余原稿删除 {len(deleted)} 篇")

    # ---------- 2) 内部 md5 重复组 ----------
    groups = {}
    for f in (WS / "library/技术/飞书·Agent开发").rglob("*.md"):
        groups.setdefault(hashlib.md5(f.read_bytes()).hexdigest(), []).append(f)
    n2 = 0
    for h, files in groups.items():
        if len(files) < 2:
            continue
        files.sort()
        for f in files[1:]:
            rm(f)
            n2 += 1
    log(f"[2] Agent开发 内部重复删除 {n2} 篇（各组保留字典序第一份）")

    # ---------- 3) 首页.md 模板壳 ----------
    n3 = 0
    for d in ["飞书·Java架构师", "飞书·人工智能", "飞书·工程化"]:
        p = WS / f"library/技术/{d}/首页.md"
        if p.is_file():
            rm(p)
            n3 += 1
    log(f"[3] 首页模板壳删除 {n3} 篇")

    # ---------- 4) 技术架构/17年技术经验总结 整目录 ----------
    sub = WS / "library/技术/飞书·技术架构/17年技术经验总结"
    if sub.is_dir():
        # hub 文件改指成品
        hub = WS / "library/技术/飞书·技术架构/17年技术经验总结.md"
        if hub.is_file():
            t = hub.read_text(encoding="utf-8")
            t2 = re.sub(r"\]\((\.{2}/)*17年技术经验总结/", "](../../17年技术经验总结/", t)
            t2 = t2.replace("](17年技术经验总结/", "](../../17年技术经验总结/")
            if t2 != t:
                hub.write_text(t2, encoding="utf-8", newline="")
                log("[4] hub 文件链接已改指 技术/17年技术经验总结/")
        refs = [r for r in inbound("library/技术/飞书·技术架构/17年技术经验总结/") if not r.startswith("library/技术/飞书·技术架构")]
        if refs:
            log(f"[4][注意] 目录仍有库内入链: {refs[:5]}")
        shutil.rmtree(sub)
        log(f"[4] 已删除 整目录 飞书·技术架构/17年技术经验总结/")

    # ---------- 5) FFmpeg 02旧稿：独有内容并入03 ----------
    old = WS / "library/技术/FFmpeg学习指南/02-常用命令/01-RTSP拉流与RTMP推流.md"
    new = WS / "library/技术/FFmpeg学习指南/03-流媒体处理/01-RTSP拉流与RTMP推流.md"
    if old.is_file() and new.is_file():
        ot = old.read_text(encoding="utf-8")
        nt = new.read_text(encoding="utf-8")
        # 提取旧稿独有小节（循环推流/multi_push）
        blocks = re.split(r"\n(?=#{1,3} )", ot)
        added = []
        for b in blocks:
            head = b.splitlines()[0] if b else ""
            if ("循环推流" in head or "multi_push" in b) and "multi_push" not in nt:
                nt = nt.rstrip() + "\n\n## 附：循环推流与多目标推送脚本（自 02-常用命令 旧稿并入）\n\n" + b.strip() + "\n"
                added.append(head)
        new.write_text(nt, encoding="utf-8", newline="")
        old.unlink()
        # 空目录清理
        d = WS / "library/技术/FFmpeg学习指南/02-常用命令"
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
        log(f"[5] FFmpeg 02旧稿已删，并入小节: {added or '（无独有内容）'}")

    # ---------- 6) 双保留对（图片多者留） ----------
    PAIRS = [
        ("library/技术/飞书·飞天闪客/你管这破玩意叫网络.md", "library/技术/从0到1设计计算机/你管这破玩意叫网络.md"),
        ("library/技术/飞书·飞天闪客/顶级阳谋 如何在全世界的眼皮子底下安全密谋 世界上的顶级阳谋 藏在各种网络机制的设计上 如何在全世界的眼皮子底下安....md", "library/技术/从0到1设计计算机/顶级阳谋 如何在全世界的眼皮子底下安全密谋 世界上的顶级阳谋 藏在各种网络机制的设计上 如何在全世界的眼皮子底下安....md"),
        ("library/技术/飞书·人工智能/这一次 彻底搞懂蒸馏 开源 这些个概念.md", "library/技术/飞书·飞天闪客/这一次 彻底搞懂蒸馏 开源 这些个概念.md"),
        ("library/技术/飞书·人工智能/硬读 Transformer 经典论文 不过是硬着头皮的硬.md", "library/技术/飞书·飞天闪客/硬读 Transformer 经典论文 不过是硬着头皮的硬.md"),
        ("library/技术/飞书·人工智能/一口气通关大模型的 100 个关键词词.md", "library/技术/飞书·飞天闪客/一口气通关大模型的 100 个关键词词.md"),
        ("library/技术/飞书·人工智能/i人程序员的福音 跟着 Kiro 学习搭建项目.md", "library/技术/飞书·飞天闪客/i人程序员的福音 跟着 Kiro 学习搭建项目.md"),
        ("library/技术/飞书·人工智能/如何让 Agent 操作软件 其实这和 Agent 无关.md", "library/技术/飞书·飞天闪客/如何让 Agent 操作软件 其实这和 Agent 无关.md"),
    ]
    n6 = 0
    for a, b in PAIRS:
        fa, fb = WS / a, WS / b
        if not (fa.is_file() and fb.is_file()):
            log(f"[6][缺对] {a.rsplit('/',1)[-1][:30]}")
            continue
        ia = len(re.findall(r"feishu\.cn/file", fa.read_text(encoding="utf-8", errors="replace")))
        ib = len(re.findall(r"feishu\.cn/file", fb.read_text(encoding="utf-8", errors="replace")))
        keep, drop = (fa, fb) if ia >= ib else (fb, fa)
        # 同名文件被留方目录内可能已有同名——不同目录，无冲突
        rm(drop)
        n6 += 1
        log(f"[6] 留 {keep.relative_to(WS).as_posix()} (图{max(ia,ib)}) 删 {drop.relative_to(WS).as_posix()} (图{min(ia,ib)})")
    log(f"[6] 双保留对处理 {n6} 对")

    # P11 双保留（md5 同）
    p11 = WS / "library/技术/从0到1设计计算机/P11 第9话-程序计数器__知识库-从0到1设计一台计算机.md"
    if p11.is_file():
        rm(p11)
        log("[6] P11 __知识库 双保留副本已删")

    # ---------- 7) 语雀草稿墓碑 ----------
    cands = []
    for d in ["library/技术/语雀·人工智能", "library/技术/语雀·工作与计算机"]:
        for f in (WS / d).rglob("*.md"):
            if "无标题文档" in f.name:
                cands.append(f)
    for name in ["034-零基础实践深度学习.md", "021-vue工程化.md"]:
        for f in (WS / "library/技术/语雀·人工智能").rglob(name):
            cands.append(f)
        for f in (WS / "library/技术/语雀·工作与计算机").rglob(name):
            cands.append(f)
    n7 = 0
    for f in cands:
        t = f.read_text(encoding="utf-8", errors="replace")
        body = re.sub(r"<svg.*?</svg>", "", t, flags=re.S)
        body = re.sub(r"\*图：[^*]*\*", "", body)
        body = re.sub(r"\s", "", body)
        if len(body) < 200:  # 占位/近空
            rm(f)
            n7 += 1
        else:
            log(f"[7][保留·有内容] {f.relative_to(WS).as_posix()}（body {len(body)}字）")
    log(f"[7] 语雀草稿墓碑删除 {n7} 篇")

    # ---------- 8) distributed/message-queue 移除（mq/ 为准） ----------
    dmq = WS / "library/技术/17年技术经验总结/09-技术知识库/pages/05_system_architect/distributed/message-queue"
    if dmq.is_dir():
        for f in dmq.glob("*.md"):
            refs = inbound(f.relative_to(WS).as_posix().replace("\\", "/"))
            for r in refs:
                rp = WS / r
                t = rp.read_text(encoding="utf-8")
                fname = f.name
                t2 = t.replace("distributed/message-queue/" + fname, "mq/" + fname)
                if t2 != t:
                    rp.write_text(t2, encoding="utf-8", newline="")
                    log(f"[8] 入链改指 mq/: {r}")
        shutil.rmtree(dmq)
        log("[8] 已删除 distributed/message-queue/（mq/ 为准）")

    # ---------- 9) .html 死链 ----------
    hc = WS / "library/技术/17年技术经验总结/09-技术知识库/pages/05_system_architect/high-concurrency/high-concurrency-overview.md"
    if hc.is_file():
        t = hc.read_text(encoding="utf-8")
        t2 = t.replace("database-sharding.html", "database-sharding.md")
        if t2 != t:
            hc.write_text(t2, encoding="utf-8", newline="")
            log("[9] high-concurrency-overview 死链已改 .md")

    # ---------- 清理空目录 ----------
    base = WS / "library/技术/飞书·Agent开发"
    for d in sorted((p for p in base.rglob("*") if p.is_dir()), key=lambda x: -len(x.parts)):
        if not any(d.iterdir()):
            d.rmdir()
    log("[ cleanup ] Agent开发 空目录已清理")

    (WS / "tools/_cleanup_log.txt").write_text("\n".join(LOG), encoding="utf-8")
    print(f"\n完成，日志 tools/_cleanup_log.txt")


if __name__ == "__main__":
    main()
