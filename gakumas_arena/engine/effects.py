"""Effect-DSL interpreter.

Each `op` maps to a handler `def _op_<name>(ctx, eff)`. Unknown ops raise NotImplementedError so
missing mechanics are loud, never silent. Formulas here are placeholders until
docs/rules/lesson_exam_engine.md is finalised — see TODO markers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..data.schema import Condition, Effect
from .state import StageConfig, StageState


@dataclass
class Ctx:
    cfg: StageConfig
    st: StageState
    registry: object  # DataRegistry
    rng: object

    def current_stat_value(self) -> int:
        tt = self.cfg.turn_types[self.st.turn - 1] if self.cfg.turn_types else None
        if tt is None:
            return max(self.cfg.stats.values()) if self.cfg.stats else 0
        return self.cfg.stats.get(tt, 0)


def check_condition(ctx: Ctx, c: Condition) -> bool:
    if c.kind == "stat":
        lhs = getattr(ctx.st, c.stat, None)
        if lhs is None:
            lhs = ctx.st.status.get(c.stat, 0)
    elif c.kind == "turn":
        lhs = ctx.st.turn
    elif c.kind == "stamina_ratio":
        lhs = ctx.st.stamina / max(1, ctx.cfg.max_stamina)
    elif c.kind == "is_first_turn":
        return ctx.st.turn == 1
    else:
        raise NotImplementedError(f"condition kind {c.kind}")
    ops: dict[str, Callable[[float, float], bool]] = {
        ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b, "==": lambda a, b: a == b,
        ">": lambda a, b: a > b, "<": lambda a, b: a < b, "!=": lambda a, b: a != b,
    }
    return ops[c.op or ">="](lhs, c.value or 0)


def all_conditions(ctx: Ctx, conds: list[Condition]) -> bool:
    return all(check_condition(ctx, c) for c in conds)


# ---- score formula (TODO: verify against rules doc) ----
def score_gain(ctx: Ctx, base: float) -> int:
    st = ctx.st
    mult = 1.0
    if ctx.cfg.plan == "sense":
        base = base + st.focus
        if st.excellent_condition > 0:
            mult += 0.5 + 0.1 * st.good_condition  # TODO verify 絶好調 formula
        elif st.good_condition > 0:
            mult += 0.5
    # parameter multiplier: score * (stat / 100) rounded up (TODO verify rounding / caps)
    stat = ctx.current_stat_value()
    param_mult = 1.0 + stat / 100.0 if stat else 1.0
    import math
    return math.ceil(base * mult * param_mult)


HANDLERS: dict[str, Callable[[Ctx, Effect], None]] = {}


def op(name: str):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco


@op("score")
def _op_score(ctx: Ctx, e: Effect):
    ctx.st.score += score_gain(ctx, e.value or 0)


@op("genki")
def _op_genki(ctx: Ctx, e: Effect):
    if ctx.st.status.get("genki_gain_disabled", 0) > 0:
        return
    v = e.value or 0
    if ctx.cfg.plan == "logic":
        v += ctx.st.motivation  # TODO やる気 adds to genki gain
    ctx.st.genki = max(0, ctx.st.genki + int(v))


@op("buff")
def _op_buff(ctx: Ctx, e: Effect):
    """Generic increment of a named stat / status effect; `turns` for duration-type effects."""
    name = e.stat
    amount = int(e.turns if e.turns is not None else (e.value or 0))
    if hasattr(ctx.st, name):
        setattr(ctx.st, name, max(0, getattr(ctx.st, name) + amount))
    else:
        ctx.st.status[name] = max(0, ctx.st.status.get(name, 0) + amount)


@op("stamina")
def _op_stamina(ctx: Ctx, e: Effect):
    ctx.st.stamina = max(0, min(ctx.cfg.max_stamina, ctx.st.stamina + int(e.value or 0)))


@op("draw")
def _op_draw(ctx: Ctx, e: Effect):
    from .stage import draw_cards
    draw_cards(ctx, int(e.value or 1))


@op("extra_play")
def _op_extra_play(ctx: Ctx, e: Effect):
    ctx.st.extra_plays += int(e.value or 1)


@op("conditional")
def _op_conditional(ctx: Ctx, e: Effect):
    if all_conditions(ctx, e.conditions):
        for sub in e.effects:
            apply_effect(ctx, sub)


@op("delayed")
def _op_delayed(ctx: Ctx, e: Effect):
    after = int(getattr(e, "after_turns", 1) or 1)
    ctx.st.status.setdefault("_delayed", 0)
    pending = ctx.st.__dict__.setdefault("_pending", [])
    pending.append((ctx.st.turn + after, [s.model_dump() for s in e.effects]))


def apply_effect(ctx: Ctx, e: Effect) -> None:
    if e.conditions and not all_conditions(ctx, e.conditions):
        return
    h = HANDLERS.get(e.op)
    if h is None:
        raise NotImplementedError(f"effect op '{e.op}' not implemented")
    h(ctx, e)
