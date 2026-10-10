with open("scripts/parlay_builder_v3.py", "r") as f:
    kode = f.read()

# Cari fungsi bandingkan_opsi_2
if "def bandingkan_opsi_2" not in kode:
    print("❌ Fungsi bandingkan_opsi_2 tidak ketemu")
else:
    # Cek apakah sudah ada handler 2.5
    if "pick_25" in kode:
        print("✅ Handler 2.5 sudah ada")
    else:
        # Cari "return top_1x2, top_ou, titik_buta"
        old_return = "    return top_1x2, top_ou, titik_buta"
        
        new_return = '''    # ===== HANDLE KASUS 2.5 ADA DI MARKET =====
    # Kalau 2.5 ada, pakai titik buta untuk arah
    if titik_buta and titik_buta.get("ada_di_market"):
        for ou in ou_lines:
            if abs(ou.get("line", 0) - 2.5) < 0.01:
                # Arah dari titik buta
                if titik_buta["over_rate"] > 50:
                    pick_25 = "OVER 2.5"
                    odds_25 = ou.get("over", 0)
                    prob_25 = titik_buta["over_rate"]
                else:
                    pick_25 = "UNDER 2.5"
                    odds_25 = ou.get("under", 0)
                    prob_25 = 100 - titik_buta["over_rate"]
                
                if odds_25 and odds_25 > 1:
                    gap_25 = prob_25 - (100 / odds_25)
                    top_ou = {
                        "jenis": "OU",
                        "pick": pick_25,
                        "odds": round(odds_25, 2),
                        "prob": round(prob_25, 1),
                        "gap": round(gap_25, 1),
                        "line": 2.5,
                    }
                break
    
    return top_1x2, top_ou, titik_buta'''
        
        if old_return in kode:
            kode = kode.replace(old_return, new_return, 1)
            with open("scripts/parlay_builder_v3.py", "w") as f:
                f.write(kode)
            print("✅ Handler 2.5 ditambah")
        else:
            print("⚠️ 'return top_1x2, top_ou, titik_buta' tidak ketemu")
            # Coba cari versi lain
            import re
            pattern = r'return top_1x2, top_ou, titik_buta'
            if re.search(pattern, kode):
                print("   Ada tapi format beda")

# Verifikasi
import subprocess
result = subprocess.run(
    ["python3", "-c", "import ast; ast.parse(open('scripts/parlay_builder_v3.py').read())"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("✅ File VALID!")
else:
    print(f"❌ Error: {result.stderr}")
