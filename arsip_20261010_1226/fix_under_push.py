with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# ===== FIX 1: Fungsi bandingkan_opsi_2 (line 853) =====
# Cari blok: over_count = ... ; under_prob = 100 - over_prob
target = None
for i, l in enumerate(lines):
    if "under_prob = 100 - over_prob" in l:
        # Ambil yang kedua (fungsi _2)
        if i > 800:
            target = i
            break

if target is None:
    print("❌ Tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    print(f"   {lines[target].rstrip()}")
    
    # Cek 3 baris sebelum — cari over_count
    start = None
    for j in range(target-5, target+1):
        if "over_count = sum" in lines[j]:
            start = j
            break
    
    if start is None:
        print("❌ 'over_count' tidak ketemu")
    else:
        print(f"   over_count di line {start+1}")
        
        # Dapatkan indentasi
        indent = " " * (len(lines[start]) - len(lines[start].lstrip()))
        
        # Ganti blok dari start sampai target
        # Blok lama:
        #   over_count = sum(1 for g in total_gols if g > line)
        #   over_prob = (over_count / n) * 100
        #   under_prob = 100 - over_prob
        
        # Blok baru:
        new_block = [
            f'{indent}over_count = sum(1 for g in total_gols if g > line)\n',
            f'{indent}under_count = sum(1 for g in total_gols if g < line)\n',
            f'{indent}push_count = sum(1 for g in total_gols if g == line)\n',
            f'{indent}over_prob = (over_count / n) * 100\n',
            f'{indent}under_prob = (under_count / n) * 100\n',
            f'{indent}push_prob = (push_count / n) * 100\n',
        ]
        
        # Replace dari start sampai target
        lines[start:target+1] = new_block
        print(f"✅ Fix blok: line {start+1} s/d {target+1}")

with open("scripts/parlay_builder_v3.py", "w") as f:
    f.writelines(lines)

# ===== FIX 2: Value Gap dengan Push =====
with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "under_gap = under_prob - (100 / under_odds)" (yang di _2)
target_gap = None
for i, l in enumerate(lines):
    if "under_gap = under_prob" in l and i > 800:
        target_gap = i
        break

if target_gap is None:
    print("⚠️ under_gap tidak ketemu")
else:
    print(f"\n✅ under_gap di line {target_gap+1}")
    
    # Cek apakah sudah ada "push_prob" di sekitar
    konteks = "".join(lines[max(0, target_gap-3):target_gap+5])
    if "push_prob" in konteks and "over_gap +=" in konteks:
        print("✅ Push sudah di-handle")
    else:
        indent = " " * (len(lines[target_gap]) - len(lines[target_gap].lstrip()))
        
        # Tambah handling push setelah under_gap
        tambahan = [
            f'\n',
            f'{indent}# Handle push untuk line .0 (3.0, 4.0, dst)\n',
            f'{indent}if push_prob > 0:\n',
            f'{indent}    over_gap += push_prob / 2\n',
            f'{indent}    under_gap += push_prob / 2\n',
        ]
        
        lines[target_gap+1:target_gap+1] = tambahan
        print(f"✅ Push handling ditambah di line {target_gap+2}")

with open("scripts/parlay_builder_v3.py", "w") as f:
    f.writelines(lines)

# Verifikasi
import subprocess
result = subprocess.run(
    ["python3", "-c", "import ast; ast.parse(open('scripts/parlay_builder_v3.py').read())"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("\n✅ File VALID!")
else:
    print(f"\n❌ Error: {result.stderr}")
