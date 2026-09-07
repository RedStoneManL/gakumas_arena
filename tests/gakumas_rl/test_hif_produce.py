"""H.I.F（Hatsuboshi IDOL FESTIVAL）培育外循环的回归测试。

覆盖：主数据驱动的場景装配（produce-007 選抜試験 / produce-008 本戦）、スター性 资源、
新增 ProduceEffectType 处理、本戦 两轮合计与 一番星 判定、選抜試験メモリー 交接，以及
`docs/scenarios/hif.md` §7 / `docs/research/existing_engines.md` §6.1 的評価値公式。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import pytest
import yaml

from gakumas_rl.idol_config import build_idol_loadout
from gakumas_rl.produce_score import (
    HIF_TARGET_RATING_BY_RANK,
    calculate_hif_produce_rating,
    calculate_hif_round1_rating,
    calculate_hif_round2_rating,
    calculate_hif_round2_star_gain,
    get_hif_produce_rank,
)
from gakumas_rl.repository.master_data import (
    HIF_FINAL_PRODUCE_ID,
    HIF_PRODUCE_TYPE,
    HIF_ROUTE_FINAL,
    HIF_ROUTE_SELECTION,
    HIF_SELECTION_PRODUCE_ID,
    MasterDataRepository,
)
from gakumas_rl.simulation.produce.hif import HIF_OPEN_LESSON_ACTION_TYPES, HifSelectionMemory
from gakumas_rl.simulation.produce.runtime import ProduceRuntime

AMAO_R = 'i_card-amao-1-000'
HIF_WAPPEN_ITEM_ID = 'pitem_00-3-265-0'


@pytest.fixture(scope='module')
def repository() -> MasterDataRepository:
    """整个模块共享一份主数据仓库。"""

    return MasterDataRepository()


def _build_runtime(
    repository: MasterDataRepository,
    produce_id: str,
    *,
    seed: int,
    dearness_level: int = 37,
    memory: HifSelectionMemory | None = None,
    weak_rivals: bool = False,
) -> ProduceRuntime:
    """构造一个 HIF 运行时；`weak_rivals=True` 时把对手分数压成 0，便于验证完整日程。"""

    scenario = repository.build_scenario(produce_id)
    loadout = build_idol_loadout(repository, scenario, AMAO_R, producer_level=35, idol_rank=4, dearness_level=dearness_level)
    runtime = ProduceRuntime(repository, scenario, seed=seed, idol_loadout=loadout, hif_selection_memory=memory)
    if weak_rivals:
        original = runtime._simulate_rival_scores

        def _weak(exam_runtime: Any, effective_score: float):
            scores, breakdowns, _rank, multiplier = original(exam_runtime, effective_score)
            for breakdown in breakdowns:
                breakdown['final'] = 0.0
            return [0.0 for _ in scores], breakdowns, 1, multiplier

        runtime._simulate_rival_scores = _weak  # type: ignore[method-assign]
    runtime.reset()
    return runtime


def _run_random_policy(runtime: ProduceRuntime, seed: int, max_steps: int = 300) -> list[dict[str, Any]]:
    """用固定 seed 的随机合法动作策略把培育跑到终止，返回每步日志。"""

    rng = np.random.default_rng(seed)
    history: list[dict[str, Any]] = []
    terminated = False
    while not terminated and len(history) < max_steps:
        candidates = runtime.legal_actions()
        available = [index for index, candidate in enumerate(candidates) if candidate.available]
        assert available, f'no legal action at step={runtime.state["step"]} phase={runtime.pre_audition_phase}'
        index = int(rng.choice(available))
        reward, terminated, info = runtime.step(index)
        assert not info.get('invalid_action'), info
        history.append(
            {
                'step': int(runtime.state['step']),
                'action_type': candidates[index].action_type,
                'label': candidates[index].label,
                'reward': float(reward),
                'info': info,
                'star_quality': float(runtime.state.get('star_quality') or 0.0),
            }
        )
    assert terminated, 'produce did not terminate within max_steps'
    return history


def _audition_steps(history: list[dict[str, Any]]) -> list[int]:
    """从日志里提取每场试验被接受时的步数。"""

    steps: list[int] = []
    for entry in history:
        if entry['action_type'] in {'audition_accept'} or any(key.startswith('audition_') for key in entry['info']):
            if entry['info'].get('pre_audition_phase') == 'weekly' and any(key.startswith('audition_') for key in entry['info']):
                steps.append(entry['step'])
    return steps


# ── 场景装配 ─────────────────────────────────────────────────────────────


def test_build_hif_scenarios_from_master_data(repository: MasterDataRepository) -> None:
    """produce-007 / produce-008 应装配成独立的 HIF 路线，而不是 first_star。"""

    selection = repository.build_scenario(HIF_SELECTION_PRODUCE_ID)
    final = repository.build_scenario(HIF_FINAL_PRODUCE_ID)

    assert selection.route_type == HIF_ROUTE_SELECTION and selection.is_hif
    assert final.route_type == HIF_ROUTE_FINAL and final.is_hif
    assert selection.produce_type == final.produce_type == HIF_PRODUCE_TYPE
    assert selection.produce_split_type == 'ProduceSplitType_Selection'
    assert final.produce_split_type == 'ProduceSplitType_Final'
    assert selection.split_pair_produce_id == HIF_FINAL_PRODUCE_ID
    assert final.split_pair_produce_id == HIF_SELECTION_PRODUCE_ID

    assert selection.steps == 20 and final.steps == 9
    assert selection.action_point_quantity == final.action_point_quantity == 20
    assert selection.parameter_growth_limit == pytest.approx(3000.0)
    assert final.parameter_growth_limit == pytest.approx(3000.0)
    assert selection.drink_limit == final.drink_limit == 3
    assert selection.max_refresh_count == final.max_refresh_count == 0

    assert selection.checkpoint_steps == (7, 13, 20)
    assert final.checkpoint_steps == (7, 9)
    assert selection.audition_sequence == (
        'ProduceStepType_AuditionMid1',
        'ProduceStepType_AuditionMid2',
        'ProduceStepType_AuditionFinal',
    )
    assert final.audition_sequence == ('ProduceStepType_AuditionMid1', 'ProduceStepType_AuditionFinal')

    assert selection.hif is not None and final.hif is not None
    assert [item.rank_threshold for item in selection.hif.auditions] == [2, 2, 2]
    assert [item.rank_threshold for item in final.hif.auditions] == [3, 1]
    assert [item.star_score_bonus_baseline for item in selection.hif.auditions] == [50.0, 200.0, 400.0]
    assert [item.star_score_bonus_baseline for item in final.hif.auditions] == [600.0, 800.0]
    assert [item.turns for item in selection.hif.auditions] == [10, 12, 12]
    assert [item.turns for item in final.hif.auditions] == [9, 12]
    assert all(not item.is_static_npc_score for item in selection.hif.auditions)
    assert all(item.is_static_npc_score for item in final.hif.auditions)
    assert final.hif.interval_step == 8 and selection.hif.interval_step == 0
    assert final.hif.round1_score_multiplier == pytest.approx(1.2)

    for action_type in HIF_OPEN_LESSON_ACTION_TYPES:
        assert action_type in selection.action_types
    assert 'hif_interval' in final.action_types and 'hif_interval' not in selection.action_types
    assert 'lesson_vocal_hard' not in selection.action_types
    assert selection.hif.opening_event_detail_id == 'event-detail-p_story-003-produce-007-opening-1'
    assert set(selection.hif.after_audition_event_detail_ids) == set(selection.audition_sequence)
    assert HIF_SELECTION_PRODUCE_ID in repository.list_supported_scenarios()
    assert HIF_FINAL_PRODUCE_ID in repository.list_supported_scenarios()


def test_non_hif_scenarios_keep_previous_routes(repository: MasterDataRepository) -> None:
    """既有路线不受 HIF 装配影响。"""

    assert repository.build_scenario('produce-001').route_type == 'first_star'
    assert repository.build_scenario('produce-005').route_type == 'nia'
    assert repository.build_scenario('produce-006').checkpoint_steps == ()
    assert repository.build_scenario('produce-006').hif is None


# ── 評価値公式 ───────────────────────────────────────────────────────────


def test_hif_rating_formula_matches_documented_examples() -> None:
    """hif.md §7.2 的 SSS / S4+ 目安 应落在对应等级；分段表与 §6.1 一致。"""

    sss = calculate_hif_produce_rating(
        params=(2000.0, 2000.0, 2000.0),
        star_quality_before_round2=1100.0,
        round1_score=500000.0,
        round2_score=350000.0,
    )
    assert sss['round1_rating'] == 2000
    assert sss['round2_rating'] == 0
    assert sss['round2_star_gain_base'] == 66
    assert sss['round2_star_gain'] == 99
    assert sss['stat_star_rating'] == 20992
    assert sss['rating'] == 20992
    assert sss['rank'] == 'SSS'

    s4_plus = calculate_hif_produce_rating(
        params=(2000.0, 2000.0, 2000.0),
        star_quality_before_round2=1335.0,
        round1_score=700000.0,
        round2_score=1500000.0,
    )
    # Round2 前的スター性按 1110 封顶，R2 分数再换算 +225 → 1335
    assert s4_plus['star_quality_before_round2'] == pytest.approx(1110.0)
    assert s4_plus['round2_star_gain'] == 225
    assert s4_plus['final_star_quality'] == pytest.approx(1335.0)
    assert s4_plus['round1_rating'] == 4000
    assert s4_plus['round2_rating'] == 6000
    assert s4_plus['rating'] == 30012
    assert s4_plus['rank'] == 'S4+'

    # 分段表端点
    assert calculate_hif_round2_star_gain(400000.0) == 75
    assert calculate_hif_round2_star_gain(600000.0) == 120
    assert calculate_hif_round2_star_gain(2000000.0) == 150
    assert calculate_hif_round1_rating(300000.0) == 0
    assert calculate_hif_round1_rating(1000000.0) == 4900
    assert calculate_hif_round1_rating(5000000.0) == 5500
    assert calculate_hif_round2_rating(900000.0) == 1200
    assert calculate_hif_round2_rating(2400000.0) == 7400
    assert calculate_hif_round2_rating(9999999.0) == 7400

    # 参数单项上限 3200
    capped = calculate_hif_produce_rating(params=(5000.0, 0.0, 0.0), star_quality_before_round2=0.0, round1_score=0.0, round2_score=0.0)
    assert capped['parameter_total'] == pytest.approx(3200.0)


def test_hif_rank_thresholds_match_produce_grade_table(repository: MasterDataRepository) -> None:
    """等级阈值应与主数据 ProduceGrade（produce_group-003）一致，并包含 S4+ / S5。"""

    grade_rows = [row for row in repository.load_table('ProduceGrade').rows if str(row.get('produceGroupId') or '') == 'produce_group-003']
    assert grade_rows, 'ProduceGrade rows for produce_group-003 missing'
    thresholds = {str(row.get('grade') or row.get('resultGrade') or ''): int(row.get('threshold') or row.get('value') or 0) for row in grade_rows}
    assert 35000 in thresholds.values()
    assert 30000 in thresholds.values()
    assert HIF_TARGET_RATING_BY_RANK['S5'] == 35000
    assert HIF_TARGET_RATING_BY_RANK['S4+'] == 30000
    assert get_hif_produce_rank(35000) == 'S5'
    assert get_hif_produce_rank(34999) == 'S4+'
    assert get_hif_produce_rank(0) == 'F'


# ── スター性 与 ProduceEffect 处理 ───────────────────────────────────────


def test_hif_star_quality_sources_and_effect_handlers(repository: MasterDataRepository) -> None:
    """親愛度 StarPermilUp、公開レッスン、H.I.Fワッペン StarAddition、ParameterLimitUp、饮料上限。"""

    runtime = _build_runtime(repository, HIF_SELECTION_PRODUCE_ID, seed=5, dearness_level=37)
    assert runtime.hif is not None
    # 亲爱度 37：獲得するスター性 +50%（star_permil_up lv9）、Pドリンク所持上限+1
    assert runtime.state['star_gain_rate'] == pytest.approx(0.5)
    assert runtime._effective_drink_limit() == 4
    # 开场事件发放 H.I.Fワッペン（fireLimit 20）
    wappen = [item for item in runtime.active_produce_items if item.item_id == HIF_WAPPEN_ITEM_ID]
    assert len(wappen) == 1 and wappen[0].spec.fire_limit == 20

    # 公開レッスン：スター性 5 × 1.5 = 7.5 → 7（向下取整，wikiwiki 实测）
    assert runtime.hif.gain_star(5) == 7
    assert runtime.state['star_quality'] == pytest.approx(7.0)

    # スキルカード獲得時 → StarAddition +10 × 1.5 = 15
    before = runtime.state['star_quality']
    runtime._grant_resource('ProduceResourceType_ProduceCard', 'p_card-00-act-0_001', 0)
    assert runtime.state['star_quality'] == pytest.approx(before + 15.0)
    assert wappen[0].fire_count == 1

    # ParameterLimitUp 抬高上限并影响裁剪
    limit_effect = runtime.produce_effects.first('p_effect-parameter_limit_up-0200_0200')
    assert limit_effect is not None
    runtime._apply_produce_effect(limit_effect, source_action_type='hif_growth_panel')
    assert runtime._parameter_growth_limit() == pytest.approx(3200.0)
    runtime._gain_parameter('vocal', 10000.0)
    assert runtime.state['vocal'] == pytest.approx(3200.0)

    # StarPermilUp 叠加
    permil_effect = runtime.produce_effects.first('p_effect-star_permil_up-0050_0050')
    runtime._apply_produce_effect(permil_effect, source_action_type='idol_skill')
    assert runtime.state['star_gain_rate'] == pytest.approx(0.55)

    # スター性 上限：Round2 前最多 1110
    runtime.state['star_quality'] = 1100.0
    runtime.hif.gain_star(1000)
    assert runtime.state['star_quality'] == pytest.approx(1110.0)


def test_hif_open_lesson_candidates_follow_master_table(repository: MasterDataRepository) -> None:
    """公開レッスン 候选的数值应来自 ProduceStepOpenLesson（含成长率与スター性）。"""

    runtime = _build_runtime(repository, HIF_SELECTION_PRODUCE_ID, seed=9, dearness_level=27)
    scenario_hif = runtime.scenario.hif
    assert scenario_hif is not None
    # 关闭 SP 随机，确保读取通常行
    runtime.hif.config = replace(scenario_hif, open_lesson_sp_base_rate=0.0)
    runtime.state['generic_sp_rate_bonus'] = 0.0
    runtime.state['vocal_sp_rate_bonus'] = 0.0
    candidate = runtime._sample_action('lesson_vocal_open_star')
    row = repository.load_table('ProduceStepOpenLesson').first(candidate.source_row_id)
    assert row is not None and candidate.source_row_id.startswith('p_step_open_lesson-produce_007-01-star-')
    assert candidate.stamina_delta == pytest.approx(-6.0)
    assert candidate.star_delta == pytest.approx(20.0)
    expected_main = 50.0 * (1.0 + runtime.state['vocal_growth'])
    assert candidate.stat_deltas[0] == pytest.approx(expected_main)
    assert sum(1 for value in candidate.stat_deltas if value > 0) == 2

    parameter_candidate = runtime._sample_action('lesson_dance_open')
    assert parameter_candidate.star_delta == pytest.approx(5.0)
    assert parameter_candidate.stat_deltas[1] == pytest.approx(60.0 * (1.0 + runtime.state['dance_growth']))


def test_all_master_produce_effect_types_have_a_handler() -> None:
    """ProduceEffect.yaml 中出现的每个 effectType 都应在 runtime 里有显式处理分支。"""

    import gakumas_rl.simulation.produce.runtime as runtime_module

    source = open(runtime_module.__file__, encoding='utf-8').read()
    rows = yaml.safe_load(open('data/raw/gakumasu-diff/ProduceEffect.yaml', encoding='utf-8'))
    effect_types = sorted({str(row.get('produceEffectType') or '') for row in rows if row.get('produceEffectType')})
    missing = [effect_type for effect_type in effect_types if f"'{effect_type}'" not in source]
    assert not missing, f'unhandled ProduceEffectType: {missing}'


# ── 完整流程 ─────────────────────────────────────────────────────────────


def test_hif_selection_full_produce_with_random_policy(repository: MasterDataRepository) -> None:
    """選抜試験：20 步、3 场试验（第 7/13/20 步）、スター性 积累、メモリー 导出。"""

    runtime = _build_runtime(repository, HIF_SELECTION_PRODUCE_ID, seed=11, weak_rivals=True)
    history = _run_random_policy(runtime, seed=11)

    assert runtime.state['step'] == 20
    assert len(runtime.audition_history) == 3
    assert _audition_steps(history) == [7, 13, 20]
    assert [item['stage_type'] for item in runtime.audition_history] == list(runtime.scenario.audition_sequence)
    assert all(item['cleared'] for item in runtime.audition_history)
    assert all(item['hif_star_gain_base'] >= 0 for item in runtime.audition_history)
    # 试验日只允许考前恢复（HIF 试验前回复 50%）
    exam_day_labels = [entry['label'] for entry in history if entry['step'] in {7, 13, 20} and entry['action_type'] == 'refresh']
    assert exam_day_labels and all('試験日' in label for label in exam_day_labels)
    assert runtime.state['star_quality'] > 0.0
    assert runtime.state['star_quality'] <= 1110.0

    summary = runtime.final_summary
    assert summary['route'] == HIF_ROUTE_SELECTION
    assert summary['route_clear'] is True
    assert summary['ending_type'] == 'hif_selection_clear'
    assert summary['produce_result']['formula_source'] == 'hif_selection_partial_formula'
    assert summary['star_quality'] == pytest.approx(runtime.state['star_quality'])

    memory = runtime.export_hif_selection_memory()
    assert memory.source_produce_id == HIF_SELECTION_PRODUCE_ID
    assert memory.star_quality == pytest.approx(runtime.state['star_quality'])
    assert memory.vocal == pytest.approx(runtime.state['vocal'])
    assert len(memory.deck_cards) == len(runtime.deck)
    assert len(memory.selection_scores) == 3
    assert any(item_id == HIF_WAPPEN_ITEM_ID for item_id, _count in memory.produce_item_fire_counts)


def test_hif_final_full_produce_with_selection_memory(repository: MasterDataRepository) -> None:
    """本戦：メモリー 继承 → 6 天准备 → Round1(×1.2) → インターバル → Round2 → 合计分/一番星/評価値。"""

    selection_runtime = _build_runtime(repository, HIF_SELECTION_PRODUCE_ID, seed=21, weak_rivals=True)
    _run_random_policy(selection_runtime, seed=21)
    memory = selection_runtime.export_hif_selection_memory()

    runtime = _build_runtime(repository, HIF_FINAL_PRODUCE_ID, seed=22, memory=memory, weak_rivals=True)
    assert runtime.state['vocal'] == pytest.approx(memory.vocal)
    assert runtime.state['dance'] == pytest.approx(memory.dance)
    assert runtime.state['visual'] == pytest.approx(memory.visual)
    assert runtime.state['star_quality'] == pytest.approx(min(memory.star_quality, 1110.0))
    assert len(runtime.deck) == len(memory.deck_cards)
    carried_wappen = [item for item in runtime.active_produce_items if item.item_id == HIF_WAPPEN_ITEM_ID]
    assert len(carried_wappen) == 1
    assert carried_wappen[0].fire_count == dict(memory.produce_item_fire_counts)[HIF_WAPPEN_ITEM_ID]

    history = _run_random_policy(runtime, seed=22)
    assert runtime.state['step'] == 9
    assert len(runtime.audition_history) == 2
    assert _audition_steps(history) == [7, 9]
    interval_entries = [entry for entry in history if entry['step'] == 8]
    assert interval_entries and all(entry['action_type'].startswith('hif_interval') for entry in interval_entries)

    round1, round2 = runtime.audition_history
    assert round1['hif_round'] == 1 and round2['hif_round'] == 2
    assert round1['hif_round1_adjusted_score'] == pytest.approx(np.floor(round1['exam_score'] * 1.2))
    assert round2['hif_combined_score'] == pytest.approx(round1['hif_round1_adjusted_score'] + round2['exam_score'])
    assert round2['hif_combined_rank'] == 1 and round2['hif_prima_stella'] is True
    assert runtime.state['hif_round1_score'] == pytest.approx(round1['exam_score'])
    assert runtime.state['hif_round2_score'] == pytest.approx(round2['exam_score'])

    summary = runtime.final_summary
    assert summary['route'] == HIF_ROUTE_FINAL
    assert summary['route_clear'] is True
    assert summary['competitive_top1'] is True
    assert summary['ending_type'] == 'hif_prima_stella'
    produce_result = summary['produce_result']
    assert produce_result['formula_source'] == 'hif_community_formula_v1'
    expected = calculate_hif_produce_rating(
        params=(runtime.state['vocal'], runtime.state['dance'], runtime.state['visual']),
        star_quality_before_round2=runtime.state['hif_star_before_round2'],
        round1_score=runtime.state['hif_round1_score'],
        round2_score=runtime.state['hif_round2_score'],
        star_gain_multiplier=1.0 + runtime.state['star_gain_rate'],
        parameter_cap=runtime._parameter_growth_limit(),
    )
    assert produce_result['score'] == pytest.approx(float(expected['rating']))
    assert produce_result['rank'] == expected['rank']


@pytest.mark.parametrize('produce_id, seed', [(HIF_SELECTION_PRODUCE_ID, 101), (HIF_FINAL_PRODUCE_ID, 102)])
def test_hif_random_policy_terminates_cleanly_against_real_rivals(repository: MasterDataRepository, produce_id: str, seed: int) -> None:
    """不削弱对手时也应无异常终止（通常在首场试验失败），并产出一致的终局摘要。"""

    runtime = _build_runtime(repository, produce_id, seed=seed)
    _run_random_policy(runtime, seed=seed)
    summary = runtime.final_summary
    assert summary['route'] in {HIF_ROUTE_SELECTION, HIF_ROUTE_FINAL}
    assert summary['ending_type'] in {'failed', 'hif_selection_clear', 'hif_final_clear', 'hif_prima_stella'}
    assert summary['produce_result']['rank'] in HIF_TARGET_RATING_BY_RANK
    if not summary['route_clear']:
        assert summary['failed_stage_type'] in runtime.scenario.audition_sequence


def test_hif_round2_combined_ranking_uses_round1_multiplier(repository: MasterDataRepository) -> None:
    """一番星 由 floor(R1×1.2)+R2 的合计分决定；对手同样按 R1×1.2 登记。"""

    runtime = _build_runtime(repository, HIF_FINAL_PRODUCE_ID, seed=31)
    hif = runtime.hif
    assert hif is not None
    round1 = hif.adjust_audition_result(
        stage_type='ProduceStepType_AuditionMid1',
        effective_score=400000.0,
        rival_scores=[403161.0, 301182.0],
        rival_character_ids=['jsna', 'hrnm'],
        rank=2,
        rank_threshold=3,
    )
    assert round1['cleared'] is True and round1['rank'] == 2
    assert round1['hif_round1_adjusted_score'] == pytest.approx(480000.0)
    hif.apply_accepted_result({**round1, 'stage_type': 'ProduceStepType_AuditionMid1', 'exam_score': 400000.0, 'cleared': True})
    # Round1 分数换算的スター性：按 ×1.2 后的 480000 查 R2 表 → 93 × 1.5 = 139
    assert round1['hif_star_gain_base'] == calculate_hif_round2_star_gain(480000.0)

    lose = hif.adjust_audition_result(
        stage_type='ProduceStepType_AuditionFinal',
        effective_score=600000.0,
        rival_scores=[598779.0, 437672.0],
        rival_character_ids=['jsna', 'hrnm'],
        rank=1,
        rank_threshold=1,
    )
    # 星南：floor(403161×1.2)=483793 + 598779 = 1082572 > 480000 + 600000
    assert lose['hif_combined_score'] == pytest.approx(1080000.0)
    assert lose['hif_rival_combined_scores'][0] == pytest.approx(1082572.0)
    assert lose['hif_combined_rank'] == 2 and lose['cleared'] is False and lose['hif_prima_stella'] is False

    win = hif.adjust_audition_result(
        stage_type='ProduceStepType_AuditionFinal',
        effective_score=610000.0,
        rival_scores=[598779.0, 437672.0],
        rival_character_ids=['jsna', 'hrnm'],
        rank=1,
        rank_threshold=1,
    )
    assert win['hif_combined_rank'] == 1 and win['cleared'] is True and win['hif_prima_stella'] is True


def test_hif_growth_panel_parameter_limit_applies_only_to_final(repository: MasterDataRepository) -> None:
    """H.I.F ボーナス「全属性上限値」面板只在本戦（ProduceSplitType_Final）生效。"""

    for produce_id, expected_limit in ((HIF_SELECTION_PRODUCE_ID, 3000.0), (HIF_FINAL_PRODUCE_ID, 3200.0)):
        scenario = repository.build_scenario(produce_id)
        assert scenario.hif is not None
        scenario = replace(scenario, hif=replace(scenario.hif, growth_panel_levels={'06': 6, '07': 1, '08': 1}))
        loadout = build_idol_loadout(repository, scenario, AMAO_R, producer_level=35, idol_rank=4, dearness_level=27)
        runtime = ProduceRuntime(repository, scenario, seed=41, idol_loadout=loadout)
        runtime.reset()
        assert runtime._parameter_growth_limit() == pytest.approx(expected_limit)
        # 初期Pポイント 面板（選抜 sheet-07 / 本戦 sheet-08）各 +50
        assert runtime.state['produce_points'] >= 50.0
