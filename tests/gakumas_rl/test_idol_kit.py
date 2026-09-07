"""偶像卡完整套件（才能開花 / ポテンシャル / プリマステラ / メモリー）从主数据解析进 loadout 的测试。

对应 docs/OPEN_ITEMS.md B7、docs/loadouts.md §7。所有断言都对照 data/raw/gakumasu-diff 的原始行：
- `i_card-hmsz-3-016`（秦谷美鈴 VEIL，H.I.F 一番星卡）：ポテンシャル 1 段 再抽選+1 → 4 段 再抽選+2、3 段成长率 vo+40/vi+20、4 段体力+3；
- `i_card-ttmr-3-000`（Luna say maybe）：才能開花 表 `idol_card_level_limit_produce_skill_001` 在 rank2 / rank6 各给一次 SP 発生率技能（Lv1 / Lv2）；
- `memory_gift-20260516-hif-plan1-1`（hski 配布メモリー）：3 条 初期三维+15 アビリティ + ProduceStart 入组卡。
"""
from __future__ import annotations

import numpy as np
import pytest

from gakumas_arena.masterdata import default_dump_dir

pytestmark = pytest.mark.skipif(not default_dump_dir().is_dir(), reason="master data dump not fetched")

PRIMA_IDOL = "i_card-hmsz-3-016"
SENSE_IDOL = "i_card-ttmr-3-000"
HSKI_R = "i_card-hski-1-000"
HIF_GIFT = "memory_gift-20260516-hif-plan1-1"
REROLL_SKILL = "p_idol_skill-common-p_trigger-produce_start-no_description-produce_card_select_reroll_count_up-03-001"
SP_RATE_SKILL = "p_idol_skill-common-p_trigger-produce_start-no_description-lesson_sp_change_rate_permil_addition-03-001"


@pytest.fixture(scope="module")
def repo():
    from gakumas_rl.interfaces.service import get_repository

    return get_repository()


def _scenario(name: str):
    from gakumas_rl.interfaces.service import get_scenario

    return get_scenario(name)


def _build(repo, scenario_id: str, idol: str, **kwargs):
    from gakumas_rl.idol_config import build_idol_loadout

    return build_idol_loadout(repo, _scenario(scenario_id), idol, **kwargs)


def _skills(loadout, source: str):
    return [skill for skill in loadout.produce_skills if skill.source == source]


def test_potential_skills_resolve_for_known_idol(repo):
    """ポテンシャル 技能：1 段解锁 再抽選+1（Lv1），4 段升到 Lv2（+2）；同一技能只保留最高等级。"""
    from gakumas_rl.idol_config import max_potential_level

    assert max_potential_level(repo, PRIMA_IDOL) == 4

    none = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=6)
    assert none.potential_level == 0 and not _skills(none, "potential")

    lv1 = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=6, potential_level=1)
    assert [(s.skill_id, s.level) for s in _skills(lv1, "potential")] == [(REROLL_SKILL, 1)]
    assert _skills(lv1, "potential")[0].effect_ids == ("p_effect-produce_card_select_reroll_count_up-0001_0001",)

    lv4 = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=6, potential_level=4)
    assert [(s.skill_id, s.level) for s in _skills(lv4, "potential")] == [(REROLL_SKILL, 2)]
    assert _skills(lv4, "potential")[0].effect_ids == ("p_effect-produce_card_select_reroll_count_up-0002_0002",)
    assert lv4.metadata["potential_level"] == 4

    # 超过主数据上限时裁到上限
    assert _build(repo, "produce-001", PRIMA_IDOL, potential_level=9).potential_level == 4


def test_initial_stats_change_with_potential_level(repo):
    """ポテンシャル 数值段：3 段成长率（vo +40‰ / vi +20‰）、4 段体力 +3、2 段「初期Pアイテム変更」→ + 版固有道具。"""
    idol_row = repo.load_table("IdolCard").first(PRIMA_IDOL)
    base = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=6, potential_level=0)
    lv2 = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=6, potential_level=2)
    lv3 = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=6, potential_level=3)
    lv4 = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=6, potential_level=4)

    assert base.stat_profile.vocal_growth_rate == pytest.approx(lv2.stat_profile.vocal_growth_rate)
    assert lv3.stat_profile.vocal_growth_rate == pytest.approx(base.stat_profile.vocal_growth_rate + 0.040)
    assert lv3.stat_profile.visual_growth_rate == pytest.approx(base.stat_profile.visual_growth_rate + 0.020)
    assert lv3.stat_profile.dance_growth_rate == pytest.approx(base.stat_profile.dance_growth_rate)
    assert lv3.stat_profile.stamina == pytest.approx(base.stat_profile.stamina)
    assert lv4.stat_profile.stamina == pytest.approx(base.stat_profile.stamina + 3.0)
    # 三维本身不随 ポテンシャル 变化（只有才能開花 加三维）
    assert (lv4.stat_profile.vocal, lv4.stat_profile.dance, lv4.stat_profile.visual) == (
        base.stat_profile.vocal, base.stat_profile.dance, base.stat_profile.visual,
    )
    # 显式 potential_level 时 use_after_item 由 2 段决定；未给 potential_level 时沿用旧规则 idol_rank >= 4
    assert base.use_after_item is False and base.produce_item_id == idol_row["beforeProduceItemId"]
    assert lv2.use_after_item is True and lv2.produce_item_id == idol_row["afterProduceItemId"]
    legacy = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=4)
    assert legacy.potential_level == 0 and legacy.use_after_item is True
    assert _build(repo, "produce-001", PRIMA_IDOL, idol_rank=0, potential_level=4, use_after_item=False).use_after_item is False


def test_potential_growth_rate_reaches_produce_runtime(repo):
    """成长率与体力加成要真正进到 ProduceRuntime 的初始状态。"""
    from gakumas_rl.simulation.produce.runtime import ProduceRuntime

    scenario = _scenario("produce-001")
    base = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=6, potential_level=0)
    lv4 = _build(repo, "produce-001", PRIMA_IDOL, idol_rank=6, potential_level=4)
    rt_base = ProduceRuntime(repo, scenario, idol_loadout=base, seed=1)
    rt_lv4 = ProduceRuntime(repo, scenario, idol_loadout=lv4, seed=1)
    rt_base.reset()
    rt_lv4.reset()
    assert float(rt_lv4.state["max_stamina"]) == pytest.approx(float(rt_base.state["max_stamina"]) + 3.0)
    # 再抽選+2 的技能已注册为 Lv2（且没有 Lv1 残留）
    reroll = [(s.skill_id, s.level) for s in rt_lv4.active_produce_skills if s.skill_id == REROLL_SKILL] or [
        (REROLL_SKILL, 2) if float(rt_lv4.state.get("produce_card_select_reroll_count", 0) or 0) >= 2 else (REROLL_SKILL, 0)
    ]
    assert reroll[0][1] == 2


def test_level_limit_skills_keep_only_highest_level(repo):
    """才能開花：同一技能在 rank2（Lv1）与 rank6（Lv2）各出现一次，ProduceSkill 每级数值是总量，只能注册最高一级。"""
    rank1 = _build(repo, "produce-001", SENSE_IDOL, idol_rank=1)
    rank2 = _build(repo, "produce-001", SENSE_IDOL, idol_rank=2)
    rank6 = _build(repo, "produce-001", SENSE_IDOL, idol_rank=6)
    rank7 = _build(repo, "produce-001", SENSE_IDOL, idol_rank=7)
    assert not _skills(rank1, "level_limit")
    assert [(s.skill_id, s.level) for s in _skills(rank2, "level_limit")] == [(SP_RATE_SKILL, 1)]
    assert [(s.skill_id, s.level) for s in _skills(rank6, "level_limit")] == [(SP_RATE_SKILL, 2)]
    assert _skills(rank6, "level_limit")[0].effect_ids == ("p_effect-lesson_sp_change_rate_permil_addition-0100_0100",)
    # rank 7 再解锁 固有卡カスタマイズ
    rank7_ids = [s.skill_id for s in _skills(rank7, "level_limit")]
    assert any("idol_card_produce_card_customize_enable" in sid for sid in rank7_ids)
    assert [(s.skill_id, s.level) for s in _skills(rank7, "level_limit") if s.skill_id == SP_RATE_SKILL] == [(SP_RATE_SKILL, 2)]
    # 三维/体力 status up 仍按 rank 累加
    assert rank6.stat_profile.vocal > rank1.stat_profile.vocal


def test_prima_stella_skills_resolve_for_hif_idol_only_in_final(repo):
    """プリマステラ：只有 H.I.F 本戦（produce-008）注册「培育开始时获得 一番星 卡」，選抜 / 初 不注册；非一番星卡为 0。"""
    from gakumas_rl.idol_config import max_prima_stella_level

    assert max_prima_stella_level(repo, PRIMA_IDOL) == 1
    assert max_prima_stella_level(repo, SENSE_IDOL) == 0

    final = _build(repo, "produce-008", PRIMA_IDOL, idol_rank=6, prima_stella_level=1)
    prima = _skills(final, "prima_stella")
    assert len(prima) == 1 and final.prima_stella_level == 1
    assert prima[0].skill_id.startswith("p_primastella_skill-common-hatsuboshi_idol_festival-final-")
    assert prima[0].trigger_id == "p_trigger-produce_start"
    assert prima[0].effect_ids == ("p_effect-produce_reward-0001_0001-produce_card-p_card-03-ido-100_047-0",)
    effect = repo.load_table("ProduceEffect").first(prima[0].effect_ids[0])
    assert effect["produceEffectType"] == "ProduceEffectType_ProduceReward"
    assert effect["produceRewards"][0]["resourceId"] == "p_card-03-ido-100_047"

    assert not _skills(_build(repo, "produce-007", PRIMA_IDOL, idol_rank=6, prima_stella_level=1), "prima_stella")
    assert not _skills(_build(repo, "produce-001", PRIMA_IDOL, idol_rank=6, prima_stella_level=1), "prima_stella")
    assert not _skills(_build(repo, "produce-008", PRIMA_IDOL, idol_rank=6, prima_stella_level=0), "prima_stella")
    assert _build(repo, "produce-008", SENSE_IDOL, idol_rank=6, prima_stella_level=1).prima_stella_level == 0


def test_prima_stella_card_is_granted_at_produce_start_in_final(repo):
    """本戦 ProduceRuntime.reset 后卡组里应有 一番星 卡（ProduceReward 效果走现有 produce_start 触发路径）。"""
    from gakumas_rl.simulation.produce.runtime import ProduceRuntime

    scenario = _scenario("produce-008")
    loadout = _build(repo, "produce-008", PRIMA_IDOL, idol_rank=6, prima_stella_level=1)
    runtime = ProduceRuntime(repo, scenario, idol_loadout=loadout, seed=5)
    runtime.reset()
    assert any(str(card.get("id")) == "p_card-03-ido-100_047" for card in runtime.deck)
    plain = ProduceRuntime(repo, scenario, idol_loadout=_build(repo, "produce-008", PRIMA_IDOL, idol_rank=6), seed=5)
    plain.reset()
    assert not any(str(card.get("id")) == "p_card-03-ido-100_047" for card in plain.deck)


def test_memories_resolve_from_master_data(repo):
    """メモリー：MemoryGift id → ProduceMemorySpec；アビリティ → p_memory_skill 培育技能；ProduceStart 卡进初始卡组。"""
    from gakumas_rl.idol_config import build_initial_exam_deck, memory_spec_from_gift
    from gakumas_rl.loadout import ProduceMemoryCardSpec, ProduceMemorySpec

    spec = memory_spec_from_gift(repo, HIF_GIFT)
    assert spec.idol_card_id == HSKI_R and spec.grade == "ResultGrade_Sss"
    assert spec.produce_card == ProduceMemoryCardSpec(card_id="p_card-01-act-2_001", upgrade_count=1)
    assert len(spec.ability_ids) == 3 and (spec.vocal, spec.dance, spec.visual, spec.stamina) == (200, 300, 400, 25)

    loadout = _build(repo, "produce-001", HSKI_R, idol_rank=4, memories=(HIF_GIFT,))
    assert loadout.memories == (spec,) and loadout.metadata["memory_count"] == 1
    memory_skills = _skills(loadout, "memory")
    assert sorted(s.effect_ids[0] for s in memory_skills) == [
        "p_effect-dance_addition-0015_0015",
        "p_effect-visual_addition-0015_0015",
        "p_effect-vocal_addition-0015_0015",
    ]
    assert all(s.skill_id.startswith("p_memory_skill-") and s.trigger_id == "p_trigger-produce_start-initial" for s in memory_skills)

    deck = build_initial_exam_deck(repo, _scenario("produce-001"), rng=np.random.default_rng(0), loadout=loadout)
    assert any(str(c["id"]) == "p_card-01-act-2_001" and int(c.get("upgradeCount") or 0) == 1 for c in deck)

    # 自定义メモリー（不写 idol_card_id 则不做角色校验）
    custom = ProduceMemorySpec(memory_id="custom", ability_ids=spec.ability_ids[:1], produce_card=None)
    assert len(_skills(_build(repo, "produce-001", SENSE_IDOL, memories=(custom,)), "memory")) == 1
    # 配布メモリー按角色归属：ttmr 不能带 hski 的メモリー
    with pytest.raises(ValueError):
        _build(repo, "produce-001", SENSE_IDOL, memories=(HIF_GIFT,))
    with pytest.raises(KeyError):
        _build(repo, "produce-001", SENSE_IDOL, memories=("memory_gift-does-not-exist",))


def test_memory_stat_bonus_reaches_produce_runtime(repo):
    """初期三维+15 ×3 的メモリーアビリティ 在 ProduceRuntime.reset 后体现在初始属性上。"""
    from gakumas_rl.simulation.produce.runtime import ProduceRuntime

    scenario = _scenario("produce-001")
    plain = _build(repo, "produce-001", HSKI_R, idol_rank=4)
    with_memory = _build(repo, "produce-001", HSKI_R, idol_rank=4, memories=(HIF_GIFT,))
    rt_plain = ProduceRuntime(repo, scenario, idol_loadout=plain, seed=3)
    rt_memory = ProduceRuntime(repo, scenario, idol_loadout=with_memory, seed=3)
    rt_plain.reset()
    rt_memory.reset()
    # 运行时把「初期○○上昇」按偶像成长率放大（+15 × (1 + growth_rate)）
    growth = {
        "vocal": plain.stat_profile.vocal_growth_rate,
        "dance": plain.stat_profile.dance_growth_rate,
        "visual": plain.stat_profile.visual_growth_rate,
    }
    for key in ("vocal", "dance", "visual"):
        expected = float(rt_plain.state[key]) + 15.0 * (1.0 + float(growth[key]))
        assert float(rt_memory.state[key]) == pytest.approx(expected, abs=0.05), key


def test_presets_default_to_max_potential_and_prima_stella():
    """gakumas_arena 预设：potential_level / prima_stella_level 默认取主数据上限，并经 facade 进入 loadout。"""
    from gakumas_arena.env import build_loadout, make_loadout_config
    from gakumas_arena.loadouts import describe_loadout, get_loadout

    sense = get_loadout("hif_sense_default")
    anomaly = get_loadout("hif_anomaly_default")
    assert sense.potential_level is None and sense.resolved_potential_level() == 4 and sense.resolved_prima_stella_level() == 0
    assert anomaly.resolved_prima_stella_level() == 1
    cfg = sense.to_loadout_config()
    assert (cfg.potential_level, cfg.prima_stella_level, cfg.memories) == (4, 0, ())

    loadout = build_loadout("hif", loadout="hif_anomaly_default")
    assert (loadout.potential_level, loadout.prima_stella_level) == (4, 1)
    assert loadout.use_after_item is True  # ポテンシャル 2 段 初期Pアイテム変更
    assert _skills(loadout, "potential") and not _skills(loadout, "prima_stella")  # 選抜 不给一番星
    final = build_loadout("produce-008", loadout="hif_anomaly_default")
    assert _skills(final, "prima_stella")

    # 显式偶像覆盖预设时，上限按覆盖后的偶像查
    assert make_loadout_config(PRIMA_IDOL, "hif_sense_default").prima_stella_level == 1
    assert make_loadout_config("i_card-amao-1-000", "hif_sense_default").prima_stella_level == 0

    # 预设里显式降级
    from dataclasses import replace

    downgraded = build_loadout("hif", loadout=replace(sense, name="tmp", potential_level=1, prima_stella_level=0))
    assert downgraded.potential_level == 1 and not downgraded.use_after_item

    info = describe_loadout("hif_anomaly_default")
    assert info["idol"]["potential_level"] == 4 and info["idol"]["prima_stella_level"] == 1 and info["idol"]["has_prima_stella"]
    assert {s["source"] for s in info["idol_kit_skills"]} == {"level_limit", "potential"}
