#!/usr/bin/env python3
"""生成 M0 标注样本（50 首，按 9 类场合配额）。

流程：种子清单 → 搜索取 hash → 过滤版本变体 → 回查存在性 → 去重 → 写 CSV。
诚实标注：本脚本只验证「曲库存在」（exists），不验证「能唤起」（verified）。
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_songs import search, verify  # noqa: E402

# 版本变体过滤：命中即丢弃，避免落在翻唱/DJ/现场版上
BAD = ("live", "演唱会", "现场", "翻唱", "cover", "remix", "dj", "咚鼓",
       "钢琴版", "吉他版", "童声", "0.8x", "0.9x", "降调", "加速", "伴奏")

# (title, artist, venue) —— 每类按配额
CANDIDATES = [
    # home_solo 5
    ("夜的钢琴曲5", "石进", "home_solo"),
    ("小半", "陈粒", "home_solo"),
    ("理想三旬", "陈鸿宇", "home_solo"),
    ("斑马斑马", "宋冬野", "home_solo"),
    ("南山南", "马頔", "home_solo"),
    # home_social 6
    ("成都", "赵雷", "home_social"),
    ("平凡之路", "朴树", "home_social"),
    ("晴天", "周杰伦", "home_social"),
    ("红豆", "王菲", "home_social"),
    ("突然好想你", "五月天", "home_social"),
    ("小幸运", "田馥甄", "home_social"),
    # work_focus 6
    ("River Flows In You", "Yiruma", "work_focus"),
    ("卡农", "纯音乐", "work_focus"),
    ("Merry Christmas Mr. Lawrence", "坂本龙一", "work_focus"),
    ("Summer", "久石让", "work_focus"),
    ("天空之城", "久石让", "work_focus"),
    ("Kiss The Rain", "Yiruma", "work_focus"),
    # work_public 5
    ("云烟成雨", "房东的猫", "work_public"),
    ("奇妙能力歌", "陈粒", "work_public"),
    ("当你老了", "赵照", "work_public"),
    ("贝加尔湖畔", "李健", "work_public"),
    ("风吹麦浪", "李健", "work_public"),
    # venue_commercial 7
    ("玫瑰人生", "小野丽莎", "venue_commercial"),
    ("夏日漱石", "橘子海", "venue_commercial"),
    ("春风十里", "鹿先森乐队", "venue_commercial"),
    ("小情歌", "苏打绿", "venue_commercial"),
    ("旅行的意义", "陈绮贞", "venue_commercial"),
    ("想见你想见你想见你", "八三夭", "venue_commercial"),
    ("慢慢喜欢你", "莫文蔚", "venue_commercial"),
    # event_party 6
    ("Something Just Like This", "The Chainsmokers", "event_party"),
    ("Closer", "The Chainsmokers", "event_party"),
    ("Wake Me Up", "Avicii", "event_party"),
    ("Faded", "Alan Walker", "event_party"),
    ("野狼disco", "宝石Gem", "event_party"),
    ("卡路里", "火箭少女101", "event_party"),
    # event_ceremony 5
    ("今天你要嫁给我", "陶喆", "event_ceremony"),
    ("最美的期待", "周笔畅", "event_ceremony"),
    ("终于等到你", "张靓颖", "event_ceremony"),
    ("因为爱情", "陈奕迅", "event_ceremony"),
    ("求婚", "张靓颖", "event_ceremony"),
    # outdoor_motion 5
    ("Stronger", "Kanye West", "outdoor_motion"),
    ("Till I Collapse", "Eminem", "outdoor_motion"),
    ("奔跑", "羽泉", "outdoor_motion"),
    ("追梦赤子心", "GALA", "outdoor_motion"),
    ("怒放的生命", "汪峰", "outdoor_motion"),
    # transit 5
    ("稻香", "周杰伦", "transit"),
    ("七里香", "周杰伦", "transit"),
    ("告白气球", "周杰伦", "transit"),
    ("起风了", "买辣椒也用券", "transit"),
    ("岁月神偷", "金玟岐", "transit"),
]

FALLBACKS = [
    ("安和桥", "宋冬野", "home_solo"),
    ("消愁", "毛不易", "home_solo"),
    ("当你", "林俊杰", "home_social"),
    ("后来", "刘若英", "home_social"),
    ("Kiss The Rain", "李闰珉", "work_focus"),
    ("梦中的婚礼", "理查德·克莱德曼", "work_focus"),
    ("我要你", "任素汐", "work_public"),
    ("南方姑娘", "赵雷", "work_public"),
    ("City Of Stars", "Ryan Gosling", "venue_commercial"),
    ("Counting Stars", "OneRepublic", "event_party"),
    ("Sugar", "Maroon 5", "event_party"),
    ("Beautiful In White", "Westlife", "event_ceremony"),
    ("倔强", "五月天", "outdoor_motion"),
    ("海阔天空", "Beyond", "outdoor_motion"),
    ("平凡之路", "朴树", "transit"),
]

QUOTA = {
    "home_solo": 5, "home_social": 6, "work_focus": 6, "work_public": 5,
    "venue_commercial": 7, "event_party": 6, "event_ceremony": 5,
    "outdoor_motion": 5, "transit": 5,
}


def pick_one(title, artist, venue):
    """搜一首歌，返回第一条通过版本过滤且回查存在的记录。"""
    try:
        hits = search(f"{artist} {title}", 6)
    except Exception as e:
        print(f"  [!] 搜索失败 {title} - {artist}: {e}")
        return None
    for h in hits:
        name = h["title"].lower()
        if any(b in name for b in BAD):
            continue
        if len(h["hash"]) != 32:
            continue
        ok, _ = verify(h)
        if ok:
            return {"title": h["title"], "artist": h["artist"], "hash": h["hash"],
                    "duration": h["duration"], "venue": venue}
    return None


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "m0-sample.csv")
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    rows, seen, got = [], set(), {k: 0 for k in QUOTA}
    for title, artist, venue in CANDIDATES:
        if got[venue] >= QUOTA[venue]:
            continue
        print(f"[{venue}] {title} - {artist}")
        r = pick_one(title, artist, venue)
        if r and r["hash"] not in seen:
            seen.add(r["hash"])
            rows.append(r)
            got[venue] += 1
    # 配额未满时用备选补
    for title, artist, venue in FALLBACKS:
        if got[venue] >= QUOTA[venue]:
            continue
        r = pick_one(title, artist, venue)
        if r and r["hash"] not in seen:
            seen.add(r["hash"])
            rows.append(r)
            got[venue] += 1

    fields = ["sample_id", "venue", "title", "artist", "hash", "duration",
              "bpm", "camelot", "energy", "warmth", "density", "vocal",
              "familiarity", "edge", "confidence", "note"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(rows, 1):
            w.writerow({"sample_id": f"M0-{i:03d}", **r,
                        "bpm": "", "camelot": "", "energy": "", "warmth": "",
                        "density": "", "vocal": "", "familiarity": "", "edge": "",
                        "confidence": "", "note": ""})

    print("\n=== 配额完成情况 ===")
    for k, v in QUOTA.items():
        print(f"{k}: {got[k]}/{v}")
    print(f"总计 {len(rows)} 首 → {out}")


if __name__ == "__main__":
    main()
