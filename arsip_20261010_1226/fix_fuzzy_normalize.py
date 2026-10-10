"""
Fix fuzzy matching — normalisasi + alias
"""
with open("scripts/auto_track.py", "r") as f:
    kode = f.read()

# Ganti fungsi fuzzy_match
old_fuzzy = '''def fuzzy_match(nama_a, nama_b):
    """Cek apakah 2 nama tim cocok"""
    a = nama_a.lower().strip()
    b = nama_b.lower().strip()
    
    if a == b:
        return True
    
    # Substring (min 5 char)
    if len(a) >= 5 and len(b) >= 5:
        if a in b or b in a:
            return True
    
    return False'''

new_fuzzy = '''import unicodedata

# Prefix/suffix umum yang bisa dibuang
KATA_UMUM = [
    "fc", "sc", "ac", "afc", "cf", "cd", "sk", "ik", "fk", "if",
    "sv", "bv", "rc", "as", "ss", "us", "ssc", "fk", "kf",
    "united", "utd", "city", "town", "club", "de", "cf",
]

# Alias khusus (web → fotmob)
ALIAS_KHUSUS = {
    "gais goteborg": "gais",
    "ik sirius fk": "sirius",
    "caykur rizespor": "rizespor",
    "wsg tirol": "wsg tirol",
    "sv ried": "ried",
    "maritimo": "maritimo",
}


def normalize_nama(nama):
    """Normalisasi nama tim"""
    if not nama:
        return ""
    
    # 1. Lowercase
    n = nama.lower().strip()
    
    # 2. Buang aksen (í → i, ç → c, ö → o)
    n = unicodedata.normalize("NFKD", n)
    n = "".join(c for c in n if not unicodedata.combining(c))
    
    # 3. Buang tanda baca
    n = n.replace(".", " ").replace("-", " ").replace("'", "")
    n = " ".join(n.split())
    
    return n


def normalize_buang_umum(nama):
    """Normalisasi + buang kata umum"""
    n = normalize_nama(nama)
    words = [w for w in n.split() if w not in KATA_UMUM]
    return " ".join(words)


def fuzzy_match(nama_a, nama_b):
    """Cek apakah 2 nama tim cocok (dengan normalisasi + alias)"""
    if not nama_a or not nama_b:
        return False
    
    # 1. Cek alias khusus dulu
    a_raw = normalize_nama(nama_a)
    b_raw = normalize_nama(nama_b)
    
    if a_raw in ALIAS_KHUSUS and ALIAS_KHUSUS[a_raw] == b_raw:
        return True
    if b_raw in ALIAS_KHUSUS and ALIAS_KHUSUS[b_raw] == a_raw:
        return True
    
    # 2. Normalisasi
    a = normalize_nama(nama_a)
    b = normalize_nama(nama_b)
    
    # Exact match
    if a == b:
        return True
    
    # 3. Normalisasi + buang kata umum
    a2 = normalize_buang_umum(nama_a)
    b2 = normalize_buang_umum(nama_b)
    
    if a2 and b2 and a2 == b2:
        return True
    
    # 4. Substring check (min 4 char)
    if len(a2) >= 4 and len(b2) >= 4:
        if a2 in b2 or b2 in a2:
            # Cek selisih panjang max 50%
            diff = abs(len(a2) - len(b2))
            if diff <= max(len(a2), len(b2)) * 0.5:
                return True
    
    return False'''

if old_fuzzy in kode:
    kode = kode.replace(old_fuzzy, new_fuzzy)
    with open("scripts/auto_track.py", "w") as f:
        f.write(kode)
    print("✅ Fuzzy matching diupdate dengan normalisasi")
else:
    print("⚠️ Fungsi fuzzy_match tidak ketemu")
    print("   Cek manual: grep -n 'def fuzzy_match' scripts/auto_track.py")
