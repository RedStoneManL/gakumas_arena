# tools/masterdata

Utilities for the datamined 学マス master DB (YAML dump, one file per table,
each file a list of row dicts — e.g. the `gakumasu-diff` repository).

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

Outputs of this script were used to write `docs/research/master_data_atlas.md`
and `docs/research/master_data_enums.md`.
