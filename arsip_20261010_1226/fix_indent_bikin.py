with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "def bikin_slip_tier"
target = None
for i, l in enumerate(lines):
    if "def bikin_slip_tier" in l:
        target = i
        break

if target is None:
    print("❌ Fungsi tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    
    # Cari akhir fungsi (sampai "return slip" + beberapa baris)
    end = target
    for j in range(target + 1, min(target + 60, len(lines))):
        if "return slip" in lines[j]:
            # Cari akhir blok return (sampai baris kosong berikutnya)
            for k in range(j+1, min(j+5, len(lines))):
                if lines[k].strip() == "":
                    end = k - 1
                    break
            break
        end = j
    
    print(f"   Akhir fungsi: line {end+1}")
    print(f"   Total baris: {end - target + 1}")
    
    # Ganti dengan fungsi baru yang BERSIH
    indent = " " * (len(lines[target]) - len(lines[target].lstrip()))
    
    new_func = [
        f'{indent}def bikin_slip_tier(tim_list, nama, n_min=2, n_max=5):\n',
        f'{indent}    """Bikin slip dari 1 tier. Hanya gap >= 5%."""\n',
        f'{indent}    # FILTER: cuma gap >= 5%\n',
        f'{indent}    filtered = [m for m in tim_list if m.get("value_gap", 0) >= 5]\n',
        f'{indent}    \n',
        f'{indent}    if len(filtered) < n_min:\n',
        f'{indent}        return None\n',
        f'{indent}    \n',
        f'{indent}    n = min(n_max, len(filtered))\n',
        f'{indent}    slip = sorted(filtered, key=lambda x: -x.get("pick_conf", 0))[:n]\n',
        f'{indent}    \n',
        f'{indent}    total_odds = 1.0\n',
        f'{indent}    for p in slip:\n',
        f'{indent}        total_odds *= p.get("pick_odds", 1)\n',
        f'{indent}    \n',
        f'{indent}    print(f"\\n{{chr(61)*60}}")\n',
        f'{indent}    print(f"🎯 {{nama}} ({{n}} MATCH)")\n',
        f'{indent}    print(f"{{chr(61)*60}}")\n',
        f'{indent}    \n',
        f'{indent}    for i, m in enumerate(slip, 1):\n',
        f'{indent}        jenis = m.get("pick_jenis", "")\n',
        f'{indent}        emoji = {{"1X2": "🏠", "OU": "⚽", "BTTS": "🥅"}}.get(jenis, "🎯")\n',
        f'{indent}        print(f"\\n{{i}}. [{{m[\'liga\']}}]")\n',
        f'{indent}        print(f"   {{m[\'home\']}} vs {{m[\'away\']}} ({{m[\'waktu\']}})")\n',
        f'{indent}        print(f"   H2H: {{m[\'h2h\']}}x | Skor: {{m[\'skor\']}} | {{m[\'tier\']}}")\n',
        f'{indent}        print(f"   {{emoji}} {{m[\'pick\']}} ({{m[\'pick_conf\']}}%) | odds {{m.get(\'pick_odds\', 0)}}")\n',
        f'{indent}        print(f"   └─ gap {{m.get(\'value_gap\', 0):+.1f}}% | {{m.get(\'kategori_gap\', \'?\')}}")\n',
        f'{indent}    \n',
        f'{indent}    potensi = 100_000 * total_odds\n',
        f'{indent}    print(f"\\n💰 Total Odds: {{total_odds:.2f}}")\n',
        f'{indent}    print(f"💰 Modal: Rp 100,000")\n',
        f'{indent}    print(f"💰 Potensi: Rp {{potensi:,.0f}}")\n',
        f'{indent}    \n',
        f'{indent}    return slip\n',
    ]
    
    lines[target:end+1] = new_func
    
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.writelines(lines)
    print(f"✅ Fungsi bikin_slip_tier di-replace")

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
