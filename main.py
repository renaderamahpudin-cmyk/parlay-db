#!/usr/bin/env python3
"""
MAIN.PY v2 — Menu Utama dengan Refresh Match
"""
import os
import sys
import subprocess
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
from scripts.pick_policy import MIN_OU_GAP, is_eligible_ou_pick

class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def clear():
    os.system('clear' if os.name != 'nt' else 'cls')


def pause():
    input(f"\n{C.YELLOW}Tekan ENTER untuk kembali ke menu...{C.END}")


def print_header(title):
    print("=" * 55)
    print(f"{C.BOLD}{C.CYAN}{title}{C.END}")
    print("=" * 55)


def run_script(nama, script, args=None):
    print_header(nama)
    start = datetime.now()
    cmd = [sys.executable, script]
    if args:
        cmd.extend(args)
    result = subprocess.run(cmd, capture_output=False)
    durasi = (datetime.now() - start).total_seconds()
    
    if result.returncode == 0:
        print(f"\n{C.GREEN}✅ {nama} selesai ({durasi:.1f}s){C.END}")
        return True
    print(f"\n{C.RED}❌ {nama} gagal{C.END}")
    return False


def cek_match_cache():
    """Cek kapan terakhir update match"""
    if not os.path.exists("output/match_full.json"):
        return None, None
    
    mtime = os.path.getmtime("output/match_full.json")
    waktu = datetime.fromtimestamp(mtime)
    selisih = datetime.now() - waktu
    
    # Hitung selisih
    menit = int(selisih.total_seconds() / 60)
    if menit < 60:
        str_selisih = f"{menit} menit lalu"
    elif menit < 1440:
        str_selisih = f"{menit // 60} jam lalu"
    else:
        str_selisih = f"{menit // 1440} hari lalu"
    
    with open("output/match_full.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return len(data), f"{waktu.strftime('%H:%M')} ({str_selisih})"


# ============================================================
# MENU 1: PREDIKSI
# ============================================================
def menu_prediksi():
    clear()
    print_header("🎯 PREDIKSI — Cari Slip Hari Ini")
    
    # Cek cache
    n_match, waktu = cek_match_cache()
    if n_match:
        print(f"\n{C.CYAN}📦 Match cache: {n_match} match (update: {waktu}){C.END}")
        print(f"\n{C.YELLOW}Pilih:{C.END}")
        print(f"  [1] Fetch match BARU dari web (disarankan)")
        print(f"  [2] Pakai cache lama (kalau baru saja fetch)")
        print(f"  [3] Batal")
        
        pilih = input(f"\n{C.YELLOW}Pilihan (1-3): {C.END}").strip()
        
        if pilih == "3":
            return
        if pilih == "2":
            # Skip fetch, langsung analisa
            if not run_script("Analisa H2H + Generate Slip", 
                             "scripts/parlay_builder_v3.py"):
                pause()
                return
            pause()
            return
    
    # Fetch match baru
    if not run_script("1/2 Fetch Match Terbaru", "scripts/parse_full.py"):
        pause()
        return
    
    if not run_script("2/2 Analisa H2H + Generate Slip", 
                     "scripts/parlay_builder_v3.py"):
        pause()
        return
    
    print(f"\n{C.GREEN}{'='*70}{C.END}")
    print(f"{C.GREEN}🎉 PREDIKSI SELESAI!{C.END}")
    print(f"{C.GREEN}{'='*70}{C.END}")
    pause()


# ============================================================
# MENU 2: CEK SLIP
# ============================================================
def menu_cek_slip():
    clear()
    print_header("📋 CEK SLIP — Lihat Slip Tersimpan")
    
    if not os.path.exists("output/best_pick.json"):
        print(f"{C.YELLOW}⚠️  Belum ada slip.{C.END}")
        pause()
        return
    
    # Tampilkan waktu update
    mtime = os.path.getmtime("output/best_pick.json")
    print(f"\n{C.CYAN}📅 Terakhir analisa: {datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')}{C.END}\n")
    
    with open("output/best_pick.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    eligible = [pick for pick in data if is_eligible_ou_pick(pick)]
    eligible.sort(key=lambda pick: (-pick["value_gap"], -pick.get("pick_conf", 0)))
    skipped = len(data) - len(eligible)
    print(
        f"📊 Pick O/U lolos gap >=+{MIN_OU_GAP:.0f}%: "
        f"{len(eligible)} | dilewati: {skipped}\n"
    )

    if not eligible:
        print("📭 Belum ada pick O/U dengan gap yang memenuhi batas.")
        pause()
        return

    for i, m in enumerate(eligible, 1):
        
        print(f"{C.BOLD}#{i} [{m.get('liga', '?')}]{C.END}")
        print(f"   {m.get('home', '?')} vs {m.get('away', '?')}")
        print(
            f"   ⚽ {m.get('pick', '?')} "
            f"(peluang settlement {m.get('pick_conf', 0)}%) "
            f"| odds {m.get('pick_odds', 0)}"
        )
        print(
            f"   💡 Gap no-vig: {m.get('value_gap', 0):+.2f} pp "
            f"| EV model: {m.get('pick_expected_return', 0):+.3f} unit "
            f"| {m.get('kategori_gap', '-')}"
        )
        print()
    
    fair = sum(1 for m in eligible if m.get("kategori_gap") == "FAIR")
    value = sum(1 for m in eligible if m.get("kategori_gap") == "VALUE")
    print(f"📊 FAIR: {fair} | VALUE: {value} | TOTAL O/U: {len(eligible)}")
    
    pause()


# ============================================================
# MENU 3: BACKTEST
# ============================================================
def menu_backtest():
    clear()
    print_header("⚽ BACKTEST O/U POISSON — Walk-Forward Kronologis")

    print("   Uji memakai 20% tanggal pertandingan paling baru.")
    print("   Form kandang/tandang hanya memakai hasil sebelum tanggal uji.")
    print("   Poisson + settlement; odds arsip yang tersedia konsisten di line 2.5.")
    print()

    lanjut = input(f"{C.YELLOW}Lanjut jalankan? (y/n): {C.END}").strip().lower()
    if lanjut != "y":
        return

    if os.path.exists("scripts/backtest_ou_walkforward.py"):
        run_script(
            "Backtest O/U Walk-Forward",
            "scripts/backtest_ou_walkforward.py",
        )
    else:
        print(f"{C.RED}❌ Script backtest O/U tidak ditemukan{C.END}")

    pause()


# ============================================================
# MENU 4: UPDATE DATABASE H2H
# ============================================================
def menu_update_db():
    clear()
    print_header("🔄 UPDATE DATABASE — Refresh Data H2H")
    
    print(f"{C.CYAN}Jenis database:{C.END}\n")
    print(f"  {C.GREEN}[1]{C.END} Top Leagues    — EPL, La Liga, Serie A, dll")
    print(f"  {C.GREEN}[2]{C.END} Extra Leagues  — Brazil, Argentina, USA, dll")
    print(f"  {C.GREEN}[3]{C.END} Keduanya")
    print(f"  {C.RED}[4]{C.END} Kembali")
    print()
    print(f"{C.YELLOW}💡 Update 1x sebulan cukup. Data historis jarang berubah.{C.END}")
    
    pilihan = input(f"\n{C.YELLOW}Pilihan (1-4): {C.END}").strip()
    
    if pilihan == "1":
        run_script("Update Top Leagues", "build_db.py")
        pause()
    elif pilihan == "2":
        run_script("Update Extra Leagues", "build_db_extra.py")
        pause()
    elif pilihan == "3":
        run_script("Update Top Leagues", "build_db.py")
        run_script("Update Extra Leagues", "build_db_extra.py")
        pause()
    elif pilihan == "4":
        return


# ============================================================
# MENU 5: REFRESH MATCH (CACHE)
# ============================================================
def menu_refresh_match():
    clear()
    print_header("🔄 REFRESH MATCH — Fetch Match Terbaru (Tanpa Analisa)")
    
    print(f"{C.CYAN}Fungsi: Ambil daftar match hari ini dari web{C.END}")
    print(f"{C.CYAN}       Tanpa analisa H2H — cuma cache match{C.END}\n")
    
    print(f"{C.YELLOW}💡 Berguna kalau:{C.END}")
    print(f"   • Mau lihat match apa saja yang ada hari ini")
    print(f"   • Mau cek jam kick-off")
    print(f"   • Belum mau langsung analisa")
    print()
    
    if run_script("Fetch Match", "scripts/parse_full.py"):
        # Tampilkan summary
        try:
            with open("output/match_full.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            print(f"\n{C.GREEN}📊 {len(data)} match tersedia:{C.END}\n")
            
            # Group by liga
            from collections import defaultdict
            liga_count = defaultdict(list)
            for m in data:
                liga_count[m["liga"]].append(m)
            
            for liga, matches in sorted(liga_count.items()):
                print(f"{C.BOLD}{liga}{C.END} ({len(matches)} match)")
                for m in matches[:3]:
                    print(f"   • {m['waktu']} | {m['home']} vs {m['away']}")
                if len(matches) > 3:
                    print(f"   ... dan {len(matches) - 3} match lain")
                print()
        except Exception as e:
            print(f"⚠️ {e}")
    
    pause()


# ============================================================
# MENU UTAMA
# ============================================================
def menu_utama():
    while True:
        clear()
        print(f"{C.BOLD}{C.CYAN}")
        print("=" * 50)
        print("        🎯 PARLAY BUILDER 🎯")
        print("     Model Gol Home/Away + Value O/U")
        print("=" * 50)
        print(f"{C.END}")
        
        # Info data
        db_top = "✅" if os.path.exists("data/football_data/all_football_data.csv") else "❌"
        db_extra = "✅" if os.path.exists("data/football_data_extra/all_extra.csv") else "❌"
        
        # Info cache match
        n_match, waktu = cek_match_cache()
        if n_match:
            cache_info = f"{n_match} match ({waktu})"
        else:
            cache_info = "belum ada"
        
        print(f"  📊 Database H2H: Top {db_top} | Extra {db_extra}")
        print(f"  📦 Match cache:  {cache_info}")
        print()
        
        print(f"{C.BOLD}Pilih menu:{C.END}")
        print(f"  {C.GREEN}[1]{C.END} 🎯 Prediksi")
        print(f"  {C.GREEN}[2]{C.END} 📋 Cek Slip")
        print(f"  {C.GREEN}[3]{C.END} 🔄 Refresh Match")
        print(f"  {C.GREEN}[4]{C.END} 🔬 Backtest")
        print(f"  {C.GREEN}[5]{C.END} 📥 Update Database")
        print(f"  {C.RED}[0]{C.END} 🚪 Exit")
        print()
        
        pilihan = input(f"{C.YELLOW}Pilihan (0-5): {C.END}").strip()
        
        if pilihan == "1":
            menu_prediksi()
        elif pilihan == "2":
            menu_cek_slip()
        elif pilihan == "3":
            menu_refresh_match()
        elif pilihan == "4":
            menu_backtest()
        elif pilihan == "5":
            menu_update_db()
        elif pilihan == "0":
            clear()
            print(f"\n{C.CYAN}👋 Terima kasih! Sampai jumpa!{C.END}\n")
            break
        else:
            print(f"{C.RED}⚠️  Pilihan tidak valid!{C.END}")
            pause()


if __name__ == "__main__":
    try:
        menu_utama()
    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}⚠️  Dibatalkan{C.END}\n")
        sys.exit(0)
