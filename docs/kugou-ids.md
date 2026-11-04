# 酷狗标识符与深链测绘

> 目的：确定「如何用一条链接精确打开某首歌，并尽可能唤起本机酷狗客户端」。
> 所有结论标注验证状态：✅ 实测通过 ｜ ❌ 实测失败 ｜ ⚠️ 推测未验

---

## 一、核心突破：分享链能反解出全部 ID

**输入**：`https://m.kugou.com/share/song.html?chain=DBwV9aG7V2`
**方式**：`probe/probe_share.py`（urllib + Android UA，抓原始 HTML 正则抽取）
**结果**：HTML 源码里带齐了所有标识符 ——

| 字段 | 值 |
|---|---|
| 歌名 | 潮汐 (Natural) |
| 歌手 | 傅梦彤 |
| `hash` | `a4713521e4754b8ed3f09af1e41756e5` |
| `songid` | `84785711` |
| `album_audio_id` | `278511146` |
| `album_id` | `39769270` |
| 时长 | 02:48 |

✅ **这解决了最大卡点**：之前网页搜索结果里只有歌名+歌手，拿不到 ID；
但只要有一台装了酷狗客户端、能"分享"的机器，或者用户随手贴的分享链，就能把 ID 全部反解出来。

---

## 二、✅ 已验证的链接格式

### L1 单曲页（网页，最可靠）

```
https://www.kugou.com/mixsong/4ltgkqde.html
```

✅ **实测落在《潮汐 - 傅梦彤》，标题正确，时长 02:48 一致。**

**mixsong_id 从哪来？** 分享链的 URL 片段就是它。
分享链 `https://m.kugou.com/share/song.html?chain=DBwV9aG7V2` 打开后，
页面里的规范链接是 `https://www.kugou.com/share/DBwV9aG7V2.html#4ltgkqde`，
**`#` 后面这 8 位就是 mixsong_id**。

规则：`mixsong_id` = 8 位、字母数字混合、通常以 `g` 开头（如 `g7251h15`、`4ltgkqde`、`g8c6scbc`）。

### L2 分享链（网页，已验证可开）

```
https://m.kugou.com/share/song.html?chain=DBwV9aG7V2     ✅
https://www.kugou.com/share/DBwV9aG7V2.html#4ltgkqde     ✅
```

### L3 官网播放器路由（首页实见，✅ 路由存在）

首页「热门频道」栏目的真实链接：

```
https://www.kugou.com/song/#fm_id=32&fm_name=%E5%AE%89%E9%9D%99
```

说明 `https://www.kugou.com/song/#<参数>` 是官网播放器的真实路由，支持 `#` 后传参。
⚠️ 但**是否支持 `#hash=...` 直接定位到单曲**未验证。

---

## 三、❌ 已排除的假设

**假设：用 share 的 chain 值直接拼 mixsong 路径。**
测 `https://www.kugou.com/share/g7251h15.html` ❌ 回落到首页。
结论：`www.kugou.com/share/<id>.html` 不是有效路由，别往这个方向试。

**假设：无效 mixsong id 会报错。**
测 `https://www.kugou.com/mixsong/1k7v5a09.html` ❌ **静默回落首页，不报错、不返回 404**。
→ **重要工程含义**：校验 id 是否有效，**只能靠比对页面标题是否含歌名**，不能靠 HTTP 状态码。
这必须写进校验层，否则会生成一堆"看起来正常但其实指向首页"的死链接。

---

## 四、⚠️ 未验证：客户端唤起协议

本环境没有酷狗客户端，**无法实测**。以下参数按公开资料推测，**必须实机验证后才能上线**：

| 格式 | 推测用途 | 风险 |
|---|---|---|
| `kugou://play?songid=84785711` | 直接播指定歌 | 参数名可能不是 `songid` |
| `kugou://play?hash=a4713521e4754b8ed3f09af1e41756e5` | 按 hash 播 | hash 可能是必需项 |
| `kugou://startmylist?...` | 打开我的列表 | 场景不符 |
| `web+kugou://...` | 带 web 回退的唤起 | iOS 支持，桌面端行为未知 |

**验证清单**（需要在装了客户端的 Win / Mac 上做）：
- [ ] 分别测 `songid` 与 `hash`，看哪个被接受、哪个必需
- [ ] 测未安装客户端时的行为（静默失败？弹窗？）
- [ ] 测 `kugou://` 到实际开始播放的延迟
- [ ] 测是否支持 `kugou://` 带"自动播放"参数（有些协议只打开页面不播放）

---

## 五、工程结论

1. **兜底链必须存在且永远可用**：`mixsong 页` → 失败则 `搜索页`。
   且因为失败是静默的，**必须做标题校验**才能判断成功与否。
2. **分享链是 ID 的黄金入口**。产品设计上应该鼓励用户贴分享链——
   比让用户报歌名靠谱得多，一次贴链就能拿到全部四个 ID。
3. **唤起协议是唯一未验证的环节**，也是"唤醒客户端"这个需求的全部难点所在。
   在没实机验证前，任何"点了就会自动播放"的承诺都不成立。
