#!/usr/bin/env python3
"""kgJP 手机端服务。

把 MCP 工具的能力通过 HTTP 暴露给手机浏览器 ——
手机跑不了 MCP，但能开网页。

和 MCP server 共用 library.py / kugou.py 的同一套选曲逻辑，
避免"网页推荐的和 Agent 推荐的不一样"这种分裂。

用法:
    python3 web.py --port 8801
"""

import argparse
import json
import os
import sys
import threading
import traceback
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kugou
from library import LIBRARY, SCENES

_RECENT = []
_RECENT_MAX = 5
_LOCK = threading.Lock()

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


# ══════════════ 业务逻辑 ══════════════

def api_recommend(scene, brief, platform):
    with _LOCK:
        recent = list(_RECENT)

    songs, note = kugou.pick(scene, brief, limit=1, recent=recent)

    if not songs:
        return {
            "found": False,
            "message": note or "该场景暂无匹配曲目",
            "scene": scene,
        }

    song = songs[0]
    with _LOCK:
        _RECENT.append(song["id"])
        if len(_RECENT) > _RECENT_MAX:
            _RECENT.pop(0)

    return {
        "found": True,
        "id": song["id"],
        "title": song["title"],
        "artist": song["artist"],
        "album": song.get("album", ""),
        "duration_text": f"{song['duration'] // 60}:{song['duration'] % 60:02d}",
        "reason": kugou.build_reason(song, SCENES[scene], brief),
        "links": {
            "web": kugou.web_url(song),
            "scheme": kugou.play_scheme(song),
            "intent": kugou.intent_url(song),
        },
        "verified": song.get("verified", False),
        "dropped": note or None,
    }


def api_share(url, platform):
    if "kugou.com" not in url or "share" not in url:
        return {"ok": False, "error": "不是酷狗分享链（需含 /share/）"}
    try:
        info = kugou.resolve_share(url)
    except Exception as e:
        return {"ok": False, "error": f"解析失败: {e}"}
    if not info or not info.get("hash"):
        return {"ok": False, "error": "未解析出 hash，页面结构可能已变"}
    return {
        "ok": True,
        "info": info,
        "links": {
            "web": kugou.web_url(info),
            "scheme": kugou.play_scheme(info),
            "intent": kugou.intent_url(info),
        },
    }


# ══════════════ HTTP ══════════════

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[kgjp] %s\n" % (fmt % args))

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        path = u.path

        try:
            if path in ("/", "/index.html"):
                return self._serve_file("index.html")
            if path == "/api/scenes":
                return self._send(200, {
                    "scenes": [
                        {"id": k, "label": v["label"], "desc": v["desc"]}
                        for k, v in SCENES.items()
                    ]
                })
            if path == "/api/recommend":
                scene = (q.get("scene") or [""])[0]
                brief = unquote((q.get("brief") or [""])[0])
                plat = (q.get("platform") or ["android"])[0]
                return self._send(200, api_recommend(scene, brief, plat))
            if path == "/api/share":
                url = (q.get("url") or [""])[0]
                return self._send(200, api_share(url, "android"))
            if path == "/api/stats":
                return self._send(200, {
                    "total": len(LIBRARY),
                    "verified": sum(1 for s in LIBRARY if s.get("verified")),
                    "scenes": len(SCENES),
                })
            if path == "/health":
                return self._send(200, {"ok": True})
            return self._send(404, {"error": "not found"})
        except Exception as e:
            traceback.print_exc()
            return self._send(500, {"error": str(e)})

    def _serve_file(self, name):
        fp = os.path.join(STATIC, name)
        if not os.path.exists(fp):
            return self._send(404, {"error": "file not found"})
        with open(fp, "rb") as f:
            data = f.read()
        self._send(200, data, "text/html; charset=utf-8")


def main():
    ap = argparse.ArgumentParser()
    # 云端部署会注入 PORT 环境变量，优先用它；本地跑再用 --port
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8801)))
    ap.add_argument("--host", default="0.0.0.0")
    a = ap.parse_args()

    srv = ThreadingHTTPServer((a.host, a.port), Handler)

    import socket
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass

    print(f"[kgjp] 曲库 {len(LIBRARY)} 首 / 场景 {len(SCENES)} 个", file=sys.stderr)
    print(f"[kgjp] 监听 {a.host}:{a.port}", file=sys.stderr)
    for ip in ips:
        print(f"[kgjp] 手机访问 http://{ip}:{a.port}", file=sys.stderr)

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[kgjp] 已停止", file=sys.stderr)


if __name__ == "__main__":
    main()
