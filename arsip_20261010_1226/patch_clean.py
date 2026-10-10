with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "if top_1x2_m:" di print best pick
start_utama = None
for i, l in enumerate(lines):
    if "# UTAMA (1X2)" in l:
        start_utama = i
        break

if start_utama is None:
    print("❌ UTAMA tidak ketemu")
else:
    print(f"✅ UTAMA di line {start_utama+1}")
    
    # Cari akhir blok UTAMA (sampai blank line atau next section)
    end_utama = start_utama
    for j in range(start_utama, min(start_utama + 10, len(lines))):
        # Stop kalau ketemu "# ALTERNATIF"
        if "# ALTERNATIF" in lines[j]:
            end_utama = j - 1
            break
        end_utama = j
    
    print(f"   Akhir blok UTAMA: line {end_utama+1}")
    
    # Tampilkan isi blok
    print(f"\n   Isi blok UTAMA (akan dihapus):")
    for k in range(start_utama, end_utama+1):
        print(f"     {k+1}: {lines[k].rstrip()}")
    
    # Hapus blok UTAMA
    del lines[start_utama:end_utama+1]
    print(f"\n   🗑️ Blok UTAMA dihapus ({end_utama-start_utama+1} baris)")

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
