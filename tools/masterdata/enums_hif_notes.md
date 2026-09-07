### 4.1 H.I.F 在 master 里的落点（解读）

- **剧本定义**：`ProduceGroup` produce_group-003 `ProduceType_HatsuboshiIdolFestival`（limitGrade=Sssss）；`Produce` produce-007『選抜試験』(ProduceSplitType_Selection, 20 周) 与 produce-008『本戦』(ProduceSplitType_Final, 9 周) 互为 `splitPairProduceId`；解锁条件 `cd-hif_selection_produce-unlock_open`（任一偶像亲爱度 Lv27）。`ProduceSetting` p_setting-7/8：休息回复 50%、定制 2 张、Legend 卡 1 张。
- **選抜メモリー**：`Produce.selectionMemoryEmbedProduceCardId` → `ExamContestEmbedProduceCard` exam_contest_embed_produce_card-produce_008（按流派 18 张）；`ProduceSetting.selectionMemoryNeedProduceCardCount`=1。本戦开始时通过 `ProduceSkill(p_memory_skill-common-hatsuboshi_idol_festival-…)`（`produceType=HatsuboshiIdolFestival`，触发 `p_trigger-start_audition-for_hif_memory`）把 `ProduceExamStatusEnchant enchant-p_ef-hif_memory-p_card-…` 挂到试炼里（“試験ごとに、以降1回まで、X 使用後、…”），`MemoryAbility` 有 105 条对应。
- **公開レッスン**：`ProduceStepOpenLesson`（produce_007，主/副参数 + `star` スター性）；`ProduceStepType_OpenLesson{Vocal,Dance,Visual}{Normal,Sp}{,Star}` 12 个周程类型。
- **スター性**：`ResultGradePattern` ResultGradeType_ProduceStar（E=20…S+=1200）；`ProduceEffectType_StarAddition / StarPermilUp`；`ProduceStepAuditionDifficulty.starScoreBonusBaseLine`（本戦 600/800）。
- **本戦试炼**：`ProduceStepAuditionDifficulty` produce-008 两轮（AuditionMid1 rankThreshold 3、AuditionFinal rankThreshold 1），`isStaticNpcScore=true`，NPC 组含 `npc_hif_border`（`ProduceExamBattleNpcMob.isBorder`=合格线）。
- **プリマステラ（一番星）**：`IdolCard.primaStellaConsumptionSetId/idolCardPrimaStellaProduceSkillId/primaStellaAchievementId`（10 张 SSR）→ `IdolCardPrimaStellaProduceSkill` → `ProduceSkill(p_primastella_skill-…-final-…)`：本戦开始时获得专属 Legend 卡 `p_card-0x-ido-100_0xx`（`ProduceCard.originPrimaStellaIdolCardId`）；`TutorialType_PrimaStella`；`MissionType_AbsoluteIdolCardPrimaStellaCount`。
- **育成パネル**：`ProduceGrowthPanelSheet` produce_growth_panel_sheet-hif → `ProduceGrowthPanel` 50 格（`produceSplitType` 区分 選抜/本戦 生效），点数道具 `item-produce-produce_growth_panel_sheet_point-hif`。
- **ADV/演出**：`ProduceSplitAdv`（24）、`ProduceStepTransition.produceIds=[produce-007, produce-008]`、`ProduceStepAuditionMotion` `mot_aud_*-hif-final01-*`、unit REVERSI（`ProduceCharacterUnit`）。
- **描述标签**：`Label_ProduceType_HatsuboshiIdolFestival{,_Selection,_Final}` / `Swap_…`，`ProduceDescriptionProduceType` 模板 `{Label_ProduceType_HatsuboshiIdolFestival_Final}` → “H.I.F本戦専用”。
- **未在 master 中**：フェス回合流程、投票/一番星判定公式、周程排布——需从游戏内/攻略确认。
