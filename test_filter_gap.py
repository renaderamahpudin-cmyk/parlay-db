"""
TEST: Filter gap >= 5% — script terpisah, nggak sentuh builder
"""
import json

with open("output/best_pick.json") as f:
    picks = json.load(f)

print("=" * 70)
print("🔍 TEST FILTER GAP")
print("=" * 70)
print(f"Total pick: {len(picks)}\n")

# Filter
lolos = [p for p in picks if p.get("value_gap", 0) >= 5]
gagal = [p for p in picks if p.get("value_gap", 0) < 5]

print(f"✅ LOLOS (gap >= 5%): {len(lolos)}")
print(f"❌ SKIP (gap < 5%):   {len(gagal)}\n")

print("=" * 70)
print("✅ YANG LOLOS — Masuk Slip")
print("=" * 70)
for p in sorted(lolos, key=lambda x: -x.get("value_gap", 0)):
    gap = p.get("value_gap", 0)
    conf = p.get("pick_conf", 0)
    tier = p.get("tier", "?")
    print(f"\n{p['home']} vs {p['away']}")
    print(f"  Pick: {p['pick']} ({conf}%)")
    print(f"  Gap:  {gap:+.1f}% | Tier: {tier} | Skor: {p.get('skor', 0)}")

print("\n" + "=" * 70)
print("❌ YANG SKIP — JANGAN Masuk Slip")
print("=" * 70)
for p in sorted(gagal, key=lambda x: x.get("value_gap", 0)):
    gap = p.get("value_gap", 0)
    print(f"\n{p['home']} vs {p['away']}")
    print(f"  Pick: {p['pick']}")
    print(f"  Gap:  {gap:+.1f}% ← ❌ SKIP")

print("\n" + "=" * 70)
print(f"Total lolos: {len(lolos)}")
print(f"Total skip:  {len(gagal)}")
print("=" * 70)
