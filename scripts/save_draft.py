"""
SIMPAN DRAFT — Match yang belum di-track
"""
import json
import os
from datetime import datetime

PICK_FILE = "output/best_pick.json"
MAPPING_FILE = "output/mapping_liga.json"
TRACK_FILE = "output/track_record.csv"
DRAFT_FILE = "output/draft_pending.json"

def main():
    # Load
    with open(PICK_FILE) as f:
        picks = json.load(f)
    with open(MAPPING_FILE) as f:
        mapping = json.load(f)
    
    # Kategorisasi
    pending_auto = []      # Belum selesai, auto-track nanti
    not_found = []         # Fuzzy matching gagal
    skip_liga = []         # Liga nggak di mapping
    
    # Match yang sudah di track
    tracked = set()
    if os.path.exists(TRACK_FILE):
        import pandas as pd
        df = pd.read_csv(TRACK_FILE)
        if len(df) > 0:
            tracked = set(zip(df["home"], df["away"]))
    
    for p in picks:
        if (p["home"], p["away"]) in tracked:
            continue
        
        liga = p["liga"]
        
        if liga not in mapping:
            skip_liga.append({
                "home": p["home"],
                "away": p["away"],
                "liga": liga,
                "waktu": p["waktu"],
                "pick": p["pick"],
                "alasan": "Liga nggak di mapping",
            })
        else:
            pending_auto.append({
                "home": p["home"],
                "away": p["away"],
                "liga": liga,
                "waktu": p["waktu"],
                "pick": p["pick"],
                "fotmob_id": mapping[liga]["id"],
                "alasan": "Belum kick-off — cek nanti",
            })
    
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
    for p in pending_auto:
        print(f"  [{p['liga']}] {p['home']} vs {p['away']} ({p['waktu']})")
    
    print(f"\n❌ Skip (liga nggak di mapping): {len(skip_liga)}")
    for p in skip_liga:
        print(f"  [{p['liga']}] {p['home']} vs {p['away']}")
    
    print(f"\n💾 File: {DRAFT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
