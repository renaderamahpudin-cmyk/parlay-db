with open("scripts/parlay_builder_v3.py", "r") as f:
    kode = f.read()

# Turunkan MIN_CONF_PICK dari 60 ke 30
old = "MIN_CONF_PICK = 60"
new = "MIN_CONF_PICK = 30"

count = kode.count(old)
if count > 0:
    kode = kode.replace(old, new)
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.write(kode)
    print(f"✅ MIN_CONF_PICK diubah: 60 → 30 ({count} kali)")
else:
    print("⚠️ MIN_CONF_PICK = 60 tidak ketemu")
    # Coba cari yang lain
    import re
    matches = re.findall(r'MIN_CONF_PICK = \d+', kode)
    print(f"   Ditemukan: {matches}")

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
