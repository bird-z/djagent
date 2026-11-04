# kgJP

场景 → 音乐 → 一键跳转酷狗。

当用户在对话中描述某个场景（深夜赶 deadline、烦躁、剪视频找 BGM……），给出对味的歌，
并附一条能直接跳到酷狗播放页的链接。目标覆盖 ad 端 / Windows / macOS。

## 状态

- **手机端已上线**：<https://kgjp-music.app.workbuddy.host/?sharecode=ZKYOSRB7JM>
- Agent Tool 已接入（MCP），等待手动信任激活
- **端到端已真机验证（2026-11-03）**：Mobile Agent「系统功能」深链唤起酷狗并**自动播放指定曲目**
  （cmd=212 定点播放生效），无需 Root、无浏览器

## 文档

**产品需求与状态以 [`docs/PRD.md`](docs/PRD.md) 为准**，全部文档索引见 [`docs/README.md`](docs/README.md)。

专题文档：

- [`docs/ambience-system.md`](docs/ambience-system.md) — **氛围体系**（判断层核心资产）：8 轴受控词表、
  场合卡（Venue Card）字段与三张示例、12 条映射规则、数据契约、内部认同机制与一致性门槛。
  配 [`docs/ambience-glossary.md`](docs/ambience-glossary.md) 一页术语卡（标注前必读）。
- [`docs/scene-lifecycle.md`](docs/scene-lifecycle.md) — **场景 × 生命周期三段**：分场景（场景族→场景→场合卡）、
  场前编排（六步流程、三栏界面、六项校验、plan 交付物）、临场使用（只读池、5 个动作、事件记录与复盘）。
- [`docs/product-form.md`](docs/product-form.md) — **落地形态**：六种形态评分（H5/小程序/App/桌面编排台/Skill/硬件）、
  四阶段路径与出口条件、三层产品矩阵（判断层·C 端·B 端）、变现假设、形态风险对照。
- [`docs/research.md`](docs/research.md) — **DJ Agent 产品研究**：5 个同类产品对比（页面结构/主要数据/用户动作/优缺点）、
  手机端智能体能力边界、现状与实用的差距、本期不做清单、公开参考资料与待验证项。
- [`docs/brainstorm.md`](docs/brainstorm.md) — 头脑风暴稿：已验证的酷狗事实、产品形态分叉、
  选曲策略、跳转链路六种落法、三端差异、十个坑。
- [`docs/kugou-ids.md`](docs/kugou-ids.md) — 酷狗标识符与深链测绘：实测通过的链接格式、
  已排除的假设、未验证的客户端唤起协议。
- [`docs/android-launch.md`](docs/android-launch.md) — 安卓唤起酷狗：三层方案（官方 SDK / scheme / intent）与取舍。
- [`docs/no-browser-launch.md`](docs/no-browser-launch.md) — 无浏览器唤起：三条路径（adb 直控 / 手机本地 / 电脑端）与配对步骤，
  含真机验证结论。
- [`docs/android-agent-projects.md`](docs/android-agent-projects.md) — 安卓上能跑 Agent + 工具调用的开源项目盘点
  （ZorvAI / Operit / PokeClaw / Mobile Agent / Open Interpreter…）与 kgJP 推荐排序。
- [`docs/mobile-agent-deploy.md`](docs/mobile-agent-deploy.md) — Mobile Agent v0.2.0 装机指南（APK/sha256/模型配置/
  skill 安装/验证步骤），唤起酷狗走「系统功能」深链能力，不需要 Root。
- [`docs/mobile-agent-dev-plan.md`](docs/mobile-agent-dev-plan.md) — **基于 Mobile Agent 二次开发方案**：
  三种姿态（skill / 原生 KugouProvider / 全 App 定制）、四工具设计、Kotlin 骨架、里程碑与风险。
- [`probe/probe_share.py`](probe/probe_share.py) — 分享链探测脚本，输入分享 URL，输出全部 ID。
- [`probe/make_links.py`](probe/make_links.py) — 分享链 → 全套测试链接生成器。
- [`probe/test.html`](probe/test.html) — 手机可打开的唤起测试页（5 种链接对照）。

## 手机端（公网）

- [`phone/README.md`](phone/README.md) — 线上链接、架构、部署踩坑、已知限制。
- `phone/` 为部署目录：`app.py` + `library.py` + `kugou.py` + `static/index.html`。

> `library.py` / `kugou.py` 与 `tool/` 下同名文件是同一份逻辑，修改时两边需同步。

## Agent Tool（MCP）

- [`tool/server.py`](tool/server.py) — 手写 MCP server，零依赖，JSON-RPC over stdio。
- [`tool/library.py`](tool/library.py) — 9 首曲库 + 5 个场景定义。
- [`tool/kugou.py`](tool/kugou.py) — 深链构造 + 选曲打分 + 分享链解析。
- [`tool/fetch_songs.py`](tool/fetch_songs.py) — 搜索接口批量取曲 + hash 回查验证。
- [`tool/README.md`](tool/README.md) — 接入方式、四个工具、设计决定、已知限制。

四个工具：`recommend_music` / `resolve_share` / `list_scenes` / `library_stats`。

## Skill（手机版 Agent 可用）

- [`skills/kugou-launch/SKILL.md`](skills/kugou-launch/SKILL.md) — 供手机版 agent 加载的技能文件：
  深链协议 + 各平台唤起命令（am start / termux-open-url / xdg-open / start / open）、
  hash 获取方法、已验证曲目、未验证声明与降级方案。
- [`skills/kugou-launch/mobile-agent.md`](skills/kugou-launch/mobile-agent.md) — 同一技能的
  Mobile Agent 适配版：不走 shell，改走「系统功能」深链能力 + 设备工具降级。
- [`skills/device-bridge/SKILL.md`](skills/device-bridge/SKILL.md) — **设备桥技能（云端 agent 可用）**：
  任意云端 agent 通过 `POST /device/task` 远程操控用户手机（放歌 / 场景选曲 / 通知 / 剪贴板），
  拉模式零配置，手机端不暴露端口。

## MVP

- [`mvp/index.html`](mvp/index.html) — 单文件 MVP，10.6 KB，无依赖，离线可用。
- [`mvp/README.md`](mvp/README.md) — 传到小米 10S 的三种方式 + 跑通判定 + 排查表。

## 已验证的技术事实

1. 酷狗网页搜索结果**不含单曲 ID**，只有歌名 + 歌手 + 专辑 ID。
2. 单曲页 URL 规则：`https://www.kugou.com/mixsong/<mixsong_id>.html`，✅ 实测可打开指定歌曲。
3. `curl` 直连酷狗接口会被沙箱安全策略拦截，WebFetch 通道可用。
4. **分享链能反解出全部 ID**：`m.kugou.com/share/song.html?chain=XXX` 的 HTML 源码里带
   `hash` / `songid` / `album_audio_id` / `album_id`；打开后规范链接的 `#` 片段即 `mixsong_id`。
5. **无效 mixsong id 静默回落首页，不返回 404** —— 校验只能靠比对页面标题，不能靠状态码。
