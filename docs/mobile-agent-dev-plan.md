# 基于 Mobile Agent 的 kgJP 二次开发方案

日期：2026-11-03。前提：Mobile Agent v0.2.0 端到端唤起酷狗已真机验证成功。
本方案回答"怎么在它上面继续开发"，按侵入度从低到高分三个阶段，每阶段独立可用。

## 0. 三种开发姿态对比

| 姿态 | 做法 | 优点 | 缺点 | 适用 |
|---|---|---|---|---|
| A. Skill 层开发（已完成） | 用它的 skill 创建工具喂 `mobile-agent.md` | 零编译、零权限、热更新 | 曲库/选曲逻辑是"提示词里的一段文字"，模型执行有抖动 | 已跑通 ✅，作为基线保留 |
| B. 原生工具开发 | Fork 仓库，在 `:tools` 模块新增 KugouProvider 能力组 | 工具是真代码：确定性执行、结构化返回、细粒度权限 | 要跟上游版本维护 fork | **推荐主路线**，本方案主体 |
| C. 全 App 定制 | Fork 后改 UI/品牌/默认模型服务 | 可做成自己的产品 | 工程量最大、上游更新难合并 | 远期产品化才考虑 |

## 1. 环境与构建（先跑起来再说）

- 上游：`github.com/looper42/mobile_agent`（Apache-2.0，fork 自留）。
- 模块：`:app`（Compose UI）、`:agent-core`（会话/调度）、`:model`（供应商适配）、
  `:device`（Root/无障碍）、`:data`（Room/DataStore）、`:tools`（工具注册）——**我们要动的主要是 `:tools`**。
- 构建：JDK 17+，Android SDK（targetSdk 36），`./gradlew assembleDebug`；
  minSdk 24（Android 7.0），小米 10S 满足。
- 验证闭环：`adb install -r app-debug.apk`；MI 10S 开 USB/无线调试后可直装。

## 2. 阶段 B1：KugouProvider 原生能力组（核心增量）

### 2.1 设计四个原生工具

按它的公共工具契约（稳定 ID、输入/输出 Schema、副作用等级、超时/取消语义）：

| 工具 ID | 功能 | 副作用等级 | 实现要点 |
|---|---|---|---|
| `kugou_search` | 搜歌名 → 返回 hash/歌手/时长列表 | READ | 直连 `http://mobilecdn.kugou.com/api/v3/search/song`（OkHttp，超时 5s，失败如实报错） |
| `kugou_deep_link` | 拼 `kugou://start.weixin?cmd=212` 深链并唤起 | EXTERNAL_WRITE | 复用上游「系统功能」组的深链打开实现；参数校验 hash 为 32 位十六进制 |
| `kugou_recommend` | 场景 → 选曲（内置曲库 + 打分 + 去重） | READ | 把 `tool/kugou.py` 的 `score/pick/build_reason` 移植成 Kotlin；曲库放 assets JSON，随 APK 分发 |
| `kugou_history` | 查询最近播放记录 | READ | Room 加一张表，或先放内存 List（MVP） |

### 2.2 落点（对照架构文档）

- 新建能力提供者，实现公共工具接口并注册——上游约定"新工具只实现公共接口并注册，
  无须修改聊天页面或供应商适配器"。
- 授权：四个工具归入一个「酷狗音乐」能力组，UI 自动获得"每次询问/始终允许"两档开关，
  不用自己写授权面板。
- `kugou_deep_link` 属 EXTERNAL_WRITE：首次调用走现有批准面板，不需要新建授权机制。

### 2.3 Kotlin 代码骨架（示意）

```kotlin
class KugouProvider(private val context: Context) : CapabilityProvider {
    override val id = "kugou"
    override val displayName = "酷狗音乐"
    override val tools = listOf(searchTool, deepLinkTool, recommendTool, historyTool)

    // deepLinkTool 核心：与真机验证过的协议严格一致
    fun buildDeepLink(hash: String, filename: String): String {
        val payload = """{"cmd":212,"jsonStr":{"hash":"$hash","filename":"$filename","extname":"mp3"}}"""
        return "kugou://start.weixin?" + URLEncoder.encode(payload, "UTF-8")
    }
    // 唤起：Intent(ACTION_VIEW, Uri.parse(link)).addFlags(FLAG_ACTIVITY_NEW_TASK)
    //  捕获 ActivityNotFoundException → 返回结构化错误（未安装酷狗）
}
```

### 2.4 验收标准

1. 对话说"放首适合专注的歌"→ agent 调 `kugou_recommend` + `kugou_deep_link` → 酷狗自动播放；
   全过程工具卡显示真实参数与结果（不再依赖模型拼 URL）。
2. 搜不存在的歌：`kugou_search` 返回空列表，agent 如实说找不到，不编造 hash。
3. 卸载酷狗的设备上：`kugou_deep_link` 返回"未安装"结构化错误，聊天不崩。
4. 能力组开关关闭后，模型请求中不再包含这四个工具（上游已有过滤机制，验证即可）。

## 3. 阶段 B2：曲库与体验增强

1. **曲库 JSON 化**：`tool/library.py` 9 首 → `assets/kugou_library.json`，字段对齐
   （hash/artist/title/scene/vocal/instrument/energy/tags）；`fetch_songs.py` 改造为
   "生成 JSON"的离线流水线，hash 回查通过才入库。
2. **场景扩展**：5 → 10 个场景（通勤/睡前/健身/做饭/带娃…），`kugou_recommend` 支持模糊场景匹配。
3. **播放历史回灌**：`kugou_history` 结果进入上下文，agent 能说"上次你听过 X，换个口味"。
4. **resolve_share 能力**：分享链 `chain` → 解析 ID → 入库（把 `probe/probe_share.py` 的解析逻辑原生实现），
   对话里发个酷狗分享文本就能收藏进曲库。

## 4. 阶段 C（远期，可选）

- 改默认模型服务/品牌/图标，做独立发行版。
- 多音乐平台：QQ 音乐/网易云深链协议测绘后，把 Provider 抽象成 `MusicProvider` 接口，酷狗是第一个实现。
- 上游同步策略：`git remote add upstream`，定期 rebase；我们的增量全部收敛在
  `:tools` 的 KugouProvider + assets 曲库 + （C 阶段的 UI 资源），冲突面最小化。

## 5. 里程碑

| 里程碑 | 内容 | 判定 |
|---|---|---|
| M-B1 | fork 构建出 debug APK 并装上手机，聊天可用 | 编译+安装+一轮对话 |
| M-B2 | KugouProvider 四工具注册，`kugou_deep_link` 真机唤起 | 对话唤起酷狗（不靠模型拼 URL） |
| M-B3 | `kugou_recommend` 场景选曲真机 | "来点专注音乐"→自动播 |
| M-B4 | 曲库 JSON 化 + 扩到 50 首 + 历史回灌 | 连续 5 次场景提问不重复 |

## 6. 风险与边界

- 上游是早期项目（v0.2.0），公共工具接口可能变——所以增量全部收敛在一个 Provider 文件 + assets，
  接口变了只改一处。
- `mobilecdn.kugou.com` 是非官方接口，可能限流/变更——Provider 里做失败降级（返回曲库内结果）。
- 版权边界：本项目只做"推荐 + 唤起"，播放/会员/下载全部交给酷狗 App 自己处理，不碰音源。
EOF