# 安卓唤起酷狗音乐：可行路径与实测方案

> 结论先行：**能，而且有官方支持。** 但"点一下就跳到这首歌的播放页"有前提条件，
> 下面按可靠性分三层，每层都标注了可信来源和验证状态。

---

## 一、结论

安卓上唤起酷狗并跳到指定歌曲，有三层可用的手段，**可靠性从高到低**：

| 层 | 手段 | 是否需要 appid | 能否精确到单曲 | 可靠性 |
|---|---|---|---|---|
| **L1** | 官方 SDK `JumpKugouAPPUtils.openKugouAndPlayMusic` | ✅ 需要 | ✅ 能 | ★★★★★ |
| **L2** | URL Scheme `kugou://start.weixin?{"cmd":212,...}` | ❌ 不需要 | ✅ 能（按 hash） | ★★★☆ |
| **L3** | `intent://` + package 打开 App 首页 | ❌ 不需要 | ❌ 只能到首页 | ★★★★ |

**这是全部答案的核心**：如果只是"打开酷狗"，L3 就够且稳；如果要"打开就播这首歌"，必须走 L1 或 L2。

---

## 二、L1：官方 SDK（唯一 100% 保证的方案）

### 证据

酷狗开放平台《android客户端sdk接入文档》第 3 节「跳转相关」原文列出两个方法：

```java
JumpKugouAPPUtils.openKugou                                  // 3.1 打开酷狗APP
JumpKugouAPPUtils.openKugouAndPlayMusic                      // 3.2 打开酷狗APP，并跳转到酷狗播放页进行播放歌曲
OpenKugouH5Util.getKgPlayWebUrlForSong(hash, albumAudioId, name)  // 3.3 取 H5 播放 URL
```

来源：`https://open.kugou.com/docs/mini-player/#/android?v=3`

**3.2 的方法名直译就是"打开酷狗并播放音乐"**，这是官方对"唤起 App 到指定歌曲"这个需求给的正式答案。

### 关键约束

- **必须申请 appid / appkey**，在酷狗开放平台开通「曲库开放组件」，审核通过后才能下载 SDK。
- SDK 是 `aar`，需要**你自己的安卓 App** 集成（不能从网页/Agent 直接调用）。
- 文档里的「曲库开放计划」写明：**按调用次数计费**，费用需咨询客户经理。

→ **这条路的含义**：它不是"Agent 直接调用"，而是"你得先做个安卓 App，App 里集成 SDK"。
如果 kgJP 最终形态是独立 App，选它；如果只是想在对话里给个链接，这条路不适用。

### 所需参数
`hash` + `albumAudioId`（即 album_audio_id）。这两个我们**已经从分享链解析出来了**（见 `kugou-ids.md`）。

---

## 三、L2：URL Scheme（不需要 appid，值得先试）

### 格式

```
kugou://start.weixin?{"cmd":212,"jsonStr":{"hash":"<hash>","filename":"<歌手> - <歌名>","extname":"mp3"}}
```

实际使用时整个 JSON 部分必须 **URL 编码**。解码后的结构：

```json
{"cmd": 212, "jsonStr": {"hash": "...", "filename": "莫文蔚 - 阴天"}}
```

### 依据

第三方实测文章《NFC音乐墙避坑指南》（做 NFC 音乐墙的人需要把 URL 写进芯片，属于真实落地场景）明确给出：

- `cmd: 212` = 播放指定音频
- `jsonStr.hash` = **绝对必需**，定位音频的核心 ID
- `jsonStr.filename` = 建议保留，影响播放界面显示的歌曲名
- `jsonStr.extname` = 建议保留（如 mp3）
- `userid` / `u` / `h1` / `h2` 等用户字段 = **可安全删除**

⚠️ **未在同一台安卓机器上实机复验**。这条信息的可信度是"有真实落地案例"，不是"我亲眼验证过"。

### 对本项目的《潮汐》可直接生成

hash = `a4713521e4754b8ed3f09af1e41756e5`，
filename = `傅梦彤 - 潮汐 (Natural)`

对应链接已生成在 `probe/links.md`，可直接在安卓手机上点。

### 已知风险
- `start.weixin` 这个 path 名字暗示它原本是给微信/QQ 分享回流设计的，**官方可能随时改掉**。
- 不同酷狗版本可能行为不一致（老版本接受、新版本拒绝，或反之）。
- 未安装酷狗时，可能是静默失败，也可能是系统弹"没有应用可处理"。

---

## 四、L3：intent:// （打开 App 最稳，但只能到首页）

```html
<a href="intent://#Intent;scheme=kugou;package=com.kugou.android;end">打开酷狗</a>
```

- 包名 `com.kugou.android`（多个来源一致）。
- 这是 Android 官方推荐的应用间跳转方式，`package=` 能避免 scheme 被别的 App 抢注。
- **缺点：没有可靠的"落到指定歌曲"参数**。往 `intent://` 里塞 `hash=` 这类自定义参数，
  只有酷狗 App 自己声明对应的 `intent-filter` 并解析才会生效，这属于未公开行为。

### 桌面/浏览器里的写法（带 fallback）

```html
<a href="intent://play?hash=a4713521e4754b8ed3f09af1e41756e5#Intent;scheme=kugou;package=com.kugou.android;S.browser_fallback_url=https%3A%2F%2Fwww.kugou.com%2Fmixsong%2F4ltgkqde.html;end">
  在酷狗中播放
</a>
```

`browser_fallback_url` 是 Chrome 支持的官方机制：**没装 App 时自动跳去网页版**，不会出现死按钮。
这解决了之前担心的"静默失败"问题——**安卓上这一点比 iPad/mac 好办**。

---

## 五、其他线索（记录但优先级低）

搜索过程中还见到两个说法，**可信度低，不建议投入**：

- `kugouURL://`（某个"主流平台 scheme 合集"博客里出现）—— 无出处、无参数说明。
- `KugouKtvUrl://`（CSDN 老帖，2017 年）—— 疑似 K 歌子应用，与主 App 播放无关。

另外注意：`kugou://` 在 **iOS 上大概率不通**（苹果对未备案 scheme 的跨 App 调用限制更严），
不要把安卓验证成功的结果直接套到 iOS。

---

## 六、给 kgJP 的建议

按"你想做成什么形态"分叉：

**如果 kgJP 保持是 Agent 技能 / 网页卡片**
→ 只能用 L2 + L3。产出 `<a href="intent://...#Intent;...;S.browser_fallback_url=<mixsong页>;end">`。
   乐观情况下点开就播，最差情况落到网页单曲页。**没有 appid 依赖，可立刻开工。**

**如果 kgJP 要做成安卓 App**
→ 走 L1，申请 appid，集成 SDK，`openKugouAndPlayMusic(hash, albumAudioId)`。
   体验最好，有官方保证，但要过审 + 按量付费。

**通用设计原则（无论哪条路）**
1. **永远带 fallback**。安卓用 `browser_fallback_url`，其他端用 800ms 超时后跳 mixsong 页。
2. **点击前告知落点**。卡片上写清"将在酷狗 App 中播放"还是"打开网页版"，不要骗用户。
3. **hash 是唯一必需参数**，`album_audio_id` 是第二重要。其他都可以省。

---

## 七、下一步

- [ ] **拿一台安卓机，点 `probe/links.md` 里的测试链接**，记录：是否唤起、是否直接播放、是否落在正确歌曲
- [ ] 测未安装酷狗时 `intent://` 的 fallback 是否按预期跳网页
- [ ] 测酷狗不同版本（老版本 / 最新版）行为是否一致
- [ ] 决定 kgJP 最终形态：技能 / 网页卡片 / 独立 App —— **这决定走 L1 还是 L2**
