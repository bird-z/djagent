# kgJP Agent Tool（MCP 版本）

让 Agent 在对话里调用工具，按场景推荐歌并返回酷狗深链。

---

## 已接入

`~/.workbuddy/mcp.json` 已写入：

```json
{
  "mcpServers": {
    "kgjp": {
      "command": "/home/bird/.workbuddy/binaries/python/versions/3.13.12/bin/python3",
      "args": ["/home/bird/work/kgJP/tool/server.py"]
    }
  }
}
```

**需要你手动做一步**：打开连接器管理页，右上角「自定义连接器」，找到 `kgjp`，点「信任」。
MCP 不会自动激活。

---

## 为什么手写而不是用官方 SDK

官方 `mcp` 包依赖 `cryptography`（4.8 MB）。本机网络反复失败：

```
× Download failed after 21 attempts because not enough bytes were received (2.9 MB/4.8 MB)
```

MCP 本质是 JSON-RPC 2.0 over stdio，手写 200 行足够，顺带得到三个好处：零依赖、启动快、不受 pip 网络影响。

---

## 四个工具

| 工具 | 用途 | 参数 |
|---|---|---|
| `recommend_music` | 按场景推荐一首 + 生成深链 | `scene`（必填）、`brief`、`platform` |
| `resolve_share` | 解析酷狗分享链，提取全部 ID | `share_url`（必填）、`platform` |
| `list_scenes` | 列出场景及其选曲约束 | — |
| `library_stats` | 查看曲库规模与验证状态 | — |

### 场景枚举

`focus` 写代码 / `tired` 深夜疲惫 / `restless` 心烦 / `nostalgia` 怀旧 / `bgm` 找 BGM

### recommend_music 返回样例

```json
{
  "found": true,
  "title": "夜的钢琴曲5",
  "artist": "石进",
  "duration_text": "2:13",
  "reason": "你说「改了三版还没过，眼睛发酸」，这首没有会突然炸出来的副歌，适合当写到一半时的垫底",
  "links": {
    "web": "https://www.kugou.com/yy/html/search.html#searchKeyWord=...",
    "android_scheme": "kugou://start.weixin?%7B%22cmd%22%3A212...",
    "android_intent": "intent://play?hash=...#Intent;scheme=kugou;package=com.kugou.android;..."
  },
  "verified_on_device": false,
  "how_to_present": "把 reason 原样说出来（它引用了用户原话，不要改写）..."
}
```

---

## 设计决定（都有理由）

**1. 理由必须引用用户原话。**
`reason` 会把 `brief` 嵌进去。工具返回的 `how_to_present` 明确要求 Agent 不要改写 —— 因为"这首很适合你"是推送，"你说改了三版还没过，这首没有会炸出来的副歌"才是推荐。

**2. 硬约束优先于打分。**
BGM 场景 `require_instrument: true`，有人声的歌直接出局，不参与排序。原因是第一版这里出过错：给"找 BGM"推了《潮汐》，理由写"这首是纯器乐"，**而它明明有人声**。理由和事实不符比推错歌更伤。

**3. 连续推荐去重。**
进程内记最近 5 首，重复的扣 25 分。实测不加之前，四个不同场景有三次推同一首。

**4. 版本过滤只拦明确的变体。**
拦 `DJ` / `Live` / `翻唱` / `remix` / `(钢琴版)` 等。
**不拦**「钢琴曲」「改编」—— 它们可能是独立作品（《夜的钢琴曲5》是原创钢琴曲，不是《晴天》的钢琴版）。第一版拦了，导致合法曲目被误杀。

**5. 曲库太小就如实说没有。**
`found: false` 时返回具体原因（如"有人声，不能当 BGM"），并提示 Agent"严禁编造歌名或 hash"。宁可说没有，也不凑。

**6. verified 与 exists 分开。**
当前 9 首全部 `exists: true`（已用搜索接口回查 hash 确认存在），但 `verified: false`（没在真机上验证过唤起）。两者混为一谈会让决策建立在错误假设上。

---

## 曲库（9 首，全部 hash 已验证存在）

| 曲目 | 人声 | 纯器乐 | 能量 | 适合 |
|---|---|---|---|---|
| 夜的钢琴曲5 / 石进 | 1 | ✅ | 1 | 专注、心烦、BGM |
| River Flows In You / Yiruma | 1 | ✅ | 2 | 专注、BGM |
| 卡农 / 纯音乐 | 1 | ✅ | 2 | 专注、怀旧 |
| 潮汐 / 傅梦彤 | 2 | — | 3 | 专注、疲惫 |
| 晴天 / 周杰伦 | 4 | — | 3 | 怀旧 |
| 平凡之路 / 朴树 | 4 | — | 4 | 怀旧 |
| 南山南 / 马頔 | 4 | — | 2 | 深夜、怀旧 |
| 安和桥 / 宋冬野 | 4 | — | 2 | 深夜、怀旧 |
| 成都 / 赵雷 | 4 | — | 3 | 怀旧 |

---

## 已知限制

1. **唤起协议仍未真机验证**。`kugou://start.weixin` 来自第三方实操文章，非官方文档。可能只开 App 不播放。
2. **`mixsong` 大多为空**。只有《潮汐》有（`4ltgkqde`）。原因是 mixsong_id 不在静态 HTML 里，
   搜索接口给的是 `album_audio_id`（数字型），两者编码体系不同，无法换算。所以多数歌的网页兜底会落到搜索页。
3. **去重状态不落盘**。server 重启即清空。
4. **无联网选歌**。曲库是静态的 9 首，不调用大模型，也不实时搜歌。

---

## 本地自测

```bash
cd /home/bird/work/kgJP/tool
printf '%s\n' \
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
'{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"recommend_music","arguments":{"scene":"focus","brief":"改了三版还没过"}}}' \
| /home/bird/.workbuddy/binaries/python/versions/3.13.12/bin/python3 server.py
```

---

## 文件

| 文件 | 作用 |
|---|---|
| `server.py` | MCP server，JSON-RPC 分发 |
| `library.py` | 曲库 + 场景定义 |
| `kugou.py` | 深链构造 + 选曲算法 + 分享链解析 |
| `fetch_songs.py` | 从搜索接口批量取曲目并回查验证 |
