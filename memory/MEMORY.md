# Ryndor Character Maker — Project Memory

## Stack
- Python + Streamlit (streamlit==1.40.1)
- Docker (python:3.11-slim, port 8501)
- Volume mount: `./app:/app/app` (live reload without rebuild)
- Run: `docker compose up --build`

## File Structure
```
app/
  app.py               # Main Streamlit app (~2000 lines)
  data/
    races.json         # 6 Ryndor races with bonus_skills field
    classes.json       # 13 classes (12 SRD + Sev'rinn) with subclasses
    backgrounds.json   # 9 Ryndor-specific backgrounds
    class_mechanics.json  # Skill choices, equipment, spellcasting per class
    class_features.json   # Core SRD features + interactive choices per class
Dockerfile
docker-compose.yml
requirements.txt
```

## App Flow (9 steps)
1. Basics (name, level, alignment)
2. Race (6 Ryndor races)
3. Class (13 classes + Ryndor subclass)
4. Features (class features at current level + interactive choices)
5. Background (9 Ryndor backgrounds)
6. Stats (Standard Array / Point Buy / Manual + racial ASI preview)
7. Skills (class skill selection + Expertise for Rogue/Bard + Language selection)
8. Gear (equipment choices + live AC preview)
9. Sheet (full character sheet)

## Key Features Implemented
- **Step 4 Features**: Shows core SRD class features up to character level + interactive choices:
  - Fighting Style (Fighter L1, Paladin L2, Ranger L1-2)
  - Favored Enemy (Ranger L1) — 14 creature type options
  - Natural Explorer (Ranger L1) — 8 terrain options
  - Metamagic (Sorcerer L3) — pick 2 from 8 options
  - Eldritch Invocations (Warlock L2) — pick 2 from 13 options
  - Pact Boon (Warlock L3) — pick 1 of 3
- **Expertise**: Rogue (always) and Bard (L3+) get expertise selection in Skills step
  - Double proficiency bonus; shown with ★ on sheet and in preview
- **Languages**: Skills step shows auto languages (race + bg) and optional additional language picker (ALL_LANGUAGES list)
- **Saving Throws**: Prominent 6-column stat-box layout on sheet with gold border for proficient saves
- **Class choices display**: Sheet shows selected Fighting Style, Pact Boon, etc. in Proficiencies section

## Session State Keys
```python
defaults = {
    "step": 1,
    "char_name": "", "player_name": "", "char_level": 1,
    "race_id": None, "class_id": None, "subclass_id": None,
    "background_id": None, "alignment": "",
    "stats": {"STR":15,"DEX":14,"CON":13,"INT":12,"WIS":10,"CHA":8},
    "stat_method": "Standard Array",
    "chosen_skills": [],
    "equip_choices": {},    # {choice_id: option_index}
    "class_options": {},    # {choice_key: selected_id or [selected_ids]}
    "expertise_skills": [], # list of skill names with doubled proficiency
    "chosen_languages": [], # additional languages beyond race/bg
    "notes": "", "personality": "", "ideals": "", "bonds": "", "flaws": "",
}
```

## Constants in app.py
- `FULL_CASTER_SLOTS`, `HALF_CASTER_SLOTS`, `PACT_SLOTS` — spell slot tables
- `ALL_SKILLS` — 18 (name, ability_key) tuples
- `RYNDOR_LANGUAGES` — ["Auran", "Drakarim", "Inglishmek", "Leoporin", "Sylvan"]
- `SRD_LANGUAGES` — 15 standard + exotic languages
- `ALL_LANGUAGES` — sorted combined list
- `CLASS_FEATURES` — loaded from class_features.json

## Design
- Dark fantasy: Cinzel (headers) + Crimson Text (body), gold/parchment palette
- CSS variables: --ink, --parchment, --gold, --crimson, --teal
- Custom step progress bar (1-9 nodes with connectors)
- Stat boxes: `.stat-box` CSS class, gold border when proficient
- Expertise: ★ symbol, `#e8c870` (brighter gold) color
- Saving throws on sheet: 6 stat-boxes in a row, gold border = proficient

## Known Patterns
- `get_race/class/background/subclass()` — lookup by id
- `effective_stat(stat_key, race)` — applies racial ASI
- `modifier_int(score)` / `modifier(score)` — int vs string (+N)
- `proficiency_bonus(level)` — SRD formula
- `compute_ac(class_id, race, equip_choices)` — returns (ac_val, note_str)
- `get_all_proficient_skills(race, bg, chosen_skills)` — full proficiency set
- Sev'rinn is excluded from standard spellcasting display (custom mechanic)
- `st.text_area` height must be ≥ 68px (Streamlit constraint)
