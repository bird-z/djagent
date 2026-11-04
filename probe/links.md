# 安卓唤起测试链接

**傅梦彤 - 潮汐**　时长 2:48

| 字段 | 值 |
|---|---|
| hash | `a4713521e4754b8ed3f09af1e41756e5` |
| songid (audio_id) | `84785711` |
| album_audio_id | `278511146` |
| album_id | `39769270` |
| fileName | `傅梦彤 - 潮汐` |
| pay_type / privilege | 1 / 10 |

## 按推荐顺序测试

### 1. L2 分享回流 scheme — 最有希望直接播放
[点我在酷狗中播放](kugou://start.weixin?%7B%22cmd%22%3A212%2C%22jsonStr%22%3A%7B%22hash%22%3A%22a4713521e4754b8ed3f09af1e41756e5%22%2C%22filename%22%3A%22%E5%82%85%E6%A2%A6%E5%BD%A4%20-%20%E6%BD%AE%E6%B1%90%22%2C%22extname%22%3A%22mp3%22%7D%7D)

```
kugou://start.weixin?%7B%22cmd%22%3A212%2C%22jsonStr%22%3A%7B%22hash%22%3A%22a4713521e4754b8ed3f09af1e41756e5%22%2C%22filename%22%3A%22%E5%82%85%E6%A2%A6%E5%BD%A4%20-%20%E6%BD%AE%E6%B1%90%22%2C%22extname%22%3A%22mp3%22%7D%7D
```

### 2. L3a intent + 网页兜底 — 没装 App 会跳网页
[点我（带 fallback）](intent://play?hash=a4713521e4754b8ed3f09af1e41756e5#Intent;scheme=kugou;package=com.kugou.android;S.browser_fallback_url=https%3A%2F%2Fwww.kugou.com%2Fmixsong%2F4ltgkqde.html;end)

```
intent://play?hash=a4713521e4754b8ed3f09af1e41756e5#Intent;scheme=kugou;package=com.kugou.android;S.browser_fallback_url=https%3A%2F%2Fwww.kugou.com%2Fmixsong%2F4ltgkqde.html;end
```

### 3. L3b 只打开酷狗 — 最保守，先确认能否唤起
[点我打开酷狗](intent://#Intent;scheme=kugou;package=com.kugou.android;S.browser_fallback_url=https%3A%2F%2Fwww.kugou.com%2Fmixsong%2F4ltgkqde.html;end)

### 4. L3c 猜测格式 — 大概率不生效，作对照
[点我](kugou://play?hash=a4713521e4754b8ed3f09af1e41756e5)

### 5. 纯网页兜底 — 一定可用
[点我打开网页版](https://www.kugou.com/mixsong/4ltgkqde.html)

## 测试记录

| 编号 | 唤起 App | 自动播放 | 落点正确 | 备注 |
|---|---|---|---|---|
| 1 L2 |  |  |  |  |
| 2 L3a |  |  |  |  |
| 3 L3b |  |  |  |  |
| 4 L3c |  |  |  |  |
| 5 web |  |  |  |  |
