#!/usr/bin/env python
"""自动打牌评估：固定种子跑 N 局考试，输出逐局 CSV 与 mean/median/p10/p90。

示例
----
    python scripts/eval_exam.py --scenario 初 --stage mid1 --policy search --seeds 10 --out out/exam.csv
    python scripts/eval_exam.py --scenario 初 --stage final --compare random,heuristic,search --seeds 20
    python scripts/eval_exam.py --policy search --depth 3 --samples 2 --seeds 5      # 更深的搜索
    python scripts/eval_exam.py --compare heuristic,search:d1k2,search:d2k2          # 简写覆盖深度/采样

``--loadout`` 接受 JSON 字符串或 .json/.yaml 路径，字段同 ``gakumas_rl.interfaces.service.LoadoutConfig``
（``idol_rank`` / ``producer_level`` / ``support_card_ids`` / ``challenge_item_ids`` ...）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gakumas_arena.env import DEFAULT_IDOL  # noqa: E402
from gakumas_arena.policies.evaluation import (  # noqa: E402
    EXAM_COLUMNS,
    POLICY_NAMES,
    evaluate_exam,
    format_head_to_head,
    format_table,
    parse_loadout,
    write_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default="first_star", help="场景别名或 Produce.id（初 / nia / hif / produce-001 ...）")
    parser.add_argument("--idol", default=DEFAULT_IDOL, help="偶像卡 id（默认 花海咲季 R）")
    parser.add_argument("--loadout", default=None, help="JSON 字符串或 .json/.yaml 文件（LoadoutConfig 字段）")
    parser.add_argument("--stage", default="mid1", help="mid1 / mid2 / final 或原始 ProduceStepType_*")
    parser.add_argument("--policy", default="heuristic", help=f"单策略：{' | '.join(POLICY_NAMES)}（search 可写 search:d2k2）")
    parser.add_argument("--compare", default=None, help="逗号分隔的多策略，在相同 seed 上对比，如 random,heuristic,search")
    parser.add_argument("--seeds", type=int, default=10, help="局数（seed = seed-start .. seed-start+N-1）")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--depth", type=int, default=2, help="search：前瞻动作数")
    parser.add_argument("--samples", type=int, default=2, help="search：机会节点采样数 K")
    parser.add_argument("--out", default=None, help="逐局结果 CSV 路径")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    loadout = parse_loadout(args.loadout)
    policies = [p.strip() for p in (args.compare or args.policy).split(",") if p.strip()]
    rows = []
    for name in policies:
        if not args.quiet:
            print(f"== {name}  scenario={args.scenario} stage={args.stage} idol={args.idol} seeds={args.seeds}", flush=True)
        rows += evaluate_exam(
            args.scenario, args.idol, loadout, args.stage, name, args.seeds,
            seed_start=args.seed_start, depth=args.depth, samples=args.samples, verbose=not args.quiet,
        )
    print()
    print(format_table(rows, "score", ("passed",)))
    if len(policies) > 1:
        print()
        print(format_head_to_head(rows, "score", rows[0]["policy"]))
    if args.out:
        path = write_csv(rows, args.out, EXAM_COLUMNS)
        print(f"\nwrote {len(rows)} rows -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
