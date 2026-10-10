with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "if sinyal < 1:" atau "if sinyal < 2:"
target = None
for i, l in enumerate(lines):
    if "if sinyal <" in l:
        target = i
        break

if target is None:
    print("❌ Filter sinyal tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    print(f"   {lines[target].rstrip()}")
    
    # Cari "return None" setelahnya
    end = target
    for j in range(target, min(target + 5, len(lines))):
        if "return None" in lines[j]:
            end = j
            break
    
    print(f"   Blok: line {target+1} s/d {end+1}")
    
    # Hapus blok (ganti dengan komentar)
    indent = " " * (len(lines[target]) - len(lines[target].lstrip()))
    
    new_block = [
        f'{indent}# FILTER SINYAL DIHAPUS — fokus O/U\n',
        f'{indent}# (Sinyal kualitas cuma untuk 1X2 yang sudah dihapus)\n',
    ]
    
    lines[target:end+1] = new_block
    
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.writelines(lines)
    
    print(f"✅ Filter sinyal dihapus")

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
