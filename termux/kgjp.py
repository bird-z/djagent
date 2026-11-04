#!/usr/bin/env python3
"""kgJP 手机端 Agent（Termux 版）。

设计目标：
  在手机上运行，不依赖浏览器、不依赖电脑、不依赖 adb。
  直接用 Android 的 am start 命令唤起酷狗客户端。

依赖：
  - Termux（F-Droid 版）
  - pkg install python
  - 可选：Termux:API（提供 termux-open-url 备用通道和 toast 提示）

用法：
  python kgjp.py focus 改了三版还没过      # 按场景推荐并播放
  python kgjp.py tired                     # 省略 brief
  python kgjp.py scenes                    # 列出场景
  python kgjp.py list                      # 列出曲库
  python kgjp.py play 4b11c876080c74c8cdacd737ac11e7b5 "石进 - 夜的钢琴曲5"
                                           # 按 hash 直接播
  python kgjp.py dry focus xxx             # 只打印不唤起（验证选曲逻辑）
"""

import json
import os
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kugou
from library import LIBRARY, SCENES

# ── 会话内去重 ──────────────────────────────────────────────
RECENT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".recent")
RECENT_MAX = 5


def load_recent():
    try:
        with open(RECENT_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def save_recent(ids):
    try:
        with open(RECENT_FILE, "w") as f:
            json.dump(ids[-RECENT_MAX:], f)
    except Exception:
        pass  # 去重失败不影响主流程


# ── 唤起通道（按可靠性排序，逐个尝试）──────────────────────

def launch_kugou(scheme):
    """按顺序尝试三条通道，返回 (成功与否, 用的通道名)。

    1. am start —— Termux 内可直接调用 Android 的 activity manager，
       是最直接的"命令唤起"，不经过任何浏览器。
    2. termux-open-url —— 需要 Termux:API 插件，走系统 URL 分发。
    3. xdg-open —— Termux 自带的兜底，最终也是走 am。
    """
    channels = [
        ("am", ["am", "start", "-a", "android.intent.action.VIEW", "-d", scheme]),
        ("termux-open-url", ["termux-open-url", scheme]),
        ("xdg-open", ["xdg-open", scheme]),
    ]
    errors = []
    for name, cmd in channels:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            # am start 失败时输出含 "Error" / "Exception"
            out = (r.stdout + r.stderr).lower()
            if r.returncode == 0 and "error" not in out and "not found" not in out:
                return True, name
            errors.append(f"{name}: rc={r.returncode} {out[:80]}")
        except FileNotFoundError:
            errors.append(f"{name}: 命令不存在")
        except Exception as e:
            errors.append(f"{name}: {e}")
    return False, "；".join(errors)


def toast(msg):
    """Termux:API 的屏幕提示，失败静默。"""
    try:
        subprocess.run(["termux-toast", msg], timeout=5,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


# ── 核心动作 ────────────────────────────────────────────────

def do_recommend(scene, brief, dry=False, quiet=False):
    if scene not in SCENES:
        print(f"未知场景 {scene}。可用: {', '.join(SCENES)}")
        return 1

    recent = load_recent()
    songs, note = kugou.pick(scene, brief, limit=1, recent=recent)

    if not songs:
        print(f"✗ {note or '该场景暂无匹配曲目'}")
        print("  曲库没覆盖这个场景，如实说明，不硬凑。")
        return 1

    song = songs[0]
    recent.append(song["id"])
    save_recent(recent)

    reason = kugou.build_reason(song, SCENES[scene], brief)
    dur = f"{song['duration'] // 60}:{song['duration'] % 60:02d}"

    print()
    print(f"♪ {song['title']} — {song['artist']}  ({dur})")
    print(f"  {reason}")
    print(f"  链接: {kugou.web_url(song)}")
    if song.get("verified"):
        print("  [已真机验证]")
    else:
        print("  [唤起协议未真机验证：若只打开不播放，请反馈]")
    print()

    if dry:
        print("(dry 模式，未唤起)")
        print(f"  scheme: {kugou.play_scheme(song)[:80]}…")
        return 0

    ok, detail = launch_kugou(kugou.play_scheme(song))
    if ok:
        if not quiet:
            print(f"✓ 已通过 {detail} 唤起酷狗")
        toast(f"正在播放: {song['title']}")
        return 0
    else:
        print(f"✗ 唤起失败（{detail}）")
        print("  兜底：打开网页版")
        try:
            subprocess.run(["termux-open-url", kugou.web_url(song)], timeout=10)
        except Exception:
            print(f"  请手动打开: {kugou.web_url(song)}")
        return 2


def do_play_by_hash(hash_, name, dry=False):
    song = {"hash": hash_.lower(), "title": name, "artist": "", "duration": 0,
            "mixsong": ""}
    if dry:
        print(f"scheme: {kugou.play_scheme(song)[:90]}…")
        return 0
    ok, detail = launch_kugou(kugou.play_scheme(song))
    print(("✓ 已唤起（" + detail + "）") if ok else f"✗ 失败: {detail}")
    return 0 if ok else 2


def do_scenes():
    print("可用场景：")
    for k, v in SCENES.items():
        print(f"  {k:10s} {v['label']}  — {v['desc']}")


def do_list():
    print(f"曲库 {len(LIBRARY)} 首：")
    for s in LIBRARY:
        v = "✓真机" if s.get("verified") else " 未验"
        inst = "纯音乐" if s.get("instrument") else "人声  "
        print(f"  [{v}] {s['title']} — {s['artist']}  "
              f"({inst} 能量{s['energy']})")


def do_test():
    """自检：不唤起，验证选曲逻辑和命令通道是否存在。"""
    print("=== 环境 ===")
    for cmd in ("am", "termux-open-url", "xdg-open"):
        r = subprocess.run(["which", cmd], capture_output=True, text=True)
        print(f"  {cmd:16s} {'✓ ' + r.stdout.strip() if r.returncode==0 else '✗ 无'}")

    print("\n=== 逐场景选曲（dry）===")
    recent = load_recent()
    for sid, sc in SCENES.items():
        songs, note = kugou.pick(sid, "自检", limit=1, recent=recent)
        if songs:
            print(f"  {sid:10s} → {songs[0]['title']} / {songs[0]['artist']}")
        else:
            print(f"  {sid:10s} → 无匹配（{note}）")

    print("\n=== 深链样例（潮汐）===")
    chaoxi = next((s for s in LIBRARY if s["id"] == "chaoxi"), None)
    if chaoxi:
        print(f"  {kugou.play_scheme(chaoxi)[:90]}…")
    print("\n自检完成。真机唤起测试: python kgjp.py focus 测试")


# ── 入口 ────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0

    cmd = args[0]
    if cmd in ("scenes", "场景"):
        do_scenes()
    elif cmd in ("list", "曲库"):
        do_list()
    elif cmd == "test":
        do_test()
    elif cmd == "play":
        if len(args) < 2:
            print("用法: play <hash> [名称]")
            return 1
        return do_play_by_hash(args[1], args[2] if len(args) > 2 else "")
    elif cmd == "dry":
        if len(args) < 2:
            print("用法: dry <场景> [brief]")
            return 1
        return do_recommend(args[1],
                            " ".join(args[2:]) or "", dry=True)
    elif cmd in SCENES:
        return do_recommend(cmd, " ".join(args[1:]))
    else:
        print(f"未知命令 {cmd}。场景: {', '.join(SCENES)}；其他: scenes/list/test/play/dry")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
