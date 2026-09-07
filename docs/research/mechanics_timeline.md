# 学マス master data：数据时效性与机制/评分变更时间线

> 目的：审计 `data/raw/gakumasu-diff`（vertesan/gakumasu-diff 的 git clone）相对真实游戏的**新鲜度**，并从全部 git 历史中提取**机制与评分规则随时间的变化**，据此给出通用引擎必须具备的扩展点清单。
> 生成工具：`tools/masterdata/history_diff.py`（见 §B.0）。审计日期：2026-09-07。
> 相关文档：`docs/research/data_sources.md`（数据源）、`docs/research/existing_engines.md`（现有模拟器）、`docs/ARCHITECTURE.md` §8。

---

## Part A — 数据新鲜度

### A.1 dump 现状

| 项目 | 值 |
|---|---|
| 仓库 | `vertesan/gakumasu-diff`，本地 clone 已 `--unshallow`，**249 个 commit**，2024-05-18 → 2026-09-04 |
| 最新 commit | `5b8969e` 2026-09-04 11:03:33 UTC（=JST 20:03）；同日还有 `855a24f` 02:03 UTC（=JST 11:03） |
| 提交者 | 237/249 为 `vts-server`（自动化账号），其余 12 个是 2024-05～2025-04 间作者 `vertesan` 的手动提交（大版本当天补跑）；commit message 是 master DB 文件的 sha256，无人工描述 |
| `ForceAppVersion.yaml` | iOS / Android / DMM 均为 **3.3.0**（`PlatformType_Other` 仍是 1.10.1，为占位） |
| 表数量 | 286 个 YAML（初始 dump 195 → 现在 286；历史上删除过 9 个） |

### A.2 与真实游戏的对照

能核实到的官方/半官方事实（本环境的出口代理封锁了 `gakuen.idolmaster-official.jp`、`idolmaster-official.jp`、App Store、Google Play、X、seesaawiki、wikiwiki 等域名，只能通过搜索引擎摘要间接核实；下列结论已用多条独立搜索结果交叉确认）：

- **ver.3.3.0** 于 **2026-08-17 11:00 JST** 上线（内容之一：サポートイベントのスキルカードが強化済みで獲得可能、可在设置中开关）。搜索引擎摘要将其描述为「約 3 週間前」，与今天 2026-09-07 吻合。
- 搜索 `ver.3.3.1` / `ver.3.3.2` / `ver.3.4.0` 均无结果，说明截至 2026-09-07 **3.3.0 仍是最新版本**。
- 2026-08-26 16:40 JST 有一次「あさり先生のプロデュースゼミ」的紧急维护（修复メモリーアビリティ重复的 bug）；dump 同日 02:03 UTC 有 commit `10fd0cf`。
- 2026-09-04 11:00 JST 新剧情活动「さいごの文化祭」开始；dump 同日 02:03 UTC（=11:03 JST）即有 commit `855a24f`，20:03 JST 再次 commit。
- 第三方商店镜像（QooApp）曾记录 v3.2.3 更新于 2026-08-05；dump 的 `ForceAppVersion` 在 2026-08-10 变为 3.2.3、2026-08-21 变为 3.3.0，与「发布日 + 数日后强制更新」的官方惯例一致（官方 X 历史公告：ver.1.3.0 于 7/18 发布、7/22 强制更新；ver.1.4.0 于 8/28 发布、9/1 强制更新）。

**结论：dump 没有落后于线上。** 最新 commit 就是 2026-09-04 当天两次更新的 master data；`ForceAppVersion` 3.3.0 与线上最新版本一致。dump 的「滞后」上限就是 vts-server 的轮询周期（见 A.3），实际观测为**同一小时内**。

### A.3 vertesan/campus 的更新机制与节奏

- `vertesan/campus`（Go）是 `gakumasu-diff` 与 `gkms-webdata` 的后台 cronjob：用 Firebase 匿名认证登录游戏服务器、下载加密的 master DB（MasterMemory/MessagePack）与混淆的 AssetBundle，解密后把每张表写成一个 YAML 文件，再由 `push_master.sh` 推送到 gakumasu-diff。仓库含 `cronjob.sh`、Docker 封装。
- 观测到的节奏（249 commits / 840 天 ≈ **每 3.4 天一次**，每月 4–13 次）。commit 的 UTC 小时分布高度集中在 02 时（=JST 11 时，学マス的常规更新时刻）与 06–11 时之间，说明 cron 以小时级轮询、只有 master 变化时才 commit。
- 最长间隔 **13 天**（2026-01-27 → 02-09），其余均 ≤12 天；从未出现「几周没更新」的情况，因此不存在系统性滞后。
- 每次 commit 改动 25–130 个文件；**改动文件 ≥ 100 的 commit 与大版本对应**：2024-11-16 `cda4882`（1.5.0）、2024-12-20 `4bad77b`（1.6.x）、2024-12-26 `cb5768d`（1.7.0 / N.I.A）、2025-05-16 `be4e3b4`（2.0.0）、2025-12-26 `6edc27e`（2.7.0 / レジェンド）、2026-05-16 `f0dac51`（3.0.2 / H.I.F）。
- 一个可直接用作「版本↔日期」映射的副产品：`ForceAppVersion.yaml` 自 2024-12-20 出现以来每次变化都对应一次强制更新（见 §B.3.0 的版本表）。

### A.4 对引擎的含义

- 每次同步 dump 后先跑 `history_diff.py HEAD@{1} HEAD`，把「新表 / 新枚举值 / 配置行变化」作为**升级信号**；不要假设 master data 只是「加卡」。
- 机制变化和版本号并不总是同步：2025-10-31 的最終試験スコア上限属于**代码侧**改动，`ResultGradePattern` / `ProduceGrade` 表当天没有任何变化（见 §B.3）。因此引擎的评分规则需要带 `effective_from` 日期、而非只跟 dump commit 走。

---

## Part B — 机制时间线（来自 git 历史）

### B.0 方法与工具

`tools/masterdata/history_diff.py DUMP OLD NEW [--cache DIR] [--examples T:F] [--json OUT]`：

- **新表 / 删表**：`git ls-tree` 比较。
- **顶层字段增删、枚举值增删**（按 `(table, field-path)`）：对每个 commit 的每张表做**逐行文本扫描**（不做 YAML 解析，`- key: value` 布局是机器生成的，扫描结果与解析一致），每个 commit 约 13 s，结果 pickle 到 `--cache`；两个 commit 的 diff 本身瞬时完成。
- **配置表逐行 diff**（默认 `Produce, ProduceSetting, ExamSetting, ResultGradePattern, ProduceGrade, ProduceExamBattleScoreConfig, ProduceStepAuditionDifficulty, ProduceExamBattleConfig, ProduceLiveEvaluation, ProduceSeason, ProduceSeasonZeroGrade, ForceAppVersion`，可用 `--config-tables` 覆盖）：`CSafeLoader` 解析，行键 = `id`；当 `id` 不唯一（如 `ProduceStepAuditionDifficulty` 每个角色 4 行共用一个 id）或没有 `id`（`ResultGradePattern`、`ForceAppVersion`）时自动改用 `id + 所有 *Id/*Type 字段 + number/level/grade` 的复合键。
- `--examples ProduceExamEffect:effectType`：对每个新枚举值在 NEW 版本里找一行示例并打印其 `produceDescriptions[*].text`（日文说明）。
- 本文的数据来自：对全部 249 个 commit 建缓存后按时间顺序两两 diff（脚本 `history_diff.summarize` + 一个 30 行的驱动），以及对上述配置表在**每个触碰它的 commit** 上做逐行 diff（比「按月抽样」更精确：本文给出的首次出现日期都是精确到 commit 的）。

常用：

```bash
python tools/masterdata/history_diff.py data/raw/gakumasu-diff HEAD~1 HEAD --cache /tmp/hcache --examples ProduceExamEffect:effectType,ProduceExamTrigger:phaseTypes
python tools/masterdata/history_diff.py data/raw/gakumasu-diff 6edc27e f0dac51 --cache /tmp/hcache --tables '^Produce' --json legend_to_hif.json
```

注意事项：
- 初始 commit `6a55c6a`/`2621ae8`（2024-05-18）就是 1.0 上线时的全量数据，因此「首次出现 = 2024-05-18」的项目只表示「上线即有」。
- 2024-05-19 `7eeab79` 出现了大量 `*_Unknown` 值和空字段（`null -> ""`）——这是 vertesan 改了序列化方式（把 0 值/默认值也写出来），不是机制变化。同理 2025-01-20/22 `ca49096`/`94c6eb3` 把所有 `descriptions` 字段改名为 `produceDescriptions`（并删除了 `ProduceDescription*Type` 旧表）。**读历史时要区分「序列化变化」与「机制变化」**。
- `ExamSetting` 里的功能开关字段会**出现→翻转→消失**（`examShuffleFixed` 2024-08-10 出现 false→08-29 true→12-20 消失；`auditionSupportUpgradeAdded`、`examCardSelectEvaluationTriggerCoefficientEnable`、`examDrawCountLimitFixed`、`examDrinkTriggerFixed`、`examStanceChangeAssignmentCountEnable` 2024-12～2025-08 出现、2025-10-14 全部翻回 false、2025-10-21 消失）。这些是官方修 bug 时的灰度开关，消失即「行为固化为 true」。引擎不必实现开关本身，但要知道对应行为的生效日期（见 B.3.4）。

### B.1 枚举值时间线

每个家族只列**初始 dump 之后**新增的值（初始值见 `docs/research/master_data_enums.md` / `inspect_dump.py --enums`）。「值」列省略了家族前缀。


#### `ProduceExamEffectType`（`ProduceExamEffect.effectType`，试验内效果）

共 138 个值，其中 67 个在初始 dump（2024-05-18）之后出现。

| 首次出现 | commit | 值 | 名称 / 示例说明（日文，取自 `produceDescriptions[*].text` 或 `ProduceDescription*`.name） | 示例行 |
|---|---|---|---|---|
| 2024-06-01 | `fc8c4c9` | `ExamBlockPerUseCardCount` | 元気+2（レッスン中に使用したスキルカード1枚につき、元気増加量+10） | `e_effect-exam_block_per_use_card_count-0002-0010` `effectValue1=2,effectValue2=10` |
| 2024-08-01 | `d2ff174` | `ExamLessonAddMultipleParameterBuff` | パラメータ+16（好調効果を1.5倍適用） | `e_effect-exam_lesson_add_multiple_parameter_buff-0016-0500-01` `effectValue1=16,effectValue2=500,effectCount=1` |
| 2024-08-01 | `d2ff174` | `ExamLessonDependParameterBuff` | 好調の100%分パラメータ上昇させ、好調を半分にする | `e_effect-exam_lesson_depend_parameter_buff-1000-0500-01` `effectValue1=1000,effectValue2=500,effectCount=1` |
| 2024-08-10 | `05469e1` | `ExamBlockDependExamReview` | 好印象の100%分元気増加 | `e_effect-exam_block_depend_exam_review-1000-01` `effectValue1=1000,effectCount=1` |
| 2024-08-22 | `2e0eccd` | `ExamLessonDependPlayCardCountSum` | パラメータ+20（レッスン中に使用したスキルカード1枚につき、パラメータ上昇量+10） | `e_effect-exam_lesson_depend_play_card_count_sum-0020-0010-01` `effectValue1=20,effectValue2=10,effectCount=1` |
| 2024-09-01 | `dbbca94` | `ExamBlockAddMultipleAggressive` | 元気+10（やる気効果を1.6倍適用） | `e_effect-exam_block_add_multiple_aggressive-0010-0600-01` `effectValue1=10,effectValue2=600,effectCount=1` |
| 2024-09-20 | `3421aa7` | `ExamAggressiveReduce` | やる気減少 / やる気減少1 | `e_effect-exam_aggressive_reduce-0001` `effectValue1=1` |
| 2024-09-20 | `3421aa7` | `ExamLessonBuffReduce` | 集中減少 / 集中減少1 | `e_effect-exam_lesson_buff_reduce-0001` `effectValue1=1` |
| 2024-09-20 | `3421aa7` | `ExamLessonValueMultipleDown` | パラメータ上昇量減少 （描述表无模板，游戏内显示回退文本）| `e_effect-exam_lesson_value_multiple_down-p_card_search-deck_all-all-0_0-g_effect-lesson_reduce-2` |
| 2024-09-20 | `3421aa7` | `ExamParameterBuffReduce` | 好調減少 / 好調減少1 | `e_effect-exam_parameter_buff_reduce-0001` `effectValue1=1` |
| 2024-09-20 | `3421aa7` | `ExamReviewReduce` | 好印象減少 / 好印象減少1 | `e_effect-exam_review_reduce-0001` `effectValue1=1` |
| 2024-10-08 | `6978853` | `ExamLessonDependStaminaConsumptionSum` | レッスン中に消費した体力の1000%分パラメータ上昇 | `e_effect-exam_lesson_depend_stamina_consumption_sum-10000-01` `effectValue1=10000,effectCount=1` |
| 2024-10-18 | `3e082a0` | `ExamReviewDependExamBlock` | 元気の100%分好印象増加させ、元気を0にする | `e_effect-exam_review_depend_exam_block-1000-1000-01` `effectValue1=1000,effectValue2=1000,effectCount=1` |
| 2024-10-25 | `8f45f8b` | `ExamAddGrowEffect` | 成長 （描述表无模板，游戏内显示回退文本）| `e_effect-exam_add_grow_effect-p_card_search-target_is_self-g_effect-lesson_add-8-g_effect-lesson_count_add-1-g_effect-cost_add-1` |
| 2024-10-25 | `8f45f8b` | `ExamStanceReset` | 指針解除 / 指針解除 | `e_effect-exam_stance_reset` |
| 2024-10-25 | `8f45f8b` | `StanceLock` | 指針固定 / 指針固定1ターン | `e_effect-stance_lock-01` `effectTurn=1` |
| 2024-10-28 | `6e35819` | `ExamLessonBuffDependParameterBuff` | 好調の100%分集中増加 | `e_effect-exam_lesson_buff_depend_parameter_buff-1000-01` `effectValue1=1000,effectCount=1` |
| 2024-11-16 | `cda4882` | `ExamForcePlayCardSearch` | 山札か捨札にあるスキルカードを1枚選択し、コストを消費せず使用 | `e_effect-exam_force_play_card_search-p_card_search-deck_grave-select-1_1` |
| 2024-11-16 | `cda4882` | `ExamFullPowerPointReduce` | 全力値減少 / 全力値減少1 | `e_effect-exam_full_power_point_reduce-0001` `effectValue1=1` |
| 2024-11-16 | `cda4882` | `ExamLessonFullPowerPoint` | パラメータ+10（累積全力値の100%分、パラメータ上昇量増加・2回） | `e_effect-exam_lesson_full_power_point-0010-1000-02` `effectValue1=10,effectValue2=1000,effectCount=2` |
| 2024-12-09 | `b83654c` | `ExamAggressiveValueMultiple` | やる気1.3倍 | `e_effect-exam_aggressive_value_multiple-0300` `effectValue1=300` |
| 2024-12-20 | `4bad77b` | `ExamDebuffRecover` | 低下状態回復 / 低下状態回復1 | `e_effect-exam_debuff_recover-0001` `effectValue1=1` |
| 2025-03-21 | `4ba70d5` | `ExamAggressiveAdditive` | やる気増加量増加 / やる気増加量増加+25%（3ターン） | `e_effect-exam_aggressive_additive-0250-03` `effectValue1=250,effectTurn=3` |
| 2025-03-21 | `4ba70d5` | `ExamConcentrationLessonMultipleAdditive` | 強気強化 / 強気強化+35% | `e_effect-exam_concentration_lesson_multiple_additive-0350-inf` `effectValue1=350,effectTurn=-1` |
| 2025-03-21 | `4ba70d5` | `ExamEnthusiasticAdditive` | 熱意追加 / 熱意追加+25（2ターン） | `e_effect-exam_enthusiastic_additive-0025-02` `effectValue1=25,effectTurn=2` |
| 2025-03-21 | `4ba70d5` | `ExamEnthusiasticMultiple` | 熱意増加 / 熱意増加+100%（3ターン） | `e_effect-exam_enthusiastic_multiple-1000-03` `effectValue1=1000,effectTurn=3` |
| 2025-03-21 | `4ba70d5` | `ExamFullPowerLessonMultipleAdditive` | 全力強化 / 全力強化+20%（4ターン） | `e_effect-exam_full_power_lesson_multiple_additive-0200-04` `effectValue1=200,effectTurn=4` |
| 2025-03-21 | `4ba70d5` | `ExamFullPowerPointAdditive` | 全力値増加量増加 / 全力値増加量増加+25%（1ターン） | `e_effect-exam_full_power_point_additive-0250-01` `effectValue1=250,effectTurn=1` |
| 2025-03-21 | `4ba70d5` | `ExamGrowEffectLessonAddAdditive` | パラメータ上昇値増加量増加 | `` |
| 2025-03-21 | `4ba70d5` | `ExamLessonBuffAdditive` | 集中増加量増加 / 集中増加量増加+100%（2ターン） | `e_effect-exam_lesson_buff_additive-1000-02` `effectValue1=1000,effectTurn=2` |
| 2025-03-21 | `4ba70d5` | `ExamLessonDependStamina` | 体力の1000%分パラメータ上昇 | `e_effect-exam_lesson_depend_stamina-10000-01` `effectValue1=10000,effectCount=1` |
| 2025-03-21 | `4ba70d5` | `ExamLessonValueMultipleDependReviewOrAggressive` | プライド / プライド（2ターン） | `e_effect-exam_lesson_value_multiple_depend_review_or_aggressive-02` `effectTurn=2` |
| 2025-03-21 | `4ba70d5` | `ExamOverPreservation` | のんびり / のんびりに変更 | `e_effect-exam_over_preservation` |
| 2025-03-21 | `4ba70d5` | `ExamParameterBuffAdditive` | 好調増加量増加 / 好調増加量増加+100%（3ターン） | `e_effect-exam_parameter_buff_additive-1000-03` `effectValue1=1000,effectTurn=3` |
| 2025-03-21 | `4ba70d5` | `ExamParameterBuffMultiplePerTurnReduce` | 絶好調減少 / 絶好調減少1 | `e_effect-exam_parameter_buff_multiple_per_turn_reduce-0001` `effectValue1=1` |
| 2025-03-21 | `4ba70d5` | `ExamReviewAdditive` | 好印象増加量増加 / 好印象増加量増加+100%（3ターン） | `e_effect-exam_review_additive-1000-03` `effectValue1=1000,effectTurn=3` |
| 2025-03-21 | `4ba70d5` | `ExamReviewDependExamCardPlayAggressive` | やる気の300%分好印象増加 | `e_effect-exam_review_depend_exam_card_play_aggressive-3000-01` `effectValue1=3000,effectCount=1` |
| 2025-03-21 | `4ba70d5` | `ExamReviewMultiple` | 好印象強化 / 好印象強化+100%（3ターン） | `e_effect-exam_review_multiple-1000-03` `effectValue1=1000,effectTurn=3` |
| 2025-03-24 | `0981177` | `ExamItemFireLimitAdd` | アイドル固有Pアイテムの発動回数+1 | `e_effect-exam_item_fire_limit_add-0001` `effectValue1=1` |
| 2025-04-21 | `a1d531d` | `ExamLessonDependAggressiveAndSearchCount` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2025-04-21 | `a1d531d` | `ExamLessonDependBlockAndSearchCount` | 除外にある私を超えて（翔）1枚につき、元気の20%分パラメータ上昇 | `e_effect-exam_lesson_depend_block_and_search_count-0200-01-p_card_search-lost-p_card-02-ido-3_190-all-0_0` `effectValue2=200,effectCount=1` |
| 2025-04-21 | `a1d531d` | `ExamLessonDependReviewAndSearchCount` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2025-04-22 | `3f61123` | `ExamAggressiveDependReview` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2025-04-22 | `3f61123` | `ExamAggressivePerSearchCount` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2025-04-22 | `3f61123` | `ExamBlockPerSearchCount` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2025-04-22 | `3f61123` | `ExamFullPowerPointPerSearchCount` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2025-04-22 | `3f61123` | `ExamLessonBuffPerSearchCount` | 除外にあるスキルカード2枚につき、集中+1 | `e_effect-exam_lesson_buff_per_search_count-0500-p_card_search-lost-all-0_0` `effectValue2=500` |
| 2025-04-22 | `3f61123` | `ExamMultipleConcentrationLesson` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2025-04-22 | `3f61123` | `ExamMultipleEnthusiasticLesson` | パラメータ+1（熱意効果を2倍適用） | `e_effect-exam_multiple_enthusiastic_lesson-0001-1000-01` `effectValue1=1,effectValue2=1000,effectCount=1` |
| 2025-04-22 | `3f61123` | `ExamMultipleFullPowerLesson` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2025-04-22 | `3f61123` | `ExamParameterBuffDependLessonBuff` | 集中の100%分好調増加させ、集中を半分にする | `e_effect-exam_parameter_buff_depend_lesson_buff-1000-0500-01` `effectValue1=1000,effectValue2=500,effectCount=1` |
| 2025-04-22 | `3f61123` | `ExamParameterBuffPerSearchCount` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2025-04-22 | `3f61123` | `ExamReviewPerSearchCount` | 山札か捨札にあるスキルカード1枚ごとに、好印象+1 | `e_effect-exam_review_per_search_count-1000-p_card_search-deck_grave` `effectValue2=1000` |
| 2025-12-26 | `6edc27e` | `ExamLessonDependBlockConsumptionSum` | レッスン中に消費した元気の100%分パラメータ上昇 | `e_effect-exam_lesson_depend_block_consumption_sum-1000-01` `effectValue1=1000,effectCount=1` |
| 2026-03-31 | `ff8795e` | `ExamBlockDependBlockConsumptionSum` | レッスン中に消費した元気の100%分元気増加 | `e_effect-exam_block_depend_block_consumption_sum-1000-01` `effectValue1=1000,effectCount=1` |
| 2026-03-31 | `ff8795e` | `ExamEnthusiasticTurnAdd` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2026-03-31 | `ff8795e` | `ExamReviewCountAdd` | 好印象追加発動 / 好印象追加発動+1（3ターン） | `e_effect-exam_review_count_add-0001-03` `effectValue1=1,effectTurn=3` |
| 2026-05-16 | `f0dac51` | `ExamForcePlayCardSearchWithCost` | 除外以外のスキルカードを1枚選択し、コストを消費して使用 | `e_effect-exam_force_play_card_search_with_cost-p_card_search-not_lost-select-1_1` |
| 2026-05-16 | `f0dac51` | `ExamStatusEnchantEncore` | 再演 / レッスン終了まで、スキルカード使用後、手札にある自然体の魅力が1枚以上の場合、自身を再使用（4回まで発動・ターン内1回まで）再演：スキルカード使用後、手札にある自然体の魅力が1枚以上の場合、自身を再使用（4回まで・ターン | `e_effect-exam_status_enchant_encore-0001-04-inf-enchant-p_card-01-ido-3_200-enc01` `effectValue1=1,effectCount=4,effectTurn=-1` |
| 2026-05-26 | `aba06dc` | `ExamAggressiveAdditiveFix` | やる気増加量追加 / やる気増加量追加+1（2ターン） | `e_effect-exam_aggressive_additive_fix-0001-02` `effectValue1=1,effectTurn=2` |
| 2026-05-26 | `aba06dc` | `ExamFullPowerPointAdditiveFix` | 全力値増加量追加 | `` |
| 2026-05-26 | `aba06dc` | `ExamLessonBuffAdditiveFix` | 集中増加量追加 / 集中増加量追加+1（4ターン） | `e_effect-exam_lesson_buff_additive_fix-0001-04` `effectValue1=1,effectTurn=4` |
| 2026-05-26 | `aba06dc` | `ExamParameterBuffAdditiveFix` | 好調増加量追加 | `` |
| 2026-05-26 | `aba06dc` | `ExamReviewAdditiveFix` | 好印象増加量追加 | `` |
| 2026-06-11 | `3d6c98c` | `ExamFullPowerPointDependFullPowerPointGetSum` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2026-06-11 | `3d6c98c` | `ExamLessonDependEnthusiasticGetSum` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |
| 2026-06-11 | `3d6c98c` | `ExamMoveGrowEffect` | （HEAD 中无示例行；仅在枚举/描述表出现） | `` |

#### `ProduceExamPhaseType`（`ProduceExamTrigger.phaseTypes[]`，触发相位）

共 30 个值，其中 18 个在初始 dump（2024-05-18）之后出现。

| 首次出现 | commit | 值 | 名称 / 示例说明（日文，取自 `produceDescriptions[*].text` 或 `ProduceDescription*`.name） | 示例行 |
|---|---|---|---|---|
| 2024-06-19 | `63cb6ba` | `ExamStaminaReduce` | 直接効果で体力が減少した時、の場合、使用可 | `e_trigger-exam_stamina_reduce` |
| 2024-06-24 | `9b0cc92` | `ExamCardMoveLost` | スキルカードが除外に移動した時、の場合、使用可 | `e_trigger-exam_card_move_lost-p_card_search-target` |
| 2024-06-24 | `9b0cc92` | `ExamPlayTurnCountInterval` | 好印象が6以上の場合、ターン内にスキルカードを2回使用するごとに、好印象が6以上の場合、使用可 | `e_trigger-exam_play_turn_count_interval-2-review_up-6-p_card_search-target` `phaseValues=[2]` |
| 2024-11-06 | `3d0028d` | `None` | 山札か捨札にあるトラブルカードが1枚以上の場合、山札か捨札にあるトラブルカードが1枚以上の場合、使用可 | `e_trigger-none-card_search_count_up-1-p_card_search-trouble-deck_grave` |
| 2024-11-16 | `cda4882` | `ExamCardMoveGrave` | 自身が捨て札に移動した時、の場合、使用可 | `e_trigger-exam_card_move_grave-p_card_search-target_is_self` |
| 2024-11-16 | `cda4882` | `ExamCardMoveHand` | 自身が手札に移動した時、の場合、使用可 | `e_trigger-exam_card_move_hand-p_card_search-target_is_self` |
| 2024-11-16 | `cda4882` | `ExamSearchCardPlay` | （描述表无模板，游戏内显示回退文本）| `e_trigger-exam_search_card_play-full_power_up-p_card_search-target_is_self-0_1` |
| 2024-11-16 | `cda4882` | `ExamStanceChangeConcentration` | 直接効果で強気になった時、このレッスン中の累計全力値が5以上の場合、このレッスン中の累計全力値が5以上の場合、使用可 | `e_trigger-exam_stance_change_concentration-full_power_point_get_sum_up-5` |
| 2024-11-16 | `cda4882` | `ExamStanceChangeCountInterval` | 直接効果で指針を2回変更するたび、の場合、使用可 | `e_trigger-exam_stance_change_count_interval-2` `phaseValues=[2]` |
| 2024-11-16 | `cda4882` | `ExamStanceChangeFullPower` | 全力になった時、強気になった回数が1回以上の場合、強気になった回数が1回以上の場合、使用可 | `e_trigger-exam_stance_change_full_power-concentration_change_count_up-1` |
| 2024-11-16 | `cda4882` | `ExamStanceChangePreservation` | 直接効果で温存になった時、の場合、使用可 | `e_trigger-exam_stance_change_preservation` |
| 2025-02-21 | `e65dc7e` | `ExamBuffConsume` | スキルカードコストで強化状態を消費した時、好調が3ターン以上の場合、好調が3ターン以上の場合、使用可 | `e_trigger-exam_buff_consume-parameter_buff_up-3` |
| 2025-03-24 | `0981177` | `ExamTurnSkip` | ターンスキップ時、絶好調状態の場合、絶好調状態の場合、使用可 | `e_trigger-exam_turn_skip-parameter_buff_multiple_per_turn_up-1` |
| 2025-06-09 | `28cf6f6` | `ExamEndTurnInterval` | 2ターンごとのターン終了時、除外にあるスキルカードが8枚以下の場合、除外にあるスキルカードが8枚以下の場合、使用可 | `e_trigger-exam_end_turn_interval-2-not-card_search_count_up-9-p_card_search-lost` `phaseValues=[2]` |
| 2025-08-12 | `f6ea7d0` | `ExamStanceChangeFromFullPower` | 全力を解除後、除外にあるでこれーとまじっくが1枚以上の場合、除外にあるでこれーとまじっくが1枚以上の場合、使用可 | `e_trigger-exam_stance_change_from_full_power-card_search_count_up-1-p_card_search-lost-p_card-03-ido-3_144` |
| 2026-02-19 | `374cf1a` | `ExamPlayCountIntervalAfter` | 好調が5ターン以上の場合、メンタルスキルカード使用後3回ごとに、好調が5ターン以上の場合、使用可 | `e_trigger-exam_play_count_interval_after-3-parameter_buff_up-5-p_card_search-mental_skill-target` `phaseValues=[3]` |
| 2026-03-09 | `8f2f3e2` | `ExamStanceChangeFromConcentration` | 直接効果で強気を解除後、全力の場合、全力の場合、使用可 | `e_trigger-exam_stance_change_from_concentration-full_power_up` |
| 2026-05-26 | `aba06dc` | `ExamAggressiveUpInterval` | 直接効果でやる気が5回増加時、の場合、使用可 | `e_trigger-exam_aggressive_up_interval-5-exam_card_play_aggressive` `phaseValues=[5]` |

#### `ProduceExamFieldStatusType`（`ProduceExamTrigger.fieldStatusTypes[]`，触发条件）

共 29 个值，其中 14 个在初始 dump（2024-05-18）之后出现。

| 首次出现 | commit | 值 | 名称 / 示例说明（日文，取自 `produceDescriptions[*].text` 或 `ProduceDescription*`.name） | 示例行 |
|---|---|---|---|---|
| 2024-06-24 | `9b0cc92` | `PlayCardLesson` | アクティブスキルカード使用時、直前にアクティブスキルカードを使用した状態の場合、直前にアクティブスキルカードを使用した状態の場合、使用可 | `e_trigger-exam_card_play-play_card_lesson-p_card_search-active_skill-playing-0_1` |
| 2024-06-24 | `9b0cc92` | `PlayCardSkill` | アクティブスキルカード使用時、直前にメンタルスキルカードを使用した状態の場合、直前にメンタルスキルカードを使用した状態の場合、使用可 | `e_trigger-exam_card_play-play_card_skill-p_card_search-active_skill-playing-0_1` |
| 2024-11-16 | `cda4882` | `ConcentrationChangeCountUp` | 【ダンスレッスン・ダンスターンのみ】ターン開始時、強気になった回数が3回以上の場合、強気になった回数が3回以上の場合、使用可 | `e_trigger-exam_start_turn-concentration_change_count_up-3-lesson_dance` `fieldStatusValues=[3]` |
| 2024-11-16 | `cda4882` | `ConcentrationUp` | 【ダンスレッスン・ダンスターンのみ】ターン開始後、強気の場合、強気の場合、使用可 | `e_trigger-start_play-concentration_up-lesson_dance` |
| 2024-11-16 | `cda4882` | `FullPowerChangeCountUp` | 全力になった時、全力になった回数が2回以上の場合、全力になった回数が2回以上の場合、使用可 | `e_trigger-exam_stance_change_full_power-full_power_change_count_up-2` `fieldStatusValues=[2]` |
| 2024-11-16 | `cda4882` | `FullPowerPointGetSumUp` | 直接効果で強気になった時、このレッスン中の累計全力値が5以上の場合、このレッスン中の累計全力値が5以上の場合、使用可 | `e_trigger-exam_stance_change_concentration-full_power_point_get_sum_up-5` `fieldStatusValues=[5]` |
| 2024-11-16 | `cda4882` | `FullPowerPointUp` | アイドル固有スキルカード使用後、全力値が9以下の場合、全力値が9以下の場合、使用可 | `e_trigger-exam_card_play_after-not-full_power_point_up-10-p_card_search-playing-idol-unique-0_1` `fieldStatusValues=[10]` |
| 2024-11-16 | `cda4882` | `FullPowerUp` | （描述表无模板，游戏内显示回退文本）| `e_trigger-exam_search_card_play-full_power_up-p_card_search-target_is_self-0_1` |
| 2024-11-16 | `cda4882` | `NoStance` | いずれかの指針の場合、強気効果のスキルカード使用後3回ごとに、いずれかの指針の場合、使用可 | `e_trigger-exam_play_count_interval_after-3-not-no_stance-p_card_search-target-effect_group-visible-exam_concentration-000` |
| 2024-11-16 | `cda4882` | `PreservationChangeCountUp` | 【ビジュアルレッスン・ビジュアルターンのみ】ターン開始時、温存になった回数が4回以上の場合、温存になった回数が4回以上の場合、使用可 | `e_trigger-exam_start_turn-preservation_change_count_up-4-lesson_visual` `fieldStatusValues=[4]` |
| 2024-11-16 | `cda4882` | `PreservationUp` | 【ビジュアルレッスン・ビジュアルターンのみ】ターン開始後、温存の場合、温存の場合、使用可 | `e_trigger-start_play-preservation_up-lesson_visual` |
| 2024-12-20 | `4de551b` | `StanceChangeCountUp` | 【ボーカルレッスン・ボーカルターンのみ】ターン開始時、指針を変更した回数が4回以上の場合、指針を変更した回数が4回以上の場合、使用可 | `e_trigger-exam_start_turn-stance_change_count_up-4-lesson_vocal` `fieldStatusValues=[4]` |
| 2025-01-09 | `8c8cd91` | `CardSearchCountUp` | 【ビジュアルレッスン・ビジュアルターンのみ】ターン開始時、除外にあるスキルカードが7枚以上の場合、除外にあるスキルカードが7枚以上の場合、使用可 | `e_trigger-exam_start_turn-card_search_count_up-7-p_card_search-lost-lesson_visual` `fieldStatusValues=[7]` |
| 2025-08-22 | `0fdb17b` | `ParameterBuffMultiplePerTurnUp` | スキルカード使用後、絶好調が5ターン以上の場合、絶好調が5ターン以上の場合、使用可 | `e_trigger-exam_card_play_after-parameter_buff_multiple_per_turn_up-5-p_card_search-target-0_1` `fieldStatusValues=[5]` |

#### `ProduceCardGrowEffectType`（`ProduceCardGrowEffect.effectType`，卡牌成长/カスタマイズ）

共 54 个值，其中 53 个在初始 dump（2024-05-18）之后出现。整个家族在 2024-10-25（アノマリー/成長 上线）才出现。

| 首次出现 | commit | 值 | 名称 / 示例说明（日文，取自 `produceDescriptions[*].text` 或 `ProduceDescription*`.name） | 示例行 |
|---|---|---|---|---|
| 2024-10-25 | `4eeeeea` | `AggressiveAdd` | やる気値増加 | `g_effect-aggressive_add-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `AggressiveReduce` | やる気値減少 | `` |
| 2024-10-25 | `8f45f8b` | `BlockAdd` | 元気値増加 | `g_effect-block_add-1` `value=1` |
| 2024-10-25 | `8f45f8b` | `BlockReduce` | 元気値減少 | `g_effect-block_reduce-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `CardDrawAdd` | ドロー枚数増加 | `` |
| 2024-10-25 | `4eeeeea` | `CardDrawReduce` | ドロー枚数減少 | `` |
| 2024-10-25 | `4eeeeea` | `CardStatusEnchantChange` | 成長変更 | `g_effect-card_status_enchant_change-card_enchant-e_trigger-exam_card_play_after-p_card_search-target-effect_group-visible-exam_concentration-000-0_1-2-g_effect-lesson_add-15-g_effect-lesson_count_add-1` |
| 2024-10-25 | `8f45f8b` | `CostAdd` | コスト値増加 | `g_effect-cost_add-1` `value=1` |
| 2024-10-25 | `8f45f8b` | `CostBuffAdd` | 強化状態コスト値増加 | `` |
| 2024-10-25 | `8f45f8b` | `CostBuffReduce` | 強化状態コスト値減少 | `` |
| 2024-10-25 | `8f45f8b` | `CostPenetrateAdd` | 体力消費コスト値増加 | `g_effect-cost_penetrate_add-1` `value=1` |
| 2024-10-25 | `8f45f8b` | `CostPenetrateReduce` | 体力消費コスト値減少 | `g_effect-cost_penetrate_reduce-1` `value=1` |
| 2024-10-25 | `8f45f8b` | `CostReduce` | コスト値減少 | `g_effect-cost_reduce-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `EffectAdd` | 効果追加 | `g_effect-effect_add-e_effect-exam_add_grow_effect-p_card_search-deck_all-all-0_0-g_effect-lesson_add-1` |
| 2024-10-25 | `4eeeeea` | `EffectChange` | 効果置換 | `g_effect-effect_change-e_effect-exam_block_per_use_card_count-0002-0008-e_effect-exam_status_enchant-02-inf-enchant-p_card-02-ido-3_067-enc01` |
| 2024-10-25 | `4eeeeea` | `EffectDelete` | 効果削除 | `` |
| 2024-10-25 | `8f45f8b` | `FullPowerPointAdd` | 全力値増加 | `g_effect-full_power_point_add-1` `value=1` |
| 2024-10-25 | `8f45f8b` | `FullPowerPointReduce` | 全力値減少 | `g_effect-full_power_point_reduce-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `InitialAdd` | 開始時手札効果付与 | `g_effect-initial_add` |
| 2024-10-25 | `8f45f8b` | `LessonAdd` | パラメータ値増加 | `g_effect-lesson_add-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `LessonBuffAdd` | 集中値増加 | `g_effect-lesson_buff_add-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `LessonBuffReduce` | 集中値減少 | `` |
| 2024-10-25 | `8f45f8b` | `LessonCountAdd` | パラメータ上昇回数増加 | `g_effect-lesson_count_add-1` `value=1` |
| 2024-10-25 | `8f45f8b` | `LessonCountReduce` | パラメータ上昇回数減少 | `g_effect-lesson_count_reduce-1` `value=1` |
| 2024-10-25 | `8f45f8b` | `LessonReduce` | パラメータ値減少 | `g_effect-lesson_reduce-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `ParameterBuffMultiplePerTurnAdd` | 絶好調値増加 | `g_effect-parameter_buff_multiple_per_turn_add-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `ParameterBuffMultiplePerTurnReduce` | 絶好調値減少 | `` |
| 2024-10-25 | `4eeeeea` | `ParameterBuffTurnAdd` | 好調値増加 | `g_effect-parameter_buff_turn_add-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `ParameterBuffTurnReduce` | 好調値減少 | `` |
| 2024-10-25 | `4eeeeea` | `PlayEffectTriggerChange` | 効果発動条件を置換 | `g_effect-play_effect_trigger_change-e_trigger-exam_card_play-card_play_aggressive_up-3` |
| 2024-10-25 | `4eeeeea` | `PlayMovePositionTypeChange` | 使用後移動先変更 | `g_effect-play_move_position_type_change-grave` |
| 2024-10-25 | `4eeeeea` | `PlayTriggerChange` | 使用可能条件を置換 | `g_effect-play_trigger_change-e_trigger-none-block_up-30-e_trigger-none-block_up-15` |
| 2024-10-25 | `4eeeeea` | `ReviewAdd` | 好印象値増加 | `g_effect-review_add-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `ReviewReduce` | 好印象値減少 | `` |
| 2024-10-25 | `4eeeeea` | `StaminaConsumptionAddTurnAdd` | 消費体力増加値減少 | `` |
| 2024-10-25 | `4eeeeea` | `StaminaConsumptionAddTurnReduce` | 消費体力増加値増加 | `` |
| 2024-10-25 | `4eeeeea` | `StaminaConsumptionDownTurnAdd` | 消費体力減少値増加 | `g_effect-stamina_consumption_down_turn_add-1` `value=1` |
| 2024-10-25 | `4eeeeea` | `StaminaConsumptionDownTurnReduce` | 消費体力減少値減少 | `` |
| 2024-12-20 | `4bad77b` | `CostAggressiveAdd` | やる気コスト値増加 | `g_effect-cost_aggressive_add-1` `value=1` |
| 2024-12-20 | `4bad77b` | `CostAggressiveReduce` | やる気コスト値減少 | `g_effect-cost_aggressive_reduce-1` `value=1` |
| 2024-12-20 | `4bad77b` | `CostFullPowerPointAdd` | 全力値コスト値増加 | `g_effect-cost_full_power_point_add-1` `value=1` |
| 2024-12-20 | `4bad77b` | `CostFullPowerPointReduce` | 全力値コスト値減少 | `g_effect-cost_full_power_point_reduce-1` `value=1` |
| 2024-12-20 | `4bad77b` | `CostLessonBuffAdd` | 集中コスト値増加 | `g_effect-cost_lesson_buff_add-1` `value=1` |
| 2024-12-20 | `4bad77b` | `CostLessonBuffReduce` | 集中コスト値減少 | `g_effect-cost_lesson_buff_reduce-1` `value=1` |
| 2024-12-20 | `4bad77b` | `CostParameterBuffAdd` | 好調コスト値増加 | `g_effect-cost_parameter_buff_add-1` `value=1` |
| 2024-12-20 | `4bad77b` | `CostParameterBuffReduce` | 好調コスト値減少 | `g_effect-cost_parameter_buff_reduce-1` `value=1` |
| 2024-12-20 | `4bad77b` | `CostReviewAdd` | 好印象コスト値増加 | `g_effect-cost_review_add-1` `value=1` |
| 2024-12-20 | `4bad77b` | `CostReviewReduce` | 好印象コスト値減少 | `g_effect-cost_review_reduce-1` `value=1` |
| 2024-12-20 | `4bad77b` | `LessonDependBlockAdd` | 元気分パラメータ倍率増加 | `g_effect-lesson_depend_block_add-100` `value=100` |
| 2024-12-20 | `4bad77b` | `LessonDependExamCardPlayAggressiveAdd` | やる気分パラメータ倍率増加 | `g_effect-lesson_depend_exam_card_play_aggressive_add-1000` `value=1000` |
| 2024-12-20 | `4bad77b` | `LessonDependExamReviewAdd` | 好印象分パラメータ倍率増加 | `g_effect-lesson_depend_exam_review_add-1000` `value=1000` |
| 2025-03-21 | `4ba70d5` | `CostParameterBuffMultiplePerTurnAdd` | 絶好調コスト値増加 | `` |
| 2025-03-21 | `4ba70d5` | `CostParameterBuffMultiplePerTurnReduce` | 絶好調コスト値減少 | `g_effect-cost_parameter_buff_multiple_per_turn_reduce-1` `value=1` |

#### `ProduceEffectType`（`ProduceEffect.produceEffectType`，培育外循环效果）

共 103 个值，其中 32 个在初始 dump（2024-05-18）之后出现。

| 首次出现 | commit | 值 | 名称 / 示例说明（日文，取自 `produceDescriptions[*].text` 或 `ProduceDescription*`.name） | 示例行 |
|---|---|---|---|---|
| 2024-09-20 | `3421aa7` | `AuditionNpcEnhance` | ライバルのスコア | `p_effect-audition_npc_enhance-0020_0020` |
| 2024-09-20 | `3421aa7` | `BeforeAuditionRefreshStaminaDown` | 試験前体力回復量減少 | `p_effect-before_audition_refresh_stamina_down-0250_0250` |
| 2024-09-20 | `3421aa7` | `BeforeAuditionRefreshStaminaUp` | 試験前体力回復量増加 | `p_effect-before_audition_refresh_stamina_up-0050_0050` |
| 2024-09-20 | `3421aa7` | `EventActivityProducePointDown` | お出かけの消費Pポイント減少 | `p_effect-event_activity_produce_point_down-0500_0500` |
| 2024-09-20 | `3421aa7` | `EventActivityProducePointUp` | お出かけの消費Pポイント増加 | `p_effect-event_activity_produce_point_up-0250_0250` |
| 2024-09-20 | `3421aa7` | `EventSchoolStaminaDown` | 授業の消費体力減少 | `p_effect-event_school_stamina_down-0500_0500` |
| 2024-09-20 | `3421aa7` | `EventSchoolStaminaUp` | 授業の消費体力増加 | `p_effect-event_school_stamina_up-0100_0100` |
| 2024-09-20 | `3421aa7` | `ExamTurnDown` | ターン数減少 | `p_effect-exam_turn_down-0001_0001` |
| 2024-09-20 | `3421aa7` | `ExamTurnUp` | ターン数増加 | `` |
| 2024-09-20 | `3421aa7` | `ShopPriceUpMultiple` | 相談の全項目を割増 | `p_effect-shop_price_up_multiple-0050_0050` |
| 2024-09-20 | `3421aa7` | `ShopProduceCardDeletePriceUpMultiple` | 相談のスキルカード削除を割増 | `` |
| 2024-09-20 | `3421aa7` | `ShopProduceCardPriceUpMultiple` | 相談のスキルカードを割増 | `` |
| 2024-09-20 | `3421aa7` | `ShopProduceCardUpgradePriceUpMultiple` | 相談のスキルカード強化を割増 | `` |
| 2024-09-20 | `3421aa7` | `ShopProduceDrinkPriceUpMultiple` | 相談のPドリンクを割増 | `` |
| 2024-12-26 | `cb5768d` | `AuditionVoteCountUp` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-audition_vote_count_up-0050_0050` |
| 2024-12-26 | `cb5768d` | `EventBusinessVoteCountUp` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-event_business_vote_count_up-0050_0050` |
| 2024-12-26 | `cb5768d` | `ProduceCardExcludeCountUp` | スキルカード除去 | `p_effect-produce_card_exclude_count_up-0001_0001` |
| 2024-12-26 | `cb5768d` | `VoteCountAddition` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-vote_count_addition-0800_0800` |
| 2025-03-21 | `4ba70d5` | `HighScoreGoldAddition` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-high_score_gold_addition-0020_0020` |
| 2025-05-16 | `be4e3b4` | `IdolCardProduceCardCustomizeEnable` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-idol_card_produce_card_customize_enable` |
| 2025-06-19 | `15272c3` | `ShopRerollCountUp` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-shop_reroll_count_up-0001_0001` |
| 2025-12-26 | `6edc27e` | `ExamPermanentAuditionStatusEnchant` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-exam_permanent_audition_status_enchant-enchant-customize_pitem-01-04-3-001_00-04-2-001_01-01-1-001_00-04-4-001-enc01` |
| 2025-12-26 | `6edc27e` | `ExamPermanentLessonStatusEnchant` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-exam_permanent_lesson_status_enchant-enchant-pitem_00-1-048-challenge-enc01` |
| 2026-03-31 | `ff8795e` | `AuditionNpcWeaken` | ライバルのスコア | `p_effect-audition_npc_weaken-0500_0500` |
| 2026-05-16 | `f0dac51` | `CustomizeProduceCardProducePointDownMultiple` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-customize_produce_card_produce_point_down_multiple-0200_0200` |
| 2026-05-16 | `f0dac51` | `ParameterLimitUp` | パラメータ上限増加 | `p_effect-parameter_limit_up-0050_0050` |
| 2026-05-16 | `f0dac51` | `ProduceCardChangeSelect` | セレクトチェンジ | `p_effect-produce_card_change_select-0001_0001-p_rd-produce_007-customizeitem-p_card_search-active_skill-mental_skill-deck_all-select-01_01` |
| 2026-05-16 | `f0dac51` | `ProduceCustomizeItemUpgrade` | （HEAD 中无示例行；仅在枚举/描述表出现） | `p_effect-produce_customize_item_upgrade-select-01_01` |
| 2026-05-16 | `f0dac51` | `ProduceDrinkPossessLimitUp` | Pドリンク所持上限増加 | `p_effect-produce_drink_possess_limit_up-0001_0001` |
| 2026-05-16 | `f0dac51` | `ShopProduceCardPriceDiscountMultiplePermanent` | 相談のスキルカードを割引 | `p_effect-shop_produce_card_price_discount_multiple_permanent-0050_0050-p_card_search-deck_all` |
| 2026-05-16 | `f0dac51` | `StarAddition` | スター性獲得 | `p_effect-star_addition-0010_0010` |
| 2026-05-16 | `f0dac51` | `StarPermilUp` | スター性獲得量増加 | `p_effect-star_permil_up-0050_0050` |

#### `ProducePhaseType`（`ProduceTrigger.phaseType`，培育相位）


**`ProducePhaseType`**：共 29 个值，初始之后新增 15 个。

- 2024-07-22 `4202981`：`BuyShopItemProduceDrink`
- 2024-12-26 `cb5768d`：`EndBeforeAuditionRefresh`, `StartAuditionFinal`, `StartAuditionMid1`, `StartAuditionMid2`, `StartCustomize`
- 2025-05-01 `117c736`：`ChangeProduceCard`
- 2025-05-19 `676438a`：`EndPresent`, `EndShop`, `EndStepEventBusiness`
- 2025-05-29 `87149c3`：`GetProduceDrink`
- 2025-06-09 `28cf6f6`：`CustomizeProduceCard`
- 2025-09-17 `ac884f1`：`GetProduceItem`
- 2025-12-26 `6edc27e`：`StartAudition`
- 2026-07-31 `6271031`：`BuyShopItemProduceCard`

#### `ProduceStepType`（步骤类型；出现在 `ProduceStepAuditionDifficulty.stepType`、`ProduceStepTransition` 等）


**`ProduceStepType`**：共 34 个值，初始之后新增 21 个。

- 2024-12-26 `cb5768d`：`AuditionMid2`, `Business`, `FanPresent`, `SelfLessonDanceNormal`, `SelfLessonDanceSp`, `SelfLessonVisualNormal`, `SelfLessonVisualSp`, `SelfLessonVocalNormal`, `SelfLessonVocalSp`
- 2026-05-16 `f0dac51`：`OpenLessonDanceNormal`, `OpenLessonDanceNormalStar`, `OpenLessonDanceSp`, `OpenLessonDanceSpStar`, `OpenLessonVisualNormal`, `OpenLessonVisualNormalStar`, `OpenLessonVisualSp`, `OpenLessonVisualSpStar`, `OpenLessonVocalNormal`, `OpenLessonVocalNormalStar`, `OpenLessonVocalSp`, `OpenLessonVocalSpStar`

#### `ProduceType` / `ProduceSplitType`（剧本族 / 分段）


**`ProduceType`**：共 4 个值，初始之后新增 2 个。

- 2024-12-26 `cb5768d`：`NextIdolAudition`
- 2026-05-16 `f0dac51`：`HatsuboshiIdolFestival`

**`ProduceSplitType`**：共 3 个值，初始之后新增 2 个。

- 2026-05-16 `f0dac51`：`Final`, `Selection`

#### `ProduceCardCategory` / `ProduceCardRarity` / `ProduceCardMovePositionType` / `ProduceCardPositionType` / `ProduceCardMoveEffectTriggerType` / `ProducePlanType` / `ExamCostType`


**`ProduceCardCategory`**：共 4 个值，初始之后新增 0 个。

- （无新增）

**`ProduceCardRarity`**：共 5 个值，初始之后新增 1 个。

- 2025-12-26 `6edc27e`：`Legend`

**`ProduceCardMovePositionType`**：共 8 个值，初始之后新增 2 个。

- 2024-06-24 `9b0cc92`：`DeckLast`
- 2024-11-16 `cda4882`：`Hold`

**`ProduceCardPositionType`**：共 10 个值，初始之后新增 4 个。

- 2024-06-24 `9b0cc92`：`Lost`
- 2024-11-16 `cda4882`：`DeckGrave`, `Hold`
- 2025-12-26 `6edc27e`：`NotLost`

**`ProduceCardMoveEffectTriggerType`**：共 3 个值，初始之后新增 2 个。

- 2025-12-26 `6edc27e`：`Hand`
- 2026-03-31 `ff8795e`：`Hold`

**`ProducePlanType`**：共 5 个值，初始之后新增 1 个。

- 2024-10-25 `8f45f8b`：`Plan3`

**`ExamCostType`**：共 7 个值，初始之后新增 2 个。

- 2024-11-16 `cda4882`：`ExamFullPowerPoint`
- 2026-03-09 `8f2f3e2`：`ExamParameterBuffMultiplePerTurn`

**`ProducePickRangeType`**：共 4 个值，初始之后新增 0 个。

- （无新增）

**`ProducePickCountType`**：共 2 个值，初始之后新增 1 个。

- 2026-05-16 `f0dac51`：`Shortage`

#### `ProduceStepAuditionType` / `ProduceStepBusinessType` / `ProduceStepLessonType`


**`ProduceStepAuditionType`**：共 11 个值，初始之后新增 10 个。

- 2024-12-26 `cb5768d`：`FinalEasy`, `FinalHard`, `FinalNormal`, `FinalVeryHard`, `Mid1Easy`, `Mid1Hard`, `Mid1Normal`, `Mid2Easy`, `Mid2Hard`, `Mid2Normal`

**`ProduceStepBusinessType`**：共 4 个值，初始之后新增 3 个。

- 2025-08-22 `0fdb17b`：`ProduceCard`, `ProduceDrink`, `ProducePoint`

**`ProduceStepLessonType`**：共 5 个值，初始之后新增 1 个。

- 2024-09-20 `3421aa7`：`LessonSp`

#### `ResultGrade` / `ResultGradeType` / `ProducerRankingGrade`


**`ResultGrade`**：共 20 个值，初始之后新增 6 个。

- 2025-05-19 `676438a`：`Sss`, `SssPlus`
- 2025-12-26 `6edc27e`：`Ssss`
- 2026-05-16 `f0dac51`：`SsssPlus`, `Sssss`, `SssssPlus`

**`ResultGradeType`**：共 6 个值，初始之后新增 2 个。

- 2024-12-26 `cb5768d`：`ProduceVoteCount`
- 2026-05-16 `f0dac51`：`ProduceStar`

**`ProducerRankingGrade`**：共 6 个值，初始之后新增 6 个。

- 2025-09-29 `26f0628`：`Bronze`, `Gold`, `Normal`, `Rainbow`, `RainbowPlus`, `Silver`

#### `ProduceExamAutoEvaluationType` / `ExamPlayType` / `ExamStatusEffectType`（官方 AutoPlay 与 コンテスト）


**`ProduceExamAutoEvaluationType`**：共 53 个值，初始之后新增 35 个。

- 2024-06-24 `9b0cc92`：`ExamExtraTurn`
- 2024-10-25 `4eeeeea`：`ExamConcentration`, `ExamConcentrationCount`, `ExamFullPower`, `ExamFullPowerCount`, `ExamFullPowerPointTotal`, `ExamPreservation`, `ExamPreservationCount`, `HoldCount`
- 2024-12-20 `4bad77b`：`DrawCardCount`, `ExamAntiDebuff`, `RemainTurn`
- 2025-03-21 `4ba70d5`：`ExamAggressiveAdditive`, `ExamBlockRestriction`, `ExamConcentrationLessonMultipleAdditive`, `ExamEnthusiasticAdditive`, `ExamEnthusiasticMultiple`, `ExamFullPowerLessonMultipleAdditive`, `ExamFullPowerPointAdditive`, `ExamGrowEffectLessonAddAdditive`, `ExamLessonBuffAdditive`, `ExamLessonValueMultiple`, `ExamLessonValueMultipleDependReviewOrAggressive`, `ExamParameterBuffAdditive`, `ExamReviewAdditive`, `ExamReviewMultiple`, `StanceLock`
- 2026-03-31 `ff8795e`：`ExamReviewCountAdd`, `StanceLockConcentration`, `StanceLockFullPower`, `StanceLockPreservation`
- 2026-05-12 `c344b6e`：`ExamBuffConsumptionAdd`, `ExamBuffConsumptionDown`, `ExamParameterBuffTurnEndReduceLock`, `ExamReviewTurnEndReduceLock`

**`ExamPlayType`**：共 5 个值，初始之后新增 1 个。

- 2025-11-14 `4e3a93c`：`AutoPlayCompetition`

**`ExamStatusEffectType`**：共 6 个值，初始之后新增 6 个。

- 2025-11-14 `4e3a93c`：`Aggressive`, `FullPowerPoint`, `LessonBuff`, `ParameterBuff`, `ParameterBuffMultiplePerTurn`, `Review`

#### `ProduceEventCharacterType` / `ProduceLiveType` / `ProduceResourceType` / `ProducerLevelUnlockType` / `IdolCardLevelLimitEffectType`


**`ProduceEventCharacterType`**：共 15 个值，初始之后新增 14 个。

- 2025-03-21 `4ba70d5`：`AfterAuditionFinal`, `AfterAuditionMid1`, `AfterAuditionMid2`, `AfterStep1`, `AfterStep2`, `BeforeAuditionFinal`, `BeforeAuditionMid1`, `BeforeAuditionMid2`, `Ending`, `Failure`, `Opening`
- 2026-05-16 `f0dac51`：`AfterStepBeforeAuditionFinal`, `AfterStepBeforeAuditionMid1`, `AfterStepBeforeAuditionMid2`

**`ProduceLiveType`**：共 7 个值，初始之后新增 1 个。

- 2026-05-12 `c344b6e`：`E`

**`ProduceResourceType`**：共 6 个值，初始之后新增 1 个。

- 2026-05-16 `f0dac51`：`ProduceCustomizeItem`

**`ProducerLevelUnlockType`**：共 7 个值，初始之后新增 2 个。

- 2025-03-21 `4ba70d5`：`ProduceCardExcludeCount`
- 2025-12-26 `6edc27e`：`ProduceCardConversion`

**`IdolCardLevelLimitEffectType`**：共 5 个值，初始之后新增 1 个。

- 2026-05-16 `f0dac51`：`SecondProduceCardUpgrade`

#### B.1 小结：枚举增长的节律

| 日期 | commit | 版本/内容 | 新枚举值（试验内） |
|---|---|---|---|
| 2024-06～10 | 多个 | 每期新 SSR 偶像卡带 1～2 个新 `ExamLessonDepend*` / `Exam*Reduce` 效果 | `ExamBlockPerUseCardCount`, `ExamLessonDependParameterBuff`, `ExamLessonDependPlayCardCountSum`, … |
| 2024-10-25 | `4eeeeea`/`8f45f8b` | 1.5.0 前置：**アノマリー**（Plan3）+ **成長（GrowEffect）** | `ProducePlanType_Plan3`, 整个 `ProduceCardGrowEffectType`(38), `ExamAddGrowEffect`, `StanceLock`, `ExamStanceReset` |
| 2024-11-16 | `cda4882` | 1.5.0：アノマリー正式上线（強気/温存/全力 指針） | `ExamCostType_ExamFullPowerPoint`, `ProduceCardMovePositionType_Hold`, 8 个 `ExamStanceChange*` 相位, 9 个 `FullPower*/Preservation*/Concentration*` 触发条件, `ExamForcePlayCardSearch`, `ExamLessonFullPowerPoint` |
| 2024-12-20/26 | `4bad77b`/`cb5768d` | 1.6.1/1.7.0：**カスタマイズ**、**N.I.A**（Mid2 试验、Business、SelfLesson、FanPresent、VoteCount） | `ProduceType_NextIdolAudition`, `ProduceStepType_AuditionMid2/Business/SelfLesson*/FanPresent`, 10 个 `ProduceStepAuditionType_*Easy/Normal/Hard/VeryHard`, `ResultGradeType_ProduceVoteCount`, `ExamDescriptionType_Customize*`, `ProducePhaseType_StartCustomize` |
| 2025-03-21 | `4ba70d5` | 1.10.x：**のんびり（OverPreservation）**、熱意、プライド 等 17 个新效果（アノマリー扩展 + ハイスコア活动） | `ExamOverPreservation`, `ExamEnthusiastic*`, `Exam*Additive`, `ExamLessonValueMultipleDependReviewOrAggressive`, `ProduceHighScoreEventType_Rush` |
| 2025-04-21/22 | `a1d531d`/`3f61123` | 1.11.0：`*PerSearchCount` / `*AndSearchCount` 系（按区域卡数计数） | 12 个 |
| 2025-05-16/19 | `be4e3b4`/`676438a` | 2.0.0：**N.I.A マスター**、SSS/SSS+ 评级 | `ResultGrade_Sss/SssPlus`, `ProducePhaseType_EndPresent/EndShop/EndStepEventBusiness` |
| 2025-08-18/22 | `e55755f`/`0fdb17b` | 2.3.0：`ProduceStepBusinessType`，`ParameterBuffMultiplePerTurnUp` 触发条件 | |
| 2025-09-29 | `26f0628` | 2.4.0：プロデューサーランキング / シーズン制 | `ProducerRankingGrade_*` |
| 2025-10-21 | `d1637c4` | 2.5.0 前置：**コンバージョン**、`ProduceLegendProduceCard`/`ProduceInitialDeck` 表（空）、`ProduceSelectScreenOrderType` | |
| 2025-11-14 | `4e3a93c` | 2.6.0：**コンテスト改版（Competition）**、`ExamPlayType_AutoPlayCompetition`、`ExamStatusEffectType` | |
| 2025-12-26 | `6edc27e` | 2.7.0：**初・レジェンド**（`produce-006`）、`ProduceCardRarity_Legend`、`ProduceCardPositionType_NotLost`、`ExamPermanent*StatusEnchant`、SSSS 评级 | `ExamLessonDependBlockConsumptionSum`, `ProduceCardMoveEffectTriggerType_Hand` |
| 2026-02-19～03-31 | `374cf1a`/`8f2f3e2`/`ff8795e` | 2.9～2.10：`pickCountType`、`chainProduceExamEffectIds`、`ExamCostType_ExamParameterBuffMultiplePerTurn`（绝好调作为费用）、`ExamReviewCountAdd`、`ExamEnthusiasticTurnAdd`、Easy 模式 | |
| 2026-05-12/16 | `c344b6e`/`f0dac51` | 3.0.x：**H.I.F**（`ProduceType_HatsuboshiIdolFestival`，`ProduceSplitType_Selection/Final`，`OpenLesson*Star` 步骤，`ResultGradeType_ProduceStar`，SSSS+/SSSSS/SSSSS+）、**プリマステラ**、**成長パネル**、**ユニット**、`ExamStatusEnchantEncore`（再演）、`ExamForcePlayCardSearchWithCost`、`ExamBuffConsumption*` | |
| 2026-05-26～06-11 | `aba06dc`/`3d6c98c` | 3.0.3/3.1.0：`Exam*AdditiveFix` 5 个、`ExamAggressiveUpInterval` 相位、`ExamMoveGrowEffect`、`Exam*GetSum` | |
| 2026-07～09 | | 没有新的试验内枚举值；只有 `ProducePhaseType_BuyShopItemProduceCard`（07-31） | |

结论：**平均每 1～2 个月出现一批新的 `ProduceExamEffectType`（2 年内 +67）**，大版本一次加 10～20 个；触发相位 `ProduceExamPhaseType`（+18）和触发条件 `ProduceExamFieldStatusType`（+15）也在持续增长。任何把效果类型写死为 switch/enum 的引擎在每个大版本后都会遇到未知值。

### B.2 新表时间线

初始 dump 有 195 张表；之后新增 100 张、删除 9 张。与 produce 模拟相关的新增表（其余为 Photo/Gasha/Home/Tour/Gvg 等 UI 与活动表，列表见 `git log --diff-filter=A --name-only`）：

| 首次出现 | commit | 表 | 说明（字段来自 HEAD 样本） |
|---|---|---|---|
| 2024-07-19 | `87cc008` | `ProduceExamAutoCardSelectEvaluation` | 官方 AutoPlay 的「选卡奖励」权重（`examEffectType, remainingTerm, evaluationType, evaluation`），Vibbit 逆向的 AI 表之一 |
| 2024-08-29 | `5107190` | `ProduceChallengeCharacter`, `ProduceChallengeSlot`, `ProduceItemChallengeGroup` | 「チャレンジPアイテム」槽位：`ProduceChallengeSlot(produceId, number) → ProduceItemChallengeGroup(produceItemId, lessonLimitUpScore, auditionParameterGrowthRatePermil)`，マスター难度的附加规则 |
| 2024-10-25 | `4eeeeea` | `ProduceExamAutoGrowEffectEvaluation` | AutoPlay 对「成長」效果的权重（アノマリー前置） |
| 2024-12-20 | `4bad77b` | `ProduceCardCustomize`, `ProduceCardCustomizeRarityEvaluation` | **カスタマイズ**：`ProduceCard.produceCardCustomizeIds[]` → `ProduceCardCustomize(customizeCount, produceCardGrowEffectIds[], producePoint, overwriteProduceCardGrowEffectType)`；稀有度→评价值 |
| 2024-12-20 | `4bad77b` | `ProduceDescription*`（9 张）, `ProduceCharacter`, `ProduceCharacterAdv`, `ProduceStoryGroup`, `ProduceGroupLiveCommon`, `ProduceStepSelfLesson(+Motion)`, `ProduceStepAuditionCharacter`, `ProduceStepFanPresentMotion`, `ForceAppVersion`, `ProduceExamAutoPlayCardEvaluation` | 描述模板体系重构；N.I.A 的自习（`ProduceStepSelfLesson: progressLevel, stamina, parameter`）、ファンプレゼント、试验对手角色（`ProduceStepAuditionCharacter: successNextIdolAuditionRank/failureNextIdolAuditionRank`）；AutoPlay 每张卡的固定权重表 |
| 2025-04-21 | `264c0c7` | `ProduceGrade`, `ProduceGuide*`（4 张） | **评级阈值改为按 `produceGroupId`**（`ProduceGrade(produceGroupId, grade, threshold)`），取代全局 `ResultGradePattern`；新手推荐牌组 |
| 2025-05-16 | `be4e3b4` | `ProduceCardPool`, `ProduceNextIdolAuditionMasterRankingSeason`, `SupportCardProduceSkillFilter` | 随机卡池（`produceCardRatios[{id, upgradeCount, ratio}]`，供 `ExamCardCreateSearch`）；NIA マスター ランキング赛季 |
| 2025-08-18 | `e55755f` | `ResearchMemoryRerollCost` | リサーチ（メモリー再抽）费用表 |
| 2025-09-29 | `26f0628` | `ProduceSeason`, `ProduceSeasonZeroGrade`, `ProducerRanking*`（5 张）, `Badge` | プロデューサーランキング：赛季（`ProduceSeason: startTime/endTime/fixRankTime`，シーズン0 = 2024-05-16～2025-09-29）、季前旧评级阈值快照 |
| 2025-10-21 | `d1637c4` | `ProduceCardConversion`, `ProduceInitialDeck`, `ProduceLegendProduceCard` | **コンバージョン**（`beforeProduceCardId → afterProduceCardId`, `conditionSetId`=プロデューサーLv 条件）；每个剧本按 `examEffectType`（=プラン代表 buff）的初始牌组 id；**レジェンドカード**候选（`produceId, examEffectType, produceCardIds[]`，2025-12-26 才填入 6 行，2026-03 两次扩充） |
| 2025-11-14 | `4e3a93c` | `CompetitionSeason`, `CompetitionStageSectionLock`, `CompetitionExamStatusEffectIcon`, `ExamContestEmbedProduceCard`, `ProduceExamAutoPlayProduceCardEvaluation` | コンテスト改版（`CompetitionGrade__1..8`, `CompetitionStageType__1..3`）；コンテスト嵌入卡；AutoPlay 按卡的负权重（-100000 = 禁用） |
| 2026-05-12 | `c344b6e` | `IdolCardPrimaStellaProduceSkill`, `ProduceGrowthPanel`, `ProduceGrowthPanelSheet`, `ProduceCustomizeItem`, `ProduceCustomizeItemRelationship`, `ProduceCharacterUnit`, `ProduceLiveEvaluation`, `ProduceSplitAdv`, `ProduceStepOpenLesson(+Motion)`, `ProduceStepAuditionRivalActor(+Motion)`, `ProduceStepAuditionCharacterBgm`, `ProduceStepAuditionCharacterUnitMotion`, `ExamUnitMotion`, `ProduceDescriptionProduceType` | **3.0 / H.I.F 全套**：プリマステラ（偶像卡新一档解放 → 追加 `ProduceSkill`，`IdolCard.idolCardPrimaStellaProduceSkillId/secondProduceCardId/...`）；**成長パネル**（`ProduceGrowthPanel(level, produceGrowthPanelSheetId, produceEffectIds[], unlockItemQuantity)`，按 `ProduceType` 的永久成长树，50 格）；**カスタマイズPアイテム**（`ProduceCustomizeItem: isBase/isTerminal, produceExamTriggerId, produceExamEffectIds, examEffectTurn/Count` + 父子关系树）；ユニット（REVERSI = kllj+ssmk）；H.I.F 的公開レッスン（`ProduceStepOpenLesson: mainParameter, subParameter, star`）；试验对手（`RivalActor`）；`ProduceLiveEvaluation(produceId, characterId, liveType)` 决定结局 live 种类 |

删除的表：`CostumeGroup`(2025-01-09)、`ProduceDescription`/`ProduceDescriptionProduce{CardGrowEffect,Effect,ExamEffect,Plan}Type`（2025-01-20，被 `ProduceDescription*` 新体系取代）、`ProduceLiveCommon`（→`ProduceGroupLiveCommon`）、`GashaAnimation`、`PhotoLookEffectorCharacter`（2026-08-17）。

