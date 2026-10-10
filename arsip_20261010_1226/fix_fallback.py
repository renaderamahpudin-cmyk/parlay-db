with open("scripts/parlay_builder_v3.py", "r") as f:
    kode = f.read()

# Cari blok yang bermasalah
old = '''        if not kandidat_scored:
            return None
        
        # Sort: value_gap tertinggi dulu, kalau sama confidence tertinggi
        kandidat_scored.sort(key=lambda x: (-x["value_gap"], -x["confidence"]))
        best = kandidat_scored[0]'''

new = '''        if not kandidat_scored:
            # FALLBACK: panggil bandingkan_opsi_2 dari market
            _t1x2, _tou, _titik = None, None, None
            if ou_lines:
                try:
                    _t1x2, _tou, _titik = bandingkan_opsi_2(
                        gol_pairs=gol_pairs,
                        ou_lines=ou_lines,
                        odds_home=odds_home,
                        odds_draw=odds_draw,
                        odds_away=odds_away,
                        home_win_rate=win_rate,
                        away_win_rate=(100 - win_rate - draw_rate),
                        draw_rate=draw_rate,
                    )
                except Exception:
                    _tou = None
            
            if _tou:
                kandidat_scored = [{
                    "jenis": "OU",
                    "pick": _tou["pick"],
                    "confidence": _tou["prob"],
                    "alasan": f"Market: {_tou['pick']}",
                    "value_gap": _tou["gap"],
                    "odds_real": _tou["odds"],
                }]
            else:
                return None
        
        # Sort: value_gap tertinggi dulu, kalau sama confidence tertinggi
        kandidat_scored.sort(key=lambda x: (-x["value_gap"], -x["confidence"]))
        best = kandidat_scored[0]'''

if old in kode:
    kode = kode.replace(old, new, 1)
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.write(kode)
    print("✅ Fallback ditambah")
else:
    print("⚠️ Blok tidak ketemu, coba cari variasi")
    import re
    # Cari pola yang mirip
    pattern = r'if not kandidat_scored:\s*\n\s*return None'
    if re.search(pattern, kode):
        print("   Ketemu versi regex")
        kode = re.sub(pattern, new, kode, count=1)
        with open("scripts/parlay_builder_v3.py", "w") as f:
            f.write(kode)
        print("   ✅ Sudah diperbaiki")

# Verifikasi
import subprocess
result = subprocess.run(
    ["python3", "-c", "import ast; ast.parse(open('scripts/parlay_builder_v3.py').read())"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("✅ File VALID!")
else:
    print(f"❌ Error: {result.stderr}")
