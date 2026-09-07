# 学マス master data 图谱（Master Data Atlas）

> 数据源：datamined master DB 的 YAML dump（`vertesan/gakumasu-diff`，commit `{{COMMIT}}`，286 张表，每表一个文件、每文件一个 row dict 列表）。
> 字段类型来自 `pmaster.proto` / `pcommon.proto`（574 个 message，一表一 message），枚举全集来自 `penum.proto`。
> 生成方式：`python tools/masterdata/build_docs.py --cache md.pkl --proto-dir <proto> --out-dir docs/research`；数据统计由 `tools/masterdata/inspect_dump.py` 提供，中文注释在 `tools/masterdata/atlas_annotations*.py`。
> 姊妹文档：`master_data_enums.md`（全部枚举取值 + 效果类型逐值语义）。

## 0. 读前须知

### 0.1 dump 的物理形态与读取

- 每张表一个 `Table.yaml`，顶层是 list，每个元素是一行 dict；嵌套 list-of-dict（`produceDescriptions`、`playEffects`、`rewards`、`stages`…）就是 proto 里的 `repeated message`。
- 整个 dump 约 209 MB YAML（ProduceCard 38 MB、ProduceExamEffect 28 MB、ProduceExamStatusEnchant 25 MB、ProduceExamGimmickEffectGroup 21 MB、ProduceItem 16 MB）。**必须用 libyaml 的 `yaml.CSafeLoader`**（PyPI 的 PyYAML wheel 自带；Debian 的 python3-yaml 没有），全量解析约 2.5 分钟，之后请走 pickle/JSON 缓存。
- 两个文件不是合法 YAML：`Localization.yaml`（块标量 `|` 后紧跟 `\r` 与正文）和 `Rule.yaml`（含 `\x0b` 控制字符）。`inspect_dump.py` 里有修复回退；二者与模拟无关。
- 枚举值序列化为 `EnumName_Value` 字符串；`EnumName_Unknown`（proto 编号 0）是“未设置”，在筛选/统计时应视为空。
- 千分比字段以 `Permil` 结尾（1000 = 100%），万分比 `Permyriad`；时间是 Unix 毫秒的**字符串**（`"1715824800000"`，`"0"` = 无）。
- 主键：多数表是 `id`；`ProduceCard` 是 `(id, upgradeCount)`；`ProduceSkill` 是 `(id, level)`；`ProduceExamGimmickEffectGroup`、`ProduceCardPool/RandomPool`、`ProduceExamBattleNpcGroup`、`ProduceExamBattleScoreConfig`、`ConditionSet`、`ConsumptionSet`、`IdolCardLevelLimit`、`IdolCardPotential`、`ProduceGrowthPanel` 等是“同一 id 多行”的分组表（用 `number`/`priority`/`level`/`parameter` 区分）。
- **id 本身携带大量语义**（如 `e_effect-exam_lesson-0009-01` = ExamLesson v1=9 count=1；`p_trigger-end_lesson-lesson_dance-dance-0400_0000` = 舞蹈课结束且 Dance≥400）。`ProduceTrigger` 表甚至**只有 id + phaseType**，条件只存在于 id 里，实现时需要解析 id 或依赖描述文本。

### 0.2 描述文本是最好的文档

自 2025-01-20 起独立的 `ProduceDescription` 表被删除，描述以 `produceDescriptions[]`（`pcommon.ProduceDescriptionSegment`）内联在每一行上。片段的 `text` 已是渲染后的文本，顺序拼接即游戏内说明。§2 说明其结构与 `ProduceDescription*` 模板表的映射规则；`master_data_enums.md` §2.1 给出了每个 ProduceExamEffectType 的日文说明文与示例文本。

### 0.3 三层效果模型（实现引擎时的心智图）

```
培育外循环                                   考试内（レッスン/試験/コンテスト）
ProduceSkill / ProduceItem / ProduceCustomizeItem / 事件 / 成长面板
   └─ ProduceTrigger(时机) + ProduceEffect(原子效果)
         ├─ 三维/体力/P点/商店/卡牌操作/奖励
         └─ ExamStatusEnchant / ExamPermanent*StatusEnchant ──► ProduceExamStatusEnchant（持续效果）
                                                                    = ProduceExamTrigger(时机+条件) + ProduceExamEffect[]（原子效果）
ProduceCard.playProduceExamTriggerId（使用条件）
ProduceCard.playEffects[] ──► ProduceExamEffect（可各带 ProduceExamTrigger 附加条件）
ProduceCard.produceCardStatusEnchantId ──► ProduceCardStatusEnchant（成长：ProduceExamTrigger + ProduceCardGrowEffect[]）
ProduceDrink ──► ProduceDrinkEffect ──► ProduceExamEffect
试炼 gimmick ──► ProduceExamGimmickEffectGroup（startTurn + 条件 + ProduceExamEffect）
对象/条件计数统一用 ProduceCardSearch；效果分组用 EffectGroup。
```

### 0.4 已知空表 / 缺失

- 空表：`ProduceCardStatusEffect`、`ExamSimulation`、`ProduceCardSimulation(Group)`、`ProduceItemSimulation(Group)`、`IdolCardSimulation`、`SupportCardSimulation(Group)`、`ProduceExamAutoResourceEvaluation`、`TowerLayer*`、`CompetitionSeason` 等。
- `ProduceRewardSet` 引用的“奖励集合 → 候选卡/道具”表不在 dump 中（集合 id 只出现在 `ProduceEffect.id` 的 `p_rd-…` 片段里）。
- 课程/事件在周程中的出现概率、SP 课程基础概率、商店刷新规则等**流程参数不在 master 里**（在服务端逻辑），需从别处确认。
