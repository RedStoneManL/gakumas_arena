"""gakumas_arena: local, seeded, RL-ready sandbox of Gakuen Idolmaster produce mode.

The simulation engine is the vendored ``gakumas_rl`` package (GPL-3.0, see
``third_party/gakumas_rl_upstream/PROVENANCE.txt``); this package is a thin facade:

- ``gakumas_arena.masterdata`` - our own loader over the datamined master-data dump
- ``gakumas_arena.env``        - ``make_exam_env`` / ``make_produce_env`` (Gymnasium envs)
- ``gakumas_arena.sim``        - ``run_exam`` / ``run_produce`` seeded rollouts with a policy
- ``gakumas_arena.agents``     - tiny baseline policies
"""
__version__ = "0.1.0"

__all__ = ["__version__"]
