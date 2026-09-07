"""Second half of the hand-written annotations (tables F-J) + per-value notes for key enums."""
from atlas_annotations import COMMON, NESTED, T, add  # noqa: F401

# =========================================================================== F. 偶像 / 角色 / 支援卡
add("IdolCard",
    "偶像卡（プロデュースアイドル，151）。培育起点：三维初始值 produceVocal/Dance/Visual、成长率 permil、体力、固有卡 produceCardId、固有道具 before/afterProduceItemId（+ 版）、"
    "流派 examEffectType、试炼难度组、初始卡组、潜能/上限/一番星 技能表。id 编码 `i_card-{chr}-{1R|2SR|3SSR}-{序号}`。",
    {"originalIdolCardSkinId": "→ IdolCardSkin 默认皮肤。", "anotherCostumeHeadId": "→ CostumeHead。", "anotherCostumeId": "→ Costume。",
     "idolCardPotentialId": "→ IdolCardPotential（潜能 4 段）。", "idolCardPotentialProduceSkillId": "→ IdolCardPotentialProduceSkill。",
     "idolCardLevelLimitId": "→ IdolCardLevelLimit（突破消耗）。", "idolCardLevelLimitProduceSkillId": "→ IdolCardLevelLimitProduceSkill（突破解锁技能）。",
     "maxIdolCardLevelLimitRank": "最大突破段（6 或 7）。", "additionalAnotherCostumeHeadIds": "额外服装。", "additionalAnotherCostumeIds": "额外服装。",
     "idolCardLevelLimitStatusUpId": "→ IdolCardLevelLimitStatusUp（突破加三维）。",
     "produceVocal": "初始 Vocal。", "produceDance": "初始 Dance。", "produceVisual": "初始 Visual。",
     "produceVocalGrowthRatePermil": "Vocal 成长率千分比（课程/试炼参数加成）。", "produceDanceGrowthRatePermil": "。", "produceVisualGrowthRatePermil": "。",
     "produceStamina": "初始最大体力。", "produceStepAuditionDifficultyId": "→ ProduceStepAuditionDifficulty 难度组。",
     "examInitialDeckId": "→ ExamInitialDeck（流派 2 张组：initial_deck-parameter_buff 等，用于表示卡的流派/教程）。",
     "beforeProduceItemId": "→ ProduceItem 固有道具。", "afterProduceItemId": "→ ProduceItem 固有道具+。",
     "produceChallengeSlotId": "→ ProduceChallengeSlot。", "showExamEffectType": "图鉴额外显示的流派（温存）。",
     "secondProduceCardId": "→ ProduceCard 第二固有卡（部分 SSR）。", "beforeLevelLimitProduceItemId": "未使用。", "afterLevelLimitProduceItemId": "未使用。",
     "primaStellaConsumptionSetId": "→ ConsumptionSet，プリマステラ 解放消耗。", "idolCardPrimaStellaProduceSkillId": "→ IdolCardPrimaStellaProduceSkill。", "primaStellaAchievementId": "→ Achievement。",
     "potentialRankVoiceAssetId": "语音。", "produceSelectVoiceAssetId": "语音。", "produceScheduleFrontVoiceGroupId": "→ VoiceGroup。", "produceScheduleBackVoiceGroupId": "未使用。",
     "useProduceCardVoiceAssetId": "语音。", "useSecondProduceCardVoiceAssetId": "语音。", "usePrimaStellaProduceCardVoiceAssetId": "语音。", "primaStellaVoiceAssetId": "语音。",
     "produceStoryIds": "→ ProduceStory 偶像卡剧情。", "achievementIds": "→ Achievement。"})
add("IdolCardLevelLimit", "突破(レベル上限解放)消耗：id=按稀有度/プラン/主属性的模板，每段 rank 一行 → ConsumptionSet。", {"rank": "IdolCardLevelLimitRank(_1.._7)。", "consumptionSetId": "→ ConsumptionSet。"})
add("IdolCardLevelLimitProduceSkill", "突破到 rank 时解锁/升级的 ProduceSkill(p_idol_skill)。", {"produceSkillLevel": "技能等级。", "rank": "突破段。"})
add("IdolCardLevelLimitStatusUp", "突破各段的效果：ProduceVoDaVi(+三维)/ProduceSkill/ProduceCardUpgrade(固有卡强化)/ProduceStamina/SecondProduceCardUpgrade。",
    {"rank": "突破段。", "effectTypes": "IdolCardLevelLimitEffectType。", "effectValue": "数值（体力+3 等）。", "produceVocal": "+Vocal。", "produceDance": "。", "produceVisual": "。", "isIllustrationChange": "换立绘。"})
add("IdolCardPotential", "潜能(ポテンシャル) 4 段：每段效果类型（ProduceSkill/InitialProduceItemChange/ProduceStamina/ProduceVoDaViGrowthRatePermil）、成长率加成、消耗碎片。",
    {"rank": "IdolCardPotentialRank。", "effectTypes": "IdolCardPotentialEffectType。", "effectValue": "体力等数值。", "produceVocalGrowthRatePermil": "成长率+。", "produceDanceGrowthRatePermil": "。", "produceVisualGrowthRatePermil": "。", "anotherCostumeProvide": "赠服装。", "consumptionPiece": "消耗碎片数。"})
add("IdolCardPotentialProduceSkill", "潜能段解锁的 ProduceSkill。", {"produceSkillLevel": "等级。", "rank": "潜能段。"})
add("IdolCardPrimaStellaProduceSkill", "プリマステラ（H.I.F 一番星称号）解放后获得的技能：培育开始时获得专属 Legend 卡（p_card-xx-ido-100_0xx）。")
add("IdolCardSimulation", "空表。")
add("Character", "角色（24，isPlayable 13 位可培育偶像 + NPC）。含服装、亲爱度任务组、真结局加成等引用。",
    {"lastName": "姓。", "firstName": "名。", "alphabetLastName": "罗马字姓。", "alphabetFirstName": "罗马字名。", "isPlayable": "可培育。", "personalityType": "CharacterPersonalityType。",
     "characterTrueEndBonusId": "→ CharacterTrueEndBonus。", "achievementIds": "→ Achievement。", "masterAchievementId": "→ Achievement。", "idolCardIds": "→ IdolCard。", "supportCardIds": "→ SupportCard。",
     "changeCostumeConditionSetId": "→ ConditionSet。", "normalCostumeHeadId": "服装。", "trainingCostumeHeadId": "。", "liveCostumeHeadId": "。", "normalCostumeId": "。", "trainingCostumeId": "。", "liveCostumeId": "。",
     "dearnessMissionGroupId": "→ MissionGroup。", "dearnessStoryUnlockItemId": "→ Item。", "produceCardIds": "→ ProduceCard（nasr 专属）。", "otherStoryIds": "→ Story。",
     "potentialRank1VoiceAssetId": "语音。", "potentialRank3VoiceAssetId": "语音。", "potentialRank4VoiceAssetId": "语音。", "useProduceCardVoiceAssetId": "语音。",
     "standingListPositionX": "UI。", "standingListPositionY": "UI。", "rosterDetailPositionX": "UI。", "rosterDetailPositionY": "UI。", "storyPositionX": "UI。", "storyPositionY": "UI。",
     "produceHighScorePositionX": "UI。", "produceHighScorePositionY": "UI。", "produceHighScoreRushPositionX": "UI。", "produceHighScoreRushPositionY": "UI。"})
add("CharacterDearnessLevel", "亲爱度等级表（每角色 1..37 级）：每级的培育条件、**获得的 ProduceSkill(p_dearness_skill) 及等级**、真结局目标等级标记。",
    {"dearnessLevel": "亲爱度等级。", "advAssetId": "剧情 ADV。", "storyId": "未使用。", "produceConditionDescription": "升级所需培育条件说明。",
     "produceConditionAchievementId": "→ Achievement。", "produceConditionAchievementThreshold": "成就阈值。", "produceSkills": "该级获得的技能列表。", "produceSkills.id": "→ ProduceSkill。", "produceSkills.level": "技能等级。",
     "rewards": "奖励。", "rewards.resourceType": "。", "rewards.resourceId": "。", "rewards.quantity": "。", "ignoreReport": "不出报告。", "itemUnlockConditionSetId": "→ ConditionSet。",
     "isStepThresholdLevel": "阶段门槛级。", "isTargetLevel": "真结局目标级（最終試験1位/FINALE優勝/一番星）。", "targetDescription": "目标说明。", "trueEndAchievementProduceType": "对应剧本系列。",
     "dearnessPointThreshold": "所需亲爱度点。", "storyGroupOrder": "排序。"})
add("CharacterTrueEndBonus", "真结局(トゥルーエンド)达成后的永久培育加成：按剧本系列给三维/成长率/体力。", {"produceVocal": "+Vocal。", "produceDance": "。", "produceVisual": "。", "produceVocalGrowthRatePermil": "成长率+。", "produceDanceGrowthRatePermil": "。", "produceVisualGrowthRatePermil": "。", "produceStamina": "+体力。"})
add("SupportCard", "支援卡（201）：type(Vocal/Dance/Visual/Assist)、プラン、稀有度、等级表、突破表、剧情、**课程中强化手牌概率 produceCardUpgradePermil**（レッスンサポート）。",
    {"characterIds": "登场角色。", "type": "SupportCardType。", "supportCardLevelId": "→ SupportCardLevel。", "supportCardLevelLimitId": "→ SupportCardLevelLimit。", "produceStoryIds": "→ ProduceStory。",
     "displayPositionX": "UI。", "displayPositionY": "UI。", "displayScale": "UI。", "exchangeReward.resourceType": "分解奖励。", "exchangeReward.resourceId": "。", "exchangeReward.quantity": "。",
     "produceCardUpgradePermil": "レッスンサポート 发生率千分比（每张卡基础值；技能 SupportCardProduceCardUpgradeProbabilityUp 叠加）。", "upgradeProduceCardSearchId": "→ ProduceCardSearch（手札）。",
     "produceCardUpgradeLessonParameterType": "只在该属性课程中发生。", "gashaSupportAnimationNumber": "抽卡演出。", "upgradeProduceCardProduceDescriptions": "サポート发生率描述（確率小/中/大）。"})
add("SupportCardBonus", "支援卡等级里程碑加成（rarity × level → bonusPermyriad，万分比）。", {"bonusPermyriad": "加成万分比。"})
add("SupportCardLevel", "支援卡经验表（3 种稀有度 × 等级 → totalExp）。", {"totalExp": "累计经验。"})
add("SupportCardLevelLimit", "支援卡突破段 → 等级上限。", {"rank": "SupportCardLevelLimitRank。", "levelLimit": "等级上限。"})
add("SupportCardProduceSkillLevelVocal", "Vocal 支援卡在各等级解锁/升级的 ProduceSkill(p_support_skill)：(supportCardId, produceSkillId, produceSkillLevel) 于 supportCardLevel 生效。", {"produceSkillLevel": "技能等级。", "supportCardLevel": "支援卡等级。"})
add("SupportCardProduceSkillLevelDance", "同上，Dance 支援卡。", {"produceSkillLevel": "技能等级。", "supportCardLevel": "支援卡等级。"})
add("SupportCardProduceSkillLevelVisual", "同上，Visual 支援卡。", {"produceSkillLevel": "技能等级。", "supportCardLevel": "支援卡等级。"})
add("SupportCardProduceSkillLevelAssist", "同上，Assist 支援卡。", {"produceSkillLevel": "技能等级。", "supportCardLevel": "支援卡等级。"})
add("SupportCardProduceSkillFilter", "支援卡技能筛选 UI 分类（title → ProduceEffectType 列表 + ProduceTrigger 列表）。", {"produceEffectTypes": "。", "produceTriggerIds": "→ ProduceTrigger。"})

# =========================================================================== G. 自动打牌评估
add("ProduceExamAutoEvaluation",
    "自动打牌(オート)的启发式权重表（11130 = 5 ExamPlayType × 6 流派 × 7 remainingTerm × 53 evaluationType）：对每个状态量 evaluationType 给出权重 evaluation，以及持续效果系数 examStatusEnchantCoefficientPermil。可作为我们 baseline agent 的价值函数参考。",
    {"type": "ExamPlayType（AutoPlay/AutoPlayCompetition/ManualPlayLesson/ManualPlayLessonHard/ManualPlayAudition）。", "remainingTerm": "剩余回合分档 1..7（7=7 回合以上）。", "evaluationType": "ProduceExamAutoEvaluationType。", "examStatusEnchantCoefficientPermil": "持续效果的折算系数。"})
add("ProduceExamAutoTriggerEvaluation", "自动打牌对持续效果触发器的估值系数（coefficientPermil）与预计触发次数(count)。", {"examStatusEnchantProduceExamTriggerId": "→ ProduceExamTrigger。", "coefficientPermil": "系数。", "count": "预计次数。"})
add("ProduceExamAutoPlayCardEvaluation", "特定卡在剩余回合分档下的固定评价（-100000=不要打，1000000=必打）。", {"remainingTerm": "剩余回合分档。"})
add("ProduceExamAutoPlayProduceCardEvaluation", "同上，按 ExamPlayType 区分。", {"type": "ExamPlayType。", "remainingTerm": "分档。"})
add("ProduceExamAutoCardSelectEvaluation", "アノマリー(強気/全力)下自动选卡系数（LessonCoefficient / FullPowerPointCoefficient / FullPowerPointValue2Coefficient）。", {"type": "ExamPlayType。", "remainingTerm": "分档。", "evaluationType": "ProduceExamAutoCardSelectEvaluationType。"})
add("ProduceExamAutoResourceEvaluation", "空表。")
add("ProduceExamAutoGrowEffectEvaluation", "アノマリー下各成长效果类型的估值。", {"type": "ExamPlayType。", "remainingTerm": "分档。", "growEffectType": "ProduceCardGrowEffectType。", "examStatusEnchantCoefficientPermil": "系数。"})

# =========================================================================== H. 描述模板系统
add("ProduceDescriptionExamEffect",
    "ProduceExamEffectType → 显示名(name)与说明标签的映射（88 种有 UI 名称的效果）：produceDescriptionLabelId=培育外说明，examProduceDescriptionLabelId=考试内说明（部分类型两者不同，如 集中 _Produce/_Exam）；"
    "mainBuffMinThresholds=主 buff 图标分级阈值（好調 [3,5]、集中/好印象/やる気/全力値 [5,10]）；noIcon/noReference=不显示图标/不可点击引用。",
    {"type": "ProduceExamEffectType。", "produceDescriptionSwapId": "→ ProduceDescriptionSwap（レッスン/試験 用词替换）。", "produceDescriptionLabelId": "→ ProduceDescriptionLabel。", "examProduceDescriptionLabelId": "→ ProduceDescriptionLabel。", "mainBuffMinThresholds": "图标分级阈值。", "noIcon": "无图标。", "noReference": "不可引用。"})
add("ProduceDescriptionLabel",
    "术语/标签字典（226）：Label_*（效果/概念名 + 其说明片段）、Description_*（可复用的描述片段，如 Description_ProduceCardIsInitial）、Convert_*（受场景替换的词，如 レッスン↔試験・ステージ）。produceDescriptions 是该术语的说明文本（本身也是片段列表，可嵌套引用其他 Label）。",
    {"iconAssetId": "图标（style-dot=项目符号）。"})
add("ProduceDescriptionSwap", "场景替换词表：id × swapType(Lesson/Audition) → text。例如 Swap_Label_ExamLesson: Lesson=パラメータ / Audition=スコア；Swap_Convert_002: レッスン / 試験・ステージ。", {"swapType": "ProduceDescriptionSwapType。", "text": "替换后文本。"})
add("ProduceDescriptionProduceCardGrowEffect", "ProduceCardGrowEffectType → 名称、说明标签、定制界面短文案（例：LessonAdd → パラメータ値増加 / パラメータ+）。", {"type": "ProduceCardGrowEffectType。", "noIcon": "。", "noReference": "。", "produceCardCustomizeDescription": "定制界面短文案。"})
add("ProduceDescriptionProduceCardMovePosition", "ProduceCardMovePositionType → 位置名标签（山札の一番上 / 手札 / 除外…），Lost 额外有卡面用标签 レッスン中1回。", {"type": "ProduceCardMovePositionType。", "produceCardProduceDescriptionLabelId": "卡面用标签。"})
add("ProduceDescriptionProduceEffect", "ProduceEffectType → 显示名（92），少数带说明标签。", {"type": "ProduceEffectType。"})
add("ProduceDescriptionProducePlan", "ProducePlanType → 名称/标签（共通、【センス専用】…）。", {"type": "ProducePlanType。", "planDetailProduceDescriptionLabelId": "详细说明标签。"})
add("ProduceDescriptionProduceStep", "ProduceStepType → 名称标签（学園活動、プレゼント）。", {"type": "ProduceStepType。"})
add("ProduceDescriptionProduceType", "ProduceType × ProduceSplitType → 专用标记文本模板（{Label_ProduceType_...}）。", {"template": "模板串。"})

# =========================================================================== I. 通用
add("ConditionSet",
    "通用条件集（5084 行 / 3725 个 id）：同一 id 多行按 number 排序，用 conditionOperatorType(And/Or) 组合；conditionType 决定 resourceId1/2 与 min/max 的含义（DearnessLevel / ProducerLevel / MainTaskCompleted / TimeTerm / ItemCount…）。培育相关：剧本解锁、卡牌转换、チャレンジ 角色解锁。",
    {"conditionOperatorType": "And/Or。", "conditionType": "ConditionType。", "resourceId1": "条件对象 1（多态，如 characterId/main task id）。", "resourceId2": "条件对象 2。",
     "minMaxType": "ConditionMinMaxType（Min/Max/MinMax/Unknown）。", "min": "下限（字符串）。", "max": "上限。", "beforeTime": "时间上界(ms)。", "afterTime": "时间下界(ms)。"})
add("ConsumptionSet", "消耗集（突破/プリマステラ 等）：id 多行 → resourceType/resourceId/quantity。")

# =========================================================================== J. 其他相关（备注级）
add("PvpRateConfig", "コンテスト(PvpRate) 赛季配置：三维基准、评分曲线、3 个 stage（回合数、P道具、gimmick 组）。复用考试引擎（AutoPlayCompetition）。", {"stages": "阶段列表。"})
add("Tower", "（备注）“アイドルへの道”塔模式表头；TowerLayer/TowerLayerExam/TowerLayerRank 为空表，塔层数据不在 dump 中（ProduceItem 的 pitem_tower_* 与 ProduceExamStatusEnchant tower* 是其道具）。")
add("CompetitionExamStatusEffectIcon", "コンテスト状态图标顺序（planType × ExamStatusEffectType）。")
add("ProduceGuide", "（备注）新手推荐卡组指南（偶像卡 × P等级 → 分类组）。")
add("MemoryAbility", T["MemoryAbility"]["desc"], T["MemoryAbility"]["fields"])

# =========================================================================== enum per-value notes (Chinese)
ENUM_NOTES = {}


def en(family, mapping):
    ENUM_NOTES[family] = mapping


en("ProduceExamEffectType", {
    "Unknown": "占位/未指定。",
    "ExamLesson": "パラメータ/スコア +v1，effectCount 次（“パラメータ+9（2回）”）。受 好調/集中/強気/全力/熱意 等倍率修正。",
    "ExamParameterBuff": "好調 +effectTurn 回合（参数 ×1.5，ExamSetting.examParameterBuffPermil）。",
    "ExamBlock": "元気 +v1（受 やる気 加成、不安/弱気 减成）。",
    "ExamCardDraw": "抽 v1 张牌。",
    "ExamStaminaConsumptionDown": "消費体力減少 状态 effectTurn 回合（×50%）。",
    "ExamCardCreateId": "生成指定卡 targetProduceCardId（targetUpgradeCount 段）pickCount 张到 movePositionType；レッスン結束后删除。",
    "ExamStaminaReduceFix": "体力消費 v1（无视元気直接扣体力）。",
    "ExamLessonBuff": "集中 +v1（每点使 パラメータ +1）。",
    "ExamCardUpgrade": "レッスン中強化：把筛选到的卡临时升级（pickRange/pickCount）。",
    "ExamPlayableValueAdd": "スキルカード使用数追加 +effectCount（本回合额外出牌次数）。",
    "ExamLessonBuffMultiple": "集中強化：集中带来的参数增量 ×(1+v1‰)，effectTurn 回合。",
    "ExamCardStaminaConsumptionChange": "（proto/描述表定义，dump 无行）改变某卡消耗体力。",
    "ExamBlockRestriction": "元気増加無効 effectTurn 回合。",
    "ExamStatusEnchant": "挂载持续效果 produceExamStatusEnchantId，持续 effectTurn(-1=整场)，最多 effectCount 次；本身无数值。",
    "ExamCardStaminaConsumptionDownSpecify": "（定义，dump 无行）指定卡消耗降低。",
    "ExamStaminaDamage": "体力減少 v1（试炼 gimmick 用，元気可抵挡）。",
    "ExamStaminaRecoverFix": "体力回復 v1。",
    "ExamLessonFix": "固定パラメータ +v1（不受强化/低下状态影响）。",
    "ExamCardDuplicate": "複製：把筛选/选择的卡复制到 movePositionType。",
    "ExamReview": "好印象 +v1（回合结束按好印象值加参数，回合开始 -1）。",
    "ExamCardSearchEffectPlayCountBuff": "スキルカード追加発動：下 effectCount 张符合筛选的卡效果再发动 v1 次，effectTurn 回合内。",
    "ExamLessonValueMultiple": "パラメータ上昇量増加 +v1‰（含好印象带来的上升），effectTurn 回合。",
    "ExamCardPlayAggressive": "やる気 +v1（每点使 元気增量 +1）。",
    "ExamConcentration": "指針→強気（v1=段数 1/2）。",
    "ExamPreservation": "指針→温存（v1=段数）。",
    "ExamFullPower": "指針→全力。",
    "ExamStanceReset": "指針解除（解除温存/強気）。",
    "ExamFullPowerPoint": "全力値 +v1（回合末 ≥10 则下回合开始消费 10 进入全力）。",
    "ExamFullPowerPointReduce": "全力値 -v1。",
    "ExamSearchPlayCardStaminaConsumptionChange": "使用的符合筛选的卡消耗体力改为 0，effectCount 次，effectTurn(-1)。",
    "ExamUplifting": "高揚（定义，dump 无行）：回合末按高揚值加元気。",
    "ExamExtraTurn": "ターン追加 +1。",
    "ExamAntiDebuff": "低下状態無効 effectCount 次。",
    "ExamStaminaConsumptionAdd": "消費体力増加 effectTurn 回合（+100%）。",
    "ExamBlockAddDown": "不安 effectTurn 回合（元気获得 -33%）。",
    "ExamBlockAddDownRestriction": "不安無効（定义，无行）。",
    "ExamStaminaRecoverAdd": "体力回復効果増加（定义，无行）。",
    "ExamStaminaReduceChange": "体力消費軽減（定义，无行）。",
    "ExamPanic": "気まぐれ effectTurn 回合：手牌消耗体力随机（候选 ExamSetting.produceExamPanicStaminaCandidates）。",
    "ExamLessonChangeSpecifyLessThan": "パラメータ上昇値変更（定义，无行）。",
    "ExamHandHold": "手札持ち越し（定义，无行）。",
    "ExamStaminaConsumptionAddFix": "消費体力追加 +v1（固定值），effectTurn(-1)。",
    "ExamStaminaConsumptionAddDown": "（定义，无行）。",
    "ExamStaminaRecoverRestriction": "体力回復無効，effectTurn。",
    "ExamStaminaConsumptionDownAdd": "（定义，无行）。",
    "ExamGetCardUpgrade": "生成強化（定义，无行）。",
    "ExamStaminaConsumptionDownFix": "消費体力削減 -v1（固定值），effectTurn(-1)。",
    "ExamHandGraveCountCardDraw": "手札をすべて入れ替える（弃全部手牌并抽同数）。",
    "ExamEffectTimer": "発動予約：v1 回合后（effectCount 次）发动 chainProduceExamEffectId(s)。“次のターン、…”。",
    "ExamGimmickLessonDebuff": "緊張 v1（每点参数 -1），effectTurn。",
    "ExamGimmickParameterDebuff": "不調 effectTurn 回合（参数 ×2/3）。",
    "ExamGimmickSleepy": "弱気 v1（每点元気获得 -1）。",
    "ExamGimmickEnthusiastic": "熱意（定义，直接行为 0；通过温存解除等产生）：每点参数 +1，回合末清零。",
    "ExamGimmickPlayCardLimit": "使用不可：筛选到的卡 effectTurn 回合不可用。",
    "ExamGimmickSlump": "スランプ effectTurn 回合：参数不上升。",
    "ExamGimmickStartTurnCardDrawDown": "手札減少 v1（回合开始少抽 v1 张），effectTurn。",
    "ExamBlockFix": "固定元気 +v1（不受 buff/debuff 影响）。",
    "ExamLessonChangeSpecifyMoreThan": "うわの空（定义，无行）。",
    "ExamParameterBuffMultiplePerTurn": "絶好調 effectTurn 回合：好調的加成按好調剩余回合每回合 +10%。",
    "StanceLock": "指針固定 effectTurn 回合（不能变更指針与段数）。",
    "ExamDebuffRecover": "低下状態回復 v1 个（0=全部）。",
    "ExamReviewReduce": "好印象 -v1。", "ExamAggressiveReduce": "やる気 -v1。", "ExamLessonBuffReduce": "集中 -v1。", "ExamParameterBuffReduce": "好調 -v1 回合。",
    "ExamLessonValueMultipleDown": "パラメータ上昇量減少 v1‰，effectTurn。",
    "ExamAddGrowEffect": "成長：对筛选到的卡（pickRange All）附加 produceCardGrowEffectIds（レッスン終了まで）。",
    "ExamOverPreservation": "指針→のんびり（温存 3 段）。",
    "ExamEnthusiasticAdditive": "熱意追加 +v1（固定值），effectTurn(-1)。",
    "ExamEnthusiasticMultiple": "熱意増加 +v1‰。",
    "ExamFullPowerLessonMultipleAdditive": "全力強化：全力倍率再 +v1‰，effectTurn。",
    "ExamConcentrationLessonMultipleAdditive": "強気強化：強気倍率再 +v1‰。",
    "ExamLessonBuffAdditive": "集中増加量増加 +v1‰，effectTurn。", "ExamParameterBuffAdditive": "好調増加量増加 +v1‰。", "ExamAggressiveAdditive": "やる気増加量増加 +v1‰。", "ExamReviewAdditive": "好印象増加量増加 +v1‰。", "ExamFullPowerPointAdditive": "全力値増加量増加 +v1‰。",
    "ExamGrowEffectLessonAddAdditive": "（定义，无行）。",
    "ExamParameterBuffMultiplePerTurnReduce": "絶好調 -v1。",
    "ExamLessonValueMultipleDependReviewOrAggressive": "プライド effectTurn 回合：min(好印象,やる気)×2%（上限 50%）参数加成。",
    "ExamReviewMultiple": "好印象強化 +v1‰（好印象带来的参数上升倍率），effectTurn。",
    "ExamReviewCountAdd": "好印象追加発動 +v1（回合末好印象结算次数），effectTurn。",
    "ExamParameterBuffAdditiveFix": "好調増加量追加 +v1（固定）（定义，无行）。", "ExamLessonBuffAdditiveFix": "集中増加量追加 +v1（固定），effectTurn。", "ExamAggressiveAdditiveFix": "やる気増加量追加 +v1。", "ExamReviewAdditiveFix": "（定义，无行）。", "ExamFullPowerPointAdditiveFix": "（定义，无行）。",
    "ExamStatusEnchantEncore": "再演：挂载 produceExamStatusEnchantId，条件满足时再次使用自身（不付费用），effectCount 次、每回合 1 次；isOncePlayEffect。",
    # types without ProduceDescriptionExamEffect row
    "ExamAggressiveValueMultiple": "やる気 ×(1+v1‰)（“やる気1.3倍”）。",
    "ExamAggressivePerSearchCount": "按筛选卡数每 v2 张 やる気+…（dump 1 行）。",
    "ExamAggressiveDependReview": "按好印象比例增加やる気（dump 1 行）。",
    "ExamBlockAddMultipleAggressive": "元気 +v1，其中やる気加成按 v2‰ 倍率适用（“やる気効果を1.4倍適用”）。",
    "ExamBlockDependBlockConsumptionSum": "本场消耗元気总量 ×v1‰ 的元気。",
    "ExamBlockDependExamReview": "好印象 ×v1‰ 的元気。",
    "ExamBlockDown": "元気 -v1‰（百分比削减）。",
    "ExamBlockPerUseCardCount": "元気 +v1，本场每用 1 张卡 元気增量 +v2。",
    "ExamBlockPerSearchCount": "按筛选卡数增加元気（1 行）。",
    "ExamBlockValueMultiple": "元気 ×(1+v1‰)。",
    "ExamCardCreateSearch": "生成 pickCount 张来自 produceCardSearch（随机池）的卡到 movePositionType；pickCountType=Shortage 时补足到 N 张。",
    "ExamCardMove": "移动筛选/选择的卡到 movePositionType（手札/山札/捨札/除外/保留）。",
    "ExamForcePlayCardSearch": "无视费用直接使用筛选到的卡。", "ExamForcePlayCardSearchWithCost": "选择一张卡付费使用。",
    "ExamItemFireLimitAdd": "偶像固有 P道具 发动次数 +v1。",
    "ExamLessonAddMultipleLessonBuff": "集中 ×(1+v1‰)（“集中1.2倍”）。",
    "ExamLessonAddMultipleParameterBuff": "パラメータ +v1，其中好調加成按 v2‰ 倍率（“好調効果を2倍適用”）。",
    "ExamLessonBuffDependParameterBuff": "好調回合数 ×v1‰ 的集中（v2 存在时同时把集中减半等）。",
    "ExamLessonBuffPerSearchCount": "筛选卡数每 v2‰⁻¹ 张 集中+1（“除外2枚につき集中+1”）。",
    "ExamLessonDependBlock": "元気 ×v1‰ 的パラメータ（v2 为附加倍率）。",
    "ExamLessonDependBlockAndSearchCount": "筛选卡每张 元気×v2‰ 的パラメータ。",
    "ExamLessonDependBlockConsumptionSum": "本场消耗元気总量 ×v1‰ 的パラメータ。",
    "ExamLessonDependExamCardPlayAggressive": "やる気 ×v1‰ 的パラメータ。",
    "ExamLessonDependExamReview": "好印象 ×v1‰ 的パラメータ。",
    "ExamLessonDependParameterBuff": "好調回合数 ×v1‰ 的パラメータ。",
    "ExamLessonDependPlayCardCountSum": "パラメータ +v1，本场每用 1 张卡再 +v2。",
    "ExamLessonDependStamina": "当前体力 ×v1‰ 的パラメータ。",
    "ExamLessonDependStaminaConsumptionSum": "本场消耗体力总量 ×v1‰ 的パラメータ。",
    "ExamLessonDependAggressiveAndSearchCount": "筛选卡每张 やる気×v2‰ 的パラメータ。", "ExamLessonDependReviewAndSearchCount": "筛选卡每张 好印象×v2‰ 的パラメータ。", "ExamLessonDependEnthusiasticGetSum": "本场累计熱意 比例的パラメータ（1 行）。",
    "ExamLessonFullPowerPoint": "パラメータ +v1（累计全力値 ×v2‰ 追加），effectCount 次。",
    "ExamLessonPerSearchCount": "パラメータ +v1，按筛选卡数每张 +v2‰（未被引用）。",
    "ExamMultipleLessonBuffLesson": "パラメータ +v1，集中效果按 v2‰ 倍率适用。", "ExamMultipleEnthusiasticLesson": "パラメータ +v1，熱意效果 ×v2‰。", "ExamMultipleConcentrationLesson": "強気效果倍率适用（1 行）。", "ExamMultipleFullPowerLesson": "全力效果倍率适用（1 行）。",
    "ExamParameterBuffDependLessonBuff": "集中 ×v1‰ 的好調回合（v2 存在时集中减半）。", "ExamParameterBuffPerSearchCount": "按筛选卡数加好調（1 行）。",
    "ExamReviewDependExamBlock": "元気 ×v1‰ 的好印象。", "ExamReviewDependExamCardPlayAggressive": "やる気 ×v1‰ 的好印象。", "ExamReviewPerSearchCount": "筛选卡每张 好印象 +v2‰⁻¹。", "ExamReviewValueMultiple": "好印象 ×(1+v1‰)。",
    "ExamStaminaRecoverMultiple": "最大体力 ×v1‰ 回复。", "ExamStaminaReduce": "最大体力 ×v1‰ 消耗（可为负=回复）。",
    "ExamMoveGrowEffect": "移动成长效果（1 行）。", "ExamGimmickTiredFix": "疲労（仅描述表）。", "ExamPlayableValueHold": "使用回数持ち越し（仅描述表）。", "ExamStaminaThresholdAddRestriction": "消費体力増加無効（仅描述表）。",
    "ExamSearchPlayCardValueBuff": "カード効果増加（仅描述表）。", "ExamEnthusiasticTurnAdd": "熱意回合延长（1 行）。", "ExamFullPowerPointPerSearchCount": "按筛选卡数加全力値（1 行）。", "ExamFullPowerPointDependFullPowerPointGetSum": "按累计全力値加全力値（1 行）。",
    "ExamStaminaReduceChange": "体力消費軽減。", "ExamBlockAddDownRestriction": "不安無効。", "ExamCardStaminaConsumptionChange": "消費体力変化。",
})

en("ProduceExamPhaseType", {
    "None": "无时机，纯条件（用于 playProduceExamTriggerId 使用条件、GrowEffect 的条件）。",
    "ExamStartExam": "レッスン/試験 开始时。", "StartExamPlay": "レッスン開始後（首回合发牌后）。",
    "ExamStartTurn": "ターン開始時（发牌前）。", "StartPlay": "ターン開始後（发牌后、可出牌时）。", "ExamEndTurn": "ターン終了時。",
    "ExamEndTurnInterval": "每 N 回合的回合结束时（phaseValue=N）。", "ExamTurnInterval": "每 N 回合（回合开始）。", "ExamTurnTimer": "第 N 回合开始时（phaseValue=N；用于 ExamEffectTimer 延迟）。",
    "ExamTurnSkip": "ターンスキップ時。",
    "ExamCardPlay": "スキルカード使用時（结算前；配合 produceCardSearch=playing 表示“使用的是 X 卡”）。", "ExamCardPlayAfter": "スキルカード使用後（结算后）。", "ExamSearchCardPlay": "使用符合筛选的卡时（2 行，描述未定义）。",
    "ExamPlayCountInterval": "每使用 N 张卡时。", "ExamPlayCountIntervalAfter": "使用后每 N 张。", "ExamPlayTurnCountInterval": "回合内每使用 N 张（筛选）卡。",
    "ExamBuffConsume": "スキルカードコストで強化状態を消費した時（好調/集中等作费用）。",
    "ExamStatusChange": "直接効果で X が N 以上増加後（effectTypes+phaseValue）。", "ExamAggressiveUpInterval": "直接効果でやる気が N 回増加時。",
    "ExamStaminaReduce": "直接効果で体力が減少した時。", "ExamStaminaReduceCard": "スキルカードコストで体力減少時。",
    "ExamCardMoveGrave": "（自身）捨札に移動した時。", "ExamCardMoveHand": "手札に移動した時。", "ExamCardMoveLost": "除外に移動した時。",
    "ExamStanceChangeConcentration": "直接効果で強気になった時（phaseValue=段）。", "ExamStanceChangePreservation": "温存になった時。", "ExamStanceChangeFullPower": "全力になった時。",
    "ExamStanceChangeFromConcentration": "強気を解除後。", "ExamStanceChangeFromFullPower": "全力を解除後。", "ExamStanceChangeCountInterval": "直接効果で指針を N 回変更するたび。",
})
en("ProduceExamFieldStatusType", {
    "Unknown": "无条件。", "BlockUp": "元気 ≥ v。", "NoBlock": "元気 = 0。", "LessonBuffUp": "集中 ≥ v。", "ReviewUp": "好印象 ≥ v。", "CardPlayAggressiveUp": "やる気 ≥ v。",
    "ParameterBuff": "好調状態（Not=非好調）。", "ParameterBuffUp": "好調残り ≥ v ターン。", "ParameterBuffMultiplePerTurnUp": "絶好調 ≥ v。", "StaminaConsumptionDown": "消費体力減少状態。",
    "StaminaUpMultiple": "体力 ≥ v‰ 最大体力。", "StaminaLessMultiple": "体力 ≤ v‰。", "RemainingTurn": "残り ≤ v ターン。", "TurnProgressUp": "第 v+1 回合以后。",
    "ConditionThresholdMultiple": "レッスンCLEAR 条件的 v‰ 以上（試験：スコア ≥ v）。", "ConditionThresholdMultipleDown": "CLEAR 的 v‰ 以下。",
    "CardSearchCountUp": "fieldStatusProduceCardSearchIds 命中的卡 ≥ v 张。", "PlayCardLesson": "直前使用的是アクティブ卡。", "PlayCardSkill": "直前使用的是メンタル卡。",
    "ConcentrationUp": "強気（v=段）。", "PreservationUp": "温存（v=段）。", "FullPowerUp": "全力。", "NoStance": "无指針（Not=いずれかの指針）。",
    "ConcentrationChangeCountUp": "強気になった回数 ≥ v。", "PreservationChangeCountUp": "温存になった回数 ≥ v。", "FullPowerChangeCountUp": "全力になった回数 ≥ v。", "StanceChangeCountUp": "指針変更回数 ≥ v。",
    "FullPowerPointUp": "全力値 ≥ v。", "FullPowerPointGetSumUp": "本场累计全力値 ≥ v。",
})
en("ProducePhaseType", {
    "ProduceStart": "培育开始时（-initial 变体用于“初期…”，-no_description 无文案）。", "StartLesson": "课程开始时（lesson/lesson_sp/lesson_hard/按属性）。", "EndLesson": "课程结束时（含 CLEAR 后奖励前）。", "EndLessonBeforePresent": "课程结束、领取奖励前（P点获得量加成）。",
    "StartAudition": "试炼开始时。", "StartAuditionMid1": "1 次试炼开始。", "StartAuditionMid2": "2 次。", "StartAuditionFinal": "最終试炼开始。", "EndAudition": "试炼结束。", "EndBeforeAuditionRefresh": "试炼前自动回复结束时（= 试炼开始前）。",
    "StartShop": "相談 选择时。", "EndShop": "相談 结束。", "BuyShopItemProduceCard": "相談交换卡后。", "BuyShopItemProduceDrink": "相談交换饮料后。",
    "StartPresent": "活動支給・差し入れ 选择时。", "EndPresent": "同结束。", "StartRefresh": "休む 选择时。", "StartCustomize": "特別指導 开始。",
    "EndStepEventActivity": "お出かけ 结束。", "EndStepEventSchool": "授業・営業 结束。", "EndStepEventBusiness": "营业结束（按营业种类）。",
    "GetProduceCard": "获得卡时（筛选：类别/effectGroup）。", "GetProduceDrink": "获得饮料时。", "GetProduceItem": "获得道具时。", "UpgradeProduceCard": "强化卡时。", "DeleteProduceCard": "删除卡时。", "ChangeProduceCard": "チェンジ 时。", "CustomizeProduceCard": "定制卡时。",
    "Unknown": "p_trigger-none-stamina_ratio-… 纯条件。",
})
en("ProduceCardGrowEffectType", {
    "LessonAdd": "パラメータ値 +v。", "LessonReduce": "-v。", "LessonCountAdd": "パラメータ上昇回数 +v。", "LessonCountReduce": "-v。", "BlockAdd": "元気値 +v。", "BlockReduce": "-v。",
    "CostAdd": "体力コスト +v。", "CostReduce": "-v。", "CostPenetrateAdd": "体力消費(无视元気)コスト +v。", "CostPenetrateReduce": "-v。",
    "CostBuffAdd/Reduce": "强化状态费用 ±（未使用）。", "CostLessonBuffAdd": "集中コスト +v。", "CostLessonBuffReduce": "-v。", "CostReviewAdd": "好印象コスト +v。", "CostReviewReduce": "-v。", "CostAggressiveAdd": "やる気コスト +v。", "CostAggressiveReduce": "-v。", "CostParameterBuffAdd": "好調コスト +v。", "CostParameterBuffReduce": "-v。", "CostFullPowerPointAdd": "全力値コスト +v。", "CostFullPowerPointReduce": "-v。", "CostParameterBuffMultiplePerTurnReduce": "絶好調コスト -v。",
    "ParameterBuffTurnAdd": "好調回合 +v。", "LessonBuffAdd": "集中 +v。", "ReviewAdd": "好印象 +v。", "AggressiveAdd": "やる気 +v。", "FullPowerPointAdd": "全力値 +v。", "FullPowerPointReduce": "-v。", "ParameterBuffMultiplePerTurnAdd": "絶好調 +v。",
    "StaminaConsumptionDownTurnAdd": "消費体力減少 回合 +v。", "LessonDependBlockAdd": "元気分パラメータ倍率 +v‰。", "LessonDependExamCardPlayAggressiveAdd": "やる気分 +v‰。", "LessonDependExamReviewAdd": "好印象分 +v‰。",
    "EffectAdd": "追加效果 playProduceExamEffectId。", "EffectChange": "把 targetPlayProduceExamEffectIds 替换为 playProduceExamEffectId。", "EffectDelete": "删除效果（未使用）。", "CardStatusEnchantChange": "替换成长规则。",
    "PlayTriggerChange": "替换使用条件。", "PlayEffectTriggerChange": "替换效果条件。", "PlayMovePositionTypeChange": "用后去向改为 playMovePositionType。", "InitialAdd": "开始时入手牌。",
})
en("ExamCostType", {"Unknown": "无非体力费用（普通体力费用看 stamina/forceStamina）。", "ExamParameterBuff": "消费好調 costValue 回合。", "ExamLessonBuff": "消费集中。", "ExamReview": "消费好印象。", "ExamCardPlayAggressive": "消费やる気。", "ExamFullPowerPoint": "消费全力値。", "ExamParameterBuffMultiplePerTurn": "消费絶好調。"})
en("ProduceCardMovePositionType", {"Unknown": "不适用。", "Grave": "捨札。", "Lost": "除外（レッスン中1回）。", "Hand": "手札。", "Hold": "保留（全力用，上限 holdLimit=2）。", "DeckFirst": "山札の一番上。", "DeckLast": "一番下。", "DeckRandom": "山札のランダムな位置。"})
en("ProduceCardMoveEffectTriggerType", {"Unknown": "无移动时效果。", "Hand": "移动到手札时发动 moveProduceExamEffectIds。", "Hold": "移动到保留时发动。"})
en("ProduceCardPositionType", {"Deck": "山札。", "DeckAll": "所有卡（山札+手札+捨札…，即“持有的卡”）。", "DeckGrave": "山札か捨札。", "Hand": "手札。", "Hold": "保留。", "Lost": "除外。", "NotLost": "除外以外。", "Playing": "正在使用的卡。", "Target": "效果的目标卡（用于 trigger 的 lowerSearchCount 判定）。", "RandomPool": "随机池（生成卡）。"})
en("ExamDescriptionType", {
    "Unknown": "非数值槽片段。", "CustomizeEffectValue1": "填 effectValue1。", "CustomizeEffectValue2": "填 effectValue2。", "CustomizeEffectValuePercent1": "effectValue1 以 % 显示（‰/10）。", "CustomizeEffectValuePercent2": "同 v2。",
    "CustomizeTurn": "填 turn。", "CustomizeEffectCount": "填 effectCount。", "CustomizeCostValue": "填 costValue。", "CustomizeLessonCountAdd": "引用 Description_LessonCountAdd_CountSection（“（N回）”）。",
    "CustomizeInitialAdd": "引用 Description_ProduceCardIsInitial（开始时入手牌）。", "CustomizePlayMovePositionLost": "卡面末尾“レッスン中1回”槽。", "CustomizeEffectAdd": "定制追加效果的插入点。",
    "ExamValue": "Label 模板里运行时填的值。", "ExamValue2": "同 v2。", "ExamTurn": "运行时回合数。", "ExamCount": "运行时次数。", "ExamTurnTimer": "发动预约回合。", "ExamProduceCardSearch": "运行时填筛选器描述。", "ExamProduceExamEffect": "运行时填子效果描述（exam_template）。",
})
en("ProduceDescriptionType", {"PlainText": "纯文本（空=换行）。", "Exam": "数值槽（见 ExamDescriptionType）。", "ProduceExamEffectType": "效果名标签（可点击）。", "ProduceCardGrowEffectType": "成长效果名标签。", "ProduceCardCategory": "卡类别标签。", "ProduceCard": "卡名（targetId=卡 id）。", "ProduceItem": "道具名。", "ProduceDrink": "饮料名。", "ProduceDescriptionName": "引用 Label/Convert（受场景替换）。", "ProduceDescription": "引用 Label（术语）。", "DiffText": "强化前后差异高亮文本。", "ProduceStepBusinessType": "营业种类名。"})
en("ProducePlanType", {"Unknown": "未指定。", "Common": "共通。", "Plan1": "センス（好調/集中）。", "Plan2": "ロジック（好印象/やる気）。", "Plan3": "アノマリー（指針：全力/強気/温存）。"})
en("ProduceCardCategory", {"ActiveSkill": "アクティブスキルカード。", "MentalSkill": "メンタルスキルカード。", "Trouble": "トラブルカード。"})
en("ProduceCardRarity", {"N": "N。", "R": "R。", "Sr": "SR。", "Ssr": "SSR。", "Legend": "Legend（レジェンド/H.I.F 专属）。"})
en("ProduceType", {"FirstStar": "定期公演『初』。", "NextIdolAudition": "N.I.A。", "HatsuboshiIdolFestival": "H.I.F。"})
en("ProduceSplitType", {"Selection": "H.I.F 選抜試験（produce-007）。", "Final": "H.I.F 本戦（produce-008）。"})
en("ExamPlayType", {"AutoPlay": "培育内自动打牌。", "AutoPlayCompetition": "コンテスト自动。", "ManualPlayLesson": "手动课程时的提示评估。", "ManualPlayLessonHard": "追い込み。", "ManualPlayAudition": "试炼。"})
en("ExamStatusEffectType", {"ParameterBuff": "好調。", "LessonBuff": "集中。", "Review": "好印象。", "Aggressive": "やる気。", "FullPowerPoint": "全力値。", "ParameterBuffMultiplePerTurn": "絶好調。"})
en("ProduceStepBusinessType", {"ProduceCard": "商業施設（得强化卡）。", "ProduceDrink": "企業イベント会場（得饮料）。", "ProducePoint": "自治体イベント会場（得 P点）。", "Stamina": "リゾート施設（回体力；仅标签）。"})
en("ProduceEffectType", {
    "VocalAddition": "Vocal +v。", "DanceAddition": "Dance +v。", "VisualAddition": "Visual +v。", "VocalGrowthRateAddition": "Vocal 成长率 +v‰。", "DanceGrowthRateAddition": "。", "VisualGrowthRateAddition": "。",
    "StaminaRecoverFix": "体力 +v。", "StaminaRecoverMultiple": "最大体力 ×v‰ 回复。", "StaminaReduceFix": "体力 -v。", "MaxStaminaAddition": "最大体力 +v。", "MaxStaminaReduceFix": "最大体力 -v。",
    "ProducePointAddition": "P点 +v。", "ProducePointAdditionDisableTrigger": "初期 P点 +v（不触发获得事件）。", "ProducePointReduceFix": "P点 -v。",
    "ProduceReward": "给固定奖励 produceRewards。", "ProduceRewardSet": "从奖励集合（id 内 p_rd-…）按 pickRange 给 pickCount 个 produceResourceType。",
    "ProduceCardUpgrade": "强化筛选/选择的卡。", "ProduceCardChange": "チェンジ 为集合内其他卡。", "ProduceCardChangeSelect": "セレクトチェンジ。", "ProduceCardChangeUpgrade": "チェンジして強化。", "ProduceCardDelete": "删除卡。", "ProduceCardDuplicate": "コピー。", "ProduceCardExcludeCountUp": "スキルカード除去回数 +v。", "ProduceCardSelectRerollCountUp": "获得卡再抽次数 +v。",
    "ExamStatusEnchant": "下次课程/试炼开始时挂持续效果。", "ExamPermanentAuditionStatusEnchant": "以后所有试炼开始时挂持续效果。", "ExamPermanentLessonStatusEnchant": "以后所有课程开始时挂。",
    "ExamTurnDown": "回合数 -v。", "AuditionNpcEnhance": "对手分数 +v‰。", "AuditionNpcWeaken": "对手分数 -v‰。", "AuditionParameterBonusMultiple": "试炼スコアボーナス +v‰。", "AuditionVoteCountUp": "试炼票数 +v‰。", "EventBusinessVoteCountUp": "营业票数 +v‰。", "VoteCountAddition": "票数 +v。",
    "LessonSpChangeRatePermilAddition": "SP 课程发生率 +v‰。", "LessonVocalSpChangeRatePermilAddition": "。", "LessonDanceSpChangeRatePermilAddition": "。", "LessonVisualSpChangeRatePermilAddition": "。",
    "LessonPresentProducePointUp": "课程奖励 P点 +v‰。", "LessonPresentProduceCardRewardCountUp": "课程奖励选卡数 +v。", "SupportCardProduceCardUpgradeProbabilityUp": "该支援卡 レッスンサポート 发生率 +v‰。",
    "SupportCardEventStaminaRecoverUp": "支援事件体力回复 +v‰。", "SupportCardEventProducePointAdditionValueUp": "。", "SupportCardEventParameterAdditionValueUp": "。",
    "ShopPriceDiscountMultiple": "相談全项 -v‰。", "ShopPriceUpMultiple": "+v‰。", "ShopProduceCardPriceDiscountMultiple": "相談卡 -v‰（本次）。", "ShopProduceCardPriceDiscountMultiplePermanent": "永久。", "ShopProduceDrinkPriceDiscountMultiple": "。", "ShopProduceCardUpgradePriceDiscountMultiple": "。", "ShopProduceCardDeletePriceDiscountMultiple": "。", "ShopRerollCountUp": "相談刷新 +v。",
    "EventSchoolStaminaUp": "授業消耗体力 +v‰。", "EventSchoolStaminaDown": "-v‰。", "EventActivityProducePointUp": "お出かけ P点消耗 +v‰。", "EventActivityProducePointDown": "-v‰。",
    "BeforeAuditionRefreshStaminaUp": "试炼前回复 +v‰。", "BeforeAuditionRefreshStaminaDown": "-v‰。", "ParameterLimitUp": "参数上限 +v。", "StarAddition": "スター性 +v。", "StarPermilUp": "スター性获得 +v‰。",
    "HighScoreGoldAddition": "活动货币 +v。", "CustomizeProduceCardProducePointDownMultiple": "下次定制费用 -v‰。", "IdolCardProduceCardCustomizeEnable": "允许定制固有卡。", "ProduceCustomizeItemUpgrade": "升级定制道具。", "ProduceDrinkPossessLimitUp": "饮料上限 +v。",
})

# =========================================================================== fill-ins for remaining fields
def _f(table, **kw):
    T.setdefault(table, {"desc": "", "fields": {}, "notes": "", "fk": []})["fields"].update(kw)

_f("ProduceSeason", fixRankTime="排名锁定时间（Unix ms 字符串）。")
_f("ProduceNextIdolAuditionMasterRankingSeason", fixRankTime="排名锁定时间。")
_f("ProduceStepSelfLesson", progressLevel="进度等级（全 1）。")
_f("PvpRateCommonProduceCard", produceCards="公共卡列表（id/upgradeCount/customizes）。", **{"produceCards.id": "→ ProduceCard。", "produceCards.upgradeCount": "强化段。", "produceCards.customizes": "定制（空）。"})
_f("MemoryGift", grade="ResultGrade（メモリー评价）。", produceCardPhaseType="ProduceMemoryProduceCardPhaseType：该卡在 ProduceStart 还是 EndAuditionMid 时进入卡组。",
   memoryAbilities="→ MemoryAbility 列表。", vocal="メモリー三维。", dance="。", visual="。", stamina="体力。",
   examBattleProduceCards="コンテスト用卡组。", examBattleProduceItemIds="→ ProduceItem コンテスト用道具。",
   **{"produceCard.id": "→ ProduceCard。", "produceCard.upgradeCount": "强化段。", "produceCard.customizes": "定制列表。",
      "produceCard.customizes.id": "→ ProduceCardCustomize。", "produceCard.customizes.customizeCount": "段数。",
      "memoryAbilities.id": "→ MemoryAbility。", "memoryAbilities.level": "等级。",
      "examBattleProduceCards.id": "→ ProduceCard。", "examBattleProduceCards.upgradeCount": "强化段。", "examBattleProduceCards.customizes": "定制。"})
_f("ProduceEffectIcon", type="ProduceEffectType。", iconAssetId="图标。", backgroundAssetId="背景。")
_f("IdolCardPrimaStellaProduceSkill", produceSkillLevel="技能等级（全 1）。")
_f("ProduceExamAutoTriggerEvaluation", type="ExamPlayType。")
_f("PvpRateConfig", vocal="赛季基准 Vocal。", dance="。", visual="。", examBattleFirstRankBonusPermil="第一名分数加成千分比（200）。",
   startTimelineInitialTimePermil="演出时间参数。", winTimelineAssetId="演出。", loseTimelineAssetId="演出。", topAssetId="UI。",
   **{"stages.stageType": "PvpRateStageType（_1/_2/_3）。", "stages.planType": "该阶段プラン。", "stages.turn": "回合数。", "stages.produceItemId": "→ ProduceItem 阶段道具。",
      "stages.produceItemIds": "→ ProduceItem。", "stages.produceExamGimmickEffectGroupId": "→ ProduceExamGimmickEffectGroup。", "stages.bgmAssetId": "BGM。",
      "stages.startTimelineAssetId": "演出。", "stages.examTimelineAssetId": "演出。", "stages.vocal": "阶段基准 Vocal。", "stages.dance": "。", "stages.visual": "。",
      "stages.produceExamBattleScoreConfigId": "→ ProduceExamBattleScoreConfig。"})
_f("CompetitionExamStatusEffectIcon", examStatusEffectType="ExamStatusEffectType。")
_f("ProduceGuide", producerLevel="适用 P 等级（20/35）。", produceGuideProduceCardCategoryGroupId="→ ProduceGuideProduceCardCategoryGroup。", produceGuideProduceCardSampleDeckCategoryGroupId="→ ProduceGuideProduceCardSampleDeckCategoryGroup。")
_f("ProduceSplitAdv", type="ProduceAdvType。", produceSplitTypes="适用的 ProduceSplitType。", targetCharacterId="→ Character。")
_f("ProduceGroupLiveCommon", type="ProduceLiveType。", needForceLiveCommonIdolCard="需要指定形象卡。", musicId="→ Music。")
_f("SeminarExamTransition", isLessonInt="1=课程型研修。", seminarExamGroupName="研修组名。", seminarExamName="研修名。", rewards="奖励。", seminarExamGroupId="研修组 id（不在 dump 中）。", seminarExamId="研修 id（不在 dump 中）。",
   **{"rewards.resourceType": "。", "rewards.resourceId": "。", "rewards.quantity": "。"})
_f("TutorialProduce", tutorialType="TutorialType。", idolCardParameterGrowthLimit="参数上限 1200。", memoryGiftId="→ MemoryGift。", musicId="→ Music。")
_f("TutorialProduceStep", tutorialType="TutorialType。", stepNumber="周序号。", tutorialStep="教程步骤号。", produceStepRefresh="是否休息。", produceStepLessonId="→ ProduceStepLesson。",
   progressLevel="进度等级。", produceNavigationNumber="导航台词序号。", rankThreshold="合格名次。", parameterBaseLine="参数基准。", baseScore="基础分。", forceEndScore="强制结束分。",
   produceExamBattleNpcGroupId="→ ProduceExamBattleNpcGroup。", produceExamBattleConfigId="→ ProduceExamBattleConfig。", produceExamGimmickEffectGroupId="→ ProduceExamGimmickEffectGroup。")
_f("ProduceStory", produceEventHintProduceConditionDescriptions="触发条件提示文本。", advAssetId="ADV。")
_f("ProduceAdv", type="ProduceAdvType。")

ENUM_NOTES["ProduceCardGrowEffectType"].pop("CostBuffAdd/Reduce", None)
ENUM_NOTES["ProduceCardGrowEffectType"].update({"CostBuffAdd": "强化状态费用 +v（未使用）。", "CostBuffReduce": "强化状态费用 -v（未使用）。"})
