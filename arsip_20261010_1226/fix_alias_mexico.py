with open("scripts/auto_track.py", "r") as f:
    kode = f.read()

# Tambah alias Mexico
old_alias = '''ALIAS_KHUSUS = {
    "gais goteborg": "gais",
    "ik sirius fk": "sirius",
    "caykur rizespor": "rizespor",
    "wsg tirol": "wsg tirol",
    "sv ried": "ried",
    "maritimo": "maritimo",
}'''

new_alias = '''ALIAS_KHUSUS = {
    "gais goteborg": "gais",
    "ik sirius fk": "sirius",
    "caykur rizespor": "rizespor",
    "wsg tirol": "wsg tirol",
    "sv ried": "ried",
    "maritimo": "maritimo",
    # Mexico
    "guadalajara chivas": "chivas",
    "guadalajara": "chivas",
    "cd guadalajara": "chivas",
}'''

if old_alias in kode:
    kode = kode.replace(old_alias, new_alias)
    with open("scripts/auto_track.py", "w") as f:
        f.write(kode)
    print("✅ Alias Mexico ditambah")
else:
    print("⚠️ Blok ALIAS_KHUSUS tidak ketemu")
