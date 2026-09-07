"""Gymnasium wrapper around engine.Stage (inner card-play loop)."""
from __future__ import annotations

import gymnasium as gym
import numpy as np

from ..data.loader import DataRegistry
from ..engine import Rng, Stage, StageConfig

MAX_HAND = 5
MAX_DRINKS = 3


class StageEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, cfg: StageConfig, registry: DataRegistry):
        self.cfg = cfg
        self.reg = registry
        self.card_index = {cid: i + 1 for i, cid in enumerate(sorted(registry.skill_cards))}
        n_actions = MAX_HAND + MAX_DRINKS + 1
        self.action_space = gym.spaces.Discrete(n_actions)
        self.observation_space = gym.spaces.Dict({
            "hand": gym.spaces.MultiDiscrete([len(self.card_index) + 1] * MAX_HAND),
            "state": gym.spaces.Box(-1e4, 1e4, shape=(16,), dtype=np.float32),
        })
        self.stage: Stage | None = None

    def _obs(self):
        st = self.stage.st
        hand = np.zeros(MAX_HAND, dtype=np.int64)
        for i, cid in enumerate(st.hand[:MAX_HAND]):
            hand[i] = self.card_index[cid]
        vec = np.array([
            st.turn, self.cfg.turns - st.turn, st.score, st.stamina, st.genki, st.focus,
            st.good_condition, st.excellent_condition, st.motivation, st.good_impression,
            st.zenryoku, st.onzon, st.strength, len(st.deck), len(st.discard), st.extra_plays,
        ], dtype=np.float32)
        return {"hand": hand, "state": vec}

    def action_mask(self) -> np.ndarray:
        m = np.zeros(self.action_space.n, dtype=bool)
        for kind, idx in self.stage.legal_actions():
            if kind == "play":
                m[idx] = True
            elif kind == "drink":
                m[MAX_HAND + idx] = True
            else:
                m[-1] = True
        return m

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.stage = Stage(self.cfg, self.reg, Rng(seed))
        return self._obs(), {"action_mask": self.action_mask()}

    def step(self, action: int):
        before = self.stage.st.score
        if action < MAX_HAND:
            act = ("play", int(action))
        elif action < MAX_HAND + MAX_DRINKS:
            act = ("drink", int(action - MAX_HAND))
        else:
            act = ("skip", 0)
        self.stage.step(act)
        st = self.stage.st
        reward = float(st.score - before)
        return self._obs(), reward, st.done, False, {"action_mask": self.action_mask()}
