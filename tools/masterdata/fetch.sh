#!/usr/bin/env bash
# Clone or update the datamined master DB (vertesan/gakumasu-diff) into data/raw/ (git-ignored).
# The dump is NOT redistributed in this repo; every developer fetches it locally.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="${GAKUMAS_MASTERDATA_DIR:-$ROOT/data/raw/gakumasu-diff}"
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --ff-only
else
  git clone --depth 1 https://github.com/vertesan/gakumasu-diff "$DEST"
fi
git -C "$DEST" log -1 --format='master data at %ci (%h)'
TR="${GAKUMAS_RL_LOCALIZATION_ROOT:-$ROOT/data/raw/GakumasTranslationData}"
if [ -d "$TR/.git" ]; then git -C "$TR" pull --ff-only; else git clone --depth 1 https://github.com/chinosk6/GakumasTranslationData "$TR"; fi
git -C "$TR" log -1 --format='translation data at %ci (%h)'
python3 "$ROOT/tools/masterdata/build_cache.py" "$DEST"
