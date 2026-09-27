"""Construit data/items-classic.json à partir de la base ouverte nexus-devs/wow-classic-items (MIT).

Garde les objets Classic (Vanilla) de qualité Rare ou mieux, à partir du niveau 55,
qui viennent d'un donjon, d'un raid, de l'artisanat ou d'une quête.
Usage : python3 scripts/build_items.py
"""
import json
import pathlib
import re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "source"
OUT = ROOT / "data" / "items-classic.json"

items = json.load(open(SRC / "items-classic.json"))
zones = {z["id"]: z for z in json.load(open(SRC / "zones.json"))}

RAID_FR = {
    "Molten Core": "Molten Core", "Onyxia's Lair": "Onyxia", "Blackwing Lair": "Blackwing Lair",
    "Zul'Gurub": "Zul'Gurub", "Ruins of Ahn'Qiraj": "Ruines d'Ahn'Qiraj", "Ahn'Qiraj": "Temple d'Ahn'Qiraj",
    "Naxxramas": "Naxxramas",
}
RAID_ORDER = ["Molten Core", "Onyxia", "Zul'Gurub", "Blackwing Lair", "Ruines d'Ahn'Qiraj", "Temple d'Ahn'Qiraj", "Naxxramas"]
PROF_FR = {"Blacksmithing": "Forge", "Leatherworking": "Travail du cuir", "Tailoring": "Couture",
           "Engineering": "Ingénierie", "Alchemy": "Alchimie", "Enchanting": "Enchantement",
           "Jewelcrafting": "Joaillerie", "Cooking": "Cuisine", "First Aid": "Secourisme"}
CLASS_KEYS = {"Warrior": "war", "Rogue": "rog", "Hunter": "hun", "Druid": "dru", "Shaman": "sha",
              "Paladin": "pal", "Mage": "mag", "Priest": "pri", "Warlock": "wlk"}
SKIP_LINES = re.compile(r"^(Phase \d|Item Level|Binds|Unique|Durability|Requires Level|Sell Price|Dropped by|Drop Chance|Classes:)")

def is_vanilla(i):
    return i["itemId"] < 24000 and i["itemLevel"] <= 92 and i["requiredLevel"] <= 60

def level_ok(i):
    # Niveau 55+ requis, ou niveau d'objet 57+ (Hand of Justice, Savage Gladiator Chain… demandent 52-53).
    return i["requiredLevel"] >= 55 or i["itemLevel"] >= 57

# Boss -> zone, déduit des objets dont la source est renseignée (sert quand seule l'infobulle cite le boss).
BOSS_ZONE = {}
for _i in items:
    _s = _i.get("source") or {}
    if _s.get("name") and _s.get("zone") in zones and _i["itemId"] < 24000:
        BOSS_ZONE.setdefault(_s["name"], _s["zone"])

BOSS_ZONE.setdefault("Onyxia", next(z for z, v in zones.items() if v["name"] == "Onyxia's Lair"))

# Objets sans source dans la base, ajoutés à la main.
EXTRA = {
    "Sulfuras, Hand of Ragnaros": {"t": "raid", "zone": "Molten Core", "boss": "Ragnaros (légendaire, artisanat)"},
    "Quel'Serrar": {"t": "quest", "zone": "Quête", "boss": "Onyxia (quête Foror's Compendium)"},
}

def first_block(tooltip):
    """La base concatène parfois plusieurs versions d'un objet : on garde la première."""
    out, seen_name = [], False
    for t in tooltip[1:]:
        if t["label"] == tooltip[0]["label"] and seen_name:
            break
        if t["label"].startswith("Item Level"):
            if seen_name:
                break
            seen_name = True
        out.append(t)
    return out

def source_of(i):
    if i["name"] in EXTRA:
        return dict(EXTRA[i["name"]])
    if i["name"].startswith("Desecrated ") and 22349 <= i["itemId"] <= 22372:
        return {"t": "raid", "zone": "Naxxramas", "boss": "Boss divers (jeton T3)"}
    s = i.get("source") or {}
    if not s:
        by = next((t["label"][11:].strip() for t in i["tooltip"] if t["label"].startswith("Dropped by:")), None)
        if by and by in BOSS_ZONE:
            s = {"category": "Boss Drop", "name": by, "zone": BOSS_ZONE[by]}
    z = zones.get(s.get("zone"))
    if z and s.get("category") in ("Boss Drop", "Rare Drop", "Zone Drop"):
        if z["name"] in RAID_FR:
            return {"t": "raid", "zone": RAID_FR[z["name"]], "boss": s.get("name") or "Butin partagé / trash",
                    "drop": s.get("dropChance")}
        lvl = z.get("level") or [None, None]
        if z.get("category") == "Dungeon" and lvl[1] and 54 <= lvl[1] <= 60:
            return {"t": "dungeon", "zone": z["name"], "boss": s.get("name") or "Trash",
                    "drop": s.get("dropChance")}
        return None
    if s.get("category") == "Quest":
        q = s.get("quests") or []
        return {"t": "quest", "zone": "Quête", "boss": q[0]["name"] if q else "Quête"}
    for c in i.get("createdBy") or []:
        if (c.get("requiredSkill") or 0) <= 300 and c.get("category") in PROF_FR:
            return {"t": "craft", "zone": "Artisanat", "boss": PROF_FR[c["category"]], "skill": c.get("requiredSkill")}
    return None

SLOT_FR = {"Head": "Tête", "Neck": "Cou", "Shoulder": "Épaules", "Back": "Dos", "Chest": "Torse", "Wrist": "Poignets",
           "Hands": "Mains", "Waist": "Taille", "Legs": "Jambes", "Feet": "Pieds", "Finger": "Anneau", "Trinket": "Bijou",
           "One-Hand": "Une main", "Two-Hand": "Deux mains", "Main Hand": "Main droite", "Off Hand": "Main gauche",
           "Held In Off-hand": "Tenu en main gauche", "Ranged": "À distance", "Relic": "Relique", "Thrown": "Jet"}
TYPE_FR = {"Cloth": "Tissu", "Leather": "Cuir", "Mail": "Mailles", "Plate": "Plaques", "Sword": "Épée", "Mace": "Masse",
           "Dagger": "Dague", "Axe": "Hache", "Shield": "Bouclier", "Staff": "Bâton", "Wand": "Baguette", "Polearm": "Arme d'hast",
           "Gun": "Arme à feu", "Bow": "Arc", "Fist Weapon": "Arme de pugilat", "Crossbow": "Arbalète", "Libram": "Libram",
           "Totem": "Totem", "Idol": "Idole", "Thrown": "Arme de jet"}
ALL = ["war", "rog", "hun", "dru", "sha", "pal", "mag", "pri", "wlk"]
# Qui porte l'objet de façon « normale » au niveau 60 (armure de sa classe, armes utilisables en Classic).
ARMOR_USERS = {"Plate": ["war", "pal"], "Mail": ["hun", "sha"], "Leather": ["rog", "dru"], "Cloth": ["mag", "pri", "wlk"]}
WEAPON_USERS = {
    ("Dagger", 1): ["rog", "war", "hun", "sha", "dru", "mag", "pri", "wlk"],
    ("Sword", 1): ["war", "rog", "pal", "hun", "mag", "wlk"], ("Sword", 2): ["war", "pal", "hun"],
    ("Axe", 1): ["war", "pal", "hun", "sha"], ("Axe", 2): ["war", "pal", "hun", "sha"],
    ("Mace", 1): ["war", "rog", "pal", "sha", "dru", "pri"], ("Mace", 2): ["war", "pal", "sha", "dru"],
    ("Polearm", 2): ["war", "pal", "hun"], ("Staff", 2): ["war", "hun", "dru", "sha", "mag", "pri", "wlk"],
    ("Fist Weapon", 1): ["war", "rog", "hun", "sha", "dru"],
    ("Bow", 0): ["war", "rog", "hun"], ("Gun", 0): ["war", "rog", "hun"], ("Crossbow", 0): ["war", "rog", "hun"],
    ("Thrown", 0): ["war", "rog"], ("Wand", 0): ["mag", "pri", "wlk"], ("Shield", 1): ["war", "pal", "sha"],
    ("Libram", 0): ["pal"], ("Totem", 0): ["sha"], ("Idol", 0): ["dru"],
}

def users_of(i, token):
    if token:
        return ALL
    sub, slot = i.get("subclass"), i["slot"]
    if sub in ARMOR_USERS and slot not in ("Back",):
        return ARMOR_USERS[sub]
    hands = 2 if slot == "Two-Hand" else 0 if slot in ("Ranged", "Relic", "Thrown") else 1
    return WEAPON_USERS.get((sub, hands)) or WEAPON_USERS.get((sub, 1)) or ALL

# Rôles intéressés, déduits des caractéristiques de l'objet.
RX = {k: re.compile(v) for k, v in {
    "heal": r"healing done|healing spells|increases healing|mana per 5|mana every 5|restores \d+ mana",
    "spell": r"spell power|spell damage|damage (and healing )?done by|spell penetration|with spells",
    "int": r"intellect|spirit",
    "phys": r"strength|agility|(?<!increases )attack power|increases attack power by \d+\.|ranged attack power|weapon skill|axes|swords|daggers|maces|expertise|armor penetration",
    "crit": r"critical strike|hit rating|chance to hit",
    "tank": r"defense|dodge|parry|block",
}.items()}

def roles_of(stats, token, typ):
    """La base décrit les caractéristiques au format moderne (« hit rating », « spell power ») :
    touche et critique ne comptent comme physiques que sans aucune caractéristique de sort."""
    if token:
        return []
    t = " ".join(stats).lower()
    t = re.sub(r"increases attack power by \d+ in cat[^.]*\.", "", t)  # PA farouche des armes de druide
    r = set()
    caster_ish = RX["heal"].search(t) or RX["spell"].search(t) or RX["int"].search(t)
    if RX["heal"].search(t): r.add("heal")
    if RX["spell"].search(t) or RX["int"].search(t): r.update(["caster", "heal"])
    if RX["phys"].search(t) or (RX["crit"].search(t) and not caster_ish): r.update(["melee", "ranged"])
    if RX["tank"].search(t): r.add("tank")
    if typ == "Wand": r.update(["caster", "heal"])
    if not r and typ in ("Bow", "Gun", "Crossbow"): r.add("ranged")
    if not r and typ in ("Dagger", "Sword", "Axe", "Mace", "Fist Weapon", "Polearm", "Thrown"): r.update(["melee", "ranged"])
    return sorted(r)

out = []
for i in items:
    if not is_vanilla(i) or i["quality"] not in ("Rare", "Epic", "Legendary"):
        continue
    src = source_of(i)
    if not src:
        continue
    equippable = i["slot"] not in ("Non-equippable", "Bag", "Shirt", "Tabard", "Ammo")
    token = not equippable and src["t"] == "raid" and i["quality"] in ("Epic", "Legendary") and i["class"] in ("Quest", "Miscellaneous", "Reagent", "Trade Goods")
    if not (equippable or token):
        continue
    if equippable and not level_ok(i):
        continue
    tip = first_block(i["tooltip"])
    classes = []
    for t in tip:
        if t["label"].startswith("Classes:"):
            classes = [CLASS_KEYS[c.strip()] for c in t["label"][8:].split(",") if c.strip() in CLASS_KEYS]
    stats = [t["label"].strip() for t in tip if t["label"].strip() and not SKIP_LINES.match(t["label"])
             and not re.match(r"^\(\d\) Set", t["label"])][:14]
    usable = classes or users_of(i, token)
    out.append({
        "id": i["itemId"], "name": i["name"], "quality": i["quality"].lower(), "ilvl": i["itemLevel"],
        "req": i["requiredLevel"], "slot": "Jeton" if token else SLOT_FR.get(i["slot"], i["slot"]),
        "type": "" if token else TYPE_FR.get(i.get("subclass"), ""),
        "phase": i.get("contentPhase"), "restricted": bool(classes), "classes": usable,
        "roles": roles_of(stats, token, i.get("subclass")), "src": src, "stats": stats,
    })

out.sort(key=lambda x: ({"raid": 0, "dungeon": 1, "craft": 2, "quest": 3}[x["src"]["t"]],
                        RAID_ORDER.index(x["src"]["zone"]) if x["src"]["zone"] in RAID_ORDER else 99,
                        x["src"]["zone"], x["src"]["boss"], x["name"]))
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print(len(out), "objets ->", OUT, f"({OUT.stat().st_size // 1024} Ko)")
print(Counter(x["src"]["t"] for x in out))
print(Counter(x["src"]["zone"] for x in out if x["src"]["t"] in ("raid", "dungeon")))
