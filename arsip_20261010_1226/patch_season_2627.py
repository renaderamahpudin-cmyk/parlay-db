with open("build_db.py", "r") as f:
    kode = f.read()

# Cek apakah sudah ada 2627
if '"2627"' in kode:
    print("✅ 2627 sudah ada")
else:
    # Cari SEASONS block
    old = '''SEASONS = [
    "0506", "0607", "0708", "0809", "0910",
    "1011", "1112", "1213", "1314", "1415",
    "1516", "1617", "1718", "1819", "1920",
    "2021", "2122", "2223", "2324", "2425", "2526",
]'''

    new = '''SEASONS = [
    "0506", "0607", "0708", "0809", "0910",
    "1011", "1112", "1213", "1314", "1415",
    "1516", "1617", "1718", "1819", "1920",
    "2021", "2122", "2223", "2324", "2425", "2526",
    "2627",  # Musim 2026/27 - TAMBAHAN
]'''

    if old in kode:
        kode = kode.replace(old, new)
        with open("build_db.py", "w") as f:
            f.write(kode)
        print("✅ Patch berhasil: 2627 ditambah")
    else:
        print("⚠️ Blok SEASONS tidak ketemu")
        print("   Cek manual: grep -A 8 '^SEASONS' build_db.py")

# Verifikasi
import subprocess
result = subprocess.run(
    ["python3", "-c", "import ast; ast.parse(open('build_db.py').read())"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("✅ File VALID!")
else:
    print(f"❌ Error: {result.stderr}")
