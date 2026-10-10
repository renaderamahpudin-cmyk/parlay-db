"""
TEST 7: Eksplorasi squad FULL (5 kelompok)
"""
import json

with open("fotmob_barcelona.json", "r", encoding="utf-8") as f:
    data = json.load(f)

squad = data.get("squad", {}).get("squad", [])

print("=" * 70)
print("TEST 7: SQUAD FULL")
print("=" * 70)
print(f"Total kelompok: {len(squad)}\n")

for i, grup in enumerate(squad):
    title = grup.get("title", "?")
    members = grup.get("members", [])
    print(f"\n[{i}] {title.upper()} — {len(members)} orang")
    
    # Tampilkan 3 orang pertama
    for j, m in enumerate(members[:3]):
        if isinstance(m, dict):
            print(f"     {j+1}. {m.get('name', '?')} | {m.get('role', '?')} | "
                  f"age: {m.get('age', '?')} | inj: {m.get('injuryInformation', '-')}")
    
    # Cek apakah ada info cedera
    if members and isinstance(members[0], dict):
        keys = list(members[0].keys())
        print(f"     Keys: {keys}")

# ===== CEK PLAYER SAMPLE =====
print(f"\n{'─'*70}")
print("📋 SAMPLE PEMAIN LENGKAP (pertama dari tiap grup):")
print(f"{'─'*70}")

for i, grup in enumerate(squad):
    members = grup.get("members", [])
    if members and isinstance(members[0], dict):
        print(f"\n[{grup.get('title', '?')}]")
        for k, v in members[0].items():
            print(f"   {k}: {str(v)[:80]}")

print("\n" + "=" * 70)
