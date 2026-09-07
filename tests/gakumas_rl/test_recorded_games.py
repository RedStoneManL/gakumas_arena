"""实机录像回归：按 YouTube 录像逐回合复现 体力 / 元気 / スコア / 状態修正。

夹具来自 kjirou/gakumas-core 的 e2e 测试（2024 年录像，卡牌数据为当时版本），已按日文名映射到当前主数据；
录像与当前主数据/引擎不一致的夹具在 setup 里写 `xfail` 原因。新增夹具的方法见 docs/rules/scoring_fidelity.md §5。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gakumas_rl.repository.master_data import MasterDataRepository

from recorded_game_harness import RecordedGameReplayer, iter_fixture_paths, load_fixture


@pytest.fixture(scope='module')
def repository() -> MasterDataRepository:
    return MasterDataRepository()


def _fixture_params():
    params = []
    for path in iter_fixture_paths():
        fixture = load_fixture(path)
        marks = [pytest.mark.xfail(reason=fixture.xfail_reason, strict=True)] if fixture.xfail_reason else []
        params.append(pytest.param(path, id=fixture.fixture_id, marks=marks))
    return params


@pytest.mark.parametrize('fixture_path', _fixture_params())
def test_recorded_game_replays_video(repository: MasterDataRepository, fixture_path: Path) -> None:
    fixture = load_fixture(fixture_path)
    replayer = RecordedGameReplayer(repository, fixture)
    replayer.replay()
