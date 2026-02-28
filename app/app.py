import streamlit as st
import json
import math
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ryndor: Character Maker",
    page_icon="🐉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_races():
    with open(DATA_DIR / "races.json") as f:
        return json.load(f)["races"]

@st.cache_data
def load_classes():
    with open(DATA_DIR / "classes.json") as f:
        classes = json.load(f)["classes"]
    try:
        with open(DATA_DIR / "srd_subclasses.json") as f:
            srd = json.load(f)
        for cls in classes:
            srd_subs = srd.get(cls["id"], [])
            if srd_subs:
                cls["subclasses"] = cls["subclasses"] + srd_subs
    except FileNotFoundError:
        pass
    return classes

@st.cache_data
def load_backgrounds():
    with open(DATA_DIR / "backgrounds.json") as f:
        return json.load(f)["backgrounds"]

@st.cache_data
def load_class_mechanics():
    with open(DATA_DIR / "class_mechanics.json") as f:
        return json.load(f)

@st.cache_data
def load_class_features():
    with open(DATA_DIR / "class_features.json") as f:
        return json.load(f)

RACES = load_races()
CLASSES = load_classes()
BACKGROUNDS = load_backgrounds()
CLASS_MECHANICS = load_class_mechanics()
CLASS_FEATURES = load_class_features()

# ── Spell slot tables (SRD constants) ─────────────────────────────────────────
# Index = level-1. Each inner list: [1st,2nd,3rd,4th,5th,6th,7th,8th,9th] slots.
FULL_CASTER_SLOTS = [
    [2,0,0,0,0,0,0,0,0],[3,0,0,0,0,0,0,0,0],[4,2,0,0,0,0,0,0,0],[4,3,0,0,0,0,0,0,0],
    [4,3,2,0,0,0,0,0,0],[4,3,3,0,0,0,0,0,0],[4,3,3,1,0,0,0,0,0],[4,3,3,2,0,0,0,0,0],
    [4,3,3,3,1,0,0,0,0],[4,3,3,3,2,0,0,0,0],[4,3,3,3,2,1,0,0,0],[4,3,3,3,2,1,0,0,0],
    [4,3,3,3,2,1,1,0,0],[4,3,3,3,2,1,1,0,0],[4,3,3,3,2,1,1,1,0],[4,3,3,3,2,1,1,1,0],
    [4,3,3,3,2,1,1,1,1],[4,3,3,3,3,1,1,1,1],[4,3,3,3,3,2,1,1,1],[4,3,3,3,3,2,2,1,1],
]
HALF_CASTER_SLOTS = [
    [0,0,0,0,0],[2,0,0,0,0],[3,0,0,0,0],[3,0,0,0,0],[4,2,0,0,0],
    [4,2,0,0,0],[4,3,0,0,0],[4,3,0,0,0],[4,3,2,0,0],[4,3,2,0,0],
    [4,3,3,0,0],[4,3,3,0,0],[4,3,3,1,0],[4,3,3,1,0],[4,3,3,2,0],
    [4,3,3,2,0],[4,3,3,3,1],[4,3,3,3,1],[4,3,3,3,2],[4,3,3,3,2],
]
# Warlock: [slot_count, slot_level]
PACT_SLOTS = [
    [1,1],[2,1],[2,2],[2,2],[2,3],[2,3],[2,4],[2,4],
    [2,5],[2,5],[3,5],[3,5],[3,5],[3,5],[3,5],[3,5],
    [4,5],[4,5],[4,5],[4,5],
]
ALL_SKILLS = [
    ("Acrobatics",    "DEX"), ("Animal Handling", "WIS"), ("Arcana",       "INT"),
    ("Athletics",     "STR"), ("Deception",       "CHA"), ("History",      "INT"),
    ("Insight",       "WIS"), ("Intimidation",    "CHA"), ("Investigation","INT"),
    ("Medicine",      "WIS"), ("Nature",          "INT"), ("Perception",   "WIS"),
    ("Performance",   "CHA"), ("Persuasion",      "CHA"), ("Religion",     "INT"),
    ("Sleight of Hand","DEX"),("Stealth",         "DEX"), ("Survival",     "WIS"),
]

# ── Languages ─────────────────────────────────────────────────────────────────
RYNDOR_LANGUAGES = ["Auran", "Drakarim", "Inglishmek", "Leoporin", "Sylvan"]
SRD_LANGUAGES = [
    "Common", "Dwarvish", "Elvish", "Giant", "Gnomish", "Goblin", "Halfling", "Orc",
    "Abyssal", "Celestial", "Deep Speech", "Draconic", "Infernal", "Primordial", "Undercommon",
]
ALL_LANGUAGES = sorted(set(RYNDOR_LANGUAGES + SRD_LANGUAGES))

# ── Optimal stat priority per class ───────────────────────────────────────────
# Order: highest priority stat first. Standard Array [15,14,13,12,10,8] assigned in this order.
CLASS_STAT_PRIORITY = {
    "barbarian": ["STR", "CON", "DEX", "WIS", "CHA", "INT"],
    "bard":      ["CHA", "DEX", "CON", "WIS", "INT", "STR"],
    "cleric":    ["WIS", "CON", "STR", "CHA", "INT", "DEX"],
    "druid":     ["WIS", "CON", "INT", "DEX", "CHA", "STR"],
    "fighter":   ["STR", "CON", "DEX", "WIS", "INT", "CHA"],
    "monk":      ["DEX", "WIS", "CON", "STR", "INT", "CHA"],
    "paladin":   ["STR", "CHA", "CON", "WIS", "DEX", "INT"],
    "ranger":    ["DEX", "WIS", "CON", "STR", "INT", "CHA"],
    "rogue":     ["DEX", "CON", "INT", "WIS", "CHA", "STR"],
    "sorcerer":  ["CHA", "CON", "DEX", "WIS", "INT", "STR"],
    "warlock":   ["CHA", "CON", "DEX", "WIS", "INT", "STR"],
    "wizard":    ["INT", "CON", "DEX", "WIS", "CHA", "STR"],
    "artificer": ["INT", "CON", "DEX", "WIS", "CHA", "STR"],
    "sevrinn":   ["CON", "DEX", "WIS", "STR", "INT", "CHA"],
}
STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

# ─────────────────────────────────────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────────────────────────────────────
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

/* ── Root Theme ── */
:root {
    --ink:       #1a0a00;
    --parchment: #f5ead0;
    --parch-mid: #ede0c0;
    --parch-dark:#d4c49a;
    --crimson:   #8b0000;
    --gold:      #c9a84c;
    --gold-light:#e8c870;
    --teal:      #2a5f5f;
    --teal-light:#3a7f7f;
    --shadow:    rgba(26,10,0,0.25);
}

/* ── Global resets ── */
html, body, [class*="css"] {
    font-family: 'Crimson Text', Georgia, serif;
    background-color: var(--ink) !important;
}
.stApp { background-color: #110800 !important; }
.block-container { padding-top: 1rem !important; max-width: 1100px; }

/* ── Headings ── */
h1, h2, h3, h4, .cinzel { font-family: 'Cinzel', serif !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #1a0a00; }
::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 3px; }

/* ── Step progress bar ── */
.step-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 1rem auto 2rem;
    max-width: 720px;
}
.step-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    cursor: default;
}
.step-circle {
    width: 40px; height: 40px;
    border-radius: 50%;
    border: 2px solid var(--parch-dark);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Cinzel', serif;
    font-size: 14px;
    font-weight: 700;
    color: var(--parch-dark);
    background: #1a0a00;
    transition: all .3s;
}
.step-circle.active {
    border-color: var(--gold);
    color: var(--gold);
    background: rgba(201,168,76,0.12);
    box-shadow: 0 0 12px rgba(201,168,76,0.4);
}
.step-circle.done {
    border-color: var(--teal);
    color: var(--teal-light);
    background: rgba(42,95,95,0.2);
}
.step-label {
    font-family: 'Cinzel', serif;
    font-size: 9px;
    letter-spacing: 0.08em;
    color: var(--parch-dark);
    text-align: center;
    opacity: 0.7;
}
.step-label.active { color: var(--gold); opacity: 1; }
.step-connector {
    width: 60px; height: 2px;
    background: var(--parch-dark);
    opacity: 0.3;
    margin-bottom: 20px;
}
.step-connector.done { background: var(--teal); opacity: 0.6; }

/* ── Page title ── */
.page-title {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
}
.page-title h1 {
    font-family: 'Cinzel', serif !important;
    font-size: 2.6rem;
    font-weight: 900;
    color: var(--gold);
    text-shadow: 0 2px 20px rgba(201,168,76,0.5), 0 0 40px rgba(201,168,76,0.2);
    letter-spacing: 0.12em;
    margin: 0;
}
.page-title p {
    font-family: 'Crimson Text', serif;
    font-style: italic;
    color: var(--parch-dark);
    font-size: 1.1rem;
    margin: 0.3rem 0 0;
    opacity: 0.8;
}

/* ── Card ── */
.card {
    background: linear-gradient(160deg, #2a1800 0%, #1e1000 60%, #160c00 100%);
    border: 1px solid rgba(201,168,76,0.3);
    border-radius: 4px;
    padding: 1.5rem;
    margin: 0.5rem 0;
    box-shadow: 0 4px 20px var(--shadow), inset 0 0 40px rgba(0,0,0,0.3);
    position: relative;
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
}

/* ── Selection card (clickable) ── */
.sel-card {
    background: linear-gradient(160deg, #2a1800 0%, #1e1000 100%);
    border: 1px solid rgba(201,168,76,0.2);
    border-radius: 4px;
    padding: 1rem 1.2rem;
    margin: 0.4rem 0;
    cursor: pointer;
    transition: all .25s;
}
.sel-card:hover {
    border-color: rgba(201,168,76,0.6);
    background: linear-gradient(160deg, #3a2000 0%, #2a1400 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(201,168,76,0.15);
}
.sel-card.selected {
    border-color: var(--gold);
    background: linear-gradient(160deg, #3d2500 0%, #2a1800 100%);
    box-shadow: 0 0 0 1px var(--gold), 0 4px 20px rgba(201,168,76,0.2);
}
.sel-card h3 {
    font-family: 'Cinzel', serif;
    color: var(--gold);
    font-size: 1.05rem;
    margin: 0 0 0.3rem;
}
.sel-card p {
    font-family: 'Crimson Text', serif;
    color: var(--parch-dark);
    font-size: 0.95rem;
    margin: 0;
    opacity: 0.85;
    line-height: 1.4;
}
.sel-card .icon { font-size: 1.8rem; margin-bottom: 0.3rem; }

/* ── Trait block ── */
.trait-block {
    background: rgba(0,0,0,0.3);
    border-left: 3px solid var(--gold);
    border-radius: 0 3px 3px 0;
    padding: 0.6rem 1rem;
    margin: 0.4rem 0;
}
.trait-block .name {
    font-family: 'Cinzel', serif;
    color: var(--gold-light);
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 0.2rem;
}
.trait-block .desc {
    font-family: 'Crimson Text', serif;
    color: var(--parch-dark);
    font-size: 0.95rem;
    line-height: 1.5;
    opacity: 0.9;
}

/* ── Ability score box ── */
.stat-box {
    background: linear-gradient(180deg, #2a1800 0%, #1a0e00 100%);
    border: 1px solid var(--gold);
    border-radius: 4px;
    text-align: center;
    padding: 0.8rem 0.4rem;
}
.stat-box .stat-name {
    font-family: 'Cinzel', serif;
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--gold);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.stat-box .stat-val {
    font-family: 'Cinzel', serif;
    font-size: 2.2rem;
    font-weight: 900;
    color: var(--parch);
    line-height: 1.1;
}
.stat-box .stat-mod {
    font-family: 'Cinzel', serif;
    font-size: 1rem;
    font-weight: 700;
    color: var(--gold-light);
    background: rgba(0,0,0,0.4);
    border-radius: 50%;
    width: 32px; height: 32px;
    display: flex; align-items: center; justify-content: center;
    margin: 0.3rem auto 0;
}

/* ── Section headers ── */
.section-header {
    font-family: 'Cinzel', serif;
    color: var(--gold);
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-bottom: 1px solid rgba(201,168,76,0.3);
    padding-bottom: 0.4rem;
    margin: 1.2rem 0 0.8rem;
}

/* ── Info badge ── */
.badge {
    display: inline-block;
    background: rgba(201,168,76,0.15);
    border: 1px solid rgba(201,168,76,0.4);
    border-radius: 2px;
    padding: 2px 8px;
    font-family: 'Cinzel', serif;
    font-size: 0.72rem;
    color: var(--gold-light);
    letter-spacing: 0.05em;
    margin: 2px;
}
.badge.teal {
    background: rgba(42,95,95,0.2);
    border-color: rgba(58,127,127,0.4);
    color: var(--teal-light);
}
.badge.crimson {
    background: rgba(139,0,0,0.15);
    border-color: rgba(180,0,0,0.3);
    color: #e05050;
}

/* ── Character sheet ── */
.sheet-header {
    background: linear-gradient(180deg, #3d2000 0%, #1e0f00 100%);
    border: 2px solid var(--gold);
    border-radius: 6px 6px 0 0;
    padding: 2rem;
    text-align: center;
    position: relative;
}
.sheet-header .char-name {
    font-family: 'Cinzel', serif;
    font-size: 2.8rem;
    font-weight: 900;
    color: var(--gold);
    text-shadow: 0 2px 15px rgba(201,168,76,0.5);
    letter-spacing: 0.1em;
}
.sheet-header .char-sub {
    font-family: 'Crimson Text', serif;
    font-style: italic;
    color: var(--parch-dark);
    font-size: 1.2rem;
    margin-top: 0.3rem;
}
.sheet-divider {
    border: none;
    border-top: 1px solid rgba(201,168,76,0.3);
    margin: 1rem 0;
}
.sheet-section {
    background: linear-gradient(160deg, #2a1800 0%, #1a0e00 100%);
    border: 1px solid rgba(201,168,76,0.25);
    border-radius: 4px;
    padding: 1.2rem 1.5rem;
    margin: 0.6rem 0;
}
.sheet-section-title {
    font-family: 'Cinzel', serif;
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--gold);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
    border-bottom: 1px solid rgba(201,168,76,0.2);
    padding-bottom: 0.4rem;
}
.feat-row {
    display: flex;
    gap: 0.5rem;
    align-items: baseline;
    margin: 0.4rem 0;
}
.feat-row .fname {
    font-family: 'Cinzel', serif;
    color: var(--gold-light);
    font-size: 0.9rem;
    font-weight: 600;
    min-width: 180px;
}
.feat-row .fdesc {
    font-family: 'Crimson Text', serif;
    color: var(--parch-dark);
    font-size: 0.95rem;
    line-height: 1.5;
    flex: 1;
    opacity: 0.88;
}

/* ── Navigation buttons ── */
.stButton > button {
    font-family: 'Cinzel', serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    border-radius: 2px !important;
    transition: all .25s !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8b0000, #5c0000) !important;
    border: 1px solid var(--crimson) !important;
    color: var(--parch) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stNumberInput > div > div > input {
    background: #2a1800 !important;
    border: 1px solid rgba(201,168,76,0.35) !important;
    color: var(--parch) !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1rem !important;
}
.stTextInput label, .stSelectbox label, .stNumberInput label {
    font-family: 'Cinzel', serif !important;
    font-size: 0.78rem !important;
    color: var(--gold) !important;
    letter-spacing: 0.08em !important;
}
.stRadio label { color: var(--parch-dark) !important; }
.stRadio > div { gap: 0.5rem !important; }

/* ── Expander ── */
details {
    background: rgba(0,0,0,0.2) !important;
    border: 1px solid rgba(201,168,76,0.2) !important;
    border-radius: 3px !important;
}
summary {
    font-family: 'Cinzel', serif !important;
    color: var(--gold-light) !important;
    font-size: 0.88rem !important;
    padding: 0.5rem !important;
}

/* ── Alert ── */
.ryndor-alert {
    background: rgba(139,0,0,0.15);
    border: 1px solid rgba(180,0,0,0.3);
    border-radius: 3px;
    padding: 0.8rem 1rem;
    font-family: 'Crimson Text', serif;
    color: #e05050;
    font-size: 0.95rem;
    margin: 0.5rem 0;
}

/* ── Weirding surge table ── */
.surge-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Crimson Text', serif;
}
.surge-table th {
    font-family: 'Cinzel', serif;
    font-size: 0.75rem;
    color: var(--gold);
    letter-spacing: 0.08em;
    text-align: left;
    border-bottom: 1px solid rgba(201,168,76,0.3);
    padding: 0.4rem 0.6rem;
}
.surge-table td {
    padding: 0.4rem 0.6rem;
    color: var(--parch-dark);
    font-size: 0.95rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.surge-table td:first-child {
    font-family: 'Cinzel', serif;
    color: var(--gold-light);
    font-weight: 700;
    width: 40px;
}

/* ── Print styles ── */
@media print {
    .no-print { display: none !important; }
    .stApp, html, body { background: white !important; }
    .sheet-header { background: #f0e8d0 !important; }
    .sheet-section { background: #faf6ee !important; border-color: #c8a84c !important; }
    * { color: black !important; }
    .char-name { color: #8b0000 !important; }
    .fname { color: #5c3a00 !important; }
}
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    "step": 1,
    "char_name": "",
    "player_name": "",
    "char_level": 1,
    "race_id": None,
    "class_id": None,
    "subclass_id": None,
    "background_id": None,
    "alignment": "",
    "stats": {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8},
    "stat_method": "Standard Array",
    "chosen_skills": [],
    "equip_choices": {},   # {choice_id: option_index}
    "class_options": {},   # {choice_key: selected_id or [selected_ids]}
    "expertise_skills": [],
    "chosen_languages": [],
    "notes": "",
    "personality": "",
    "ideals": "",
    "bonds": "",
    "flaws": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_race(id_):
    return next((r for r in RACES if r["id"] == id_), None)

def get_class(id_):
    return next((c for c in CLASSES if c["id"] == id_), None)

def get_background(id_):
    return next((b for b in BACKGROUNDS if b["id"] == id_), None)

def get_subclass(cls, sub_id):
    if not cls or not sub_id:
        return None
    return next((s for s in cls.get("subclasses", []) if s["id"] == sub_id), None)

def modifier(score):
    mod = math.floor((score - 10) / 2)
    return f"+{mod}" if mod >= 0 else str(mod)

def modifier_int(score):
    return math.floor((score - 10) / 2)

def proficiency_bonus(level):
    return 2 + math.floor((level - 1) / 4)

def effective_stat(stat_key, race):
    base = st.session_state.stats[stat_key]
    asi = race.get("ability_scores", {}) if race else {}
    name_map = {"STR": "Strength", "DEX": "Dexterity", "CON": "Constitution",
                "INT": "Intelligence", "WIS": "Wisdom", "CHA": "Charisma"}
    bonus = asi.get(name_map[stat_key], 0) if isinstance(asi.get(name_map[stat_key], 0), int) else 0
    return base + bonus

STAT_KEY_MAP = {"DEX":"DEX","STR":"STR","CON":"CON","INT":"INT","WIS":"WIS","CHA":"CHA"}
ABILITY_SHORT = {"DEX":"Dex","STR":"Str","CON":"Con","INT":"Int","WIS":"Wis","CHA":"Cha"}

def skill_modifier(skill_name, ability_key, race, prof_bonus, proficient_skills):
    score = effective_stat(ability_key, race)
    mod = modifier_int(score)
    if skill_name in proficient_skills:
        mod += prof_bonus
    return mod

def get_all_proficient_skills(race, bg, chosen_skills):
    """Return full set of proficient skill names from race + background + chosen class skills."""
    proficient = set(chosen_skills)
    if race:
        proficient.update(race.get("bonus_skills", []))
    if bg:
        proficient.update(bg.get("skill_proficiencies", []))
    return proficient

def get_mech(class_id):
    return CLASS_MECHANICS.get(class_id, {})

def compute_ac(class_id, race, equip_choices):
    """Compute base AC from chosen equipment. Returns (ac_value, note_string)."""
    mech = get_mech(class_id)
    dex_mod = modifier_int(effective_stat("DEX", race))
    con_mod = modifier_int(effective_stat("CON", race))
    wis_mod = modifier_int(effective_stat("WIS", race))
    shield_bonus = 0
    armor_ac = None
    armor_type = None

    # Check equipment choices for armor
    for choice in mech.get("equipment_choices", []):
        cid = choice["id"]
        idx = equip_choices.get(cid, 0)
        if idx < len(choice["options"]):
            opt = choice["options"][idx]
            if opt.get("ac_base") is not None:
                armor_ac = opt["ac_base"]
                armor_type = opt["ac_type"]
            if opt.get("shield"):
                shield_bonus = 2

    # If no armor chosen from choices, check default_ac
    if armor_ac is None and "default_ac" in mech:
        armor_ac = mech["default_ac"]["ac_base"]
        armor_type = mech["default_ac"]["ac_type"]

    # Special unarmored calculations
    special = mech.get("special_ac")
    if armor_ac is None:
        if special == "barbarian":
            return 10 + dex_mod + con_mod + shield_bonus, f"Unarmored Defense (10+DEX+CON)"
        elif special == "monk":
            return 10 + dex_mod + wis_mod, "Unarmored Defense (10+DEX+WIS)"
        else:
            return 10 + dex_mod + shield_bonus, "Unarmored"

    if armor_type == "fixed":
        return armor_ac + shield_bonus, "Heavy armor"
    elif armor_type == "medium":
        return armor_ac + min(dex_mod, 2) + shield_bonus, "Medium armor"
    else:  # light or unarmored
        return armor_ac + dex_mod + shield_bonus, "Light armor"

def get_spell_slots(slot_type, level):
    """Return list of (slot_level_str, count) for display, filtering zeros."""
    idx = min(level - 1, 19)
    if slot_type == "full":
        slots = FULL_CASTER_SLOTS[idx]
        return [(f"{i+1}{'st' if i==0 else 'nd' if i==1 else 'rd' if i==2 else 'th'}", n)
                for i, n in enumerate(slots) if n > 0]
    elif slot_type == "half":
        slots = HALF_CASTER_SLOTS[idx]
        return [(f"{i+1}{'st' if i==0 else 'nd' if i==1 else 'rd' if i==2 else 'th'}", n)
                for i, n in enumerate(slots) if n > 0]
    elif slot_type == "pact":
        count, slvl = PACT_SLOTS[idx]
        suffix = "st" if slvl==1 else "nd" if slvl==2 else "rd" if slvl==3 else "th"
        return [(f"{slvl}{suffix} (Pact)", count)]
    return []

def get_spells_known_or_prepared(sc, level, race):
    """Return (int_or_formula_str, label) for display."""
    if sc is None:
        return None, None
    idx = min(level - 1, 19)
    spells_known = sc.get("spells_known")
    formula = sc.get("prepare_formula")
    ability = sc.get("ability", "")
    key_map = {"Wisdom":"WIS","Intelligence":"INT","Charisma":"CHA",
               "Strength":"STR","Dexterity":"DEX","Constitution":"CON"}
    if spells_known is not None:
        count = spells_known[idx]
        return count, "Spells Known"
    elif formula:
        race_ = get_race(st.session_state.race_id)
        akey = key_map.get(ability, "WIS")
        mod = modifier_int(effective_stat(akey, race_))
        if "half_level" in formula:
            val = max(1, mod + math.floor(level / 2))
        else:
            val = max(1, mod + level)
        return val, "Max Prepared"
    return None, None

# ─────────────────────────────────────────────────────────────────────────────
# STEP BAR
# ─────────────────────────────────────────────────────────────────────────────
STEPS = ["Basics", "Race", "Class", "Features", "Background", "Stats", "Skills", "Gear", "Sheet"]

def render_step_bar():
    current = st.session_state.step
    html = '<div class="step-bar">'
    for i, label in enumerate(STEPS, 1):
        if i == current:
            css = "active"
        elif i < current:
            css = "done"
        else:
            css = ""
        html += f'<div class="step-node"><div class="step-circle {css}">{i}</div><div class="step-label {css}">{label}</div></div>'
        if i < len(STEPS):
            conn_css = "done" if i < current else ""
            html += f'<div class="step-connector {conn_css}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-title">
  <h1>🐉 Ryndor: The Weirded Lands</h1>
  <p>Choose Your Fate — Character Sheet Builder</p>
</div>
""", unsafe_allow_html=True)

render_step_bar()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — BASICS
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.step == 1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">⚔️ Character Basics</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-family: Crimson Text, serif; color: #c8aa70; font-style: italic; margin-bottom:1.5rem;">In a world as vast and diverse as Ryndor, every face tells a story and every soul carries the essence of something greater. What story will yours tell?</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.session_state.char_name = st.text_input("Character Name", st.session_state.char_name, placeholder="e.g. Isera Wyrgleam")
    with col2:
        st.session_state.player_name = st.text_input("Player Name", st.session_state.player_name, placeholder="Your name")
    with col3:
        st.session_state.char_level = st.number_input("Level", min_value=1, max_value=20, value=st.session_state.char_level)

    alignments = [
        "Lawful Good", "Neutral Good", "Chaotic Good",
        "Lawful Neutral", "True Neutral", "Chaotic Neutral",
        "Lawful Evil", "Neutral Evil", "Chaotic Evil"
    ]
    st.session_state.alignment = st.selectbox(
        "Alignment",
        alignments,
        index=alignments.index(st.session_state.alignment) if st.session_state.alignment in alignments else 4
    )
    st.markdown('</div>', unsafe_allow_html=True)

    _, right = st.columns([6, 1])
    with right:
        if st.button("Next →", type="primary", use_container_width=True):
            if not st.session_state.char_name.strip():
                st.error("Please enter a character name.")
            else:
                st.session_state.step = 2
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — RACE
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == 2:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🌍 Choose Your Race</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-family: Crimson Text, serif; color: #c8aa70; font-style: italic; margin-bottom:1rem;">The people of Ryndor are as varied as the lands they tread.</p>', unsafe_allow_html=True)

        for race in RACES:
            selected = st.session_state.race_id == race["id"]
            sel_cls = "selected" if selected else ""
            st.markdown(
                f'<div class="sel-card {sel_cls}" id="race-{race["id"]}">'
                f'<div class="icon">{race["icon"]}</div>'
                f'<h3>{race["name"]}</h3>'
                f'<p>{race["description"][:110]}…</p>'
                f'</div>',
                unsafe_allow_html=True
            )
            if st.button(f"Select {race['name']}", key=f"race_{race['id']}", use_container_width=True):
                st.session_state.race_id = race["id"]
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        race = get_race(st.session_state.race_id)
        if race:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center; font-size:3rem; margin-bottom:0.5rem">{race["icon"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="font-family:Cinzel,serif; color:#c9a84c; text-align:center; font-size:1.6rem; margin:0 0 0.3rem">{race["name"]}</h2>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-family:Crimson Text,serif; font-style:italic; color:#a08060; text-align:center; margin:0 0 1rem">{race.get("flavor","")}</p>', unsafe_allow_html=True)

            # ASI
            asi = race.get("ability_scores", {})
            if isinstance(asi, dict):
                note = asi.get("note", "")
                badges = " ".join([
                    f'<span class="badge">+{v} {k}</span>'
                    for k, v in asi.items() if k != "note" and isinstance(v, int)
                ])
                if note:
                    badges += f' <span class="badge crimson">{note}</span>'
                st.markdown(f'<div style="margin:0.5rem 0">{badges}</div>', unsafe_allow_html=True)

            # Speed
            spd = race.get("speed", {})
            speed_parts = []
            if spd.get("walk"):
                speed_parts.append(f'<span class="badge">🚶 {spd["walk"]} ft</span>')
            if spd.get("fly"):
                speed_parts.append(f'<span class="badge teal">🦅 {spd["fly"]} ft fly</span>')
            if spd.get("note"):
                speed_parts.append(f'<span class="badge crimson" style="font-size:0.65rem">{spd["note"]}</span>')
            st.markdown(f'<div style="margin:0.3rem 0">{"".join(speed_parts)}</div>', unsafe_allow_html=True)

            # Languages
            langs = " ".join([f'<span class="badge teal">🗣 {l}</span>' for l in race.get("languages", [])])
            st.markdown(f'<div style="margin:0.3rem 0">{langs}</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header" style="margin-top:1rem">Racial Traits</div>', unsafe_allow_html=True)
            for trait in race.get("traits", []):
                st.markdown(
                    f'<div class="trait-block"><div class="name">{trait["name"]}</div>'
                    f'<div class="desc">{trait["description"]}</div></div>',
                    unsafe_allow_html=True
                )

            # Age/Size/Alignment
            st.markdown(f'<p style="font-family:Crimson Text,serif; color:#907050; font-size:0.88rem; margin-top:0.8rem"><b style="color:#c9a84c">Age:</b> {race.get("age","")} &nbsp;|&nbsp; <b style="color:#c9a84c">Size:</b> {race.get("size","")} &nbsp;|&nbsp; <b style="color:#c9a84c">Alignment:</b> {race.get("alignment","")}</p>', unsafe_allow_html=True)

            # Suggested classes
            sc = ", ".join(race.get("suggested_classes", []))
            st.markdown(f'<p style="font-family:Crimson Text,serif; color:#907050; font-size:0.88rem"><b style="color:#c9a84c">Suggested Classes:</b> {sc}</p>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><p style="font-family:Crimson Text,serif; color:#907050; font-style:italic; text-align:center; padding:2rem">← Select a race to see its details</p></div>', unsafe_allow_html=True)

    col1, _, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            if not st.session_state.race_id:
                st.error("Please select a race.")
            else:
                st.session_state.step = 3
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — CLASS
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == 3:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">⚔️ Choose Your Class</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-family: Crimson Text, serif; color: #c8aa70; font-style: italic; margin-bottom:1rem;">Every adventurous road in Ryndor has its calling.</p>', unsafe_allow_html=True)

        for cls in CLASSES:
            selected = st.session_state.class_id == cls["id"]
            sel_cls_css = "selected" if selected else ""
            subs = cls.get("subclasses", [])
            sub_names = " · ".join(s["name"] for s in subs)
            st.markdown(
                f'<div class="sel-card {sel_cls_css}">'
                f'<div style="display:flex; align-items:center; gap:0.7rem">'
                f'<span style="font-size:1.5rem">{cls["icon"]}</span>'
                f'<div><h3 style="margin:0">{cls["name"]}</h3>'
                f'<p style="margin:0; font-size:0.82rem; color:#7a6040">{sub_names}</p></div></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if st.button(f"Select {cls['name']}", key=f"cls_{cls['id']}", use_container_width=True):
                if st.session_state.class_id != cls["id"]:
                    st.session_state.class_id = cls["id"]
                    st.session_state.subclass_id = None
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        cls = get_class(st.session_state.class_id)
        if cls:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center; font-size:2.5rem; margin-bottom:0.3rem">{cls["icon"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="font-family:Cinzel,serif; color:#c9a84c; text-align:center; margin:0 0 0.5rem">{cls["name"]}</h2>', unsafe_allow_html=True)

            # Core stats
            hit = f'<span class="badge">❤️ Hit Die: {cls["hit_die"]}</span>'
            primary = f'<span class="badge teal">✨ {cls["primary_ability"]}</span>'
            saves = " ".join([f'<span class="badge crimson">🛡 {s}</span>' for s in cls["saves"]])
            st.markdown(f'<div style="text-align:center; margin-bottom:0.5rem">{hit} {primary} {saves}</div>', unsafe_allow_html=True)

            st.markdown(f'<p style="font-family:Crimson Text,serif; font-style:italic; color:#a08060; margin:0.5rem 0">{cls["flavor"]}</p>', unsafe_allow_html=True)

            # Skills
            st.markdown(f'<p style="font-family:Crimson Text,serif; color:#907050; font-size:0.88rem"><b style="color:#c9a84c">Skills:</b> {cls["skills"]}</p>', unsafe_allow_html=True)

            # Special note for Sev'rinn
            if cls["id"] == "sevrinn":
                st.markdown(f'<div class="ryndor-alert">⚠️ {cls["special_note"]}</div>', unsafe_allow_html=True)

            # Subclass selection
            st.markdown('<div class="section-header">Ryndor Subclass</div>', unsafe_allow_html=True)
            subs = cls.get("subclasses", [])
            for sub in subs:
                selected = st.session_state.subclass_id == sub["id"]
                sel_css = "selected" if selected else ""
                st.markdown(
                    f'<div class="sel-card {sel_css}">'
                    f'<h3 style="margin:0 0 0.3rem">{sub["name"]}</h3>'
                    f'<p style="margin:0">{sub["description"]}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if st.button(f"Choose {sub['name']}", key=f"sub_{sub['id']}", use_container_width=True):
                    st.session_state.subclass_id = sub["id"]
                    st.rerun()

            # Feature preview for selected subclass
            sub = get_subclass(cls, st.session_state.subclass_id)
            if sub:
                level = st.session_state.char_level
                st.markdown('<div class="section-header" style="margin-top:1rem">Subclass Features</div>', unsafe_allow_html=True)

                # Patron list for Warlock
                if "patrons" in sub:
                    st.markdown('<p style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.85rem; margin-bottom:0.3rem">Available Rift Patrons:</p>', unsafe_allow_html=True)
                    for patron in sub["patrons"]:
                        st.markdown(
                            f'<div class="trait-block"><div class="name">{patron["name"]}</div>'
                            f'<div class="desc">{patron["description"]}</div></div>',
                            unsafe_allow_html=True
                        )

                # Oath spells or domain spells
                for spell_key in ["domain_spells", "oath_spells", "circle_spells"]:
                    if spell_key in sub:
                        with st.expander("📜 Subclass Spells"):
                            for lvl, spells in sub[spell_key].items():
                                spell_list = ", ".join(spells)
                                st.markdown(f'<p style="font-family:Crimson Text,serif; color:#c8aa70; margin:0.2rem 0"><b style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.8rem">{lvl}:</b> {spell_list}</p>', unsafe_allow_html=True)

                # Features up to current level
                features = sub.get("features", [])
                available = [f for f in features if f["level"] <= level]
                future = [f for f in features if f["level"] > level]

                if available:
                    for feat in available:
                        st.markdown(
                            f'<div class="trait-block">'
                            f'<div class="name">{feat["name"]} <span style="color:#7a6040; font-size:0.78rem">(Level {feat["level"]})</span></div>'
                            f'<div class="desc">{feat["description"]}</div></div>',
                            unsafe_allow_html=True
                        )
                if future:
                    st.markdown(f'<p style="font-family:Cinzel,serif; color:#7a6040; font-size:0.78rem; margin-top:0.5rem">+{len(future)} more features at higher levels</p>', unsafe_allow_html=True)

                # Sev'rinn special: show shift table and techniques
                if cls["id"] == "sevrinn" and "shift_table" in sub:
                    with st.expander("🌀 Elemental Shift Table"):
                        st.markdown('<table class="surge-table"><tr><th>d6</th><th>Effect</th><th>Description</th></tr>', unsafe_allow_html=True)
                        for entry in sub["shift_table"]:
                            st.markdown(f'<tr><td>{entry["roll"]}</td><td style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.85rem">{entry["name"]}</td><td>{entry["effect"]}</td></tr>', unsafe_allow_html=True)
                        st.markdown('</table>', unsafe_allow_html=True)

                    techs = sub.get("techniques", [])
                    avail_techs = [t for t in techs if t["level"] <= level]
                    if avail_techs:
                        with st.expander(f"⚗️ Combat Techniques ({len(avail_techs)} available)"):
                            for tech in avail_techs:
                                st.markdown(
                                    f'<div class="trait-block">'
                                    f'<div class="name">{tech["name"]} <span style="color:#7a6040; font-size:0.78rem">(Lv {tech["level"]})</span></div>'
                                    f'<div class="desc">{tech["description"]}</div></div>',
                                    unsafe_allow_html=True
                                )

                    # Level table
                    if "mechanics" in cls:
                        with st.expander("📊 Sev'rinn Level Table"):
                            st.markdown('<table class="surge-table"><tr><th>Level</th><th>Charges</th><th>Techniques</th><th>Surge DC</th></tr>', unsafe_allow_html=True)
                            for row in cls["mechanics"]["level_table"]:
                                hl = "color:#c9a84c; font-weight:bold" if row["level"] == level else ""
                                st.markdown(f'<tr><td style="{hl}">{row["level"]}</td><td>{row["charges"]}</td><td>{row["techniques"]}</td><td>{row["surge_dc"]}</td></tr>', unsafe_allow_html=True)
                            st.markdown('</table>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><p style="font-family:Crimson Text,serif; color:#907050; font-style:italic; text-align:center; padding:2rem">← Select a class to see its details</p></div>', unsafe_allow_html=True)

    col1, _, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            if not st.session_state.class_id:
                st.error("Please select a class.")
            elif not st.session_state.subclass_id:
                st.error("Please select a subclass.")
            else:
                st.session_state.step = 4
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — CLASS FEATURES & CHOICES
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == 4:
    cls   = get_class(st.session_state.class_id)
    level = st.session_state.char_level

    cf_data  = CLASS_FEATURES.get(st.session_state.class_id or "", {})
    features = cf_data.get("features", [])
    choices  = cf_data.get("choices", [])

    # Filter to current level
    avail_feats   = [f for f in features if f["level"] <= level]
    avail_choices = [c for c in choices  if c["level"] <= level]

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-header">⚡ Class Features — {cls["name"] if cls else ""}</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="font-family:Crimson Text,serif; color:#c8aa70; font-style:italic; margin-bottom:1rem">'
        'Review your class features and make any required choices for your level.</p>',
        unsafe_allow_html=True
    )

    # ── Interactive choices ──
    if avail_choices:
        st.markdown('<div class="section-header" style="margin-top:0">Required Choices</div>', unsafe_allow_html=True)
        class_opts = dict(st.session_state.class_options)

        for choice in avail_choices:
            key       = choice["key"]
            pick      = choice["pick"]
            ctype     = choice["type"]
            options   = choice.get("options", [])
            level_req = choice["level"]

            st.markdown(
                f'<div style="margin:1.2rem 0 0.4rem">'
                f'<span style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.95rem; font-weight:700">'
                f'{choice["name"]}</span>'
                f'<span style="font-family:Cinzel,serif; color:#7a6040; font-size:0.75rem; margin-left:0.5rem">'
                f'(Level {level_req})</span></div>'
                f'<p style="font-family:Crimson Text,serif; color:#a08060; font-size:0.92rem; margin:0 0 0.6rem">'
                f'{choice["description"]}</p>',
                unsafe_allow_html=True
            )

            current_val = class_opts.get(key)

            if ctype == "single_choice":
                opt_labels = [o["name"] for o in options]
                opt_descs  = {o["name"]: o["description"] for o in options}
                opt_ids    = {o["name"]: o["id"] for o in options}
                try:
                    cur_idx = next(
                        (i for i, o in enumerate(options) if o["id"] == current_val), 0
                    )
                except Exception:
                    cur_idx = 0
                sel = st.radio(
                    choice["name"],
                    opt_labels,
                    index=cur_idx,
                    key=f"cf_{key}",
                    label_visibility="collapsed"
                )
                class_opts[key] = opt_ids[sel]
                st.markdown(
                    f'<p style="font-family:Crimson Text,serif; color:#c8aa70; font-size:0.88rem; '
                    f'font-style:italic; margin:0.2rem 0 0; padding-left:0.5rem">'
                    f'{opt_descs[sel]}</p>',
                    unsafe_allow_html=True
                )

            elif ctype == "multi_choice":
                selected_ids = current_val if isinstance(current_val, list) else []
                new_selected = list(selected_ids)
                for opt in options:
                    is_checked = opt["id"] in new_selected
                    at_limit   = len(new_selected) >= pick and not is_checked
                    label_text = opt["name"] + (f" — *{opt['description']}*" if not at_limit else f" — {opt['description']}")
                    if at_limit and not is_checked:
                        label_text = opt["name"] + " *(limit reached)*"
                    checked = st.checkbox(
                        f"**{opt['name']}** — {opt['description']}",
                        value=is_checked,
                        disabled=at_limit,
                        key=f"cf_{key}_{opt['id']}"
                    )
                    if checked and opt["id"] not in new_selected:
                        new_selected.append(opt["id"])
                    elif not checked and opt["id"] in new_selected:
                        new_selected.remove(opt["id"])
                class_opts[key] = new_selected[:pick]
                st.markdown(
                    f'<p style="font-family:Cinzel,serif; color:#{"c9a84c" if len(new_selected)==pick else "e04040"}; '
                    f'font-size:0.78rem; margin-top:0.3rem">'
                    f'Selected: {len(new_selected)}/{pick}</p>',
                    unsafe_allow_html=True
                )

        st.session_state.class_options = class_opts

    elif not avail_feats:
        st.markdown(
            '<p style="font-family:Crimson Text,serif; color:#907050; font-style:italic">'
            'No class features or choices available yet — check back as you level up!</p>',
            unsafe_allow_html=True
        )

    # ── Automatic features ──
    if avail_feats:
        st.markdown(
            f'<div class="section-header" style="margin-top:1.2rem">'
            f'Features at Level {level}</div>',
            unsafe_allow_html=True
        )
        for feat in avail_feats:
            st.markdown(
                f'<div class="trait-block">'
                f'<div class="name">{feat["name"]} '
                f'<span style="color:#7a6040; font-size:0.75rem">(Level {feat["level"]})</span></div>'
                f'<div class="desc">{feat["description"]}</div></div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

    col1, _, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True, key="feat_back"):
            st.session_state.step = 3
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True, key="feat_next"):
            # Validate all required choices are made
            all_ok = True
            for choice in avail_choices:
                val = st.session_state.class_options.get(choice["key"])
                if val is None:
                    all_ok = False
                elif isinstance(val, list) and len(val) < choice["pick"]:
                    all_ok = False
            if not all_ok:
                st.error("Please complete all required class choices before continuing.")
            else:
                st.session_state.step = 5
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — BACKGROUND
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == 5:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📜 Choose Your Background</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-family: Crimson Text, serif; color: #c8aa70; font-style: italic; margin-bottom:1rem;">Where did your story begin?</p>', unsafe_allow_html=True)

        for bg in BACKGROUNDS:
            selected = st.session_state.background_id == bg["id"]
            sel_cls = "selected" if selected else ""
            st.markdown(
                f'<div class="sel-card {sel_cls}">'
                f'<div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.3rem">'
                f'<span style="font-size:1.4rem">{bg["icon"]}</span>'
                f'<h3 style="margin:0">{bg["name"]}</h3></div>'
                f'<p style="margin:0">{bg["description"][:100]}…</p>'
                f'</div>',
                unsafe_allow_html=True
            )
            if st.button(f"Select {bg['name']}", key=f"bg_{bg['id']}", use_container_width=True):
                st.session_state.background_id = bg["id"]
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        bg = get_background(st.session_state.background_id)
        if bg:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:center; font-size:2.5rem; margin-bottom:0.3rem">{bg["icon"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="font-family:Cinzel,serif; color:#c9a84c; text-align:center; margin:0 0 0.5rem">{bg["name"]}</h2>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-family:Crimson Text,serif; font-style:italic; color:#a08060">{bg["description"]}</p>', unsafe_allow_html=True)

            # Skills
            st.markdown('<div class="section-header">Proficiencies</div>', unsafe_allow_html=True)
            skills = " ".join([f'<span class="badge">🎲 {s}</span>' for s in bg.get("skill_proficiencies", [])])
            tools = " ".join([f'<span class="badge teal">🔧 {t}</span>' for t in bg.get("tool_proficiencies", [])])
            langs = " ".join([f'<span class="badge">🗣 {l}</span>' for l in bg.get("languages", [])])
            st.markdown(f'<div style="margin-bottom:0.5rem">{skills} {tools} {langs}</div>', unsafe_allow_html=True)

            # Equipment
            st.markdown('<div class="section-header">Starting Equipment</div>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-family:Crimson Text,serif; color:#c8aa70; font-size:0.95rem">{bg["equipment"]}</p>', unsafe_allow_html=True)

            # Feature
            feat = bg.get("feature", {})
            st.markdown('<div class="section-header">Background Feature</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="trait-block"><div class="name">{feat["name"]}</div>'
                f'<div class="desc">{feat["description"]}</div></div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><p style="font-family:Crimson Text,serif; color:#907050; font-style:italic; text-align:center; padding:2rem">← Select a background to see its details</p></div>', unsafe_allow_html=True)

    col1, _, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 4
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            if not st.session_state.background_id:
                st.error("Please select a background.")
            else:
                st.session_state.step = 6
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — ABILITY SCORES
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == 6:
    race = get_race(st.session_state.race_id)

    cls_stats = get_class(st.session_state.class_id)
    priority = CLASS_STAT_PRIORITY.get(st.session_state.class_id or "", [])
    STAT_KEYS = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    STAT_FULL = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
    STAT_LONG = {"STR":"Strength","DEX":"Dexterity","CON":"Constitution",
                 "INT":"Intelligence","WIS":"Wisdom","CHA":"Charisma"}

    # ── Optimize button: assign Standard Array in class priority order ──
    if priority and cls_stats:
        # Show priority order as badge strip
        priority_html = " → ".join(
            f'<span class="badge" style="font-size:0.8rem;padding:3px 8px">'
            f'{"★ " if i == 0 else ""}{k}</span>'
            for i, k in enumerate(priority)
        )
        opt_col1, opt_col2 = st.columns([3, 1])
        with opt_col1:
            st.markdown(
                f'<div style="margin-bottom:0.6rem">'
                f'<span style="font-family:Cinzel,serif;color:#c9a84c;font-size:0.78rem;'
                f'letter-spacing:0.08em">OPTIMAL FOR {cls_stats["name"].upper()}: </span>'
                f'{priority_html}</div>',
                unsafe_allow_html=True
            )
        with opt_col2:
            if st.button(f"⚡ Auto-Arrange", use_container_width=True, help=f"Assign Standard Array values in optimal order for {cls_stats['name']}"):
                for stat_key, value in zip(priority, STANDARD_ARRAY):
                    st.session_state.stats[stat_key] = value
                st.rerun()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎲 Ability Scores</div>', unsafe_allow_html=True)

    method = st.radio(
        "Score Method",
        ["Standard Array", "Point Buy", "Manual Entry"],
        index=["Standard Array", "Point Buy", "Manual Entry"].index(st.session_state.stat_method),
        horizontal=True
    )
    st.session_state.stat_method = method

    if method == "Standard Array":
        st.markdown(
            f'<p style="font-family:Crimson Text,serif; color:#c8aa70; margin-bottom:0.8rem">'
            f'Assign these values to your abilities: <b>{" · ".join(str(x) for x in STANDARD_ARRAY)}</b>'
            f'{"  —  click ⚡ Auto-Arrange to apply the optimal order for your class." if priority else ""}</p>',
            unsafe_allow_html=True
        )
        cols = st.columns(6)
        for i, (col, key, full) in enumerate(zip(cols, STAT_KEYS, STAT_FULL)):
            with col:
                options = sorted(set(STANDARD_ARRAY), reverse=True)
                current = st.session_state.stats[key]
                if current not in options:
                    current = options[i % len(options)]
                # Highlight if this stat is the top priority
                label = full[:3]
                if priority and priority.index(key) == 0:
                    label = f"★ {full[:3]}"
                choice = st.selectbox(label, options, index=options.index(current), key=f"sa_{key}")
                st.session_state.stats[key] = choice

    elif method == "Point Buy":
        COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
        total_points = 27
        spent = sum(COSTS.get(v, 0) for v in st.session_state.stats.values())
        remaining = total_points - spent
        color = "#50c050" if remaining >= 0 else "#e04040"
        st.markdown(
            f'<p style="font-family:Cinzel,serif; color:{color}; margin-bottom:0.8rem">'
            f'Points Remaining: <b>{remaining}</b> / {total_points}'
            f'{"  —  click ⚡ Auto-Arrange for the optimal distribution for your class." if priority else ""}</p>',
            unsafe_allow_html=True
        )
        cols = st.columns(6)
        for col, key, full in zip(cols, STAT_KEYS, STAT_FULL):
            with col:
                label = full[:3]
                if priority and priority.index(key) == 0:
                    label = f"★ {full[:3]}"
                val = st.number_input(label, min_value=8, max_value=15, value=st.session_state.stats[key], key=f"pb_{key}")
                st.session_state.stats[key] = val

    else:  # Manual
        st.markdown(
            f'<p style="font-family:Crimson Text,serif; color:#c8aa70; margin-bottom:0.8rem">'
            f'Enter your scores directly (rolled or custom).'
            f'{"  The ⚡ Auto-Arrange button can suggest an optimal distribution." if priority else ""}</p>',
            unsafe_allow_html=True
        )
        cols = st.columns(6)
        for col, key, full in zip(cols, STAT_KEYS, STAT_FULL):
            with col:
                label = full[:3]
                if priority and priority.index(key) == 0:
                    label = f"★ {full[:3]}"
                val = st.number_input(label, min_value=1, max_value=30, value=st.session_state.stats[key], key=f"man_{key}")
                st.session_state.stats[key] = val

    st.markdown('</div>', unsafe_allow_html=True)

    # Preview stats with racial bonuses
    st.markdown('<div class="section-header" style="color:#c9a84c; margin-top:1.5rem">📊 Final Ability Scores (with Racial Bonuses)</div>', unsafe_allow_html=True)
    cols = st.columns(6)
    for col, key, full in zip(cols, STAT_KEYS, STAT_FULL):
        eff = effective_stat(key, race)
        mod = modifier(eff)
        col.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-name">{full[:3].upper()}</div>'
            f'<div class="stat-val">{eff}</div>'
            f'<div class="stat-mod">{mod}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Derived stats
    level = st.session_state.char_level
    prof = proficiency_bonus(level)
    con_mod = modifier_int(effective_stat("CON", race))
    dex_mod = modifier_int(effective_stat("DEX", race))
    cls = get_class(st.session_state.class_id)
    hit_die_num = int(cls["hit_die"][1:]) if cls else 8
    hp = hit_die_num + con_mod + (level - 1) * (math.floor(hit_die_num / 2) + 1 + con_mod)

    st.markdown('<br>', unsafe_allow_html=True)
    dcol1, dcol2, dcol3, dcol4 = st.columns(4)
    for c, label, val in [
        (dcol1, "Proficiency Bonus", f"+{prof}"),
        (dcol2, "Initiative", f"{modifier(effective_stat('DEX', race))}"),
        (dcol3, "HP (Average)", str(max(hp, 1))),
        (dcol4, "Passive Perception", str(10 + modifier_int(effective_stat("WIS", race)) + prof)),
    ]:
        c.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-name" style="font-size:0.55rem">{label.upper()}</div>'
            f'<div class="stat-val" style="font-size:1.6rem">{val}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Character details
    st.markdown('<div class="card" style="margin-top:1.5rem">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🖊️ Character Details (Optional)</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.personality = st.text_area("Personality Traits", st.session_state.personality, height=80, placeholder="How does your character act?")
        st.session_state.ideals = st.text_area("Ideals", st.session_state.ideals, height=80, placeholder="What drives your character?")
    with col2:
        st.session_state.bonds = st.text_area("Bonds", st.session_state.bonds, height=80, placeholder="What connects your character to the world?")
        st.session_state.flaws = st.text_area("Flaws", st.session_state.flaws, height=80, placeholder="What are your character's weaknesses?")
    st.session_state.notes = st.text_area("Additional Notes", st.session_state.notes, height=68, placeholder="Any other notes about your character…")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, _, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 5
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.step = 7
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — SKILL PROFICIENCIES
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == 7:
    race  = get_race(st.session_state.race_id)
    cls   = get_class(st.session_state.class_id)
    bg    = get_background(st.session_state.background_id)
    mech  = get_mech(st.session_state.class_id or "")
    level = st.session_state.char_level
    prof  = proficiency_bonus(level)

    sc = mech.get("skill_choices", {})
    class_options = sc.get("options", [])
    pick_count    = sc.get("count", 2)

    bg_skills     = bg.get("skill_proficiencies", []) if bg else []
    race_skills   = race.get("bonus_skills", []) if race else []
    auto_skills   = set(bg_skills) | set(race_skills)

    # Eligible: class options not already granted for free
    eligible = [s for s in class_options if s not in auto_skills]

    # Restore or prune previous selection to valid choices
    prev = [s for s in st.session_state.chosen_skills if s in eligible]
    if prev != st.session_state.chosen_skills:
        st.session_state.chosen_skills = prev

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎯 Choose Skill Proficiencies</div>', unsafe_allow_html=True)

    if bg_skills or race_skills:
        auto_badges = " ".join(
            [f'<span class="badge teal">✔ {s} (background)</span>' for s in bg_skills] +
            [f'<span class="badge">✔ {s} (race)</span>' for s in race_skills]
        )
        st.markdown(f'<p style="font-family:Crimson Text,serif; color:#c8aa70; margin-bottom:0.6rem">Already proficient: {auto_badges}</p>', unsafe_allow_html=True)

    if eligible:
        st.markdown(
            f'<p style="font-family:Crimson Text,serif; color:#c8aa70; margin-bottom:1rem">'
            f'Choose <b style="color:#c9a84c">{pick_count}</b> additional skills from your class list '
            f'({cls["name"] if cls else ""}):</p>',
            unsafe_allow_html=True
        )
        chosen = list(st.session_state.chosen_skills)
        for skill in eligible:
            is_checked = skill in chosen
            at_limit   = len(chosen) >= pick_count and not is_checked
            key        = f"skill_{skill}"
            label      = f"{skill}" + (" *(limit reached)*" if at_limit and not is_checked else "")
            if st.checkbox(label, value=is_checked, disabled=at_limit, key=key):
                if skill not in chosen:
                    chosen.append(skill)
            else:
                if skill in chosen:
                    chosen.remove(skill)
        st.session_state.chosen_skills = chosen[:pick_count]
    else:
        st.markdown('<p style="font-family:Crimson Text,serif; color:#907050; font-style:italic">All class skill options are already covered by your race/background proficiencies.</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Expertise (Rogue L1, Bard L3+) ───────────────────────────────────────
    all_prof = get_all_proficient_skills(race, bg, st.session_state.chosen_skills)
    has_expertise = (
        st.session_state.class_id == "rogue" or
        (st.session_state.class_id == "bard" and level >= 3)
    )
    if has_expertise:
        expertise_pick = 2
        st.markdown('<div class="card" style="margin-top:1rem">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🌟 Expertise</div>', unsafe_allow_html=True)
        st.markdown(
            f'<p style="font-family:Crimson Text,serif; color:#c8aa70; margin-bottom:0.6rem">'
            f'Choose <b style="color:#c9a84c">{expertise_pick}</b> skills you are proficient in. '
            f'Your proficiency bonus is <b>doubled</b> for those skills.</p>',
            unsafe_allow_html=True
        )
        proficient_list = sorted(all_prof)
        chosen_exp = [s for s in st.session_state.expertise_skills if s in proficient_list]
        if chosen_exp != st.session_state.expertise_skills:
            st.session_state.expertise_skills = chosen_exp
        new_exp = list(chosen_exp)
        for skill in proficient_list:
            is_checked = skill in new_exp
            at_limit   = len(new_exp) >= expertise_pick and not is_checked
            if st.checkbox(
                skill + (" *(limit reached)*" if at_limit and not is_checked else ""),
                value=is_checked,
                disabled=at_limit,
                key=f"exp_{skill}"
            ):
                if skill not in new_exp:
                    new_exp.append(skill)
            else:
                if skill in new_exp:
                    new_exp.remove(skill)
        st.session_state.expertise_skills = new_exp[:expertise_pick]
        st.markdown(
            f'<p style="font-family:Cinzel,serif; color:#{"c9a84c" if len(new_exp)==expertise_pick else "e04040"}; '
            f'font-size:0.78rem; margin-top:0.3rem">Selected: {len(new_exp)}/{expertise_pick}</p>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Language Selection ────────────────────────────────────────────────────
    st.markdown('<div class="card" style="margin-top:1rem">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🗣 Languages</div>', unsafe_allow_html=True)

    # Auto languages from race and background
    race_langs = race.get("languages", []) if race else []
    bg_langs   = bg.get("languages", []) if bg else []
    auto_langs = list(dict.fromkeys(race_langs + bg_langs))  # preserve order, dedupe
    if auto_langs:
        badges = " ".join([f'<span class="badge teal">🗣 {l}</span>' for l in auto_langs])
        st.markdown(
            f'<p style="font-family:Crimson Text,serif; color:#c8aa70; margin-bottom:0.6rem">'
            f'Known from race & background: {badges}</p>',
            unsafe_allow_html=True
        )

    # Additional languages (optional — for GM-approved extra languages)
    extra_options = [l for l in ALL_LANGUAGES if l not in auto_langs]
    st.markdown(
        '<p style="font-family:Crimson Text,serif; color:#c8aa70; font-size:0.9rem; margin-bottom:0.4rem">'
        'Additional languages (with GM approval — for backgrounds or feats that grant extras):</p>',
        unsafe_allow_html=True
    )
    chosen_langs = st.multiselect(
        "Additional Languages",
        extra_options,
        default=[l for l in st.session_state.chosen_languages if l in extra_options],
        key="lang_select",
        label_visibility="collapsed"
    )
    st.session_state.chosen_languages = chosen_langs
    st.markdown('</div>', unsafe_allow_html=True)

    # Preview: full skill list with modifiers
    st.markdown('<div class="section-header" style="color:#c9a84c; margin-top:1.5rem">📋 All Skills Preview</div>', unsafe_allow_html=True)
    expertise_set = set(st.session_state.expertise_skills)
    cols = st.columns(3)
    for i, (sname, akey) in enumerate(ALL_SKILLS):
        is_exp = sname in expertise_set
        eff_prof = prof * 2 if is_exp else prof
        mod_val = skill_modifier(sname, akey, race, eff_prof, all_prof)
        sign    = f"+{mod_val}" if mod_val >= 0 else str(mod_val)
        dot     = "★" if is_exp else ("●" if sname in all_prof else "○")
        color   = "#e8c870" if is_exp else ("#c9a84c" if sname in all_prof else "#907050")
        cols[i % 3].markdown(
            f'<div style="display:flex;justify-content:space-between;padding:0.2rem 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.04)">'
            f'<span style="font-family:Crimson Text,serif;color:{color}">'
            f'<span style="font-size:0.85rem">{dot}</span> {sname} '
            f'<span style="font-size:0.75rem;opacity:0.6">({ABILITY_SHORT[akey]})</span></span>'
            f'<span style="font-family:Cinzel,serif;color:{color};font-weight:700">{sign}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    col1, _, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 6
            st.rerun()
    with col3:
        if st.button("Next →", type="primary", use_container_width=True):
            if len(st.session_state.chosen_skills) < min(pick_count, len(eligible)):
                st.error(f"Please choose {pick_count} skill(s) from the list.")
            else:
                st.session_state.step = 8
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — STARTING EQUIPMENT
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == 8:
    cls  = get_class(st.session_state.class_id)
    mech = get_mech(st.session_state.class_id or "")
    choices  = mech.get("equipment_choices", [])
    fixed    = mech.get("equipment_fixed", [])

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-header">🎒 Starting Equipment — {cls["name"] if cls else ""}</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-family:Crimson Text,serif; color:#c8aa70; margin-bottom:1rem">Choose your starting gear. Your armor choice also determines your base Armor Class.</p>', unsafe_allow_html=True)

    equip = dict(st.session_state.equip_choices)
    for choice in choices:
        cid = choice["id"]
        options = [o["label"] for o in choice["options"]]
        current = equip.get(cid, 0)
        if current >= len(options):
            current = 0
        st.markdown(f'<p style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.85rem; margin:0.8rem 0 0.3rem; letter-spacing:0.06em">{choice["prompt"].upper()}</p>', unsafe_allow_html=True)
        sel = st.radio(
            choice["prompt"],
            options,
            index=current,
            key=f"equip_{cid}",
            label_visibility="collapsed"
        )
        equip[cid] = options.index(sel)
    st.session_state.equip_choices = equip

    if fixed:
        st.markdown('<div class="section-header" style="margin-top:1rem">Also included</div>', unsafe_allow_html=True)
        st.markdown(" ".join([f'<span class="badge">📦 {item}</span>' for item in fixed]), unsafe_allow_html=True)

    # AC preview
    race = get_race(st.session_state.race_id)
    if st.session_state.class_id:
        ac_val, ac_note = compute_ac(st.session_state.class_id, race, equip)
        st.markdown(
            f'<div style="margin-top:1.5rem; display:flex; align-items:center; gap:1rem">'
            f'<div class="stat-box" style="width:100px">'
            f'<div class="stat-name" style="font-size:0.6rem">ARMOR CLASS</div>'
            f'<div class="stat-val" style="font-size:2rem">{ac_val}</div>'
            f'</div>'
            f'<p style="font-family:Crimson Text,serif; color:#a08060; font-style:italic">{ac_note}</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Full item list preview
    all_items = list(fixed)
    for choice in choices:
        cid = choice["id"]
        idx = equip.get(cid, 0)
        if idx < len(choice["options"]):
            all_items.extend(choice["options"][idx]["items"])
    st.markdown('<div class="section-header" style="margin-top:1rem">Your Full Equipment List</div>', unsafe_allow_html=True)
    st.markdown(
        "<ul style='font-family:Crimson Text,serif; color:#c8aa70; columns:2; margin:0; padding-left:1.2rem'>" +
        "".join(f"<li>{item}</li>" for item in all_items) +
        "</ul>",
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    col1, _, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 7
            st.rerun()
    with col3:
        if st.button("View Sheet →", type="primary", use_container_width=True):
            st.session_state.step = 9
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — CHARACTER SHEET
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.step == 9:
    race = get_race(st.session_state.race_id)
    cls = get_class(st.session_state.class_id)
    sub = get_subclass(cls, st.session_state.subclass_id)
    bg = get_background(st.session_state.background_id)
    level = st.session_state.char_level
    prof = proficiency_bonus(level)

    STAT_KEYS = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    STAT_FULL = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]

    # ── Header ──
    race_name = race["name"] if race else "Unknown Race"
    cls_name = cls["name"] if cls else "Unknown Class"
    sub_name = sub["name"] if sub else ""
    bg_name = bg["name"] if bg else "Unknown Background"
    race_icon = race["icon"] if race else ""
    cls_icon = cls["icon"] if cls else ""

    st.markdown(
        f'<div class="sheet-header">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem">'
        f'<span style="font-family:Cinzel,serif; font-size:0.75rem; color:#a08060; letter-spacing:0.1em">RYNDOR: THE WEIRDED LANDS</span>'
        f'<span style="font-family:Cinzel,serif; font-size:0.75rem; color:#a08060">LEVEL {level}</span>'
        f'</div>'
        f'<div class="char-name">{st.session_state.char_name}</div>'
        f'<div class="char-sub">'
        f'{race_icon} {race_name} &nbsp;·&nbsp; {cls_icon} {cls_name}'
        f'{" — " + sub_name if sub_name else ""}'
        f' &nbsp;·&nbsp; 📜 {bg_name}'
        f'</div>'
        f'<div style="margin-top:0.5rem">'
        f'<span class="badge">{st.session_state.alignment}</span>'
        f'{"&nbsp;" + "<span class=badge>Player: " + st.session_state.player_name + "</span>" if st.session_state.player_name else ""}'
        f'<span class="badge">Proficiency Bonus: +{prof}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── Ability Scores ──
    st.markdown('<div class="sheet-section" style="margin-top:0">', unsafe_allow_html=True)
    st.markdown('<div class="sheet-section-title">Ability Scores</div>', unsafe_allow_html=True)
    cols = st.columns(6)
    for col, key, full in zip(cols, STAT_KEYS, STAT_FULL):
        eff = effective_stat(key, race)
        mod = modifier(eff)
        col.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-name">{full[:3]}</div>'
            f'<div class="stat-val">{eff}</div>'
            f'<div class="stat-mod">{mod}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Derived Stats ──
    mech_sheet = get_mech(st.session_state.class_id or "")
    con_mod = modifier_int(effective_stat("CON", race))
    dex_mod = modifier_int(effective_stat("DEX", race))
    wis_mod = modifier_int(effective_stat("WIS", race))
    hit_die_num = int(cls["hit_die"][1:]) if cls else 8
    hp = hit_die_num + con_mod + (level - 1) * (math.floor(hit_die_num / 2) + 1 + con_mod)
    ac_val, ac_note = compute_ac(st.session_state.class_id or "", race, st.session_state.equip_choices)
    all_prof_skills = get_all_proficient_skills(race, bg, st.session_state.chosen_skills)

    # Passive Perception: 10 + Perception modifier
    perc_mod = skill_modifier("Perception", "WIS", race, prof, all_prof_skills)

    st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
    st.markdown('<div class="sheet-section-title">Combat Statistics</div>', unsafe_allow_html=True)
    dcols = st.columns(5)
    stats_display = [
        ("Max HP", str(max(hp, 1))),
        ("Armor Class", f"{ac_val}"),
        ("Initiative", modifier(effective_stat("DEX", race))),
        ("Speed", str(race["speed"].get("walk", 30) if race else 30) + " ft"),
        ("Passive Perception", str(10 + perc_mod)),
    ]
    for col, (label, val) in zip(dcols, stats_display):
        col.markdown(
            f'<div class="stat-box">'
            f'<div class="stat-name" style="font-size:0.55rem">{label.upper()}</div>'
            f'<div class="stat-val" style="font-size:1.5rem">{val}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.markdown(f'<p style="font-family:Crimson Text,serif; color:#7a6040; font-size:0.82rem; margin:0.3rem 0 0; font-style:italic">AC: {ac_note} · Hit Die: {cls["hit_die"] if cls else "d8"} · Proficiency Bonus: +{prof}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Saving Throws (prominent stat-box style) ──
    st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
    st.markdown('<div class="sheet-section-title">Saving Throws</div>', unsafe_allow_html=True)
    class_saves = cls["saves"] if cls else []
    save_cols = st.columns(6)
    for (full, key), col in zip(
        [("Strength","STR"),("Dexterity","DEX"),("Constitution","CON"),
         ("Intelligence","INT"),("Wisdom","WIS"),("Charisma","CHA")],
        save_cols
    ):
        eff = effective_stat(key, race)
        mod_val = modifier_int(eff)
        is_prof = full in class_saves
        total = mod_val + (prof if is_prof else 0)
        sign = f"+{total}" if total >= 0 else str(total)
        border_color = "var(--gold)" if is_prof else "rgba(201,168,76,0.25)"
        label_color  = "#c9a84c"     if is_prof else "#907050"
        prof_label   = "★ PROF"      if is_prof else "SAVE"
        col.markdown(
            f'<div class="stat-box" style="border-color:{border_color}">'
            f'<div class="stat-name">{full[:3]}</div>'
            f'<div class="stat-val" style="font-size:1.8rem">{sign}</div>'
            f'<div style="font-family:Cinzel,serif;font-size:0.52rem;color:{label_color};margin-top:0.15rem">{prof_label}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Proficiencies & Languages ──
    st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
    st.markdown('<div class="sheet-section-title">Proficiencies & Languages</div>', unsafe_allow_html=True)
    prof_col1, prof_col2 = st.columns(2)
    with prof_col1:
        # Languages: race + bg + chosen
        race_langs_sheet = race.get("languages", []) if race else []
        bg_langs_sheet   = bg.get("languages", []) if bg else []
        extra_langs      = st.session_state.get("chosen_languages", [])
        all_sheet_langs  = list(dict.fromkeys(race_langs_sheet + bg_langs_sheet + extra_langs))
        if all_sheet_langs:
            st.markdown('<p style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.75rem; margin:0 0 0.3rem">LANGUAGES</p>', unsafe_allow_html=True)
            for l in all_sheet_langs:
                st.markdown(f'<div style="font-family:Crimson Text,serif; color:#c8aa70; padding:0.12rem 0">🗣 {l}</div>', unsafe_allow_html=True)
        if bg and bg.get("tool_proficiencies"):
            st.markdown('<p style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.75rem; margin:0.5rem 0 0.3rem">TOOLS</p>', unsafe_allow_html=True)
            for t in bg["tool_proficiencies"]:
                st.markdown(f'<div style="font-family:Crimson Text,serif; color:#c8aa70; padding:0.12rem 0">🔧 {t} (+{prof})</div>', unsafe_allow_html=True)
    with prof_col2:
        if cls:
            st.markdown('<p style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.75rem; margin:0 0 0.3rem">ARMOR & WEAPONS</p>', unsafe_allow_html=True)
            for item in cls.get("armor", []) + cls.get("weapons", []):
                st.markdown(f'<div style="font-family:Crimson Text,serif; color:#c8aa70; padding:0.1rem 0; font-size:0.88rem">⚔ {item}</div>', unsafe_allow_html=True)
        # Class options summary (Fighting Style, Pact Boon, etc.)
        class_opts_display = st.session_state.get("class_options", {})
        cf_choices = CLASS_FEATURES.get(st.session_state.class_id or "", {}).get("choices", [])
        if class_opts_display and cf_choices:
            st.markdown('<p style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.75rem; margin:0.5rem 0 0.3rem">CLASS CHOICES</p>', unsafe_allow_html=True)
            for choice in cf_choices:
                val = class_opts_display.get(choice["key"])
                if val:
                    if isinstance(val, list):
                        opts = choice.get("options", [])
                        names = [o["name"] for o in opts if o["id"] in val]
                        display = ", ".join(names)
                    else:
                        opts = choice.get("options", [])
                        display = next((o["name"] for o in opts if o["id"] == val), val)
                    st.markdown(
                        f'<div style="font-family:Crimson Text,serif; color:#c8aa70; padding:0.12rem 0; font-size:0.88rem">'
                        f'<span style="font-family:Cinzel,serif; color:#e8c870; font-size:0.78rem">{choice["name"]}:</span> {display}</div>',
                        unsafe_allow_html=True
                    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Skills ──
    sheet_expertise = set(st.session_state.get("expertise_skills", []))
    st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
    title_suffix = ' <span style="font-family:Crimson Text,serif;font-size:0.75rem;color:#907050;font-weight:normal;font-style:italic">★ = Expertise (double prof)</span>' if sheet_expertise else ""
    st.markdown(f'<div class="sheet-section-title">Skills{title_suffix}</div>', unsafe_allow_html=True)
    skill_cols = st.columns(3)
    for i, (sname, akey) in enumerate(ALL_SKILLS):
        is_exp    = sname in sheet_expertise
        eff_prof  = prof * 2 if is_exp else prof
        mod_val   = skill_modifier(sname, akey, race, eff_prof, all_prof_skills)
        sign      = f"+{mod_val}" if mod_val >= 0 else str(mod_val)
        dot       = "★" if is_exp else ("●" if sname in all_prof_skills else "○")
        color     = "#e8c870" if is_exp else ("#c9a84c" if sname in all_prof_skills else "#907050")
        skill_cols[i % 3].markdown(
            f'<div style="display:flex;justify-content:space-between;padding:0.2rem 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.04)">'
            f'<span style="font-family:Crimson Text,serif;color:{color}">'
            f'<span style="font-size:0.85rem">{dot}</span> {sname} '
            f'<span style="font-size:0.72rem;opacity:0.55">({ABILITY_SHORT[akey]})</span></span>'
            f'<span style="font-family:Cinzel,serif;color:{color};font-weight:700;font-size:0.9rem">{sign}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Equipment ──
    mech_eq = get_mech(st.session_state.class_id or "")
    eq_fixed = mech_eq.get("equipment_fixed", [])
    eq_choices = mech_eq.get("equipment_choices", [])
    eq_items = list(eq_fixed)
    for choice in eq_choices:
        cid = choice["id"]
        idx = st.session_state.equip_choices.get(cid, 0)
        if idx < len(choice["options"]):
            eq_items.extend(choice["options"][idx]["items"])
    if bg:
        eq_items.append(bg.get("equipment", ""))

    st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
    st.markdown('<div class="sheet-section-title">🎒 Equipment</div>', unsafe_allow_html=True)
    st.markdown(
        "<ul style='font-family:Crimson Text,serif; color:#c8aa70; columns:2; margin:0; padding-left:1.2rem; font-size:0.95rem'>" +
        "".join(f"<li>{item}</li>" for item in eq_items if item) +
        "</ul>",
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Spellcasting (non-Sev'rinn only) ──
    sc_data = mech_sheet.get("spellcasting")
    if sc_data and st.session_state.class_id != "sevrinn":
        sc_ability = sc_data["ability"]
        sc_key_map = {"Wisdom":"WIS","Intelligence":"INT","Charisma":"CHA"}
        sc_key = sc_key_map.get(sc_ability, "WIS")
        sc_mod = modifier_int(effective_stat(sc_key, race))
        spell_dc = 8 + prof + sc_mod
        spell_atk = f"+{prof + sc_mod}" if (prof + sc_mod) >= 0 else str(prof + sc_mod)
        cantrips = sc_data.get("cantrips_known")
        cantrips_val = cantrips[min(level-1, 19)] if cantrips else "—"
        slots = get_spell_slots(sc_data.get("slot_type"), level)
        spells_val, spells_label = get_spells_known_or_prepared(sc_data, level, race)

        st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
        st.markdown(f'<div class="sheet-section-title">✨ Spellcasting ({sc_ability})</div>', unsafe_allow_html=True)

        sp_cols = st.columns(4)
        sp_cols[0].markdown(f'<div class="stat-box"><div class="stat-name" style="font-size:0.55rem">SPELL SAVE DC</div><div class="stat-val" style="font-size:1.8rem">{spell_dc}</div></div>', unsafe_allow_html=True)
        sp_cols[1].markdown(f'<div class="stat-box"><div class="stat-name" style="font-size:0.55rem">SPELL ATTACK</div><div class="stat-val" style="font-size:1.8rem">{spell_atk}</div></div>', unsafe_allow_html=True)
        sp_cols[2].markdown(f'<div class="stat-box"><div class="stat-name" style="font-size:0.55rem">CANTRIPS KNOWN</div><div class="stat-val" style="font-size:1.8rem">{cantrips_val}</div></div>', unsafe_allow_html=True)
        if spells_val is not None:
            sp_cols[3].markdown(f'<div class="stat-box"><div class="stat-name" style="font-size:0.55rem">{(spells_label or "SPELLS").upper()}</div><div class="stat-val" style="font-size:1.8rem">{spells_val}</div></div>', unsafe_allow_html=True)

        if slots:
            st.markdown('<p style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.75rem; margin:0.8rem 0 0.4rem; letter-spacing:0.1em">SPELL SLOTS</p>', unsafe_allow_html=True)
            slot_html = " ".join([
                f'<span class="badge" style="font-size:0.82rem; padding:4px 10px">{lvl}: {cnt} slot{"s" if cnt != 1 else ""}</span>'
                for lvl, cnt in slots
            ])
            st.markdown(slot_html, unsafe_allow_html=True)
            if sc_data.get("slot_type") == "pact":
                st.markdown('<p style="font-family:Crimson Text,serif; color:#7a6040; font-size:0.82rem; margin-top:0.3rem; font-style:italic">Pact Magic slots recover on a short rest.</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="font-family:Crimson Text,serif; color:#7a6040; font-size:0.82rem; margin-top:0.3rem; font-style:italic">Spell slots recover on a long rest.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Racial Traits ──
    if race:
        st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
        st.markdown(f'<div class="sheet-section-title">{race["icon"]} Racial Traits — {race["name"]}</div>', unsafe_allow_html=True)
        for trait in race.get("traits", []):
            st.markdown(
                f'<div class="feat-row">'
                f'<div class="fname">{trait["name"]}</div>'
                f'<div class="fdesc">{trait["description"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Class Features ──
    if sub:
        st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
        st.markdown(f'<div class="sheet-section-title">{cls["icon"]} {sub["name"]} Features</div>', unsafe_allow_html=True)
        available = [f for f in sub.get("features", []) if f["level"] <= level]
        for feat in available:
            st.markdown(
                f'<div class="feat-row">'
                f'<div class="fname">{feat["name"]} <span style="color:#7a6040; font-size:0.75rem">(L{feat["level"]})</span></div>'
                f'<div class="fdesc">{feat["description"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Sev'rinn extras
        if cls and cls["id"] == "sevrinn":
            mech = cls.get("mechanics", {})
            lvl_data = None
            for row in mech.get("level_table", []):
                if row["level"] <= level:
                    lvl_data = row
            if lvl_data:
                st.markdown(
                    f'<div style="display:flex; gap:1rem; margin:0.8rem 0">'
                    f'<span class="badge">⚡ Charges: {lvl_data["charges"]}</span>'
                    f'<span class="badge">📚 Techniques Known: {lvl_data["techniques"]}</span>'
                    f'<span class="badge crimson">🌀 Surge DC: {lvl_data["surge_dc"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            techs = [t for t in sub.get("techniques", []) if t["level"] <= level]
            if techs:
                st.markdown('<div class="sheet-section-title" style="margin-top:0.8rem">Combat Techniques</div>', unsafe_allow_html=True)
                for tech in techs:
                    st.markdown(
                        f'<div class="feat-row">'
                        f'<div class="fname">{tech["name"]}</div>'
                        f'<div class="fdesc">{tech["description"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Background Feature ──
    if bg:
        st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
        st.markdown(f'<div class="sheet-section-title">{bg["icon"]} Background Feature — {bg["name"]}</div>', unsafe_allow_html=True)
        feat = bg.get("feature", {})
        st.markdown(
            f'<div class="feat-row">'
            f'<div class="fname">{feat.get("name","")}</div>'
            f'<div class="fdesc">{feat.get("description","")}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown(f'<div style="margin-top:0.5rem"><b style="font-family:Cinzel,serif; color:#c9a84c; font-size:0.8rem">EQUIPMENT:</b> <span style="font-family:Crimson Text,serif; color:#c8aa70">{bg["equipment"]}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Character Details ──
    if any([st.session_state.personality, st.session_state.ideals,
            st.session_state.bonds, st.session_state.flaws, st.session_state.notes]):
        st.markdown('<div class="sheet-section">', unsafe_allow_html=True)
        st.markdown('<div class="sheet-section-title">📖 Character Details</div>', unsafe_allow_html=True)
        details = [
            ("Personality", st.session_state.personality),
            ("Ideals", st.session_state.ideals),
            ("Bonds", st.session_state.bonds),
            ("Flaws", st.session_state.flaws),
            ("Notes", st.session_state.notes),
        ]
        for label, val in details:
            if val:
                st.markdown(
                    f'<div class="feat-row">'
                    f'<div class="fname">{label}</div>'
                    f'<div class="fdesc">{val}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Actions ──
    st.markdown('<br>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Edit Character", use_container_width=True):
            st.session_state.step = 8
            st.rerun()
    with col2:
        if st.button("🔄 Start Over", use_container_width=True):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()
    with col3:
        st.button("🖨️ Print / Save PDF", use_container_width=True, help="Use your browser's Print function (Ctrl+P / Cmd+P) to save as PDF")

    st.markdown(
        '<p style="font-family:Crimson Text,serif; color:#5a4030; font-style:italic; text-align:center; margin-top:1rem; font-size:0.85rem">'
        'To save as PDF: use your browser\'s Print function → "Save as PDF" &nbsp;·&nbsp; '
        'Ryndor: The Weirded Lands character sheet builder'
        '</p>',
        unsafe_allow_html=True
    )
