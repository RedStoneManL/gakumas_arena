"""Hand-written Chinese annotations for the master-data atlas.

Used by build_docs.py.  Keys are table names; each entry has
  desc   : prose describing the table (Chinese, identifiers in English)
  fields : {fieldPath: meaning}
  notes  : optional extra prose appended after the samples
  fk     : optional manual foreign-key notes (list of str)
Field paths use the same dotted notation as inspect_dump.py (e.g. "playEffects.produceExamEffectId").
"""

# --------------------------------------------------------------------------- shared field meanings
COMMON = {
    "id": "主键。绝大多数表的 id 本身就是“可读的编码”（见各表说明），很多语义只在 id 里出现。",
    "name": "显示名（日文）。",
    "assetId": "美术/预制体资源 id（非外键；AssetDownload 里只登记了一部分）。",
    "order": "客户端排序键（字符串或整数，纯展示用）。",
    "viewStartTime": "可见起始时间，Unix 毫秒字符串；\"0\" 表示一直可见。",
    "isLimited": "限定标记（全库均为 false）。",
    "libraryHidden": "图鉴（ピクチャーブック）中隐藏。",
    "produceDescriptions": "描述模板片段列表（结构见 §2），渲染后即游戏内效果文本。**这是效果语义最可靠的说明**。",
    "customizeProduceDescriptions": "卡牌定制（カスタマイズ）界面用的描述片段：与 produceDescriptions 相同，只是在开头多一个 `Label_StyleDot`（项目符号）。",
    "effectGroupIds": "→ EffectGroup。把效果归入“xx效果”组，用于筛选（例如“好調効果のスキルカード”这类条件就是按 effectGroup 匹配）。",
    "planType": "ProducePlanType：Common=全プラン通用 / Plan1=センス / Plan2=ロジック / Plan3=アノマリー。",
    "rarity": "稀有度枚举。",
    "unlockConditionSetId": "→ ConditionSet，解锁条件。",
    "viewConditionSetId": "→ ConditionSet，显示条件。",
    "characterId": "→ Character（4 字母缩写，如 amao=有村麻央、hski=花海咲季）。",
    "produceId": "→ Produce（剧本/难度）。",
    "produceGroupId": "→ ProduceGroup（剧本系列：初 / N.I.A / H.I.F）。",
    "evaluation": "评价分：用于メモリー/编成强度评估（越高越强）。",
    "number": "组内序号。",
    "produceCardSearchId": "→ ProduceCardSearch，卡牌筛选器（决定作用对象/统计对象）。",
    "pickRangeType": "ProducePickRangeType：All=全部命中对象 / Random=随机抽取 / Select=玩家选择 / Unknown=不适用。",
    "pickCountMin": "选取数量下限。",
    "pickCountMax": "选取数量上限。",
    "produceExamStatusEnchantId": "→ ProduceExamStatusEnchant（持续效果 = 触发器 + 效果列表）。",
    "produceExamTriggerId": "→ ProduceExamTrigger（考试内触发/条件）。",
    "produceExamEffectId": "→ ProduceExamEffect（考试内原子效果）。",
    "produceExamEffectIds": "→ ProduceExamEffect 列表，按顺序依次结算。",
    "produceEffectId": "→ ProduceEffect（培育外循环效果）。",
    "produceEffectIds": "→ ProduceEffect 列表。",
    "produceTriggerId": "→ ProduceTrigger（培育外循环触发时机）。",
    "produceSkillId": "→ ProduceSkill。",
    "supportCardId": "→ SupportCard。",
    "idolCardId": "→ IdolCard。",
    "produceCardId": "→ ProduceCard（注意 ProduceCard 主键是 (id, upgradeCount)）。",
    "produceCardIds": "→ ProduceCard 列表（可重复表示多张）。",
    "upgradeCount": "强化段数（0=未强化，1=+，2/3 见 legend 卡）。",
    "examEffectType": "ProduceExamEffectType；在“按プラン/主 buff 分流”的表里表示 6 大流派之一（ExamParameterBuff=好調系 / ExamLessonBuff=集中系 / ExamReview=好印象系 / ExamCardPlayAggressive=やる気系 / ExamConcentration=強気(アノマリー) / ExamFullPower=全力(アノマリー)）。",
    "description": "说明文（日文）。",
    "produceType": "ProduceType：FirstStar=定期公演『初』 / NextIdolAudition=N.I.A / HatsuboshiIdolFestival=H.I.F。",
    "produceSplitType": "ProduceSplitType：H.I.F 把一次培育拆成 Selection(選抜試験, produce-007) 与 Final(本戦, produce-008) 两半；Unknown=不区分。",
    "stepType": "ProduceStepType（周程类型：LessonXxx / AuditionMid1/Mid2/Final / EventXxx / Present / Refresh / OpenLesson / SelfLesson ...）。",
    "resourceType": "ResourceType/ProduceResourceType 枚举。",
    "resourceId": "资源 id，按 resourceType 多态指向 Item/ProduceCard/ProduceItem/ProduceDrink/...。",
    "quantity": "数量。",
    "voiceAssetId": "语音资源 id。",
    "title": "标题。",
    "level": "等级。",
    "startTime": "开始时间（Unix ms 字符串）。",
    "endTime": "结束时间（Unix ms 字符串，0=无）。",
    "isBusinessExcellent": "营业(Business)事件的“大成功”版本标记。",
}

# --------------------------------------------------------------------------- nested structures explained once
NESTED = {
    "produceDescriptions": {
        "produceDescriptionType": "ProduceDescriptionType：片段类型（PlainText=纯文本 / Exam=数值槽 / ProduceExamEffectType=效果名标签 / ProduceCard=卡名 / ProduceDescriptionName=引用 Label / DiffText=强化差异高亮 / ProduceCardCategory / ProduceCardGrowEffectType / ProduceDescription / ProduceItem / ProduceDrink / ProduceStepBusinessType）。",
        "examDescriptionType": "ExamDescriptionType：数值槽种类（CustomizeEffectValue1/2、CustomizeEffectValuePercent1/2、CustomizeTurn、CustomizeEffectCount、CustomizeCostValue、CustomizeLessonCountAdd、CustomizeInitialAdd、CustomizePlayMovePositionLost、CustomizeEffectAdd、ExamValue/ExamValue2/ExamTurn/ExamCount/ExamTurnTimer=运行时填充的槽）。",
        "examEffectType": "当片段是效果名标签时，指明是哪种 ProduceExamEffectType。",
        "produceCardGrowEffectType": "当片段是成长效果名标签时的 ProduceCardGrowEffectType。",
        "produceCardCategory": "当片段是卡牌类别标签时的 ProduceCardCategory。",
        "produceCardMovePositionType": "当片段描述移动位置时的 ProduceCardMovePositionType。",
        "produceStepType": "片段引用的 ProduceStepType（例如“学園活動”）。",
        "produceStepBusinessType": "片段引用的 ProduceStepBusinessType（营业种类）。",
        "text": "**已渲染的文本**（大多数片段都直接带最终文字；空字符串的 PlainText = 换行）。",
        "targetId": "片段引用对象：Label_*/Description_*/Convert_*（→ ProduceDescriptionLabel）或 ProduceCard/ProduceItem 的 id。",
        "targetLevel": "引用对象的等级/强化段（几乎全 0）。",
        "effectValue1": "槽位对应的原始数值（如 permil 值 200 渲染成 “20%”）。",
        "effectValue2": "第二数值。",
        "effectCount": "次数。",
        "turn": "回合数。",
        "costValue": "费用值。",
        "produceDescriptionSwapId": "→ ProduceDescriptionSwap：文本按 レッスン/試験(オーディション) 场景替换（パラメータ↔スコア 等）。",
        "originProduceExamTriggerId": "该片段来源的 ProduceExamTrigger。",
        "originProduceExamEffectId": "该片段来源的 ProduceExamEffect。",
        "originProduceCardStatusEnchantId": "该片段来源的 ProduceCardStatusEnchant。",
        "isCost": "该片段属于费用说明。",
        "isOnlyOutGame": "只在培育外（图鉴/编成）显示，考试内不显示（例如“重複不可”）。",
        "changeColor": "变色高亮。",
    },
    "playEffects": {
        "produceExamTriggerId": "该条效果的附加发动条件（空=无条件）。",
        "produceExamEffectId": "→ ProduceExamEffect。",
        "hideIcon": "不显示效果图标。",
        "isOncePlayEffect": "每场只发动一次的效果（用于 再演 ExamStatusEnchantEncore 等）。",
    },
    "rewards": {
        "resourceType": "ResourceType。",
        "resourceId": "资源 id（多态）。",
        "quantity": "数量。",
    },
}

T = {}  # table annotations, filled below


def add(name, desc, fields=None, notes="", fk=None):
    T[name] = {"desc": desc, "fields": fields or {}, "notes": notes, "fk": fk or []}


# =========================================================================== A. 剧本与全局设定
add("Produce",
    "培育剧本/难度的顶层定义。8 行 = 『初』レギュラー/プロ/マスター/レジェンド(produce-001/002/003/006)、N.I.A プロ/マスター(004/005)、"
    "H.I.F 選抜試験/本戦(007/008)。每行决定周数(steps)、参数成长上限、试炼配置等；通过 produceSettingId / examSettingId 挂接数值设定。",
    {
        "baseStepLevel": "起始 step level（决定课程强度表 ProduceStepLessonLevel 的 progressLevel 起点；初 プロ/マスター=5）。",
        "maxRefreshCount": "可“休息(Refresh)”的最大次数（N.I.A / レジェンド=4，其他 0=不限）。",
        "produceSelectScreenOrderType": "选择界面分页（First/Second，レジェンド在第二页）。",
        "challengeViewConditionSetId": "→ ConditionSet，チャレンジPアイテム 栏位显示条件。",
        "examSettingId": "→ ExamSetting（全库唯一 p_exam_setting-1）。",
        "produceSettingId": "→ ProduceSetting，每个剧本一份。",
        "idolCardParameterGrowthLimit": "三维参数成长上限（初 1000/1500/1800/3000，NIA 2000/2600，HIF 3000）。",
        "maxProduceEventCharacterGrowthNumber": "角色成长事件（CharacterGrowth）最多触发次数（仅『初』2/3）。",
        "steps": "总周数（初 13/16/18，NIA 27/26，HIF 選抜 20 + 本戦 9）。",
        "actionPointQuantity": "消耗 AP（15/20）。",
        "produceNavigationNormalId": "→ ProduceNavigation，普通导航台词组。",
        "produceNavigationAuditionId": "→ ProduceNavigation，试炼前导航台词组。",
        "produceNavigationLoseId": "→ ProduceNavigation，失败导航台词组。",
        "gradientColor1": "UI 渐变色。", "gradientColor2": "UI 渐变色。",
        "easyProduceItemIds": "→ ProduceItem，简单模式(イージー)附赠道具（仅 NIA プロ）。",
        "easyConditionSetId": "→ ConditionSet，简单模式可选条件（亲爱度 1..18）。",
        "easyProduceConditionSetId": "简单模式限制条件（id 以 p-cd- 开头，不在 ConditionSet 中）。",
        "splitPairProduceId": "→ Produce，H.I.F 的另一半（007↔008）。",
        "selectionMemoryEmbedProduceCardId": "→ ExamContestEmbedProduceCard，H.I.F 選抜メモリー生成时嵌入的卡池。",
    })
add("ProduceGroup",
    "剧本系列。3 行：定期公演『初』(FirstStar) / NEXT IDOL AUDITION / Hatsuboshi IDOL FESTIVAL。挂 Produce 列表、评价上限、通用 Live 设置。",
    {
        "type": "ProduceType。",
        "produceIds": "→ Produce。",
        "failedProduceMemoryAssetId": "培育失败时的メモリー图。",
        "isForceLiveCommon": "结束 Live 是否强制使用通用曲目（NIA/HIF=true）。",
        "disableForceLiveCommonEndingLiveType": "例外：该 ProduceLiveType 不强制通用（TrueEnd）。",
        "limitGrade": "该系列可达到的最高评价（初 Ssss / NIA SssPlus / HIF Sssss）。",
    })
add("ProduceSetting",
    "每剧本一份的培育数值设定（休息回复比例、饮料上限、定制次数等）。",
    {
        "initialProducePoint": "初始 P ポイント（全 0）。",
        "produceDrinkPossessLimit": "P饮料默认持有上限 3。",
        "refreshStaminaRecoveryPermil": "“休む”回复最大体力的千分比（700 / HIF 500）。",
        "customizeProduceCardCount": "特别指导(カスタマイズ)一次可定制卡数（1 或 2）。",
        "stepSkipStaminaRecoveryPermil": "跳过周程的体力回复千分比 250。",
        "beforeAuditionRefreshStaminaRecoveryPermil": "试炼前自动回复千分比（700 / NIA・HIF 500）。",
        "stepCustomizeStartAlertProducePointThreshold": "进入定制时 P点低于该值弹提示。",
        "examStartAlertStaminaThreshold": "考试前体力低于 10 弹提示。",
        "continueCount": "可コンティニュー次数 3。",
        "produceAuditionTrendAssessmentPermilUpper": "试炼“合格趋势”评估上界千分比（200 或 110）。",
        "produceAuditionTrendAssessmentPermilLower": "同上下界。",
        "maxLegendProduceCardCount": "可持有的 Legend 卡数（レジェンド/HIF=1）。",
        "stepIntervalUpgradeProduceCardCount": "每次强化周程可强化卡数 1。",
        "stepIntervalCustomizeProduceCardCount": "每次定制周程可定制卡数 2。",
        "selectionMemoryNeedProduceCardCount": "H.I.F 選抜メモリー需要卡数 1。",
        "produceDrinkPossessMaxLimit": "饮料持有硬上限 4（含上限+1 技能）。",
    })
add("ExamSetting",
    "考试（レッスン/試験）引擎的全局常量，全库仅 1 行 p_exam_setting-1；Produce/PvpRateConfig/Tour/GvgRaid/TutorialProduce 全部指向它。**实现引擎必须逐字段读取**。",
    {
        "examStaminaConsumptionDownPermil": "消費体力減少 状态：消耗×50%。",
        "examStaminaConsumptionAddPermil": "消費体力増加 状态：消耗+100%。",
        "examBlockAddDownPermil": "不安：元気获得×66.7%（即 -33%）。",
        "examStaminaConsumptionAddDownPermil": "消費体力増加効果減少（1250）：增加效果被削到 50%（未使用效果）。",
        "examStaminaReduceChange": "体力消費軽減 常量 1（未使用）。",
        "examStaminaConsumptionDownAddPermil": "消費体力減少効果増加：减少效果改为 60%（未使用）。",
        "examConcentrationLessonValueMultiplePermil": "強気 参数倍率 2000（旧字段，被 ...Permil1/2 取代）。",
        "fullPowerPlayableValueAdd": "进入全力时 追加使用次数 +1。",
        "examFullPowerLessonValueMultiplePermil": "全力 参数倍率 3000（=+200%）。",
        "holdLimit": "保留(ホールド)区上限 2。",
        "handLimit": "手牌上限 5。",
        "turnStartDistribute": "每回合开始发牌 3 张。",
        "examGimmickParameterDebuffPermil": "不調：参数×66.7%。",
        "examParameterBuffPermil": "好調：参数×150%。",
        "examTurnEndRecoveryStamina": "回合结束回复体力 2（试炼特有规则）。",
        "produceExamPanicStaminaCandidates": "気まぐれ 随机消耗体力候选值列表（1..15）。",
        "examParameterBuffMultiplePerTurnPermil": "絶好調：每剩余 1 回合好調 +10%。",
        "preservationReleasePlayableValueAdd1": "温存1段 解除时 使用次数+1。",
        "preservationReleasePlayableValueAdd2": "温存2段 解除时 使用次数+1。",
        "preservationReleaseBlockAdd1": "温存1段 解除时 固定元気 +0。",
        "preservationReleaseBlockAdd2": "温存2段 解除时 固定元気 +5。",
        "preservationReleaseEnthusiastic1": "温存1段 解除时 熱意 +5。",
        "preservationReleaseEnthusiastic2": "温存2段 解除时 熱意 +8。",
        "examConcentrationLessonValueMultiplePermil1": "強気1段 参数 +100%。",
        "examConcentrationLessonValueMultiplePermil2": "強気2段 参数 +150%。",
        "examPreservationLessonValueMultiplePermil1": "温存1段 参数×50%。",
        "examPreservationLessonValueMultiplePermil2": "温存2段 参数×25%。",
        "examConcentrationStaminaMultiplePermil1": "強気1段 消耗体力×200%。",
        "examConcentrationStaminaMultiplePermil2": "強気2段 消耗体力×200%。",
        "examPreservationStaminaMultiplePermil1": "温存1段 消耗×50%。",
        "examPreservationStaminaMultiplePermil2": "温存2段 消耗×25%。",
        "examConcentrationStaminaPenetrateReduce1": "強気1段 每用一张卡额外 体力消費(无视元気) 0。",
        "examConcentrationStaminaPenetrateReduce2": "強気2段 每用一张卡额外 体力消費 1。",
        "examAutoPlayEnableVersion": "自动打牌算法版本 2。",
        "examAutoPlaySearchCommandLimit": "自动打牌搜索深度 5。",
        "overPreservationReleasePlayableValueAdd": "のんびり 解除 使用次数+1。",
        "overPreservationReleaseBlockAdd": "のんびり 解除 固定元気+5。",
        "overPreservationReleaseEnthusiastic": "のんびり→強気 熱意+10。",
        "examOverPreservationLessonValueMultiplePermil": "のんびり 参数×0%。",
        "examOverPreservationStaminaMultiplePermil": "のんびり 消耗×0%。",
        "overPreservationReleaseToFullPowerGrowEffectLessonAdd": "のんびり→全力 时全卡 パラメータ値増加+10。",
        "examAutoPlaySearchCommandPlanLimits": "各プラン自动打牌搜索深度 [5,5,5]。",
        "examLessonValueMultipleDependReviewOrAggressiveMultiplePermil": "プライド：min(好印象,やる気) 每 1 点 +2%。",
        "examLessonValueMultipleDependReviewOrAggressiveMaxPermil": "プライド 上限 +50%。",
        "fixMoveCardShuffleDeckEnable": "移动卡到牌库指定位置后是否保持洗牌规则 true。",
        "examBuffConsumptionDownPermil": "強化状態コスト減少 ×50%（未使用效果）。",
        "examBuffConsumptionAddPermil": "強化状態コスト増加 +100%。",
    })
add("ProduceSeason", "培育赛季（シーズン0/1）的时间窗，用于评价/榜单结算。", {"fixRankTime": "排名锁定时间。"})
add("ProduceSeasonZeroGrade", "シーズン0 期间各剧本系列的评价(ResultGrade)分数阈值（已被 ProduceGrade 取代）。",
    {"grade": "ResultGrade。", "threshold": "达到该评价所需 培育评分。"})
add("ProduceGrade", "当前各剧本系列的最终评价阈值：F=0,E=1000,D=2000,C=3000,C+=4500,B=6000,B+=8000,A=10000,A+=11500,S=13000,S+=14500,SS=16000,SS+=18000,SSS=20000,SSS+=23000,SSSS=26000(初/HIF),SSSS+=30000,SSSSS=35000(仅 HIF)。",
    {"grade": "ResultGrade。", "threshold": "培育评分阈值。"})
add("ResultGradePattern", "四类结果评价的通用阈值表：ProduceScore(评分, 到 SSSSS+=40000)、ProduceIdolCardParameter(参数, E=100…SSS+=3500)、ProduceVoteCount(NIA 投票数, E=3000…SSS+=160000)、ProduceStar(HIF スター性, E=20…S+=1200)。",
    {"type": "ResultGradeType。", "grade": "ResultGrade。", "threshold": "阈值。"})
add("ProduceHighScore", "高分活动（ハイスコアイベント / 十王邦夫のアイドル強化月間）定义，Normal/Rush 两种；与 ProduceItem.isHighScoreRush、ProduceEffectType_HighScoreGoldAddition 关联。",
    {"produceHighScoreEventType": "Normal / Rush。", "bannerAssetId": "横幅图。"})
add("ProduceLegendProduceCard", "『初』レジェンド(produce-006) 每个流派(examEffectType)可选的 Legend 稀有度卡列表（每流派 5 张，共 15 张）。",
    {"produceCardIds": "→ ProduceCard（rarity=Legend）。"})
add("ProduceNavigation", "（仅备注）培育中导航角色台词：id=台词组，number=序号，description=台词（含 <COLOR_VOCAL> 富文本）。与模拟无关。",
    {"description": "台词文本。"})
add("ProduceCharacter", "剧本 × 角色 的开放关系（哪个角色可在哪个剧本培育，及解锁条件）。",
    {"forceLiveCommonIdolCardId": "→ IdolCard，通用 Live 时使用的形象卡。"})
add("ProduceCharacterUnit", "H.I.F 的双人 unit（REVERSI：kllj↔ssmk）定义，仅影响演出。", {"targetCharacterId": "本人。", "unitCharacterId": "搭档。"})
add("ProduceChallengeSlot", "チャレンジPアイテム 槽位：剧本(003/005/006) × 流派 × 槽序号 → ProduceItemChallengeGroup。",
    {"produceItemChallengeGroupId": "→ ProduceItemChallengeGroup。", "unlockDescription": "解锁条件说明。"})
add("ProduceChallengeCharacter", "チャレンジ 模式按角色的解锁条件（亲爱度 10 等）。")
add("ProduceItemChallengeGroup", "チャレンジPアイテム 分组：一组里多件道具，附带课程上限分加成与试炼参数成长率。",
    {"produceItemId": "→ ProduceItem（isChallenge=true 的道具）。", "lessonLimitUpScore": "课程 CLEAR 上限提升。", "auditionParameterGrowthRatePermil": "试炼参数成长率千分比。"})
add("ProduceNextIdolAuditionMasterRankingSeason", "N.I.A マスター 排行赛季时间窗。")
add("ProduceGrowthPanelSheet", "成长面板（H.I.F 专属“育成パネル”）表头：解锁道具、任务组、成就。", {"unlockItemId": "→ Item，面板点数道具。", "missionGroupId": "→ MissionGroup。", "achievementId": "→ Achievement。"})
add("ProduceGrowthPanel", "成长面板的每格：9 个面板(id) × 最多 6 级(level)，每级消耗 unlockItemQuantity 点数，给予永久 ProduceEffect（三维加成、成长率、SP率、上限+、商店折扣等）。produceSplitType 指明只在 選抜/本戦 生效。",
    {"unlockItemQuantity": "解锁所需点数。", "isUnlockRecommended": "推荐标记。"})
add("ProduceLive", "结束 Live 曲目/舞台资源表（musicId × ProduceLiveType）。与模拟无关，仅备注。", {"type": "ProduceLiveType（A/B/C/D/E/TrueEnd）。", "musicId": "→ Music。"})
add("ProduceLiveEvaluation", "剧本 × 角色 × 可出现的 Live 类型（评价等级 → Live 分支）。", {"liveType": "ProduceLiveType。"})
add("ProduceGroupLiveCommon", "（备注）各剧本系列通用 Live 的资源。")
add("ProduceAdv", "（备注）『初』/N.I.A 的固定剧情 ADV（试炼前夜、结果等）。", {"type": "ProduceAdvType。"})
add("ProduceSplitAdv", "（备注）H.I.F 的固定剧情 ADV，按 Selection/Final 与目标角色分。")
add("ProduceStory", "培育中剧情条目（3341）：类型 Character/CharacterGrowth/IdolCard/SupportCard/Step*Event；produceEventHintProduceConditionDescriptions 是“事件出现条件”的人读提示。仅备注。",
    {"type": "ProduceStoryType。", "produceEventHintProduceConditionDescriptions": "触发条件提示文本。"})
add("ProduceStoryGroup", "剧情组 → 角色 → 具体剧情 的映射（同一组每个角色一条）。", {"produceStoryId": "→ ProduceStory。"})
add("SeminarExamTransition", "（备注）試験研修/基礎研修 教学考试列表（仅 produce-001）。")
add("TutorialProduce", "（备注）新手教程培育设定（3 个初始偶像）。")
add("TutorialProduceStep", "（备注）教程周程脚本。")

# =========================================================================== B. 周程 / 课程 / 试炼
add("ProduceStepLesson",
    "课程(レッスン)实例表。id 编码：`p_step_lesson_level-{produce序号}-{角色}-{hard|normal|sp}-{vo|da|vi}-{序号}`（初）或 `p_step_lesson-produce_00X-{流派}-{normal|sp}-{序号}`（レジェンド/HIF）。"
    "name 是课程档位名（通常レッスンA..E / SPレッスンA..D / 追い込みレッスン / 追加レッスン / レジェンドレッスン / チュートリアル）。真正的数值在 produceStepLessonLevelId。",
    {"produceStepLessonLevelId": "→ ProduceStepLessonLevel（回合数、CLEAR 线、PERFECT 线）。"},
    notes="课程与周次的绑定规则（第几周出现哪个档位）**不在 master 里**，需从游戏/攻略确认；这里只提供档位数值池。")
add("ProduceStepLessonLevel",
    "课程数值档位。id 编码 `p_step_lesson_level-{produce}-{planN}-{hard|normal|sp}-{序号}`。",
    {"progressLevel": "进度等级（全 1）。", "limitTurn": "回合数（normal 5/6，sp 5/6，hard 9/10，legend 更长）。",
     "successThreshold": "CLEAR 目标分。", "resultTargetValueLimit": "PERFECT 目标分（超过后停止计分/满分线）。"})
add("ProduceStepSelfLesson", "自主レッスン（N.I.A produce-004）：固定消耗体力与固定参数收益（无打牌）。", {"stamina": "消耗体力。", "parameter": "参数收益。"})
add("ProduceStepOpenLesson", "公開レッスン（H.I.F produce-007 選抜試験）：消耗体力，主参数+mainParameter，副参数(subParameterType)+subParameter，获得 star（スター性）。id 里含 parameter/star 与 sp 标记。",
    {"stamina": "消耗体力。", "subParameterType": "副参数种类。", "mainParameter": "主参数收益。", "subParameter": "副参数收益。", "star": "スター性收益。"})
add("ProduceStepAuditionDifficulty",
    "试炼(中間/最終試験、オーディション)难度表：id=难度组（按角色 `p_step_audition_difficulty-{chr}` 或按偶像卡 `-i_card-...`，IdolCard.produceStepAuditionDifficultyId 指向），"
    "行 = (id, produceId, stepType, number)。给出参数基准线、基础分、NPC 组、战斗配置(回合/参数)、gimmick 组、票数基准等。",
    {"rankThreshold": "合格名次（初=3 名以内，NIA/HIF 最终=1 位）。", "parameterBaseLine": "参数基准（用于评分换算/合格趋势）。",
     "baseScore": "基础目标分（试炼合格线的基准）。", "forceEndScore": "达到即强制结束（仅『初』中間，如 900）。",
     "produceExamBattleNpcGroupId": "→ ProduceExamBattleNpcGroup（对手 NPC 分数区间）。",
     "produceExamBattleConfigId": "→ ProduceExamBattleConfig（回合数、评分用参数与分数曲线）。",
     "produceExamGimmickEffectGroupId": "→ ProduceExamGimmickEffectGroup（试炼场地效果时间表）。",
     "auditionType": "ProduceStepAuditionType（NIA 的 Mid1Easy..FinalVeryHard 难度分级）。",
     "isUnlockAnimation": "解锁演出。", "voteCountBaseLine": "NIA 投票数基准。", "isStaticNpcScore": "NPC 分数固定（HIF 本戦 border 用）。",
     "dearnessLevel": "需要的亲爱度（NIA FinalHard/VeryHard 14/17）。", "voteCount": "NIA 合格所需票数。", "starScoreBonusBaseLine": "HIF スター性 分数加成基准。"})
add("ProduceStepAuditionCharacter", "N.I.A 各角色每次试炼的合格/失败后排名（successNextIdolAuditionRank / failure...）与选择画面剪影。",
    {"successNextIdolAuditionRank": "合格后的 NIA 排名。", "failureNextIdolAuditionRank": "失败后的排名。", "auditionSelectHeaderSilhouetteAssetId": "剪影角色。"})
add("ProduceExamBattleConfig", "试炼/竞赛的战斗配置：回合数、评分基准三维(vocal/dance/visual)、评分曲线 id；Excellent/Bad 是 NIA 高低分档参数。",
    {"turn": "回合数。", "vocal": "基准 Vocal。", "dance": "基准 Dance。", "visual": "基准 Visual。",
     "produceExamBattleScoreConfigId": "→ ProduceExamBattleScoreConfig。",
     "vocalExcellent": "高分档参数。", "danceExcellent": "同。", "visualExcellent": "同。", "vocalBad": "低分档参数。", "danceBad": "同。", "visualBad": "同。"})
add("ProduceExamBattleScoreConfig", "试炼评分曲线：同一 id 多行，按 parameter（偶像该维参数）分段，给出每维的 permil 系数（分数 = 卡牌スコア × 系数/1000 之类的分段线性插值）。",
    {"parameter": "分段起点（参数值）。", "vocalPermil": "Vocal 回合系数。", "dancePermil": "Dance 回合系数。", "visualPermil": "Visual 回合系数。"})
add("ProduceExamBattleNpcGroup", "试炼对手组：每组 number 个对手（角色或 mob），分数区间 scoreMin..scoreMax、三维占比、开场/中段/终盘得分分配（op/mid/ed Permil）。",
    {"produceExamBattleNpcMobId": "→ ProduceExamBattleNpcMob（路人/边界线 NPC）。", "scoreMin": "最终分下限。", "scoreMax": "上限。",
     "vocalPermil": "分数三维占比。", "dancePermil": "。", "visualPermil": "。", "opScorePermil": "前段得分比例。", "midScorePermil": "中段。", "edScorePermil": "后段。"})
add("ProduceExamBattleNpcMob", "路人 NPC 定义（含 HIF 的 border=合格线虚拟对手 isBorder）。", {"isBorder": "是否为“合格线”虚拟对手。"})
add("ProduceExamGimmickEffectGroup",
    "试炼场地效果（ギミック）时间表：同一 id 多行，priority 排序，startTurn 起生效，可带 fieldStatus 条件（如“元気≤5 时体力-2”），效果为 produceExamEffectId；isPositive 区分正/负面。"
    "PvpRateConfig.stages 与 ProduceStepAuditionDifficulty 引用。",
    {"priority": "同组排序。", "remainingTurnPermil": "未使用(0)。", "startTurn": "生效起始回合。", "remainingTurn": "未使用(0)。",
     "fieldStatusType": "ProduceExamFieldStatusType 条件。", "fieldStatusValue": "条件阈值。", "fieldStatusCheckType": "Not=取反。",
     "fieldStatusProduceCardSearchId": "未使用。", "isPositive": "正面效果标记。"})
add("ProduceStepEventDetail",
    "周程事件（6888）：角色事件(Character/CharacterGrowth/IdolCard/SupportCard) 与 学園活動事件(School/Business/Activity)。id 编码含来源；effect 直接给 produceEffectIds，或给出选项列表 produceStepEventSuggestionIds（お出かけ/授業/営业的选择肢）。",
    {"suggestionType": "全 Primary。", "produceStoryId": "→ ProduceStory（角色事件对应的具体剧情）。", "produceStoryGroupId": "→ ProduceStoryGroup（按角色展开的剧情组）。",
     "produceStepEventSuggestionIds": "→ ProduceStepEventSuggestion（选项）。", "eventType": "ProduceEventType。",
     "eventCharacterType": "ProduceEventCharacterType（Opening/AfterStep1/AfterAuditionMid1/Ending/Failure…触发时机）。"})
add("ProduceStepEventSuggestion",
    "事件选项：消耗 P点/体力，给予 produceEffectIds；可带成功率 successProbabilityPermyriad（万分比）与成功/失败分支效果及后续事件(successStepId)。",
    {"producePoint": "消耗 P点。", "stamina": "消耗体力。", "produceCardUpgradeCount": "赠卡强化段。",
     "stepType": "后续周程类型。", "stepId": "后续周程/事件 id（多为 event-detail-activity-*，少数 exam-*）。",
     "successProbabilityPermyriad": "成功率（万分比，0=无判定）。", "successProduceEffectIds": "成功效果。", "successStepType": "成功后周程类型。", "successStepId": "→ ProduceStepEventDetail 成功后事件。",
     "failProduceEffectIds": "失败效果。", "failStepType": "未使用。", "failStepId": "未使用。", "alwaysSuccessful": "无判定=true。",
     "produceEffectFireStep": "未使用(0)。", "isCampaign": "未使用(false)。"})
add("ProduceEventCharacterGrowth", "角色成长事件（每角色 3 个）：达到某维参数阈值(vocal/dance/visual)后触发 produceStepEventDetailId。",
    {"vocal": "触发阈值。", "dance": "。", "visual": "。", "produceStepEventDetailId": "→ ProduceStepEventDetail。"})
add("ProduceEventSupportCard", "支援卡事件：每张支援卡 3 个事件，需要 supportCardLevel(1/20/40) 才解锁。", {"supportCardLevel": "解锁等级。", "produceStepEventDetailId": "→ ProduceStepEventDetail。"})
add("ProduceStepTransition", "（备注）周程前后过场：角色 × stepType × Before/After 的 ADV/语音/服装。", {"stepPhaseType": "Before/After。", "advAssetId": "ADV。"})
add("ProduceStepFanPresentMotion", "（仅备注）粉丝礼物周程的角色动作。", {"motionType": "Reaction/Wait。"})

# =========================================================================== C. 卡牌
add("ProduceCard",
    "技能卡（スキルカード）。主键 (id, upgradeCount)：同一 id 有 0/1（部分 legend 到 2/3）多行，name 带 '+'。"
    "id 编码 `p_card-{00共通|01センス|02ロジック|03アノマリー}-{act|men|acc(トラブル)|sup(支援卡来源)|ido(偶像固有)}-{稀有度 0N/1R/2SR/3SSR/100Legend}_{序号}`。"
    "打牌语义 = playProduceExamTriggerId（使用条件）+ playEffects（按序结算的 ProduceExamEffect，可各带附加条件）+ playMovePositionType（用后去向）+ 成长(produceCardStatusEnchantId)。",
    {
        "isCharacterAsset": "使用角色专属立绘。",
        "category": "ProduceCardCategory：ActiveSkill / MentalSkill / Trouble。",
        "stamina": "体力消耗（受元気抵扣、消費体力減少/増加 影响）。",
        "forceStamina": "体力消費(无视元気)：直接扣体力的费用。",
        "costType": "ExamCostType：非体力费用种类（好調/集中/好印象/やる気/全力値/絶好調）。",
        "costValue": "非体力费用数值。",
        "playProduceExamTriggerId": "→ ProduceExamTrigger，使用条件（例：元気 0、好調中、強気2段）。",
        "playEffects": "效果列表（结构见 §2）。",
        "playMovePositionType": "用后去向：Grave=弃牌堆 / Lost=除外（レッスン中1回）。",
        "moveEffectTriggerType": "ProduceCardMoveEffectTriggerType：移动到 Hand/Hold 时触发 moveProduceExamEffectIds。",
        "moveProduceExamEffectIds": "移动时效果。",
        "moveProduceExamTriggerIds": "未使用。",
        "isEndTurnLost": "未使用(false)。",
        "isInitial": "レッスン開始時手札に入る。",
        "isRestrict": "未使用(false)。",
        "produceCardStatusEnchantId": "→ ProduceCardStatusEnchant，成长(成長)规则。",
        "searchTag": "标签：starter / idol-unique（ProduceCardSearch.cardSearchTag 用）。",
        "noDeckDuplication": "重複不可（卡组内只能一张）。",
        "isReward": "未使用。",
        "unlockProducerLevel": "解锁所需 P 等级。",
        "rentalUnlockProducerLevel": "租借解锁等级。",
        "originIdolCardId": "→ IdolCard，偶像固有卡来源。",
        "originSupportCardId": "→ SupportCard，支援卡来源（sup 卡）。",
        "isInitialDeckProduceCard": "初始卡组卡（アピールの基本 等）。",
        "produceCardCustomizeIds": "→ ProduceCardCustomize，可选定制方案。",
        "maxCustomizeCount": "最大定制次数（2/3）。",
        "isConversion": "由 ProduceCardConversion 转换得到的卡。",
        "originCharacterId": "→ Character（nasr 专属卡）。",
        "originPrimaStellaIdolCardId": "→ IdolCard，プリマステラ(H.I.F 一番星) 专属卡来源。",
        "playEffects.produceExamTriggerId": NESTED["playEffects"]["produceExamTriggerId"],
        "playEffects.produceExamEffectId": NESTED["playEffects"]["produceExamEffectId"],
        "playEffects.hideIcon": NESTED["playEffects"]["hideIcon"],
        "playEffects.isOncePlayEffect": NESTED["playEffects"]["isOncePlayEffect"],
    })
add("ProduceCardTag", "卡牌标签字典：idol-unique / starter / strike（レッスンメニュー）。")
add("ProduceCardSearch",
    "**卡牌筛选器**（280）：几乎所有“对象选择/条件计数”都通过它表达：位置(cardPositionType)、类别、稀有度、指定卡 id、标签、effectGroup、体力区间、随机池；isSelf=自身。produceDescriptions 给出人读描述（如“手札のアクティブスキルカード”）。",
    {"cardRarities": "稀有度过滤。", "upgradeCounts": "强化段过滤。", "cardCategories": "类别过滤。", "cardStatusType": "未使用。",
     "orderType": "ProduceCardOrderType：First=按顺序取 / Random。", "cardPositionType": "ProduceCardPositionType：Deck/DeckAll/DeckGrave/Hand/Hold/Lost/NotLost/Playing(正在使用的卡)/Target(效果目标)/RandomPool。",
     "cardSearchTag": "→ ProduceCardTag。", "produceCardRandomPoolId": "→ ProduceCardPool/RandomPool（生成随机卡用）。", "limitCount": "数量上限（如“1枚”）。",
     "staminaMinMaxType": "体力费用区间判定类型。", "staminaMin": "。", "staminaMax": "。", "isSelf": "对象=自身。", "produceCardPoolId": "→ ProduceCardPool。", "costType": "未使用。", "isCustomized": "未使用。"})
add("ProduceCardPool", "随机卡池（嵌套 produceCardRatios：卡 id、强化段、权重）。与 ProduceCardRandomPool 内容相同（一个是嵌套形式一个是展开行）。",
    {"produceCardRatios": "权重列表。", "produceCardRatios.id": "→ ProduceCard。", "produceCardRatios.upgradeCount": "强化段。", "produceCardRatios.ratio": "权重。"})
add("ProduceCardRandomPool", "随机卡池展开行形式（id=池，每行一张卡+权重）。", {"ratio": "权重。"})
add("ProduceCardConversion", "卡牌转换（P 等级解锁后 before→after 的替换，例如 R 卡换成新版本）。", {"beforeProduceCardId": "→ ProduceCard。", "afterProduceCardId": "→ ProduceCard。", "conditionSetId": "→ ConditionSet（P等级）。", "isNotReward": "全 true。"})
add("ProduceCardCustomize", "卡牌定制方案：customizeCount 段（1..3）分别给一组成长效果(produceCardGrowEffectIds)，花费 producePoint；overwriteProduceCardGrowEffectType 用于显示成“成長追加”等。",
    {"customizeCount": "定制段数。", "overwriteProduceCardGrowEffectType": "显示用覆盖类型。", "producePoint": "P点费用（20/40/70/100…）。"})
add("ProduceCardCustomizeRarityEvaluation", "定制后评价加成（每稀有度 +12）。")
add("ProduceCardGrowEffect",
    "卡牌成长/定制的原子效果（453）：effectType + value（数值型：LessonAdd 等），或结构型：EffectAdd/EffectChange(替换 targetPlayProduceExamEffectIds→playProduceExamEffectId)、PlayTriggerChange/PlayEffectTriggerChange(替换触发)、CardStatusEnchantChange(换成长规则)、PlayMovePositionTypeChange。",
    {"effectType": "ProduceCardGrowEffectType。", "costType": "未使用。", "value": "数值（LessonDepend* 为千分比）。",
     "playProduceExamTriggerId": "PlayTriggerChange 的新使用条件。", "playEffectProduceExamTriggerId": "PlayEffectTriggerChange 的新效果条件。",
     "targetPlayEffectProduceExamTriggerIds": "被替换的旧触发。", "playProduceExamEffectId": "EffectAdd/EffectChange 加入的新效果。",
     "targetPlayProduceExamEffectIds": "EffectChange 被替换的旧效果。", "produceCardStatusEnchantId": "CardStatusEnchantChange 的新成长规则。",
     "playMovePositionType": "PlayMovePositionTypeChange 的新去向。"})
add("ProduceCardStatusEnchant", "卡牌成长规则（成長）：produceExamTriggerId 满足时对自身应用 produceCardGrowEffectIds，最多 triggerCount 次（0=无限）。",
    {"produceCardGrowEffectIds": "→ ProduceCardGrowEffect。", "triggerCount": "最多触发次数。"})
add("ProduceCardStatusEffect", "空表（0 行）。")
add("ExamInitialDeck", "初始卡组定义：produce_default-{流派}（8 张基础卡）、produce_006/007-{流派}、contest-{偶像卡}（竞赛用 4 张）、以及流派 2 张组。",
    {"produceCardUpgradeCounts": "对应各卡的强化段（空=全 0）。"})
add("ProduceInitialDeck", "剧本 × 流派 → ExamInitialDeck（初/NIA 用 produce_default，レジェンド用 produce_006，HIF 用 produce_007）。", {"examInitialDeckId": "→ ExamInitialDeck。"})
add("ExamContestEmbedProduceCard", "コンテスト/H.I.F 選抜メモリー 生成时按流派嵌入的卡池（每流派 18 张）。")
add("PvpRateCommonProduceCard", "（备注）コンテスト(PvpRate) 各プラン的公共卡。")

# =========================================================================== D. 考试效果引擎
add("ProduceExamEffect",
    "**考试内原子效果**（2070 行，107 种 effectType）。数值槽：effectValue1/2、effectCount、effectTurn(-1=无限)；对象槽：produceCardSearchId + pickRangeType/pickCountMin/Max + movePositionType；"
    "链式：chainProduceExamEffectId(s)（ExamEffectTimer 延迟发动的目标）；结构引用：produceExamStatusEnchantId（ExamStatusEnchant 挂载的持续效果）、produceCardGrowEffectIds（ExamAddGrowEffect 附加的成长）。"
    "每种 effectType 使用哪些槽见 master_data_enums.md §ProduceExamEffectType。id 编码 `e_effect-{snake_type}-{value...}`。",
    {"effectType": "ProduceExamEffectType。", "effectValue1": "主数值（整数或千分比，视类型）。", "effectValue2": "副数值（倍率千分比等）。",
     "effectCount": "次数（参数上升次数 / 生效次数）。", "effectTurn": "持续回合，-1=永久（レッスン終了まで）。",
     "targetProduceCardId": "→ ProduceCard（ExamCardCreateId 生成的卡）。", "targetUpgradeCount": "生成卡的强化段。", "targetExamEffectType": "未使用。",
     "movePositionType": "ProduceCardMovePositionType（移动/生成的目的地）。", "pickCountReferenceProduceCardSearchId": "Shortage 模式下参考的筛选器（“使山札达到 N 张”）。",
     "pickCountType": "ProducePickCountType：Shortage=补足到 N。", "produceCardSearchId2": "未使用。", "pickRangeType2": "未使用。", "pickCountReferenceProduceCardSearchId2": "未使用。", "pickCountType2": "未使用。", "pickCountMin2": "未使用。", "pickCountMax2": "未使用。",
     "chainProduceExamEffectId": "→ ProduceExamEffect，延迟/链式目标。", "chainProduceExamEffectIds": "多个链式目标。",
     "produceCardStatusEnchantId": "未使用。", "produceCardGrowEffectIds": "→ ProduceCardGrowEffect（ExamAddGrowEffect/ExamLessonValueMultipleDown 用）。"})
add("ProduceExamTrigger",
    "**考试内触发/条件**（676）：phaseTypes=时机（ProduceExamPhaseType），phaseValues=时机参数（每 N 次/第 N 回合），fieldStatusTypes/Values(+CheckTypes Not)=场上状态条件，produceCardSearchId + lower/upperSearchCount=对象卡条件（如“使用的是アクティブ卡”），effectTypes=ExamStatusChange/AggressiveUpInterval 关注的效果种类，lessonType=仅某属性课程/回合。"
    "三组描述：produceDescriptions=作为持续效果条件时的文案；playProduceDescriptions=作为使用条件时（…の場合、使用可）；playEffectProduceDescriptions=作为效果附加条件时。",
    {"phaseTypes": "ProduceExamPhaseType 列表（None=纯条件，无时机）。", "phaseValues": "时机参数。", "fieldStatusCheckTypes": "Not=取反（“以下”“非…状態”）。",
     "fieldStatusTypes": "ProduceExamFieldStatusType 列表。", "fieldStatusValues": "阈值（≥；Not 时为 <）。", "fieldStatusProduceCardSearchIds": "CardSearchCountUp 计数用的筛选器。",
     "upperSearchCount": "未使用(0)。", "lowerSearchCount": "命中卡数下限（1=“使用的卡满足筛选”）。", "cardMovePositionType": "未使用。",
     "effectTypes": "关注的效果类型。", "lessonType": "ProduceStepLessonType 限定。",
     "playProduceDescriptions": "使用条件文案。", "playEffectProduceDescriptions": "效果条件文案。"})
add("ProduceExamStatusEnchant",
    "**持续效果**（2003）：= 一个触发器 + 效果列表，由 ProduceExamEffect(ExamStatusEnchant)/ProduceItemEffect/ProduceEffect 挂到场上，回合/次数限制由挂载方给出（effectTurn/effectCount）。"
    "id 前缀表明来源：p_item_effect_*(P道具)、p_card-*(卡)、p_ef-hif_memory-*(HIF メモリー技能)、customize_pitem-*、tower*、p_exam_gimmick-*、bullet_point-*(多条效果的列表式描述)。",
    {"produceExamEffectIds": "→ ProduceExamEffect，触发时依次结算。"})
add("EffectGroup", "效果分组字典（67）：把 ProduceExamEffectType / ProduceEffectType 的多个具体类型归为“xx效果”，用于卡牌/道具筛选和图鉴过滤（hiddenFilter=不在筛选 UI 里显示）。",
    {"examEffectType": "主考试效果类型。", "produceEffectType": "主培育效果类型。", "examEffectTypes": "归入本组的全部考试效果类型。", "produceEffectTypes": "归入本组的培育效果类型。", "hiddenFilter": "筛选 UI 隐藏。", "produceCardGrowEffectTypes": "未使用。"})
add("ExamSimulation", "空表（0 行）。")

# =========================================================================== E. 培育外循环效果
add("ProduceEffect",
    "**培育外循环原子效果**（2114，66 种 produceEffectType）：三维加成、成长率、体力/P点、商店折扣、卡牌操作(強化/削除/チェンジ/コピー)、报酬(ProduceReward/RewardSet)、挂考试持续效果(ExamStatusEnchant/ExamPermanent*)。"
    "数值 effectValueMin..Max（几乎全部 Min=Max；千分比或整数视类型）。",
    {"produceEffectType": "ProduceEffectType。", "effectValueMin": "数值下限。", "effectValueMax": "数值上限。",
     "produceResourceType": "ProduceResourceType（RewardSet/ProduceCardChange 的资源种类）。", "produceRewards": "ProduceReward 的具体奖励列表。",
     "produceRewards.resourceType": "ProduceResourceType。", "produceRewards.resourceId": "→ ProduceCard/ProduceDrink/ProduceItem。", "produceRewards.resourceLevel": "强化段。",
     "produceStepEventDetailId": "未使用。", "isResearch": "リサーチ活动用。"},
    fk=["ProduceRewardSet 的奖励集合 id 只出现在 ProduceEffect.id 里（`p_rd-...`），对应的“集合→候选卡”表**不在 dump 中**。"])
add("ProduceTrigger",
    "培育外循环触发时机（176）。**注意：dump 中该表只有 id 与 phaseType 两个字段**，附加条件（如 `vocal-0400_0000`=Vocal≥400、`stamina_ratio-0500_0000`=体力≥50%、`produce_card_count-0020_0000`=持卡≥20、`for_nia_master` 等）只能从 id 字符串解析，或从 ProduceSkill/ProduceItem 的 produceDescriptions 文本反推。",
    {"phaseType": "ProducePhaseType（ProduceStart/StartLesson/EndLesson/StartAudition/EndAudition/StartShop/GetProduceCard/…）。"})
add("ProduceSkill",
    "培育技能（1488 = 684 个 skill × level）：id 前缀 p_support_skill(支援卡技能 1066) / p_memory_skill(メモリーアビリティ 340) / p_dearness_skill(亲爱度技能 45) / p_idol_skill(偶像卡潜能/上限技能 27) / p_primastella_skill(HIF 一番星 10)。"
    "一条技能 = produceTriggerId1 + produceEffectId1 (+ activationRatePermil1 概率) ，activationCount=培育中最多发动次数；2/3 槽位未使用。",
    {"level": "技能等级（同 id 多行）。", "rarity": "SkillRarity。", "tag": "全 'tag'。", "activationCount": "培育中最多发动次数（0=不限）。",
     "produceEffectId1": "→ ProduceEffect。", "produceTriggerId1": "→ ProduceTrigger。", "activationRatePermil1": "发动概率千分比（0=100%）。",
     "produceEffectId2": "未使用。", "produceTriggerId2": "未使用。", "activationRatePermil2": "未使用。", "produceEffectId3": "未使用。", "produceTriggerId3": "未使用。", "activationRatePermil3": "未使用。"})
add("ProduceItem",
    "P道具（1038）。id 编码 `pitem_{00共通|01|02|03}-{稀有度}-{序号}-{0|1强化}[-000 竞赛变体]`、`pitem_..-challenge[-流派]`、`pitem_tower_*`。"
    "两类：isExamEffect=true 的考试内道具（skills → ProduceItemEffect(ExamStatusEnchant)）与培育外道具（produceTriggerId + skills → ProduceItemEffect(ProduceEffect)），fireLimit/fireInterval 控制次数/间隔。",
    {"fireLimit": "培育中发动次数上限（0=不限）。", "fireInterval": "发动间隔。", "produceTriggerIds": "未使用。", "produceItemEffectIds": "→ ProduceItemEffect。",
     "skills": "效果列表（每项 produceItemEffectId，produceTriggerId 均空）。", "skills.produceTriggerId": "未使用。", "skills.produceItemEffectId": "→ ProduceItemEffect。",
     "isExamEffect": "考试内生效的道具。", "originIdolCardId": "→ IdolCard 固有道具来源。", "originSupportCardId": "→ SupportCard 来源。", "isUpgraded": "强化版（+）。",
     "isChallenge": "チャレンジPアイテム。", "isHighScoreRush": "高分 Rush 活动道具。", "isResearch": "リサーチ活动道具。", "isEasy": "简单模式道具。"})
add("ProduceItemEffect", "P道具效果：ExamStatusEnchant（挂 produceExamStatusEnchantId，effectTurn -1=整场，effectCount=每场次数）或 ProduceEffect（produceEffectId）。",
    {"effectType": "ProduceItemEffectType。", "effectTurn": "持续回合（-1 无限）。", "effectCount": "每场次数。"})
add("ProduceDrink", "P饮料（29）：效果直接是 ProduceDrinkEffect → ProduceExamEffect（即时效果，无触发）。", {"produceDrinkEffectIds": "→ ProduceDrinkEffect。", "unlockProducerLevel": "解锁 P 等级。", "originSupportCardId": "未使用。"})
add("ProduceDrinkEffect", "饮料效果行：仅 produceExamEffectId 有值。", {"produceEffectId": "未使用。"})
add("ProduceCustomizeItem",
    "N.I.A マスター 的“カスタマイズPアイテム”树（180）：isBase 根节点 → ProduceCustomizeItemRelationship 子节点，每个节点 = produceTriggerId + produceEffectIds（含挂持续效果），produceEffectTriggerCount=培育中次数。",
    {"effectType": "全 ProduceEffect。", "assetId1": "外观层 1。", "assetId2": "层 2。", "assetId3": "层 3。", "assetId4": "层 4。", "assetId5": "未使用。",
     "isBase": "根节点。", "isTerminal": "叶节点。", "examEffectTurn": "未使用。", "examEffectCount": "未使用。", "produceExamTriggerId": "未使用。", "produceExamEffectIds": "未使用。",
     "produceEffectTriggerCount": "培育中发动次数。", "produceEffectTriggerInterval": "未使用。"})
add("ProduceCustomizeItemRelationship", "定制道具树的父子边。", {"parentProduceCustomizeItemId": "→ ProduceCustomizeItem。", "childProduceCustomizeItemId": "→ ProduceCustomizeItem。"})
add("MemoryAbility", "メモリー的アビリティ（575）：指向 ProduceSkill(p_memory_skill)，带评价分与可用剧本系列；isUniqueActivation=重複発動不可。",
    {"skillId": "→ ProduceSkill。", "produceGroupIds": "→ ProduceGroup 可用系列。", "isUniqueActivation": "同名只发动一次。"})
add("MemoryGift", "（备注）赠送的固定メモリー（新手/活动），含卡、アビリティ、三维。")
add("ProduceEffectIcon", "（备注）ProduceEffectType → 图标资源。")
