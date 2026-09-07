# 待验证 / 待办清单（持续更新）

> 引擎能跑通 ≠ 数值正确。本页记录所有「代码里已做出选择但尚未用实机验证」的点，以及下一步的工作项。
> 代码中对应位置以 `TODO(HIF-verify)` / `ScoringRules` 开关标注。

## A. 数值保真（最高优先）

| # | 项目 | 现状 | 验证方式 |
|---|------|------|----------|
| A1 | 分数/参数取整（每步 ceil）、元気 floor、好調/絶好調整数化 | 审计 agent 进行中（`docs/rules/scoring_fidelity.md`） | gakumas-core 的 9 段录像用例移植为回归测试 |
| A2 | 集中倍率与好調百分比的 ceil 先后 | seesaawiki 标「検証の必要あり」 | 实机录像逐回合对拍 |
| A3 | HIF 選抜分数 → スター性 换算（14k/150k/390k 线性分段） | 推断 | 实机记录 選抜 分数与获得スター性 |
| A4 | スター性 → 考试分数加成曲线（线性到 1335 时 +25%） | 推断 | 实机记录不同スター性下同牌组分数 |
| A5 | 公開レッスン SP 概率（0.15 基础）与副属性选择 | 推断 | 实机统计 |
| A6 | 本戦 NPC 分数生成（静态/采样） | `isStaticNpcScore` 字段 + 采样模式 | 实机记录对手分数分布 |
| A7 | 2025-10-31 最终考试分数上限等代码侧结算改动 | 需版本化配置 | 对照官方公告 + 社区计算器 |

## B. 引擎能力

- B1 `EffectTaxonomy.action_types` 未加入 HIF 动作（one-hot 全零），旧 checkpoint 兼容 vs 特征表达力，需要决定。
- B2 HIF 相談（商店）未作为每周动作暴露。
- B3 `p_rd-item_set-produce_008-end_mid_audition-all` 在 dump 中无可解析的奖励池。
- B4 `RemainingTurn` 触发条件 ≥/≤ 方向（审计 agent 处理中）。
- B5 隐藏概率：SP 課程率、事件权重、shop 刷新、回合颜色分布、`ProduceCardRandomPool` 权重——全部为近似，需实测拟合。

## C. 观察到的现象

- C1 `run_produce(scenario="hif", policy="heuristic")` 使用默认偶像/空编成时在第 2 场選抜試験失败（`ending_type: failed`）。
  这说明 baseline 需要一套像样的 HIF 编成（支援卡 + メモリー）作为默认 loadout，否则 RL 早期 reward 全是失败信号。

## D. 下一步（建议顺序）

1. A1 完成后跑一遍全量测试 + `tools/masterdata/coverage.py --strict`。
2. 构造一套合理的 HIF 默认 loadout（从 `SupportCard`/`IdolCard` 里选高等级卡），让 heuristic 能稳定通过選抜。
3. 自动打牌脚本：对固定 loadout 用 heuristic / 1-ply / MCTS 做分数分布评估，输出 CSV。
4. 培育策略搜索：先做 seed 固定的贪心/束搜索，再上 MaskablePPO（`gakumas_rl.training` 已有流程）。
5. 建立实机录像 → jsonl 的采集格式（`gakumas_rl/manual_exam_setups.py`）用于 A 组验证。
