#!/usr/bin/env python3
"""从酷狗搜索接口批量取曲目，供补充曲库用。

关键：接口返回的 hash 必须经过「mixsong 页标题校验」才算可信。
无效 ID 会静默回落首页而不报 404（已实测），所以必须比对标题。
"""

import json
import sys
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
SEARCH = "http://mobilecdn.kugou.com/api/v3/search/song"


def search(keyword, pagesize=5):
    url = (f"{SEARCH}?keyword={urllib.parse.quote(keyword)}"
           f"&page=1&pagesize={pagesize}&format=json&showtype=1")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    d = json.loads(urllib.request.urlopen(req, timeout=15).read())
    out = []
    for it in d.get("data", {}).get("info", []):
        out.append({
            "title": it.get("songname", ""),
            "artist": it.get("singername", ""),
            "album": it.get("album_name", ""),
            "hash": (it.get("hash") or "").lower(),
            "album_audio_id": it.get("album_audio_id", ""),
            "duration": it.get("duration", 0),
        })
    return out


def verify(song):
    """用 artist - title 搜索，确认 hash 在酷狗里真能搜到。

    注意：这里只能验证「存在」，不能验证「能唤起」。
    """
    q = f"{song['artist']} {song['title']}"
    try:
        hits = search(q, 10)
    except Exception as e:
        return False, f"搜索失败 {e}"
    for h in hits:
        if h["hash"] == song["hash"]:
            return True, f"确认存在（{h['title']} - {h['artist']}）"
    return False, "搜索结果中未找到该 hash"


if __name__ == "__main__":
    kws = sys.argv[1:] or ["夜的钢琴曲 石进", "River Flows in You", "卡农"]
    for kw in kws:
        print(f"=== {kw} ===")
        try:
            for s in search(kw, 4):
                ok, why = verify(s)
                flag = "OK " if ok else "FAIL"
                print(f"  [{flag}] {s['title']} | {s['artist']} | "
                      f"hash={s['hash']} | aai={s['album_audio_id']} | {s['duration']}s")
        except Exception as e:
            print("  错误:", e)
