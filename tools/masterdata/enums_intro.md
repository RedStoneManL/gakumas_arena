# 学マス master data 枚举全集（Master Data Enums）

> 数据源：`gakumasu-diff` dump（commit `{{COMMIT}}`）+ `penum.proto`（枚举定义全集，含 dump 中尚未使用的值）。
> 生成：`tools/masterdata/build_docs.py`（统计来自 `inspect_dump.py`；中文语义注释在 `atlas_annotations_more.py::ENUM_NOTES`）。
> 计数口径：值在整个 dump 中出现的次数（包含嵌套的 `produceDescriptions[]` 片段字段，因此 `ProduceExamEffectType_ExamLesson` 之类的计数远大于 ProduceExamEffect 的行数）。§2.1 另给出 **ProduceExamEffect 表内按 effectType 的行数**。
> 标记：**(dump 中无)** = proto 定义了但当前 dump 没有任何行使用；**(不在 proto 中)** = dump 里出现但 proto 未定义（通常是被枚举正则误判的 id 片段，如 `Convert_*`、`CardPlayAggressive_group_20`）。

## 0. 速查：实现考试引擎需要的枚举

| 枚举 | 用途 | 详解位置 |
|---|---|---|
| ProduceExamEffectType | 原子效果类型（ProduceExamEffect.effectType）；138 个定义值，dump 使用 107 个 | §2.1 |
| ProduceExamPhaseType | 触发时机（ProduceExamTrigger.phaseTypes） | §2.2 |
| ProduceExamFieldStatusType / ProduceExamTriggerCheckType | 场上状态条件 / 取反 | §2.2 |
| ProduceCardPositionType / ProduceCardOrderType / ProducePickRangeType / ProducePickCountType | 卡牌筛选与选取 | §3 |
| ProduceCardMovePositionType / ProduceCardMoveEffectTriggerType | 卡去向 / 移动时效果 | §3 |
| ExamCostType | 非体力费用 | §3 |
| ProduceCardGrowEffectType | 成长/定制效果 | §3 |
| ProduceEffectType / ProducePhaseType | 培育外循环效果与时机 | §2.3, §3 |
| ExamDescriptionType / ProduceDescriptionType | 描述模板片段 | §3 |
| ProduceExamAutoEvaluationType / ExamPlayType | 官方自动打牌权重 | §3 |
