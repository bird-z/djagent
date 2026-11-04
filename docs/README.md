# docs/ 文档索引

产品需求与状态以 [PRD.md](PRD.md) 为准。

## 推荐阅读顺序（按决策链，不是按文件名）

第一次接触这个项目，按这四步读，半小时能掌握全貌：

| 顺序 | 文档 | 读完你应该知道 |
|---|---|---|
| 1 | [PRD.md](PRD.md) | 产品做什么、不做什么、现在到哪一步、下一关的出口条件 |
| 2 | [research.md](research.md) | 为什么是这个定位：5 个竞品的空白、手机厂商智能体的边界、8 条现实差距 |
| 3 | [ambience-system.md](ambience-system.md) + [ambience-glossary.md](ambience-glossary.md) | 判断层怎么建：8 轴词表、场合卡、12 条规则、内部认同怎么度量 |
| 4 | [knowledge-base.md](knowledge-base.md) | 数据从哪来、怎么长、怎么审、agent 怎么查怎么答怎么播 |
| 5 | [scene-lifecycle.md](scene-lifecycle.md) → [product-form.md](product-form.md) | 三段体验怎么落、以什么形态落地、钱从哪来 |

**只关心技术实现**：直接看 [kugou-ids.md](kugou-ids.md)、[no-browser-launch.md](no-browser-launch.md)、
[mobile-agent-dev-plan.md](mobile-agent-dev-plan.md)。

## 需求与方案

| 文档 | 内容 | 什么时候看 |
|---|---|---|
| [PRD.md](PRD.md) | 产品需求文档 v2.0：定位、三层矩阵、生命周期三段、判断层 J1-J5、C 端 C1-C8、B 端 B1-B5、指标树、里程碑、12 项不做、风险表 | **最先读**，一切需求的真源 |
| [research.md](research.md) | DJ Agent 产品研究：5 个竞品对比、手机端智能体能力边界、差距分析、待验证项 | 定方向、做取舍时 |
| [ambience-system.md](ambience-system.md) | **氛围体系**：8 轴受控词表、场合卡字段与示例、12 条映射规则、数据契约、内部认同机制与一致性门槛 | 做判断层、评审推荐质量时 |
| [ambience-glossary.md](ambience-glossary.md) | 氛围体系术语卡（一页版）：8 轴判定问题、5 条硬规则、标注自检、一致性门槛 | 标注/评审前必读，可贴墙 |
| [knowledge-base.md](knowledge-base.md) | **知识库架构**：三层仓（公共/团队/个人）、五类知识对象、冷启动规模、贡献审核流水线、agent 四工具检索与证据链回答、数据质量与演化 | 做数据、做检索、做审核时 |
| [scene-lifecycle.md](scene-lifecycle.md) | **场景 × 生命周期**：分场景 / 场前编排 / 临场使用三段的目标、界面、数据、指标与硬约束 | 设计功能、拆分版本时 |
| [product-form.md](product-form.md) | **落地形态**：六种形态评分（H5/小程序/App/桌面台/Skill/硬件）、四阶段路径、三层矩阵、变现假设 | 定版本节奏、谈资源与商业化时 |
| [mobile-agent-dev-plan.md](mobile-agent-dev-plan.md) | 基于 Mobile Agent 二次开发方案：三姿态、KugouProvider 四工具、M-B1~B4 | 做 M-B2 原生开发时 |

## 调研与决策依据（历史链，不删除）

| 文档 | 内容 |
|---|---|
| [brainstorm.md](brainstorm.md) | 头脑风暴稿：产品形态分叉、选曲策略 S1-S4、跳转链路 J1-J6、十个坑 |
| [kugou-ids.md](kugou-ids.md) | 酷狗标识符与深链测绘：hash/mixsong_id/album_audio_id 实测结论 |
| [android-launch.md](android-launch.md) | 安卓唤起三层方案（官方 SDK / scheme / intent）与取舍 |
| [no-browser-launch.md](no-browser-launch.md) | 无浏览器唤起三路径 + **真机验证结论（2026-11-03 通过）** |
| [android-agent-projects.md](android-agent-projects.md) | 安卓 Agent 宿主项目盘点（ZorvAI / Operit / PokeClaw / Mobile Agent…）与推荐排序 |

## 操作手册

| 文档 | 内容 |
|---|---|
| [mobile-agent-deploy.md](mobile-agent-deploy.md) | Mobile Agent v0.2.0 装机指南：APK/sha256/模型配置/skill 安装/验证步骤 |

## 案例

| 文档 | 内容 |
|---|---|
| [case-meetup-pep.md](case-meetup-pep.md) | 场景案例 01：小型分享会·打气段——从真实需求走完整链路（解析→建卡→筛选→校验→深链→现场脚本），并暴露 6 个体系缺口 |

## 维护约定

- 真机验证结论一律回填 `no-browser-launch.md`；PRD 附录 A 只留结论不贴过程。
- 新文档加入后在本表登记一行，并放进"推荐阅读顺序"对应的位置。
- 历史调研文档（brainstorm/kugou-ids/android-launch 等）不删除——它们是决策依据链，被证伪时在原位加注。
- 版本化约定：PRD 改动在 §12 记变更；氛围体系改动升 `ruleset-vX.Y` 并回写卡片 `status`。
