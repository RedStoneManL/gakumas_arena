#!/usr/bin/env python3
"""Build docs/research/master_data_atlas.md and master_data_enums.md.

Sources:
  * the parsed dump (pickle cache produced by inspect_dump.py --cache)
  * the protobuf schema  (pmaster.proto / pcommon.proto / penum.proto)  - field types, full enum lists
  * hand-written Chinese annotations (atlas_annotations.py + atlas_annotations_more.py)

Usage:
  python tools/masterdata/build_docs.py --cache /tmp/md.pkl --proto-dir DIR --out-dir docs/research [--dump-commit HASH] [--which atlas|enums|both]

Sections are appended to the output files as they are produced (flush after every section).
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pickle
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import atlas_annotations as A
import atlas_annotations_more as A2
import inspect_dump as ins

# --------------------------------------------------------------------------- proto parsing


def parse_messages(path, prefix="", out=None):
    """{message: [(field, type, repeated)]}; keys are registered as `prefix.Name`, `Outer.Inner`
    and the bare name (bare name is only set if not already present, so load pmaster first)."""
    out = {} if out is None else out
    stack = []  # nested messages: `message Outer { message Inner {...} }`
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*message\s+(\w+)\s*\{", line)
        if m:
            name = m.group(1)
            full = ".".join([s for s in stack] + [name])
            stack.append(name)
            out[full + "@" + prefix] = []
            for key in ((prefix + "." + full) if prefix else None, full, name):
                # top-level pmaster messages own the bare name (nested helpers like
                # CharacterDearnessLevel.ProduceSkill must not shadow the real table)
                if key and (key not in out or (key == name and len(stack) == 1 and prefix == "pmaster")):
                    out[key] = out[full + "@" + prefix]
            continue
        if re.match(r"\s*(enum|oneof)\s+\w+\s*\{", line):
            stack.append("")  # ignore enum/oneof bodies but keep brace balance
            continue
        if stack and re.match(r"\s*\}", line):
            stack.pop()
            continue
        if stack and stack[-1]:
            m = re.match(r"\s*(repeated\s+)?([\w.]+)\s+(\w+)\s*=\s*\d+", line)
            if m:
                out[".".join(stack) + "@" + prefix].append((m.group(3), m.group(2), bool(m.group(1))))
    return out


def parse_enums(path):
    """{enum: [(value, number)]}"""
    out = {}
    cur = None
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\s*enum\s+(\w+)\s*\{", line)
        if m:
            cur = m.group(1)
            out[cur] = []
            continue
        if cur and re.match(r"\s*\}", line):
            cur = None
            continue
        if cur:
            m = re.match(r"\s*(\w+)\s*=\s*(-?\d+)", line)
            if m:
                out[cur].append((m.group(1), int(m.group(2))))
    return out


# --------------------------------------------------------------------------- rendering helpers

def render_desc(ds):
    s = ""
    for d in ds:
        if d.get("text"):
            s += d["text"]
        elif d.get("produceDescriptionType") == "ProduceDescriptionType_PlainText":
            s += "\n"
    return re.sub(r"</?nobr>", "", s).strip().replace("\n", " / ")


def trim_val(v, maxlen=60):
    if isinstance(v, str):
        return v if len(v) <= maxlen else v[: maxlen - 1] + "…"
    if isinstance(v, list):
        if v and all(isinstance(x, dict) for x in v) and "produceDescriptionType" in v[0]:
            return "(渲染) " + trim_val(render_desc(v), 160)
        out = [trim_val(x, maxlen) for x in v[:5]]
        if len(v) > 5:
            out.append(f"…(+{len(v) - 5})")
        return out
    if isinstance(v, dict):
        return {k: trim_val(x, maxlen) for k, x in v.items()}
    return v


def sample_row(r):
    out = {}
    for k, v in r.items():
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v) and "produceDescriptionType" in v[0]:
            out[k] = "(渲染) " + trim_val(render_desc(v), 200)
        elif v in ("", 0, False, [], None) or (isinstance(v, str) and v.endswith("_Unknown")):
            continue
        else:
            out[k] = trim_val(v, 90)
    return out


def md_escape(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


DESC_SUFFIX = ("produceDescriptions", "customizeProduceDescriptions", "playProduceDescriptions",
               "playEffectProduceDescriptions", "upgradeProduceCardProduceDescriptions")


class Builder:
    def __init__(self, tables, stats, msgs, enums, fks, commit):
        self.T, self.S, self.M, self.E, self.commit = tables, stats, msgs, enums, commit
        self.fks = collections.defaultdict(list)
        for t, path, target, m, n, r in fks:
            self.fks[t].append((path, target, m, n, r))
        self.enum_use = collections.defaultdict(collections.Counter)  # value -> Counter(table.field)
        for t, fs in stats.items():
            for path, st in fs.items():
                for v, c in st.enum_values.items():
                    self.enum_use[v][f"{t}.{path}"] += c

    # ---- proto helpers
    def field_type(self, table, path):
        msg = self.M.get(table)
        parts = path.split(".")
        for i, p in enumerate(parts):
            if not msg:
                return "?"
            hit = [f for f in msg if f[0] == p]
            if not hit:
                return "?"
            name, ty, rep = hit[0]
            if i == len(parts) - 1:
                short = ty.split(".")[-1]
                return ("repeated " if rep else "") + short
            msg = self.M.get(ty) or self.M.get(ty.split(".")[-1])
        return "?"

    def annot(self, table):
        return A.T.get(table) or {"desc": "", "fields": {}, "notes": "", "fk": []}

    def field_meaning(self, table, path):
        ann = self.annot(table)["fields"]
        if path in ann:
            return ann[path]
        leaf = path.rsplit(".", 1)[-1]
        parent = path.rsplit(".", 1)[0] if "." in path else ""
        if parent.endswith(DESC_SUFFIX) and leaf in A.NESTED["produceDescriptions"]:
            return A.NESTED["produceDescriptions"][leaf]
        if leaf in A.COMMON:
            return A.COMMON[leaf]
        if leaf.endswith("Ids") or leaf.endswith("Id"):
            return "外键/引用 id（见 FK）。"
        return "（未注释）"

    # ---- atlas table block
    def table_block(self, table):
        rows = self.T.get(table, [])
        st = self.S.get(table, {})
        ann = self.annot(table)
        lines = [f"### {table}（{len(rows)} 行）", ""]
        if ann["desc"]:
            lines += [ann["desc"], ""]
        if table not in self.M:
            lines.append("> proto 中无同名 message。")
        if rows:
            lines += ["| 字段 | proto 类型 | 非空率 | 含义 | 示例值 |", "|---|---|---|---|---|"]
            for path, fs in st.items():
                parent = path.rsplit(".", 1)[0] if "." in path else ""
                if parent.endswith(DESC_SUFFIX):
                    continue  # explained once in §2
                ty = self.field_type(table, path)
                ratio = f"{(fs.n - fs.empty) / fs.n:.0%}" if fs.n else "-"
                ex = ", ".join(md_escape(json.dumps(trim_val(x, 40), ensure_ascii=False)) for x in fs.samples[:2])
                indent = "&nbsp;&nbsp;↳ " if "." in path else ""
                lines.append(f"| {indent}`{path.rsplit('.', 1)[-1] if '.' in path else path}` | {ty} | {ratio} | {md_escape(self.field_meaning(table, path))} | {ex} |")
            lines.append("")
        # FK
        fk_lines = []
        for path, target, m, n, r in self.fks.get(table, []):
            if target is None:
                continue
            if r >= 0.9:
                fk_lines.append(f"- `{path}` → **{target}** ({m}/{n} 命中)")
            elif r > 0:
                fk_lines.append(f"- `{path}` → {target.rstrip('?')}? ({m}/{n} = {r:.0%}，多态或部分引用)")
        fk_lines += [f"- {x}" for x in ann["fk"]]
        if fk_lines:
            lines += ["外键（按 id 连接验证）："] + fk_lines + [""]
        # samples
        if rows:
            picks = [rows[0]] + ([rows[len(rows) // 2]] if len(rows) > 1 else [])
            lines.append("代表行：")
            lines.append("```json")
            for r in picks:
                lines.append(json.dumps(sample_row(r), ensure_ascii=False))
            lines.append("```")
            lines.append("")
        if ann["notes"]:
            lines += [ann["notes"], ""]
        return "\n".join(lines) + "\n"

    # ---- enum section
    def enum_family(self, fam):
        proto_vals = self.E.get(fam)
        dump = collections.Counter()
        for v, cnt in self.enum_use.items():
            if v.split("_", 1)[0] == fam:
                dump[v] = sum(cnt.values())
        lines = []
        if proto_vals is None:
            lines.append(f"### {fam}（dump 中出现，proto 未定义 — 可能是 id 噪声）")
        else:
            lines.append(f"### {fam}（proto 定义 {len(proto_vals)} 个值；dump 中出现 {len(dump)} 个）")
        notes = A2.ENUM_NOTES.get(fam, {})
        lines += ["", "| 值 | proto# | dump 出现次数 | 出现字段（前 4） | 含义 |", "|---|---|---|---|---|"]
        seen = set()
        order = [(v, n) for v, n in (proto_vals or [])] + [(v, "") for v in sorted(dump) if v not in {p[0] for p in (proto_vals or [])}]
        for v, n in order:
            seen.add(v)
            short = v.split("_", 1)[1] if "_" in v else v
            cnt = dump.get(v, 0)
            where = "; ".join(f"{k}={c}" for k, c in self.enum_use[v].most_common(4)) if cnt else "—"
            flag = "" if cnt else " **(dump 中无)**"
            if n == "":
                flag = " **(不在 proto 中)**"
            note = notes.get(short, "")
            lines.append(f"| `{short}`{flag} | {n} | {cnt} | {md_escape(where)} | {md_escape(note)} |")
        return "\n".join(lines) + "\n\n"


# --------------------------------------------------------------------------- effect profile for the enums doc

def effect_profile(b: Builder):
    T = b.T
    DE = {r["type"]: r for r in T["ProduceDescriptionExamEffect"]}
    LB = {r["id"]: r for r in T["ProduceDescriptionLabel"]}
    E = {r["id"]: r for r in T["ProduceExamEffect"]}
    NUM = ["effectValue1", "effectValue2", "effectCount", "effectTurn", "targetProduceCardId", "targetUpgradeCount",
           "produceCardSearchId", "movePositionType", "pickRangeType", "pickCountReferenceProduceCardSearchId", "pickCountType",
           "pickCountMin", "pickCountMax", "chainProduceExamEffectId", "chainProduceExamEffectIds", "produceExamStatusEnchantId", "produceCardGrowEffectIds"]
    bytype = collections.defaultdict(list)
    for r in T["ProduceExamEffect"]:
        bytype[r["effectType"]].append(r)
    use = collections.defaultdict(collections.Counter)

    def note(eid, src):
        if eid in E:
            use[E[eid]["effectType"]][src] += 1
    for r in T["ProduceCard"]:
        for pe in r["playEffects"]:
            note(pe["produceExamEffectId"], "ProduceCard.playEffects")
        for e in r["moveProduceExamEffectIds"]:
            note(e, "ProduceCard.move")
    for r in T["ProduceExamStatusEnchant"]:
        for e in r["produceExamEffectIds"]:
            note(e, "StatusEnchant")
    for r in T["ProduceExamGimmickEffectGroup"]:
        note(r["produceExamEffectId"], "Gimmick")
    for r in T["ProduceDrinkEffect"]:
        note(r["produceExamEffectId"], "Drink")
    for r in T["ProduceCardGrowEffect"]:
        if r["playProduceExamEffectId"]:
            note(r["playProduceExamEffectId"], "GrowEffect")
    for r in T["ProduceExamEffect"]:
        if r["chainProduceExamEffectId"]:
            note(r["chainProduceExamEffectId"], "chain")
        for e in r["chainProduceExamEffectIds"]:
            note(e, "chain")
    notes = A2.ENUM_NOTES.get("ProduceExamEffectType", {})
    proto = [v for v, _ in b.E.get("ProduceExamEffectType", [])]
    alltypes = proto + sorted(set(list(bytype) + list(DE)) - set(proto))
    out = []
    for ty in alltypes:
        short = ty.split("_", 1)[1]
        rows = bytype.get(ty, [])
        de = DE.get(ty)
        out.append(f"#### {short}  — rows={len(rows)}" + (f"  UI名=**{de['name']}**" if de else "  （无 UI 名称行）"))
        out.append("")
        if notes.get(short):
            out.append(f"- 语义：{notes[short]}")
        if de:
            lb = LB.get(de["produceDescriptionLabelId"])
            if lb and lb["produceDescriptions"]:
                out.append(f"- 说明文（{de['produceDescriptionLabelId']}）：{render_desc(lb['produceDescriptions'])}")
            elb = LB.get(de["examProduceDescriptionLabelId"])
            if elb and elb is not lb and elb["produceDescriptions"]:
                out.append(f"- 考试内说明（{de['examProduceDescriptionLabelId']}）：{render_desc(elb['produceDescriptions'])}")
            extra = []
            if de["mainBuffMinThresholds"]:
                extra.append(f"图标阈值={de['mainBuffMinThresholds']}")
            if de["produceDescriptionSwapId"]:
                extra.append(f"swap={de['produceDescriptionSwapId']}")
            if de["noIcon"]:
                extra.append("noIcon")
            if de["noReference"]:
                extra.append("noReference")
            if extra:
                out.append("- " + "，".join(extra))
        if not rows:
            out.append("- dump 中无 ProduceExamEffect 行。")
            out.append("")
            continue
        nz = collections.Counter()
        vals = collections.defaultdict(set)
        for r in rows:
            for f in NUM:
                v = r[f]
                if v not in (0, "", [], None) and not (isinstance(v, str) and v.endswith("_Unknown")):
                    nz[f] += 1
                    if len(vals[f]) < 14:
                        vals[f].add(v if not isinstance(v, list) else tuple(v))
        out.append("- 非零字段：" + ", ".join(f"`{f}` {c}/{len(rows)}" for f, c in nz.most_common()))
        for f in ("effectValue1", "effectValue2", "effectCount", "effectTurn", "pickRangeType", "movePositionType", "pickCountMin", "pickCountMax"):
            if f in vals:
                vv = sorted(vals[f], key=lambda x: (isinstance(x, str), x))
                out.append(f"  - {f} 取值：{[x.split('_', 1)[1] if isinstance(x, str) and '_' in x else x for x in vv]}")
        out.append("- 被谁引用：" + (", ".join(f"{k}={c}" for k, c in use[ty].most_common()) or "（无引用）"))
        ex = rows[0]
        exrow = {k: v for k, v in sample_row(ex).items() if k not in ("effectType", "effectGroupIds", "produceDescriptions", "customizeProduceDescriptions")}
        out.append(f"- 示例行：`{json.dumps(exrow, ensure_ascii=False)}`")
        out.append(f"  - 文本：「{render_desc(ex['produceDescriptions'])}」")
        if len(rows) > 1:
            ex2 = rows[len(rows) // 2]
            out.append(f"  - 另一例 `{ex2['id']}`：「{render_desc(ex2['produceDescriptions'])}」")
        out.append("")
    return "\n".join(out) + "\n"


def trigger_profile(b: Builder):
    T = b.T
    out = ["#### ProduceExamPhaseType 各时机的触发器示例", ""]
    seen = collections.defaultdict(list)
    for r in T["ProduceExamTrigger"]:
        for p in r["phaseTypes"]:
            seen[p].append(r)
    notes = A2.ENUM_NOTES.get("ProduceExamPhaseType", {})
    for v, _ in b.E.get("ProduceExamPhaseType", []):
        rows = seen.get(v, [])
        short = v.split("_", 1)[1]
        pv = collections.Counter(tuple(r["phaseValues"]) for r in rows)
        out.append(f"- **{short}**（{len(rows)} 个触发器；phaseValues 分布 {dict(pv) if rows else '—'}）：{notes.get(short, '')}")
        for r in rows[:2]:
            out.append(f"  - `{r['id']}` → 「{render_desc(r['produceDescriptions'])}」 / 使用条件文案「{render_desc(r['playProduceDescriptions'])}」")
    out += ["", "#### ProduceExamFieldStatusType 各条件的触发器示例", ""]
    seen = collections.defaultdict(list)
    for r in T["ProduceExamTrigger"]:
        for i, f in enumerate(r["fieldStatusTypes"]):
            seen[f].append((r, r["fieldStatusValues"][i] if i < len(r["fieldStatusValues"]) else None))
    gim = collections.Counter((r["fieldStatusType"], r["fieldStatusCheckType"].split("_")[-1]) for r in T["ProduceExamGimmickEffectGroup"])
    notes = A2.ENUM_NOTES.get("ProduceExamFieldStatusType", {})
    for v, _ in b.E.get("ProduceExamFieldStatusType", []):
        rows = seen.get(v, [])
        short = v.split("_", 1)[1]
        vals = collections.Counter(x for _, x in rows)
        g = {k[1]: c for k, c in gim.items() if k[0] == v}
        out.append(f"- **{short}**（触发器 {len(rows)}，阈值分布 {dict(vals) if rows else '—'}；Gimmick 中 {g or '—'}）：{notes.get(short, '')}")
        for r, x in rows[:2]:
            out.append(f"  - `{r['id']}` → 「{render_desc(r['produceDescriptions'])}」")
    return "\n".join(out) + "\n\n"


def produce_effect_profile(b: Builder):
    T = b.T
    DPE = {r["type"]: r for r in T["ProduceDescriptionProduceEffect"]}
    users = collections.defaultdict(list)
    for r in T["ProduceSkill"]:
        users[r["produceEffectId1"]].append(("Skill", render_desc(r["produceDescriptions"])))
    IE = {r["id"]: r for r in T["ProduceItemEffect"]}
    for r in T["ProduceItem"]:
        for s in r["skills"]:
            ie = IE[s["produceItemEffectId"]]
            if ie["produceEffectId"]:
                users[ie["produceEffectId"]].append(("Item", render_desc(r["produceDescriptions"])))
    for r in T["ProduceStepEventDetail"]:
        for e in r["produceEffectIds"]:
            users[e].append(("Event", render_desc(r["produceDescriptions"])))
    for r in T["ProduceStepEventSuggestion"]:
        for e in r["produceEffectIds"] + r["successProduceEffectIds"] + r["failProduceEffectIds"]:
            users[e].append(("Suggestion", render_desc(r["produceDescriptions"])))
    for r in T["ProduceGrowthPanel"]:
        for e in r["produceEffectIds"]:
            users[e].append(("GrowthPanel", render_desc(r["produceDescriptions"])))
    for r in T["ProduceCustomizeItem"]:
        for e in r["produceEffectIds"]:
            users[e].append(("CustomizeItem", render_desc(r["produceDescriptions"])))
    bytype = collections.defaultdict(list)
    for r in T["ProduceEffect"]:
        bytype[r["produceEffectType"]].append(r)
    notes = A2.ENUM_NOTES.get("ProduceEffectType", {})
    out = []
    for v, _ in b.E.get("ProduceEffectType", []):
        short = v.split("_", 1)[1]
        rows = bytype.get(v, [])
        d = DPE.get(v)
        out.append(f"#### {short} — rows={len(rows)}" + (f"  UI名=**{d['name']}**" if d else ""))
        if notes.get(short):
            out.append(f"- 语义：{notes[short]}")
        if not rows:
            out.append("- dump 中无 ProduceEffect 行。")
            out.append("")
            continue
        nz = collections.Counter()
        for r in rows:
            for f in ("effectValueMin", "effectValueMax", "produceResourceType", "produceRewards", "produceCardSearchId", "produceExamStatusEnchantId", "pickRangeType", "pickCountMin", "pickCountMax", "isResearch"):
                x = r[f]
                if x not in (0, "", [], False) and not (isinstance(x, str) and x.endswith("_Unknown")):
                    nz[f] += 1
        vals = sorted(set((r["effectValueMin"], r["effectValueMax"]) for r in rows))[:10]
        out.append(f"- 非零字段：{dict(nz)}；(min,max) 取值：{vals}")
        uc = collections.Counter(u[0] for r in rows for u in users.get(r["id"], []))
        out.append(f"- 被谁引用：{dict(uc) or '（无引用）'}")
        ex = rows[0]
        out.append(f"- 示例行：`{json.dumps({k: v for k, v in sample_row(ex).items() if k != 'produceEffectType'}, ensure_ascii=False)}`")
        us = users.get(ex["id"]) or next((users[r["id"]] for r in rows if users.get(r["id"])), [])
        if us:
            out.append(f"  - 文本（{us[0][0]}）：「{us[0][1][:200]}」")
        out.append("")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- documents

ATLAS_GROUPS = [
    ("A. 剧本与全局设定", ["Produce", "ProduceGroup", "ProduceSetting", "ExamSetting", "ProduceSeason", "ProduceSeasonZeroGrade", "ProduceGrade", "ResultGradePattern",
                          "ProduceHighScore", "ProduceLegendProduceCard", "ProduceCharacter", "ProduceCharacterUnit", "ProduceChallengeSlot", "ProduceChallengeCharacter",
                          "ProduceItemChallengeGroup", "ProduceNextIdolAuditionMasterRankingSeason", "ProduceGrowthPanelSheet", "ProduceGrowthPanel",
                          "ProduceLive", "ProduceLiveEvaluation", "ProduceNavigation"]),
    ("B. 周程：课程 / 试炼 / 事件", ["ProduceStepLesson", "ProduceStepLessonLevel", "ProduceStepSelfLesson", "ProduceStepOpenLesson", "ProduceStepAuditionDifficulty",
                                   "ProduceStepAuditionCharacter", "ProduceExamBattleConfig", "ProduceExamBattleScoreConfig", "ProduceExamBattleNpcGroup", "ProduceExamBattleNpcMob",
                                   "ProduceExamGimmickEffectGroup", "ProduceStepEventDetail", "ProduceStepEventSuggestion", "ProduceEventCharacterGrowth", "ProduceEventSupportCard",
                                   "ProduceStepTransition", "ProduceStepFanPresentMotion"]),
    ("C. 技能卡", ["ProduceCard", "ProduceCardTag", "ProduceCardSearch", "ProduceCardPool", "ProduceCardRandomPool", "ProduceCardConversion", "ProduceCardCustomize",
                 "ProduceCardCustomizeRarityEvaluation", "ProduceCardGrowEffect", "ProduceCardStatusEnchant", "ProduceCardStatusEffect", "ExamInitialDeck", "ProduceInitialDeck",
                 "ExamContestEmbedProduceCard", "PvpRateCommonProduceCard"]),
    ("D. 考试（レッスン/試験）效果引擎", ["ProduceExamEffect", "ProduceExamTrigger", "ProduceExamStatusEnchant", "EffectGroup", "ExamSimulation"]),
    ("E. 培育外循环效果：技能 / 道具 / 饮料", ["ProduceEffect", "ProduceTrigger", "ProduceSkill", "ProduceItem", "ProduceItemEffect", "ProduceDrink", "ProduceDrinkEffect",
                                          "ProduceCustomizeItem", "ProduceCustomizeItemRelationship", "MemoryAbility", "MemoryGift", "ProduceEffectIcon"]),
    ("F. 偶像卡 / 角色 / 支援卡", ["IdolCard", "IdolCardLevelLimit", "IdolCardLevelLimitProduceSkill", "IdolCardLevelLimitStatusUp", "IdolCardPotential", "IdolCardPotentialProduceSkill",
                                "IdolCardPrimaStellaProduceSkill", "IdolCardSimulation", "Character", "CharacterDearnessLevel", "CharacterTrueEndBonus", "SupportCard", "SupportCardBonus",
                                "SupportCardLevel", "SupportCardLevelLimit", "SupportCardProduceSkillLevelVocal", "SupportCardProduceSkillLevelDance", "SupportCardProduceSkillLevelVisual",
                                "SupportCardProduceSkillLevelAssist", "SupportCardProduceSkillFilter"]),
    ("G. 自动打牌评估", ["ProduceExamAutoEvaluation", "ProduceExamAutoTriggerEvaluation", "ProduceExamAutoPlayCardEvaluation", "ProduceExamAutoPlayProduceCardEvaluation",
                       "ProduceExamAutoCardSelectEvaluation", "ProduceExamAutoResourceEvaluation", "ProduceExamAutoGrowEffectEvaluation"]),
    ("H. 描述模板系统", ["ProduceDescriptionExamEffect", "ProduceDescriptionLabel", "ProduceDescriptionSwap", "ProduceDescriptionProduceCardGrowEffect",
                       "ProduceDescriptionProduceCardMovePosition", "ProduceDescriptionProduceEffect", "ProduceDescriptionProducePlan", "ProduceDescriptionProduceStep", "ProduceDescriptionProduceType"]),
    ("I. 通用条件/消耗", ["ConditionSet", "ConsumptionSet"]),
    ("J. 其他相关（备注级）", ["PvpRateConfig", "Tower", "CompetitionExamStatusEffectIcon", "ProduceGuide", "ProduceStory", "ProduceStoryGroup", "ProduceAdv", "ProduceSplitAdv",
                          "ProduceGroupLiveCommon", "SeminarExamTransition", "TutorialProduce", "TutorialProduceStep"]),
]


def write_atlas(b: Builder, path, intro_path):
    with open(path, "w", encoding="utf-8") as f:
        def emit(s):
            f.write(s)
            f.flush()
        emit(open(intro_path, encoding="utf-8").read().replace("{{COMMIT}}", b.commit))
        # overview table
        covered = [t for _, ts in ATLAS_GROUPS for t in ts]
        emit("\n## 1. 表总览\n\n")
        emit(f"dump 共 {len(b.T)} 张表；本图谱详述 {len(covered)} 张。全部表的行数：\n\n")
        emit("| 表 | 行数 | 本文分组 |\n|---|---|---|\n")
        grp = {t: g for g, ts in ATLAS_GROUPS for t in ts}
        for t in sorted(b.T):
            emit(f"| {t} | {len(b.T[t])} | {grp.get(t, '')} |\n")
        emit("\n")
        # nested structures
        emit("## 2. 通用嵌套结构\n\n### 2.1 produceDescriptions[]（pcommon.ProduceDescriptionSegment）\n\n")
        emit("几乎所有效果表都带 `produceDescriptions`（2025-01-20 起独立的 ProduceDescription 表被删除，描述改为内联到各行）。"
             "每个片段是一段“模板 token”，**`text` 字段已经是渲染后的文本**（数值、卡名、标签名都已填入），因此把片段的 text 顺序拼接（空 PlainText 视为换行，去掉 `<nobr>`）就能得到游戏内显示的完整效果说明。"
             "只有 `Exam` 型且 `examDescriptionType` 为 ExamValue/ExamTurn/ExamCount/… 的片段 text 为空——它们是 **Label 模板**里留给运行时填充的槽。\n\n")
        emit("| 片段字段 | proto 类型 | 含义 |\n|---|---|---|\n")
        for name, ty, rep in b.M.get("ProduceDescriptionSegment", []):
            emit(f"| `{name}` | {('repeated ' if rep else '') + ty.split('.')[-1]} | {md_escape(A.NESTED['produceDescriptions'].get(name, ''))} |\n")
        emit("\n**模板→文本的映射规则**（由 ProduceDescription* 表定义）：\n\n"
             "1. `ProduceDescriptionType_ProduceExamEffectType` 片段：`examEffectType` → `ProduceDescriptionExamEffect.name`（如 ExamParameterBuff→好調），`targetId` 指向其说明 Label。\n"
             "2. `ProduceDescriptionType_ProduceDescriptionName`/`ProduceDescription` 片段：`targetId`=Label_*/Convert_* → `ProduceDescriptionLabel.name`；若 Label 带 `produceDescriptionSwapId`，按场景（レッスン/試験）用 `ProduceDescriptionSwap.text` 替换（パラメータ↔スコア、レッスン↔試験・ステージ）。\n"
             "3. `ProduceDescriptionType_Exam` 片段：按 `examDescriptionType` 从所属效果行取 effectValue1/2/effectCount/turn/costValue 格式化（Percent 型除以 10 显示为 %）。\n"
             "4. `ProduceCard`/`ProduceItem`/`ProduceDrink` 片段：`targetId`→对应表 name。\n"
             "5. `ProduceCardGrowEffectType` 片段 → `ProduceDescriptionProduceCardGrowEffect.name`；`ProduceCardCategory` → Label_ActiveSkillCard 等。\n"
             "6. Label 的 `produceDescriptions` 本身也是片段列表，可递归引用；其中 `Exam(ExamValue/ExamTurn…)` 槽由效果行的数值填充——这就是 **Label 模板** 与 **效果行** 的连接方式。\n\n")
        emit("### 2.2 playEffects[]（ProduceCard）\n\n| 字段 | 含义 |\n|---|---|\n")
        for k, v in A.NESTED["playEffects"].items():
            emit(f"| `{k}` | {v} |\n")
        emit("\n### 2.3 rewards[] / produceRewards[]\n\n`{resourceType, resourceId, quantity|resourceLevel}`，resourceId 按 resourceType 多态。\n\n")
        # groups
        n = 3
        for gname, tables in ATLAS_GROUPS:
            emit(f"## {n}. {gname}\n\n")
            for t in tables:
                emit(b.table_block(t))
            n += 1
        # relationships summary
        emit(f"## {n}. 关键关系链（供建模）\n\n")
        emit(open(os.path.join(HERE, "atlas_relations.md"), encoding="utf-8").read())
        n += 1
        # other tables
        emit(f"\n## {n}. 未详述但与培育/考试相关的其他表\n\n")
        others = [t for t in sorted(b.T) if t not in covered and re.search(r"Produce|Exam|Idol|Support|Memory|Competition|Pvp|Tower|Tour|Gvg|Seminar|Character", t)]
        for t in others:
            emit(f"- **{t}**（{len(b.T[t])} 行）：字段 {', '.join(k for k in b.S[t] if '.' not in k)[:300]}\n")
        emit("\n")


def write_enums(b: Builder, path, intro_path):
    with open(path, "w", encoding="utf-8") as f:
        def emit(s):
            f.write(s)
            f.flush()
        emit(open(intro_path, encoding="utf-8").read().replace("{{COMMIT}}", b.commit))
        # overview
        fams_dump = collections.Counter()
        for v, cnt in b.enum_use.items():
            fams_dump[v.split("_", 1)[0]] += 1
        emit("\n## 1. 枚举总览（penum.proto 全部 %d 个枚举）\n\n" % len(b.E))
        emit("| 枚举 | proto 值数 | dump 出现值数 | dump 总出现次数 | 主要字段 |\n|---|---|---|---|---|\n")
        for fam in sorted(b.E):
            vals = [v for v, _ in b.E[fam]]
            used = [v for v in vals if v in b.enum_use]
            total = sum(sum(b.enum_use[v].values()) for v in used)
            fields = collections.Counter()
            for v in used:
                for k, c in b.enum_use[v].items():
                    fields[k] += c
            emit(f"| {fam} | {len(vals)} | {len(used)} | {total} | {md_escape('; '.join(k for k, _ in fields.most_common(3)))} |\n")
        noise = [fam for fam in fams_dump if fam not in b.E]
        emit(f"\ndump 中形似枚举但 proto 未定义的前缀（多为 id 噪声）：{', '.join(sorted(noise))}\n\n")
        # key enum deep dives
        emit("## 2. 核心枚举详解\n\n")
        emit("### 2.1 ProduceExamEffectType（考试内效果类型）——效果解释器的实现清单\n\n")
        emit("每个值给出：语义（中文）、UI 名称与说明文（来自 ProduceDescriptionExamEffect → ProduceDescriptionLabel）、ProduceExamEffect 中的行数与非零字段、取值范围、引用来源、示例行与渲染文本。"
             "`v1/v2` 指 effectValue1/2；‰ 表示千分比。\n\n")
        emit(effect_profile(b))
        emit("### 2.2 ProduceExamPhaseType / ProduceExamFieldStatusType（触发时机与条件）\n\n")
        emit(trigger_profile(b))
        emit("### 2.3 ProduceEffectType（培育外循环效果类型）\n\n")
        emit(produce_effect_profile(b))
        # full lists
        emit("## 3. 全部枚举：完整取值与计数\n\n每张表：proto 定义值（含 dump 中未出现者）+ dump 中出现但 proto 未定义者；计数为该值在整个 dump（含嵌套 produceDescriptions）中的出现次数。\n\n")
        key_first = ["ProduceExamEffectType", "ProduceExamPhaseType", "ProduceExamFieldStatusType", "ProduceExamTriggerCheckType", "ProduceEffectType", "ProducePhaseType",
                     "ProduceCardGrowEffectType", "ProducePlanType", "ProduceStepType", "ProduceStepBusinessType", "ProduceCardCategory", "ProduceCardRarity", "ExamCostType",
                     "ProduceCardMovePositionType", "ProduceCardMoveEffectTriggerType", "ProduceCardPositionType", "ProduceCardOrderType", "ProducePickRangeType", "ProducePickCountType",
                     "ExamDescriptionType", "ProduceDescriptionType", "ProduceDescriptionSwapType", "ProduceExamAutoEvaluationType", "ProduceExamAutoCardSelectEvaluationType", "ExamPlayType",
                     "ProduceType", "ProduceSplitType", "ExamStatusEffectType", "ProduceItemEffectType", "ProduceResourceType", "ProduceEventType", "ProduceEventCharacterType",
                     "ProduceStepAuditionType", "ProduceStepLessonType", "ProduceStepPhaseType", "ResultGrade", "ResultGradeType", "ProduceLiveType", "ProduceItemRarity", "ProduceDrinkRarity",
                     "SkillRarity", "IdolCardRarity", "IdolCardLevelLimitRank", "IdolCardLevelLimitEffectType", "IdolCardPotentialRank", "IdolCardPotentialEffectType",
                     "SupportCardType", "SupportCardRarity", "SupportCardLevelLimitRank", "ProduceParameterType", "ProduceMemoryProduceCardPhaseType", "ProducerLevelUnlockType",
                     "ConditionType", "ConditionOperatorType", "ConditionMinMaxType", "ResourceType"]
        done = set()
        for fam in key_first + sorted(set(b.E) - set(key_first)):
            if fam in done or fam not in b.E:
                continue
            done.add(fam)
            emit(b.enum_family(fam))
        for fam in sorted(fams_dump):
            if fam not in b.E:
                emit(b.enum_family(fam))
        # HIF grep
        emit("## 4. H.I.F / プリマステラ / festival 相关出现位置（grep）\n\n")
        hits, ex = ins.grep(b.T, r"hif|primastella|prima_stella|festival|fes\b|_fes|fes_|hatsuboshi_idol")
        emit("| 表.字段 | 命中数 | 示例 |\n|---|---|---|\n")
        for (t, p), c in sorted(hits.items(), key=lambda kv: -kv[1]):
            emit(f"| {t}.{p} | {c} | {md_escape(ex[(t, p)][:100])} |\n")
        emit("\n")
        emit(open(os.path.join(HERE, "enums_hif_notes.md"), encoding="utf-8").read())
        # appendix per-field
        emit("\n## 5. 附录：按字段列出的枚举取值（dump 实测）\n\n")
        for t, p, cnt in ins.enum_fields(b.S):
            emit(f"- `{t}.{p}`：" + ", ".join(f"{v.split('_', 1)[1] if '_' in v else v}={c}" for v, c in sorted(cnt.items())) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--proto-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--dump-commit", default="(unknown)")
    ap.add_argument("--which", default="both", choices=["atlas", "enums", "both"])
    a = ap.parse_args()
    tables = pickle.load(open(a.cache, "rb"))
    stats = ins.analyse(tables)
    msgs = {}
    for fn in ("pmaster.proto", "pcommon.proto"):
        parse_messages(os.path.join(a.proto_dir, fn), prefix=fn.split(".")[0], out=msgs)
    enums = parse_enums(os.path.join(a.proto_dir, "penum.proto"))
    fks = ins.infer_fks(tables, stats)
    b = Builder(tables, stats, msgs, enums, fks, a.dump_commit)
    os.makedirs(a.out_dir, exist_ok=True)
    if a.which in ("atlas", "both"):
        write_atlas(b, os.path.join(a.out_dir, "master_data_atlas.md"), os.path.join(HERE, "atlas_intro.md"))
        print("atlas written")
    if a.which in ("enums", "both"):
        write_enums(b, os.path.join(a.out_dir, "master_data_enums.md"), os.path.join(HERE, "enums_intro.md"))
        print("enums written")


if __name__ == "__main__":
    main()
