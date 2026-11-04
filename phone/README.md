# kgJP 手机端（线上版）

## 访问链接

```
https://kgjp-music.app.workbuddy.host/?sharecode=ZKYOSRB7JM
```

⚠️ **`?sharecode=` 不能丢**。网关靠它校验访问权限，只打开域名会返回 403「链接不完整」。

手机浏览器直接打开即可，无需安装任何东西。建议加到主屏幕当 PWA 用。

---

## 为什么不走局域网

最初设想在本机起 HTTP 服务让手机访问同一 Wi-Fi。实测不可行，两个硬限制：

**1. 进程无法常驻。**
沙箱会回收 bash 调用结束后启动的子进程。`nohup`、`setsid`、`disown` 全部无效 ——
单次调用内服务完全正常（`/health` 返回 200），下一次调用时进程已消失，端口不再监听。

**2. 代理拦截 localhost 请求。**
环境里有 `HTTP_PROXY=http://127.0.0.1:46355`，curl 默认把 `127.0.0.1` 的请求也发给代理，
返回 `upstream connect failed`。必须加 `--noproxy '*'` 才能直连。

结论：**只能部署到公网**。这反而是更好的形态 —— 手机不用和电脑同网，在外面也能用。

---

## 架构

```
phone/
├── app.py              # HTTP 服务，监听 $PORT（云端注入）
├── library.py          # 曲库（与 MCP 工具共用）
├── kugou.py            # 深链构造 + 选曲（与 MCP 工具共用）
└── static/index.html   # 手机页面
```

`library.py` 和 `kugou.py` 是从 `tool/` 复制来的**同一份逻辑**，
保证网页推荐和 Agent 推荐结果一致 —— 不会出现"网页说这首、Agent 说那首"的分裂。

修改时要**两边同步**：`tool/library.py` ↔ `phone/library.py`。

---

## 接口

| 路径 | 说明 |
|---|---|
| `GET /` | 手机页面 |
| `GET /api/scenes` | 场景列表 |
| `GET /api/recommend?scene=&brief=&platform=` | 推荐一首 + 深链 |
| `GET /api/share?url=` | 解析酷狗分享链 |
| `GET /api/stats` | 曲库统计 |
| `GET /health` | 健康检查 |

---

## 部署踩到的两个坑

**坑 1：必须读 `PORT` 环境变量。**
云端注入 `PORT`，如果服务写死端口（原先写死 8801），部署后无法访问。
`app.py` 已改为 `default=int(os.environ.get("PORT", 8801))`，本地和云端都能跑。

**坑 2：前端 fetch 必须透传 sharecode。**
这是**上线后才发现的实际故障**：页面用 `fetch("/api/scenes")` 相对路径，
不带 `?sharecode=`，被网关 403 拦掉。表现是**页面能打开，但一条数据都加载不出来**。

修法：注入 `api()` 包装函数，所有请求自动附加分享码。

```js
const SC = new URLSearchParams(location.search).get("sharecode");
function api(path){
  const sep = path.includes("?") ? "&" : "?";
  return SC ? path + sep + "sharecode=" + encodeURIComponent(SC) : path;
}
```

现在 5 处 fetch 全部走 `api()`，已验证线上 200。

---

## 本地调试

```bash
cd phone
python3 app.py --port 8801
# 浏览器开 http://127.0.0.1:8801
```

注意本地调试时 curl 要加 `--noproxy '*'`，否则会被代理拦。

---

## 已知限制

1. **唤起协议仍未真机验证**。`kugou://start.weixin` 来自第三方实操案例，
   可能只打开 App 不播放。页面上每张卡片都标了"尚未真机验证"。
2. **曲库 9 首**，只覆盖 5 个场景的低配版本。没歌时会如实说"没有"。
3. **去重状态在进程内**。云端实例重启即清空。
4. **网页兜底多数落搜索页**。因为 `mixsong_id` 与 `album_audio_id` 编码不通用，
   只有《潮汐》有单曲页 id。
