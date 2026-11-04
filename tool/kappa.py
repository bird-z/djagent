#!/usr/bin/env python3
"""M0 标注一致性计算：有序轴加权 Cohen's κ + 场合类型 Krippendorff's α。

用法:
    python3 kappa.py A.csv B.csv          # 两份标注表对比
    python3 kappa.py --selftest           # 内置用例自检

标注表要求（UTF-8 CSV）：列含 sample_id, venue,
以及 energy/warmth/density/vocal/familiarity/edge（有序轴，整数）。

判定门槛（见 AGENTS.md 与氛围体系 §7）：
    有序轴加权 κ ≥ 0.60 ；场合类型 α ≥ 0.70
未达标时的处置是「改轴定义」，不是「换标注员」。
"""

import csv
import sys
from collections import Counter, defaultdict

ORDINAL_AXES = ["energy", "warmth", "density", "vocal", "familiarity", "edge"]
AXIS_RANGE = {           # 每轴的合法档位，用于加权
    "energy": (1, 7), "warmth": (1, 3), "density": (1, 3),
    "vocal": (1, 4), "familiarity": (1, 4), "edge": (1, 3),
}
NOMINAL_AXIS = "venue"


def load(path):
    with open(path, encoding="utf-8") as f:
        return {r["sample_id"]: r for r in csv.DictReader(f)}


def weighted_kappa(pairs, lo, hi):
    """有序轴：二次加权 Cohen's κ。pairs = [(a, b), ...]"""
    if not pairs:
        return None
    k = hi - lo + 1
    observed = Counter(pairs)
    n = len(pairs)
    row = Counter(a for a, _ in pairs)
    col = Counter(b for _, b in pairs)
    num = den = 0.0
    for i in range(lo, hi + 1):
        for j in range(lo, hi + 1):
            w = 1 - ((i - j) ** 2) / ((k - 1) ** 2)      # 二次一致权重
            o = observed.get((i, j), 0) / n
            e = (row.get(i, 0) / n) * (col.get(j, 0) / n)
            num += w * o
            den += w * e
    if den == 0 or den == 1:
        return 1.0 if num == 1 else None
    # κ = (Po_w - Pe_w) / (1 - Pe_w)
    return (num - den) / (1 - den)


def krippendorff_alpha_nominal(units):
    """名义变量 α。units = {unit_id: [标注值, ...]}"""
    n_total = sum(len(v) for v in units.values())
    if n_total < 2:
        return None
    do_num = 0.0
    for vals in units.values():
        m = len(vals)
        if m < 2:
            continue
        counts = Counter(vals)
        for c, n_uc in counts.items():
            do_num += n_uc * (m - n_uc) / (m - 1)
    Do = do_num / n_total
    all_vals = [v for vals in units.values() for v in vals]
    n_c = Counter(all_vals)
    De = sum(v * (n_total - v) for v in n_c.values()) / (n_total * (n_total - 1))
    return 1 - Do / De if De else None


def agreement(pairs):
    return sum(1 for a, b in pairs if a == b) / len(pairs) if pairs else None


def evaluate(a_path, b_path):
    A, B = load(a_path), load(b_path)
    ids = sorted(set(A) & set(B))
    if not ids:
        raise SystemExit("两份标注没有共同的 sample_id")

    print(f"共同样本 {len(ids)} 条（A {len(A)} / B {len(B)}）\n")
    print(f"{'轴':<14}{'n':>4}{'一致率':>8}{'κ / α':>10}{'门槛':>7}  判定")
    print("-" * 56)

    results = {}
    for axis in ORDINAL_AXES:
        lo, hi = AXIS_RANGE[axis]
        pairs = []
        for i in ids:
            try:
                pairs.append((int(A[i][axis]), int(B[i][axis])))
            except (KeyError, ValueError):
                continue
        k = weighted_kappa(pairs, lo, hi)
        ag = agreement(pairs)
        ok = k is not None and k >= 0.60
        results[axis] = k
        print(f"{axis:<14}{len(pairs):>4}{ag:>9.0%}{(k if k is not None else float('nan')):>10.2f}{'≥0.60':>7}  "
              f"{'通过' if ok else '未达标'}")

    units = defaultdict(list)
    for i in ids:
        for src in (A, B):
            v = src[i].get(NOMINAL_AXIS, "").strip()
            if v:
                units[i].append(v)
    alpha = krippendorff_alpha_nominal(units)
    ok = alpha is not None and alpha >= 0.70
    print(f"{NOMINAL_AXIS:<14}{len(ids):>4}{'-':>9}{(alpha if alpha is not None else float('nan')):>10.2f}"
          f"{'≥0.70':>7}  {'通过' if ok else '未达标'}")

    print("\n结论：")
    weak = [a for a, v in results.items() if v is not None and v < 0.60]
    if weak:
        print(f"  未达标轴：{', '.join(weak)} → 先改判定问题与档位定义，再重测（不要换标注员）")
    if alpha is not None and alpha < 0.70:
        print(f"  {NOMINAL_AXIS} 未达标 → 检查 9 类场合的边界（尤其 work_public vs venue_commercial）")
    if not weak and alpha is not None and alpha >= 0.70:
        print("  全部达标 → 可冻结 v1.0，进入 P3 盲评")
    return weak, alpha


def selftest():
    """内置用例：完全一致应为 1.0；完全分歧应为 0 或负。"""
    perfect = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
    k = weighted_kappa(perfect, 1, 7)
    assert abs(k - 1.0) < 1e-9, k
    systematic = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
    k2 = weighted_kappa(systematic, 1, 7)
    # 二次加权下"整体偏 1 档"约 0.8，这是加权 κ 的固有特性，不是 bug
    assert k2 is not None and 0.7 < k2 < 0.9, k2

    extreme = [(1, 7), (2, 7), (3, 7), (1, 6), (2, 6)]
    k3 = weighted_kappa(extreme, 1, 7)
    assert k3 is not None and k3 < 0.6, k3

    units_same = {"u1": ["a", "a"], "u2": ["b", "b"], "u3": ["c", "c"]}
    assert abs(krippendorff_alpha_nominal(units_same) - 1.0) < 1e-9
    units_diff = {"u1": ["a", "b"], "u2": ["b", "c"], "u3": ["c", "a"]}
    a = krippendorff_alpha_nominal(units_diff)
    assert a is not None and a < 0.7, a
    print("自检通过：κ 与 α 计算符合预期")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif len(sys.argv) >= 3:
        evaluate(sys.argv[1], sys.argv[2])
    else:
        print(__doc__)
