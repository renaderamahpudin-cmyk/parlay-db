with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "if not kandidat:" 
target = None
for i, l in enumerate(lines):
    if "if not kandidat:" in l:
        target = i
        break

if target is None:
    print("❌ 'if not kandidat' tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    
    # Cari "return None" setelahnya
    end = target
    for j in range(target, min(target + 5, len(lines))):
        if "return None" in lines[j]:
            end = j
            break
    
    print(f"   Blok: line {target+1} s/d {end+1}")
    
    # Ganti dengan komentar
    indent = " " * (len(lines[target]) - len(lines[target].lstrip()))
    
    new_block = [
        f'{indent}# KANDIDAT DIHAPUS — fokus O/U dari market\n',
        f'{indent}# (Bandingkan_opsi_2 dipanggil di bawah untuk pilih pick)\n',
    ]
    
    lines[target:end+1] = new_block
    print(f"✅ Blok 'if not kandidat' dihapus")

with open("scripts/parlay_builder_v3.py", "w") as f:
    f.writelines(lines)

# ===== Cari "if best["confidence"] < MIN_CONF_PICK" =====
with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

target2 = None
for i, l in enumerate(lines):
    if "MIN_CONF_PICK" in l and "best" in l.lower():
        target2 = i
        break

if target2 is None:
    for i, l in enumerate(lines):
        if "if best" in l and "confidence" in l:
            target2 = i
            break

if target2 is None:
    print("⚠️ Cek confidence best tidak ketemu")
else:
    print(f"✅ Cek confidence di line {target2+1}")
    print(f"   {lines[target2].rstrip()}")
    
    # Cari "return None" setelahnya
    end2 = target2
    for j in range(target2, min(target2 + 5, len(lines))):
        if "return None" in lines[j]:
            end2 = j
            break
    
    indent = " " * (len(lines[target2]) - len(lines[target2].lstrip()))
    
    new_block2 = [
        f'{indent}# Cek confidence DIHAPUS — confidence dari market (bandingkan_opsi_2)\n',
    ]
    
    lines[target2:end2+1] = new_block2
    print(f"✅ Blok cek confidence best dihapus")

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
