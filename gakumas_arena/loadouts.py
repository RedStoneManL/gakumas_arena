"""命名预设编成（loadout presets）：从主数据构造的「像样的账号状态」，供 heuristic / RL 基线使用。

背景（docs/OPEN_ITEMS.md C1）：facade 默认偶像 ``i_card-amao-1-000``（R 卡）+ 空编成跑 H.I.F 时在第 2 场
選抜試験 失败。本模块为每个プラン（センス / ロジック / アノマリー）提供一套预设：

- SSR 偶像卡，``idol_rank`` 取 ``IdolCard.maxIdolCardLevelLimitRank``（当前主数据为 6）；
- 6 张支援卡（由 ``gakumas_rl.support_card_selector`` 按偶像プラン/三维挑选，结果固化在本文件里，
  ``suggest_support_cards`` 可重新生成），等级取该稀有度上限（SSR=60，见 ``SupportCardLevelLimit``）；
- H.I.F ボーナス 成长面板等级（``ProduceGrowthPanel``，剧本级配置，见 ``HifScenarioConfig.growth_panel_levels``）。

引擎目前 **不支持** 的账号要素（预设里无法表达，见 docs/loadouts.md）：
- 偶像卡 ポテンシャル（``IdolCard.idolCardPotentialId`` / ``idolCardPotentialProduceSkillId`` 未被 ``idol_config`` 读取）；
- プリマステラ 技能（``idolCardPrimaStellaProduceSkillId`` 未被读取）；
- 培育メモリー（``IdolLoadout`` 没有メモリー字段；引擎里只有 選抜試験メモリー → 本戦 的交接）。

用法::

    from gakumas_arena.loadouts import get_loadout, list_loadouts
    from gakumas_arena.sim import run_produce
    run_produce("hif", loadout="hif_sense_default", seed=1, policy="heuristic")
    run_produce("hif", seed=1, policy="heuristic")   # scenario="hif" 时默认即 hif_sense_default
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

from gakumas_rl.interfaces.service import LoadoutConfig
from gakumas_rl.loadout import DEFAULT_DEARNESS_LEVEL
from gakumas_rl.repository.master_data import ScenarioSpec
from gakumas_rl.support_card_selector import SupportCardAutoSelectConfig, auto_select_support_cards

__all__ = [
    "PLAN_TYPES",
    "PLAN_LABELS",
    "LoadoutPreset",
    "PRESETS",
    "DEFAULT_PRESET_BY_SCENARIO",
    "get_loadout",
    "list_loadouts",
    "default_loadout_name",
    "describe_loadout",
    "suggest_support_cards",
    "apply_preset_to_scenario",
    "hif_growth_panel_max_levels",
]

#: 主数据 ``ProducePlanType`` → 预设名里的短标签。
PLAN_TYPES: dict[str, str] = {
    "sense": "ProducePlanType_Plan1",
    "logic": "ProducePlanType_Plan2",
    "anomaly": "ProducePlanType_Plan3",
}
PLAN_LABELS: dict[str, str] = {"sense": "センス", "logic": "ロジック", "anomaly": "アノマリー"}

_TRANSLATION_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "GakumasTranslationData" / "local-files" / "masterTrans"

#: H.I.F ボーナス 面板全部拉满时的等级（01~04 上限 5，05~09 上限 6；见 ``hif_growth_panel_max_levels``）。
_HIF_GROWTH_MAX: dict[str, int] = {"01": 5, "02": 5, "03": 5, "04": 5, "05": 6, "06": 6, "07": 6, "08": 6, "09": 6}


@dataclass(frozen=True)
class LoadoutPreset:
    """一套命名编成。``to_loadout_config`` 转成 gakumas_rl 的 ``LoadoutConfig``。"""

    name: str
    scenario: str
    plan: str
    idol_card_id: str
    support_card_ids: tuple[str, ...]
    idol_rank: int = 6
    producer_level: int = 50
    dearness_level: int = DEFAULT_DEARNESS_LEVEL
    support_card_level: int = 60
    use_after_item: bool | None = None
    challenge_item_ids: tuple[str, ...] = ()
    #: 剧本级覆盖：H.I.F ボーナス 成长面板等级（仅对 produce-007/008 生效）。
    hif_growth_panel_levels: dict[str, int] = field(default_factory=dict)
    description: str = ""

    def to_loadout_config(self, **overrides: Any) -> LoadoutConfig:
        cfg = LoadoutConfig(
            idol_card_id=self.idol_card_id,
            producer_level=int(self.producer_level),
            idol_rank=int(self.idol_rank),
            dearness_level=int(self.dearness_level),
            use_after_item=self.use_after_item,
            auto_support_cards=not self.support_card_ids,
            support_card_ids=tuple(self.support_card_ids),
            support_card_level=int(self.support_card_level),
            challenge_item_ids=tuple(self.challenge_item_ids),
        )
        return replace(cfg, **overrides) if overrides else cfg


def hif_growth_panel_max_levels() -> dict[str, int]:
    """从主数据 ``ProduceGrowthPanel`` 读取 H.I.F 面板各项的最高等级（``{'01': 5, ..., '09': 6}``）。"""

    from gakumas_arena.env import get_repository

    levels: dict[str, int] = {}
    for row in get_repository().load_table("ProduceGrowthPanel").rows:
        if str(row.get("produceGrowthPanelSheetId") or "") != "produce_growth_panel_sheet-hif":
            continue
        key = str(row.get("id") or "").rsplit("-", 1)[-1]
        levels[key] = max(levels.get(key, 0), int(row.get("level") or 0))
    return levels


def suggest_support_cards(
    idol_card_id: str,
    scenario: str = "hif",
    *,
    level: int = 60,
    idol_rank: int = 6,
    producer_level: int = 50,
) -> tuple[str, ...]:
    """用 gakumas_rl 的自动编成器为偶像挑 6 张支援卡（预设里固化的 id 即由此生成）。"""

    from gakumas_arena.env import build_loadout, get_repository, get_scenario

    spec = get_scenario(scenario)
    base = build_loadout(
        scenario,
        idol_card_id,
        LoadoutConfig(idol_card_id=idol_card_id, idol_rank=idol_rank, producer_level=producer_level, auto_support_cards=False),
    )
    chosen = auto_select_support_cards(
        get_repository(), spec, base, SupportCardAutoSelectConfig(support_card_level=int(level), deck_size=6)
    )
    return tuple(card.support_card_id for card in chosen)


def _hif_preset(name: str, plan: str, idol_card_id: str, support_card_ids: tuple[str, ...], description: str) -> LoadoutPreset:
    return LoadoutPreset(
        name=name,
        scenario="hif",
        plan=plan,
        idol_card_id=idol_card_id,
        support_card_ids=support_card_ids,
        hif_growth_panel_levels=dict(_HIF_GROWTH_MAX),
        description=description,
    )


# 支援卡 id 由 ``suggest_support_cards(idol, "hif", level=60)`` 生成（selector：偏好偶像三维×剧本权重排序的类型，
# 3/2/1 槽位 + 事件/技能/SP 加成），固化在此以保证基线稳定；主数据更新后可重新生成并更新 docs/loadouts.md。
PRESETS: dict[str, LoadoutPreset] = {
    preset.name: preset
    for preset in (
        _hif_preset(
            "hif_sense_default",
            "sense",
            "i_card-hski-3-019",
            ("s_card-3-0010", "s_card-3-0001", "s_card-3-0098", "s_card-3-0030", "s_card-3-0070", "s_card-3-0093"),
            "花海咲季 SSR「GO MY WAY!!」（センス）rank6 + 6 张 SSR 支援卡 Lv60 + H.I.F ボーナス 面板全满",
        ),
        _hif_preset(
            "hif_logic_default",
            "logic",
            "i_card-atbm-3-000",
            ("s_card-3-0010", "s_card-3-0001", "s_card-3-0037", "s_card-3-0030", "s_card-3-0070", "s_card-3-0093"),
            "SSR「理論武装して」（ロジック）rank6 + 6 张 SSR 支援卡 Lv60 + H.I.F ボーナス 面板全满",
        ),
        _hif_preset(
            "hif_anomaly_default",
            "anomaly",
            "i_card-hmsz-3-016",
            ("s_card-3-0010", "s_card-3-0001", "s_card-3-0037", "s_card-3-0030", "s_card-3-0070", "s_card-3-0093"),
            "SSR「VEIL」（アノマリー）rank6 + 6 张 SSR 支援卡 Lv60 + H.I.F ボーナス 面板全满",
        ),
    )
}

#: 剧本 id → 未指定编成时使用的预设。
DEFAULT_PRESET_BY_SCENARIO: dict[str, str] = {
    "produce-007": "hif_sense_default",
    "produce-008": "hif_sense_default",
}


def list_loadouts() -> list[str]:
    return list(PRESETS)


def get_loadout(name: str) -> LoadoutPreset:
    key = str(name).strip()
    if key not in PRESETS:
        raise KeyError(f"unknown loadout preset {name!r}; available: {', '.join(PRESETS)}")
    return PRESETS[key]


def default_loadout_name(scenario_id: str) -> str | None:
    """剧本对应的默认预设名（没有则 None，facade 退回 ``DEFAULT_IDOL`` + 自动支援卡）。"""

    return DEFAULT_PRESET_BY_SCENARIO.get(str(scenario_id))


def apply_preset_to_scenario(spec: ScenarioSpec, preset: LoadoutPreset | None) -> ScenarioSpec:
    """把预设里的剧本级覆盖（目前只有 H.I.F 成长面板）写进 ``ScenarioSpec``。"""

    if preset is None or not preset.hif_growth_panel_levels or getattr(spec, "hif", None) is None:
        return spec
    return replace(spec, hif=replace(spec.hif, growth_panel_levels=dict(preset.hif_growth_panel_levels)))


@lru_cache(maxsize=8)
def _translation(table: str) -> dict[str, dict[str, Any]]:
    path = _TRANSLATION_DIR / f"{table}.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(row.get("id")): row for row in payload.get("data", []) if isinstance(row, dict) and row.get("id")}


def _character_name(character_id: str) -> str:
    row = _translation("Character").get(character_id) or {}
    return f"{row.get('lastName', '')}{row.get('firstName', '')}" or character_id


def describe_loadout(name: str) -> dict[str, Any]:
    """预设内容（含日文原名 + 中文译名，译名来自 data/raw/GakumasTranslationData）。"""

    from gakumas_arena.env import get_repository

    preset = get_loadout(name)
    repo = get_repository()
    idol_row = repo.load_table("IdolCard").first(preset.idol_card_id) or {}
    idol_zh = (_translation("IdolCard").get(preset.idol_card_id) or {}).get("name")
    supports = []
    for card_id in preset.support_card_ids:
        row = repo.support_cards.first(card_id) or {}
        supports.append(
            {
                "id": card_id,
                "name": row.get("name"),
                "name_zh": (_translation("SupportCard").get(card_id) or {}).get("name"),
                "type": str(row.get("type") or "").rsplit("_", 1)[-1],
                "plan": str(row.get("planType") or "").rsplit("_", 1)[-1],
                "rarity": str(row.get("rarity") or "").rsplit("_", 1)[-1].upper(),
                "level": preset.support_card_level,
            }
        )
    return {
        "name": preset.name,
        "scenario": preset.scenario,
        "plan": preset.plan,
        "plan_label": PLAN_LABELS.get(preset.plan, preset.plan),
        "idol": {
            "id": preset.idol_card_id,
            "name": idol_row.get("name"),
            "name_zh": idol_zh,
            "character": _character_name(str(idol_row.get("characterId") or "")),
            "rarity": str(idol_row.get("rarity") or "").rsplit("_", 1)[-1].upper(),
            "rank": preset.idol_rank,
            "stats": [idol_row.get("produceVocal"), idol_row.get("produceDance"), idol_row.get("produceVisual")],
            "stamina": idol_row.get("produceStamina"),
            "exam_effect_type": idol_row.get("examEffectType"),
        },
        "producer_level": preset.producer_level,
        "dearness_level": preset.dearness_level,
        "support_cards": supports,
        "challenge_item_ids": list(preset.challenge_item_ids),
        "hif_growth_panel_levels": dict(preset.hif_growth_panel_levels),
        "description": preset.description,
    }
