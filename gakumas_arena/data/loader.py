from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .schema import Idol, PDrink, PItem, SkillCard, StatusEffectDef

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass
class DataRegistry:
    skill_cards: dict[str, SkillCard] = field(default_factory=dict)
    p_items: dict[str, PItem] = field(default_factory=dict)
    p_drinks: dict[str, PDrink] = field(default_factory=dict)
    idols: dict[str, Idol] = field(default_factory=dict)
    status_effects: dict[str, StatusEffectDef] = field(default_factory=dict)

    def card(self, card_id: str) -> SkillCard:
        return self.skill_cards[card_id]


def _load_list(path: Path, model):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        rows = json.load(f)
    out = {}
    for row in rows:
        obj = model.model_validate(row)
        if obj.id in out:
            raise ValueError(f"duplicate id {obj.id} in {path}")
        out[obj.id] = obj
    return out


def load_registry(data_dir: Path | str = DEFAULT_DATA_DIR) -> DataRegistry:
    d = Path(data_dir)
    return DataRegistry(
        skill_cards=_load_list(d / "skill_cards.json", SkillCard),
        p_items=_load_list(d / "p_items.json", PItem),
        p_drinks=_load_list(d / "p_drinks.json", PDrink),
        idols=_load_list(d / "idols.json", Idol),
        status_effects=_load_list(d / "status_effects.json", StatusEffectDef),
    )
