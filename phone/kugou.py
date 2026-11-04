"""深链构造 + 选曲逻辑。"""

import json
import re
import urllib.parse

PKG_ANDROID = "com.kugou.android"

# 版本标记（硬过滤用）
# 只拦「明确是变体」的标记，不要拦「钢琴曲」「改编」这类
# —— 它们本身可能就是合法作品（如《夜的钢琴曲5》是原创钢琴曲，不是《晴天》的钢琴版）
_BAD_VERSION = [
    "dj", "咚鼓", "live", "演唱会", "现场",
    "翻唱", "cover", "remix", "伴奏",
    "0.8x", "0.9x", "降调", "加速",
    "(钢琴版)", "(吉他版)", "(女声版)", "(男声版)",
    "(童声", "(合唱版)", "(独唱版)", "(交响", "(史诗",
]


def version_ok(title: str, artist: str) -> bool:
    """判断是否为「原版」而非变体版本。

    宁可漏掉一些合法版本，也不能让翻唱/DJ 版流出去 ——
    用户点了听到不知名翻唱，信任直接归零。
    """
    low = f"{title} {artist}".lower()
    return not any(m in low for m in _BAD_VERSION)


# ── 链接构造 ─────────────────────────────────────────────────

def web_url(song: dict) -> str:
    """网页单曲页。有 mixsong 用单曲页，否则退回搜索页。

    搜索页也能用，但对用户是「落到一堆同名结果里」，体验差一档。
    所以优先单曲页。
    """
    if song.get("mixsong"):
        return f"https://www.kugou.com/mixsong/{song['mixsong']}.html"
    q = urllib.parse.quote(f"{song['artist']} {song['title']}")
    return f"https://www.kugou.com/yy/html/search.html#searchKeyWord={q}"


def find_mixsong(hash_: str, keyword: str) -> str:
    """通过搜索接口反查 mixsong_id。

    注意：搜索接口返回的是 album_audio_id（数字型），和 mixsong_id（8 位字母数字）
    不是同一套编码，无法直接换算。这里只做「有就填」的尽力而为，
    拿不到就返回空串，让 web_url 退回搜索页 —— 不猜、不编。
    """
    return ""


def play_scheme(song: dict) -> str:
    """L2 分享回流协议。cmd=212 表示播放指定音频。

    注意：此格式未经真机验证，来源为第三方实操案例。
    失败时应回落到 web_url。
    """
    payload = {
        "cmd": 212,
        "jsonStr": {
            "hash": song["hash"],
            "filename": f"{song['artist']} - {song['title']}",
            "extname": "mp3",
        },
    }
    enc = urllib.parse.quote(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), safe=""
    )
    return f"kugou://start.weixin?{enc}"


def intent_url(song: dict) -> str:
    """L3 安卓 intent，带未安装兜底。

    browser_fallback_url 是 Chrome 官方支持的参数，
    没装 App 时自动跳网页，避免死按钮。
    """
    fb = urllib.parse.quote(web_url(song), safe="")
    return (
        f"intent://play?hash={song['hash']}"
        f"#Intent;scheme=kugou;package={PKG_ANDROID}"
        f";S.browser_fallback_url={fb};end"
    )


# ── 选曲 ─────────────────────────────────────────────────────

def score(song: dict, scene: dict, brief: str) -> int:
    """按场景要求打分。分数低的不返回，而不是硬凑。"""
    s = 0

    # 人声强度：超出上限直接出局（专注场景的核心约束）
    if song["vocal"] > scene["want_vocal_max"]:
        return -999
    s += (scene["want_vocal_max"] - song["vocal"]) * 3

    # 能量区间
    lo, hi = scene["want_energy"]
    if lo <= song["energy"] <= hi:
        s += 5
    else:
        s -= abs(song["energy"] - (lo if song["energy"] < lo else hi)) * 4

    # 标签命中
    overlap = set(song["tags"]) & set(scene["tags_boost"])
    s += len(overlap) * 4

    # 真机验证过的优先
    if song.get("verified"):
        s += 6

    return s


def pick(scene_id: str, brief: str, limit: int = 1, recent=None):
    """返回 (选中列表, 淘汰说明)。

    recent: 最近推过的 song id 列表。会被降权，避免连续推同一首 ——
    同一天问三次都给《夜的钢琴曲5》，会显得很蠢。
    """
    from library import LIBRARY, SCENES

    recent = set(recent or [])
    scene = SCENES.get(scene_id)
    if not scene:
        return [], f"未知场景 {scene_id}，可用: {', '.join(SCENES)}"

    dropped = []
    cands = []
    for song in LIBRARY:
        if not version_ok(song["title"], song["artist"]):
            dropped.append(f"{song['title']}（版本过滤）")
            continue
        # 硬约束：BGM 场景必须有歌唱的不能上，否则理由里"纯器乐"会与事实不符
        if scene.get("require_instrument") and not song.get("instrument"):
            dropped.append(f"{song['title']}（有人声，不能当 BGM）")
            continue
        sc = score(song, scene, brief)
        if sc < 0:
            dropped.append(f"{song['title']}（人声过强，不适合{scene['label']}）")
            continue
        # 近期推过的重罚，迫使选别的
        if song["id"] in recent:
            sc -= 25
        cands.append((sc, song))

    cands.sort(key=lambda x: -x[0])
    chosen = [s for _, s in cands[:limit]]

    if not chosen:
        why = "；".join(dropped) if dropped else "曲库为空"
        return [], f"曲库中没有符合「{scene['label']}」的曲目（{why}）"

    return chosen, ("；".join(dropped) if dropped else "")


def build_reason(song: dict, scene: dict, brief: str) -> str:
    """推荐理由必须引用用户原话，不能是空话。"""
    b = brief.strip() or scene["label"]
    if len(b) > 20:
        b = b[:20] + "…"
    return scene["reason_tpl"].format(brief=f"「{b}」")


# ── 分享链解析 ──────────────────────────────────────────────

_UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36")


def resolve_share(url: str) -> dict:
    """解析酷狗分享链，返回 hash / songid / album_audio_id 等。

    实测：分享页的 `var phpParam` 里带 song_info.data，含全部 ID。
    mixsong_id 不在静态 HTML 里，只在渲染后的规范链接中，故留空。
    """
    import urllib.request

    req = urllib.request.Request(
        url, headers={"User-Agent": _UA, "Referer": "https://m.kugou.com/"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode("utf-8", "replace")

    m = re.search(r"var phpParam = (\{.*?\});", html, re.S)
    if not m:
        return {}

    param = json.loads(m.group(1))
    si = param.get("song_info", {}).get("data", {})
    if not si:
        return {}

    return {
        "title": si.get("songName", ""),
        "artist": si.get("singerName") or si.get("author_name", ""),
        "album": si.get("albumName", ""),
        "hash": (si.get("hash") or "").lower(),
        "songid": str(si.get("audio_id", "")),
        "album_audio_id": str(si.get("album_audio_id", "")),
        "album_id": str(si.get("albumid", "")),
        "duration": si.get("timeLength", 0),
        "pay_type": si.get("pay_type", 0),
        "privilege": si.get("privilege", 0),
    }
