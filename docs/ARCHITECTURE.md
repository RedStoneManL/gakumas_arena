# gakumas_arena 架构设计

> 目标：一个本地、可配置剧本、可复现（seeded RNG）、可给 RL 直接用的 学園アイドルマスター(学マス) 培育沙盒。
> 第一优先剧本：H.I.F編（Hatsuboshi IDOL FESTIVAL，2026-05 上线）。次优先：初(Hajime)、N.I.A.（作为基线和验证对照）。

## 1. 分层

```
┌──────────────────────────────────────────────────────────────┐
│ agents/     启发式 / MCTS / RL policy（PyTorch 等，后期）        │
├──────────────────────────────────────────────────────────────┤
│ env/        Gymnasium 封装：StageEnv(内层打牌) ProduceEnv(外层培育) │
├──────────────────────────────────────────────────────────────┤
│ produce/    培育外循环：周程、行动(课程/休息/外出/商店…)、考试调度     │
│             剧本由 scenarios/*.yaml 驱动，不写死在代码里            │
├──────────────────────────────────────────────────────────────┤
│ engine/     课程/考试卡牌引擎：回合、手牌、效果 DSL 解释器、状态效果    │
├──────────────────────────────────────────────────────────────┤
│ masterdata/ 解包 master data(YAML→JSON缓存) 访问层；data/ 类型化视图 │
│ tools/      拉取/转换 master data、校验、名称翻译映射               │
└──────────────────────────────────────────────────────────────┘
```

依赖方向只能向下。`engine` 不知道剧本；`produce` 通过 `ScenarioConfig` 知道剧本；`env` 只做观测/动作编码。

## 2. 目录

```
gakumas_arena/
  data/        schema.py（pydantic 模型）, loader.py, registry.py
  engine/      state.py, cards.py, effects.py(DSL), stage.py(一局课程/考试), rng.py, status.py
  produce/     scenario.py(配置加载), run.py(一次完整培育), actions.py, idol.py, shop.py, evaluate.py(评级)
  scenarios/   hajime.yaml, nia.yaml, hif.yaml
  env/         stage_env.py, produce_env.py, spaces.py(观测/动作编码)
  agents/      random_agent.py, greedy.py, mcts.py
data/          skill_cards.json, p_items.json, p_drinks.json, idols.json, support_cards.json, status_effects.json
tools/         scrapers/, parsers/, validate.py
tests/
docs/          rules/ scenarios/ research/
```

## 3. 数据与效果表示（核心决定，2026-09-07 修订）

**唯一真源 = 解包 master data**（`vertesan/gakumasu-diff`，YAML，每表一文件，随游戏版本自动更新）。
不再解析 wiki 文本；wiki/攻略站只用于**校验数值和补充语义**。

- dump 不入库（版权原因）：`tools/masterdata/fetch.sh` 拉到 `data/raw/gakumasu-diff`（gitignore），
  `tools/masterdata/build_cache.py` 一次性转 JSON 缓存（YAML 解析太慢）。
- 访问层：`gakumas_arena/masterdata/store.py` 的 `MasterData.table()/by_id()/where()/enum_values()`；
  其余代码只经过它读数据。
- 关键联表：`ProduceCard.playEffects[].produceExamEffectId → ProduceExamEffect`，
  `ProduceExamEffect.effectType`（`ProduceExamEffectType_*` 枚举，~100 个）+ `effectValue1/2/effectCount/effectTurn`
  + `chainProduceExamEffectIds` + `produceExamStatusEnchantId`（状态附魔）+ `produceExamTriggerId`（触发条件）。
  `ProduceItem/ProduceDrink` 同样引用效果与触发表；`Produce/ProduceStep*/ProduceStepAuditionDifficulty/ResultGradePattern`
  描述培育外循环和评级；`ProduceExamAutoEvaluation*` 是官方自动出牌 AI 的权重表（可直接做 baseline 策略）。
- **效果解释器 = 按 `ProduceExamEffectType` 分发**（`engine/effects.py`），每个枚举值一个 handler，未实现的枚举值
  直接抛错。这样新卡随 dump 更新自动可用，不需要手写卡牌定义。
- 之前设计的自研 JSON DSL 降级为「测试/自定义卡」用途，保留但不作为主路径。
- 校验：`ProduceDescription*` 表把枚举映射到日文说明文案，是效果语义的官方文档；再叠加 seesaawiki 的取整/时序表。

## 4. 剧本配置（scenarios/*.yaml）

```yaml
id: hif
weeks: 
  - {week: 1, kind: free, actions: [lesson, sp_lesson, rest, outing, consult]}
  - {week: 6, kind: exam, exam: midterm}
  ...
lesson:
  base_gain: ...
  sp_multiplier: ...
exam:
  midterm: {turns: 6, target: ..., stat_order: by_stat_desc}
special:    # 剧本特有系统（HIF：フェス回合、一番星 等）走 plugin
  module: gakumas_arena.produce.plugins.hif
evaluate:
  rank_table: [...]
```

通用部分靠配置；确实无法配置化的剧本特有逻辑放 `produce/plugins/<scenario>.py`，通过固定的 hook 接口接入（`on_week_start`, `on_action`, `on_exam_end` …）。

## 5. RL 接口

- **StageEnv**（内层）：一局课程/考试。obs = 手牌编码 + 状态向量 + 牌堆统计；action = 出第 i 张牌 / 用饮料 j / 跳过；动作掩码 `info["action_mask"]`。reward = 分数增量（或终局 clear/perfect）。
- **ProduceEnv**（外层）：一次完整培育。obs = 周数、三维属性、体力、牌组摘要、道具、剧本状态；action = 周行动 + 选卡/选饮料等子决策。内层可以：a) 交给启发式/已训练的 StageEnv policy；b) 展开成分层动作。
- 全部随机性来自 `engine/rng.py` 的单个 `numpy.random.Generator`，由 seed 控制，保证可复现；支持 `clone_state()` 给 MCTS 用。

## 6. 校验策略

1. 单元测试：每个 op、每个状态效果的公式（对照 wiki 数值）。
2. 与开源引擎对拍：把 gakumas-core / gakumas-engine 的同一牌组、同一 seed 场景跑出来的分数序列做 fixture。
3. 真机录像/攻略站的"回合记录"作为端到端用例。

## 7. 里程碑

| # | 内容 | 产出 |
|---|------|------|
| M0 | 调研 + 骨架（本轮） | docs/、包结构、DSL schema |
| M1 | master data 加载层 + 枚举图谱 + 类型化视图 | masterdata/, docs/research/master_data_*.md |
| M2 | 卡牌引擎跑通 センス/ロジック；对拍开源引擎 | engine/, tests |
| M3 | アノマリー + 全部状态效果 | engine/ |
| M4 | 培育外循环：初(Hajime) 基线 | produce/, scenarios/hajime.yaml |
| M5 | H.I.F 剧本 | scenarios/hif.yaml, plugins/hif.py |
| M6 | Gym env + 启发式 agent + 自动打牌脚本 | env/, agents/ |
| M7 | RL 训练（PPO 等） | 训练脚本 |

## 8. 数据时效性与新机制兼容（设计原则）

- **数据版本可追溯**：`MasterData` 记录 dump 的 commit/日期（`masterdata_json/_meta.json`）；每次模拟结果带上数据版本。
  `tools/masterdata/fetch.sh` 一条命令更新；`tools/masterdata/history_diff.py` 比较两个 commit 之间新增的表/枚举值/配置改动。
- **未知即报错**：效果类型、触发类型、状态附魔、步骤类型全部走注册表，遇到未注册的枚举值抛 `UnsupportedMechanic`，
  并有一个 `tools/masterdata/coverage.py` 报告「dump 里出现过但引擎未实现」的枚举值清单。新版本上线后先跑覆盖率报告。
- **结算公式版本化**：评价/评级/分数换算不硬编码，放在 `rules/scoring/*.yaml`，带 `effective_from` 日期与来源
  （master 表优先：`ResultGradePattern`、`ProduceExamBattleScoreConfig`、`ProduceStepAuditionDifficulty`；wiki 公式次之）。
- **剧本以 `Produce.id` 为键**：新剧本 = 新配置 + 可选 plugin，不改引擎核心。
- **回归对拍**：固定 seed + 固定牌组的黄金分数序列作为 fixture；升级 dump 后跑一遍，差异即为版本变更信号。
