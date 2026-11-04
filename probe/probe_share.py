#!/usr/bin/env python3
"""探测酷狗分享页，抽取可用于深链的标识符。

用法: python3 probe_share.py <share_url>
"""
import re
import sys
import urllib.request

UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36")

PATTERNS = {
    "mixsong_id":   r"mixsong/([0-9a-zA-Z]{6,16})\.html",
    "hash_32":      r'"(?:hash|FileHash)"\s*:\s*"([0-9A-Fa-f]{32})"',
    "songid":       r'"(?:songid|song_id|SongId|audio_id)"\s*:\s*"?(\d{4,})"?',
    "album_audio_id": r'"(?:album_audio_id|albumid_audioid|mixsongid)"\s*:\s*"?(\d{6,})"?',
    "album_id":     r'"(?:album_id|AlbumId)"\s*:\s*"?(\d{4,})"?',
    "encode_id":    r'encode_album_audio_id=([0-9a-zA-Z]+)',
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Referer": "https://m.kugou.com/"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.geturl(), r.read().decode("utf-8", "replace")


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: probe_share.py <share_url>")
    url = sys.argv[1]
    final_url, html = fetch(url)
    print(f"请求: {url}")
    print(f"落地: {final_url}")
    print(f"长度: {len(html)} 字符")

    title = re.search(r"<title>(.*?)</title>", html, re.S)
    print(f"标题: {title.group(1).strip() if title else '未找到'}")
    print("-" * 60)

    # 记录最后一次出现的位置，越靠后通常越是真实数据
    found = {}
    for name, pat in PATTERNS.items():
        hits = re.findall(pat, html)
        if hits:
            found[name] = hits

    if not found:
        print("未命中任何 ID 模式。")
    for name, hits in found.items():
        uniq = list(dict.fromkeys(hits))
        print(f"{name:16s} 共 {len(hits)} 处, 去重 {len(uniq)}: {uniq[:8]}")

    print("-" * 60)
    for m in re.findall(r"https?://[^\"'\s<>]*kugou[^\"'\s<>]*", html)[:15]:
        print("URL:", m)


if __name__ == "__main__":
    main()
