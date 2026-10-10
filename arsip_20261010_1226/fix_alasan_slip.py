with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari print alasan di bikin_slip_tier (yang "Over 2.5: 60% dari H2H")
targets = []
for i, l in enumerate(lines):
    if "pick_alasan" in l and "print" in l:
        targets.append(i)

print(f"Ketemu {len(targets)} print alasan:")
for t in targets:
    print(f"  Line {t+1}: {lines[t].rstrip()[:80]}")

if not targets:
    print("❌ Tidak ketemu")
else:
    # Fix semua print alasan
    for t in reversed(targets):  # dari belakang biar index nggak shift
        # Dapatkan indentasi
        indent = " " * (len(lines[t]) - len(lines[t].lstrip()))
        
        # Cek apakah sudah di-patch
        konteks = "".join(lines[max(0, t-5):t])
        if "pick_now" in konteks or "top_ou_a" in konteks:
            print(f"  ✅ Line {t+1} sudah di-patch, skip")
            continue
        
        # Ganti dengan print alasan baru
        new_print = (
            f'{indent}# Alasan sesuai pick (dari market)\n'
            f'{indent}pick_now = m.get("pick", "")\n'
            f'{indent}if pick_now.startswith("OVER") or pick_now.startswith("UNDER"):\n'
            f'{indent}    top_ou_a = m.get("top_ou")\n'
            f'{indent}    if top_ou_a:\n'
            f'{indent}        print(f"   └─ {{top_ou_a[\'pick\']}}: prob {{top_ou_a[\'prob\']}}% | gap {{top_ou_a[\'gap\']:+}}%")\n'
            f'{indent}    else:\n'
            f'{indent}        print(f"   └─ {{m[\'pick_alasan\']}}")\n'
            f'{indent}else:\n'
            f'{indent}    print(f"   └─ {{m[\'pick_alasan\']}}")\n'
        )
        
        lines[t] = new_print
        print(f"  ✅ Line {t+1} diganti")

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
