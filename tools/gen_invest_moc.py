# -*- coding: utf-8 -*-
# ============================================================
# DEPRECATED（2026-11-07）：四源备份已按主题打乱重组到根目录六库
# （投资/工作/技术/考证/家庭/创作），源目录“语雀备份/”已不存在，
# 本脚本不可再运行。RULES/EMPTY_DOCS/SECTION_SUFFIX 已由
# tools/reorg4sources.py 复用为分类规则；已生成的 library/投资与交易/
# 七册 MOC 的链接已由 tools/reorg_relink.py 改指 ../../投资/0X-* 目录。
# 保留本文件仅作历史记录与规则出处。
# ============================================================
"""生成 library/投资与交易/ 的 7 个 MOC 文件。

原则：MOC 只做索引不搬文件，链接全部指向四个语雀备份库的原文。
分组规则由 RULES 定义（first-match-wins），运行后必须零未归类才算通过。
"""
import os
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
YUQUE = WS / "语雀备份"
OUT = WS / "library" / "投资与交易"

# ---------------- 分组规则 ----------------
# 每库一组有序规则：(moc_key, [匹配器])，匹配器 "re:xxx" 为正则，否则为文件名前缀
RULES = {
    "爬坑笔记": [
        ("01", ["001-", "002-", "004-", "005-", "016-", "017-", "020-", "023-", "024-",
                 "042-", "043-", "044-", "046-", "048-", "049-", "050-", "051-", "052-",
                 "054-", "055-", "056-", "057-", "058-", "059-", "060-", "061-", "062-",
                 "063-", "156-", "177-", "179-"]),
        ("02", ["007-", "009-", "010-", "019-", "028-", "040-", "064-", "065-", "066-",
                 "067-", "068-", "069-", "070-", "073-", "075-", "076-", "078-", "079-",
                 "080-", "081-", "082-", "083-", "133-", "155-", "157-", "158-", "175-",
                 "178-", "180-", "182-", "183-", "184-", "185-", "186-", "187-"]),
        ("03", ["003-", "014-", "031-", "032-", "041-", "047-", "071-", "072-", "074-",
                 "077-", "084-", "085-", "086-", "121-", "122-", "123-", "124-", "125-",
                 "126-", "127-", "128-", "129-", "130-", "131-", "132-", "134-", "135-",
                 "136-", "137-", "138-", "139-", "140-", "141-", "142-", "143-", "144-",
                 "145-", "146-", "147-", "148-", "150-", "151-", "152-", "153-", "159-",
                 "160-", "161-", "162-", "163-", "164-", "165-", "176-"]),
        ("04", ["120-", "154-", "166-", "167-", "168-", "169-", "170-", "171-", "172-",
                 "173-", "174-", "188-", "189-", "190-", "191-"]),
        ("05", ["006-", "011-", "012-", "013-", "015-", "018-", "021-", "022-", "025-",
                 "026-", "027-", "029-", "030-", "035-", "036-", "037-", "053-", "087-",
                 "181-"]),
        ("06", ["008-", "033-", "034-", "039-", "045-", "149-", "192-", "193-", "194-",
                 "195-", "196-", "197-", "198-", "199-", "200-", "201-", "202-", "203-",
                 "204-", "205-", "206-", "207-", "208-", "209-", "210-"]),
        ("07", ["038-", "088-", "089-", "090-", "091-", "092-", "093-", "094-", "095-",
                 "096-", "097-", "098-", "099-", "100-", "101-", "102-", "103-", "104-",
                 "105-", "106-", "107-", "108-", "109-", "110-", "111-", "112-", "113-",
                 "114-", "115-", "116-", "117-", "118-", "119-"]),
    ],
    "交易系统": [
        ("01", ["001-", "003-", "004-", "005-", "006-", "007-", "010-", "073-", "081-",
                 "087-", "089-", "090-", "092-"]),
        ("02", ["002-", "008-", "009-", "011-", "012-", "013-", "014-", "016-", "019-",
                 "020-", "021-", "046-", "074-", "075-", "076-", "079-", "080-", "085-",
                 "091-"]),
        ("03", ["015-", "017-", "023-", "027-", "028-", "032-", "036-", "037-", "038-",
                 "039-", "042-", "043-", "044-", "057-", "058-", "059-", "060-", "063-",
                 "064-", "071-", "082-", "083-", "084-", "086-", "088-"]),
        ("04", ["022-", "024-", "025-", "026-", "029-", "030-", "031-", "033-", "034-",
                 "035-", "040-", "041-", "045-", "047-", "048-", "049-", "050-", "051-",
                 "052-", "053-", "054-", "055-", "056-", "061-", "062-", "065-", "066-",
                 "067-", "068-", "069-", "070-", "072-", "077-", "078-"]),
        ("05", ["018-"]),
    ],
    "八位数花园": [
        ("02", ["001-", "003-", "004-", "005-", "006-", "007-", "009-", "010-", "011-",
                 "012-", "013-", "017-", "018-", "020-", "021-", "023-", "025-", "026-",
                 "027-", "028-", "032-", "033-", "034-", "036-", "038-", "039-", "040-",
                 "043-", "045-", "048-", "051-", "055-", "056-", "058-", "060-", "061-",
                 "062-"]),
        ("03", ["002-", "008-", "014-", "015-", "016-", "019-", "022-", "024-", "029-",
                 "030-", "031-", "035-", "037-", "041-", "042-", "044-", "046-", "047-",
                 "049-", "050-", "052-", "053-", "054-", "057-", "059-"]),
    ],
    "底层逻辑": [
        ("05", ["re:宏观及", "re:行业解析", "re:咖啡赛道", "re:微短剧", "re:外卖战争",
                 "re:出海", "re:Spacex", "re:元宇宙", "re:虚拟货币", "re:数字人民币",
                 "re:腾讯、苹果", "re:财富管理", "re:聊聊加盟", "re:繁花", "re:Sora",
                 "re:三体版权"]),
        ("06", ["re:方法论", "re:选股逻辑", "re:选基逻辑", "re:猪周期", "re:三个汉堡",
                 "re:慢慢变富"]),
        ("02", ["re:毒鸡汤"]),
    ],
}

LIBS = ["爬坑笔记", "底层逻辑", "交易系统", "八位数花园"]

# ---------------- MOC 定义 ----------------
MOCS = {
    "01": {
        "file": "01-我的实盘与成长史.md",
        "title": "我的实盘与成长史",
        "intro": (
            "这里是**我自己写的**东西：账户、总结、心路、规划——不是课程笔记，是亲身经历。\n"
            "回看顺序建议：先看「爬坑笔记 1-3」认识当年的坑，再看年度总结看轨迹，最后看 2026 方案看现在的打法。"
        ),
        "sections": [
            ("语雀·爬坑笔记——踩坑、心路与总结", "爬坑笔记",
             "042-044 三篇「爬坑笔记」是自传体核心；054-063 是 2023-2025 的年度/月度复盘链。"),
            ("语雀·交易系统——重启与执行", "交易系统",
             "2026 方案/执行/预案三件套 + 月度总结，是当下正在用的作战记录。"),
            ("资产与账本（散落在各备份中的孤本）", None, None),
        ],
        "external": [
            ("腾讯文档·资产负债分析表（xlsx，敏感勿外传）", "../../腾讯文档导出/2炒股养家/资产负债分析表.xlsx"),
            ("为知·投资笔记", "../../为知笔记迁移/投资与理财/投资笔记.md"),
            ("为知·股票账户", "../../为知笔记迁移/投资与理财/股票账户.md"),
            ("为知·书籍学习消费", "../../为知笔记迁移/投资与理财/书籍学习消费.md"),
            ("为知·极客时间消费", "../../为知笔记迁移/投资与理财/极客时间消费.md"),
            ("为知·资产负债表", "../../为知笔记迁移/个人成长规划/资产负债表.md"),
            ("为知·一个IT工薪族的4年奋斗成果", "../../为知笔记迁移/个人成长规划/一个IT工薪族的4年奋斗成果.md"),
            ("为知·不可思议的456天", "../../为知笔记迁移/投资与理财/不可思议的456天-寄正通往监狱大门的外包服务商们.md"),
        ],
    },
    "02": {
        "file": "02-交易心理与悟道.md",
        "title": "交易心理与悟道",
        "intro": (
            "交易是一场心理游戏——这一册收的是**心态、认知、境界**类的文章。\n"
            "「八位数花园」63 篇几乎全是这个频道，是本册主力；柚子系游资的心法语录也在这里。"
        ),
        "sections": [
            ("语雀·八位数花园——交易心理专辑", "八位数花园", "作者死磕交易15年的感悟流，几乎篇篇可读。"),
            ("语雀·交易系统——认知与世界观", "交易系统", "交易世界观、散户亏损本质、悟道、庄家收割的真相。"),
            ("语雀·爬坑笔记——心法与境界", "爬坑笔记", "十大境界、赢家思维、武侠秘籍系列（九阳神功/易筋经等）。"),
            ("语雀·底层逻辑——杂谈", "底层逻辑", None),
        ],
    },
    "03": {
        "file": "03-交易系统与实战战法.md",
        "title": "交易系统与实战战法",
        "intro": (
            "**怎么干**的部分：交易系统的搭建、具体战法、技术细节。\n"
            "核心资产是爬坑笔记里的「援军战法」完整体系（121-153 号），以及交易系统库里的短线干货。\n"
            "连线实录里的实战干货（盈亏比、震仓、低吸）也归在本册。"
        ),
        "sections": [
            ("语雀·爬坑笔记——援军战法全体系", "爬坑笔记",
             "121-128 是七要素（题材/复盘/逻辑/筹码/援军/时机/对手），136-143 是八大形态战法，150-152 是心法与详解。"),
            ("语雀·交易系统——短线实战干货", "交易系统",
             "盈亏比/胜率/盘感、震仓、低吸、放量判读、交易流程。"),
            ("语雀·八位数花园——系统与执行", "八位数花园",
             "从 0 到 1 组建交易系统、1-2-3 法则、大小周期配合、波段精髓。"),
        ],
    },
    "04": {
        "file": "04-游资与高手实录.md",
        "title": "游资与高手实录",
        "intro": (
            "向打过仗的人学习：**柚子系游资**（赵老哥、炒股养家、92科比……）的心法合集，\n"
            "以及 2025-2026 抖音连线的大毛哥/二万哥/野人哥实录——按时间排的盘中复盘，是第一手的市场情绪记录。"
        ),
        "sections": [
            ("语雀·爬坑笔记——柚子（游资）人物系列", "爬坑笔记", "九位知名游资（退学炒股/Asking/92科比/小鳄鱼/独股一箭/赵老哥/炒股养家等）的心法，附手法知识点与交易员课。",
             ["120-", "154-", "166-", "167-", "168-", "169-", "170-", "171-", "172-", "173-", "174-"]),
            ("语雀·交易系统——抖音连线实录", "交易系统", "大毛哥、二万哥、野人哥，按日期排序的连线笔记。", None),
            ("语雀·爬坑笔记——抖音财经课与交易员课", "爬坑笔记", None,
             ["188-", "189-", "190-", "191-"]),
        ],
    },
    "05": {
        "file": "05-宏观与行业底层逻辑.md",
        "title": "宏观与行业底层逻辑",
        "intro": (
            "看懂盘面之前先看懂世界：宏观政策、行业赛道、商业逻辑。\n"
            "主力是语雀「底层逻辑」库的**宏观及商业环境**系列（黄金/关税/化债/AI 时代…），\n"
            "配合爬坑笔记里的十五五规划与软件行业分析。"
        ),
        "sections": [
            ("语雀·底层逻辑——宏观及商业环境", "底层逻辑", "一位职业投资人的课程笔记，按集数倒序。", ["re:宏观及"]),
            ("语雀·爬坑笔记——政策与行业观察", "爬坑笔记", "十五五、四中全会、软件/工业软件、AI 团队。", None),
            ("行业解析专题", "底层逻辑", "新能源/芯片/电影/医美/连锁/咖啡/微短剧/外卖等赛道拆解。",
             ["re:行业解析", "re:咖啡赛道", "re:微短剧", "re:外卖战争", "re:Spacex", "re:元宇宙",
              "re:虚拟货币", "re:数字人民币", "re:腾讯、苹果", "re:财富管理", "re:聊聊加盟",
              "re:繁花", "re:Sora", "re:三体版权"]),
            ("语雀·交易系统——行业周期", "交易系统", None, None),
            ("为知·商业思考（2013-2017 年的老笔记）", None, None, None),
        ],
        "external": [
            ("为知·50个不同行业企业的发展规划", "../../为知笔记迁移/投资与理财/50个不同行业企业的发展规划.md"),
            ("为知·中国未来商业模式的30个大胆思考", "../../为知笔记迁移/投资与理财/中国未来商业模式的30个大胆思考.md"),
        ],
    },
    "06": {
        "file": "06-选股基金与量化.md",
        "title": "选股、基金与量化",
        "intro": (
            "**选什么**的问题：选股逻辑、基金定投、财报退市规则，以及一条完整的量化路线\n"
            "（Python 基础 → numpy/pandas → 动量/双均线/配对策略 → 可视化，共 19 篇，192-210 号）。"
        ),
        "sections": [
            ("语雀·底层逻辑——投资方法论/选股/选基", "底层逻辑", "消费品定价、估值、补仓、逃顶信号、庄股识别、高分红陷阱。"),
            ("语雀·爬坑笔记——规则与量化", "爬坑笔记", "财报披露/退市新规 + Python 量化全系列。"),
        ],
    },
    "07": {
        "file": "07-新手学习路线.md",
        "title": "新手学习路线",
        "intro": (
            "如果从头再学一遍交易，按这个顺序走：\n\n"
            "1. **入门**：新手炒股 8 讲（088-095）——选股、买卖点、仓位、跟庄、解套\n"
            "2. **筑基**：《什么是真正的交易》17 讲（096-112）——性格、趋势/反转、交易体系\n"
            "3. **进阶**：《像证券交易员一样思考和行动》6 讲（113-119）——理解市场、绝招、纪律\n"
            "4. **开胃**：三个汉堡经济学、慢慢变富（底层逻辑 001/002/108）\n\n"
            "学完再回 02/03 册深化，别在第一步恋战。"
        ),
        "sections": [
            ("语雀·爬坑笔记——课程全记录（按学习顺序）", "爬坑笔记", None),
            ("语雀·底层逻辑——入门科普", "底层逻辑", None),
        ],
    },
}

# ---------------- 内联 SVG 示意图（注入各册文件头，不影响分组逻辑） ----------------
SVG_BLOCKS = {
    "01": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 380" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="280" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">实盘成长史回看路线</text>
  <rect x="150" y="58" width="260" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="280" y="86" text-anchor="middle" font-size="13" fill="#1e293b">踩坑与心路（爬坑笔记1-3）</text>
  <line x1="280" y1="104" x2="280" y2="130" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="150" y="134" width="260" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="280" y="162" text-anchor="middle" font-size="13" fill="#1e293b">年度/月度复盘轨迹（054-063）</text>
  <line x1="280" y1="180" x2="280" y2="206" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="150" y="210" width="260" height="52" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="280" y="231" text-anchor="middle" font-size="13" fill="#1e293b">2026 作战方案三件套</text>
  <text x="280" y="251" text-anchor="middle" font-size="13" fill="#1e293b">（方案/执行/预案）</text>
  <line x1="280" y1="262" x2="280" y2="308" stroke="#64748b" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#ar1)"/>
  <rect x="180" y="312" width="200" height="40" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="280" y="337" text-anchor="middle" font-size="13" fill="#1e293b">资产与账本孤本（外链区）</text>
</svg>

*图：本册主题结构示意（依各小节整理）*""",
    "02": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 400" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <text x="350" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">交易心理与悟道导图</text>
  <rect x="265" y="185" width="170" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="350" y="215" text-anchor="middle" font-size="13" fill="#1e293b">交易心理与悟道</text>
  <line x1="265" y1="195" x2="230" y2="100" stroke="#64748b" stroke-width="1.5"/>
  <line x1="265" y1="225" x2="230" y2="296" stroke="#64748b" stroke-width="1.5"/>
  <line x1="435" y1="195" x2="470" y2="100" stroke="#64748b" stroke-width="1.5"/>
  <line x1="435" y1="225" x2="470" y2="290" stroke="#64748b" stroke-width="1.5"/>
  <rect x="10" y="80" width="220" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="120" y="105" text-anchor="middle" font-size="13" fill="#1e293b">八位数花园·心理专辑（63篇）</text>
  <rect x="470" y="80" width="190" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="565" y="105" text-anchor="middle" font-size="13" fill="#1e293b">交易系统·认知与世界观</text>
  <rect x="40" y="270" width="190" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="135" y="291" text-anchor="middle" font-size="13" fill="#1e293b">爬坑·心法与境界</text>
  <text x="135" y="311" text-anchor="middle" font-size="13" fill="#1e293b">（十大境界/武侠秘籍）</text>
  <rect x="470" y="270" width="190" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="565" y="295" text-anchor="middle" font-size="13" fill="#1e293b">底层逻辑·杂谈</text>
</svg>

*图：本册主题结构示意（依各小节整理）*""",
    "03": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 400" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <text x="350" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">交易系统与战法导图</text>
  <rect x="265" y="185" width="170" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="350" y="215" text-anchor="middle" font-size="13" fill="#1e293b">交易系统与实战战法</text>
  <line x1="265" y1="195" x2="230" y2="100" stroke="#64748b" stroke-width="1.5"/>
  <line x1="265" y1="225" x2="230" y2="296" stroke="#64748b" stroke-width="1.5"/>
  <line x1="435" y1="195" x2="470" y2="100" stroke="#64748b" stroke-width="1.5"/>
  <line x1="435" y1="225" x2="470" y2="296" stroke="#64748b" stroke-width="1.5"/>
  <rect x="10" y="80" width="220" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="120" y="105" text-anchor="middle" font-size="13" fill="#1e293b">援军战法·七要素（121-128）</text>
  <rect x="470" y="80" width="200" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="570" y="105" text-anchor="middle" font-size="13" fill="#1e293b">八大形态战法（136-143）</text>
  <rect x="40" y="270" width="190" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="135" y="291" text-anchor="middle" font-size="13" fill="#1e293b">短线实战干货</text>
  <text x="135" y="311" text-anchor="middle" font-size="13" fill="#1e293b">（盈亏比/震仓/低吸）</text>
  <rect x="470" y="270" width="190" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="565" y="291" text-anchor="middle" font-size="13" fill="#1e293b">系统与执行</text>
  <text x="565" y="311" text-anchor="middle" font-size="13" fill="#1e293b">（1-2-3法则/大小周期）</text>
</svg>

*图：本册主题结构示意（依各小节整理）*""",
    "04": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 400" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <text x="350" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">游资与高手实录导图</text>
  <rect x="265" y="185" width="170" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="350" y="215" text-anchor="middle" font-size="13" fill="#1e293b">游资与高手实录</text>
  <line x1="265" y1="195" x2="200" y2="100" stroke="#64748b" stroke-width="1.5"/>
  <line x1="435" y1="195" x2="500" y2="100" stroke="#64748b" stroke-width="1.5"/>
  <line x1="350" y1="235" x2="350" y2="298" stroke="#64748b" stroke-width="1.5"/>
  <rect x="10" y="80" width="190" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="105" y="105" text-anchor="middle" font-size="13" fill="#1e293b">柚子系九大游资心法</text>
  <rect x="500" y="80" width="190" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="595" y="105" text-anchor="middle" font-size="13" fill="#1e293b">财经课与交易员课</text>
  <rect x="230" y="300" width="240" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="350" y="321" text-anchor="middle" font-size="13" fill="#1e293b">抖音连线实录</text>
  <text x="350" y="341" text-anchor="middle" font-size="13" fill="#1e293b">（大毛哥/二万哥/野人哥）</text>
</svg>

*图：本册主题结构示意（依各小节整理）*""",
    "05": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 400" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <text x="350" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">宏观与行业底层逻辑导图</text>
  <rect x="265" y="185" width="170" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="350" y="215" text-anchor="middle" font-size="13" fill="#1e293b">宏观与行业底层逻辑</text>
  <line x1="265" y1="195" x2="230" y2="106" stroke="#64748b" stroke-width="1.5"/>
  <line x1="265" y1="225" x2="230" y2="296" stroke="#64748b" stroke-width="1.5"/>
  <line x1="435" y1="195" x2="470" y2="106" stroke="#64748b" stroke-width="1.5"/>
  <line x1="435" y1="225" x2="470" y2="296" stroke="#64748b" stroke-width="1.5"/>
  <rect x="30" y="80" width="200" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="130" y="101" text-anchor="middle" font-size="13" fill="#1e293b">宏观及商业环境</text>
  <text x="130" y="121" text-anchor="middle" font-size="13" fill="#1e293b">（黄金/关税/化债/AI）</text>
  <rect x="470" y="80" width="200" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="570" y="101" text-anchor="middle" font-size="13" fill="#1e293b">政策与行业观察</text>
  <text x="570" y="121" text-anchor="middle" font-size="13" fill="#1e293b">（十五五/软件）</text>
  <rect x="30" y="270" width="200" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="130" y="291" text-anchor="middle" font-size="13" fill="#1e293b">行业解析专题</text>
  <text x="130" y="311" text-anchor="middle" font-size="13" fill="#1e293b">（新能源/芯片/医美/咖啡）</text>
  <rect x="470" y="270" width="200" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="570" y="291" text-anchor="middle" font-size="13" fill="#1e293b">行业周期与</text>
  <text x="570" y="311" text-anchor="middle" font-size="13" fill="#1e293b">为知老笔记</text>
</svg>

*图：本册主题结构示意（依各小节整理）*""",
    "06": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 380" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="400" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">选股基金与量化结构</text>
  <rect x="315" y="90" width="170" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="400" y="120" text-anchor="middle" font-size="13" fill="#1e293b">选股、基金与量化</text>
  <line x1="315" y1="115" x2="250" y2="115" stroke="#64748b" stroke-width="1.5"/>
  <line x1="485" y1="115" x2="550" y2="115" stroke="#64748b" stroke-width="1.5"/>
  <rect x="60" y="89" width="190" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="155" y="110" text-anchor="middle" font-size="13" fill="#1e293b">选股/选基方法论与估值</text>
  <text x="155" y="130" text-anchor="middle" font-size="13" fill="#1e293b">（底层逻辑）</text>
  <rect x="550" y="89" width="190" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="645" y="110" text-anchor="middle" font-size="13" fill="#1e293b">财报披露与退市规则</text>
  <text x="645" y="130" text-anchor="middle" font-size="13" fill="#1e293b">（爬坑）</text>
  <rect x="30" y="245" width="150" height="34" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="105" y="267" text-anchor="middle" font-size="13" fill="#1e293b">Python 基础</text>
  <line x1="182" y1="262" x2="216" y2="262" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="220" y="245" width="150" height="34" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="295" y="267" text-anchor="middle" font-size="13" fill="#1e293b">numpy/pandas</text>
  <line x1="372" y1="262" x2="406" y2="262" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="410" y="245" width="170" height="34" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="495" y="267" text-anchor="middle" font-size="13" fill="#1e293b">动量/双均线/配对策略</text>
  <line x1="582" y1="262" x2="616" y2="262" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="620" y="245" width="150" height="34" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="695" y="267" text-anchor="middle" font-size="13" fill="#1e293b">可视化</text>
  <text x="400" y="307" text-anchor="middle" font-size="12" fill="#475569">量化路线共 19 篇（192-210 号）</text>
</svg>

*图：本册主题结构示意（依各小节整理）*""",
    "07": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 380" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="280" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">新手四步学习路线</text>
  <rect x="140" y="58" width="280" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="280" y="86" text-anchor="middle" font-size="13" fill="#1e293b">①入门：新手炒股8讲</text>
  <line x1="280" y1="104" x2="280" y2="130" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="140" y="134" width="280" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="280" y="162" text-anchor="middle" font-size="13" fill="#1e293b">②筑基：什么是真正的交易17讲</text>
  <line x1="280" y1="180" x2="280" y2="206" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="140" y="210" width="280" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="280" y="238" text-anchor="middle" font-size="13" fill="#1e293b">③进阶：像证券交易员一样思考和行动6讲</text>
  <line x1="280" y1="256" x2="280" y2="282" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="140" y="286" width="280" height="46" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="280" y="314" text-anchor="middle" font-size="13" fill="#1e293b">④开胃：三个汉堡经济学/慢慢变富</text>
</svg>

*图：本册主题结构示意（依各小节整理）*""",
}

# ---------------- 空文档墓碑（与已提交 MOC 逐字一致） ----------------
# 三篇文章语雀导出为空、原件已清理：按已提交版本继续计入归类总数（474），
# 并在各册 MOC 中以纯文本行留名（不生成链接）。若原文 reappear 于备份区则自动让位。
EMPTY_DOCS = {
    "爬坑笔记": ["052-交易笔记.md", "088-新手炒股.md", "093-6.新手跟庄实战技法.md"],
}
# 个别小节标题需与已提交版本逐字一致（量词/清理说明），其余小节用默认"（N 篇）"。
SECTION_SUFFIX = {
    ("07", "语雀·爬坑笔记——课程全记录（按学习顺序）"): "（{n} 讲，其中 088/093 导出为空已清理）",
}

MOC_ORDER = ["01", "02", "03", "04", "05", "06", "07"]


def natural_key(name):
    return name


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # 1) 分配
    assign = {m: {lib: [] for lib in LIBS} for m in MOC_ORDER}
    unmatched = []
    virtual_by_lib = {
        lib: {v for v in EMPTY_DOCS.get(lib, []) if not (YUQUE / lib / v).exists()}
        for lib in LIBS
    }
    for lib in LIBS:
        real = [f for f in os.listdir(YUQUE / lib) if f.endswith(".md") and f != "README.md"]
        files = sorted(real + sorted(virtual_by_lib[lib]))
        rules = RULES[lib]
        for f in files:
            for moc_key, matchers in rules:
                hit = False
                for m in matchers:
                    if m.startswith("re:"):
                        if re.search(m[3:], f):
                            hit = True
                            break
                    elif f.startswith(m):
                        hit = True
                        break
                if hit:
                    assign[moc_key][lib].append(f)
                    break
            else:
                unmatched.append(f"{lib}/{f}")

    # 2) 校验
    total = sum(len(v) for lib_map in assign.values() for v in lib_map.values())
    print(f"已归类 {total} 篇；未归类 {len(unmatched)} 篇")
    for u in unmatched:
        print("  [未归类]", u)
    if unmatched:
        print("存在未归类文章，拒绝生成。")
        sys.exit(1)

    # 3) 生成
    for moc_key in MOC_ORDER:
        cfg = MOCS[moc_key]
        lines = [f"# {cfg['title']}", "", "> 返回 [投资与交易总纲](<README.md>)", "",
                 cfg["intro"], ""]
        if moc_key in SVG_BLOCKS:
            lines += [SVG_BLOCKS[moc_key], ""]
        n = 0
        printed = set()
        pools = {lib: list(assign[moc_key][lib]) for lib in LIBS}
        for sec in cfg["sections"]:
            heading, lib, note = sec[0], sec[1], sec[2]
            filters = sec[3] if len(sec) > 3 else None
            if lib is None:
                # 外链小节
                lines += [f"## {heading}", ""]
                for text, link in cfg.get("external", []):
                    lines.append(f"- [{text}](<{link}>)")
                    n += 1
                lines.append("")
                continue
            if filters:
                def hit(f):
                    return any(
                        re.search(m[3:], f) if m.startswith("re:") else f.startswith(m)
                        for m in filters
                    )
                files = [f for f in pools[lib] if hit(f)]
                pools[lib] = [f for f in pools[lib] if not hit(f)]  # 消费，防跨小节重复
            else:
                files = pools[lib]
                pools[lib] = []
            if not files:
                continue
            printed.update(files)
            suffix = SECTION_SUFFIX.get((moc_key, heading), "（{n} 篇）")
            lines += [f"## {heading}" + suffix.format(n=len(files)), ""]
            if note:
                lines += [note, ""]
            for f in files:
                text = f[:-3]
                if f in virtual_by_lib[lib]:
                    lines.append(f"- {text}（语雀导出为空文档）")
                    n += 1
                    continue
                link = f"../../语雀备份/{lib}/{f}"
                assert (YUQUE / lib / f).exists(), f"链接目标不存在: {link}"
                lines.append(f"- [{text}](<{link}>)")
                n += 1
            lines.append("")
        # 本册覆盖率校验：该册分到的每篇都必须印出
        missed = set()
        for lib in LIBS:
            missed.update(assign[moc_key][lib])
        missed -= printed
        assert not missed, f"{cfg['file']} 漏印: {sorted(missed)[:3]}"
        path = OUT / cfg["file"]
        with open(path, "w", encoding="utf-8", newline="\n") as fh:  # 强制 LF 行尾
            fh.write("\n".join(lines))
        print(f"生成 {path}（{n} 条链接）")

    # 4) 各库覆盖数校验
    for lib in LIBS:
        all_count = len([f for f in os.listdir(YUQUE / lib) if f.endswith(".md") and f != "README.md"]) + len(virtual_by_lib[lib])
        got = sum(len(assign[m][lib]) for m in MOC_ORDER)
        print(f"{lib}: {got}/{all_count}")


if __name__ == "__main__":
    main()
