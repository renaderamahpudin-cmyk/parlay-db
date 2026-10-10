"""
Update mapping_liga.json dengan ID yang benar
"""
import json

MAPPING = {
    "ENGLISH PREMIER LEAGUE": {"id": 47, "negara": "ENG"},
    "ITALY SERIE A": {"id": 55, "negara": "ITA"},
    "FRANCE LIGUE 1": {"id": 53, "negara": "FRA"},
    "NETHERLANDS EREDIVISIE": {"id": 57, "negara": "NED"},
    "TURKIYE SUPER LEAGUE": {"id": 71, "negara": "TUR"},
    "SWEDEN ALLSVENSKAN": {"id": 67, "negara": "SWE"},
    "AUSTRIA BUNDESLIGA": {"id": 38, "negara": "AUT"},
    "USA MAJOR LEAGUE SOCCER": {"id": 130, "negara": "USA"},
}

with open("output/mapping_liga.json", "w") as f:
    json.dump(MAPPING, f, indent=2, ensure_ascii=False)

print(f"✅ Mapping updated: {len(MAPPING)} liga")
for liga, info in MAPPING.items():
    print(f"  {liga} → ID {info['id']}")
