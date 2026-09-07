"""策略层测试：Random / Heuristic / Search 接口、确定性，以及 search 在固定 seed 上不弱于 heuristic。

实测（docs/evaluation.md）：初 mid1、默认编成，search(d2,k2,rollout) 在 10 个 seed 上对 heuristic 10 胜 0 负；
这里用 seed 0（heuristic 36 vs search 61，2026-09-07 引擎取整改动后）作为回归锚点。整套测试约 15 s。
"""
from __future__ import annotations

import numpy as np
import pytest

from gakumas_arena.masterdata import default_dump_dir

pytestmark = pytest.mark.skipif(not default_dump_dir().is_dir(), reason="master data dump not fetched")

SCENARIO = "初"
STAGE = "mid1"
SEED = 0


def _actions(result) -> list[int]:
    return [entry["action"] for entry in result.log]


def test_random_and_heuristic_policies_run_and_are_deterministic():
    from gakumas_arena.policies import HeuristicPolicy, RandomPolicy
    from gakumas_arena.sim import run_exam

    a = run_exam(SCENARIO, seed=SEED, policy=RandomPolicy(SEED), stage_type=STAGE)
    b = run_exam(SCENARIO, seed=SEED, policy=RandomPolicy(SEED), stage_type=STAGE)
    assert a.policy == "random" and a.terminated and a.score > 0
    assert (a.score, _actions(a)) == (b.score, _actions(b))

    h = run_exam(SCENARIO, seed=SEED, policy=HeuristicPolicy(SEED), stage_type=STAGE)
    assert h.policy == "heuristic" and h.terminated and h.score > 0
    # 与 facade 自带的 'heuristic' 字符串策略一致
    h2 = run_exam(SCENARIO, seed=SEED, policy="heuristic", stage_type=STAGE)
    assert (h.score, _actions(h)) == (h2.score, _actions(h2))


def test_search_policy_beats_heuristic_on_fixed_seed_and_is_deterministic():
    from gakumas_arena.policies import HeuristicPolicy, SearchPolicy
    from gakumas_arena.sim import run_exam

    heuristic = run_exam(SCENARIO, seed=SEED, policy=HeuristicPolicy(SEED), stage_type=STAGE)
    search_a = run_exam(SCENARIO, seed=SEED, policy=SearchPolicy(depth=2, samples=2, seed=SEED), stage_type=STAGE)
    search_b = run_exam(SCENARIO, seed=SEED, policy=SearchPolicy(depth=2, samples=2, seed=SEED), stage_type=STAGE)

    assert search_a.policy == "search_d2_k2_rollout"
    assert search_a.terminated and not search_a.truncated
    # 确定性：同 seed 两次完全相同的动作序列与分数
    assert (search_a.score, _actions(search_a)) == (search_b.score, _actions(search_b))
    # 固定 seed 上不弱于启发式（实测 search 61 vs heuristic 36）
    assert search_a.score >= heuristic.score, (search_a.score, heuristic.score)


def test_search_policy_does_not_disturb_env_rng():
    """搜索会临时改写 runtime RNG；搜索后必须恢复，保证真实环境的随机流与不搜索时一致。"""
    from gakumas_arena.env import legal_actions, make_exam_env
    from gakumas_arena.policies import SearchPolicy

    env = make_exam_env(SCENARIO, seed=SEED, stage_type=STAGE)
    obs, info = env.reset(seed=SEED)
    before = env.runtime.np_random.bit_generator.state["state"]
    hand_before = [card.uid for card in env.runtime.hand]
    policy = SearchPolicy(depth=2, samples=2, seed=SEED)
    action = policy.act(env, obs, info)
    assert action in set(int(i) for i in legal_actions(obs))
    assert env.runtime.np_random.bit_generator.state["state"] == before
    assert [card.uid for card in env.runtime.hand] == hand_before
    assert policy.last_stats["nodes"] > 0 and policy.last_stats["chosen"]


def test_search_policy_select_action_protocol_and_leaf_modes():
    from gakumas_arena.env import make_exam_env
    from gakumas_arena.policies import SearchPolicy

    env = make_exam_env(SCENARIO, seed=SEED, stage_type=STAGE)
    env.reset(seed=SEED)
    for leaf in ("score", "heuristic", "rollout"):
        policy = SearchPolicy(depth=1, samples=1, seed=SEED, leaf=leaf)
        chosen = policy.select_action(env.runtime)
        assert chosen is not None and chosen.kind in {"card", "drink", "end_turn"}
        assert np.isfinite(policy.evaluate(env.runtime))
    with pytest.raises(ValueError):
        SearchPolicy(depth=0)


def test_evaluation_helpers_and_make_policy():
    from gakumas_arena.policies import make_policy, summarize
    from gakumas_arena.policies.evaluation import evaluate_exam, format_head_to_head, format_table

    p = make_policy("search:d1k1", seed=3)
    assert p.depth == 1 and p.samples == 1
    with pytest.raises(ValueError):
        make_policy("nope")

    rows = evaluate_exam(SCENARIO, stage=STAGE, policy="random", seeds=2) + evaluate_exam(
        SCENARIO, stage=STAGE, policy="heuristic", seeds=2
    )
    assert len(rows) == 4 and {r["policy"] for r in rows} == {"random", "heuristic"}
    assert set(rows[0]) >= {"seed", "policy", "score", "passed", "rank", "turns", "steps", "wall_s"}
    stats = summarize([r["score"] for r in rows])
    assert stats["n"] == 4 and stats["p10"] <= stats["median"] <= stats["p90"]
    assert "heuristic" in format_table(rows, "score", ("passed",))
    assert "win" in format_head_to_head(rows, "score", "random")


def test_produce_evaluation_with_search_inner_exam_runs():
    from gakumas_arena.policies.evaluation import evaluate_produce

    rows = evaluate_produce(SCENARIO, policy="heuristic", seeds=1, exam_policy="search", depth=1, samples=1)
    assert len(rows) == 1
    row = rows[0]
    assert row["label"].startswith("heuristic/search_d1_k1")
    assert row["auditions_total"] >= 1 and row["rating"] > 0
