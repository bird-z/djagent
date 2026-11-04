#!/usr/bin/env python3
"""kgJP MCP Server —— 零依赖实现。

为什么手写 MCP 协议而不是用官方 SDK：
官方 `mcp` 包依赖 cryptography（4.8MB），本机网络反复下载失败。
MCP 本质是 JSON-RPC 2.0 over stdio，手写 200 行足够，且零依赖、启动更快。

协议要点：
- 从 stdin 逐行读 JSON-RPC 请求，往 stdout 写单行 JSON 响应
- stdout 只能有协议数据，任何调试输出必须走 stderr
- 必须实现 initialize / tools/list / tools/call
"""

import json
import sys
import traceback

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import kugou
from library import LIBRARY, SCENES

SERVER_NAME = "kgjp"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

# 最近推过的歌，用于避免连续重复。进程内有效，重启即清空 ——
# MVP 阶段不落盘，够用且无副作用。
_RECENT = []
_RECENT_MAX = 5


# ══════════════ 工具定义 ══════════════

TOOLS = [
    {
        "name": "recommend_music",
        "description": (
            "根据用户描述的场景或状态，推荐一首对味的歌，并返回可直接点击的酷狗播放链接。"
            "适用场景：用户说累了/心烦/写代码需要专注/怀旧/找 BGM，"
            "或明确问「放首歌」「来点音乐」。"
            "不要在没有场景信号时主动调用。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scene": {
                    "type": "string",
                    "enum": list(SCENES.keys()),
                    "description": (
                        "场景类型。focus=写代码专注, tired=深夜疲惫, "
                        "restless=心烦, nostalgia=怀旧, bgm=找BGM"
                    ),
                },
                "brief": {
                    "type": "string",
                    "description": (
                        "用户原话的简短摘录，会原样嵌进推荐理由里。"
                        "必须引用用户真实说过的话，不要自己编。"
                    ),
                },
                "platform": {
                    "type": "string",
                    "enum": ["android", "ios", "desktop", "auto"],
                    "default": "auto",
                    "description": "用户点击链接的设备，决定返回哪种深链格式",
                },
            },
            "required": ["scene"],
        },
    },
    {
        "name": "list_scenes",
        "description": "列出 kgJP 支持的所有场景及其选曲约束。用于确认某个场景是否已配置。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "resolve_share",
        "description": (
            "解析酷狗分享链接，提取 hash / songid / album_audio_id 等标识符，"
            "并生成可播放的深链。当用户贴了一条酷狗分享链并要求播放时使用。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "share_url": {
                    "type": "string",
                    "description": "酷狗分享链接，形如 https://m.kugou.com/share/song.html?chain=XXX",
                },
                "platform": {
                    "type": "string",
                    "enum": ["android", "ios", "desktop", "auto"],
                    "default": "auto",
                },
            },
            "required": ["share_url"],
        },
    },
    {
        "name": "library_stats",
        "description": "查看曲库规模与验证状态，用于判断推荐能力边界。",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ══════════════ 工具实现 ══════════════

def _links(song, platform):
    """按平台返回对应的链接集合。"""
    out = {
        "web": kugou.web_url(song),
    }
    if platform in ("android", "auto"):
        out["android_scheme"] = kugou.play_scheme(song)
        out["android_intent"] = kugou.intent_url(song)
    else:
        # iOS / 桌面暂无验证过的 scheme，只能给网页
        out["note"] = f"{platform} 端唤起协议未验证，仅提供网页链接"
    return out


def _play_hint(platform):
    if platform == "android" or platform == "auto":
        return (
            "在安卓手机上点 android_scheme 会尝试唤起酷狗并播放；"
            "点 android_intent 则在未安装酷狗时自动跳到网页版。"
            "注意：唤起协议尚未在真机验证，可能只打开 App 不播放。"
        )
    return "当前平台只提供网页链接，不要承诺会唤起客户端。"


def tool_recommend_music(args):
    scene = args.get("scene", "")
    brief = args.get("brief", "")
    platform = args.get("platform", "auto")

    songs, note = kugou.pick(scene, brief, limit=1, recent=_RECENT)
    if not songs:
        return {
            "found": False,
            "message": note or "该场景暂无匹配曲目",
            "suggestion": (
                "如实告知用户曲库还没覆盖这个场景，不要编造歌名或 hash。"
                "可以说明当前曲库只有「潮汐 - 傅梦彤」一首且已因约束被排除。"
            ),
            "scene": scene,
            "constraint_applied": {
                "vocal_max": SCENES[scene]["want_vocal_max"],
                "energy_range": list(SCENES[scene]["want_energy"]),
            } if scene in SCENES else None,
        }

    song = songs[0]
    _RECENT.append(song["id"])
    if len(_RECENT) > _RECENT_MAX:
        _RECENT.pop(0)

    return {
        "found": True,
        "title": song["title"],
        "artist": song["artist"],
        "album": song.get("album", ""),
        "duration_sec": song["duration"],
        "duration_text": f"{song['duration'] // 60}:{song['duration'] % 60:02d}",
        "reason": kugou.build_reason(song, SCENES[scene], brief),
        "links": _links(song, platform),
        "play_hint": _play_hint(platform),
        "verified_on_device": song.get("verified", False),
        "dropped": note or None,
        "how_to_present": (
            "把 reason 原样说出来（它引用了用户原话，不要改写），"
            "然后给出 web 链接。如果用户在用手机，额外给出 android_scheme。"
        ),
    }


def tool_list_scenes(_args):
    return {
        "scenes": [
            {
                "id": k,
                "label": v["label"],
                "desc": v["desc"],
                "vocal_max": v["want_vocal_max"],
                "energy_range": list(v["want_energy"]),
            }
            for k, v in SCENES.items()
        ],
        "note": "曲库只覆盖了部分场景，list_scenes 不代表都有歌可推。",
    }


def tool_resolve_share(args):
    url = args.get("share_url", "")
    platform = args.get("platform", "auto")
    import urllib.parse

    if "kugou.com" not in url:
        return {"ok": False, "error": "不是酷狗链接"}
    if "share" not in url:
        return {"ok": False, "error": "只支持分享链（含 /share/）"}

    try:
        info = kugou.resolve_share(url) if hasattr(kugou, "resolve_share") else None
    except Exception as e:
        return {"ok": False, "error": f"解析失败: {e}"}

    if not info or not info.get("hash"):
        return {"ok": False, "error": "未解析出 hash，页面结构可能已变"}

    return {
        "ok": True,
        "info": info,
        "links": _links(info, platform),
        "play_hint": _play_hint(platform),
    }


def tool_library_stats(_args):
    total = len(LIBRARY)
    verified = sum(1 for s in LIBRARY if s.get("verified"))
    return {
        "total": total,
        "verified_on_device": verified,
        "unverified": total - verified,
        "scenes_defined": len(SCENES),
        "coverage_warning": (
            "曲库极小，仅用于验证链路。遇到未覆盖的场景必须如实说明，"
            "严禁编造歌名或 hash。"
        ) if total < 10 else None,
        "songs": [
            {"title": s["title"], "artist": s["artist"],
             "verified": s.get("verified", False)}
            for s in LIBRARY
        ],
    }


HANDLERS = {
    "recommend_music": tool_recommend_music,
    "list_scenes": tool_list_scenes,
    "resolve_share": tool_resolve_share,
    "library_stats": tool_library_stats,
}


# ══════════════ JSON-RPC 分发 ══════════════

def handle(msg):
    method = msg.get("method")
    mid = msg.get("id")
    params = msg.get("params") or {}

    # 通知（无 id）不需要回复
    if mid is None and method and method.startswith("notifications/"):
        return None

    def ok(result):
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def err(code, message):
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": code, "message": message}}

    if method == "initialize":
        return ok({
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method == "tools/list":
        return ok({"tools": TOOLS})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = HANDLERS.get(name)
        if not fn:
            return err(-32601, f"未知工具: {name}")
        try:
            data = fn(args)
            return ok({
                "content": [{"type": "text",
                             "text": json.dumps(data, ensure_ascii=False, indent=2)}],
                "isError": False,
            })
        except Exception as e:
            print(f"[kgjp] tool {name} failed: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return ok({
                "content": [{"type": "text", "text": f"工具执行失败: {e}"}],
                "isError": True,
            })

    if method in ("ping", "health"):
        return ok({})

    if mid is None:
        return None
    return err(-32601, f"未知方法: {method}")


def main():
    print(f"[kgjp] server 启动，曲库 {len(LIBRARY)} 首", file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"[kgjp] 非法 JSON: {e}", file=sys.stderr)
            continue

        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
