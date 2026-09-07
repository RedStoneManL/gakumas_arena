# 文档索引

新接手请按顺序读前三份。

## 入门 / 交接

| 文档 | 内容 |
|---|---|
| [HANDOFF.md](HANDOFF.md) | **交接说明**：项目是什么、能用什么、不能用什么、怎么验证、协作约定 |
| [PLAN.md](PLAN.md) | 路线图、里程碑状态、下一步建议顺序、设计约束 |
| [OPEN_ITEMS.md](OPEN_ITEMS.md) | 待验证 / 待办清单（推断值、引擎缺口、实测发现） |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 设计文档：分层、数据与效果表示、剧本配置、RL 接口、版本化原则 |
| [../README.md](../README.md) | 仓库入口：许可、布局、快速开始、数据更新流程 |

## 规则规格（实现依据）

| 文档 | 内容 |
|---|---|
| [rules/lesson_exam_engine.md](rules/lesson_exam_engine.md) | 课程/考试卡牌引擎：回合结构、取整、分数公式、センス/ロジック/アノマリー、状态效果目录、相位时序 |
| [rules/produce_loop.md](rules/produce_loop.md) | 培育外循环（初 / N.I.A. 基线）：周程、行动、属性成长、最终评价公式 |
| [rules/hif_exam_effects.md](rules/hif_exam_effects.md) | H.I.F 新增考试效果类型的语义推导与证据 |
| [rules/glossary.md](rules/glossary.md) | 术语表：日文 / 中文 / 英文 / master 枚举名 / 代码标识符 |
| [scenarios/hif.md](scenarios/hif.md) | **H.I.F 剧本规格**：周程、行动数值、スター性、両ラウンド本戦、评价换算 |

## 数据与调研

| 文档 | 内容 |
|---|---|
| [research/master_data_atlas.md](research/master_data_atlas.md) | master data 图谱：127 张表逐字段注释、外键、样例行 |
| [research/master_data_enums.md](research/master_data_enums.md) | 枚举字典：214 个枚举全量，169 个考试效果类型逐条语义 |
| [research/engine_coverage.md](research/engine_coverage.md) | **覆盖率报告**（自动生成）：dump 里的枚举值哪些引擎已处理 |
| [research/mechanics_timeline.md](research/mechanics_timeline.md) | 数据时效性 + 机制/结算变更时间线 + 引擎扩展点清单 |
| [research/existing_engines.md](research/existing_engines.md) | 开源引擎/RL 仓库评估与选型依据 |
| [research/data_sources.md](research/data_sources.md) | 数据源清单：翻译数据、校验用计算器、抓取可行性 |
| [research/user_report_01_simulator_landscape.md](research/user_report_01_simulator_landscape.md) | 项目发起时的调研报告（生态现状） |
| [research/user_report_02_data_and_formulas.md](research/user_report_02_data_and_formulas.md) | 项目发起时的调研报告（数据源与公式） |

## 使用与测量

| 文档 | 内容 |
|---|---|
| [evaluation.md](evaluation.md) | 评估脚本用法、列含义、初剧本 random/heuristic/search 实测数字 |
| [loadouts.md](loadouts.md) | 编成预设内容与实测（⚠️ 通过率数字在分数爆炸修复前测得，已失效） |
