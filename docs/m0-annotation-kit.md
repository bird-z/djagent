# M0 标注套件：50 首双盲标注操作手册

> 版本 v0.1 ｜ 2026-11-04 ｜ 对应 PRD M0（判断层验证）
> 目标：验证「8 轴词表是否可被不同人稳定判定」，拿到 κ / α 数据，决定要不要进入 H5 开发。

---

## 1. 这一步为什么不能跳过

M0 是唯一有 Kill 权的阶段。若两人对同一首歌的能量、人声判断都不一致，
后面的推荐、编排、理由全部建立在流沙上——**先证伪，比先写代码便宜 100 倍**。

验收门槛（与氛围体系 §7 一致）：

| 指标 | 门槛 | 未达标怎么办 |
|---|---|---|
| 有序轴加权 Cohen's κ | ≥ 0.60 | 改判定问题与档位定义，**不换标注员** |
| 场合类型 Krippendorff's α | ≥ 0.70 | 检查 9 类场合的边界（尤其 work_public vs venue_commercial） |
| 场合卡字段一致率 | ≥ 80% | 见 P2 阶段，本套件不含 |

---

## 2. 样本从哪来

`data/m0-sample.csv`，50 首，按 9 类场合配额：home_solo 5 / home_social 6 /
work_focus 6 / work_public 5 / venue_commercial 7 / event_party 6 /
event_ceremony 5 / outdoor_motion 5 / transit 5。

生成方式：`tool/m0_sample.py` —— 种子清单 → 酷狗搜索取 hash → 过滤版本变体
（live/翻唱/remix/DJ/伴奏等）→ 回查确认存在 → 去重。

**诚实标注**：这 50 首只验证了 `exists`（酷狗曲库存在），**没有逐首真机验证 `verified`**。
标注的是「这首歌听起来如何」，与能否唤起无关。

### 2.1 样本清单

| # | 场合 | 曲目 | 艺人 | hash（前8位） | 时长 |
|---|---|---|---|---|---|
| M0-001 | home_solo | 夜的钢琴曲5 (纯音乐) | 石进 | `4b11c876` | 2:13 |
| M0-002 | home_solo | 小半 | 陈粒 | `afea9ffe` | 4:57 |
| M0-003 | home_solo | 理想三旬 | 陈鸿宇 | `8267b85e` | 3:30 |
| M0-004 | home_solo | 斑马，斑马 | 宋冬野 | `e8d0f5b0` | 4:13 |
| M0-005 | home_solo | 南山南 | 马頔 | `8bb9a346` | 5:25 |
| M0-006 | home_social | 成都 | 赵雷 | `faa0470f` | 5:28 |
| M0-007 | home_social | 平凡之路 | 朴树 | `2be5de80` | 5:01 |
| M0-008 | home_social | 晴天 | 周杰伦 | `b3a52a7a` | 4:29 |
| M0-009 | home_social | 红豆 | 王菲 | `aef916a1` | 4:16 |
| M0-010 | home_social | 突然好想你 | 五月天 | `cf67fce6` | 4:25 |
| M0-011 | home_social | 小幸运 | 田馥甄 | `d9baac26` | 4:23 |
| M0-012 | work_focus | 너의 마음속엔 강이 흐른다 | Yiruma、Ruvin(루빈) | `a32022c2` | 3:42 |
| M0-013 | work_focus | 卡农 (经典钢琴曲纯音乐) | jaycd | `fdef9290` | 2:42 |
| M0-014 | work_focus | Merry Christmas Mr. Lawrence | 坂本龍一 | `6ce3ff71` | 5:23 |
| M0-015 | work_focus | Summer (黑胶版) | 久石让、London Voices、The London Symphony Orchestra | `40fd8f18` | 3:59 |
| M0-016 | work_focus | 天空之城 | 久石让、游学志 | `7f67ce85` | 4:13 |
| M0-017 | work_focus | Kiss The Rain | Peter Bruce、Yiruma | `05d82f77` | 4:25 |
| M0-018 | work_public | 云烟成雨 | 房东的猫 | `d272a0c9` | 4:00 |
| M0-019 | work_public | 奇妙能力歌 | 陈粒 | `899a15ae` | 4:13 |
| M0-020 | work_public | 当你老了 (2012版) | 赵照 | `5278f8e3` | 5:09 |
| M0-021 | work_public | 贝加尔湖畔 | 李健 | `407277cf` | 4:05 |
| M0-022 | work_public | 风吹麦浪 | 李健 | `24a3e862` | 4:07 |
| M0-023 | venue_commercial | LA VIE EN ROSE | 小野リサ | `5d7a5ca7` | 4:44 |
| M0-024 | venue_commercial | 夏日漱石 (Summer Cozy Rock) | 橘子海 | `25ac4d5d` | 4:23 |
| M0-025 | venue_commercial | 春风十里 | 鹿先森乐队 | `7ce0ea56` | 6:15 |
| M0-026 | venue_commercial | 小情歌 | 苏打绿 | `14439dfe` | 4:33 |
| M0-027 | venue_commercial | 旅行的意义 | 陈绮贞 | `5b906e6b` | 4:04 |
| M0-028 | venue_commercial | 想见你想见你想见你 | 八三夭乐团 | `aaa0bd15` | 3:59 |
| M0-029 | venue_commercial | 慢慢喜欢你 | 莫文蔚 | `5b44a396` | 3:40 |
| M0-030 | event_party | Something Just Like This | The Chainsmokers、Coldplay | `681810a7` | 4:07 |
| M0-031 | event_party | Closer | The Chainsmokers、Halsey | `285f31c6` | 4:05 |
| M0-032 | event_party | Wake Me Up | Avicii、Aloe Blacc | `0d6fb2d2` | 4:09 |
| M0-033 | event_party | Faded | Alan Walker | `b35714e4` | 3:32 |
| M0-034 | event_party | 野狼disco | 宝石Gem | `5ecc1525` | 3:56 |
| M0-035 | event_party | 卡路里 [mqms2].flac | 火箭少女101 | `c764ee63` | 0:13 |
| M0-036 | event_ceremony | 今天你要嫁给我 | 陶喆、蔡依林 | `8c044816` | 4:32 |
| M0-037 | event_ceremony | 最美的期待 | 周笔畅 | `5ecd7fe8` | 3:30 |
| M0-038 | event_ceremony | 终于等到你 | 张靓颖 | `5f725154` | 4:55 |
| M0-039 | event_ceremony | 因为爱情 | 陈奕迅、王菲 | `16508290` | 3:36 |
| M0-040 | event_ceremony | 野心家 | 张靓颖 | `1789ad88` | 4:42 |
| M0-041 | outdoor_motion | Stronger | Ye (侃爷)、Daft Punk | `b3f57e52` | 5:17 |
| M0-042 | outdoor_motion | 'Till I Collapse | Eminem、Nate Dogg | `2ced553d` | 4:57 |
| M0-043 | outdoor_motion | 奔跑 | 羽泉、黄征 | `e2cc6f43` | 3:13 |
| M0-044 | outdoor_motion | 追梦赤子心 | GALA | `ef3e3c78` | 5:17 |
| M0-045 | outdoor_motion | 怒放的生命 | 汪峰 | `41b924c8` | 4:34 |
| M0-046 | transit | 稻香 | 周杰伦 | `8909e180` | 3:43 |
| M0-047 | transit | 七里香 | 周杰伦 | `9218d816` | 4:59 |
| M0-048 | transit | 告白气球 | 周杰伦 | `68885797` | 3:35 |
| M0-049 | transit | 起风了 | 买辣椒也用券 | `27b16858` | 5:21 |
| M0-050 | transit | 再见 你好 | 金玟岐 | `c92a4d28` | 4:14 |

---

## 3. 标注表结构

每人一份 CSV，列如下（`data/m0-sample.csv` 已含前三列与空标注列，直接复制两份改名即可）：

| 列 | 取值 | 判定依据 |
|---|---|---|
| `sample_id` | M0-001 … | 勿改 |
| `venue` | 9 类之一 | 这首歌**最适合**的场合（不是"能放"） |
| `bpm` | 整数或 `unknown` | 用 Tunebat/SongBPM 查，查不到写 `unknown`，**禁止猜** |
| `camelot` | `1A`-`12B` 或 `unknown` | 同上 |
| `energy` | 1-7 | 术语卡：如果这段音乐是个人，他多兴奋 |
| `warmth` | 1-3 | 听起来暖还是冷 |
| `density` | 1-3 | 同时有几层声音在动 |
| `vocal` | 1-4 | 人声占多大位置 |
| `familiarity` | 1-4 | 对 25-35 岁一线城市人群的熟悉度 |
| `edge` | 1-3 | 扎不扎耳朵 |
| `confidence` | 0-1 | 你对本行标注的整体把握 |
| `note` | 自由文本 | 有争议时写一句理由，供仲裁用 |

**三条纪律**：
1. 用判定问题，不用"我感觉"。
2. 每个取值要在心里找到锚点曲（术语卡里的校准例）。
3. 拿不准就填 `confidence` ≤ 0.5 并在 `note` 写原因——**不确定本身是有用数据**。

---

## 4. 执行流程（两人，约 3 小时）

| 步骤 | 内容 | 产出 |
|---|---|---|
| 1 | 两人各自通读术语卡（`docs/ambience-glossary.md`），不超过 10 分钟 | — |
| 2 | 各自独立标注 50 首，**全程不讨论、不看对方结果** | `ann-A.csv`、`ann-B.csv` |
| 3 | 跑一致性计算（见 §5） | κ/α 报告 |
| 4 | 只对未达标的轴开 60 分钟对齐会，逐条看分歧样本 | 修订后的术语卡 v0.2 |
| 5 | 修订后重标 20 首（可复用原样本），再测 | 第二轮 κ/α |
| 6 | 全部达标 → 冻结 `ambience-system v1.0` | 版本号 + 变更记录 |

**关键规则**：分歧不是"谁错了"，是"定义哪里不够清楚"。每一条分歧都要落到
"判定问题需要怎么改"，改完重测——这是把主观判断变成可共识体系的唯一办法。

---

## 5. 计算与命令

```bash
# 1) 准备两份标注（从样本复制，只填标注列）
cp data/m0-sample.csv data/ann-A.csv
cp data/m0-sample.csv data/ann-B.csv

# 2) 计算一致性（有序轴加权 κ + 场合 α）
python3 tool/kappa.py data/ann-A.csv data/ann-B.csv

# 3) 计算器自检（改过 kappa.py 后必跑）
python3 tool/kappa.py --selftest
```

输出示例（假数据，仅示意格式）：

```
轴                n     一致率     κ / α     门槛  判定
energy          50      10%      0.13  ≥0.60  未达标
venue           50        -      1.00  ≥0.70  通过
```

**读数注意**：κ 在样本方差很小时会趋近 0，即使表面一致率不低——这是 κ 悖论，
不是计算错误。所以样本必须覆盖各档位（能量 1-7 都要有歌），否则结论不可信。

---

## 6. 常见坑

| 坑 | 后果 | 规避 |
|---|---|---|
| 两人先讨论再标 | κ 虚高，体系假成立 | 独立标注，标完再对答案 |
| 只标自己熟的歌 | 样本偏差 | 50 首全标，不跳 |
| BPM 猜一个填 | 后续排序全错 | 查不到就写 `unknown` |
| 未达标就换人重标 | 永远达不到门槛 | 改定义，不改人 |
| 用"好听/不好听"代替档位 | κ 极低且无改进方向 | 严格按判定问题 |

---

## 7. 完成后的产物

| 产物 | 位置 | 用途 |
|---|---|---|
| 标注数据集 | `data/ann-A.csv`、`data/ann-B.csv` | M0 证据，进仓库（不含个人信息） |
| 一致性报告 | 贴到 PR 或 `docs/m0-report.md` | 决定是否进 M1 的依据 |
| 术语卡修订 | `docs/ambience-glossary.md` v0.2 | 版本号 + 变更记录 |
| 冻结声明 | `docs/ambience-system.md` 顶部 | `v1.0 冻结于 YYYY-MM-DD，κ=…，α=…` |

---

## 8. 自动化守护

`tests/test_contracts.py` 已锁定以下约束，任何改动破坏它们 CI 会红：

- 样本必须 50 条、覆盖 9 类场合、hash 合法且不重复
- **标注列必须留空**（预填会让双盲失去意义）
- 案例文档里的深链 hash 必须来自曲库或样本（防止手编 hash）
- `docs/` 内相对链接不得失效

CI 配置：`.github/workflows/ci.yml`（语法编译 + 契约测试 + κ 自检）。
