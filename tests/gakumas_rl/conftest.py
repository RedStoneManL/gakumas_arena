"""pytest 引导：vendored gakumas_rl 测试直接从仓库根导入 `gakumas_rl` 包。

训练 / API 相关测试依赖可选依赖（torch、sb3、fastapi）；缺少时跳过收集而不是报 ImportError，
这样 `python -m pytest tests` 在只装了基础依赖的环境里也能跑完规则测试。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_OPTIONAL_DEPENDENCIES = {
    "torch": (
        "test_autopilot.py",
        "test_bootstrap_training.py",
        "test_demo_exam.py",
        "test_rllib_model.py",
    ),
    "fastapi": ("test_inference_api.py",),
}

collect_ignore: list[str] = []
for _module, _files in _OPTIONAL_DEPENDENCIES.items():
    if importlib.util.find_spec(_module) is None:
        collect_ignore.extend(_files)

_HAS_SB3 = importlib.util.find_spec("stable_baselines3") is not None and importlib.util.find_spec("sb3_contrib") is not None


def pytest_collection_modifyitems(config, items) -> None:
    """训练后端测试按名字标记：缺 stable-baselines3 / sb3-contrib 时跳过 `*sb3*` 用例。"""
    if _HAS_SB3:
        return
    import pytest

    skip = pytest.mark.skip(reason="stable-baselines3 / sb3-contrib not installed (pip install '.[sb3]')")
    for item in items:
        if "sb3" in item.name.lower():
            item.add_marker(skip)
