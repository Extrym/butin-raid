"""Construit data/items-forever.json (catalogue Forever PROVISOIRE) à partir de la base du projet
ElliotWood/Forever (MIT), elle-même tirée du client bêta de Forever via Wowhead et wago.tools.

Garde les objets nouveaux de Forever (identifiant >= 250000), qualité rare ou mieux, niveau d'objet 55+.
Les sources (boss, réputation) sont en grande partie inconnues tant que le jeu n'est pas sorti : les
raids ouvrent le 9 décembre 2026 et le butin n'est pas dans le client. Relancer après chaque mise à jour.

Usage :
  mkdir -p source/forever
  curl -L -o source/forever/db.json https://raw.githubusercontent.com/ElliotWood/Forever/HEAD/assets/database/db.json
  python3 scripts/build_forever.py
"""
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "source" / "forever" / "db.json"
OUT = ROOT / "data" / "items-forever.json"

db = json.load(open(SRC))

# Codes de proto/common.proto du projet ElliotWood/Forever.
STAT = {0: "Strength", 1: "Agility", 2: "Stamina", 3: "Intellect", 4: "Healing Power", 5: "Spell Damage",
        6: "Arcane Damage", 7: "Fire Damage", 8: "Frost Damage", 9: "Holy Damage", 10: "Nature Damage",
        11: "Shadow Damage", 12: "Spell Hit", 13: "Spell Crit", 14: "Spell Haste", 15: "Spell Piercing",
        16: "Spirit", 17: "Attack Power", 18: "Ranged Attack Power", 19: "Feral Attack Power", 20: "Hit",
        21: "Crit", 22: "Haste", 23: "Armor Penetration", 24: "Expertise", 25: "Defense", 26: "Block",
        27: "Block Value", 28: "Dodge", 29: "Parry", 30: "Armor", 31: "Bonus Armor", 32: "Health", 33: "Mana",
        34: "MP5", 35: "Arcane Resistance", 36: "Fire Resistance", 37: "Frost Resistance",
        38: "Nature Resistance", 39: "Shadow Resistance"}
PHYS = {0, 1, 17, 18, 20, 21, 22, 23, 24}
CASTER = {3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
HEAL = {3, 4, 16, 34}
TANK = {25, 26, 27, 28, 29, 31}
CLASS = {1: "war", 2: "pal", 3: "hun", 4: "rog", 5: "pri", 7: "sha", 8: "mag", 9: "wlk", 11: "dru"}
SLOT = {1: "Tête", 2: "Cou", 3: "Épaules", 4: "Dos", 5: "Torse", 6: "Poignets", 7: "Mains", 8: "Taille",
        9: "Jambes", 10: "Pieds", 11: "Anneau", 12: "Bijou", 14: "À distance"}
HAND = {1: "Main droite", 2: "Une main", 3: "Main gauche", 4: "Deux mains"}
ARMOR = {1: "Tissu", 2: "Cuir", 3: "Mailles", 4: "Plaques"}
WEAPON = {1: "Hache", 2: "Dague", 3: "Arme de pugilat", 4: "Masse", 5: "Tenu en main gauche", 6: "Arme d'hast",
          7: "Bouclier", 8: "Bâton", 9: "Épée"}
RANGED = {1: "Arc", 2: "Arbalète", 3: "Arme à feu", 4: "Arme de jet", 5: "Baguette", 6: "Idole", 7: "Libram",
          8: "Totem"}
PROF = {1: "Alchimie", 2: "Forge", 3: "Enchantement", 4: "Ingénierie", 7: "Joaillerie", 8: "Travail du cuir",
        11: "Couture"}
QUAL = {3: "rare", 4: "epic", 5: "legendary"}

ALL = ["war", "rog", "hun", "dru", "sha", "pal", "mag", "pri", "wlk"]
ARMOR_USERS = {1: ["mag", "pri", "wlk"], 2: ["rog", "dru"], 3: ["hun", "sha"], 4: ["war", "pal"]}
WEAPON_USERS = {
    (2, 0): ["rog", "war", "hun", "sha", "dru", "mag", "pri", "wlk"],
    (9, 1): ["war", "rog", "pal", "hun", "mag", "wlk"], (9, 2): ["war", "pal", "hun"],
    (1, 1): ["war", "pal", "hun", "sha"], (1, 2): ["war", "pal", "hun", "sha"],
    (4, 1): ["war", "rog", "pal", "sha", "dru", "pri"], (4, 2): ["war", "pal", "sha", "dru"],
    (6, 2): ["war", "pal", "hun"], (8, 2): ["war", "hun", "dru", "sha", "mag", "pri", "wlk"],
    (3, 1): ["war", "rog", "hun", "sha", "dru"], (7, 1): ["war", "pal", "sha"],
    (5, 1): ["mag", "pri", "wlk", "dru", "sha", "pal"],
}
RANGED_USERS = {1: ["war", "rog", "hun"], 2: ["war", "rog", "hun"], 3: ["war", "rog", "hun"], 4: ["war", "rog"],
                5: ["mag", "pri", "wlk"], 6: ["dru"], 7: ["pal"], 8: ["sha"]}


def ilvl(i):
    return max((o.get("ilvl", 0) for o in (i.get("scalingOptions") or {}).values()), default=0)


def stats_of(i):
    best = max((i.get("scalingOptions") or {}).values(), key=lambda o: o.get("ilvl", 0), default={})
    return {int(k): v for k, v in (best.get("stats") or {}).items() if v}


def users_of(i):
    if i.get("classAllowlist"):
        return [CLASS[c] for c in i["classAllowlist"] if c in CLASS]
    t = i.get("type")
    if t == 13:
        hands = 2 if i.get("handType") == 4 else 1
        wt = i.get("weaponType")
        return WEAPON_USERS.get((wt, hands)) or WEAPON_USERS.get((wt, 1)) or WEAPON_USERS.get((wt, 0)) or ALL
    if t == 14:
        return RANGED_USERS.get(i.get("rangedWeaponType"), ALL)
    if i.get("armorType") in ARMOR_USERS and t not in (4,):
        return ARMOR_USERS[i["armorType"]]
    return ALL


def roles_of(st, i):
    keys = set(st)
    r = set()
    if keys & PHYS: r.update(["melee", "ranged"])
    if keys & CASTER: r.update(["caster", "heal"])
    if 4 in keys or 34 in keys: r.add("heal")
    if keys & TANK: r.add("tank")
    if 19 in keys: r.update(["melee", "tank"])
    if not r and i.get("type") == 13 and i.get("weaponType") not in (5, 7, 8):
        r.update(["melee", "ranged"])
    return sorted(r)


def slot_of(i):
    t = i.get("type")
    if t == 13:
        return " · ".join(x for x in (HAND.get(i.get("handType"), "Arme"), WEAPON.get(i.get("weaponType"), "")) if x)
    if t == 14:
        return " · ".join(x for x in ("À distance", RANGED.get(i.get("rangedWeaponType"), "")) if x)
    return " · ".join(x for x in (SLOT.get(t, "Autre"), ARMOR.get(i.get("armorType"), "") if t not in (2, 4, 11, 12) else "") if x)


def source_of(i):
    for s in i.get("sources") or []:
        if "crafted" in s:
            return {"t": "craft", "zone": "Artisanat", "boss": PROF.get(s["crafted"].get("profession"), "Artisanat")}
        if "drop" in s:
            return {"t": "raid", "zone": "Butin (lieu à confirmer)", "boss": ""}
    return {"t": "unknown", "zone": "Source à confirmer", "boss": ""}


out = []
for i in db["items"]:
    if i["id"] < 250000 or i.get("quality", 0) < 3 or ilvl(i) < 55:
        continue
    st = stats_of(i)
    lines = [f"+{v} {STAT[k]}" for k, v in sorted(st.items()) if k in STAT]
    if i.get("setName"):
        lines.append(f"Set : {i['setName']}")
    out.append({
        "id": i["id"], "name": i["name"], "quality": QUAL.get(i["quality"], "rare"), "ilvl": ilvl(i), "req": 0,
        "slot": slot_of(i), "type": "", "phase": i.get("phase"), "restricted": bool(i.get("classAllowlist")),
        "classes": users_of(i), "roles": roles_of(st, i), "src": source_of(i), "stats": lines,
        "version": "forever", "provisional": True,
    })

out.sort(key=lambda x: (x["src"]["zone"], x["slot"], x["name"]))
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print(len(out), "objets Forever ->", OUT, f"({OUT.stat().st_size // 1024} Ko)")
print(Counter(x["src"]["zone"] for x in out))
print(Counter(x["quality"] for x in out))
