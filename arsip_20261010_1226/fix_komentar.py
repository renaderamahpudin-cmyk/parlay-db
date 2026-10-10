with open("scripts/parlay_builder_v3.py", "r") as f:
    kode = f.read()

# Ubah komentar
old = "# ALTERNATIF (O/U)"
new = "# PICK (O/U)"

count = kode.count(old)
if count > 0:
    kode = kode.replace(old, new)
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.write(kode)
    print(f"✅ Komentar diubah: {count} kali")
else:
    print("⚠️ Komentar tidak ketemu")
