#!/usr/bin/env python3
"""生成安卓唤起酷狗的测试链接。

用法:
    python3 make_links.py --share "<分享链>" [--mixsong <mixsong_id>]
    python3 make_links.py --hash <hash> --title "歌手 - 歌名"

mixsong_id 说明：静态 HTML 里没有，它只出现在页面渲染后的规范链接中。
如果手上没有，脚本会退回用「搜索页」作为网页兜底，依然可用。
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36")

PKG = "com.kugou.android"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Referer": "https://m.kugou.com/"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", "replace")


def parse_share(url):
    """从分享页的 phpParam.song_info 里解出全部可用字段。"""
    html = fetch(url)
    m = re.search(r"var phpParam = (\{.*?\});", html, re.S)
    if not m:
        sys.exit("未在页面中找到 phpParam，页面结构可能已变")
    param = json.loads(m.group(1))
    si = param.get("song_info", {}).get("data", {})

    return {
        "hash": (si.get("hash") or "").lower(),
        "songid": str(si.get("audio_id", "")),
        "album_audio_id": str(si.get("album_audio_id", "")),
        "album_id": str(si.get("albumid", "")),
        "filename": si.get("fileName", ""),
        "song_name": si.get("songName", ""),
        "singer": si.get("singerName") or si.get("author_name", ""),
        "duration": si.get("timeLength", 0),
        "extname": si.get("extName", "mp3"),
        "pay_type": si.get("pay_type", 0),
        "privilege": si.get("privilege", 0),
    }


def build_links(info, mixsong_id=""):
    h = info["hash"]
    name = info.get("filename") or f"{info.get('singer','')} - {info.get('song_name','')}"

    if mixsong_id:
        web_page = f"https://www.kugou.com/mixsong/{mixsong_id}.html"
    else:
        web_page = ("https://www.kugou.com/yy/html/search.html#searchKeyWord="
                    + urllib.parse.quote(name))
    fb = urllib.parse.quote(web_page, safe="")

    # L2: 官方分享回流 scheme —— JSON 整体 URL 编码
    payload = {"cmd": 212,
               "jsonStr": {"hash": h, "filename": name,
                           "extname": info.get("extname", "mp3")}}
    l2 = "kugou://start.weixin?" + urllib.parse.quote(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

    # L3a: intent 带网页兜底（没装 App 自动跳网页）
    l3a = (f"intent://play?hash={h}#Intent;scheme=kugou;"
           f"package={PKG};S.browser_fallback_url={fb};end")

    # L3b: 只开 App（最保守，用于确认能否唤起）
    l3b = f"intent://#Intent;scheme=kugou;package={PKG};" \
          f"S.browser_fallback_url={fb};end"

    l3c = f"kugou://play?hash={h}"

    return {"L2": l2, "L3a": l3a, "L3b": l3b, "L3c": l3c, "web": web_page}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--share")
    ap.add_argument("--hash")
    ap.add_argument("--title")
    ap.add_argument("--mixsong", default="")
    ap.add_argument("-o", "--out", default="links.md")
    a = ap.parse_args()

    if a.share:
        info = parse_share(a.share)
    elif a.hash:
        info = {"hash": a.hash.lower(), "filename": a.title or "",
                "song_name": a.title or "", "singer": "",
                "extname": "mp3", "songid": "", "album_audio_id": "",
                "album_id": "", "duration": 0, "pay_type": 0, "privilege": 0}
    else:
        sys.exit("需要 --share 或 --hash")

    if not info["hash"]:
        sys.exit("未解出 hash，无法生成深链")

    links = build_links(info, a.mixsong)
    dur = info.get("duration") or 0
    dur_s = f"{dur // 60}:{dur % 60:02d}" if dur else "?"

    L = [
        "# 安卓唤起测试链接",
        "",
        f"**{info.get('singer','')} - {info.get('song_name','')}**　时长 {dur_s}",
        "",
        "| 字段 | 值 |",
        "|---|---|",
        f"| hash | `{info['hash']}` |",
        f"| songid (audio_id) | `{info.get('songid','')}` |",
        f"| album_audio_id | `{info.get('album_audio_id','')}` |",
        f"| album_id | `{info.get('album_id','')}` |",
        f"| fileName | `{info.get('filename','')}` |",
        f"| pay_type / privilege | {info.get('pay_type','')} / {info.get('privilege','')} |",
        "",
        "## 按推荐顺序测试",
        "",
        "### 1. L2 分享回流 scheme — 最有希望直接播放",
        f"[点我在酷狗中播放]({links['L2']})",
        "",
        "```",
        links["L2"],
        "```",
        "",
        "### 2. L3a intent + 网页兜底 — 没装 App 会跳网页",
        f"[点我（带 fallback）]({links['L3a']})",
        "",
        "```",
        links["L3a"],
        "```",
        "",
        "### 3. L3b 只打开酷狗 — 最保守，先确认能否唤起",
        f"[点我打开酷狗]({links['L3b']})",
        "",
        "### 4. L3c 猜测格式 — 大概率不生效，作对照",
        f"[点我]({links['L3c']})",
        "",
        "### 5. 纯网页兜底 — 一定可用",
        f"[点我打开网页版]({links['web']})",
        "",
        "## 测试记录",
        "",
        "| 编号 | 唤起 App | 自动播放 | 落点正确 | 备注 |",
        "|---|---|---|---|---|",
        "| 1 L2 |  |  |  |  |",
        "| 2 L3a |  |  |  |  |",
        "| 3 L3b |  |  |  |  |",
        "| 4 L3c |  |  |  |  |",
        "| 5 web |  |  |  |  |",
        "",
    ]
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"已写入 {a.out}")
    for k, v in info.items():
        print(f"  {k:16s} {v}")


if __name__ == "__main__":
    main()
