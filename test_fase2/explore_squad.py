"""
TEST 6: Eksplorasi 'squad' dari Fotmob
"""
import json

# Load data yang sudah disimpan
with open("fotmob_barcelona.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=" * 60)
print("TEST 6: EKSPLORASI SQUAD")
print("=" * 60)

# ===== 1. Cek 'squad' =====
squad = data.get("squad", {})
print(f"\n📂 'squad' keys: {list(squad.keys())}")

for key in squad.keys():
    val = squad[key]
    if isinstance(val, list):
        print(f"\n   '{key}': list ({len(val)} items)")
        if len(val) > 0:
            print(f"   Sample item [0]:")
            item = val[0]
            if isinstance(item, dict):
                for k, v in item.items():
                    print(f"      {k}: {str(v)[:60]}")
            else:
                print(f"      {str(item)[:100]}")
    elif isinstance(val, dict):
        print(f"\n   '{key}': dict ({len(val)} keys)")
        for k in list(val.keys())[:10]:
            print(f"      {k}")

# ===== 2. Cek 'stats' =====
print(f"\n{'─'*60}")
print(f"📂 'stats' keys: {list(data.get('stats', {}).keys())}")

# ===== 3. Cek 'tabs' =====
print(f"\n{'─'*60}")
print(f"📂 'tabs' items:")
for i, tab in enumerate(data.get("tabs", [])):
    if isinstance(tab, dict):
        print(f"   [{i}] {tab.get('title', '-')} (type: {tab.get('type', '-')})")

print("\n" + "=" * 60)
