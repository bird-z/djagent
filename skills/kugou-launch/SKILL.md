---
name: kugou-launch
title: 打开酷狗音乐并播放指定歌曲
description: 通过深链直接唤起酷狗音乐 App 播放歌曲。当用户说"打开酷狗音乐"、"播放XX歌"、"来点适合XX的音乐"并要求跳转酷狗时使用。支持 Android（含 Termux）、Windows、macOS。触发词：酷狗、kugou、播放音乐、跳转酷狗。
version: 0.1.0
---

# 酷狗音乐唤起 Skill

## 目标

给定一首歌的信息（至少需要 `hash`），拼出深链并用系统命令直接唤起酷狗 App 播放，**不经过浏览器**。

## 深链协议（已确认的酷狗分享回流协议）

```
kugou://start.weixin?{"cmd":212,"jsonStr":{"hash":"<32位hash>","filename":"<歌手> - <歌名>","extname":"mp3"}}
```

- `cmd=212` 含义：播放指定音频
- `hash` **必需**（32 位十六进制），没有 hash 只能打开 App 不能定点播放
- `filename` 建议保留，用于酷狗端匹配校验
- JSON 需整体 URL 编码（encodeURIComponent / `urllib.parse.quote(..., safe="")`）后再拼接

### 编码示例

原始 payload：
```json
{"cmd":212,"jsonStr":{"hash":"a4713521e4754b8ed3f09af1e41756e5","filename":"傅梦彤 - 潮汐","extname":"mp3"}}
```
URL 编码后拼成：
```
kugou://start.weixin?%7B%22cmd%22%3A212%2C%22jsonStr%22%3A%7B%22hash%22%3A%22a4713521e4754b8ed3f09af1e41756e5%22%2C%22filename%22%3A%22%E5%82%85%E6%A2%A6%E5%BD%A2%20-%20%E6%BD%AE%E6%B1%90%22%2C%22extname%22%3A%22mp3%22%7D%7D
```

## 各平台唤起命令

### Android（Termux 环境优先）

按顺序尝试，第一个成功即停：

```bash
# 1. am start（Termux / adb shell 均可，最直接）
am start -a android.intent.action.VIEW -d "<URL编码后的深链>" com.kugou.android

# 2. termux-open-url（Termux）
termux-open-url "<URL编码后的深链>"

# 3. xdg-open（兜底）
xdg-open "<URL编码后的深链>"
```

包名：`com.kugou.android`

### Windows（cmd）

```cmd
start "" "kugou://start.weixin?<URL编码后的深链>"
```

### macOS

```bash
open "kugou://start.weixin?<URL编码后的深链>"
```

### 浏览器兜底

唤起失败时给用户这个链接（网页端播放页）：
```
https://m.kugou.com/share/song.html?chain=<分享chain>
```
或官方网页播放器格式（需 album_audio_id / hash，见下方"获取 hash"）。

## 获取 hash（当用户只说歌名时）

酷狗搜索接口（无需 key）：

```bash
curl "http://mobilecdn.kugou.com/api/v3/search/song?format=json&keyword=<URL编码歌名>&page=1&pagesize=5"
```

返回 JSON 中取 `data.info[0].hash`。注意：
- 用 `http` 而非 `https`（`msearchcdn` 节点证书有 hostname mismatch 问题）
- 选第一个结果前核对歌名和歌手是否匹配用户意图

## 已验证曲目（可直接引用）

| 歌曲 | hash | 备注 |
|---|---|---|
| 傅梦彤《潮汐 (Natural)》 | `a4713521e4754b8ed3f09af1e41756e5` | hash 经回查确认存在 |

## 未验证声明（2026-11-03 部分验证）

1. `kugou://start.weixin?cmd=212` 协议**已在小米 10S 真机验证：唤起酷狗并自动播放指定曲目均生效**
   （通道：Mobile Agent v0.2.0「系统功能」打开深链接，无需 Root）。其他机型/ROM 仍可能行为不同，首次使用时确认一次。
2. 若深链在个别设备无效，降级方案：只打开 App（`monkey -p com.kugou.android -c android.intent.category.LAUNCHER 1`），再由用户手动搜索。
3. `verified` 与 `exists` 是两回事：曲库里存在 ≠ 唤起能播放（在验证过的设备上此条已消除）。

## 选曲辅助（可选）

若 agent 需要根据场景推荐歌曲，本项目已内置 9 首曲库 + 5 场景（focus/tired/restless/nostalgia/bgm），见 `/home/bird/work/kgJP/tool/library.py`，含打分与去重逻辑（`kugou.py` 的 `pick`）。手机版可复制这两个文件随 skill 携带。

## 快速自检

拿到本 skill 后可先跑一次最小验证（Android/Termux）：

```bash
am start -a android.intent.action.VIEW -d "kugou://start.weixin?%7B%22cmd%22%3A212%2C%22jsonStr%22%3A%7B%22hash%22%3A%22a4713521e4754b8ed3f09af1e41756e5%22%2C%22filename%22%3A%22%E5%82%85%E6%A2%A6%E5%BD%A2%22%2C%22extname%22%3A%22mp3%22%7D%7D" com.kugou.android
```

预期：酷狗打开；理想：自动播放《潮汐》。把实际表现反馈给用户并记录。
