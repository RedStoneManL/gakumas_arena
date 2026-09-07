"""实机录像回归夹具（jsonl）的加载与回放。

夹具格式见 `docs/rules/scoring_fidelity.md` §5。一个 `.jsonl` 文件 = 一局录像：
第 1 行 `{"kind": "setup", ...}`，之后每行 `{"kind": "turn", ...}`，最后可选 `{"kind": "final", ...}`。

回放方式：用 `ReplayHooks` 固定山札顺序 / 回合属性 / スコアボーナス / 応援，
在每回合开始（抽牌与 Pアイテム 结算之后）对照录像显示的 体力 / 元気 / スコア / 状態修正，
然后按录像逐张出牌，直到对局结束。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Callable, Iterable
import unicodedata

from gakumas_rl.idol_config import augment_loadout_with_produce_items, build_idol_loadout
from gakumas_rl.repository.master_data import MasterDataRepository
from gakumas_rl.simulation.exam.ids import ExamEffect
from gakumas_rl.simulation.exam.replay import ReplayHooks
from gakumas_rl.simulation.exam.runtime import ExamActionCandidate, ExamRuntime, RuntimeCard
from gakumas_rl.simulation.exam.scoring import ScoringRules


FIXTURE_DIR = Path(__file__).parent / 'fixtures' / 'recorded_games'

TURN_COLOR_LESSON_TYPES = {
    'vocal': 'ProduceStepLessonType_LessonVocal',
    'dance': 'ProduceStepLessonType_LessonDance',
    'visual': 'ProduceStepLessonType_LessonVisual',
}

# 応援 / メモリー アビリティ 的效果规格 → 主数据效果行的定位方式。
EFFECT_SPECS: dict[str, tuple[str, str]] = {
    'aggressive': ('ProduceExamEffectType_ExamCardPlayAggressive', 'effectValue1'),
    'review': ('ProduceExamEffectType_ExamReview', 'effectValue1'),
    'lesson_buff': ('ProduceExamEffectType_ExamLessonBuff', 'effectValue1'),
    'parameter_buff': ('ProduceExamEffectType_ExamParameterBuff', 'effectTurn'),
    'parameter_buff_multiple_per_turn': ('ProduceExamEffectType_ExamParameterBuffMultiplePerTurn', 'effectTurn'),
    'block': ('ProduceExamEffectType_ExamBlock', 'effectValue1'),
    'stamina_consumption_down': ('ProduceExamEffectType_ExamStaminaConsumptionDown', 'effectTurn'),
    'stamina_consumption_add': ('ProduceExamEffectType_ExamStaminaConsumptionAdd', 'effectTurn'),
    'stamina_damage': ('ProduceExamEffectType_ExamStaminaDamage', 'effectValue1'),
}

# 录像 UI 上的状態修正名 → 运行时读法。
MODIFIER_RESOURCES = {
    'やる気': 'aggressive',
    '好印象': 'review',
    '好調': 'parameter_buff',
    '集中': 'lesson_buff',
}
MODIFIER_TIMED_TURNS = {
    '絶好調': ExamEffect.PARAMETER_BUFF_MULTIPLE_PER_TURN,
    '消費体力減少': ExamEffect.STAMINA_CONSUMPTION_DOWN,
    '消費体力増加': ExamEffect.STAMINA_CONSUMPTION_ADD,
}
MODIFIER_TIMED_VALUE_SUM = {
    '消費体力削減': ExamEffect.STAMINA_CONSUMPTION_DOWN_FIX,
}
MODIFIER_TIMED_COUNT = {
    'スキルカード追加発動': ExamEffect.CARD_SEARCH_EFFECT_PLAY_COUNT_BUFF,
}


def _normalize_name(name: str) -> str:
    return unicodedata.normalize('NFKC', str(name or '')).strip()


@dataclass
class RecordedGameFixture:
    """一局录像夹具。"""

    setup: dict[str, Any]
    turns: list[dict[str, Any]]
    final: dict[str, Any] | None
    path: Path

    @property
    def fixture_id(self) -> str:
        return str(self.setup.get('id') or self.path.stem)

    @property
    def xfail_reason(self) -> str:
        return str(self.setup.get('xfail') or '')


def load_fixture(path: Path) -> RecordedGameFixture:
    """读取一个 jsonl 夹具。"""

    setup: dict[str, Any] | None = None
    turns: list[dict[str, Any]] = []
    final: dict[str, Any] | None = None
    for line_number, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        text = raw.strip()
        if not text or text.startswith('#'):
            continue
        record = json.loads(text)
        kind = str(record.get('kind') or '')
        if kind == 'setup':
            setup = record
        elif kind == 'turn':
            turns.append(record)
        elif kind == 'final':
            final = record
        else:
            raise ValueError(f'{path}:{line_number} unknown record kind: {kind!r}')
    if setup is None:
        raise ValueError(f'{path}: missing setup record')
    return RecordedGameFixture(setup=setup, turns=turns, final=final, path=path)


def iter_fixture_paths() -> list[Path]:
    return sorted(FIXTURE_DIR.glob('*.jsonl'))


class RecordedGameReplayer:
    """把夹具装配成 ExamRuntime 并逐回合回放。"""

    def __init__(self, repository: MasterDataRepository, fixture: RecordedGameFixture, scoring_rules: ScoringRules | None = None):
        self.repository = repository
        self.fixture = fixture
        self.setup = fixture.setup
        self.scoring_rules = scoring_rules
        self.card_rows_by_test_id: dict[str, dict[str, Any]] = {}
        self.build_index_by_test_id: dict[str, int] = {}
        self.log: list[str] = []
        self._patched_card_ids: dict[str, tuple[Any, Any]] = {}
        self._pending_auto_end = False
        self._apply_card_overrides()
        self.runtime = self._build_runtime()

    # ------------------------------------------------------------------ 主数据快照覆写

    def _apply_card_overrides(self) -> None:
        """把夹具 `card_overrides` 里的旧版（录像当时）卡面写进 repository 的按强化次数查表缓存。

        用于「只因已知的平衡调整而与现行主数据不同」的录像：覆写值必须引用主数据仓库的 commit
        （`docs/rules/scoring_fidelity.md` §5）。回放结束后由 `restore_repository()` 还原。
        """

        overrides = self.setup.get('card_overrides') or {}
        for test_id, spec in overrides.items():
            base_name = next(str(card['name']) for card in self.setup['cards'] if str(card.get('test_id') or card['name']) == test_id)
            base_row = self.card_row(base_name, 0)
            card_id = str(base_row['id'])
            repo = self.repository
            repo.card_row_by_upgrade(card_id, 0)  # 确保缓存已建立
            original = (dict(repo._card_row_by_upgrade_cache[card_id]), repo._canonical_card_row_cache.get(card_id))
            self._patched_card_ids[card_id] = original
            patched = {up: dict(row) for up, row in original[0].items()}
            for upgrade_text, fields in (spec.get('rows') or {}).items():
                row = dict(patched[int(upgrade_text)])
                for key in ('stamina', 'forceStamina', 'costType', 'costValue'):
                    if key in fields:
                        row[key] = fields[key]
                if 'playEffects' in fields:
                    play_effects = []
                    for entry in fields['playEffects']:
                        effect_id = entry if isinstance(entry, str) else str(entry['effect'])
                        if effect_id not in repo.exam_effect_map:
                            raise KeyError(f'override effect not in master data: {effect_id}')
                        play_effects.append({
                            'produceExamEffectId': effect_id,
                            'produceExamTriggerId': '' if isinstance(entry, str) else str(entry.get('trigger') or ''),
                        })
                    row['playEffects'] = play_effects
                patched[int(upgrade_text)] = row
            repo._card_row_by_upgrade_cache[card_id] = patched
            repo._canonical_card_row_cache[card_id] = patched[min(patched)]
            self.log.append(f'card override {test_id} ({card_id}): {spec.get("reason", "")}')

    def restore_repository(self) -> None:
        """还原被 `card_overrides` 覆写的 repository 缓存。"""

        for card_id, (rows, canonical) in self._patched_card_ids.items():
            self.repository._card_row_by_upgrade_cache[card_id] = rows
            if canonical is not None:
                self.repository._canonical_card_row_cache[card_id] = canonical
        self._patched_card_ids = {}

    # ------------------------------------------------------------------ 主数据定位

    def card_row(self, name: str, upgrade: int) -> dict[str, Any]:
        """按日文卡名 + 强化次数找主数据卡行（`アピールの基本` + upgrade 1 → `アピールの基本+`）。"""

        wanted = _normalize_name(name)
        base_ids = sorted({
            str(row['id'])
            for row in self.repository.produce_cards.rows
            if int(row.get('upgradeCount') or 0) == 0 and _normalize_name(row.get('name')) == wanted
        })
        if not base_ids:
            raise KeyError(f'card not found in master data: {name}')
        if len(base_ids) > 1:
            raise KeyError(f'card name is ambiguous in master data: {name} -> {base_ids}')
        row = self.repository.card_row_by_upgrade(base_ids[0], int(upgrade), fallback_to_canonical=False)
        if row is None:
            raise KeyError(f'card upgrade row not found: {name} +{upgrade}')
        return dict(row)

    def item_id(self, name: str) -> str:
        wanted = _normalize_name(name)
        matches = [str(row['id']) for row in self.repository.produce_items.rows if _normalize_name(row.get('name')) == wanted]
        if not matches:
            raise KeyError(f'produce item not found: {name}')
        return matches[0]

    def drink_row(self, name: str) -> dict[str, Any]:
        wanted = _normalize_name(name)
        for row in self.repository.produce_drinks.rows:
            if _normalize_name(row.get('name')) == wanted:
                return dict(row)
        raise KeyError(f'drink not found: {name}')

    def effect_row(self, spec: dict[str, Any]) -> dict[str, Any]:
        """把 `{"type": "aggressive", "value": 3}` 这类规格映射到主数据效果行。"""

        effect_type, key = EFFECT_SPECS[str(spec['type'])]
        value = int(spec.get('value') if 'value' in spec else spec.get('turns'))
        for row in self.repository.exam_effects.rows:
            if str(row.get('effectType') or '') != effect_type:
                continue
            if int(row.get(key) or 0) != value:
                continue
            other_key = 'effectTurn' if key == 'effectValue1' else 'effectValue1'
            if int(row.get(other_key) or 0) not in (0, value):
                continue
            if row.get('produceCardSearchId') or row.get('produceExamStatusEnchantId'):
                continue
            return row
        raise KeyError(f'effect row not found for spec {spec}')

    # ------------------------------------------------------------------ 装配

    def _build_runtime(self) -> ExamRuntime:
        setup = self.setup
        scenario = self.repository.build_scenario(str(setup.get('scenario') or 'produce-001'))
        talent_level = int(setup.get('talent_awakening_level') or 1)
        loadout = build_idol_loadout(
            self.repository,
            scenario,
            str(setup['idol_card_id']),
            idol_rank=0,
            use_after_item=talent_level >= 2,
            exam_score_bonus_multiplier=1.0,
        )
        item_ids = [self.item_id(name) for name in setup.get('produce_items', [])]
        if item_ids:
            loadout = augment_loadout_with_produce_items(self.repository, loadout, item_ids)

        deck_rows: list[dict[str, Any]] = []
        for build_index, card in enumerate(setup['cards']):
            test_id = str(card.get('test_id') or card['name'])
            row = self.card_row(str(card['name']), int(card.get('upgrade') or 0))
            self.card_rows_by_test_id[test_id] = row
            self.build_index_by_test_id[test_id] = build_index
            deck_rows.append(row)

        drink_rows = [self.drink_row(name) for name in setup.get('drinks', [])]
        turns = [str(color) for color in setup['turns']]

        hooks = ReplayHooks(
            initial_deck_order=[self.build_index_by_test_id[test_id] for test_id in setup['deck']],
            reshuffle_orders=[
                [self.build_index_by_test_id[test_id] for test_id in order]
                for order in setup.get('reshuffles', [])
            ],
            turn_colors=turns,
            score_bonus_percent={str(k): float(v) for k, v in (setup.get('score_bonus_percent') or {}).items()},
            disable_stage_gimmicks=True,
            turn_start_hooks=self._build_turn_start_hooks(setup.get('encouragements', [])),
            memory_hooks=[self._effect_hook(spec, 'memory') for spec in setup.get('memory_effects', [])],
        )

        mode = str(setup.get('mode') or 'lesson')
        common: dict[str, Any] = dict(
            loadout=loadout,
            seed=int(setup.get('seed') or 1),
            deck=deck_rows,
            drinks=drink_rows,
            starting_stamina=float(setup['stamina']),
            turn_limit=len(turns),
            replay_hooks=hooks,
        )
        if self.scoring_rules is not None:
            common['scoring_rules'] = self.scoring_rules
        if mode == 'lesson':
            post_clear = tuple(TURN_COLOR_LESSON_TYPES.values()) if setup.get('ignore_kind_condition_after_clear') else ()
            runtime = ExamRuntime(
                self.repository,
                scenario,
                battle_kind='lesson',
                lesson_type=TURN_COLOR_LESSON_TYPES[turns[0]],
                lesson_target_value=float(setup['clear']),
                lesson_perfect_value=float(setup['perfect']),
                lesson_post_clear_types=post_clear,
                exam_score_bonus_multiplier=1.0,
                **common,
            )
        else:
            stage_type = str(setup.get('stage_type') or scenario.audition_sequence[-1])
            rows = self.repository.audition_rows(
                scenario,
                stage_type,
                audition_difficulty_id=loadout.stat_profile.audition_difficulty_id,
            )
            if not rows:
                raise AssertionError(f'no audition rows for {stage_type}')
            selector = f"{str(rows[0].get('id') or '')}:{int(rows[0].get('number') or 0)}"
            runtime = ExamRuntime(
                self.repository,
                scenario,
                stage_type=stage_type,
                audition_row_id=selector,
                **common,
            )
        runtime.reset()
        max_stamina = float(setup.get('max_stamina') or setup['stamina'])
        runtime.max_stamina = max_stamina
        runtime.stamina = min(float(setup['stamina']), max_stamina)
        return runtime

    def _effect_hook(self, spec: dict[str, Any], source: str) -> Callable[[ExamRuntime], None]:
        effect = self.effect_row(spec)
        condition = spec.get('condition')

        def hook(runtime: ExamRuntime) -> None:
            if condition and not self._condition_matches(runtime, condition):
                self.log.append(f'turn {runtime.turn}: {source} {spec} skipped (condition)')
                return
            self.log.append(f'turn {runtime.turn}: {source} {spec} -> {effect["id"]}')
            runtime._apply_exam_effect(effect, source='gimmick' if source == 'encouragement' else source)

        return hook

    def _build_turn_start_hooks(self, encouragements: Iterable[dict[str, Any]]) -> dict[int, list[Callable[[ExamRuntime], None]]]:
        hooks: dict[int, list[Callable[[ExamRuntime], None]]] = {}
        for entry in encouragements:
            spec = dict(entry['effect'])
            if 'condition' in entry:
                spec['condition'] = entry['condition']
            if str(spec.get('type')) == 'trouble_card':
                # 「眠気を山札のランダムな位置に生成」：录像里条件均未满足，暂不建模（条件成立时直接报错提醒）。
                condition = spec.get('condition')

                def trouble_hook(runtime: ExamRuntime, condition=condition) -> None:
                    if condition is None or self._condition_matches(runtime, condition):
                        raise AssertionError('trouble card generation is not modelled by the harness')

                hooks.setdefault(int(entry['turn']), []).append(trouble_hook)
                continue
            hooks.setdefault(int(entry['turn']), []).append(self._effect_hook(spec, 'encouragement'))
        return hooks

    def _condition_matches(self, runtime: ExamRuntime, condition: dict[str, Any]) -> bool:
        if 'modifier' in condition:
            value = float(runtime.resources[str(condition['modifier'])])
            if 'min' in condition and value < float(condition['min']):
                return False
            if 'max' in condition and value > float(condition['max']):
                return False
            return True
        if 'score_ratio_min' in condition:
            target = float(self.setup.get('clear') or 0)
            return target > 0 and runtime.score * 100.0 >= target * float(condition['score_ratio_min'])
        raise ValueError(f'unknown condition {condition}')

    # ------------------------------------------------------------------ 读数

    def hand_test_ids(self) -> list[str]:
        return [self._test_id_of(card) for card in self.runtime.hand]

    def _test_id_of(self, card: RuntimeCard) -> str:
        for test_id, index in self.build_index_by_test_id.items():
            if index == card.build_index:
                return test_id
        return f'{card.card_id}#{card.uid}'

    def observed_modifiers(self) -> dict[str, float]:
        runtime = self.runtime
        observed: dict[str, float] = {}
        for label, key in MODIFIER_RESOURCES.items():
            observed[label] = float(runtime.resources[key])
        for label, effect_type in MODIFIER_TIMED_TURNS.items():
            turns = [
                item.remaining_turns if item.remaining_turns is not None else -1
                for item in runtime.active_effects
                if str(item.effect.get('effectType') or '') == effect_type
            ]
            observed[label] = float(max(turns)) if turns else 0.0
        for label, effect_type in MODIFIER_TIMED_VALUE_SUM.items():
            observed[label] = float(sum(
                float(item.effect.get('effectValue1') or 0)
                for item in runtime.active_effects
                if str(item.effect.get('effectType') or '') == effect_type
            ))
        for label, effect_type in MODIFIER_TIMED_COUNT.items():
            observed[label] = float(sum(
                1 for item in runtime.active_effects if str(item.effect.get('effectType') or '') == effect_type
            ))
        observed['スキルカード使用数追加'] = float(max(runtime.play_limit - 1 - runtime.turn_counters['play_count'], 0))
        observed['発動予約'] = float(len(runtime.scheduled_effects))
        return observed

    def snapshot(self) -> dict[str, Any]:
        runtime = self.runtime
        return {
            'turn': runtime.turn,
            'remaining': runtime.remaining_turns_including_current(),
            'life': float(runtime.stamina),
            'vitality': float(runtime.resources['block']),
            'score': float(runtime.score),
            'modifiers': {k: v for k, v in self.observed_modifiers().items() if v},
            'hand': self.hand_test_ids(),
        }

    # ------------------------------------------------------------------ 回放

    def check(self, expect: dict[str, Any], where: str) -> None:
        snap = self.snapshot()
        problems: list[str] = []
        for key in ('life', 'vitality', 'score'):
            if key in expect and float(expect[key]) != snap[key]:
                problems.append(f'{key}: expected {expect[key]}, got {snap[key]:g}')
        expected_modifiers = {str(k): v for k, v in (expect.get('modifiers') or {}).items()}
        observed = self.observed_modifiers()
        for label, value in expected_modifiers.items():
            if value is None:
                continue
            if label not in observed:
                problems.append(f'modifier {label}: harness cannot observe it')
            elif float(value) != observed[label]:
                problems.append(f'modifier {label}: expected {value}, got {observed[label]:g}')
        if 'modifiers' in expect:
            for label in MODIFIER_RESOURCES:
                if label not in expected_modifiers and observed[label] != 0:
                    problems.append(f'modifier {label}: expected absent, got {observed[label]:g}')
        if 'hand' in expect:
            got = self.hand_test_ids()
            if list(expect['hand']) != got:
                problems.append(f'hand: expected {expect["hand"]}, got {got}')
        if problems:
            raise AssertionError(f'[{self.fixture.fixture_id}] {where}: ' + '; '.join(problems) + f'\n  snapshot={snap}\n  log={self.log[-6:]}')

    def perform(self, action: list[Any], where: str) -> None:
        runtime = self.runtime
        kind = str(action[0])
        if kind == 'support':
            card = runtime.hand[int(action[1])]
            for _ in range(int(action[2]) if len(action) > 2 else 1):
                assert runtime._apply_support_card_upgrade(card), f'{where}: cannot apply lesson support to {self._test_id_of(card)}'
            self.log.append(f'{where}: support {self._test_id_of(card)} -> upgrade {card.base_card.get("upgradeCount")}')
            return
        if kind == 'play':
            index = int(action[1])
            if index >= len(runtime.hand):
                raise AssertionError(f'{where}: hand index {index} out of range, hand={self.hand_test_ids()}')
            card = runtime.hand[index]
            if not runtime._can_play_card(card):
                raise AssertionError(
                    f'{where}: {self._test_id_of(card)} is not playable; hand={self.hand_test_ids()} '
                    f'stamina={runtime.stamina:g} block={runtime.resources["block"]:g} play_limit={runtime.play_limit} '
                    f'played={runtime.turn_counters["play_count"]}'
                )
            score_before = runtime.score
            # 直接走 _play_card：出牌次数用尽时不立刻自动结束回合，让夹具还能在出牌后、回合结束前对照数值
            # （录像里回合结束是显式操作；`ExamRuntime.step` 会自动结束，结果等价）。
            runtime._remove_hand_card(card.uid)
            runtime._play_card(card)
            self.log.append(f'{where}: play {self._test_id_of(card)} score {score_before:g} -> {runtime.score:g}')
            if not runtime.terminated and not runtime._has_remaining_play_window():
                self._pending_auto_end = True
            return
        if kind == 'drink':
            available = [index for index, drink in enumerate(runtime.drinks) if not drink.get('_consumed')]
            index = available[int(action[1])]
            runtime._use_drink(index)
            self.log.append(f'{where}: drink {self.repository.drink_name(runtime.drinks[index])}')
            return
        if kind in {'end', 'skip'}:
            self._end_turn(where, kind)
            return
        if kind == 'expect':
            self.check(dict(action[1]), f'{where} mid-turn')
            return
        raise ValueError(f'unknown action {action}')

    def _end_turn(self, where: str, kind: str = 'end') -> None:
        runtime = self.runtime
        self._pending_auto_end = False
        if runtime.terminated:
            return
        skipped = runtime._has_remaining_play_window()
        runtime._end_turn(skipped=skipped)
        self.log.append(f'{where}: {kind}{" (skip +2)" if skipped else ""}')

    def replay(self) -> None:
        try:
            self._replay()
        finally:
            self.restore_repository()

    def _replay(self) -> None:
        runtime = self.runtime
        for record in self.fixture.turns:
            turn = int(record['turn'])
            where = f'turn {turn} (残り{record.get("remaining", "?")})'
            if runtime.terminated:
                raise AssertionError(f'{where}: game already terminated (score={runtime.score:g})')
            if runtime.turn != turn:
                raise AssertionError(f'{where}: runtime is at turn {runtime.turn}')
            for action in record.get('before', []):
                self.perform(list(action), where)
            if 'expect' in record:
                self.check(dict(record['expect']), where)
            turn_before = runtime.turn
            self._pending_auto_end = False
            for action in record.get('actions', []):
                if runtime.terminated:
                    if str(action[0]) in {'end', 'skip'}:
                        continue
                    raise AssertionError(f'{where}: game already over before action {action}')
                if self._pending_auto_end and str(action[0]) not in {'expect', 'end', 'skip'}:
                    raise AssertionError(f'{where}: no play window left before action {action}')
                self.perform(list(action), where)
            if not runtime.terminated and runtime.turn == turn_before:
                # 录像里回合结束是显式动作；夹具省略时自动结束回合。
                self._end_turn(where, 'auto-end')
        if self.fixture.final is not None:
            if not runtime.terminated:
                raise AssertionError(f'[{self.fixture.fixture_id}] expected the game to be over, snapshot={self.snapshot()}')
            self.check(dict(self.fixture.final.get('expect') or {}), 'final')
