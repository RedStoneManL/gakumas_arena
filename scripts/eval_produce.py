#!/usr/bin/env python
"""自动培育评估：固定种子跑 N 次完整培育，输出评价值 / 评级 / 各场考试通过情况 / 终局属性。

示例
----
    python scripts/eval_produce.py --scenario 初 --policy heuristic --seeds 10 --out out/produce.csv
    python scripts/eval_produce.py --scenario 初 --compare heuristic,random --seeds 20      # random 作为下限
    python scripts/eval_produce.py --policy heuristic --exam-policy search --depth 1 --seeds 10
        # 培育里的考试改由 SearchPolicy 打牌（默认 builtin = gakumas_rl 内置启发式）

外层（每周动作）策略只有 heuristic / random；``--exam-policy`` 控制培育内考试的打牌策略。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gakumas_arena.env import AUTO  # noqa: E402
from gakumas_arena.policies.evaluation import (  # noqa: E402
    PRODUCE_COLUMNS,
    evaluate_produce,
    format_head_to_head,
    format_table,
    parse_loadout,
    write_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default="first_star")
    parser.add_argument("--idol", default=AUTO, help="偶像卡 id；默认 AUTO = 预设的偶像（无预设时为 花海咲季 R）")
    parser.add_argument("--loadout", default=None, help="预设名（如 hif_sense_default）、JSON 字符串或 .json/.yaml 文件（LoadoutConfig 字段）")
    parser.add_argument("--policy", default="heuristic", help="外层策略：heuristic | random")
    parser.add_argument("--compare", default=None, help="逗号分隔的多个外层策略，相同 seed 对比")
    parser.add_argument("--exam-policy", default="builtin", help="培育内考试打牌：builtin | search | search:d1k2 ...")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--depth", type=int, default=1, help="exam-policy=search 时的前瞻动作数")
    parser.add_argument("--samples", type=int, default=2, help="exam-policy=search 时的机会节点采样数")
    parser.add_argument("--metric", default="rating", choices=("rating", "final_score"), help="汇总表使用的指标")
    parser.add_argument("--out", default=None)
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    loadout = parse_loadout(args.loadout)
    policies = [p.strip() for p in (args.compare or args.policy).split(",") if p.strip()]
    rows = []
    for name in policies:
        if not args.quiet:
            print(f"== {name}/{args.exam_policy}  scenario={args.scenario} idol={args.idol} seeds={args.seeds}", flush=True)
        rows += evaluate_produce(
            args.scenario, args.idol, loadout, name, args.seeds,
            seed_start=args.seed_start, exam_policy=args.exam_policy,
            depth=args.depth, samples=args.samples, verbose=not args.quiet,
        )
    print()
    print(format_table(rows, args.metric, ("route_clear", "auditions_passed", "final_score"), key="label"))
    if len(policies) > 1:
        print()
        print(format_head_to_head(rows, args.metric, rows[0]["label"], key="label"))
    if args.out:
        path = write_csv(rows, args.out, PRODUCE_COLUMNS)
        print(f"\nwrote {len(rows)} rows -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
