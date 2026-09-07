"""Convert every <Table>.yaml of the master-data dump to JSON once (YAML parsing is slow).

Usage: python tools/masterdata/build_cache.py [dump_dir] [--only Table1,Table2]
Cache goes to <dump_dir>/../masterdata_json/<Table>.json plus _meta.json (commit, timestamps).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gakumas_arena.masterdata.store import cache_dir_for, convert_table  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump_dir", nargs="?", default="data/raw/gakumasu-diff")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    dump = Path(args.dump_dir).resolve()
    cache = cache_dir_for(dump)
    cache.mkdir(parents=True, exist_ok=True)
    only = {t for t in args.only.split(",") if t}
    files = sorted(dump.glob("*.yaml"))
    t0 = time.time()
    done = 0
    for f in files:
        if only and f.stem not in only:
            continue
        try:
            convert_table(dump, f.stem, force=True)
        except Exception as exc:  # noqa: BLE001 - a few tables (e.g. Localization) are malformed
            print(f"SKIP {f.stem}: {type(exc).__name__}: {str(exc).splitlines()[0]}", flush=True)
            continue
        done += 1
        if done % 25 == 0:
            print(f"{done} tables, {time.time() - t0:.0f}s", flush=True)
    try:
        commit = subprocess.check_output(["git", "-C", str(dump), "log", "-1", "--format=%H %ci"], text=True).strip()
    except Exception:  # noqa: BLE001
        commit = "unknown"
    (cache / "_meta.json").write_text(json.dumps({"dump": str(dump), "commit": commit, "tables": done,
                                                  "built_at": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
    print(f"converted {done} tables in {time.time() - t0:.0f}s -> {cache}")


if __name__ == "__main__":
    main()
