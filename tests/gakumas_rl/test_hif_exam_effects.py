"""H.I.F（2026-05）新增 ProduceExamEffectType 的规则回归测试。

覆盖：ExamStatusEnchantEncore（再演）、ExamGimmickEnthusiastic（熱意）、ExamLessonDependStamina、
ExamMultipleEnthusiasticLesson、ExamFullPowerLessonMultipleAdditive（全力強化）、
ExamConcentrationLessonMultipleAdditive（強気強化）、ExamLessonBuffAdditiveFix、ExamAggressiveAdditiveFix、
ExamForcePlayCardSearchWithCost，以及效果器注册表的严格模式。语义依据见 docs/rules/hif_exam_effects.md。
"""

from __future__ import annotations

import math

from typing import Any

import pytest

from gakumas_rl.repository.master_data import MasterDataRepository
from gakumas_rl.simulation.exam.effects import EXAM_EFFECT_REGISTRY, STRICT_EFFECTS_ENV, UnknownExamEffectTypeError
from gakumas_rl.simulation.exam.effects import fallback as fallback_module
from gakumas_rl.simulation.exam.ids import ExamEffect, ExamPhase
from gakumas_rl.idol_config import build_idol_loadout
from gakumas_rl.simulation.exam.runtime import ExamRuntime, RuntimeCard



def _sample_loadout(repository: MasterDataRepository, scenario, idol_card_id: str = 'i_card-amao-1-000'):
    """构造一个稳定的默认偶像编成（与 test_rules 保持一致）。"""

    return build_idol_loadout(repository, scenario, idol_card_id, producer_level=35, idol_rank=4, dearness_level=10)


def _sample_audition_row_selector(repository: MasterDataRepository, scenario, loadout) -> str | None:
    """为测试构造一个稳定的 battle row selector（与 test_rules 保持一致）。"""

    rows = repository.audition_rows(
        scenario,
        scenario.default_stage,
        audition_difficulty_id=loadout.stat_profile.audition_difficulty_id,
    )
    if not rows:
        return None
    row = rows[0]
    return f"{str(row.get('id') or '')}:{int(row.get('number') or 0)}"


def _sample_runtime(seed: int = 7, **runtime_kwargs: Any) -> ExamRuntime:
    """构造一个可直接调用内部运行时方法的考试实例（与 test_rules 保持一致）。"""

    repository = MasterDataRepository()
    scenario = repository.build_scenario('produce-005')
    loadout = runtime_kwargs.pop('loadout', _sample_loadout(repository, scenario))
    runtime = ExamRuntime(
        repository,
        scenario,
        loadout=loadout,
        seed=seed,
        audition_row_id=runtime_kwargs.pop('audition_row_id', _sample_audition_row_selector(repository, scenario, loadout)),
        **runtime_kwargs,
    )
    runtime.reset()
    return runtime


def _first_exam_effect(repository: MasterDataRepository, effect_type: str, **conditions: int) -> dict[str, Any]:
    """按效果类型和简单字段过滤主数据里的第一条考试效果。"""

    for row in repository.load_table('ProduceExamEffect').rows:
        if str(row.get('effectType') or '') != effect_type:
            continue
        if all(int(row.get(key) or 0) == expected for key, expected in conditions.items()):
            return row
    raise AssertionError(f'Effect not found: {effect_type} {conditions}')


def _effect_row(repository: MasterDataRepository, effect_id: str) -> dict[str, Any]:
    """按 id 取一条考试效果行。"""

    row = repository.exam_effect_map.get(effect_id)
    if row is None:
        raise AssertionError(f'Effect not found: {effect_id}')
    return row


def _make_runtime(seed: int = 7, **kwargs: Any) -> ExamRuntime:
    """构造一个已 reset、可直接调用内部方法的考试实例。"""

    return _sample_runtime(seed=seed, **kwargs)


def _stub_card(
    runtime: ExamRuntime,
    card_id: str,
    *,
    effect_ids: list[str],
    stamina: float = 0.0,
    force_stamina: float = 0.0,
    move_position: str = 'ProduceCardMovePositionType_Grave',
    zone: str = 'hand',
) -> RuntimeCard:
    """向指定区域塞入一张只含给定出牌效果的测试卡。"""

    base_card: dict[str, Any] = {
        'id': card_id,
        'upgradeCount': 0,
        'name': card_id,
        'rarity': 'ProduceCardRarity_Ssr',
        'category': 'ProduceCardCategory_MentalSkill',
        'planType': 'ProducePlanType_Common',
        'stamina': stamina,
        'forceStamina': force_stamina,
        'costType': 'ExamCostType_Unknown',
        'costValue': 0,
        'playMovePositionType': move_position,
        'playProduceExamTriggerId': '',
        'playEffects': [{'produceExamEffectId': effect_id, 'produceExamTriggerId': ''} for effect_id in effect_ids],
        'effectGroupIds': [],
    }
    card = RuntimeCard(uid=runtime._next_uid(), card_id=card_id, upgrade_count=0, base_card=base_card)
    getattr(runtime, zone).append(card)
    return card


def _clear_zones(runtime: ExamRuntime) -> None:
    """清空手牌/牌堆/弃牌/保留，避免样例卡组的随机效果干扰断言。"""

    runtime.hand.clear()
    runtime.grave.clear()
    runtime.hold.clear()
    runtime.lost.clear()
    runtime.deck.clear()


# ---------------------------------------------------------------------------
# 注册表覆盖 / 严格模式
# ---------------------------------------------------------------------------


def test_every_master_effect_type_has_a_real_handler() -> None:
    """主数据里出现的所有 effectType 都必须有精确或前缀效果器，不能靠兜底静默吸收。"""

    repository = MasterDataRepository()
    effect_types = {
        str(row.get('effectType') or '')
        for row in repository.load_table('ProduceExamEffect').rows
        if row.get('effectType') and row.get('effectType') != ExamEffect.UNKNOWN
    }
    missing = sorted(effect_type for effect_type in effect_types if not EXAM_EFFECT_REGISTRY.is_registered(effect_type))
    assert missing == [], f'以下 effectType 仍然只能走兜底：{missing}'


def test_hif_effect_types_are_registered_exactly() -> None:
    """九个 H.I.F 新增类型都应精确命中效果器。"""

    for effect_type in (
        ExamEffect.STATUS_ENCHANT_ENCORE,
        ExamEffect.GIMMICK_ENTHUSIASTIC,
        ExamEffect.LESSON_DEPEND_STAMINA,
        ExamEffect.MULTIPLE_ENTHUSIASTIC_LESSON,
        ExamEffect.FULL_POWER_LESSON_MULTIPLE_ADDITIVE,
        ExamEffect.CONCENTRATION_LESSON_MULTIPLE_ADDITIVE,
        ExamEffect.LESSON_BUFF_ADDITIVE_FIX,
        ExamEffect.AGGRESSIVE_ADDITIVE_FIX,
        ExamEffect.FORCE_PLAY_CARD_SEARCH_WITH_COST,
    ):
        assert EXAM_EFFECT_REGISTRY.is_registered(effect_type), effect_type


def test_strict_mode_raises_on_unknown_effect_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """GAKUMAS_STRICT_EFFECTS=1 时未知类型直接抛错；未开启时走兜底挂成持续效果并记录类型。"""

    runtime = _make_runtime(seed=11)
    bogus = {'id': 'test-bogus', 'effectType': 'ProduceExamEffectType_ExamBogusFutureType', 'effectValue1': 1, 'effectTurn': 2}

    monkeypatch.setenv(STRICT_EFFECTS_ENV, '1')
    with pytest.raises(UnknownExamEffectTypeError):
        runtime._apply_exam_effect(bogus, source='test')
    assert not any(item.effect.get('id') == 'test-bogus' for item in runtime.active_effects)

    monkeypatch.setenv(STRICT_EFFECTS_ENV, '0')
    runtime._apply_exam_effect(bogus, source='test')
    assert any(item.effect.get('id') == 'test-bogus' for item in runtime.active_effects)
    assert 'ProduceExamEffectType_ExamBogusFutureType' in fallback_module.UNKNOWN_EFFECT_TYPES_SEEN


# ---------------------------------------------------------------------------
# 打分类：ExamLessonDependStamina / ExamMultipleEnthusiasticLesson
# ---------------------------------------------------------------------------


def test_lesson_depend_stamina_uses_current_stamina_ratio() -> None:
    """「体力の 800% 分パラメータ上昇」= ceil(当前体力 × 8)，参照当前体力而不是最大体力。"""

    runtime = _make_runtime(seed=13)
    effect = _effect_row(runtime.repository, 'e_effect-exam_lesson_depend_stamina-8000-01')
    assert effect['effectType'] == ExamEffect.LESSON_DEPEND_STAMINA

    runtime.stamina = 13.0
    assert runtime._resolve_lesson_effect_value(effect) == 13.0 * 8

    runtime.stamina = 0.0
    assert runtime._resolve_lesson_effect_value(effect) == 0.0

    effect_1200 = _effect_row(runtime.repository, 'e_effect-exam_lesson_depend_stamina-12000-01')
    runtime.stamina = 7.0
    assert runtime._resolve_lesson_effect_value(effect_1200) == 84.0


def test_multiple_enthusiastic_lesson_applies_enthusiasm_twice() -> None:
    """「パラメータ+3（熱意効果を 2 倍適用）」= 3 + 熱意 × (1 + 1000/1000)。"""

    runtime = _make_runtime(seed=17)
    effect = _effect_row(runtime.repository, 'e_effect-exam_multiple_enthusiastic_lesson-0003-1000-01')
    assert effect['effectType'] == ExamEffect.MULTIPLE_ENTHUSIASTIC_LESSON

    runtime.resources['enthusiastic'] = 0.0
    assert runtime._resolve_lesson_effect_value(effect) == 3.0

    runtime.resources['enthusiastic'] = 4.0
    assert runtime._resolve_lesson_effect_value(effect) == 3.0 + 4.0 * 2

    plain = _first_exam_effect(runtime.repository, ExamEffect.LESSON_FIX, effectValue1=3)
    assert runtime._resolve_lesson_effect_value(plain) == 3.0 + 4.0


# ---------------------------------------------------------------------------
# 指针强化：ExamFullPowerLessonMultipleAdditive / ExamConcentrationLessonMultipleAdditive
# ---------------------------------------------------------------------------


def test_full_power_lesson_multiple_additive_raises_full_power_multiplier() -> None:
    """全力強化 +25%：全力倍率 3.0 → 3.25；非全力指针下不生效。"""

    runtime = _make_runtime(seed=19)
    repository = runtime.repository
    lesson = _first_exam_effect(repository, ExamEffect.LESSON_FIX, effectValue1=10)
    additive = _effect_row(repository, 'e_effect-exam_full_power_lesson_multiple_additive-0250-inf')
    base_multiple = float(runtime.exam_setting['examFullPowerLessonValueMultiplePermil']) / 1000.0

    runtime._apply_exam_effect(additive, source='enchant:test')
    assert runtime._resolve_lesson_effect_value(lesson) == 10.0  # 尚未进入全力

    runtime._enter_full_power()
    assert runtime.stance == 'full_power'
    # 分数管线每步向上取整：10 × 3.25 = 32.5 → 33
    assert runtime._resolve_lesson_effect_value(lesson) == math.ceil(10.0 * (base_multiple + 0.25))


def test_full_power_lesson_multiple_additive_with_turns_decays() -> None:
    """全力強化 +20%（4ターン）按回合衰减，到期后倍率回到基础值。"""

    runtime = _make_runtime(seed=23)
    repository = runtime.repository
    lesson = _first_exam_effect(repository, ExamEffect.LESSON_FIX, effectValue1=10)
    additive = _effect_row(repository, 'e_effect-exam_full_power_lesson_multiple_additive-0200-04')
    base_multiple = float(runtime.exam_setting['examFullPowerLessonValueMultiplePermil']) / 1000.0

    runtime.turn = 1
    runtime._apply_exam_effect(additive, source='enchant:test')
    runtime._enter_full_power()
    assert runtime._resolve_lesson_effect_value(lesson) == pytest.approx(10.0 * (base_multiple + 0.2))
    timed = next(item for item in runtime.active_effects if item.effect.get('id') == additive['id'])
    assert timed.remaining_turns == 4

    # ターン経過減免：第 2 回合不递减，第 3～6 回合各减 1，第 6 回合开始时到期
    runtime.turn = 2
    runtime._decay_turn_effects()
    assert timed.remaining_turns == 4
    for next_turn in range(3, 7):
        runtime.turn = next_turn
        runtime._decay_turn_effects()
    assert not any(item.effect.get('id') == additive['id'] for item in runtime.active_effects)
    assert runtime._resolve_lesson_effect_value(lesson) == pytest.approx(10.0 * base_multiple)


def test_concentration_lesson_multiple_additive_raises_concentration_multiplier() -> None:
    """強気強化 +35%：強気 1 段 ×2.0 → ×2.35，2 段 ×2.5 → ×2.85；两条强化叠加为 +95%。"""

    runtime = _make_runtime(seed=29)
    repository = runtime.repository
    lesson = _first_exam_effect(repository, ExamEffect.LESSON_FIX, effectValue1=10)
    concentration = _first_exam_effect(repository, ExamEffect.CONCENTRATION, effectValue1=1)
    additive_35 = _effect_row(repository, 'e_effect-exam_concentration_lesson_multiple_additive-0350-inf')
    additive_60 = _effect_row(repository, 'e_effect-exam_concentration_lesson_multiple_additive-0600-inf')
    stage1 = float(runtime.exam_setting['examConcentrationLessonValueMultiplePermil1']) / 1000.0
    stage2 = float(runtime.exam_setting['examConcentrationLessonValueMultiplePermil2']) / 1000.0

    runtime._apply_exam_effect(additive_35, source='enchant:test')
    assert runtime._resolve_lesson_effect_value(lesson) == 10.0  # 中立指针不生效

    runtime._apply_exam_effect(concentration, source='test')
    assert runtime._resolve_lesson_effect_value(lesson) == math.ceil(10.0 * (stage1 + 0.35))

    runtime._apply_exam_effect(concentration, source='test')
    assert runtime.stance_level == 2
    assert runtime._resolve_lesson_effect_value(lesson) == math.ceil(10.0 * (stage2 + 0.35))

    runtime._apply_exam_effect(additive_60, source='enchant:test')
    assert runtime._resolve_lesson_effect_value(lesson) == math.ceil(10.0 * (stage2 + 0.95))


# ---------------------------------------------------------------------------
# 增加量追加（固定值）vs 增加量増加（千分比）
# ---------------------------------------------------------------------------


def test_lesson_buff_additive_fix_adds_flat_amount_to_concentration_gain() -> None:
    """集中増加量追加 +2（2ターン）：每次集中获得固定 +2；集中増加量増加 +100% 再按比例放大。"""

    runtime = _make_runtime(seed=31)
    repository = runtime.repository
    gain = _first_exam_effect(repository, ExamEffect.LESSON_BUFF, effectValue1=3)
    fix = _effect_row(repository, 'e_effect-exam_lesson_buff_additive_fix-0002-02')
    assert fix['effectType'] == ExamEffect.LESSON_BUFF_ADDITIVE_FIX

    runtime.resources['lesson_buff'] = 0.0
    runtime._apply_exam_effect(gain, source='card')
    assert runtime.resources['lesson_buff'] == 3.0

    runtime._apply_exam_effect(fix, source='card')
    runtime._apply_exam_effect(gain, source='card')
    assert runtime.resources['lesson_buff'] == 3.0 + (3.0 + 2.0)

    percent = {'id': 'test-lesson-buff-additive-100', 'effectType': ExamEffect.LESSON_BUFF_ADDITIVE, 'effectValue1': 1000, 'effectTurn': -1}
    runtime._apply_exam_effect(percent, source='card')
    runtime._apply_exam_effect(gain, source='card')
    assert runtime.resources['lesson_buff'] == 8.0 + (3.0 + 2.0) * 2.0


def test_lesson_buff_additive_percent_is_permil_not_flat() -> None:
    """主数据 ExamLessonBuffAdditive 的 effectValue1 是千分比（250 = +25%），不能当固定值加。"""

    runtime = _make_runtime(seed=37)
    repository = runtime.repository
    gain = _first_exam_effect(repository, ExamEffect.LESSON_BUFF, effectValue1=4)
    additive = _effect_row(repository, 'e_effect-exam_lesson_buff_additive-0250-inf')

    runtime.resources['lesson_buff'] = 0.0
    runtime._apply_exam_effect(additive, source='card')
    runtime._apply_exam_effect(gain, source='card')
    assert runtime.resources['lesson_buff'] == pytest.approx(4.0 * 1.25)


def test_aggressive_additive_fix_adds_flat_amount_to_motivation_gain() -> None:
    """やる気増加量追加 +1（2ターン）：每次やる気获得固定 +1，并按回合到期。"""

    runtime = _make_runtime(seed=41)
    repository = runtime.repository
    gain = _first_exam_effect(repository, ExamEffect.CARD_PLAY_AGGRESSIVE, effectValue1=3)
    fix = _effect_row(repository, 'e_effect-exam_aggressive_additive_fix-0001-02')
    assert fix['effectType'] == ExamEffect.AGGRESSIVE_ADDITIVE_FIX

    runtime.turn = 1
    runtime.resources['aggressive'] = 0.0
    runtime._apply_exam_effect(fix, source='card')
    runtime._apply_exam_effect(gain, source='card')
    assert runtime.resources['aggressive'] == 4.0

    percent = _effect_row(repository, 'e_effect-exam_aggressive_additive-0500-03')
    runtime._apply_exam_effect(percent, source='card')
    runtime._apply_exam_effect(gain, source='card')
    assert runtime.resources['aggressive'] == pytest.approx(4.0 + (3.0 + 1.0) * 1.5)

    # ターン経過減免：第 2 回合不递减，第 3 回合剩 1，第 4 回合开始时到期
    runtime.turn = 2
    runtime._decay_turn_effects()
    assert any(item.effect.get('id') == fix['id'] for item in runtime.active_effects)
    runtime.turn = 3
    runtime._decay_turn_effects()
    runtime.turn = 4
    runtime._decay_turn_effects()
    assert not any(item.effect.get('id') == fix['id'] for item in runtime.active_effects)


def test_review_additive_is_a_timed_percent_modifier() -> None:
    """好印象増加量増加 +50%（2ターン）是持续修饰而不是即时 +500 好印象。"""

    runtime = _make_runtime(seed=43)
    repository = runtime.repository
    additive = _effect_row(repository, 'e_effect-exam_review_additive-0500-02')
    gain = _first_exam_effect(repository, ExamEffect.REVIEW, effectValue1=2)

    runtime.resources['review'] = 0.0
    runtime._apply_exam_effect(additive, source='card')
    assert runtime.resources['review'] == 0.0
    runtime._apply_exam_effect(gain, source='card')
    assert runtime.resources['review'] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# 热意：ExamGimmickEnthusiastic
# ---------------------------------------------------------------------------


def test_gimmick_enthusiastic_effect_gains_enthusiasm_with_modifiers() -> None:
    """ExamGimmickEnthusiastic 作为效果行时按 effectValue1 加热意，并套用 熱意追加/熱意増加 修饰。"""

    runtime = _make_runtime(seed=47)
    repository = runtime.repository
    effect = {'id': 'test-enthusiastic-3', 'effectType': ExamEffect.GIMMICK_ENTHUSIASTIC, 'effectValue1': 3}

    runtime.resources['enthusiastic'] = 0.0
    runtime._apply_exam_effect(effect, source='card')
    assert runtime.resources['enthusiastic'] == 3.0

    runtime._apply_exam_effect(_effect_row(repository, 'e_effect-exam_enthusiastic_additive-0002-inf'), source='card')
    runtime._apply_exam_effect(effect, source='card')
    assert runtime.resources['enthusiastic'] == 3.0 + (3.0 + 2.0)


# ---------------------------------------------------------------------------
# 强制使用：ExamForcePlayCardSearch / ExamForcePlayCardSearchWithCost
# ---------------------------------------------------------------------------


def test_force_play_card_search_with_cost_pays_cost_and_skips_unaffordable_cards() -> None:
    """「除外以外のスキルカードを1枚選択し、コストを消費して使用」：只选费用可支付的卡，并实际扣体力。"""

    runtime = _make_runtime(seed=53)
    repository = runtime.repository
    effect = _effect_row(repository, 'e_effect-exam_force_play_card_search_with_cost-p_card_search-not_lost-select-1_1')
    assert effect['effectType'] == ExamEffect.FORCE_PLAY_CARD_SEARCH_WITH_COST
    _clear_zones(runtime)
    runtime.resources['block'] = 0.0
    runtime.stamina = 5.0
    runtime.resources['review'] = 0.0

    expensive = _stub_card(runtime, 'stub-expensive', effect_ids=['e_effect-exam_review-0002'], stamina=9.0, zone='hand')
    cheap = _stub_card(runtime, 'stub-cheap', effect_ids=['e_effect-exam_review-0002'], stamina=3.0, zone='grave')
    play_limit_before = runtime.play_limit
    play_count_before = runtime.turn_counters['play_count']

    runtime._apply_exam_effect(effect, source='enchant:test')

    assert runtime.resources['review'] == 2.0
    assert runtime.stamina == 2.0
    assert cheap not in runtime.grave and cheap in runtime.grave or cheap in runtime.grave  # 打出后回到弃牌
    assert expensive in runtime.hand
    # 效果驱动的使用不占用本回合出牌窗口
    assert runtime.play_limit - play_limit_before == runtime.turn_counters['play_count'] - play_count_before == 1
    assert runtime.current_card is None


def test_force_play_card_search_with_cost_does_nothing_when_unaffordable() -> None:
    """候选全部付不起费用时不发动。"""

    runtime = _make_runtime(seed=59)
    effect = _effect_row(runtime.repository, 'e_effect-exam_force_play_card_search_with_cost-p_card_search-not_lost-select-1_1')
    _clear_zones(runtime)
    runtime.resources['block'] = 0.0
    runtime.stamina = 2.0
    runtime.resources['review'] = 0.0
    _stub_card(runtime, 'stub-expensive', effect_ids=['e_effect-exam_review-0002'], stamina=9.0, zone='hand')

    runtime._apply_exam_effect(effect, source='enchant:test')
    assert runtime.resources['review'] == 0.0
    assert runtime.stamina == 2.0


def test_force_play_card_search_without_cost_is_free() -> None:
    """ExamForcePlayCardSearch（コストを消費せず使用）不扣体力，但效果照常结算。"""

    runtime = _make_runtime(seed=61)
    effect = _effect_row(runtime.repository, 'e_effect-exam_force_play_card_search-p_card_search-hold-all-0_0')
    _clear_zones(runtime)
    runtime.stamina = 5.0
    runtime.resources['review'] = 0.0
    _stub_card(runtime, 'stub-held', effect_ids=['e_effect-exam_review-0002'], stamina=9.0, zone='hold')

    runtime._apply_exam_effect(effect, source='enchant:test')
    assert runtime.resources['review'] == 2.0
    assert runtime.stamina == 5.0
    assert not runtime.hold


# ---------------------------------------------------------------------------
# 再演：ExamStatusEnchantEncore
# ---------------------------------------------------------------------------


def _play_stub_card_with_encore(runtime: ExamRuntime, encore_effect_id: str, *, stamina: float = 4.0) -> RuntimeCard:
    """把一张带再演的测试卡从手牌正常打出，并返回它。"""

    card = _stub_card(
        runtime,
        'stub-encore',
        effect_ids=['e_effect-exam_review-0002', encore_effect_id],
        stamina=stamina,
        move_position='ProduceCardMovePositionType_Lost',
        zone='hand',
    )
    runtime._play_card(card)
    return card


def test_encore_binds_to_the_played_card_and_refires_it_for_free_once_per_turn() -> None:
    """再演（2ターンごとに、体力が80%以上の場合、2回まで・ターン内1回まで）：绑定自身、免费再使用、同回合只发动一次、次数用尽后移除。"""

    runtime = _make_runtime(seed=67)
    repository = runtime.repository
    encore_id = 'e_effect-exam_status_enchant_encore-0001-02-inf-enchant-p_card-01-ido-3_202-enc02'
    encore = _effect_row(repository, encore_id)
    assert encore['effectType'] == ExamEffect.STATUS_ENCHANT_ENCORE
    _clear_zones(runtime)
    runtime.resources['block'] = 0.0
    runtime.max_stamina = 30.0
    runtime.stamina = 30.0
    runtime.resources['review'] = 0.0
    runtime.turn = 1

    card = _play_stub_card_with_encore(runtime, encore_id)
    assert runtime.resources['review'] == 2.0
    assert runtime.stamina == 26.0
    assert card in runtime.lost

    enchants = [item for item in runtime.active_enchants if item.enchant_id == 'enchant-p_card-01-ido-3_202-enc02']
    assert len(enchants) == 1
    enchant = enchants[0]
    assert enchant.bound_card_uid == card.uid
    assert enchant.once_per_turn is True
    assert enchant.remaining_count == 2
    assert enchant.remaining_turns is None

    # 第 1 回合：不是 2 的倍数，不发动
    runtime._dispatch_interval_phase(ExamPhase.TURN_INTERVAL, runtime.turn)
    assert runtime.resources['review'] == 2.0

    # 第 2 回合但体力 < 80%：不发动
    runtime.turn = 2
    runtime.stamina = 20.0
    runtime._dispatch_interval_phase(ExamPhase.TURN_INTERVAL, runtime.turn)
    assert runtime.resources['review'] == 2.0

    # 第 2 回合、体力 ≥ 80%：免费再使用自身（体力不变、效果结算、回到除外）
    runtime.stamina = 26.0
    runtime._dispatch_interval_phase(ExamPhase.TURN_INTERVAL, runtime.turn)
    assert runtime.resources['review'] == 4.0
    assert runtime.stamina == 26.0
    assert card in runtime.lost
    assert enchant.remaining_count == 1

    # 同一回合内再触发：ターン内1回まで
    runtime._dispatch_interval_phase(ExamPhase.TURN_INTERVAL, runtime.turn)
    assert runtime.resources['review'] == 4.0
    assert enchant.remaining_count == 1

    runtime.turn = 3
    runtime._dispatch_interval_phase(ExamPhase.TURN_INTERVAL, runtime.turn)
    assert runtime.resources['review'] == 4.0

    runtime.turn = 4
    runtime._dispatch_interval_phase(ExamPhase.TURN_INTERVAL, runtime.turn)
    assert runtime.resources['review'] == 6.0
    assert not any(item.enchant_id == 'enchant-p_card-01-ido-3_202-enc02' for item in runtime.active_enchants)

    runtime.turn = 6
    runtime._dispatch_interval_phase(ExamPhase.TURN_INTERVAL, runtime.turn)
    assert runtime.resources['review'] == 6.0


def test_encore_end_turn_remaining_turn_trigger_fires_at_exact_threshold() -> None:
    """再演「残り3ターン以内のターン終了時」：剩余恰好 3 回合时回合结束发动。

    注意：上游触发器求值器（triggers/field_status.py）把 RemainingTurn 当作「≥ 阈值」处理，
    与卡面「以内（≤）」相反；这里只在两种解释都成立的 remaining == 3 处断言，见 docs/rules/hif_exam_effects.md。
    """

    runtime = _make_runtime(seed=68)
    encore_id = 'e_effect-exam_status_enchant_encore-0001-03-inf-enchant-p_card-03-ido-3_197-enc01'
    _clear_zones(runtime)
    runtime.resources['block'] = 0.0
    runtime.stamina = 20.0
    runtime.resources['review'] = 0.0
    runtime.max_turns = 6
    runtime.turn = 4  # remaining = 3

    card = _play_stub_card_with_encore(runtime, encore_id)
    assert runtime.resources['review'] == 2.0
    runtime._dispatch_phase(ExamPhase.END_TURN, phase_value=runtime.turn)
    assert runtime.resources['review'] == 4.0
    assert runtime.stamina == 16.0
    assert card in runtime.lost
    enchant = next(item for item in runtime.active_enchants if item.enchant_id == 'enchant-p_card-03-ido-3_197-enc01')
    assert enchant.remaining_count == 2


def test_encore_is_only_attached_on_first_use() -> None:
    """再使用自身时会再次走到再演效果，但不能重复挂载/刷新次数。"""

    runtime = _make_runtime(seed=71)
    encore_id = 'e_effect-exam_status_enchant_encore-0001-03-inf-enchant-p_card-03-ido-3_197-enc01'
    _clear_zones(runtime)
    runtime.resources['block'] = 0.0
    runtime.stamina = 20.0
    runtime.max_turns = 6
    runtime.turn = 4

    _play_stub_card_with_encore(runtime, encore_id)
    runtime._dispatch_phase(ExamPhase.END_TURN, phase_value=runtime.turn)
    enchants = [item for item in runtime.active_enchants if item.enchant_id == 'enchant-p_card-03-ido-3_197-enc01']
    assert len(enchants) == 1
    assert enchants[0].remaining_count == 2


def test_encore_without_card_context_is_ignored() -> None:
    """没有出牌上下文（例如饮料/测试直接施加）时再演无法绑定，不应挂出无主附魔。"""

    runtime = _make_runtime(seed=73)
    encore = _effect_row(runtime.repository, 'e_effect-exam_status_enchant_encore-0001-03-inf-enchant-p_card-03-ido-3_197-enc01')
    before = len(runtime.active_enchants)
    runtime.current_card = None
    runtime._apply_exam_effect(encore, source='test')
    assert len(runtime.active_enchants) == before


def test_encore_after_card_play_trigger_uses_acting_card() -> None:
    """再演「燃え盛る青い炎使用後、自身を再使用」：ExamCardPlayAfter 触发器需要拿到刚打出的那张卡。"""

    runtime = _make_runtime(seed=79)
    repository = runtime.repository
    encore_id = 'e_effect-exam_status_enchant_encore-0001-02-inf-enchant-p_card-02-ido-3_198-enc01'
    _clear_zones(runtime)
    runtime.resources['block'] = 0.0
    runtime.stamina = 30.0
    runtime.resources['review'] = 0.0
    runtime.turn = 1

    card = _play_stub_card_with_encore(runtime, encore_id)
    assert runtime.resources['review'] == 2.0

    flame_row = repository.exam_effect_map  # 仅用于确认主数据可用
    assert flame_row is not None
    other = _stub_card(runtime, 'stub-other', effect_ids=[], zone='hand')
    runtime._play_card(other)
    assert runtime.resources['review'] == 2.0  # 不是燃え盛る青い炎，不触发

    flame_card = RuntimeCard(
        uid=runtime._next_uid(),
        card_id='p_card-02-ido-3_211',
        upgrade_count=0,
        base_card=dict(repository.load_table('ProduceCard').by_id['p_card-02-ido-3_211'][0]),
    )
    runtime.hand.append(flame_card)
    runtime.turn = 2
    runtime._play_card(flame_card)
    assert runtime.resources['review'] == 4.0
    assert card in runtime.lost


def test_encore_aggressive_up_interval_counts_direct_motivation_gains() -> None:
    """再演「直接効果でやる気が5回増加時」：ExamAggressiveUpInterval 按卡牌/饮料带来的やる気增加次数计数。"""

    runtime = _make_runtime(seed=83)
    repository = runtime.repository
    encore_id = 'e_effect-exam_status_enchant_encore-0001-02-inf-enchant-p_card-02-ido-3_201-enc01'
    _clear_zones(runtime)
    runtime.resources['block'] = 0.0
    runtime.stamina = 30.0
    runtime.resources['review'] = 0.0
    runtime.resources['aggressive'] = 0.0
    runtime.turn = 1
    assert 5 in repository.interval_phase_values.get(ExamPhase.AGGRESSIVE_UP_INTERVAL, ())

    _play_stub_card_with_encore(runtime, encore_id)
    gain = _first_exam_effect(repository, ExamEffect.CARD_PLAY_AGGRESSIVE, effectValue1=1)
    for index in range(4):
        runtime._apply_exam_effect(gain, source='card')
        assert runtime.resources['review'] == 2.0, index
    runtime._apply_exam_effect(gain, source='enchant:other')  # 非直接效果不计数
    assert runtime.resources['review'] == 2.0
    runtime._apply_exam_effect(gain, source='card')
    assert runtime.resources['review'] == 4.0
