with open("scripts/parlay_builder_v3.py", "r") as f:
    kode = f.read()

# Cari ALIAS dict
old_marker = '    "tigres fc": ["tigres"],\n}'

new_marker = '''    "tigres fc": ["tigres"],
    
    # ===== ENGLISH PREMIER LEAGUE =====
    "manchester united": ["man united", "man utd", "manchester utd"],
    "manchester city": ["man city"],
    "newcastle united": ["newcastle", "newcastle utd"],
    "tottenham hotspur": ["tottenham", "spurs"],
    "wolverhampton wanderers": ["wolves", "wolverhampton"],
    "brighton & hove albion": ["brighton"],
    "brighton and hove albion": ["brighton"],
    "west bromwich albion": ["west brom", "west bromwich"],
    "nottingham forest": ["nott'm forest", "nottm forest"],
    "leeds united": ["leeds"],
    "sheffield united": ["sheffield utd"],
    "west ham united": ["west ham"],
    "crystal palace": ["crystal palace"],
    "afc bournemouth": ["bournemouth"],
    "luton town": ["luton"],
    "ipswich town": ["ipswich"],
    "derby county": ["derby"],
    "stoke city": ["stoke"],
    "swansea city": ["swansea"],
    "cardiff city": ["cardiff"],
    "hull city": ["hull"],
    "birmingham city": ["birmingham"],
    "bristol city": ["bristol city"],
    "charlton athletic": ["charlton"],
    "bolton wanderers": ["bolton"],
    "blackburn rovers": ["blackburn"],
    "preston north end": ["preston"],
    "queens park rangers": ["qpr"],
    "middlesbrough": ["middlesbrough", "boro"],
    "blackpool": ["blackpool"],
    "wrexham": ["wrexham"],
    "lincoln city": ["lincoln"],
}'''

if old_marker in kode:
    kode = kode.replace(old_marker, new_marker, 1)
    with open("scripts/parlay_builder_v3.py", "w") as f:
        f.write(kode)
    print("✅ Alias English ditambah")
else:
    print("⚠️ Marker tidak ketemu, cek manual")

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
