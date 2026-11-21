import pandas as pd
from pathlib import Path
from src.extract import ekstrak_semua

# 1. Jalankan fungsi ekstrak_semua()
df = ekstrak_semua()

# 2. Filter baris level Nasional (Indonesia)
mask_nasional = (
    df["nama_wilayah"].astype(str).str.upper().str.contains("INDONESIA", na=False)
    | df["wilayah_kode"].astype(str).str.upper().isin(["IDN", "ID", "INDONESIA", "0", "00", "0000"])
)
df_idn = df[mask_nasional].copy()

# 3. Filter khusus agregat TOTAL (menghindari baris FEMALE/MALE saja)
rincian_valid = ["Tidak ada", "total", "TOTAL", "TOTAL|YEARS30-69"]
df_idn_total = df_idn[df_idn["rincian"].astype(str).str.strip().isin(rincian_valid)].copy()

# 4. Pivot menjadi Tabel Nasional: Periode x Seri (seri_kode)
df_idn_total["periode"] = pd.to_numeric(df_idn_total["periode"], errors="coerce")
df_idn_total = df_idn_total.dropna(subset=["periode"]).copy()
df_idn_total["periode"] = df_idn_total["periode"].astype(int)
df_idn_total["nilai"] = pd.to_numeric(df_idn_total["nilai"], errors="coerce")

urutan_seri = [
    "var1393", "MALARIA_EST_INCIDENCE", "SH.MLR.INCD.P3",
    "var1435", "M_Est_tob_curr_std",
    "var1480", "NCDMORT3070",
]

tabel = df_idn_total.pivot_table(
    index="periode",
    columns="seri_kode",
    values="nilai",
    aggfunc="first"
).sort_index()

kolom_ada = [s for s in urutan_seri if s in tabel.columns]
tabel = tabel[kolom_ada]

# 5. Simpan ke repo
out_path = Path("data/gold/tabel_nasional_periode_x_seri.csv")
out_path.parent.mkdir(parents=True, exist_ok=True)
tabel.to_csv(out_path)

print("\n=== TABEL NASIONAL PERIODE x SERI (TOTAL) ===")
print(tabel.to_string())
print(f"\nTersimpan di: {out_path}")

# 6. Hitung pasangan rekonsiliasi dan periode beririsan
pasangan = [
    ("var1393", "MALARIA_EST_INCIDENCE"),
    ("var1393", "SH.MLR.INCD.P3"),
    ("var1435", "M_Est_tob_curr_std"),
    ("var1480", "NCDMORT3070"),
]

print("\n=== RINGKASAN PASANGAN & PERIODE BERIRISAN ===")
tahun_irisan_total = set()
for s1, s2 in pasangan:
    if s1 in tabel.columns and s2 in tabel.columns:
        irisan = tabel[[s1, s2]].dropna().index.tolist()
        tahun_irisan_total.update(irisan)
        print(f"- {s1} vs {s2}: {len(irisan)} tahun -> {irisan}")

print(f"\npasangan_rekonsiliasi = {len(pasangan)}")
print(f"periode_beririsan     = {len(tahun_irisan_total)}")