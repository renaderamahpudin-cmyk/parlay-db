import json

# 11 match dari Stake (11 Leg Multi + extra)
dummy = [
    # Mainz vs Bayer Leverkusen (Sat, 10 Oct 8:30 PM)
    {
        "liga": "GERMANY BUNDESLIGA",
        "waktu": "20:30",
        "home": "Mainz",
        "away": "Bayer Leverkusen",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 3.5, "over": 2.10, "under": 1.74},
            {"line": 3.0, "over": 1.75, "under": 2.10},
            {"line": 4.0, "over": 2.60, "under": 1.50},
        ],
    },
    # Augsburg vs Bayern Munich (Sat, 10 Oct 8:30 PM)
    {
        "liga": "GERMANY BUNDESLIGA",
        "waktu": "20:30",
        "home": "Augsburg",
        "away": "Bayern Munich",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 4.5, "over": 2.00, "under": 1.89},
            {"line": 4.0, "over": 1.75, "under": 2.10},
            {"line": 3.5, "over": 1.45, "under": 2.85},
        ],
    },
    # Inter vs Parma (Sat, 10 Oct 11:00 PM)
    {
        "liga": "ITALY SERIE A",
        "waktu": "23:00",
        "home": "Inter",
        "away": "Parma",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 3.5, "over": 2.05, "under": 1.93},
            {"line": 3.0, "over": 1.70, "under": 2.15},
            {"line": 4.0, "over": 2.50, "under": 1.55},
        ],
    },
    # Napoli vs Frosinone (Sun, 11 Oct 1:45 AM)
    {
        "liga": "ITALY SERIE A",
        "waktu": "01:45",
        "home": "Napoli",
        "away": "Frosinone",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 3.5, "over": 2.05, "under": 1.68},
            {"line": 3.0, "over": 1.70, "under": 2.15},
            {"line": 4.0, "over": 2.60, "under": 1.50},
        ],
    },
    # Real Madrid vs Villarreal (Sun, 11 Oct 2:00 AM)
    {
        "liga": "SPAIN LA LIGA",
        "waktu": "02:00",
        "home": "Real Madrid",
        "away": "Villarreal",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 4.0, "over": 2.05, "under": 1.69},
            {"line": 3.5, "over": 1.70, "under": 2.10},
            {"line": 4.5, "over": 2.60, "under": 1.48},
        ],
    },
    # Atalanta vs Venezia (Mon, 12 Oct 11:30 PM)
    {
        "liga": "ITALY SERIE A",
        "waktu": "23:30",
        "home": "Atalanta",
        "away": "Venezia",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 3.5, "over": 2.00, "under": 1.60},
            {"line": 3.0, "over": 1.60, "under": 2.30},
            {"line": 4.0, "over": 2.50, "under": 1.55},
        ],
    },
    # Eintracht Frankfurt vs Koln (Sat, 17 Oct 1:30 AM)
    {
        "liga": "GERMANY BUNDESLIGA",
        "waktu": "01:30",
        "home": "Eintracht Frankfurt",
        "away": "FC Koln",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 3.5, "over": 2.10, "under": 1.75},
            {"line": 3.0, "over": 1.70, "under": 2.15},
            {"line": 4.0, "over": 2.60, "under": 1.50},
        ],
    },
    # Elversberg vs Augsburg (Sat, 17 Oct 8:30 PM)
    {
        "liga": "GERMANY BUNDESLIGA 2",
        "waktu": "20:30",
        "home": "Elversberg",
        "away": "Augsburg",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 3.5, "over": 2.15, "under": 1.71},
            {"line": 3.0, "over": 1.75, "under": 2.10},
            {"line": 4.0, "over": 2.60, "under": 1.50},
        ],
    },
    # Villarreal vs Elche (Sat, 17 Oct 9:15 PM)
    {
        "liga": "SPAIN LA LIGA",
        "waktu": "21:15",
        "home": "Villarreal",
        "away": "Elche",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 3.5, "over": 2.10, "under": 1.71},
            {"line": 3.0, "over": 1.70, "under": 2.15},
            {"line": 4.0, "over": 2.60, "under": 1.50},
        ],
    },
    # Bayern Munich vs RB Leipzig (Sat, 17 Oct 11:30 PM)
    {
        "liga": "GERMANY BUNDESLIGA",
        "waktu": "23:30",
        "home": "Bayern Munich",
        "away": "RB Leipzig",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 4.5, "over": 2.05, "under": 1.85},
            {"line": 4.0, "over": 1.70, "under": 2.10},
            {"line": 3.5, "over": 1.45, "under": 2.85},
        ],
    },
    # Bayer Leverkusen vs Freiburg (Sun, 18 Oct 8:30 PM)
    {
        "liga": "GERMANY BUNDESLIGA",
        "waktu": "20:30",
        "home": "Bayer Leverkusen",
        "away": "Freiburg",
        "is_live": False,
        "odds_home": 0, "odds_draw": 0, "odds_away": 0,
        "ou_lines": [
            {"line": 3.5, "over": 2.05, "under": 1.70},
            {"line": 3.0, "over": 1.65, "under": 2.25},
            {"line": 4.0, "over": 2.50, "under": 1.55},
        ],
    },
]

with open("output/match_full.json", "w", encoding="utf-8") as f:
    json.dump(dummy, f, indent=2, ensure_ascii=False)

print(f"✅ Dummy dibuat: {len(dummy)} match")
print("✅ Disimpan: output/match_full.json")
