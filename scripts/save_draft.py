"""
SIMPAN DRAFT — Match yang belum di-track
"""
import json
import os
from datetime import datetime

from pick_policy import is_eligible_ou_pick, is_over_under_pick
from settlement import match_key

PICK_FILE = "output/best_pick.json"
MAPPING_FILE = "output/mapping_liga.json"
TRACK_FILE = "output/track_record.csv"
DRAFT_FILE = "output/draft_pending.json"


PICK_FIELDS = (
    "tanggal", "liga", "home", "away", "waktu", "pick", "pick_jenis",
    "pick_conf", "pick_odds", "pick_implied", "pick_alasan", "value_gap",
    "kategori_gap", "skor", "tier", "pick_push_rate",
)


def draft_key(pick):
    return (
        *match_key(pick.get("liga"), pick.get("home"), pick.get("away")),
        str(pick.get("waktu", "")).strip(),
        str(pick.get("pick", "")).strip().upper(),
    )


def main():
    # Load
    with open(PICK_FILE) as f:
        picks = json.load(f)
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
    
    # Match yang sudah di track
    tracked = set()
    if os.path.exists(TRACK_FILE):
        import pandas as pd
        df = pd.read_csv(TRACK_FILE)
        if len(df) > 0 and {"liga", "home", "away"}.issubset(df.columns):
            tracked = {
                match_key(row.liga, row.home, row.away)
                for row in df[["liga", "home", "away"]].itertuples(index=False)
            }

    # Simpan pick lama sampai hasilnya ditrack, meskipun best_pick berganti.
    pending_by_key = {}
    if os.path.exists(DRAFT_FILE):
        try:
            with open(DRAFT_FILE, encoding="utf-8") as f:
                old_draft = json.load(f)
            for old_pick in old_draft.get("pending_auto", []):
                if not is_over_under_pick(old_pick):
                    continue
                key = match_key(
                    old_pick.get("liga"), old_pick.get("home"), old_pick.get("away")
                )
                if key not in tracked:
                    pending_by_key[draft_key(old_pick)] = old_pick
        except (OSError, json.JSONDecodeError, AttributeError, TypeError):
            print("⚠️ Draft lama tidak bisa dibaca; membuat draft baru.")

    skip_liga = []
    added = 0
    for p in picks:
        if not is_eligible_ou_pick(p):
            continue
        fixture_key = match_key(p.get("liga"), p.get("home"), p.get("away"))
        if fixture_key in tracked:
            continue
        
        liga = p.get("liga", "")
        
        if liga not in mapping:
            skip_liga.append({
                "home": p.get("home", ""),
                "away": p.get("away", ""),
                "liga": liga,
                "waktu": p.get("waktu", ""),
                "pick": p.get("pick", ""),
                "alasan": "Liga nggak di mapping",
            })
        else:
            key = draft_key(p)
            if key in pending_by_key:
                # Jangan ganti harga/confidence awal; hanya lengkapi field lama
                # yang belum tercatat.
                for field in PICK_FIELDS:
                    if pending_by_key[key].get(field) in (None, "") and field in p:
                        pending_by_key[key][field] = p[field]
                pending_by_key[key].setdefault("fotmob_id", mapping[liga]["id"])
            else:
                saved_pick = {field: p[field] for field in PICK_FIELDS if field in p}
                saved_pick.update({
                    "fotmob_id": mapping[liga]["id"],
                    "alasan": "Menunggu hasil pertandingan — cek lagi nanti",
                })
                pending_by_key[key] = saved_pick
                added += 1

    pending_auto = list(pending_by_key.values())
    
    draft = {
        "saved_at": datetime.now().isoformat(),
        "total_pending_auto": len(pending_auto),
        "total_skip_liga": len(skip_liga),
        "pending_auto": pending_auto,
        "skip_liga": skip_liga,
    }
    
    with open(DRAFT_FILE, "w") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print("💾 DRAFT DISIMPAN")
    print("=" * 60)
    print(f"\n⏳ Pending auto-track: {len(pending_auto)}")
    print(f"➕ Pick baru ditambahkan: {added}")
    for p in pending_auto:
        print(f"  [{p.get('liga', '?')}] {p.get('home', '?')} vs "
              f"{p.get('away', '?')} ({p.get('waktu', '?')}) — "
              f"{p.get('pick', '?')} @ {p.get('pick_odds', '?')}")
    
    print(f"\n❌ Skip (liga nggak di mapping): {len(skip_liga)}")
    for p in skip_liga:
        print(f"  [{p.get('liga', '?')}] {p.get('home', '?')} vs {p.get('away', '?')}")
    
    print(f"\n💾 File: {DRAFT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
