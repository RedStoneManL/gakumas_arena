"""Stage (lesson / exam / contest) state. Field names are the DSL `stat` vocabulary."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Literal

StageKind = Literal["lesson", "sp_lesson", "midterm", "final", "contest", "custom"]
TurnType = Literal["vocal", "dance", "visual"]


@dataclass
class StageConfig:
    kind: StageKind = "lesson"
    turns: int = 6
    turn_types: list[TurnType] = field(default_factory=list)  # per-turn attribute; empty → all same
    target_score: int | None = None      # lesson clear / exam target
    perfect_score: int | None = None     # lesson perfect
    hand_size: int = 3
    plan: str = "sense"
    stats: dict[str, int] = field(default_factory=lambda: {"vocal": 0, "dance": 0, "visual": 0})
    max_stamina: int = 30
    deck: list[str] = field(default_factory=list)       # card ids
    p_items: list[str] = field(default_factory=list)
    p_drinks: list[str] = field(default_factory=list)
    stat_score_cap: int | None = None  # some stages cap parameter multiplier


@dataclass
class StageState:
    turn: int = 0
    score: int = 0
    stamina: int = 0
    genki: int = 0
    # sense
    focus: int = 0
    good_condition: int = 0       # turns remaining
    excellent_condition: int = 0  # turns remaining
    # logic
    motivation: int = 0
    good_impression: int = 0
    # anomaly
    zenryoku: int = 0
    onzon: int = 0
    strength: int = 0  # 強気 etc. — vocabulary finalised after rules research
    # generic status effects: name -> value/turns
    status: dict[str, int] = field(default_factory=dict)
    # cards
    deck: list[str] = field(default_factory=list)
    hand: list[str] = field(default_factory=list)
    discard: list[str] = field(default_factory=list)
    exhausted: list[str] = field(default_factory=list)
    hold: list[str] = field(default_factory=list)
    used_once: set[str] = field(default_factory=set)
    cards_played_this_turn: int = 0
    extra_plays: int = 0
    drinks: list[str] = field(default_factory=list)
    item_activations: dict[str, int] = field(default_factory=dict)
    done: bool = False
    log: list[str] = field(default_factory=list)

    def clone(self) -> "StageState":
        return copy.deepcopy(self)
