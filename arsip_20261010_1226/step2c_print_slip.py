with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari print slip — "🏠 HOME" atau "🏠 {m['pick']}"
target = None
for i, l in enumerate(lines):
    if "🏠 HOME" in l or ("🏠" in l and "m['pick']" in l):
        target = i
        break

if target is None:
    # Cari print di fungsi bikin_slip
    for i, l in enumerate(lines):
        if "bikin_slip" in l and "def " in l:
            # Cari di dalam fungsi
            for j in range(i, min(i + 50, len(lines))):
                if "emoji" in lines[j] and "pick" in lines[j]:
                    target = j
                    break
            break

if target is None:
    print("❌ Print slip tidak ketemu")
    print("   Coba cari manual: grep -n '🏠' scripts/parlay_builder_v3.py")
else:
    print(f"✅ Ketemu di line {target+1}")
    print(f"   {lines[target].rstrip()}")
    
    # Tampilkan 10 baris sekitar
    print(f"\nKonteks:")
    for i in range(max(0, target-5), min(target+10, len(lines))):
        print(f"  {i+1}: {lines[i].rstrip()}")
