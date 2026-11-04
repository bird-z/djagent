"""kgJP 曲库。

字段说明：
- hash       必填，深链必需参数
- mixsong    单曲页 id，有则用单曲页做网页兜底，无则退搜索页
- vocal      1 纯器乐表现 - 5 强人声（决定能否用于专注/BGM 场景）
- instrument 是否纯器乐（BGM 场景硬性要求）
- energy     1 极静 - 5 极躁
- exists     是否确认酷狗曲库内存在（已用搜索接口回查 hash 确认）
- verified   是否真机验证过「唤起客户端」。**当前全部为 False** —— 尚无真机结果

诚实标注：exists=True 只代表「这首歌在酷狗里有」，不代表「点链接能唤起客户端」。
混为一谈会让后续决策建立在错误假设上。
"""

LIBRARY = [
    # ══════════ 纯器乐 / 可作背景 ══════════
    {
        "id": "yede5",
        "title": "夜的钢琴曲5",
        "artist": "石进",
        "album": "夜的钢琴曲",
        "hash": "4b11c876080c74c8cdacd737ac11e7b5",
        "mixsong": "",
        "duration": 133,
        "lang": "纯音乐",
        "vocal": 1,
        "instrument": True,
        "energy": 1,
        "tags": ["纯音乐", "专注", "安静", "深夜", "治愈"],
        "exists": True,
        "verified": False,
    },
    {
        "id": "river",
        "title": "River Flows In You",
        "artist": "Yiruma",
        "album": "First Love",
        "hash": "c6c7ea6dabc0f0022a86abdc6f8d3f59",
        "mixsong": "",
        "duration": 218,
        "lang": "纯音乐",
        "vocal": 1,
        "instrument": True,
        "energy": 2,
        "tags": ["纯音乐", "专注", "安静", "治愈"],
        "exists": True,
        "verified": False,
    },
    {
        "id": "canon",
        "title": "卡农",
        "artist": "纯音乐",
        "album": "卡农",
        "hash": "88d1d6e077579116329c25fc884bfd7b",
        "mixsong": "",
        "duration": 296,
        "lang": "纯音乐",
        "vocal": 1,
        "instrument": True,
        "energy": 2,
        "tags": ["纯音乐", "专注", "安静", "华语"],
        "exists": True,
        "verified": False,
    },

    # ══════════ 弱人声 / 低干扰 ══════════
    {
        "id": "chaoxi",
        "title": "潮汐 (Natural)",
        "artist": "傅梦彤",
        "album": "潮汐",
        "hash": "a4713521e4754b8ed3f09af1e41756e5",
        "mixsong": "4ltgkqde",
        "duration": 168,
        "lang": "国语",
        "vocal": 2,
        "instrument": False,
        "energy": 3,
        "tags": ["专注", "深夜", "疲惫", "安静"],
        "exists": True,
        "verified": False,
    },

    # ══════════ 强人声 / 情绪向 ══════════
    {
        "id": "qingtian",
        "title": "晴天",
        "artist": "周杰伦",
        "album": "叶惠美",
        "hash": "b3a52a7a958bf0aed0ebfba2e9a818b7",
        "mixsong": "",
        "duration": 269,
        "lang": "国语",
        "vocal": 4,
        "instrument": False,
        "energy": 3,
        "tags": ["怀旧", "华语", "青春"],
        "exists": True,
        "verified": False,
    },
    {
        "id": "pingfan",
        "title": "平凡之路",
        "artist": "朴树",
        "album": "猎户星座",
        "hash": "2be5de80e68b3346918d38cf7527d979",
        "mixsong": "",
        "duration": 301,
        "lang": "国语",
        "vocal": 4,
        "instrument": False,
        "energy": 4,
        "tags": ["怀旧", "华语", "燃", "治愈"],
        "exists": True,
        "verified": False,
    },
    {
        "id": "nanshan",
        "title": "南山南",
        "artist": "马頔",
        "album": "孤岛",
        "hash": "8bb9a34662de6e987a4dba08a2f46b1a",
        "mixsong": "",
        "duration": 325,
        "lang": "国语",
        "vocal": 4,
        "instrument": False,
        "energy": 2,
        "tags": ["深夜", "安静", "怀旧", "华语", "疲惫"],
        "exists": True,
        "verified": False,
    },
    {
        "id": "anheqiao",
        "title": "安和桥",
        "artist": "宋冬野",
        "album": "安和桥北",
        "hash": "314a859902ca32e8888f0431d9f744b9",
        "mixsong": "",
        "duration": 251,
        "lang": "国语",
        "vocal": 4,
        "instrument": False,
        "energy": 2,
        "tags": ["深夜", "怀旧", "安静", "华语"],
        "exists": True,
        "verified": False,
    },
    {
        "id": "chengdu",
        "title": "成都",
        "artist": "赵雷",
        "album": "无法长大",
        "hash": "faa0470f57a3ee18f0dff04c5b8ee7d2",
        "mixsong": "",
        "duration": 328,
        "lang": "国语",
        "vocal": 4,
        "instrument": False,
        "energy": 3,
        "tags": ["怀旧", "华语", "温柔"],
        "exists": True,
        "verified": False,
    },
]


# ── 场景定义 ────────────────────────────────────────────────
# want_vocal_max：人声强度上限，超出直接出局，不参与打分。
# require_instrument：是否为硬性要求纯器乐。
#
# 为什么专注场景卡 vocal<=3：
# 强人声（尤其有记忆点的副歌）会把注意力从手头的活上拽走，
# 这是 L1 状态型场景和 L4 点歌场景最本质的区别 —— 后者反而人声越强越好。

SCENES = {
    "focus": {
        "label": "写代码 / 专注",
        "desc": "需要不被打断，音乐只做背景衬底",
        "want_vocal_max": 3,
        "want_energy": (1, 3),
        "tags_boost": ["专注", "纯音乐", "安静"],
        "require_instrument": False,
        "reason_tpl": "你说{brief}，这首没有会突然炸出来的副歌，适合当写到一半时的垫底",
    },
    "tired": {
        "label": "深夜疲惫",
        "desc": "累但还不能停，需要被托住而不是被刺激",
        "want_vocal_max": 4,
        "want_energy": (2, 3),
        "tags_boost": ["深夜", "疲惫", "温柔", "安静"],
        "require_instrument": False,
        "reason_tpl": "你说{brief}，这首节奏往下走，不推你，硬撑的时候比较扛得住",
    },
    "restless": {
        "label": "心烦",
        "desc": "情绪堵着，需要疏解而不是压制",
        "want_vocal_max": 3,
        "want_energy": (1, 3),
        "tags_boost": ["安静", "治愈", "纯音乐"],
        "require_instrument": False,
        "reason_tpl": "你说{brief}，这首不劝你也不哄你，只是把节奏放慢，让你有地方喘口气",
    },
    "nostalgia": {
        "label": "有点怀旧",
        "desc": "想回到某个时间点",
        "want_vocal_max": 5,
        "want_energy": (1, 4),
        "tags_boost": ["怀旧", "华语", "青春"],
        "require_instrument": False,
        "reason_tpl": "你说{brief}，这首的编曲是那个时候的听感，不掺现在的电子味",
    },
    "bgm": {
        "label": "找 BGM",
        "desc": "给视频或画面配乐，功能优先于情绪",
        "want_vocal_max": 1,
        "want_energy": (1, 3),
        "tags_boost": ["纯音乐", "专注", "安静"],
        "require_instrument": True,
        "reason_tpl": "你说{brief}，这首是纯器乐，铺在画面下面不会盖住解说",
    },
}


# ── 版本标记 ────────────────────────────────────────────────
# 搜「晴天」能出 30 个版本，落在不知名翻唱上会直接损伤信任。
VERSION_MARKERS = {
    "DJ": ["dj", "咚鼓"],
    "Live": ["live", "演唱会", "现场"],
    "翻唱": ["翻唱", "cover", "女声版", "男声版", "童声", "合唱版", "独唱版"],
    "改编": ["remix", "钢琴曲", "吉他版", "交响", "史诗", "0.8x", "0.9x", "降调", "加速", "改编"],
}
