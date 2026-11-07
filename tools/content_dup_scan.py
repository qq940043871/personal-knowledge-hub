# -*- coding: utf-8 -*-
"""技术库查重扫描器：md5 精确重复 + minhash 近似重复。

用法:
  python tools/content_dup_scan.py <root1> [root2 ...] [--min 0.55] [--top 40]
  # root 为仓库根相对目录（可多个，跨目录比对）
输出: 精确重复组 + 近似重复对（相似度降序），路径为仓库根相对。
原理: 正文归一化（剥代码围栏/图片/链接/空白，留标题与散文）→ 字符8元组集合
      → 16个minhash签名估计 Jaccard，候选对再算精确 Jaccard 复核。
"""
import hashlib
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
M = 16
MASK = (1 << 64) - 1
SEEDS = [0x9E3779B97F4A7C15 ^ (i * 0xBF58476D1CE4E5B9) for i in range(M)]

FENCE_RE = re.compile(r"```.*?```", re.S)
IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
HTML_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def normalize(text):
    text = FENCE_RE.sub(" ", text)
    text = IMG_RE.sub(" ", text)
    text = LINK_RE.sub(r"\1", text)
    text = HTML_RE.sub(" ", text)
    text = re.sub(r"[#*`>\-|=_~\[\]()]", " ", text)
    return WS_RE.sub("", text)


def shingles(norm, k=8):
    if len(norm) < k:
        return set()
    return {norm[i:i + k] for i in range(0, len(norm) - k + 1, 2)}


def signature(hs):
    sig = [MASK] * M
    for h in hs:
        for i, seed in enumerate(SEEDS):
            v = ((h * seed) ^ (h >> 29)) & MASK
            if v < sig[i]:
                sig[i] = v
    return sig


def scan(roots, min_sim, top):
    files = []
    for r in roots:
        base = WS / r
        if not base.is_dir():
            print(f"[跳过] 目录不存在: {r}")
            continue
        for f in base.rglob("*.md"):
            if f.stat().st_size < 200:  # 墓碑/存根
                continue
            files.append(f)
    print(f"扫描 {len(files)} 个 md（>=200B）")

    exact = {}
    metas = []
    for f in files:
        raw = f.read_bytes()
        exact.setdefault(hashlib.md5(raw).hexdigest(), []).append(f.relative_to(WS).as_posix())
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", "replace")
        norm = normalize(text)
        hs = {int.from_bytes(hashlib.blake2b(s.encode("utf-8"), digest_size=8).digest(), "big")
              for s in shingles(norm)}
        metas.append((f.relative_to(WS).as_posix(), len(norm), signature(hs) if hs else None,
                      {int.from_bytes(hashlib.blake2b(s.encode("utf-8"), digest_size=8).digest(), "big")
                       for s in shingles(norm)}))
    print("-- 精确重复（md5 相同）--")
    n_exact = 0
    for h, paths in exact.items():
        if len(paths) > 1:
            n_exact += 1
            print("  [完全相同] " + "  ⇔  ".join(paths))
    print(f"  共 {n_exact} 组")

    print("-- 近似重复（minhash 预筛 + 精确 Jaccard 复核）--")
    cands = []
    n = len(metas)
    for i in range(n):
        pa, la, sa, ha = metas[i]
        if sa is None:
            continue
        for j in range(i + 1, n):
            pb, lb, sb, hb = metas[j]
            if sb is None:
                continue
            if la == 0 or lb == 0:
                continue
            r = min(la, lb) / max(la, lb)
            if r < 0.25:
                continue
            eq = sum(1 for a, b in zip(sa, sb) if a == b)
            if eq / M >= min_sim - 0.15:  # 预筛放宽
                inter = len(ha & hb)
                jac = inter / max(1, len(ha | hb))
                if jac >= min_sim:
                    cands.append((jac, pa, pb))
    cands.sort(reverse=True)
    for jac, pa, pb in cands[:top]:
        print(f"  [{jac:.2f}] {pa}")
        print(f"         ⇔ {pb}")
    print(f"  共 {len(cands)} 对（显示前 {min(top, len(cands))}）")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    min_sim = 0.55
    top = 40
    for a in sys.argv[1:]:
        if a.startswith("--min="):
            min_sim = float(a.split("=")[1])
        if a.startswith("--top="):
            top = int(a.split("=")[1])
    if not args:
        print(__doc__)
        return
    scan(args, min_sim, top)


if __name__ == "__main__":
    main()
