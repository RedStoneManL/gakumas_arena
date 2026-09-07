# gakumas_arena

学園アイドルマスター（学マス）培育模式的本地沙盒：seeded 可复现、Gymnasium 接口，用于自动培育/自动打牌脚本与 RL 训练。

引擎不是自研的：本仓库把 [skyfsj/gakumas-rl](https://github.com/skyfsj/gakumas-rl) 以包 `gakumas_rl/` 的形式 vendor 进来
（版本与提交见 `third_party/gakumas_rl_upstream/PROVENANCE.txt`，上游 README/AGENTS/训练指南也在该目录），
`gakumas_arena/` 只是一层很薄的 facade（环境构造、seeded rollout、主数据加载与覆盖率工具）。

## 许可

`gakumas_rl` 是 **GPL-3.0**（`third_party/gakumas_rl_upstream/LICENSE`）。本仓库把它作为一个包一起分发并直接 import，
因此整个发行物按 GPL-3.0 继承；`pyproject.toml` 已声明 `GPL-3.0-or-later`。对 `gakumas_rl/` 的本地修改
（主数据路径、数据漂移修复等）请保留在该目录并在 PROVENANCE 里记录。

## 布局

- `gakumas_arena/masterdata/` — 我们自己的主数据（`vertesan/gakumasu-diff` YAML dump）薄加载层，JSON 缓存
- `gakumas_arena/env/` — `make_exam_env()` / `make_produce_env()`：按剧本 id、偶像卡、loadout、seed 构造 gakumas_rl 的
  `GakumasExamEnv` / `GakumasPlanningEnv`
- `gakumas_arena/sim/` — `run_exam()` / `run_produce()`：用策略（random / gakumas_rl 内置启发式 / 自定义）跑一局，返回
  结构化结果（分数、逐步日志、事件、数据版本）
- `gakumas_rl/` — vendored 引擎（效果解释器、考试/培育运行时、Gym env、训练脚本）
- `tools/masterdata/` — 拉取/缓存/对比 dump；`coverage.py` = **新机制探测器**（dump 里出现但引擎未处理的枚举值）
- `docs/` — 设计（`ARCHITECTURE.md`）、交接（`HANDOFF.md`）、路线图（`PLAN.md`）、待验证清单（`OPEN_ITEMS.md`）、
  规则规格（`rules/`）、剧本规格（`scenarios/`）、调研与覆盖率报告（`research/`）；索引见 `docs/README.md`

## 快速开始

```bash
pip install -e ".[dev]"            # 训练后端另装 ".[sb3]" / ".[torch]"
tools/masterdata/fetch.sh          # 拉取主数据 dump 到 data/raw/gakumasu-diff（不入库）
python -m pytest tests -q          # 需要 torch/fastapi 的上游训练/API 测试在缺依赖时自动跳过收集
```

```python
from gakumas_arena.env import make_exam_env, legal_actions
from gakumas_arena.sim import run_exam, run_produce

env = make_exam_env("first_star", seed=0)          # 初 Regular；别名见 gakumas_arena.env.SCENARIOS
obs, info = env.reset(seed=0)
obs, r, done, _, info = env.step(int(legal_actions(obs)[0]))

print(run_exam("nia", seed=1, policy="heuristic").score)   # 官方 ProduceExamAutoEvaluation 先验 + 1 步前瞻
print(run_produce("first_star", seed=1).summary["final_summary"]["produce_result"])
```

## 数据更新后

```bash
tools/masterdata/fetch.sh
python tools/masterdata/coverage.py --strict    # 退出码 1 = dump 出现了引擎未处理的枚举值（新机制）
```

报告写到 `docs/research/engine_coverage.md` 与 `data/coverage.json`。当前 dump 里的枚举值已 100% 有处理器
（107 考试效果 / 66 培育效果 / 29 触发相位 / 39 成长效果 / 33 步骤类型），H.I.F 是独立剧本路线而非按 初 跑。

> 覆盖率 100% 只说明「每个枚举值都有代码路径」，不代表数值与实机一致 —— 未验证项见 `docs/OPEN_ITEMS.md`。

## 文档

**接手请先读 [`docs/HANDOFF.md`](docs/HANDOFF.md)**，然后是 [`docs/PLAN.md`](docs/PLAN.md)（路线图）和
[`docs/OPEN_ITEMS.md`](docs/OPEN_ITEMS.md)（待验证清单）。完整索引：[`docs/README.md`](docs/README.md)。
