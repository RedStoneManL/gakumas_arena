"""pytest 引导：vendored gakumas_rl 测试直接从仓库根导入 `gakumas_rl` 包。"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
