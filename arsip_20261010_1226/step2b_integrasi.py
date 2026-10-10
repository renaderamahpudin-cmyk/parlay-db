with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "stats = analisa(" di main
target = None
for i, l in enumerate(lines):
    if "stats = analisa(" in l:
        target = i
        break

if target is None:
    print("❌ 'stats = analisa(' tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    
    # Cari akhir pemanggilan analisa (baris tutup ")")
    end_call = None
    for j in range(target, min(target + 20, len(lines))):
        if lines[j].strip() == ")" or lines[j].strip() == "),":
            end_call = j
            break
        # Cek juga kalau ada ")" di akhir baris
        if lines[j].rstrip().endswith(")") and j > target:
            end_call = j
            break
    
    if end_call is None:
        print("❌ Akhir pemanggilan tidak ketemu")
    else:
        print(f"   Akhir pemanggilan: line {end_call+1}")
        print(f"   {lines[end_call].rstrip()}")
        
        # Cek apakah sudah ada override
        konteks = "".join(lines[end_call:end_call+30])
        if "override_pick" in konteks or "pick_dari_market" in konteks:
            print("✅ Override sudah ada")
        else:
            # Cari indentasi di dalam main
            indent = " " * (len(lines[target]) - len(lines[target].lstrip()))
            
            # Kode override
            kode_override = [
                f'\n',
                f'{indent}# ===== OVERRIDE PICK DARI MARKET =====\n',
                f'{indent}if stats is not None:\n',
                f'{indent}    top_ou_m = stats.get("top_ou")\n',
                f'{indent}    titik_m = stats.get("titik_buta")\n',
                f'{indent}    ou_lines_m = m.get("ou_lines", [])\n',
                f'{indent}    \n',
                f'{indent}    # Cek apakah 2.5 ada di market\n',
                f'{indent}    has_25 = any(abs(ou.get("line", 0) - 2.5) < 0.01 for ou in ou_lines_m)\n',
                f'{indent}    \n',
                f'{indent}    if has_25 and titik_m:\n',
                f'{indent}        # 2.5 ada — pakai arah dari titik buta\n',
                f'{indent}        for ou in ou_lines_m:\n',
                f'{indent}            if abs(ou.get("line", 0) - 2.5) < 0.01:\n',
                f'{indent}                if titik_m["over_rate"] > 50:\n',
                f'{indent}                    stats["pick"] = "OVER 2.5"\n',
                f'{indent}                    stats["pick_odds"] = ou.get("over", 0)\n',
                f'{indent}                    stats["pick_conf"] = titik_m["over_rate"]\n',
                f'{indent}                else:\n',
                f'{indent}                    stats["pick"] = "UNDER 2.5"\n',
                f'{indent}                    stats["pick_odds"] = ou.get("under", 0)\n',
                f'{indent}                    stats["pick_conf"] = 100 - titik_m["over_rate"]\n',
                f'{indent}                stats["pick_jenis"] = "OU"\n',
                f'{indent}                break\n',
                f'{indent}    elif top_ou_m and top_ou_m.get("gap", 0) >= 5:\n',
                f'{indent}        # 2.5 nggak ada — pakai top_ou dari market\n',
                f'{indent}        stats["pick"] = top_ou_m["pick"]\n',
                f'{indent}        stats["pick_odds"] = top_ou_m["odds"]\n',
                f'{indent}        stats["pick_conf"] = top_ou_m["prob"]\n',
                f'{indent}        stats["pick_jenis"] = "OU"\n',
            ]
            
            # Sisipkan setelah pemanggilan analisa
            lines[end_call+1:end_call+1] = kode_override
            
            with open("scripts/parlay_builder_v3.py", "w") as f:
                f.writelines(lines)
            
            print(f"✅ Override pick ditambah di line {end_call+2}")

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
