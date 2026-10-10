with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "continue" di line 957 (index 956)
target = None
for i, l in enumerate(lines):
    if l.strip() == "continue" and i > 945 and i < 965:
        # Cek konteks — apakah setelah override
        konteks = "".join(lines[max(0, i-15):i])
        if "top_ou_m" in konteks or "override" in konteks.lower():
            target = i
            break

if target is None:
    print("❌ 'continue' tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    print(f"   {lines[target].rstrip()}")
    
    # Cek 5 baris setelah
    print(f"\n5 baris setelahnya:")
    for i in range(target+1, min(target+6, len(lines))):
        print(f"  {i+1}: {lines[i].rstrip()}")
    
    # Hapus continue
    del lines[target]
    print(f"\n🗑️ 'continue' dihapus")
    
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
