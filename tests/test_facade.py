"""Facade smoke tests: gakumas_arena.env / gakumas_arena.sim over the vendored gakumas_rl engine."""
from __future__ import annotations

import numpy as np
import pytest

from gakumas_arena.masterdata import default_dump_dir

pytestmark = pytest.mark.skipif(not default_dump_dir().is_dir(), reason="master data dump not fetched")


def _random_rollout(env, seed: int) -> tuple[float, list[int], int]:
    obs, info = env.reset(seed=seed)
    rng = np.random.default_rng(seed)
    actions: list[int] = []
    for _ in range(5000):
        legal = np.flatnonzero(obs["action_mask"] > 0.5)
        assert legal.size > 0
        action = int(rng.choice(legal))
        actions.append(action)
        obs, reward, terminated, truncated, info = env.step(action)
        assert np.isfinite(reward)
        if terminated or truncated:
            break
    else:
        pytest.fail("exam did not terminate")
    return float(env.runtime.score), actions, int(env.runtime.turn)


def test_exam_env_first_star_random_rollout_is_deterministic():
    from gakumas_arena.env import DEFAULT_IDOL, get_scenario, legal_actions, make_exam_env

    env = make_exam_env("first_star", DEFAULT_IDOL, seed=123)
    assert env.scenario.scenario_id == "produce-001"
    assert get_scenario("初").scenario_id == "produce-001"
    assert env.current_loadout is not None and env.current_loadout.idol_card_id == DEFAULT_IDOL

    obs, info = env.reset(seed=7)
    assert set(obs) == {"global", "action_features", "action_mask"}
    assert obs["action_mask"].shape == (env.action_space.n,)
    assert legal_actions(obs).size >= 1  # at least end_turn
    assert info["scenario"] == "produce-001"

    score_a, actions_a, turns_a = _random_rollout(env, seed=7)
    score_b, actions_b, turns_b = _random_rollout(env, seed=7)
    assert score_a > 0
    assert turns_a >= 1
    assert (score_a, actions_a, turns_a) == (score_b, actions_b, turns_b)

    # a fresh env with the same seed reproduces too
    env2 = make_exam_env("first_star", DEFAULT_IDOL, seed=123)
    assert _random_rollout(env2, seed=7)[0] == score_a


def test_run_exam_returns_structured_result_and_is_seed_deterministic():
    from gakumas_arena.sim import run_exam

    a = run_exam("first_star", seed=11, policy="random")
    b = run_exam("first_star", seed=11, policy="random")
    assert a.kind == "exam" and a.scenario == "produce-001"
    assert a.terminated and not a.truncated
    assert a.score > 0 and a.steps == len(a.log) >= 1
    assert a.log[0]["label"] and "reward" in a.log[0]
    assert a.events, "runtime event log should be exposed"
    assert a.score == b.score and [e["action"] for e in a.log] == [e["action"] for e in b.log]
    assert "path" in a.data_version
    assert a.to_json()


def test_run_exam_heuristic_policy_runs():
    from gakumas_arena.sim import run_exam

    result = run_exam("first_star", seed=3, policy="heuristic", stage_type="final")
    assert result.terminated and result.score > 0
    assert result.stage_type == "ProduceStepType_AuditionFinal"


def test_make_produce_env_resets_and_steps():
    from gakumas_arena.env import legal_actions, make_produce_env

    env = make_produce_env("first_star", seed=5)
    obs, info = env.reset(seed=5)
    assert info["scenario"] == "produce-001"
    legal = legal_actions(obs)
    assert legal.size >= 1
    obs, reward, terminated, truncated, info = env.step(int(legal[0]))
    assert np.isfinite(reward)
    assert obs["action_mask"].shape == (env.action_space.n,)
