# tools/masterdata

Utilities for the datamined 学マス master DB (YAML dump, one file per table,
each file a list of row dicts — the `vertesan/gakumasu-diff` repository).

| file | purpose |
|---|---|
| `fetch.sh` | clone/update the dump into `data/raw/gakumasu-diff` (git-ignored) and build the JSON cache |
| `build_cache.py` | YAML → JSON cache (`gakumas_arena.masterdata.store`) |
| `inspect_dump.py` | ad-hoc inspection: row counts, field sets, enum value sets, FK inference, grep, per-table detail |
| `history_diff.py` | diff two commits of the dump (schema / enum / config-row changes) |
| `build_docs.py` | regenerates `docs/research/master_data_atlas.md` and `master_data_enums.md` |
| `atlas_annotations.py`, `atlas_annotations_more.py` | hand-written Chinese field/table/enum annotations used by `build_docs.py` |
| `atlas_intro.md`, `atlas_relations.md`, `enums_intro.md`, `enums_hif_notes.md` | prose fragments spliced into the generated docs |

## inspect_dump.py

```bash
# one-off parse is slow (~200 MB YAML); always pass --cache
python tools/masterdata/inspect_dump.py DUMP_DIR --cache /tmp/md.pkl --tables      # row counts + field sets
python tools/masterdata/inspect_dump.py DUMP_DIR --cache /tmp/md.pkl --enums       # every enum field / family
python tools/masterdata/inspect_dump.py DUMP_DIR --cache /tmp/md.pkl --enum ProduceExamEffectType
python tools/masterdata/inspect_dump.py DUMP_DIR --cache /tmp/md.pkl --table ProduceCard
python tools/masterdata/inspect_dump.py DUMP_DIR --cache /tmp/md.pkl --sample ProduceDrink 2
python tools/masterdata/inspect_dump.py DUMP_DIR --cache /tmp/md.pkl --fk          # infer foreign keys by joining
python tools/masterdata/inspect_dump.py DUMP_DIR --cache /tmp/md.pkl --grep 'hif|primastella|festival'
python tools/masterdata/inspect_dump.py DUMP_DIR --cache /tmp/md.pkl --json out.json
```

Install PyYAML from a PyPI wheel (bundles libyaml, so `yaml.CSafeLoader` exists);
the Debian `python3-yaml` package may lack the C loader and is ~20x slower.
`Localization.yaml` / `Rule.yaml` are not valid YAML (stray `\r` / `\x0b`); the loader
repairs them automatically.

## build_docs.py

```bash
python tools/masterdata/build_docs.py --cache /tmp/md.pkl \
    --proto-dir <dir with pmaster.proto pcommon.proto penum.proto> \
    --out-dir docs/research --dump-commit <hash>
```

Sections are appended and flushed one at a time, so a partial run still leaves a
usable file. Field types come from `pmaster.proto`, complete enum lists from
`penum.proto` (values absent from the dump are flagged), everything else from the
dump itself. To document a new field/enum value, edit the annotation modules and
rerun.

## history_diff.py

Compare two commits of the dump (git clone of gakumasu-diff): tables added/removed,
top-level fields added/removed per table, enum values added/removed per (table, field-path),
row-level changes of the small config tables (Produce, ProduceSetting, ExamSetting,
ResultGradePattern, ProduceGrade, ProduceExamBattleScoreConfig, ProduceStepAuditionDifficulty,
...), and an example row + Japanese description for every new enum value.

```bash
# per-commit summaries are cached (one snapshot ~13 s to scan, the diff itself is instant)
python tools/masterdata/history_diff.py DUMP_DIR HEAD~1 HEAD --cache /tmp/hcache \
    --examples ProduceExamEffect:effectType,ProduceExamTrigger:phaseTypes
python tools/masterdata/history_diff.py DUMP_DIR 6edc27e f0dac51 --cache /tmp/hcache --tables '^Produce' --json out.json
python tools/masterdata/history_diff.py DUMP_DIR --cache /tmp/hcache --summary-only <sha>   # batch pre-cache
```

Enum/field sets come from a line-oriented scan of the raw YAML (no parse); row diffs parse
with CSafeLoader and key rows by `id`, falling back to a composite key when ids collide
(e.g. ProduceStepAuditionDifficulty) or are absent (ResultGradePattern, ForceAppVersion).
Used to write `docs/research/mechanics_timeline.md`.

## coverage.py — new-mechanic detector

```bash
python tools/masterdata/coverage.py            # writes docs/research/engine_coverage.md + data/coverage.json
python tools/masterdata/coverage.py --strict   # exit 1 if the dump has enum values gakumas_rl does not handle
```

Scans `ProduceExamEffectType`, `ProduceEffectType`, trigger phase types, `ProduceExamStatusEnchant`
(derived from its effects/trigger), `ProduceCardGrowEffectType` and `ProduceStepType`, and compares
them with what the vendored `gakumas_rl/` handles (its effect registry / `ids` constants /
`_apply_produce_effect`, with a grep of the source as fallback). Unhandled values are listed with row
counts and the cards / items / scenarios that use them. Run it after every `fetch.sh`.
