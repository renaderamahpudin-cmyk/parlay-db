with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari print best pick di line 1024
target = None
for i, l in enumerate(lines):
    if "H2H:{" in l and "Skor:" in l and "m['pick']" in l:
        target = i
        break

if target is None:
    print("❌ Print best pick tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    print(f"   {lines[target].rstrip()}")
    
    # Cek 5 baris sebelum — apakah ada emoji assignment
    print(f"\nKonteks (line {target-3} s/d {target+3}):")
    for i in range(max(0, target-3), min(target+4, len(lines))):
        print(f"  {i+1}: {lines[i].rstrip()}")
    
    # Dapatkan indentasi
    indent = " " * (len(lines[target]) - len(lines[target].lstrip()))
    
    # Ganti print — pakai top_ou kalau ada
    new_print = (
        f'{indent}# Ambil pick dari top_ou kalau ada (override)\n'
        f'{indent}pick_display = m.get("pick", "?")\n'
        f'{indent}conf_display = m.get("pick_conf", 0)\n'
        f'{indent}odds_display = m.get("pick_odds", 0)\n'
        f'{indent}jenis_display = m.get("pick_jenis", "")\n'
        f'{indent}\n'
        f'{indent}# Kalau pick_jenis OU dan top_ou ada, pakai top_ou\n'
        f'{indent}if jenis_display == "OU" and m.get("top_ou"):\n'
        f'{indent}    pick_display = m["top_ou"]["pick"]\n'
        f'{indent}    conf_display = m["top_ou"]["prob"]\n'
        f'{indent}    odds_display = m["top_ou"]["odds"]\n'
        f'{indent}\n'
        f'{indent}print(f"    H2H:{{m[\'h2h\']}} Skor:{{m[\'skor\']}} Gol:{{m[\'gol_total\']}} | {{emoji}} {{pick_display}} {{conf_display}}% ({{odds_display}})")'
    )
    
    # Replace
    lines[target] = new_print + "\n"
    
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.writelines(lines)
    
    print(f"\n✅ Print best pick diupdate")

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
