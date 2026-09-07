#!/usr/bin/env python3
"""Diff two commits of a gakumasu-diff style master-data dump (one YAML file per table).

Reports, between OLD and NEW:
  * tables added / removed (YAML files),
  * top-level fields added / removed per table (schema growth),
  * enum values added / removed per (table, field-path)  - values shaped like `SomeType_Value`,
  * row-level changes (added / removed / modified rows) for a list of small "config" tables
    (Produce, ProduceSetting, ExamSetting, ResultGradePattern, ... see DEFAULT_CONFIG_TABLES),
  * optionally, for every new enum value of a given (table, field), one example row and its
    Japanese description text (produceDescriptions[*].text) at NEW.

Usage:
  python tools/masterdata/history_diff.py DUMP_DIR OLD NEW [options]
      OLD / NEW      any git revision of DUMP_DIR (hash, tag, HEAD~3, ...)
  --cache DIR        per-commit summary cache (pickle). Strongly recommended: scanning one
                     snapshot (~230 MB of YAML) takes ~20-40 s, the diff itself is instant.
  --config-tables A,B,...   override the config tables whose rows are diffed ('' = none)
  --tables REGEX     only consider tables whose name matches REGEX (default: all)
  --examples T:F,... for new enum values of table T field F, print an example row + description
  --json OUT         also write the full diff as JSON
  --no-rows          skip row diffs;  --no-enums  skip enum/field diffs
  --summary-only REV write/refresh the cached summary of one revision and exit (for batch use)

Implementation notes
  * Enum / field sets are collected with a line-oriented scan of the raw YAML text (no YAML
    parse): rows are `- key: value` blocks, top-level fields are the keys at indent 2, nested
    list items (e.g. produceDescriptions[*]) produce dotted paths.  This is ~10x faster than
    parsing and is exact for this dump's flat, machine-generated layout.
  * Row diffs parse the table with yaml.CSafeLoader (libyaml); rows are keyed by `id` when
    present, otherwise by the tuple of their string-valued fields (e.g. ResultGradePattern ->
    (type, grade), ForceAppVersion -> (platformType,)).
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pickle
import re
import subprocess
import sys
from typing import Any

try:
    import yaml

    Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
except ImportError:  # pragma: no cover
    yaml = None
    Loader = None

ENUM_RE = re.compile(r"^[A-Z][A-Za-z0-9]+_[A-Za-z0-9_]+$")
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?: (.*))?$")

DEFAULT_CONFIG_TABLES = [
    "ForceAppVersion",
    "Produce",
    "ProduceSetting",
    "ExamSetting",
    "ResultGradePattern",
    "ProduceGrade",
    "ProduceExamBattleScoreConfig",
    "ProduceStepAuditionDifficulty",
    "ProduceExamBattleConfig",
    "ProduceLiveEvaluation",
    "ProduceSeason",
    "ProduceSeasonZeroGrade",
]

# --------------------------------------------------------------------------- git helpers


def git(dump: str, *args: str, text: bool = True) -> Any:
    out = subprocess.run(["git", "-C", dump, *args], check=True, capture_output=True)
    return out.stdout.decode("utf-8", "replace") if text else out.stdout


def rev_parse(dump: str, rev: str) -> str:
    return git(dump, "rev-parse", rev).strip()


def commit_date(dump: str, rev: str) -> str:
    return git(dump, "log", "-1", "--format=%cs", rev).strip()


def list_tables(dump: str, rev: str) -> list[str]:
    names = git(dump, "ls-tree", "--name-only", rev).split()
    return sorted(n[:-5] for n in names if n.endswith(".yaml"))


def show_file(dump: str, rev: str, table: str) -> str:
    return git(dump, "show", f"{rev}:{table}.yaml")


# --------------------------------------------------------------------------- text scan


def scan_table_text(text: str) -> dict[str, Any]:
    """Return {'rows': n, 'fields': set, 'enums': {path: set}} from raw YAML text."""
    fields: set[str] = set()
    enums: dict[str, set[str]] = collections.defaultdict(set)
    rows = 0
    stack: list[tuple[int, str]] = []  # (indent, key)
    for line in text.splitlines():
        if not line or line[0] == "#":
            continue
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        is_item = stripped.startswith("- ")
        if is_item:
            if indent == 0:
                rows += 1
            stripped = stripped[2:]
            indent += 2
        stripped = stripped.rstrip("\r")
        m = KEY_RE.match(stripped)
        if m:
            key, val = m.group(1), m.group(2)
            while stack and stack[-1][0] >= indent:
                stack.pop()
            stack.append((indent, key))
            if indent == 2:
                fields.add(key)
            if val and ENUM_RE.match(val):
                enums[".".join(k for _, k in stack)].add(val)
        elif is_item and ENUM_RE.match(stripped):
            # bare list item value, e.g. `  - ProduceExamEffectType_X` under `effectTypes:`
            while stack and stack[-1][0] >= indent:
                stack.pop()
            path = ".".join(k for _, k in stack) + "[]"
            enums[path].add(stripped)
    return {"rows": rows, "fields": fields, "enums": dict(enums)}


def summarize(dump: str, rev: str, cache_dir: str | None, table_re: re.Pattern | None = None,
              quiet: bool = False) -> dict[str, Any]:
    sha = rev_parse(dump, rev)
    path = os.path.join(cache_dir, f"{sha}.pkl") if cache_dir else None
    if path and os.path.exists(path):
        with open(path, "rb") as fh:
            summ = pickle.load(fh)
        if table_re is None:
            return summ
        return {**summ, "tables": {t: v for t, v in summ["tables"].items() if table_re.search(t)}}
    tables = list_tables(dump, sha)
    summ = {"sha": sha, "date": commit_date(dump, sha), "tables": {}}
    for i, t in enumerate(tables, 1):
        if not quiet and sys.stderr.isatty():
            print(f"  [{sha[:7]} {i}/{len(tables)}] {t:<50}", file=sys.stderr, end="\r")
        summ["tables"][t] = scan_table_text(show_file(dump, sha, t))
    if not quiet and sys.stderr.isatty():
        print(file=sys.stderr)
    if path:
        os.makedirs(cache_dir, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(summ, fh, protocol=pickle.HIGHEST_PROTOCOL)
    if table_re is not None:
        summ = {**summ, "tables": {t: v for t, v in summ["tables"].items() if table_re.search(t)}}
    return summ


# --------------------------------------------------------------------------- row diffs


def load_rows(dump: str, rev: str, table: str) -> list[dict] | None:
    if yaml is None:
        sys.exit("pyyaml is required for row diffs (pip install pyyaml)")
    try:
        text = show_file(dump, rev, table)
    except subprocess.CalledProcessError:
        return None
    data = yaml.load(text, Loader=Loader)
    return data if isinstance(data, list) else []


def row_key(row: dict) -> tuple:
    if "id" in row:
        return ("id", row["id"])
    return tuple((k, v) for k, v in row.items() if isinstance(v, str))


def diff_rows(old: list[dict] | None, new: list[dict] | None) -> dict[str, Any]:
    old_map = {row_key(r): r for r in (old or [])}
    new_map = {row_key(r): r for r in (new or [])}
    added = [new_map[k] for k in new_map if k not in old_map]
    removed = [old_map[k] for k in old_map if k not in new_map]
    modified = []
    for k, nr in new_map.items():
        orr = old_map.get(k)
        if orr is None or orr == nr:
            continue
        changes = {}
        for f in sorted(set(orr) | set(nr)):
            if orr.get(f) != nr.get(f):
                changes[f] = (orr.get(f), nr.get(f))
        modified.append({"key": k, "name": nr.get("name") or orr.get("name"), "changes": changes})
    return {"added": added, "removed": removed, "modified": modified}


# --------------------------------------------------------------------------- examples


def description_text(row: dict) -> str:
    parts = []
    for k in ("produceDescriptions", "customizeProduceDescriptions", "playProduceDescriptions"):
        for d in row.get(k) or []:
            if isinstance(d, dict) and d.get("text"):
                parts.append(str(d["text"]))
    return "".join(parts)


def example_for(rows: list[dict], field: str, value: str) -> dict | None:
    for r in rows:
        v = r.get(field)
        if v == value or (isinstance(v, list) and value in v):
            return r
    return None


# --------------------------------------------------------------------------- main diff


def compute_diff(dump: str, old: str, new: str, cache_dir: str | None, table_re: re.Pattern | None,
                 config_tables: list[str], want_enums: bool, want_rows: bool,
                 examples: list[tuple[str, str]]) -> dict[str, Any]:
    result: dict[str, Any] = {"old": {}, "new": {}}
    if want_enums or table_re is not None:
        so = summarize(dump, old, cache_dir, table_re)
        sn = summarize(dump, new, cache_dir, table_re)
    else:
        so = {"sha": rev_parse(dump, old), "date": commit_date(dump, old),
              "tables": {t: None for t in list_tables(dump, old)}}
        sn = {"sha": rev_parse(dump, new), "date": commit_date(dump, new),
              "tables": {t: None for t in list_tables(dump, new)}}
    result["old"] = {"sha": so["sha"], "date": so["date"]}
    result["new"] = {"sha": sn["sha"], "date": sn["date"]}
    to, tn = so["tables"], sn["tables"]
    result["tables_added"] = sorted(t for t in tn if t not in to)
    result["tables_removed"] = sorted(t for t in to if t not in tn)
    if want_enums:
        fa, fr, ea, er = {}, {}, {}, {}
        for t in sorted(tn):
            if t not in to:
                continue
            o, n = to[t], tn[t]
            if n["fields"] - o["fields"]:
                fa[t] = sorted(n["fields"] - o["fields"])
            if o["fields"] - n["fields"]:
                fr[t] = sorted(o["fields"] - n["fields"])
            for p, vals in n["enums"].items():
                add = vals - o["enums"].get(p, set())
                if add:
                    ea[f"{t}.{p}"] = sorted(add)
            for p, vals in o["enums"].items():
                rem = vals - n["enums"].get(p, set())
                if rem:
                    er[f"{t}.{p}"] = sorted(rem)
        result.update(fields_added=fa, fields_removed=fr, enums_added=ea, enums_removed=er)
        result["row_counts"] = {t: (to[t]["rows"] if t in to else None, tn[t]["rows"]) for t in tn}
    if want_rows:
        rows = {}
        for t in config_tables:
            if table_re is not None and not table_re.search(t):
                continue
            d = diff_rows(load_rows(dump, so["sha"], t), load_rows(dump, sn["sha"], t))
            if d["added"] or d["removed"] or d["modified"]:
                rows[t] = d
        result["rows"] = rows
    if examples and want_enums:
        ex = {}
        for t, f in examples:
            key = f"{t}.{f}"
            vals = [v for k, vs in result["enums_added"].items() if k == key or k == key + "[]" for v in vs]
            if not vals:
                continue
            rows_new = load_rows(dump, sn["sha"], t) or []
            for v in vals:
                r = example_for(rows_new, f, v)
                if r is None:
                    continue
                ex[v] = {"table": t, "id": r.get("id") or r.get("name"),
                         "text": description_text(r),
                         "row": {k: r[k] for k in r if not isinstance(r[k], (list, dict))}}
        result["examples"] = ex
    return result


def fmt_val(v: Any) -> str:
    s = json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= 120 else s[:117] + "..."


def print_report(d: dict[str, Any]) -> None:
    print(f"OLD {d['old']['sha'][:10]} ({d['old']['date']})  ->  NEW {d['new']['sha'][:10]} ({d['new']['date']})")
    if d["tables_added"]:
        print("\n## tables added");  [print("  +", t) for t in d["tables_added"]]
    if d["tables_removed"]:
        print("\n## tables removed"); [print("  -", t) for t in d["tables_removed"]]
    if d.get("fields_added"):
        print("\n## fields added (top-level)")
        for t, fs in d["fields_added"].items():
            print(f"  {t}: {', '.join(fs)}")
    if d.get("fields_removed"):
        print("\n## fields removed (top-level)")
        for t, fs in d["fields_removed"].items():
            print(f"  {t}: {', '.join(fs)}")
    if d.get("enums_added"):
        print("\n## enum values added")
        for k, vs in d["enums_added"].items():
            print(f"  {k}: {', '.join(vs)}")
    if d.get("enums_removed"):
        print("\n## enum values removed")
        for k, vs in d["enums_removed"].items():
            print(f"  {k}: {', '.join(vs)}")
    if d.get("examples"):
        print("\n## examples for new enum values")
        for v, e in d["examples"].items():
            print(f"  {v}  [{e['table']} {e['id']}]")
            if e["text"]:
                print(f"      text: {e['text']}")
    for t, rd in (d.get("rows") or {}).items():
        print(f"\n## rows changed: {t}")
        for r in rd["added"]:
            print(f"  + {fmt_val(row_key(r))}  name={r.get('name', '')}")
        for r in rd["removed"]:
            print(f"  - {fmt_val(row_key(r))}  name={r.get('name', '')}")
        for m in rd["modified"]:
            print(f"  ~ {fmt_val(m['key'])}  name={m.get('name') or ''}")
            for f, (a, b) in m["changes"].items():
                print(f"      {f}: {fmt_val(a)} -> {fmt_val(b)}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dump")
    ap.add_argument("old", nargs="?")
    ap.add_argument("new", nargs="?")
    ap.add_argument("--cache")
    ap.add_argument("--config-tables", default=",".join(DEFAULT_CONFIG_TABLES))
    ap.add_argument("--tables")
    ap.add_argument("--examples", default="")
    ap.add_argument("--json")
    ap.add_argument("--no-rows", action="store_true")
    ap.add_argument("--no-enums", action="store_true")
    ap.add_argument("--summary-only")
    a = ap.parse_args(argv)
    table_re = re.compile(a.tables) if a.tables else None
    if a.summary_only:
        s = summarize(a.dump, a.summary_only, a.cache, None)
        print(f"{s['sha'][:10]} {s['date']} {len(s['tables'])} tables")
        return
    if not (a.old and a.new):
        ap.error("OLD and NEW revisions are required")
    cfg = [t for t in a.config_tables.split(",") if t]
    ex = [tuple(x.split(":", 1)) for x in a.examples.split(",") if ":" in x]
    d = compute_diff(a.dump, a.old, a.new, a.cache, table_re, cfg, not a.no_enums, not a.no_rows, ex)
    print_report(d)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    main()
