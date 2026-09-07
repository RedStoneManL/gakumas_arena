#!/usr/bin/env python3
"""Inspect a gakumasu-diff style master-data dump (one YAML file per table).

Usage:
  python tools/masterdata/inspect_dump.py DUMP_DIR [options]

Sub-commands (combine freely):
  --tables            per-table row counts + field sets (default when nothing else given)
  --enums             all enum-valued fields (values like SomeType_Value) with value counts
  --enum NAME         dump every distinct value (with counts) of one enum family, e.g.
                      --enum ProduceExamEffectType   (matches by the prefix before "_")
  --table NAME        field-level detail for one table: type(s), null/empty ratio,
                      distinct count, sample values, and FK candidates
  --sample NAME N     print N raw rows of a table (YAML-ish, trimmed)
  --fk                infer foreign keys: for every field whose name ends in Id/Ids and
                      whose values join >= 90% into some table's `id` column
  --grep REGEX        case-insensitive regex search over every scalar string in the dump;
                      reports table/field/count
  --json OUT          write the full inspection result (tables, fields, enums, fks) as JSON
  --cache FILE        pickle cache of the parsed dump (created if missing) - parsing the
                      full dump (~200MB YAML) takes ~1-2 minutes with libyaml, so cache it.

Loading uses yaml.CSafeLoader when available (libyaml).  Nested lists of dicts
(e.g. `produceDescriptions`) are flattened for field/enum statistics with a
`parent.child` path.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pickle
import re
import sys
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("pyyaml is required: pip install pyyaml")

Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
ENUM_RE = re.compile(r"^[A-Z][A-Za-z0-9]+_[A-Za-z0-9_]+$")

# --------------------------------------------------------------------------- loading


def load_dump(dump_dir: str, cache: str | None = None) -> dict[str, list[dict]]:
    """Return {table_name: [row, ...]}. Uses/creates a pickle cache if given."""
    if cache and os.path.exists(cache):
        with open(cache, "rb") as fh:
            return pickle.load(fh)
    tables: dict[str, list[dict]] = {}
    names = sorted(f for f in os.listdir(dump_dir) if f.endswith((".yaml", ".yml")))
    for i, fn in enumerate(names, 1):
        path = os.path.join(dump_dir, fn)
        data = _load_one(path)
        if data is None:
            data = []
        if not isinstance(data, list):
            data = [data]
        tables[fn.rsplit(".", 1)[0]] = data
        print(f"[{i}/{len(names)}] {fn}: {len(data)} rows", file=sys.stderr)
    if cache:
        with open(cache, "wb") as fh:
            pickle.dump(tables, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return tables


def _load_one(path: str):
    """Parse one YAML table; tolerate stray CRs / libyaml strictness."""
    with open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    try:
        return yaml.load(text, Loader=Loader)
    except yaml.YAMLError as e1:
        # e.g. Localization.yaml has a raw "\r" right after a block-scalar "|"
        # Localization.yaml: "key: |\r<text>" -> a block indicator with the text on
        # the same line; turn it into a plain scalar
        fixed = re.sub(r":\s*\|-?\r(?=[^\n])", ": ", text)
        fixed = fixed.replace("\r\n", "\n").replace("\r", "\n")
        fixed = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", fixed)  # Rule.yaml has \x0b
        for ld in (Loader, yaml.SafeLoader):
            try:
                return yaml.load(fixed, Loader=ld)
            except yaml.YAMLError:
                continue
        print(f"WARNING: could not parse {path}: {e1}", file=sys.stderr)
        return []


# --------------------------------------------------------------------------- helpers


def type_name(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, list):
        if not v:
            return "list[]"
        inner = {type_name(x) for x in v}
        return "list[" + "|".join(sorted(inner)) + "]"
    if isinstance(v, dict):
        return "dict"
    return type(v).__name__


def walk_fields(row: dict, prefix: str = "") -> Iterable[tuple[str, Any]]:
    """Yield (path, value) for scalar / list fields, descending into dict-lists."""
    for k, v in row.items():
        path = f"{prefix}{k}"
        if isinstance(v, dict):
            yield from walk_fields(v, path + ".")
        elif isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            yield path, v  # keep the list so the type shows as list[dict]
            for item in v:
                yield from walk_fields(item, path + ".")
        else:
            yield path, v


NON_ENUM_LEAVES = {"id", "name", "text", "template", "description", "assetId"}


def is_enum(v: Any) -> bool:
    return isinstance(v, str) and bool(ENUM_RE.match(v)) and not v.startswith(("Label_", "Description_", "Swap_"))


def enum_field_path(path: str) -> bool:
    """Only consider fields whose leaf name is not an id/name/text field."""
    leaf = path.rsplit(".", 1)[-1]
    return leaf not in NON_ENUM_LEAVES and not leaf.endswith(("Id", "Ids"))


def scalars(v: Any) -> Iterable[Any]:
    if isinstance(v, list):
        for x in v:
            yield from scalars(x)
    elif isinstance(v, dict):
        for x in v.values():
            yield from scalars(x)
    else:
        yield v


# --------------------------------------------------------------------------- analysis


class FieldStat:
    __slots__ = ("types", "n", "empty", "distinct", "samples", "enum_values", "track_enums")

    def __init__(self, track_enums: bool = True) -> None:
        self.track_enums = track_enums
        self.types: collections.Counter[str] = collections.Counter()
        self.n = 0
        self.empty = 0
        self.distinct: set = set()
        self.samples: list = []
        self.enum_values: collections.Counter[str] = collections.Counter()

    def add(self, v: Any) -> None:
        self.n += 1
        self.types[type_name(v)] += 1
        if v in (None, "", [], 0, False):
            self.empty += 1
        for s in scalars(v):
            if isinstance(s, (str, int, float, bool)) or s is None:
                if len(self.distinct) < 5000:
                    self.distinct.add(s)
            if self.track_enums and is_enum(s):
                self.enum_values[s] += 1
        if len(self.samples) < 5 and v not in (None, "", []) and v not in self.samples:
            self.samples.append(v)


def analyse(tables: dict[str, list[dict]]) -> dict[str, dict[str, FieldStat]]:
    out: dict[str, dict[str, FieldStat]] = {}
    for t, rows in tables.items():
        fs: dict[str, FieldStat] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            for path, v in walk_fields(row):
                fs.setdefault(path, FieldStat(enum_field_path(path))).add(v)
        out[t] = fs
    return out


def id_index(tables: dict[str, list[dict]]) -> dict[str, set]:
    """{table: set(id values)} for tables that have an `id` column."""
    idx = {}
    for t, rows in tables.items():
        ids = {r.get("id") for r in rows if isinstance(r, dict) and "id" in r}
        ids.discard(None)
        if ids:
            idx[t] = ids
    return idx


def infer_fks(tables: dict[str, list[dict]], stats, threshold: float = 0.9):
    """Return list of (table, field, target_table, matched, total, ratio)."""
    idx = id_index(tables)
    results = []
    for t, fs in stats.items():
        for path, st in fs.items():
            leaf = path.rsplit(".", 1)[-1]
            if not (leaf.endswith("Id") or leaf.endswith("Ids")) or leaf == "id":
                continue
            vals = [v for v in st.distinct if isinstance(v, str) and v]
            if not vals:
                continue
            best = None
            for tt, ids in idx.items():
                m = sum(1 for v in vals if v in ids)
                if m and (best is None or m > best[1]):
                    best = (tt, m)
            if best:
                ratio = best[1] / len(vals)
                if ratio >= threshold:
                    results.append((t, path, best[0], best[1], len(vals), ratio))
                else:
                    results.append((t, path, best[0] + "?", best[1], len(vals), ratio))
            else:
                results.append((t, path, None, 0, len(vals), 0.0))
    return results


def enum_families(stats) -> dict[str, collections.Counter]:
    fam: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for t, fs in stats.items():
        for path, st in fs.items():
            for v, c in st.enum_values.items():
                fam[v.split("_", 1)[0]][v] += c
    return fam


def enum_fields(stats):
    """[(table, field, Counter)] for fields whose non-empty values are all enum-like."""
    out = []
    for t, fs in stats.items():
        for path, st in fs.items():
            if not st.enum_values:
                continue
            nonempty = [v for v in st.distinct if isinstance(v, str) and v]
            if nonempty and all(is_enum(v) for v in nonempty):
                out.append((t, path, st.enum_values))
    return out


def grep(tables, pattern: str):
    rx = re.compile(pattern, re.I)
    hits: collections.Counter = collections.Counter()
    examples: dict = {}
    for t, rows in tables.items():
        for row in rows:
            if not isinstance(row, dict):
                continue
            for path, v in walk_fields(row):
                for s in scalars(v):
                    if isinstance(s, str) and rx.search(s):
                        hits[(t, path)] += 1
                        examples.setdefault((t, path), s[:120])
    return hits, examples


def trim(v: Any, maxlen: int = 80) -> Any:
    if isinstance(v, str) and len(v) > maxlen:
        return v[: maxlen - 1] + "…"
    if isinstance(v, list):
        return [trim(x, maxlen) for x in v[:4]] + (["…(%d more)" % (len(v) - 4)] if len(v) > 4 else [])
    if isinstance(v, dict):
        return {k: trim(x, maxlen) for k, x in v.items()}
    return v


# --------------------------------------------------------------------------- main


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dump_dir")
    ap.add_argument("--cache")
    ap.add_argument("--tables", action="store_true")
    ap.add_argument("--enums", action="store_true")
    ap.add_argument("--enum")
    ap.add_argument("--table")
    ap.add_argument("--sample", nargs=2, metavar=("NAME", "N"))
    ap.add_argument("--fk", action="store_true")
    ap.add_argument("--grep")
    ap.add_argument("--json")
    a = ap.parse_args(argv)

    tables = load_dump(a.dump_dir, a.cache)
    stats = analyse(tables)
    nothing = not any([a.tables, a.enums, a.enum, a.table, a.sample, a.fk, a.grep, a.json])

    if a.tables or nothing:
        print(f"# {len(tables)} tables")
        for t in sorted(tables):
            print(f"{t}\t{len(tables[t])}\t{', '.join(sorted(stats[t]))}")

    if a.table:
        t = a.table
        print(f"# {t}: {len(tables[t])} rows")
        for path, st in stats[t].items():
            ty = "|".join(f"{k}" for k, _ in st.types.most_common())
            print(f"- {path}: {ty}; n={st.n} empty/zero={st.empty} distinct={len(st.distinct)}"
                  f"{'+' if len(st.distinct) >= 5000 else ''}; samples={trim(st.samples[:3], 60)}")

    if a.sample:
        t, n = a.sample[0], int(a.sample[1])
        print(yaml.safe_dump(trim(tables[t][:n]), allow_unicode=True, sort_keys=False))

    if a.enums:
        for t, path, cnt in enum_fields(stats):
            print(f"{t}.{path}: " + ", ".join(f"{v}={c}" for v, c in sorted(cnt.items())))
        print("\n# enum families (prefix before '_'):")
        for fam, cnt in sorted(enum_families(stats).items()):
            print(f"{fam} ({len(cnt)} values): " + ", ".join(f"{v.split('_',1)[1]}={c}" for v, c in sorted(cnt.items())))

    if a.enum:
        fam = enum_families(stats).get(a.enum, {})
        where = collections.defaultdict(collections.Counter)
        for t, fs in stats.items():
            for path, st in fs.items():
                for v, c in st.enum_values.items():
                    if v.split("_", 1)[0] == a.enum:
                        where[v][f"{t}.{path}"] += c
        for v, c in sorted(fam.items()):
            print(f"{v}\t{c}\t" + "; ".join(f"{k}={n}" for k, n in where[v].most_common(6)))

    if a.fk:
        for t, path, target, m, n, r in sorted(infer_fks(tables, stats)):
            print(f"{t}.{path} -> {target} ({m}/{n} = {r:.2f})")

    if a.grep:
        hits, ex = grep(tables, a.grep)
        for (t, path), c in sorted(hits.items(), key=lambda kv: -kv[1]):
            print(f"{t}.{path}\t{c}\t{ex[(t, path)]!r}")

    if a.json:
        doc = {
            "tables": {t: {"rows": len(rows), "fields": {
                p: {"types": dict(st.types), "n": st.n, "empty": st.empty,
                    "distinct": len(st.distinct), "samples": trim(st.samples[:3]),
                    "enum_values": dict(st.enum_values)} for p, st in fs.items()}}
                for t, rows in tables.items() for fs in [stats[t]]},
            "enum_families": {k: dict(v) for k, v in enum_families(stats).items()},
            "fks": [list(x) for x in infer_fks(tables, stats)],
        }
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        print(f"wrote {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
