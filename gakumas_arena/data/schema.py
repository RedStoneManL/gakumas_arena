"""Pydantic models for all structured game data.

The effect DSL is deliberately open: `Effect.op` is a free string validated at
interpretation time by `engine.effects` (unknown ops raise), so that the data layer
never silently swallows an effect we have not implemented yet.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Plan = Literal["free", "sense", "logic", "anomaly"]
CardType = Literal["active", "mental", "trouble"]
Rarity = Literal["N", "R", "SR", "SSR"]
CostKind = Literal["genki", "stamina_direct", "none"]


class Condition(BaseModel):
    """A predicate over stage state, e.g. {"stat":"focus","op":">=","value":3}.

    `stat` may be any StageState field or status-effect name; `op` in {>=,<=,==,>,<,!=}.
    Special forms: {"kind":"turn","op":">=","value":3}, {"kind":"is_first_turn"},
    {"kind":"stamina_ratio","op":"<=","value":0.5} — vocabulary fixed after rules research.
    """
    model_config = {"extra": "allow"}
    kind: str = "stat"
    stat: str | None = None
    op: str | None = None
    value: float | None = None


class Effect(BaseModel):
    """One DSL instruction. Unknown fields are kept (extra=allow) for op-specific params."""
    model_config = {"extra": "allow"}
    op: str
    value: float | None = None
    stat: str | None = None
    turns: int | None = None
    conditions: list[Condition] = Field(default_factory=list)
    effects: list["Effect"] = Field(default_factory=list)  # nested (delayed / conditional / repeat)


class Cost(BaseModel):
    kind: CostKind = "genki"
    value: int = 0


class SkillCardVariant(BaseModel):
    """Base or upgraded (+) version of a card."""
    cost: Cost = Field(default_factory=Cost)
    conditions: list[Condition] = Field(default_factory=list)
    effects: list[Effect] = Field(default_factory=list)
    source_text: str = ""


class SkillCard(BaseModel):
    id: str
    name: str
    plan: Plan = "free"
    type: CardType = "active"
    rarity: Rarity = "N"
    flags: list[str] = Field(default_factory=list)  # once_per_stage, no_duplicate, hold, generated, unique, initial
    unique_to_idol: str | None = None
    base: SkillCardVariant
    upgraded: SkillCardVariant | None = None
    source_url: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class Trigger(BaseModel):
    model_config = {"extra": "allow"}
    when: str  # stage_start | turn_start | turn_end | after_card_played | on_stat_change | ...
    conditions: list[Condition] = Field(default_factory=list)
    limit: int | None = None  # max activations per stage; None = unlimited


class PItem(BaseModel):
    id: str
    name: str
    plan: Plan = "free"
    rarity: Rarity = "N"
    unique_to_idol: str | None = None
    trigger: Trigger
    effects: list[Effect] = Field(default_factory=list)
    upgraded: dict[str, Any] | None = None
    source_text: str = ""
    source_url: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class PDrink(BaseModel):
    id: str
    name: str
    plan: Plan = "free"
    rarity: Rarity = "N"
    effects: list[Effect] = Field(default_factory=list)
    source_text: str = ""
    source_url: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class Stats(BaseModel):
    vocal: int = 0
    dance: int = 0
    visual: int = 0

    def total(self) -> int:
        return self.vocal + self.dance + self.visual


class Idol(BaseModel):
    """A produce idol card (Pアイドル)."""
    id: str
    character: str  # e.g. "hanami_saki"
    name: str
    plan: Plan
    rarity: Rarity = "SSR"
    initial_stats: Stats = Field(default_factory=Stats)
    initial_stamina: int = 0
    favorite_stat: str | None = None  # 得意
    weak_stat: str | None = None      # 苦手
    unique_card_id: str | None = None
    unique_item_id: str | None = None
    initial_deck: list[str] = Field(default_factory=list)  # card ids
    source_url: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class StatusEffectDef(BaseModel):
    """Definition of a status effect (状態) so the engine can treat them uniformly."""
    id: str
    name_jp: str
    name_cn: str = ""
    kind: Literal["counter", "turns", "flag"] = "counter"
    decay: str | None = None  # e.g. "-1 per turn", "clears at turn end", None
    description: str = ""
