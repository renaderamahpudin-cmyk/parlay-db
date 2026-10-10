with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "if not kandidat_scored:" yang indentasinya aneh (>16 spasi)
target = None
for i, l in enumerate(lines):
    if "if not kandidat_scored:" in l:
        indent = len(l) - len(l.lstrip())
        if indent > 16:
            target = i
            break

if target is None:
    print("❌ Tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    print(f"   Indentasi: {len(lines[target]) - len(lines[target].lstrip())} spasi")
    print(f"   Isi: {lines[target].rstrip()}")
    
    # Cari akhir blok fallback (sampai "return None" di dalam if atau "kandidat_scored = [{")
    end = target
    for j in range(target + 1, min(target + 40, len(lines))):
        l = lines[j]
        # Stop kalau ketemu "kandidat_scored.sort" atau "best = kandidat_scored"
        if "kandidat_scored.sort" in l or "best = kandidat_scored" in l:
            end = j - 1
            break
        end = j
    
    print(f"   Akhir blok: line {end+1}")
    
    # Ganti blok dengan indentasi benar (8 spasi untuk if, 12 untuk body)
    new_block = [
        '        if not kandidat_scored:\n',
        '            # FALLBACK: panggil bandingkan_opsi_2 dari market\n',
        '            _t1x2, _tou, _titik = None, None, None\n',
        '            if ou_lines:\n',
        '                try:\n',
        '                    _t1x2, _tou, _titik = bandingkan_opsi_2(\n',
        '                        gol_pairs=gol_pairs,\n',
        '                        ou_lines=ou_lines,\n',
        '                        odds_home=odds_home,\n',
        '                        odds_draw=odds_draw,\n',
        '                        odds_away=odds_away,\n',
        '                        home_win_rate=win_rate,\n',
        '                        away_win_rate=(100 - win_rate - draw_rate),\n',
        '                        draw_rate=draw_rate,\n',
        '                    )\n',
        '                except Exception:\n',
        '                    _tou = None\n',
        '\n',
        '            if _tou:\n',
        '                kandidat_scored = [{\n',
        '                    "jenis": "OU",\n',
        '                    "pick": _tou["pick"],\n',
        '                    "confidence": _tou["prob"],\n',
        '                    "alasan": f"Market: {_tou[\'pick\']}",\n',
        '                    "value_gap": _tou["gap"],\n',
        '                    "odds_real": _tou["odds"],\n',
        '                }]\n',
        '            else:\n',
        '                return None\n',
        '        \n',
    ]
    
    # Replace
    lines[target:end+1] = new_block
    print(f"✅ Blok fallback diganti (line {target+1} s/d {end+1})")

with open("scripts/parlay_builder_v3.py", "w") as f:
    f.writelines(lines)

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
