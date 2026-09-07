"""One stage = one lesson / exam / contest run. Rules are placeholders until docs/rules is final."""
from __future__ import annotations

from ..data.loader import DataRegistry
from ..data.schema import SkillCard
from .effects import Ctx, all_conditions, apply_effect
from .rng import Rng
from .state import StageConfig, StageState


def draw_cards(ctx: Ctx, n: int) -> None:
    st = ctx.st
    for _ in range(n):
        if not st.deck:
            if not st.discard:
                return
            st.deck, st.discard = st.discard, []
            ctx.rng.shuffle(st.deck)
        st.hand.append(st.deck.pop())


class Stage:
    def __init__(self, cfg: StageConfig, registry: DataRegistry, rng: Rng | None = None):
        self.cfg = cfg
        self.reg = registry
        self.rng = rng or Rng()
        self.st = StageState(stamina=cfg.max_stamina, deck=list(cfg.deck), drinks=list(cfg.p_drinks))
        self.rng.shuffle(self.st.deck)
        self.ctx = Ctx(cfg, self.st, registry, self.rng)
        self._start_turn()

    # ---- helpers ----
    def _variant(self, card_id: str):
        card: SkillCard = self.reg.card(card_id)
        return card, (card.upgraded or card.base)

    def _start_turn(self):
        st = self.st
        st.turn += 1
        st.cards_played_this_turn = 0
        st.extra_plays = 0
        st.hand.clear()  # TODO: 保留 (hold) cards persist
        draw_cards(self.ctx, self.cfg.hand_size)
        # TODO: P-item turn_start triggers, delayed effects, status decay order

    def _end_turn(self):
        st = self.st
        # logic: 好印象 end-of-turn score, then decay (TODO verify order and formulas)
        if st.good_impression > 0:
            st.score += st.good_impression
            st.good_impression -= 1
        if st.good_condition > 0:
            st.good_condition -= 1
        if st.excellent_condition > 0:
            st.excellent_condition -= 1
        st.discard.extend(st.hand)
        st.hand.clear()
        if st.turn >= self.cfg.turns:
            st.done = True
        else:
            self._start_turn()

    def legal_actions(self) -> list[tuple[str, int]]:
        acts: list[tuple[str, int]] = []
        for i, cid in enumerate(self.st.hand):
            if self.can_play(cid):
                acts.append(("play", i))
        for j, _ in enumerate(self.st.drinks):
            acts.append(("drink", j))
        acts.append(("skip", 0))
        return acts

    def can_play(self, card_id: str) -> bool:
        card, v = self._variant(card_id)
        st = self.st
        if st.cards_played_this_turn > st.extra_plays:
            return False
        if "once_per_stage" in card.flags and card_id in st.used_once:
            return False
        if v.cost.kind == "genki" and v.cost.value > st.genki + st.stamina:
            return False
        if v.cost.kind == "stamina_direct" and v.cost.value > st.stamina:
            return False
        return all_conditions(self.ctx, v.conditions)

    def _pay(self, cost) -> None:
        st = self.st
        if cost.kind == "genki":
            from_genki = min(st.genki, cost.value)
            st.genki -= from_genki
            st.stamina -= cost.value - from_genki  # TODO 消費体力減少 etc.
        elif cost.kind == "stamina_direct":
            st.stamina -= cost.value

    def step(self, action: tuple[str, int]) -> None:
        kind, idx = action
        st = self.st
        if kind == "play":
            cid = st.hand[idx]
            assert self.can_play(cid), "illegal card"
            card, v = self._variant(cid)
            self._pay(v.cost)
            st.hand.pop(idx)
            for e in v.effects:
                apply_effect(self.ctx, e)
            if "once_per_stage" in card.flags:
                st.used_once.add(cid)
                st.exhausted.append(cid)
            else:
                st.discard.append(cid)
            st.cards_played_this_turn += 1
            st.log.append(f"T{st.turn} play {card.name} -> score {st.score}")
            if st.cards_played_this_turn > st.extra_plays:
                self._end_turn()
        elif kind == "drink":
            did = st.drinks.pop(idx)
            for e in self.reg.p_drinks[did].effects:
                apply_effect(self.ctx, e)
        elif kind == "skip":
            st.stamina = min(self.cfg.max_stamina, st.stamina + 2)  # TODO verify skip recovery
            self._end_turn()
        else:
            raise ValueError(kind)
