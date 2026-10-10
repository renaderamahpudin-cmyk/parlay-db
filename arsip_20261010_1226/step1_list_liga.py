"""
Step 1: Kumpulkan liga unik dari best_pick
"""
import json

with open("output/best_pick.json") as f:
    picks = json.load(f)

ligas = set(p["liga"] for p in picks)
print(f"Total liga unik: {len(ligas)}")
print("=" * 60)
for l in sorted(ligas):
    print(f"  - {l}")

# Simpan
with open("output/liga_unik.json", "w") as f:
    json.dump(sorted(ligas), f, indent=2)
print(f"\n💾 Disimpan: output/liga_unik.json")
