#!/usr/bin/env python3
import subprocess
import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)


def run_step(nama, script):
    print(f"\n{'='*70}")
    print(f"▶️  [{nama}]")
    print(f"{'='*70}")
    start = time.time()
    result = subprocess.run([sys.executable, script], capture_output=False, text=True)
    duration = time.time() - start
    if result.returncode == 0:
        print(f"\n✅ {nama} selesai ({duration:.1f}s)")
        return True
    print(f"\n❌ {nama} GAGAL")
    return False


def main():
    print("=" * 70)
    print("🚀 PARLAY BUILDER — RUN ALL")
    print("=" * 70)

    os.makedirs("output", exist_ok=True)

    steps = [
        ("1/2 Parse Odds dari Web", "scripts/parse_full.py"),
        ("2/2 Best Pick + Generate Slip", "scripts/parlay_builder_v3.py"),
    ]

    for nama, script in steps:
        if not os.path.exists(script):
            print(f"\n❌ Script tidak ada: {script}")
            return
        if not run_step(nama, script):
            return

    print(f"\n{'='*70}")
    print(f"🎉 SELESAI!")
    print(f"{'='*70}")
    print(f"📁 output/match_full.json     → data match web")
    print(f"📁 output/best_pick.json      → analisa + pick terbaik")


if __name__ == "__main__":
    main()
