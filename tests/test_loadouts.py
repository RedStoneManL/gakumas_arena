"""命名预设编成（gakumas_arena.loadouts）与 facade 接入的测试。

覆盖：预设能解析成 IdolLoadout（6 张支援卡、SSR 等级 60、rank 6）、facade 接受预设名 / HIF 默认预设、
支援卡稀有度归一化回归（SSR 曾被钳到 40 级）、planning 启发式会上课（曾整局只选差入）、
以及 seed=1 的 HIF heuristic 跑一局至少通过 選抜試験1 并进入 選抜試験2。
"""
from __future__ import annotations

import time

import pytest

from gakumas_arena.masterdata import default_dump_dir

pytestmark = pytest.mark.skipif(not default_dump_dir().is_dir(), reason="master data dump not fetched")


def test_presets_resolve_to_full_loadouts():
    from gakumas_arena.env import build_loadout, get_repository
    from gakumas_arena.loadouts import PLAN_TYPES, describe_loadout, get_loadout, list_loadouts

    names = list_loadouts()
    assert {"hif_sense_default", "hif_logic_default", "hif_anomaly_default"} <= set(names)
    repo = get_repository()
    for name in names:
        preset = get_loadout(name)
        idol_row = repo.load_table("IdolCard").first(preset.idol_card_id)
        assert idol_row is not None and idol_row["rarity"].endswith("Ssr"), name
        assert idol_row["planType"] == PLAN_TYPES[preset.plan], name
        assert len(preset.support_card_ids) == 6 and len(set(preset.support_card_ids)) == 6, name

        loadout = build_loadout(preset.scenario, loadout=name)
        assert loadout is not None and loadout.idol_card_id == preset.idol_card_id
        assert loadout.idol_rank == preset.idol_rank == 6
        assert len(loadout.support_cards) == 6
        # SSR 支援卡上限 60（SupportCardLevelLimit），修复稀有度大小写前会被钳到 40
        assert all(card.support_card_level == 60 for card in loadout.support_cards), name
        assert loadout.metadata["support_card_selection_mode"] == "manual"
        assert len(loadout.produce_skills) > 20  # 支援卡培育技能已合并进 loadout

        info = describe_loadout(name)
        assert info["idol"]["id"] == preset.idol_card_id and info["idol"]["name"]
        assert len(info["support_cards"]) == 6 and all(card["name"] for card in info["support_cards"])
        assert set(info["hif_growth_panel_levels"]) == {f"{i:02d}" for i in range(1, 10)}


def test_unknown_preset_raises():
    from gakumas_arena.loadouts import get_loadout

    with pytest.raises(KeyError):
        get_loadout("no_such_preset")


def test_facade_defaults_hif_to_preset_but_keeps_first_star_default_idol():
    from gakumas_arena.env import AUTO, DEFAULT_IDOL, make_loadout_config, make_produce_env, resolve_preset
    from gakumas_arena.loadouts import get_loadout

    assert resolve_preset("hif", AUTO, None).name == "hif_sense_default"
    assert resolve_preset("first_star", AUTO, None) is None
    assert resolve_preset("hif", DEFAULT_IDOL, None) is None  # explicit idol -> no preset
    assert resolve_preset("first_star", AUTO, "hif_logic_default").name == "hif_logic_default"

    cfg = make_loadout_config(AUTO, None, scenario="hif")
    assert cfg.idol_card_id == get_loadout("hif_sense_default").idol_card_id
    assert make_loadout_config(AUTO, None, scenario="first_star").idol_card_id == DEFAULT_IDOL
    # 显式偶像覆盖预设里的偶像卡
    assert make_loadout_config("i_card-amao-3-018", "hif_sense_default").idol_card_id == "i_card-amao-3-018"

    env = make_produce_env("hif", seed=3)
    assert env.current_loadout.idol_card_id == get_loadout("hif_sense_default").idol_card_id
    # 预设的剧本级覆盖（H.I.F ボーナス 成长面板）已写进 ScenarioSpec
    assert env.scenario.hif.growth_panel_levels == get_loadout("hif_sense_default").hif_growth_panel_levels
    env_named = make_produce_env("hif", loadout="hif_anomaly_default", seed=3)
    assert env_named.current_loadout.idol_card_id == get_loadout("hif_anomaly_default").idol_card_id


def test_support_card_rarity_is_normalised_to_master_level_limit():
    from gakumas_arena.env import get_repository
    from gakumas_rl.idol_config import _resolve_support_card_level
    from gakumas_rl.support_card_selector import normalize_support_card_rarity

    assert normalize_support_card_rarity("SupportCardRarity_Ssr") == "SupportCardRarity_SSR"
    assert normalize_support_card_rarity("SupportCardRarity_Sr") == "SupportCardRarity_SR"
    rows = {row["rarity"]: row for row in get_repository().support_cards.rows}
    assert _resolve_support_card_level(rows["SupportCardRarity_Ssr"], 60) == 60
    assert _resolve_support_card_level(rows["SupportCardRarity_Sr"], 60) == 50
    assert _resolve_support_card_level(rows["SupportCardRarity_R"], 60) == 40


def test_planning_heuristic_takes_lessons_on_hif():
    from gakumas_arena.env import make_produce_env
    from gakumas_rl.interfaces.service import _choose_planning_action

    env = make_produce_env("hif", seed=1)
    env.reset(seed=1)
    chosen = env.runtime.legal_actions()[_choose_planning_action(env.runtime)]
    assert chosen.action_type.startswith("lesson_"), chosen.action_type


def test_hif_heuristic_run_with_default_preset_seed_1_passes_first_selection():
    from gakumas_arena.sim import run_produce

    started = time.time()
    result = run_produce("hif", seed=1, policy="heuristic")
    assert time.time() - started < 60
    assert result.loadout == "hif_sense_default"
    assert result.terminated and not result.truncated
    history = result.summary["final_summary"]["audition_history"]
    assert history[0]["stage_type"] == "ProduceStepType_AuditionMid1" and history[0]["cleared"]
    assert len(history) >= 2, "did not reach 選抜試験2"
    # 選抜試験2（border ≈ 49.8k）在当前引擎下无法稳定通过（见 docs/loadouts.md / OPEN_ITEMS C1），这里只记录。
    stages = [item["stage_type"] for item in history]
    assert stages[:2] == ["ProduceStepType_AuditionMid1", "ProduceStepType_AuditionMid2"]
    assert result.summary["final_summary"]["produce_result"]["score"] > 0


def test_hif_preset_runs_are_seed_deterministic():
    from gakumas_arena.sim import run_produce

    a = run_produce("hif", seed=2, policy="heuristic", loadout="hif_logic_default")
    b = run_produce("hif", seed=2, policy="heuristic", loadout="hif_logic_default")
    assert a.loadout == b.loadout == "hif_logic_default"
    assert [e["action"] for e in a.log] == [e["action"] for e in b.log]
    assert a.score == b.score
