"""Single source of randomness. Everything random in the sandbox goes through here."""
from __future__ import annotations

import numpy as np


class Rng:
    def __init__(self, seed: int | None = None):
        self._g = np.random.default_rng(seed)

    def shuffle(self, items: list) -> None:
        self._g.shuffle(items)

    def choice(self, n: int) -> int:
        return int(self._g.integers(0, n))

    def random(self) -> float:
        return float(self._g.random())

    def clone(self) -> "Rng":
        c = Rng.__new__(Rng)
        c._g = np.random.default_rng()
        c._g.bit_generator.state = self._g.bit_generator.state
        return c
