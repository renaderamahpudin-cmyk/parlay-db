"""Show O/U picks that pass the same filter used by the builder and slips."""
import json
from scripts.pick_policy import (
    MIN_OU_GAP,
    is_eligible_ou_pick,
    is_over_under_pick,
)

with open("output/best_pick.json") as f:
    picks = json.load(f)

def gap_for_sort(pick):
    try:
        return float(pick.get("value_gap"))
    except (TypeError, ValueError):
        return float("-inf")

print("=" * 70)
print("🔍 TEST FILTER GAP")
print("=" * 70)
print(f"Total pick: {len(picks)}\n")

# Filter
lolos = [p for p in picks if is_eligible_ou_pick(p)]
gagal = [p for p in picks if not is_eligible_ou_pick(p)]

print(f"✅ LOLOS (O/U, gap >= +{MIN_OU_GAP:.0f}%): {len(lolos)}")
skipped_non_ou = [
    p for p in gagal
    if str(p.get("pick_jenis") or "").strip().upper() != "OU"
    or not is_over_under_pick(p)
]
skipped_ou = [
    p for p in gagal
    if str(p.get("pick_jenis") or "").strip().upper() == "OU"
    and is_over_under_pick(p)
]
print(
    f"⏭️  DILEWATI: {len(skipped_non_ou)} bukan O/U; "
    f"{len(skipped_ou)} O/U tidak lolos gap/odds/data.\n"
)

print("=" * 70)
print("✅ YANG LOLOS — Masuk Slip")
print("=" * 70)
for p in sorted(lolos, key=gap_for_sort, reverse=True):
    gap = p.get("value_gap", 0)
    conf = p.get("pick_conf", 0)
    tier = p.get("tier", "?")
    print(f"\n{p['home']} vs {p['away']}")
    print(f"  Pick: {p['pick']} ({conf}%)")
    print(f"  Gap:  {gap:+.1f}% | Tier: {tier} | Skor: {p.get('skor', 0)}")

print("\n" + "=" * 70)
print(f"Total lolos: {len(lolos)}")
print(f"Total skip:  {len(gagal)}")
print("=" * 70)
