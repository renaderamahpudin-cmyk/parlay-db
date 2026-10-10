with open("scripts/parlay_builder_v3.py", "r") as f:
    kode = f.read()

# Cari print titik buta
old_print = '''if titik_m:
    status_market = "ada" if titik_m.get("ada_di_market") else "TIDAK ADA"
    print(f"    📌 TITIK BUTA: O2.5 = {titik_m['over_rate']:.0f}% ({status_market} di market)")'''

new_print = '''if titik_m:
    status_market = "ada" if titik_m.get("ada_di_market") else "TIDAK ADA"
    over_rate = titik_m['over_rate']
    if over_rate > 50:
        label_titik = "OVER 2.5"
        prob_titik = over_rate
    else:
        label_titik = "UNDER 2.5"
        prob_titik = 100 - over_rate
    print(f"    📌 TITIK BUTA: {label_titik} = {prob_titik:.0f}% ({status_market} di market)")'''

if old_print in kode:
    kode = kode.replace(old_print, new_print)
    print("✅ Titik buta diubah jadi NETRAL (OVER/UNDER)")
else:
    print("⚠️ Print titik buta tidak ketemu")
    # Coba cari variasi
    import re
    pattern = r'print\(f"    📌 TITIK BUTA: O2\.5 = \{titik_m\[.over_rate.\]:\.0f\}% \(\{status_market\} di market\)"\)'
    match = re.search(pattern, kode)
    if match:
        print(f"   Ketemu versi alternatif")
    else:
        print("   Tidak ketemu sama sekali")

with open("scripts/parlay_builder_v3.py", "w") as f:
    f.write(kode)

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
