#!/usr/bin/env python3
"""New-mechanic detector: which master-data enum values does the vendored gakumas_rl engine handle?

Scans the datamined dump (data/raw/gakumasu-diff by default) for every value of

  * ProduceExamEffectType      (ProduceExamEffect.effectType)        - exam/lesson card effects
  * ProduceEffectType          (ProduceEffect.produceEffectType)     - produce (outer loop) effects
  * ProduceExamPhaseType       (ProduceExamTrigger.phaseTypes)       - trigger phases
  * ProduceExamStatusEnchant   (derived: the enchant's effect types + trigger phases; the table
                                has no type enum of its own)
  * ProduceCardGrowEffectType  (ProduceCardGrowEffect.effectType)    - card grow effects
  * ProduceStepType            (stepType fields of the ProduceStep* / Produce tables)

and compares them with what `gakumas_rl` handles.  Handled values are discovered by importing
gakumas_rl's registries / ids modules (EXAM_EFFECT_REGISTRY, ids.ExamEffect/GrowEffect/ExamPhase,
produce.runtime.ACTION_STEP_TYPES) and, as a fallback, by grepping the package source for the
literal enum strings (the approach of gakumas_rl/_scripts/generate_effect_coverage_matrix.py).

Status per value:
  handled     registered in a dispatch registry / constants module, or dispatched by literal
              string inside the responsible function (``_apply_produce_effect``)
  referenced  the literal string only appears somewhere in gakumas_rl source (may be a partial
              or indirect implementation - review manually)
  unhandled   never mentioned; for exam effects this means the registry's *fallback* handler
              silently treats the effect as a generic timed effect.

Outputs docs/research/engine_coverage.md and data/coverage.json.  With --strict the exit code
is 1 when any value is unhandled (rerun after every dump update; a non-zero exit = new mechanic).

Usage:
  python tools/masterdata/coverage.py [--dump DIR] [--md PATH] [--json PATH] [--strict]
                                      [--max-owners N] [--fail-on-referenced]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from gakumas_arena.masterdata.store import MasterData, default_dump_dir  # noqa: E402

GAKUMAS_RL_DIR = REPO_ROOT / "gakumas_rl"
DEFAULT_MD = REPO_ROOT / "docs" / "research" / "engine_coverage.md"
DEFAULT_JSON = REPO_ROOT / "data" / "coverage.json"
PROVENANCE = REPO_ROOT / "third_party" / "gakumas_rl_upstream" / "PROVENANCE.txt"

SENTINEL_SUFFIXES = ("_Unknown", "_None")

# Tables whose rows are scanned for id references (to answer "which card/item uses this?").
REFERENCE_TABLES = (
    "ProduceCard",
    "ProduceItem",
    "ProduceItemEffect",
    "ProduceDrink",
    "ProduceDrinkEffect",
    "ProduceExamEffect",
    "ProduceExamStatusEnchant",
    "ProduceCardStatusEnchant",
    "ProduceCardGrowEffect",
    "ProduceExamTrigger",
    "ProduceEffect",
    "ProduceExamGimmickEffectGroup",
    "ProduceSkill",
    "SupportCard",
    "ProduceStepEventDetail",
    "ProduceCustomizeItem",
    "ProduceGrowthPanel",
    "IdolCard",
)
REFERENCE_TABLE_GLOBS = ("SupportCardProduceSkill*",)
# Terminal "owner" tables: BFS over reverse references stops here.
OWNER_TABLES = {
    "ProduceCard": "name",
    "ProduceItem": "name",
    "ProduceDrink": "name",
    "SupportCard": "name",
    "IdolCard": "name",
    "ProduceSkill": None,
    "ProduceCustomizeItem": "name",
    "ProduceStepEventDetail": None,
    "ProduceExamGimmickEffectGroup": None,
    "ProduceGrowthPanel": None,
}
# Tables scanned for ProduceStepType values (top-level / nested, excluding description blobs).
STEP_TYPE_TABLES = (
    "Produce",
    "ProduceStepTransition",
    "ProduceStepEventSuggestion",
    "ProduceStepAuditionDifficulty",
    "ProduceStepLesson",
    "ProduceStepOpenLesson",
    "ProduceStepSelfLesson",
    "ProduceStepFanPresentMotion",
    "ProduceStepAuditionCharacter",
    "TutorialProduceStep",
    "ProduceGrowthPanel",
    "ProduceSkill",
    "SupportCard",
    "ProduceExamTrigger",
    "ProduceCardSearch",
)
SKIP_KEYS = {"produceDescriptions", "produceDescriptionSwapId"}

# gakumas_rl handles these step types through its action-type vocabulary (ProduceRuntime) without
# ever spelling the enum string; assert the mapping here so the detector does not cry wolf.
# Keep this list honest: only add a value after checking the runtime really implements the step.
STEP_TYPE_ACTION_ALIASES: dict[str, str] = {
    "ProduceStepType_LessonVocalSp": "lesson_vocal_sp",
    "ProduceStepType_LessonDanceSp": "lesson_dance_sp",
    "ProduceStepType_LessonVisualSp": "lesson_visual_sp",
    "ProduceStepType_Refresh": "refresh",
    "ProduceStepType_EventSchool": "school_class",
    "ProduceStepType_EventActivity": "activity / activity_supply",
    "ProduceStepType_Business": "business",
    "ProduceStepType_Present": "present",
}


# --------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------
def _is_sentinel(value: str) -> bool:
    return value.endswith(SENTINEL_SUFFIXES)


def _walk_strings(obj: Any, skip_keys: set[str] = SKIP_KEYS) -> Iterator[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if key in skip_keys:
                continue
            yield from _walk_strings(value, skip_keys)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_strings(item, skip_keys)


def _source_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "_scripts" not in p.parts)


def _source_tokens(files: Iterable[Path], prefix: str) -> set[str]:
    pattern = re.compile(rf"{re.escape(prefix)}[A-Za-z0-9_]+")
    tokens: set[str] = set()
    for path in files:
        tokens.update(pattern.findall(path.read_text(encoding="utf-8")))
    return tokens


def _function_tokens(path: Path, func_name: str, prefix: str) -> set[str]:
    """Enum strings used inside one method body (upstream's approach for ``_apply_produce_effect``)."""
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"\n(\s*)def {re.escape(func_name)}\(", text)
    if not match:
        return set()
    indent = match.group(1)
    body_start = match.end()
    next_def = re.search(rf"\n{indent}(?:def |@|class )", text[body_start:])
    body = text[body_start : body_start + next_def.start()] if next_def else text[body_start:]
    return set(re.findall(rf"{re.escape(prefix)}[A-Za-z0-9_]+", body))


def _class_constants(cls: type, prefix: str) -> set[str]:
    return {v for k, v in vars(cls).items() if isinstance(v, str) and v.startswith(prefix)}


def _dump_version(dump: Path) -> dict[str, str]:
    info: dict[str, str] = {"path": str(dump)}
    try:
        info["commit"] = subprocess.check_output(
            ["git", "-C", str(dump), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        info["commit_date"] = subprocess.check_output(
            ["git", "-C", str(dump), "log", "-1", "--format=%cI"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    meta = dump.parent / "masterdata_json" / "_meta.json"
    if meta.exists():
        try:
            info["cache_meta"] = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return info


# --------------------------------------------------------------------------------------------
# what gakumas_rl handles
# --------------------------------------------------------------------------------------------
class EngineCapabilities:
    """Handled / referenced enum sets discovered from the vendored gakumas_rl package."""

    def __init__(self, package_dir: Path = GAKUMAS_RL_DIR) -> None:
        self.package_dir = package_dir
        files = _source_files(package_dir)
        exam_files = [p for p in files if "simulation" in p.parts and "exam" in p.parts]
        produce_files = [p for p in files if "simulation" in p.parts and "produce" in p.parts]
        self.import_errors: dict[str, str] = {}

        # --- exam effects: registry (exact + prefix); fallback handler = NOT handled ---
        self.exam_exact: set[str] = set()
        self.exam_prefixes: list[str] = []
        try:
            from gakumas_rl.simulation.exam.effects.registry import EXAM_EFFECT_REGISTRY

            self.exam_exact = set(EXAM_EFFECT_REGISTRY._exact_handlers)
            self.exam_prefixes = [prefix for prefix, _ in EXAM_EFFECT_REGISTRY._prefix_handlers]
        except Exception as exc:  # noqa: BLE001 - fall back to grep
            self.import_errors["exam_registry"] = f"{type(exc).__name__}: {exc}"
        self.exam_referenced = _source_tokens(exam_files, "ProduceExamEffectType_")
        self.exam_constants: set[str] = set()
        self.grow_constants: set[str] = set()
        self.phase_constants: set[str] = set()
        try:
            from gakumas_rl.simulation.exam import ids

            self.exam_constants = _class_constants(ids.ExamEffect, "ProduceExamEffectType_")
            self.grow_constants = _class_constants(ids.GrowEffect, "ProduceCardGrowEffectType_")
            self.phase_constants = _class_constants(ids.ExamPhase, "ProduceExamPhaseType_")
        except Exception as exc:  # noqa: BLE001
            self.import_errors["exam_ids"] = f"{type(exc).__name__}: {exc}"
        if not self.exam_exact and not self.exam_prefixes:
            # grep fallback: treat anything spelled in the effects package as handled
            self.exam_exact = _source_tokens([p for p in exam_files if "effects" in p.parts], "ProduceExamEffectType_")

        # --- grow effects / trigger phases: constants + literal use in the exam simulation ---
        self.grow_referenced = _source_tokens(exam_files, "ProduceCardGrowEffectType_")
        self.phase_referenced = _source_tokens(exam_files, "ProduceExamPhaseType_")

        # --- produce effects: dispatched by literal inside _apply_produce_effect ---
        produce_runtime = package_dir / "simulation" / "produce" / "runtime.py"
        self.produce_handled = _function_tokens(produce_runtime, "_apply_produce_effect", "ProduceEffectType_")
        self.produce_referenced = _source_tokens(produce_files, "ProduceEffectType_")

        # --- produce steps: ACTION_STEP_TYPES + literals + manual alias map ---
        self.step_handled: set[str] = set()
        try:
            from gakumas_rl.simulation.produce.runtime import ACTION_STEP_TYPES

            self.step_handled = set(ACTION_STEP_TYPES.values())
        except Exception as exc:  # noqa: BLE001
            self.import_errors["produce_runtime"] = f"{type(exc).__name__}: {exc}"
        self.step_handled |= _source_tokens(files, "ProduceStepType_")
        self.step_handled |= set(STEP_TYPE_ACTION_ALIASES)
        self.step_handled = {v for v in self.step_handled if not _is_sentinel(v)}

    # status helpers -------------------------------------------------------------------------
    def exam_status(self, value: str) -> tuple[str, str]:
        if value in self.exam_exact:
            return "handled", "registry exact"
        for prefix in self.exam_prefixes:
            if value.startswith(prefix):
                return "handled", f"registry prefix {prefix}"
        if value in self.exam_constants:
            return "referenced", "ids.ExamEffect constant only"
        if value in self.exam_referenced:
            return "referenced", "literal in simulation/exam"
        return "unhandled", "falls through to registry fallback (generic timed effect)"

    def produce_status(self, value: str) -> tuple[str, str]:
        if value in self.produce_handled:
            return "handled", "_apply_produce_effect"
        if value in self.produce_referenced:
            return "referenced", "literal in simulation/produce"
        return "unhandled", "not in _apply_produce_effect"

    def phase_status(self, value: str) -> tuple[str, str]:
        if value in self.phase_referenced or value in self.phase_constants:
            return "handled", "dispatched in simulation/exam"
        return "unhandled", "never dispatched by ExamRuntime"

    def grow_status(self, value: str) -> tuple[str, str]:
        if value in self.grow_constants or value in self.grow_referenced:
            return "handled", "ids.GrowEffect / simulation/exam"
        return "unhandled", "not in ids.GrowEffect"

    def step_status(self, value: str) -> tuple[str, str]:
        if value in STEP_TYPE_ACTION_ALIASES:
            return "handled", f"ProduceRuntime action `{STEP_TYPE_ACTION_ALIASES[value]}`"
        if value in self.step_handled:
            return "handled", "ProduceRuntime / ScenarioSpec literal"
        return "unhandled", "no ProduceRuntime action"


# --------------------------------------------------------------------------------------------
# reverse reference graph (which card / item / support card uses an effect row?)
# --------------------------------------------------------------------------------------------
class ReferenceGraph:
    def __init__(self, md: MasterData) -> None:
        self.md = md
        tables = list(REFERENCE_TABLES)
        for pattern in REFERENCE_TABLE_GLOBS:
            tables.extend(p.stem for p in md.dump.glob(f"{pattern}.yaml"))
        self.tables = [t for t in dict.fromkeys(tables) if t in md]
        self.id_table: dict[str, str] = {}
        self.names: dict[str, str] = {}
        for table in self.tables:
            name_field = OWNER_TABLES.get(table)
            for row in md.table(table):
                row_id = row.get("id")
                if isinstance(row_id, str) and row_id:
                    self.id_table.setdefault(row_id, table)
                    if name_field and row.get(name_field):
                        self.names[row_id] = str(row[name_field])
        self.parents: dict[str, set[str]] = defaultdict(set)  # ref_id -> {row_id that references it}
        for table in self.tables:
            for row in md.table(table):
                row_id = row.get("id")
                if not isinstance(row_id, str):
                    continue
                for value in _walk_strings(row):
                    if value != row_id and value in self.id_table:
                        self.parents[value].add(row_id)

    def owners(self, row_id: str, max_depth: int = 6) -> list[str]:
        """Terminal owner ids (cards/items/...) reachable by walking references upwards."""
        seen = {row_id}
        frontier = [row_id]
        found: set[str] = set()
        for _ in range(max_depth):
            nxt: list[str] = []
            for node in frontier:
                for parent in self.parents.get(node, ()):
                    if parent in seen:
                        continue
                    seen.add(parent)
                    if self.id_table.get(parent) in OWNER_TABLES:
                        found.add(parent)
                    else:
                        nxt.append(parent)
            frontier = nxt
            if not frontier:
                break
        return sorted(found)

    def label(self, owner_id: str) -> str:
        table = self.id_table.get(owner_id, "?")
        name = self.names.get(owner_id)
        return f"{table}:{owner_id}" + (f" ({name})" if name else "")


# --------------------------------------------------------------------------------------------
# dimension scans
# --------------------------------------------------------------------------------------------
def _value_entry(status: str, reason: str) -> dict[str, Any]:
    return {"status": status, "reason": reason, "rows": 0, "row_ids": [], "owners": Counter()}


def scan_enum_table(
    md: MasterData, graph: ReferenceGraph, table: str, field: str, status_fn, list_field: bool = False
) -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for row in md.table(table):
        raw = row.get(field)
        items = raw if list_field else [raw]
        for value in items or []:
            if not isinstance(value, str) or _is_sentinel(value) or not value:
                continue
            entry = values.get(value)
            if entry is None:
                entry = values[value] = _value_entry(*status_fn(value))
            entry["rows"] += 1
            row_id = str(row.get("id") or "")
            if len(entry["row_ids"]) < 5:
                entry["row_ids"].append(row_id)
            if entry["status"] != "handled" and row_id:
                for owner in graph.owners(row_id):
                    entry["owners"][owner] += 1
    return values


def scan_status_enchants(
    md: MasterData, graph: ReferenceGraph, caps: EngineCapabilities
) -> dict[str, dict[str, Any]]:
    """Derived coverage: an enchant is unhandled if any of its effects / trigger phases is."""
    effects = md.by_id("ProduceExamEffect")
    triggers = md.by_id("ProduceExamTrigger")
    values: dict[str, dict[str, Any]] = {}
    for row in md.table("ProduceExamStatusEnchant"):
        components: list[tuple[str, str, str]] = []  # (kind, value, status)
        for eff_id in row.get("produceExamEffectIds") or []:
            eff = effects.get(str(eff_id))
            etype = str(eff.get("effectType") or "") if eff else ""
            if etype and not _is_sentinel(etype):
                components.append(("effect", etype, caps.exam_status(etype)[0]))
        trig = triggers.get(str(row.get("produceExamTriggerId") or ""))
        for phase in (trig or {}).get("phaseTypes") or []:
            if isinstance(phase, str) and not _is_sentinel(phase):
                components.append(("phase", phase, caps.phase_status(phase)[0]))
        worst = "handled"
        for _, _, status in components:
            if status == "unhandled":
                worst = "unhandled"
                break
            if status == "referenced":
                worst = "referenced"
        # group enchants by the component signature that makes them (un)handled
        key = "handled" if worst == "handled" else " + ".join(
            sorted({f"{kind}:{value}" for kind, value, status in components if status == worst})
        )
        entry = values.get(key)
        if entry is None:
            entry = values[key] = _value_entry(worst, "all components handled" if worst == "handled" else f"contains {worst} component(s)")
        entry["rows"] += 1
        row_id = str(row.get("id") or "")
        if len(entry["row_ids"]) < 5:
            entry["row_ids"].append(row_id)
        if worst != "handled":
            for owner in graph.owners(row_id):
                entry["owners"][owner] += 1
    return values


def scan_step_types(md: MasterData, graph: ReferenceGraph, caps: EngineCapabilities) -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for table in STEP_TYPE_TABLES:
        if table not in md:
            continue
        for row in md.table(table):
            found = {v for v in _walk_strings(row) if v.startswith("ProduceStepType_") and not _is_sentinel(v)}
            for value in found:
                entry = values.get(value)
                if entry is None:
                    entry = values[value] = _value_entry(*caps.step_status(value))
                    entry["tables"] = Counter()
                entry["rows"] += 1
                entry["tables"][table] += 1
                row_id = str(row.get("id") or row.get("characterId") or "")
                if entry["status"] != "handled" and row_id:
                    entry["owners"][f"{table}:{row_id}"] += 1
                    # Produce steps: attribute to the produce ids listed on the row
                    for pid in row.get("produceIds") or []:
                        entry["owners"][f"Produce:{pid}"] += 1
    return values


# --------------------------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------------------------
DIMENSIONS = (
    ("exam_effect_type", "ProduceExamEffectType", "ProduceExamEffect.effectType"),
    ("produce_effect_type", "ProduceEffectType", "ProduceEffect.produceEffectType"),
    ("trigger_phase_type", "ProduceExamPhaseType", "ProduceExamTrigger.phaseTypes[]"),
    ("status_enchant", "ProduceExamStatusEnchant (derived)", "ProduceExamStatusEnchant.produceExamEffectIds[].effectType + produceExamTriggerId.phaseTypes[]"),
    ("grow_effect_type", "ProduceCardGrowEffectType", "ProduceCardGrowEffect.effectType"),
    ("produce_step_type", "ProduceStepType", "stepType fields of Produce / ProduceStep* tables"),
)


def _summarize(values: dict[str, dict[str, Any]]) -> dict[str, int]:
    summary = Counter()
    rows = Counter()
    for entry in values.values():
        summary[entry["status"]] += 1
        rows[entry["status"]] += entry["rows"]
    return {
        "values": len(values),
        "handled": summary["handled"],
        "referenced": summary["referenced"],
        "unhandled": summary["unhandled"],
        "rows_unhandled": rows["unhandled"],
        "rows_referenced": rows["referenced"],
    }


def _owner_text(graph: ReferenceGraph, owners: Counter, max_owners: int) -> str:
    if not owners:
        return "-"
    parts = []
    for owner, count in owners.most_common(max_owners):
        label = graph.label(owner) if owner in graph.id_table else owner
        parts.append(f"{label} ×{count}" if count > 1 else label)
    extra = len(owners) - max_owners
    if extra > 0:
        parts.append(f"… +{extra} more")
    return "; ".join(parts)


def render_markdown(report: dict[str, Any], graph: ReferenceGraph, max_owners: int) -> str:
    esc = lambda s: str(s).replace("|", "\\|")  # noqa: E731
    lines = [
        "# gakumas_rl engine coverage of the master-data dump",
        "",
        f"Generated by `tools/masterdata/coverage.py` on {report['generated_at']} — rerun after every dump update; "
        "`--strict` exits 1 when anything is unhandled.",
        "",
        f"- dump: `{report['dump'].get('path')}` @ `{report['dump'].get('commit', '?')[:12]}` ({report['dump'].get('commit_date', '?')})",
        f"- engine: `gakumas_rl/` vendored from {report['engine'].get('upstream', '?')}",
        "",
        "Status legend: **handled** = dispatched by a registry / constants module / the responsible function; "
        "**referenced** = the literal only appears somewhere in gakumas_rl source (partial or indirect — review); "
        "**unhandled** = never mentioned (exam effects then silently hit the registry *fallback* timed-effect handler, "
        "trigger phases are never fired, produce steps have no action).",
        "",
        "## Summary",
        "",
        "| dimension | source field | values | handled | referenced | unhandled | rows unhandled |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, title, source in DIMENSIONS:
        s = report["dimensions"][key]["summary"]
        lines.append(f"| {title} | `{esc(source)}` | {s['values']} | {s['handled']} | {s['referenced']} | {s['unhandled']} | {s['rows_unhandled']} |")
    if report["engine"].get("import_errors"):
        lines += ["", "> gakumas_rl import problems (grep fallback used): " + "; ".join(f"`{k}`: {v}" for k, v in report["engine"]["import_errors"].items())]

    for key, title, source in DIMENSIONS:
        dim = report["dimensions"][key]
        lines += ["", f"## {title}", "", f"Source: `{esc(source)}`", ""]
        problem = [(v, e) for v, e in dim["values"].items() if e["status"] != "handled"]
        if not problem:
            lines.append("All values handled.")
        else:
            lines += [
                "| value | status | rows | reason | used by |",
                "| --- | --- | ---: | --- | --- |",
            ]
            for value, entry in sorted(problem, key=lambda kv: ({"unhandled": 0, "referenced": 1}[kv[1]["status"]], -kv[1]["rows"], kv[0])):
                tables = ""
                if entry.get("tables"):
                    tables = " (" + ", ".join(f"{t}×{c}" for t, c in sorted(entry["tables"].items())) + ")"
                owner_counter = Counter(entry["owners"])
                lines.append(
                    f"| `{esc(value)}` | {entry['status']} | {entry['rows']}{esc(tables)} | {esc(entry['reason'])} | {esc(_owner_text(graph, owner_counter, max_owners))} |"
                )
        handled = sorted(v for v, e in dim["values"].items() if e["status"] == "handled")
        if handled:
            lines += ["", "<details><summary>handled values (" + str(len(handled)) + ")</summary>", ""]
            lines.append(", ".join(f"`{esc(v)}`" for v in handled))
            lines += ["", "</details>"]
    lines += [
        "",
        "## Notes",
        "",
        "- `ProduceExamStatusEnchant` rows have no type enum; an enchant is classified by the worst status among the "
        "`ProduceExamEffect` rows it lists and the phases of its trigger. Rows are grouped by the offending component signature.",
        "- `ProduceStepType` handling is inferred from `ProduceRuntime.ACTION_STEP_TYPES`, literals in the package and the manual "
        "`STEP_TYPE_ACTION_ALIASES` map in the script (steps the runtime implements under an action name).",
        "- Exam effect *handled* means the type is registered in `EXAM_EFFECT_REGISTRY` (exact or `ExamLesson*` prefix). The registry "
        "has a fallback handler, so an unhandled type does **not** raise at runtime — this report is the only signal.",
        "- Description tables (`produceDescriptions`) are ignored when scanning, so localisation-only references do not count as usage.",
        "",
    ]
    return "\n".join(lines)


def _jsonable(values: dict[str, dict[str, Any]], graph: ReferenceGraph, max_owners: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for value, entry in sorted(values.items()):
        owners = Counter(entry["owners"])
        out[value] = {
            "status": entry["status"],
            "reason": entry["reason"],
            "rows": entry["rows"],
            "example_row_ids": entry["row_ids"],
            "owners": [
                {"id": o, "table": graph.id_table.get(o, o.split(":", 1)[0]), "name": graph.names.get(o), "count": c}
                for o, c in owners.most_common(max_owners)
            ],
            "owner_total": len(owners),
        }
        if entry.get("tables"):
            out[value]["tables"] = dict(entry["tables"])
    return out


def build_report(dump: Path, max_owners: int) -> tuple[dict[str, Any], ReferenceGraph]:
    md = MasterData(dump)
    caps = EngineCapabilities()
    graph = ReferenceGraph(md)
    dims = {
        "exam_effect_type": scan_enum_table(md, graph, "ProduceExamEffect", "effectType", caps.exam_status),
        "produce_effect_type": scan_enum_table(md, graph, "ProduceEffect", "produceEffectType", caps.produce_status),
        "trigger_phase_type": scan_enum_table(md, graph, "ProduceExamTrigger", "phaseTypes", caps.phase_status, list_field=True),
        "status_enchant": scan_status_enchants(md, graph, caps),
        "grow_effect_type": scan_enum_table(md, graph, "ProduceCardGrowEffect", "effectType", caps.grow_status),
        "produce_step_type": scan_step_types(md, graph, caps),
    }
    upstream = PROVENANCE.read_text(encoding="utf-8").strip() if PROVENANCE.exists() else None
    report = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "dump": _dump_version(dump),
        "engine": {"upstream": upstream, "import_errors": caps.import_errors},
        "dimensions": {
            key: {"title": title, "source": source, "summary": _summarize(dims[key]), "values": _jsonable(dims[key], graph, max_owners)}
            for key, title, source in DIMENSIONS
        },
    }
    # keep the Counter-based entries for markdown rendering
    report["_raw"] = dims
    return report, graph


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dump", type=Path, default=None, help="dump directory (default: data/raw/gakumasu-diff or $GAKUMAS_MASTERDATA_DIR)")
    ap.add_argument("--md", type=Path, default=DEFAULT_MD)
    ap.add_argument("--json", type=Path, default=DEFAULT_JSON)
    ap.add_argument("--max-owners", type=int, default=8)
    ap.add_argument("--strict", action="store_true", help="exit 1 if any value is unhandled")
    ap.add_argument("--fail-on-referenced", action="store_true", help="with --strict, also fail on 'referenced'")
    args = ap.parse_args(argv)

    dump = args.dump or default_dump_dir()
    report, graph = build_report(dump, args.max_owners)
    raw = report.pop("_raw")
    md_report = dict(report)
    md_report["dimensions"] = {
        key: {**report["dimensions"][key], "values": raw[key]} for key in raw
    }
    args.md.parent.mkdir(parents=True, exist_ok=True)
    args.md.write_text(render_markdown(md_report, graph, args.max_owners), encoding="utf-8")
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    unhandled = referenced = 0
    for key, title, _ in DIMENSIONS:
        s = report["dimensions"][key]["summary"]
        unhandled += s["unhandled"]
        referenced += s["referenced"]
        print(f"{title:38s} values={s['values']:4d} handled={s['handled']:4d} referenced={s['referenced']:3d} unhandled={s['unhandled']:3d} (rows {s['rows_unhandled']})")
    print(f"wrote {args.md} and {args.json}")
    if args.strict and (unhandled or (args.fail_on_referenced and referenced)):
        print(f"STRICT: {unhandled} unhandled / {referenced} referenced enum values", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
