#!/usr/bin/env python3
"""kgJP 设备桥 · 手机端拉取执行器（Termux 常驻）。

由 install.sh 下载并启动。循环：
  claim 任务 → 按白名单分发执行 → report 结果 → sleep

只接受四种动作，收到未知类型直接丢弃回报，绝不执行任意命令。
依赖：python3（Termux 自带）；termux-notification / termux-clipboard-set 可选。
"""

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

CONFIG = os.path.expanduser("~/.config/kgjp_bridge.json")
POLL_SECONDS = 15
HTTP_TIMEOUT = 10

ACTIONS = ("play_song", "recommend_scene", "notify", "clipboard_set")


def load_config():
    with open(CONFIG) as f:
        return json.load(f)


def http_json(url, payload=None, token=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("X-KGJP-Token", token)
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return json.loads(r.read().decode())


def build_deep_link(hash_, title):
    payload = {"cmd": 212, "jsonStr": {"hash": hash_, "filename": title, "extname": "mp3"}}
    enc = urllib.parse.quote(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), safe="")
    return f"kugou://start.weixin?{enc}"


def launch_kugou(link):
    """三条唤起通道，顺序降级。返回 (ok, detail)。"""
    for cmd in (
        ["am", "start", "-a", "android.intent.action.VIEW", "-d", link, "com.kugou.android"],
        ["termux-open-url", link],
        ["xdg-open", link],
    ):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if p.returncode == 0:
                return True, "via " + cmd[0]
        except FileNotFoundError:
            continue
        except Exception as e:
            detail = f"{cmd[0]}: {e}"
    return False, detail if 'detail' in dir() else "所有唤起通道均失败"


def do_task(task, cfg):
    action = task.get("action", "")
    params = task.get("params", {}) or {}

    if action == "play_song":
        hash_ = params.get("hash", "")
        title = params.get("title", "")
        if not hash_ or len(hash_) != 32:
            return "failed", f"hash 无效: {hash_!r}"
        ok, detail = launch_kugou(build_deep_link(hash_, f"{params.get('artist', '')} {title}".strip() or title))
        return ("done" if ok else "failed"), f"播放 {title} ({detail})"

    if action == "recommend_scene":
        scene = params.get("scene", "")
        r = http_json(cfg["base"] + "/api/recommend?scene=" + urllib.parse.quote(scene))
        if not r.get("found"):
            return "failed", f"场景 {scene} 无推荐: {r.get('message', '')}"
        song = r
        ok, detail = launch_kugou(build_deep_link(song["id"], f"{song['artist']} - {song['title']}"))
        return ("done" if ok else "failed"), f"场景 {scene} → {song['title']}({song['artist']}) ({detail})"

    if action == "notify":
        title = params.get("title", "kgJP")
        content = params.get("content", "")
        try:
            subprocess.run(["termux-notification", "--title", title, "--content", content],
                           capture_output=True, timeout=10, check=True)
            return "done", "通知已发送"
        except Exception as e:
            return "failed", f"termux-notification 不可用: {e}"

    if action == "clipboard_set":
        text = params.get("text", "")
        try:
            subprocess.run(["termux-clipboard-set", text], capture_output=True, timeout=10, check=True)
            return "done", "剪贴板已写入"
        except Exception as e:
            return "failed", f"termux-clipboard-set 不可用: {e}"

    # 未知动作：丢弃，不执行任何东西
    return "failed", f"未知动作 {action!r}，已丢弃"


def main():
    cfg = load_config()
    base = cfg["base"].rstrip("/")
    device_id, token = cfg["device_id"], cfg["token"]
    print(f"[pull] {device_id} 轮询 {base} 每 {POLL_SECONDS}s", flush=True)
    while True:
        try:
            r = http_json(f"{base}/device/task/claim?device_id={urllib.parse.quote(device_id)}&token={urllib.parse.quote(token)}")
            task = r.get("task")
            if task:
                print(f"[pull] 领取 {task['id']} {task['action']}", flush=True)
                if task["action"] not in ACTIONS:
                    status, detail = "failed", f"未知动作 {task['action']!r}，已丢弃"
                else:
                    status, detail = do_task(task, cfg)
                http_json(f"{base}/device/report",
                          {"task_id": task["id"], "status": status, "detail": detail},
                          token=token)
                print(f"[pull] {task['id']} → {status}: {detail}", flush=True)
        except Exception as e:
            print(f"[pull] 循环异常(继续): {e}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
