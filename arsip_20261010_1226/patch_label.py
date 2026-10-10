with open("scripts/parlay_builder_v3.py", "r") as f:
    kode = f.read()

# Ubah label ALTERNATIF (O/U) jadi PICK
old_label = 'ALTERNATIF (O/U):'
new_label = 'PICK (O/U):'

if old_label in kode:
    kode = kode.replace(old_label, new_label)
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.write(kode)
    print(f"✅ Label diubah: '{old_label}' → '{new_label}'")
else:
    print("⚠️ Label ALTERNATIF tidak ketemu")

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
