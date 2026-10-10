with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "stats.update(m)"
target = None
for i, l in enumerate(lines):
    if "stats.update(m)" in l:
        target = i
        break

if target is None:
    print("❌ 'stats.update(m)' tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    print(f"   {lines[target].rstrip()}")
    
    # Cek 3 baris sebelum — apakah ada "if stats is None"
    konteks = "".join(lines[max(0, target-5):target])
    if "if stats is None" in konteks:
        print("✅ Cek 'if stats is None' sudah ada")
    else:
        print("⚠️ Cek 'if stats is None' BELUM ada")
        
        # Dapatkan indentasi
        indent = " " * (len(lines[target]) - len(lines[target].lstrip()))
        
        # Sisipkan cek sebelum stats.update
        kode_cek = [
            f'{indent}if stats is None:\n',
            f'{indent}    continue\n',
            f'\n',
        ]
        
        lines[target:target] = kode_cek
        print(f"✅ Cek 'if stats is None' ditambah di line {target+1}")

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
