with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari semua "OVERRIDE PICK DARI MARKET"
targets = []
for i, l in enumerate(lines):
    if "OVERRIDE PICK DARI MARKET" in l:
        targets.append(i)

print(f"Ketemu {len(targets)} blok OVERRIDE:")
for t in targets:
    print(f"  Line {t+1}: {lines[t].rstrip()}")

if len(targets) > 1:
    # Hapus yang kedua
    start = targets[1]
    print(f"\n🗑️ Hapus blok kedua mulai line {start+1}")
    
    # Cari akhir blok (sampai baris dengan indent <= 4)
    end = start
    for j in range(start + 1, min(start + 30, len(lines))):
        if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= 4:
            end = j - 1
            break
        end = j
    
    print(f"   Akhir blok: line {end+1}")
    print(f"   Hapus {end - start + 1} baris")
    
    # Hapus
    del lines[start:end+1]
    
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.writelines(lines)
    print("✅ Duplikat dihapus")

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
