import pytest

from gakumas_arena.masterdata import MasterData, default_dump_dir

pytestmark = pytest.mark.skipif(not default_dump_dir().is_dir(), reason="master data dump not fetched")


def test_card_effect_join():
    md = MasterData()
    card = next(md.where("ProduceCard", name="アピールの基本", upgradeCount=0))
    eff_id = card["playEffects"][0]["produceExamEffectId"]
    eff = md.get("ProduceExamEffect", eff_id)
    assert eff is not None and eff["id"] == eff_id


def test_enum_values():
    md = MasterData()
    plans = md.enum_values("ProduceCard", "planType")
    assert "ProducePlanType_Common" in plans
