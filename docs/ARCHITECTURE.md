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
│ data/       结构化数据(JSON) + pydantic schema + loader            │
│ tools/      抓取 / 解析 / 校验 pipeline，把 wiki 文本变成 data/     │
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

## 3. 效果 DSL（核心决定）

卡牌、P道具、P饮料、剧本事件的效果统一用**结构化 JSON**表达，不用自然语言，不用 Python 代码：

```json
{
  "id": "sc_0001",
  "name": "アピールの基本",
  "plan": "free",            // free | sense | logic | anomaly
  "type": "active",          // active | mental
  "rarity": "N",
  "cost": {"kind": "genki", "value": 4},   // genki | stamina_direct | none
  "flags": ["once_per_stage"],             // once_per_stage, no_duplicate, hold, generated...
  "conditions": [ {"stat": "focus", "op": ">=", "value": 3} ],
  "effects": [
    {"op": "score", "value": 9},
    {"op": "buff", "stat": "focus", "value": 2},
    {"op": "buff", "stat": "good_condition", "turns": 3},
    {"op": "delayed", "after_turns": 2, "effects": [ {"op": "score", "value": 5} ]}
  ],
  "upgrade": { ...同结构，仅覆盖差异... }
}
```

- `op` 词表由 `docs/rules/lesson_exam_engine.md` 调研后固定；解释器在 `engine/effects.py`，每个 op 一个 handler，缺失 op 直接抛错（不静默）。
- P道具/饮料多一层 `trigger`（`turn_start` / `after_card_played` / `stage_start` / `when_stat_changes`...）+ `limit`（发动次数）。
- 数据文件保留 `source_text`（原始日文效果文本）和 `source_url`，便于校验 DSL 翻译是否正确。

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
| M1 | 数据导入：卡牌/P道具/饮料/偶像 全量 JSON + 校验 | data/*.json, tools/ |
| M2 | 卡牌引擎跑通 センス/ロジック；对拍开源引擎 | engine/, tests |
| M3 | アノマリー + 全部状态效果 | engine/ |
| M4 | 培育外循环：初(Hajime) 基线 | produce/, scenarios/hajime.yaml |
| M5 | H.I.F 剧本 | scenarios/hif.yaml, plugins/hif.py |
| M6 | Gym env + 启发式 agent + 自动打牌脚本 | env/, agents/ |
| M7 | RL 训练（PPO 等） | 训练脚本 |
