with open("scripts/parlay_builder_v3.py", "r") as f:
    lines = f.readlines()

# Cari print "UTAMA (1X2)"
target_utama = None
for i, l in enumerate(lines):
    if "UTAMA (1X2)" in l:
        target_utama = i
        break

if target_utama is None:
    print("❌ Print UTAMA (1X2) tidak ketemu")
else:
    print(f"✅ UTAMA (1X2) di line {target_utama+1}")
    print(f"   {lines[target_utama].rstrip()}")

# Cari print "ALTERNATIF (O/U)"
target_alternatif = None
for i, l in enumerate(lines):
    if "ALTERNATIF (O/U)" in l:
        target_alternatif = i
        break

if target_alternatif is None:
    print("❌ Print ALTERNATIF (O/U) tidak ketemu")
else:
    print(f"✅ ALTERNATIF (O/U) di line {target_alternatif+1}")
    print(f"   {lines[target_alternatif].rstrip()}")

# Tampilkan konteks print best pick
print(f"\n{'='*60}")
print("Konteks print best pick:")
for i in range(min(target_utama, target_alternatif)-5, 
               max(target_utama, target_alternatif)+10):
    if 0 <= i < len(lines):
        print(f"  {i+1}: {lines[i].rstrip()[:80]}")
