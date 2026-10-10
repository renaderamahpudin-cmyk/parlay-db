with open("scripts/parlay_builder_v3.py", "r") as f:
    kode = f.read()

# Cari fungsi bikin_slip_tier
import re

# Cari "def bikin_slip_tier"
if "def bikin_slip_tier" in kode:
    # Cari awal fungsi
    start = kode.find("def bikin_slip_tier")
    # Cari akhir fungsi (def berikutnya)
    next_def = kode.find("def ", start + 10)
    if next_def == -1:
        next_def = len(kode)
    
    old_func = kode[start:next_def]
    
    # Fungsi baru dengan filter gap
    new_func = '''def bikin_slip_tier(tim_list, nama, n_min=2, n_max=5):
    """Bikin slip dari 1 tier dengan filter gap positif"""
    # FILTER: cuma gap >= 5% (bukan negatif)
    tim_list_filtered = [m for m in tim_list if m.get("value_gap", 0) >= 5]
    
    if len(tim_list_filtered) < n_min:
        print(f"\\n⚠️ {nama}: tidak cukup match gap >= 5% (ada {len(tim_list_filtered)})")
        return None
    
    n = min(n_max, len(tim_list_filtered))
    slip = sorted(tim_list_filtered, key=lambda x: -x.get("pick_conf", 0))[:n]
    
    total_odds = 1.0
    for p in slip:
        total_odds *= p.get("pick_odds", 1)
    
    print(f"\\n{'='*60}")
    print(f"🎯 {nama} ({n} MATCH)")
    print(f"{'='*60}")
    
    for i, m in enumerate(slip, 1):
        jenis = m.get("pick_jenis", "")
        emoji = {"1X2": "🏠", "OU": "⚽", "BTTS": "🥅"}.get(jenis, "🎯")
        print(f"\\n{i}. [{m['liga']}]")
        print(f"   {m['home']} vs {m['away']} ({m['waktu']})")
        print(f"   H2H: {m['h2h']}x | Skor: {m['skor']} | {m['tier']}")
        print(f"   {emoji} {m['pick']} ({m['pick_conf']}%) | odds {m.get('pick_odds', 0)}")
        print(f"   └─ gap {m.get('value_gap', 0):+.1f}% | {m.get('kategori_gap', '?')}")
    
    potensi = 100_000 * total_odds
    print(f"\\n💰 Total Odds: {total_odds:.2f}")
    print(f"💰 Modal: Rp 100,000")
    print(f"💰 Potensi: Rp {potensi:,.0f}")
    
    return slip

'''
    
    kode = kode.replace(old_func, new_func)
    
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.write(kode)
    print("✅ Fungsi bikin_slip_tier diupdate dengan filter gap")
else:
    print("⚠️ Fungsi tidak ketemu")
