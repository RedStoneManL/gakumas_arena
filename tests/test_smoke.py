import numpy as np

from gakumas_arena.agents.random_agent import act
from gakumas_arena.data import load_registry
from gakumas_arena.engine import Rng, Stage, StageConfig
from gakumas_arena.env.stage_env import StageEnv
from gakumas_arena.produce import load_scenario


def _cfg():
    return StageConfig(kind="lesson", turns=6, plan="sense",
                       deck=["sc_sample_appeal"] * 3 + ["sc_sample_pose"] * 2 + ["sc_sample_focus"] * 2,
                       stats={"vocal": 100, "dance": 100, "visual": 100}, max_stamina=30)


def test_stage_runs_and_is_deterministic():
    reg = load_registry()
    a, b = Stage(_cfg(), reg, Rng(1)), Stage(_cfg(), reg, Rng(1))
    for s in (a, b):
        while not s.st.done:
            s.step(s.legal_actions()[0])
    assert a.st.score == b.st.score > 0
    assert a.st.log == b.st.log


def test_env_random_rollout():
    env = StageEnv(_cfg(), load_registry())
    obs, info = env.reset(seed=0)
    rng = np.random.default_rng(0)
    total, done = 0.0, False
    while not done:
        obs, r, done, _, info = env.step(act(info["action_mask"], rng))
        total += r
    assert total >= 0


def test_scenario_loads():
    assert load_scenario("hif").id == "hif"
