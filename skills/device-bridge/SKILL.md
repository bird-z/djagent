---
name: device-bridge
title: 操控用户安卓手机（零配置设备桥）
description: 通过 kgJP 设备桥远程操控用户自己的安卓手机：播放酷狗歌曲、按场景放歌、发系统通知、写剪贴板。当用户说"在我手机上放首歌"、"提醒我手机上的xxx"、"把我手机剪贴板换成xxx"时使用。适用任何云端 agent 平台，只需能发 HTTP POST。
version: 0.1.0
---

# 设备桥：远程操控用户的安卓手机

## 原理（一句话）

任务提交到云端队列（本 skill 只做 HTTP 调用），用户手机上的 Termux 轮询器 15 秒内领取并在**本地**执行（深链唤起酷狗等）。手机端不暴露任何端口，所有执行留痕可查。

## 接入信息

| 项 | 值 |
|---|---|
| BASE | `https://kgjp-music.app.workbuddy.host` |
| 提交任务 | `POST {BASE}/device/task` |
| 查询执行状态 | `GET {BASE}/device/status?token=<令牌>` |
| 鉴权 | Header `X-KGJP-Token: <令牌>`（或 body 里 `"token": "<令牌>"`） |
| 令牌来源 | 用户手机安装桥接器时生成，问用户要；每个设备一个，泄露可重装吊销 |

## 提交任务

```http
POST {BASE}/device/task
Content-Type: application/json

{"action": "<动作>", "params": {...}, "token": "<令牌>"}
```

成功返回 `{"ok": true, "task_id": "t-xxxx", "queued": true}`。

### 动作白名单（只有这四种，其他一律返回 400）

**1. play_song — 在手机上播放指定歌曲**

```json
{"action": "play_song",
 "params": {"hash": "a4713521e4754b8ed3f09af1e41756e5",
            "title": "潮汐", "artist": "傅梦彤"}}
```

`hash` 必需、32 位十六进制。不知道 hash 时用下面的搜索接口查。

**2. recommend_scene — 按场景选一首并在手机上播放**

```json
{"action": "recommend_scene", "params": {"scene": "focus"}}
```

场景取值：`focus`（专注）/ `tired`（疲惫）/ `restless`（烦躁）/ `nostalgia`（怀旧）/ `bgm`（视频配乐）。执行端会自动选曲 + 唤起酷狗播放。

**3. notify — 手机系统通知**

```json
{"action": "notify", "params": {"title": "提醒", "content": "该喝水了"}}
```

**4. clipboard_set — 写手机剪贴板**

```json
{"action": "clipboard_set", "params": {"text": "要复制的文本"}}
```

## 搜歌名取 hash（没有 hash 时先做这步）

```
GET http://mobilecdn.kugou.com/api/v3/search/song?format=json&keyword=<URL编码歌名>&page=1&pagesize=5
```

取 `data.info[0].hash`，核对歌名歌手后再提交任务。

## 查询执行结果

```http
GET {BASE}/device/status?token=<令牌>
```

返回 pending 队列长度和设备最后在线时间。任务领取后 15-30 秒内执行完毕；`task` 已 claimed 但迟迟无结果说明手机离线（Termux 被杀或没网），如实告知用户。

## 错误处理

- `401 令牌无效` → 向用户确认令牌；令牌换过（重装）就取新的
- `400 动作不在白名单` → 检查动作名拼写，不要自创动作
- `429 队列已满` → 稍后重试，不要连续轰炸
- 提交成功 ≠ 播放成功：最终以手机端回报为准，查询 /device/status 确认

## 手机端如何接入（供用户首次配置，agent 可引导）

用户在手机 Termux 里执行一条命令（agent 可把这句话发给用户）：

```
curl -s https://kgjp-music.app.workbuddy.host/device/install.sh | sh
```

脚本自动下载执行器、注册设备、启动 15 秒轮询。若手机装有 Mobile Agent，用户可以让手机 agent 用无障碍能力代替人手完成这一步。

## 边界（必须遵守）

- 只调用上面四种动作。绝不尝试让队列执行任意命令——协议层就不支持
- 不用于支付、账号、隐私敏感操作
- 放歌是"唤起酷狗播放"，会员/登录由酷狗 App 自行处理
