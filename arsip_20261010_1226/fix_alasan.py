with open("scripts/parlay_builder_v3.py", "r") as f:
    kode = f.read()

# Cari print alasan lama
old_alasan = """print(f"    └─ {m['pick_alasan']}")"""

new_alasan = """# Alasan sesuai pick
pick_now = m.get("pick", "")
if pick_now.startswith("OVER") or pick_now.startswith("UNDER"):
    # Ambil dari top_ou
    top_ou_a = m.get("top_ou")
    if top_ou_a:
        print(f"    └─ {top_ou_a['pick']}: prob {top_ou_a['prob']}% | gap {top_ou_a['gap']:+}%")
    else:
        print(f"    └─ {m['pick_alasan']}")
elif pick_now == "HOME" or pick_now == "AWAY" or pick_now == "DRAW":
    print(f"    └─ {pick_now}: prob {m.get('pick_conf', 0)}%")
else:
    print(f"    └─ {m['pick_alasan']}")"""

if old_alasan in kode:
    kode = kode.replace(old_alasan, new_alasan, 1)
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.write(kode)
    print("✅ Alasan diupdate")
else:
    print("⚠️ Print alasan tidak ketemu")

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
