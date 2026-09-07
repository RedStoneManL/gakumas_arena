以下关系全部经 id 连接验证（命中率见各表“外键”小节）。

**剧本 → 数值设定**

- `ProduceGroup.produceIds` → `Produce`；`Produce.produceSettingId` → `ProduceSetting`；`Produce.examSettingId` → `ExamSetting`（唯一）。
- `ProduceGrade.produceGroupId`、`ProduceInitialDeck.produceId` → `ExamInitialDeck.produceCardIds` → `ProduceCard`。
- `ProduceStepAuditionDifficulty(id=IdolCard.produceStepAuditionDifficultyId, produceId, stepType, number)` → `ProduceExamBattleConfig` → `ProduceExamBattleScoreConfig`；→ `ProduceExamBattleNpcGroup` → `ProduceExamBattleNpcMob`；→ `ProduceExamGimmickEffectGroup` → `ProduceExamEffect`。
- `ProduceStepLesson.produceStepLessonLevelId` → `ProduceStepLessonLevel`。

**偶像 → 培育起点**

- `IdolCard` → `ProduceCard`(produceCardId / secondProduceCardId)、`ProduceItem`(before/afterProduceItemId)、`ExamInitialDeck`、`ProduceStepAuditionDifficulty`、`IdolCardPotential(+ProduceSkill)`、`IdolCardLevelLimit(+ProduceSkill/+StatusUp)`、`IdolCardPrimaStellaProduceSkill` → `ProduceSkill`。
- `Character` → `IdolCard`、`SupportCard`、`CharacterTrueEndBonus`；`CharacterDearnessLevel.produceSkills[].id` → `ProduceSkill(p_dearness_skill)`。
- `SupportCard` → `SupportCardProduceSkillLevel{Vocal,Dance,Visual,Assist}` → `ProduceSkill(p_support_skill)`；`SupportCard.produceStoryIds` → `ProduceStory`；`ProduceEventSupportCard` → `ProduceStepEventDetail`。
- `MemoryAbility.skillId` → `ProduceSkill(p_memory_skill)`。

**培育外循环效果**

- `ProduceSkill.produceTriggerId1` → `ProduceTrigger`；`.produceEffectId1` → `ProduceEffect`。
- `ProduceItem.skills[].produceItemEffectId` → `ProduceItemEffect` → (`ProduceEffect` | `ProduceExamStatusEnchant`)；`ProduceItem.produceTriggerId` → `ProduceTrigger`。
- `ProduceCustomizeItem.produceEffectIds` → `ProduceEffect`；`ProduceCustomizeItemRelationship` 父子边。
- `ProduceStepEventDetail.produceEffectIds` / `.produceStepEventSuggestionIds` → `ProduceStepEventSuggestion.produceEffectIds|successProduceEffectIds|failProduceEffectIds` → `ProduceEffect`。
- `ProduceGrowthPanel.produceEffectIds` → `ProduceEffect`。
- `ProduceEffect.produceExamStatusEnchantId` → `ProduceExamStatusEnchant`；`.produceCardSearchId` → `ProduceCardSearch`；`.produceRewards[].resourceId` → `ProduceCard|ProduceDrink|ProduceItem`。

**考试内效果**

- `ProduceCard.playEffects[].produceExamEffectId` → `ProduceExamEffect`；`.playEffects[].produceExamTriggerId` / `.playProduceExamTriggerId` → `ProduceExamTrigger`；`.moveProduceExamEffectIds` → `ProduceExamEffect`；`.produceCardStatusEnchantId` → `ProduceCardStatusEnchant`；`.produceCardCustomizeIds` → `ProduceCardCustomize` → `ProduceCardGrowEffect`。
- `ProduceExamEffect.produceExamStatusEnchantId` → `ProduceExamStatusEnchant` → (`ProduceExamTrigger`, `ProduceExamEffect[]`)（可递归）。
- `ProduceExamEffect.chainProduceExamEffectId(s)` → `ProduceExamEffect`（ExamEffectTimer 延迟目标）；`.produceCardGrowEffectIds` → `ProduceCardGrowEffect`；`.produceCardSearchId` → `ProduceCardSearch`；`.targetProduceCardId` → `ProduceCard`。
- `ProduceExamTrigger.produceCardSearchId` / `.fieldStatusProduceCardSearchIds` → `ProduceCardSearch`。
- `ProduceCardStatusEnchant.produceExamTriggerId` → `ProduceExamTrigger`；`.produceCardGrowEffectIds` → `ProduceCardGrowEffect`；`ProduceCardGrowEffect.playProduceExamEffectId` → `ProduceExamEffect`、`.produceCardStatusEnchantId` → `ProduceCardStatusEnchant`、`.playProduceExamTriggerId` → `ProduceExamTrigger`。
- `ProduceCardSearch.produceCardIds` → `ProduceCard`；`.produceCardRandomPoolId|produceCardPoolId` → `ProduceCardPool`（=`ProduceCardRandomPool.id`）；`.effectGroupIds` → `EffectGroup`；`.cardSearchTag` → `ProduceCardTag`。
- `ProduceDrink.produceDrinkEffectIds` → `ProduceDrinkEffect.produceExamEffectId` → `ProduceExamEffect`。
- `ProduceExamAutoTriggerEvaluation.examStatusEnchantProduceExamTriggerId` → `ProduceExamTrigger`；`ProduceExamAutoPlay(Produce)CardEvaluation.produceCardId` → `ProduceCard`。

**描述模板**

- `ProduceDescriptionExamEffect.type`(ProduceExamEffectType) → `produceDescriptionLabelId`/`examProduceDescriptionLabelId` → `ProduceDescriptionLabel` → `produceDescriptionSwapId` → `ProduceDescriptionSwap`。
- 任意行的 `produceDescriptions[].targetId` → `ProduceDescriptionLabel`(Label_/Description_/Convert_) 或 `ProduceCard`/`ProduceItem`；`[].originProduceExamEffectId|originProduceExamTriggerId|originProduceCardStatusEnchantId` 回指来源行。

**条件**

- `Produce/ProduceGroup/ProduceCharacter/ProduceChallengeCharacter/ProduceCardConversion.*ConditionSetId` → `ConditionSet`（DearnessLevel / MainTaskCompleted / ProducerLevel / TimeTerm…）。
- `IdolCardLevelLimit.consumptionSetId`、`IdolCard.primaStellaConsumptionSetId` → `ConsumptionSet` → `Item`。
