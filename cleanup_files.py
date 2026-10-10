"""
BERSIH-BERSIH FILE — Pindahkan ke folder arsip, bukan hapus
"""
import os
import shutil
from datetime import datetime

# Bikin folder arsip
ARSIP = f"arsip_{datetime.now().strftime('%Y%m%d_%H%M')}"
os.makedirs(ARSIP, exist_ok=True)

# File yang mau diarsipkan (di ROOT)
FILE_ARSIP = [
    # Fix/patch
    "fix_alasan.py", "fix_alasan_slip.py", "fix_alias_mexico.py",
    "fix_fallback.py", "fix_fuzzy_normalize.py", "fix_gap_filter.py",
    "fix_indent2.py", "fix_indent_bikin.py", "fix_indent_fallback.py",
    "fix_komentar.py", "fix_none_check.py", "fix_print_bestpick.py",
    "fix_titik_5zona.py", "fix_titik_netral.py", "fix_under_push.py",
    "hapus_continue.py", "hapus_duplikat_override.py", "hapus_sinyal.py",
    
    # Patch
    "patch_clean.py", "patch_label.py", "patch_season_2627.py",
    "step1_list_liga.py", "step2a_update_func.py", "step2b_integrasi.py",
    "step2_clean.py", "step2c_print_slip.py", "tambah_alias.py",
    "turunkan_min_conf.py", "update_mapping.py", "update_portugal_test_lain.py",
    "skip_kandidat.py",
    
    # Test/debug
    "bikin_dummy.py", "cari_id_liga.py", "cari_liga_id.py",
    "cek_english.py", "debug_skip.py", "mapping_liga.py",
    "review_match.py", "test_auto_track.py", "test_fix_under.py",
    "test_fotmob_fixtures.py", "test_fotmob_fixtures2.py",
    "test_fotmob_match.py", "test_id_manual.py", "test_logic_baru.py",
]

# File di scripts/ yang mau diarsipkan (backup lama)
BACKUP_ARSIP = [
    "scripts/parlay_builder_v3.py.BROKEN",
    "scripts/parlay_builder_v3.py.BROKEN_0059",
    "scripts/parlay_builder_v3.py.BROKEN_GAP",
    "scripts/parlay_builder_v3.py.FINAL",
]

count = 0
for f in FILE_ARSIP:
    if os.path.exists(f):
        shutil.move(f, os.path.join(ARSIP, f))
        count += 1

for f in BACKUP_ARSIP:
    if os.path.exists(f):
        basename = os.path.basename(f)
        shutil.move(f, os.path.join(ARSIP, basename))
        count += 1

print(f"✅ {count} file dipindah ke: {ARSIP}/")
print(f"\n📁 Isi folder sekarang:")

items = sorted(os.listdir("."))
for item in items:
    if item.startswith(".") or item == ARSIP:
        continue
    if os.path.isdir(item):
        n = len(os.listdir(item))
        print(f"  📁 {item}/  ({n} files)")
    else:
        print(f"  📄 {item}")
