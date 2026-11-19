Zannuba arifah ilman
124450112
30 september 2026

Latihan 2.1 — Nilai hilang yang tidak tampak: sensor gudang
sensor = pd.read_csv(RAW / "sensor_gudang.csv", dtype=str, keep_default_na=False)
sensor["waktu"] = pd.to_datetime(sensor.waktu, format="%Y-%m-%d %H:%M:%S")

bagian = []
for gudang, d in sensor.groupby("id_gudang"):
    grid = pd.date_range("2026-05-01 00:00", "2026-06-29 23:50", freq="10min", name="waktu")
    g = d.set_index("waktu").reindex(grid).reset_index()
    g["baris_sisipan"] = g.id_gudang.isna()
    g["id_gudang"] = gudang
    bagian.append(g)
s = pd.concat(bagian, ignore_index=True)
print("grid lengkap:", len(s), "| baris sisipan:", s.groupby("id_gudang").baris_sisipan.sum().to_dict())

# TODO 1: ukur panjang setiap celah baris_sisipan per gudang
# TODO 2: ungkap penanda suhu_c dan kelembapan_persen; buat kolom *_status
# TODO 3: uji sembunyi (tunggal dan blok 6 jam) -> OUT / "evaluasi_interpolasi_sensor.csv"

jawaban
# TODO 1: ukur panjang setiap celah baris_sisipan per gudang
#input
celah = []
for gudang, d in s.groupby("id_gudang"):
    d = d.sort_values("waktu").reset_index(drop=True)
    blok = (d.baris_sisipan != d.baris_sisipan.shift()).cumsum()
    for _, b in d[d.baris_sisipan].groupby(blok[d.baris_sisipan]):
        celah.append({"id_gudang": gudang, "mulai": b.waktu.iloc[0],
                      "akhir": b.waktu.iloc[-1], "panjang": len(b)})
celah = pd.DataFrame(celah)
 
print("Baris hilang per gudang:", s.groupby("id_gudang").baris_sisipan.sum().to_dict())
print(celah.groupby("id_gudang").panjang.agg(["count", "min", "median", "max"]))
print(celah.groupby("id_gudang").panjang.value_counts().sort_index())  # sebaran panjang celah
# panjang celah dalam jam = panjang * 10 / 60
print(celah.sort_values("panjang", ascending=False).head(10))
#output
Baris hilang per gudang: {'GDG-BDL': 41, 'GDG-MDN': 36, 'GDG-PLM': 0}
           count  min  median  max
id_gudang                         
GDG-BDL       41    1     1.0    1
GDG-MDN        1   36    36.0   36
id_gudang  panjang
GDG-BDL    1          41
GDG-MDN    36          1
Name: count, dtype: int64
   id_gudang               mulai               akhir  panjang
41   GDG-MDN 2026-05-18 02:00:00 2026-05-18 07:50:00       36
0    GDG-BDL 2026-05-01 21:20:00 2026-05-01 21:20:00        1
2    GDG-BDL 2026-05-06 09:30:00 2026-05-06 09:30:00        1
3    GDG-BDL 2026-05-07 10:00:00 2026-05-07 10:00:00        1
4    GDG-BDL 2026-05-11 12:10:00 2026-05-11 12:10:00        1
5    GDG-BDL 2026-05-13 06:40:00 2026-05-13 06:40:00        1
6    GDG-BDL 2026-05-16 09:00:00 2026-05-16 09:00:00        1
7    GDG-BDL 2026-05-16 11:40:00 2026-05-16 11:40:00        1
8    GDG-BDL 2026-05-16 18:00:00 2026-05-16 18:00:00        1
1    GDG-BDL 2026-05-02 00:10:00 2026-05-02 00:10:00        1



# TODO 2: ungkap penanda suhu_c dan kelembapan_persen; buat kolom *_status
#input
SENTINEL = {-999, -99, -9999, 999, 9999}
KOSONG = {"", "na", "n/a", "nan", "null", "none", "-"}
VALID = {
    "suhu_c": lambda x: x.between(-10, 60),                 
    "kelembapan_persen": lambda x: x.between(0, 100, inclusive="right"),  # 0% mustahil
}
 
def tandai(kol):
    raw = s[kol]                               
    num = pd.to_numeric(raw, errors="coerce")
    kosong = raw.notna() & raw.str.strip().str.lower().isin(KOSONG)
    penanda = raw.notna() & ~kosong & (num.isna() | num.isin(SENTINEL) | ~VALID[kol](num))
    status = np.select([s.baris_sisipan, kosong, penanda],
                       ["baris_hilang", "kosong", "penanda"], default="teramati")
    return status, num.where(status == "teramati")   # bersih: hanya nilai teramati
 
for kol in ["suhu_c", "kelembapan_persen"]:
    s[kol + "_status"], s[kol + "_bersih"] = tandai(kol)
    print("\n", kol)
    print(pd.crosstab(s.id_gudang, s[kol + "_status"]))

#output
 suhu_c
suhu_c_status  baris_hilang  kosong  penanda  teramati
id_gudang                                             
GDG-BDL                  41      36       27      8536
GDG-MDN                  36      50       28      8526
GDG-PLM                   0      46       21      8573

 kelembapan_persen
kelembapan_persen_status  baris_hilang  penanda  teramati
id_gudang                                                
GDG-BDL                             41       17      8582
GDG-MDN                             36       14      8590
GDG-PLM                              0       18      8622


Code



# TODO 3: uji sembunyi (tunggal dan blok 6 jam) -> OUT / "evaluasi_interpolasi_sensor.csv"
def uji(seri, panjang, n=300, seed=42):
    """Sembunyikan blok `panjang` titik yang kedua sisinya teramati, tebak, hitung MAE."""
    rng = np.random.default_rng(seed)
    v = seri.to_numpy(float)
    ok = ~np.isnan(v)
    jendela = np.convolve(ok, np.ones(panjang + 2), "valid") == panjang + 2
    kandidat = np.where(jendela)[0]
    if len(kandidat) == 0:
        return {"rata-rata": np.nan, "ffill": np.nan, "interpolasi": np.nan, "n": 0}
    pilih = rng.choice(kandidat, size=min(n, len(kandidat)), replace=False)
    total, cnt = np.nansum(v), ok.sum()
    e = {"rata-rata": [], "ffill": [], "interpolasi": []}
    for a in pilih:
        b = a + panjang + 1
        asli = v[a + 1:b]
        rata = (total - asli.sum()) / (cnt - panjang)           
        lin = np.linspace(v[a], v[b], panjang + 2)[1:-1]
        e["rata-rata"].append(np.abs(asli - rata).mean())
        e["ffill"].append(np.abs(asli - v[a]).mean())
        e["interpolasi"].append(np.abs(asli - lin).mean())
    hasil = {k: float(np.mean(x)) for k, x in e.items()}
    hasil["n"] = len(pilih)
    return hasil
 
skenario = {"titik_tunggal": 1, "blok_6_jam": 36}   
baris = []
for gudang, d in s.groupby("id_gudang"):
    d = d.sort_values("waktu")
    for kol in ["suhu_c", "kelembapan_persen"]:
        for nama, p in skenario.items():
            r = uji(d[kol + "_bersih"].reset_index(drop=True), p)
            for metode in ["rata-rata", "ffill", "interpolasi"]:
                baris.append({"id_gudang": gudang, "variabel": kol, "skenario": nama,
                              "metode": metode, "mae": r[metode], "n_uji": r["n"]})
evaluasi = pd.DataFrame(baris)
import os
os.makedirs(OUT, exist_ok=True)
evaluasi.to_csv(OUT / "evaluasi_interpolasi_sensor.csv", index=False)   
path.join(OUT, ...)
print(evaluasi.pivot_table(index=["id_gudang", "variabel", "skenario"],
                           columns="metode", values="mae").round(3))
#output
metode                                     ffill  interpolasi  rata-rata
id_gudang variabel          skenario                                    
GDG-BDL   kelembapan_persen blok_6_jam     2.749        2.580      1.994
                            titik_tunggal  2.600        2.332      1.883
          suhu_c            blok_6_jam     0.447        0.354      0.375
                            titik_tunggal  0.220        0.155      0.377
GDG-MDN   kelembapan_persen blok_6_jam     2.677        2.486      1.953
                            titik_tunggal  2.863        2.474      1.959
          suhu_c            blok_6_jam     0.487        0.369      0.406
                            titik_tunggal  0.217        0.158      0.380
GDG-PLM   kelembapan_persen blok_6_jam     2.843        2.546      2.004
                            titik_tunggal  2.825        2.294      1.809
          suhu_c            blok_6_jam     0.473        0.378      0.422
                            titik_tunggal  0.214        0.177      0.395