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


# ══════════════ 设备桥（拉模式任务队列）══════════════
# 云端 agent POST 任务 → 手机 Termux 轮询领取 → 执行后回报。
# 手机端永不暴露端口，云端只暴露这一个受令牌保护的入口。

import time as _time
import uuid as _uuid
import secrets as _secrets

_BRIDGE_LOCK = threading.Lock()
_BRIDGE_TASKS = {}      # task_id -> {id, action, params, status, result, created, claimed_at}
_BRIDGE_ORDER = []      # 待领取顺序
_BRIDGE_DEVICES = {}    # device_id -> {token, registered_at, last_seen, last_task}
_BRIDGE_LIMIT = 50
_BRIDGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".bridge_state.json")
# 注册门禁：只有携带安装码的请求才能注册设备/领取令牌。
# 安装码嵌在一键安装命令里（install.sh），换设备 = 换安装码重装。
SETUP_CODE = "kgjp-setup-7k2m"

# 持久化设备注册信息，服务重启不丢令牌
try:
    with open(_BRIDGE_FILE) as _f:
        _BRIDGE_DEVICES = json.load(_f).get("devices", {})
except Exception:
    pass


def _bridge_save():
    try:
        with open(_BRIDGE_FILE, "w") as f:
            json.dump({"devices": _BRIDGE_DEVICES}, f)
    except Exception:
        pass


def _bridge_auth(token, device_id=None):
    if not token:
        return None
    for did, dev in _BRIDGE_DEVICES.items():
        if dev.get("token") == token and (device_id is None or did == device_id):
            return did
    return None


def bridge_register(setup):
    if setup != SETUP_CODE:
        return {"error": "安装码无效"}
    device_id = "dev-" + _uuid.uuid4().hex[:8]
    token = "kgb_" + _secrets.token_urlsafe(24)
    with _BRIDGE_LOCK:
        _BRIDGE_DEVICES[device_id] = {
            "token": token, "registered_at": int(_time.time()),
            "last_seen": 0, "last_task": None,
        }
        _bridge_save()
    return {"device_id": device_id, "token": token,
            "poll_hint": "GET /device/task/claim?device_id=..&token=.. 每 15s"}


def bridge_submit(action, params, token):
    if _bridge_auth(token) is None:
        return 401, {"ok": False, "error": "令牌无效"}
    if action not in ("play_song", "recommend_scene", "notify", "clipboard_set"):
        return 400, {"ok": False, "error": f"动作不在白名单: {action}"}
    with _BRIDGE_LOCK:
        if len(_BRIDGE_ORDER) >= _BRIDGE_LIMIT:
            return 429, {"ok": False, "error": "队列已满"}
        tid = "t-" + _uuid.uuid4().hex[:10]
        _BRIDGE_TASKS[tid] = {"id": tid, "action": action,
                              "params": params or {}, "status": "pending",
                              "result": None, "created": int(_time.time()),
                              "claimed_at": 0}
        _BRIDGE_ORDER.append(tid)
    return 200, {"ok": True, "task_id": tid, "queued": True}


def bridge_claim(device_id, token):
    with _BRIDGE_LOCK:
        if _bridge_auth(token, device_id) is None:
            return 401, {"task": None, "error": "令牌无效"}
        dev = _BRIDGE_DEVICES.get(device_id)
        if dev is not None:
            dev["last_seen"] = int(_time.time())
        for tid in list(_BRIDGE_ORDER):
            t = _BRIDGE_TASKS.get(tid)
            if t and t["status"] == "pending":
                t["status"] = "claimed"
                t["claimed_at"] = int(_time.time())
                _BRIDGE_ORDER.remove(tid)
                if dev is not None:
                    dev["last_task"] = tid
                return 200, {"task": {"id": t["id"], "action": t["action"],
                                      "params": t["params"]}}
    return 200, {"task": None}


def bridge_report(task_id, status, detail, token):
    with _BRIDGE_LOCK:
        if _bridge_auth(token) is None:
            return 401, {"ok": False, "error": "令牌无效"}
        t = _BRIDGE_TASKS.get(task_id)
        if not t:
            return 404, {"ok": False, "error": "任务不存在"}
        t["status"] = status if status in ("done", "failed") else "failed"
        t["result"] = (detail or "")[:500]
    return 200, {"ok": True}


def bridge_status(token):
    with _BRIDGE_LOCK:
        if _bridge_auth(token) is None:
            return 401, {"error": "令牌无效"}
        pending = sum(1 for t in _BRIDGE_TASKS.values() if t["status"] == "pending")
        devices = [{"device_id": d, "last_seen": v["last_seen"],
                    "last_task": v["last_task"]}
                   for d, v in _BRIDGE_DEVICES.items()]
    return 200, {"pending": pending, "devices": devices,
                 "server_time": int(_time.time())}


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
            if path == "/device/install.sh":
                return self._serve_install_sh()
            if path == "/device/pull.py":
                return self._serve_pull_src()
            if path == "/device/register":
                return self._send(200, bridge_register((q.get("setup") or [""])[0]))
            if path == "/device/task/claim":
                return self._send(*bridge_claim(
                    (q.get("device_id") or [""])[0],
                    (q.get("token") or [""])[0]))
            if path == "/device/status":
                tok = (q.get("token") or (q.get("t") or [""]))[0]
                return self._send(*bridge_status(tok))
            return self._send(404, {"error": "not found"})
        except Exception as e:
            traceback.print_exc()
            return self._send(500, {"error": str(e)})

    def do_POST(self):
        u = urlparse(self.path)
        path = u.path
        try:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            try:
                body = json.loads(raw.decode("utf-8"))
            except Exception:
                body = {}
            if not isinstance(body, dict):
                return self._send(400, {"error": "body 必须是 JSON 对象"})
            token = self.headers.get("X-KGJP-Token") or body.get("token", "")
            if path == "/device/task":
                return self._send(*bridge_submit(
                    body.get("action", ""), body.get("params"), token))
            if path == "/device/report":
                return self._send(*bridge_report(
                    body.get("task_id", ""), body.get("status", ""),
                    body.get("detail", ""), token))
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

    def _serve_pull_src(self):
        """下发手机端拉取执行器源码。"""
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_pull.py")
        if not os.path.exists(fp):
            return self._send(500, {"error": "agent_pull.py 缺失"})
        with open(fp, "r", encoding="utf-8") as f:
            self._send(200, f.read(), "text/x-python; charset=utf-8")

    def _serve_install_sh(self):
        """动态生成一键安装脚本：注入 BASE 与安装码。"""
        host = self.headers.get("Host", "")
        base = f"https://{host}" if host and "localhost" not in host and "127.0.0.1" not in host else f"http://{host or '127.0.0.1:8801'}"
        script = f"""#!/data/data/com.termux/files/usr/bin/sh
# kgJP 设备桥一键安装（Termux 内执行）
set -e
BASE="{base}"
SETUP="{SETUP_CODE}"
mkdir -p "$HOME/kgjp" "$HOME/.config"
curl -s "$BASE/device/pull.py" -o "$HOME/kgjp/agent_pull.py"
REG=$(curl -s "$BASE/device/register?setup=$SETUP")
echo "$REG" | grep -q device_id || {{ echo "注册失败: $REG"; exit 1; }}
python - "$REG" "$BASE" <<'PYEOF'
import json, sys, os
reg = json.loads(sys.argv[1]); reg["base"] = sys.argv[2]
p = os.path.expanduser("~/.config/kgjp_bridge.json")
json.dump(reg, open(p, "w"))
print("[install] 设备", reg["device_id"], "已注册")
PYEOF
termux-wake-lock 2>/dev/null || true
pkill -f agent_pull.py 2>/dev/null || true
nohup python "$HOME/kgjp/agent_pull.py" > "$HOME/kgjp/pull.log" 2>&1 &
sleep 2
tail -2 "$HOME/kgjp/pull.log"
echo "[install] 完成：轮询已启动，日志在 ~/kgjp/pull.log"
"""
        self._send(200, script, "text/x-shellscript; charset=utf-8")


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
