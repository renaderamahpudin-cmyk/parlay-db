with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari baris print TITIK BUTA
target = None
for i, l in enumerate(lines):
    if "TITIK BUTA" in l and "print" in l:
        target = i
        break

if target is None:
    print("❌ Print TITIK BUTA tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    print(f"   {lines[target].rstrip()}")
    
    # Cek 2 baris sebelum — apakah ada "if titik_m:"
    if_start = None
    for j in range(max(0, target-5), target+1):
        if "if titik_m:" in lines[j]:
            if_start = j
            break
    
    if if_start is None:
        print("⚠️ 'if titik_m:' tidak ketemu — cari manual")
    else:
        print(f"   'if titik_m:' di line {if_start+1}")
        
        # Dapatkan indentasi
        indent = " " * (len(lines[if_start]) - len(lines[if_start].lstrip()))
        body_indent = indent + "    "
        
        # Cari akhir blok (baris dengan indent <= indent)
        end_idx = target
        for j in range(target + 1, min(target + 15, len(lines))):
            if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= len(indent):
                end_idx = j - 1
                break
            end_idx = j
        
        print(f"   Akhir blok: line {end_idx+1}")
        
        # Blok baru — 5 zona
        new_block = [
            f'{indent}if titik_m:\n',
            f'{body_indent}status_market = "ada di market" if titik_m.get("ada_di_market") else "TIDAK ADA di market"\n',
            f'{body_indent}over_rate = titik_m["over_rate"]\n',
            f'{body_indent}under_rate = 100 - over_rate\n',
            f'\n',
            f'{body_indent}# ===== 5 ZONA =====\n',
            f'{body_indent}if over_rate >= 70:\n',
            f'{body_indent}    label = f"OVER 2.5 = {{over_rate:.0f}}% 🔥 KUAT"\n',
            f'{body_indent}    info = "Jelas over — aman"\n',
            f'{body_indent}elif over_rate >= 60:\n',
            f'{body_indent}    label = f"OVER 2.5 = {{over_rate:.0f}}% ⚠️ MEPET"\n',
            f'{body_indent}    info = "1 gol bisa ubah — cek line 2.75 / 3.0"\n',
            f'{body_indent}elif over_rate >= 40:\n',
            f'{body_indent}    label = f"NETRAL = O{{over_rate:.0f}}% / U{{under_rate:.0f}}% 🟡"\n',
            f'{body_indent}    info = "Tidak jelas — hindari 2.5"\n',
            f'{body_indent}elif over_rate >= 30:\n',
            f'{body_indent}    label = f"UNDER 2.5 = {{under_rate:.0f}}% ⚠️ MEPET"\n',
            f'{body_indent}    info = "1 gol bisa ubah — cek line 2.75 / 3.0"\n',
            f'{body_indent}else:\n',
            f'{body_indent}    label = f"UNDER 2.5 = {{under_rate:.0f}}% 🔥 KUAT"\n',
            f'{body_indent}    info = "Jelas under — aman"\n',
            f'\n',
            f'{body_indent}print(f"    📌 TITIK BUTA: {{label}} ({{status_market}})")\n',
            f'{body_indent}print(f"       💡 {{info}}")\n',
        ]
        
        # Replace blok
        lines[if_start:end_idx+1] = new_block
        
        with open("scripts/parlay_builder_v3.py", "w") as f:
            f.writelines(lines)
        
        print(f"✅ Titik buta 5 zona ditambah")

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
