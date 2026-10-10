with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari "with open(\"output/best_pick.json\"" di line 1250-1260
target = None
for i, l in enumerate(lines):
    if 'output/best_pick.json' in l and 'with open' in l and i > 1240 and i < 1270:
        target = i
        break

if target is None:
    print("❌ Tidak ketemu")
else:
    print(f"✅ Ketemu di line {target+1}")
    indent = len(lines[target]) - len(lines[target].lstrip())
    print(f"   Indentasi sekarang: {indent} spasi")
    print(f"   Isi: {lines[target].rstrip()}")
    
    # Cek baris sebelumnya
    print(f"\n   Line {target}: {lines[target-1].rstrip()}")
    
    # Fix: pastikan indent 4 spasi (di dalam main)
    if indent != 4:
        lines[target] = "    " + lines[target].lstrip()
        print(f"   → Fixed ke 4 spasi")
        
        # Fix baris selanjutnya yang satu blok
        for j in range(target+1, min(target+10, len(lines))):
            l = lines[j]
            if l.strip() and (len(l) - len(l.lstrip())) > indent:
                # Kurangi selisih
                diff = (len(l) - len(l.lstrip())) - indent
                lines[j] = l[diff:]
        
        with open("scripts/parlay_builder_v3.py", "w") as f:
            f.writelines(lines)
        print("✅ File diperbaiki")

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
