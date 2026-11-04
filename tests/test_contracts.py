"""契约测试：守住数据与深链的硬约束，防止改动悄悄破坏既有事实。

跑法（仓库根目录）：
    python3 -m unittest discover -s tests -v

覆盖：
1. 曲库字段与 hash 格式
2. 深链可解码且 cmd=212、hash 与曲目一致
3. 案例文档里的深链 hash 必须来自曲库或 M0 样本（不许手编）
4. M0 样本 50 条、9 类配额、hash 合法且不重复
5. docs 内相对链接必须存在（防止文档搬家后死链）
"""

import csv
import json
import os
import re
import sys
import unittest
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tool"))

import kugou                      # noqa: E402
from library import LIBRARY, SCENES  # noqa: E402

HEX32 = re.compile(r"^[0-9a-f]{32}$")
VENUES = {"home_solo", "home_social", "work_focus", "work_public",
          "venue_commercial", "event_party", "event_ceremony",
          "outdoor_motion", "transit"}


def load_sample():
    p = os.path.join(ROOT, "data", "m0-sample.csv")
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestLibrary(unittest.TestCase):
    def test_hash_format(self):
        for s in LIBRARY:
            self.assertRegex(s["hash"], HEX32, f"{s['title']} hash 非法")

    def test_required_fields(self):
        for s in LIBRARY:
            for k in ("id", "title", "artist", "hash", "vocal", "energy", "tags"):
                self.assertIn(k, s, f"{s.get('title')} 缺字段 {k}")

    def test_no_duplicate_hash(self):
        hashes = [s["hash"] for s in LIBRARY]
        self.assertEqual(len(hashes), len(set(hashes)), "曲库存在重复 hash")

    def test_scenes_valid(self):
        for key, sc in SCENES.items():
            self.assertIn("label", sc, f"{key} 缺 label")
            lo, hi = sc["want_energy"]
            self.assertLessEqual(lo, hi, f"{key} 能量区间反了")


class TestDeepLink(unittest.TestCase):
    def test_decode_roundtrip(self):
        song = {"hash": "a4713521e4754b8ed3f09af1e41756e5",
                "artist": "傅梦彤", "title": "潮汐 (Natural)"}
        link = kugou.play_scheme(song)
        self.assertTrue(link.startswith("kugou://start.weixin?"))
        payload = json.loads(urllib.parse.unquote(link.split("?", 1)[1]))
        self.assertEqual(payload["cmd"], 212)
        self.assertEqual(payload["jsonStr"]["hash"], song["hash"])
        self.assertEqual(payload["jsonStr"]["extname"], "mp3")
        self.assertIn(song["artist"], payload["jsonStr"]["filename"])


class TestCaseDocLinks(unittest.TestCase):
    """案例文档里的深链必须能解码，且 hash 出现在曲库或 M0 样本中。"""

    def test_links_are_known(self):
        known = {s["hash"] for s in LIBRARY} | {r["hash"] for r in load_sample()}
        case_file = os.path.join(ROOT, "docs", "case-meetup-pep.md")
        with open(case_file, encoding="utf-8") as f:
            text = f.read()
        links = re.findall(r"(kugou://start\.weixin\?\S+)", text)
        self.assertGreaterEqual(len(links), 3, "案例里应有至少 3 条深链")
        for link in links:
            payload = json.loads(urllib.parse.unquote(link.split("?", 1)[1]))
            self.assertEqual(payload["cmd"], 212)
            self.assertIn(payload["jsonStr"]["hash"], known,
                          f"深链 hash 不在已知曲库: {payload['jsonStr']['hash']}")


class TestM0Sample(unittest.TestCase):
    def setUp(self):
        self.rows = load_sample()

    def test_count_and_quota(self):
        self.assertEqual(len(self.rows), 50, "M0 样本应为 50 首")
        counts = {}
        for r in self.rows:
            counts[r["venue"]] = counts.get(r["venue"], 0) + 1
        self.assertEqual(set(counts), VENUES, "必须覆盖 9 类场合")
        self.assertEqual(sum(counts.values()), 50)

    def test_hash_valid_and_unique(self):
        hashes = [r["hash"] for r in self.rows]
        for h in hashes:
            self.assertRegex(h, HEX32)
        self.assertEqual(len(hashes), len(set(hashes)), "M0 样本存在重复 hash")

    def test_annotation_columns_empty(self):
        """交付时标注列必须留空——预填会让双人盲标失去意义。"""
        for r in self.rows:
            for col in ("bpm", "energy", "warmth", "density", "vocal", "familiarity", "edge"):
                self.assertEqual(r[col], "", f"{r['sample_id']} 的 {col} 被预填了")


class TestDocsLinks(unittest.TestCase):
    LINK = re.compile(r"\]\(([^)#][^)]*?\.md)\)")

    def test_relative_links_exist(self):
        docs_dir = os.path.join(ROOT, "docs")
        missing = []
        for name in sorted(os.listdir(docs_dir)):
            if not name.endswith(".md"):
                continue
            with open(os.path.join(docs_dir, name), encoding="utf-8") as f:
                text = f.read()
            for target in self.LINK.findall(text):
                if target.startswith(("http://", "https://")):
                    continue
                path = os.path.normpath(os.path.join(docs_dir, target))
                if not os.path.exists(path):
                    missing.append(f"{name} → {target}")
        self.assertEqual(missing, [], "存在失效链接：" + "; ".join(missing))


if __name__ == "__main__":
    unittest.main(verbosity=2)
