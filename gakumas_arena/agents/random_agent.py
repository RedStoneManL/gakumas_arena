import numpy as np


def act(mask: np.ndarray, rng: np.random.Generator) -> int:
    return int(rng.choice(np.flatnonzero(mask)))
