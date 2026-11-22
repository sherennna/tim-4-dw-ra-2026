"""Tahap 3 (pembersihan): grid provinsi x periode, status tiap sel, dan kelengkapan panel (BPS).

Yang dilakukan (tidak ada nilai yang diubah, diisi, atau dibuang):
1. memilih satu format sumber kanonik (JSON atau CSV) supaya baris tidak terhitung ganda,
2. memisahkan baris Indonesia (9999) dari baris provinsi,
3. membentuk grid 38 provinsi x periode per seri, lalu memberi status tiap sel:
   terisi         ada nilai di berkas mentah
   belum_berdiri  (mode "hukum") provinsi belum berdiri pada tahun itu: BUKAN missing
   belum_terbit   (mode "data") provinsi baru belum muncul di seri itu: BUKAN missing
   missing        provinsi sudah ada, periode ada di seri, tetapi tidak ada nilai
4. melaporkan kelengkapan (persen sel terisi) per seri per tahun.

Uji / jalankan:  python -m src.silver.grid
"""
from pathlib import Path

import pandas as pd

from src.ekstraksi import bps

INDONESIA = 9999
PROVINSI = {
    1100: "ACEH", 1200: "SUMATERA UTARA", 1300: "SUMATERA BARAT", 1400: "RIAU", 1500: "JAMBI",
    1600: "SUMATERA SELATAN", 1700: "BENGKULU", 1800: "LAMPUNG", 1900: "KEP. BANGKA BELITUNG",
    2100: "KEP. RIAU", 3100: "DKI JAKARTA", 3200: "JAWA BARAT", 3300: "JAWA TENGAH",
    3400: "DI YOGYAKARTA", 3500: "JAWA TIMUR", 3600: "BANTEN", 5100: "BALI",
    5200: "NUSA TENGGARA BARAT", 5300: "NUSA TENGGARA TIMUR", 6100: "KALIMANTAN BARAT",
    6200: "KALIMANTAN TENGAH", 6300: "KALIMANTAN SELATAN", 6400: "KALIMANTAN TIMUR",
    6500: "KALIMANTAN UTARA", 7100: "SULAWESI UTARA", 7200: "SULAWESI TENGAH",
    7300: "SULAWESI SELATAN", 7400: "SULAWESI TENGGARA", 7500: "GORONTALO", 7600: "SULAWESI BARAT",
    8100: "MALUKU", 8200: "MALUKU UTARA", 9100: "PAPUA BARAT", 9200: "PAPUA BARAT DAYA",
    9400: "PAPUA", 9500: "PAPUA SELATAN", 9600: "PAPUA TENGAH", 9700: "PAPUA PEGUNUNGAN",
}
BERDIRI = {6500: 2012, 9200: 2022, 9500: 2022, 9600: 2022, 9700: 2022}
SURVEI = {"var1480"}
MODE = "hukum"
KANONIK = "json"


def siapkan(df, kanonik=KANONIK):
    """Ambil satu format kanonik dan pastikan kode wilayah serta periode sah."""
    d = df[df["format"] == kanonik].copy()
    if d.empty:
        raise ValueError(f"tidak ada baris berformat {kanonik!r}")
    d["wilayah_kode"] = d["wilayah_id"].astype(int)
    luar = sorted(set(d["wilayah_kode"]) - set(PROVINSI) - {INDONESIA})
    if luar:
        raise ValueError(f"kode wilayah di luar susunan 38 provinsi: {luar}")
    tahun = d["tahun"].astype(str).str.strip()
    if not tahun.str.fullmatch(r"\d{4}").all():
        raise ValueError(f"label tahun tidak berbentuk 4 digit: {sorted(set(tahun[~tahun.str.fullmatch(r'\\d{4}')]))[:5]}")
    d["tahun"] = tahun.astype(int)
    kembar = d.duplicated(["seri_kode", "wilayah_kode", "tahun"], keep=False)
    if kembar.any():
        raise ValueError(f"{int(kembar.sum())} baris berkunci kembar (seri, wilayah, tahun)")
    return d


def bentuk_grid(d):
    """Grid provinsi x periode per seri + tabel Indonesia terpisah."""
    bagian = []
    for seri, g in d.groupby("seri_kode"):
        ada = sorted(g["tahun"].unique())
        periode = ada if seri in SURVEI else list(range(ada[0], ada[-1] + 1))
        grid = pd.MultiIndex.from_product([sorted(PROVINSI), periode],
                                          names=["wilayah_kode", "tahun"]).to_frame(index=False)
        grid["seri_kode"] = seri
        isi = g[g["wilayah_kode"] != INDONESIA][["wilayah_kode", "tahun", "nilai", "_berkas_raw", "_sha256_raw"]]
        grid = grid.merge(isi, on=["wilayah_kode", "tahun"], how="left")
        grid["status"] = "missing"
        if MODE == "hukum":
            belum = grid["tahun"] < grid["wilayah_kode"].map(BERDIRI).fillna(0).astype(int)
            label = "belum_berdiri"
        else:
            pertama = isi.dropna(subset=["nilai"]).groupby("wilayah_kode")["tahun"].min()
            belum = grid["wilayah_kode"].isin(BERDIRI) & (grid["tahun"] < grid["wilayah_kode"].map(pertama).fillna(9999))
            label = "belum_terbit"
        grid.loc[belum, "status"] = label
        grid.loc[grid["nilai"].notna(), "status"] = "terisi"
        bagian.append(grid)
    grid = pd.concat(bagian, ignore_index=True)
    grid["nama_wilayah"] = grid["wilayah_kode"].map(PROVINSI)
    grid["periode"] = grid["tahun"].astype(str)
    grid["jenis_periode"] = "tahun"
    kolom = ["seri_kode", "wilayah_kode", "nama_wilayah", "periode", "jenis_periode", "nilai", "status",
             "_berkas_raw", "_sha256_raw"]
    indonesia = d[d["wilayah_kode"] == INDONESIA][["seri_kode", "tahun", "nilai", "_berkas_raw", "_sha256_raw"]]
    return grid[kolom], indonesia.reset_index(drop=True)


def kelengkapan(grid, indonesia):
    """Persen sel terisi per seri per tahun, memakai hanya sel yang berlaku (belum_berdiri dikeluarkan)."""
    g = grid.assign(tahun=grid["periode"].astype(int))
    k = (g.groupby(["seri_kode", "tahun"])["status"].value_counts().unstack(fill_value=0)
         .reindex(columns=["terisi", "missing", "belum_berdiri", "belum_terbit"], fill_value=0).reset_index())
    k["tidak_berlaku"] = k["belum_berdiri"] + k["belum_terbit"]
    k["sel_berlaku"] = k["terisi"] + k["missing"]
    k["persen_terisi"] = (100 * k["terisi"] / k["sel_berlaku"]).round(1)
    ada_ind = indonesia.groupby(["seri_kode", "tahun"]).size().rename("ada_indonesia").reset_index()
    k = k.merge(ada_ind, on=["seri_kode", "tahun"], how="left")
    k["ada_indonesia"] = k["ada_indonesia"].fillna(0).astype(int) > 0
    return k


def rentang_seri(d):
    """Rentang tahun per seri (untuk memutuskan jendela analisis bersama)."""
    r = d[d["wilayah_kode"] != INDONESIA].groupby("seri_kode")["tahun"].agg(["min", "max", "nunique"])
    r.columns = ["tahun_awal", "tahun_akhir", "jumlah_tahun"]
    return r.reset_index()


def tulis_laporan(k, rentang, folder="reports"):
    Path(folder).mkdir(exist_ok=True)
    k.to_csv(Path(folder) / "kelengkapan-panel.csv", index=False)
    baris = ["# Kelengkapan panel provinsi x tahun (BPS)", "",
             f"Mode sel tidak berlaku: {MODE}. Sel berlaku = 38 provinsi dikurangi provinsi yang belum berdiri/terbit pada tahun itu. "
             "Persen terisi = sel terisi / sel berlaku. Baris Indonesia (9999) dilaporkan terpisah.", ""]
    for seri, g in k.groupby("seri_kode"):
        baris += [f"## {seri}", "", "| tahun | sel berlaku | terisi | missing | tidak berlaku | persen terisi | ada baris Indonesia |",
                  "|---|---|---|---|---|---|---|"]
        for r in g.itertuples():
            baris.append(f"| {r.tahun} | {r.sel_berlaku} | {r.terisi} | {r.missing} | {r.tidak_berlaku} | "
                         f"{r.persen_terisi} | {'ya' if r.ada_indonesia else 'tidak'} |")
        baris.append("")
    baris += ["## Rentang tahun per seri", "", "| seri | tahun awal | tahun akhir | jumlah tahun |", "|---|---|---|---|"]
    baris += [f"| {r.seri_kode} | {r.tahun_awal} | {r.tahun_akhir} | {r.jumlah_tahun} |" for r in rentang.itertuples()]
    (Path(folder) / "kelengkapan-panel.md").write_text("\n".join(baris) + "\n", encoding="utf-8")


if __name__ == "__main__":
    d = siapkan(bps.baca_semua())
    grid, indonesia = bentuk_grid(d)
    k = kelengkapan(grid, indonesia)
    rentang = rentang_seri(d)
    tulis_laporan(k, rentang)
    print(f"Mode: {MODE}; format kanonik: {KANONIK}; baris observasi kanonik: {len(d)} (provinsi {int((d.wilayah_kode != INDONESIA).sum())},"
          f" Indonesia {int((d.wilayah_kode == INDONESIA).sum())})")
    print("\nKelengkapan per seri per tahun:")
    print(k.drop(columns=["ada_indonesia", "belum_berdiri", "belum_terbit"]).to_string(index=False))
    print("\nRentang tahun (provinsi):")
    print(rentang.to_string(index=False))
    r = grid["status"].value_counts().to_dict()
    print(f"\nSel grid: {len(grid)}; status: {r}")
    print("Missing per seri:", grid[grid.status == 'missing'].groupby('seri_kode').size().to_dict())
    print("Laporan: reports/kelengkapan-panel.md dan reports/kelengkapan-panel.csv")
