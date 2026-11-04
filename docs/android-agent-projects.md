# 安卓上能跑 Agent + 工具调用的项目盘点（kgJP 视角）

目的：找到能在小米 10S 上直接"对话 → 工具调用 → 打开酷狗播放"的现成宿主，
评估哪条路最短。日期：2026-11-03。

## 三条技术路线

1. **终端路线**：Termux 里跑 CLI agent（Open Interpreter / 自写脚本），工具 = shell 命令，
   打开酷狗 = `am start` 深链。零权限门槛，但入口是终端。
2. **原生 Agent App 路线**：装一个开源 Agent APK，工具调用/无障碍/MCP 是一等公民，
   打开酷狗 = open_app 工具或深链工具。体验最像"手机 agent"，需要装第三方 App + 授权。
3. **自建 App 路线**：用 ADK(Kotlin)/Koog/LiteRT-LM 自己写一个小 agent App。
   完全可控，但工程量最大，不适合 MVP 验证阶段。

## 第一梯队：真 Agent、能动手（原生 App）

| 项目 | 亮点 | 与 kgJP 的契合 | 代价/风险 |
|---|---|---|---|
| **ZorvAI** (github.com/Quor-a/ZorvAI, Apache-2.0) | ACI 框架基于 AIDL Binder，任意 App 能力变工具；120+ 内置工具；无障碍/Shizuku/Root 三通道；支持 MCP；可接端侧 MNN/llama.cpp 离线模型；Android 26+ | 最契合：MCP 支持意味着可直接接我们已有的 kgjp MCP server；也可用其 open_app/shell 类工具跑 `am start` 深链 | 功能重、权限要求高、上手成本大 |
| **Operit AI** (github.com/AAswordman/Operit, 5600+ star) | 内置 Ubuntu 24.04（可 apt 装软件）；40+ 工具 + MCP 插件生态；无障碍免 Root 三档权限 | 内置 Ubuntu ≈ 手机里又一个 Termux，MCP 生态可直接挂 kgjp server | APK 约 380MB，偏重 |
| **PokeClaw** (github.com/agents-io/PokeClaw) | 本地优先：端侧 Gemma + LiteRT-LM 推理，无需 API Key；原生工具 tap/swipe/type/**open_app**/screenshot；观察→决策→执行循环 | open_app 工具天然覆盖"打开酷狗"；全离线，隐私好 | 端侧小模型对复杂意图（场景选曲）能力有限 |
| **X-OmniClaw** (OPPO 开源, Apache-2.0) | 多模态：能看/听/记/跨 App 操作；Android 8.0+ 直接装 APK | 看屏幕能力对"验证酷狗是否真的在播放"有用（截图自证） | 偏研究性质 |
| **AndroidForClaw** (github.com/xiaomochn/AndroidForClaw) | 标准 Function Calling，兼容 OpenClaw；Shell/文件/浏览器/屏幕感知工具 | shell 工具可跑 am start；支持飞书/Discord 渠道接入 | 社区项目，稳定性未知 |
| **Mobile Agent** (github.com/looper42/mobile_agent, Apache-2.0) | OpenAI 兼容接口；文件/网页/设备能力；Root/无障碍控制 + 悬浮窗；**已支持 skills**；中文文档全 | skills 支持意味着我们刚写的 kugou-launch SKILL.md 可能直接可用；悬浮窗可在后台任务时观察执行 | 早期项目，API 可能变 |

## 第二梯队：终端路线（Termux 系）

| 方案 | 说明 | 契合度 |
|---|---|---|
| **Open Interpreter on Termux** | `pip install open-interpreter`，配 OpenAI 兼容 key 即可；工具=代码执行；需 `allow-external-apps` 才能调外部 App | 可用但绕：agent 生成 python → subprocess 调 am start。上一轮我们写的 termux/kgjp.py 其实就是它的轻量替代——零依赖、不依赖外部 LLM 编排 |
| **Termux + Termux:API + 自写脚本**（现状） | 我们已有 termux/kgjp.py，三通道唤起 + 场景选曲 | 已落地；缺点是没有对话式 agent 外壳，要靠手机版 agent 来调 skill |

## 第三梯队：自建框架（了解即可，暂不投入）

- **Google ADK for Android**：Kotlin，工具= `@Tool` 注解函数，可切 Gemini Nano 端侧离线推理；早期阶段。
- **JetBrains Koog**：Kotlin/Java，模型无关，1.0 稳定 + API 稳定保证，LiteRT 跑本地模型。
- **LiteRT-LM**（2026-04 开源）：端侧推理底座，内置 function calling 支持，是上面各家"本地模型"的公共依赖。

自建的意义：如果 kgJP 未来要做成产品（ad 端投放 → 用户手机直达酷狗），内嵌 agent 比依赖第三方宿主更可控。但验证期不值得。

## 推荐排序（kgJP 当前阶段）

1. **Mobile Agent** —— 先试装。它有 skills 支持 + 无障碍控制，风险最低的"对话式打开酷狗"体验；把我们生成的 kugou-launch skill 喂给它即可验证。
2. **ZorvAI / Operit** —— 若需要 MCP 一等公民接入（把 tool/server.py 直接挂上去），这两个最对口；ZorvAI 需 Android 26+（MI 10S 是 Android 12/13，**注意版本门槛**），Operit 380MB 偏重。
3. **维持 Termux 现状** —— termux/kgjp.py + skill 文件已可用，任何能跑 shell 的 agent 宿主都能接。
4. **PokeClaw / X-OmniClaw** —— 全离线派，适合"无网络也能唤起"的极端场景，选曲智能受限。

## 一个关键校验点

MI 10S = 骁龙 865，Android 12/13（MIUI 14 可升）。筛项目时先卡 Android 版本：
ZorvAI 要 26+（Android 8.0+，OK）；X-OmniClaw 要 8.0+（OK）；端侧模型（Gemma/LiteRT）跑在 865 上可用但慢。

## 下一步

1. 在手机上装 Mobile Agent，把 `skills/kugou-launch/SKILL.md` 放进它的 skills 目录，实测"打开酷狗播放潮汐"。
2. 若 Mobile Agent 的 skill 机制不兼容 SKILL.md 格式，改试 ZorvAI 的 MCP 通道接 `tool/server.py`。
3. 任何一条路跑通后，回填 `docs/no-browser-launch.md` 的真机验证结论。

## 来源

- 掘金《安卓端"开源 + AI + 能调用工具"的软件》(juejin.cn/post/7672391884245450790)
- ProAndroidDev《Android's Agent-First Era》(proandroiddev.com)
- 各项目 GitHub README（ZorvAI / Operit / PokeClaw / X-OmniClaw / AndroidForClaw / mobile_agent）
- open-interpreter-termux (github.com/MikeBirdTech/open-interpreter-termux)
