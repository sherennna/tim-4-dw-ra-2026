"""Aturan pemilihan satu nilai per sel Gold (Tugas #20 — Kasus 04).

Menyaring tabel Silver (1.971 baris) menjadi kandidat bersih satu nilai per sel
(wilayah × periode × seri_kode) dengan aturan deterministik yang dicatat di
log-keputusan.csv (K-020 s.d. K-022):
1. Snapshot kanonik BPS: pilih berkas JSON BPS (.json) dan sisihkan duplikat CSV
   (913 baris CSV tidak terpilih; selaras keputusan K-015).
2. Rincian sebanding: pertahankan agregat total ('total', 'jenis_kelamin=TOTAL',
   'jenis_kelamin=TOTAL|usia=YEARS30-69') dan sisihkan disagregasi jenis kelamin
   FEMALE/MALE WHO GHO ke lapisan Silver saja (64 baris tidak terpilih).
3. Periode & proyeksi: pertahankan granularitas tahunan (YYYY) dan kecualikan
   baris proyeksi WHO masa depan (tandai_proyeksi_who == True) dari tabel
   rekonsiliasi historis (5 baris proyeksi WHO tidak terpilih).
4. Penanda & nilai asli terbawa: mempertahankan tandai_outlier, tandai_proyeksi_who,
   dan menandai patahan pemekaran wilayah tanpa mengubah nilai asli.
"""

from __future__ import annotations

import pandas as pd

RINCIAN_SEBANDING = {
    "total",
    "jenis_kelamin=TOTAL",
    "jenis_kelamin=TOTAL|usia=YEARS30-69",
}

PROVINSI_PEMEKARAN = {
    6500: 2012,  # Kalimantan Utara
    9200: 2022,  # Papua Barat Daya
    9300: 2022,  # Papua Selatan
    9400: 2022,  # Papua Tengah
    9500: 2022,  # Papua Pegunungan
}


def tandai_patahan_wilayah(df: pd.DataFrame) -> pd.DataFrame:
    """Pastikan penanda patahan pemekaran wilayah & cakupan 2016 terbawa ke Gold."""
    hasil = df.copy()
    tahun = pd.to_numeric(hasil["periode"].astype(str).str.slice(0, 4), errors="coerce")
    wilayah = pd.to_numeric(hasil["wilayah_kode"], errors="coerce")

    patahan_dob = pd.Series(False, index=hasil.index)
    for kode, tahun_berdiri in PROVINSI_PEMEKARAN.items():
        patahan_dob = patahan_dob | ((wilayah == kode) & (tahun >= tahun_berdiri))

    patahan_2016 = (hasil["seri_kode"] == "var1480") & (tahun == 2016)
    hasil["tandai_patahan_wilayah"] = patahan_dob | patahan_2016

    if "tandai_outlier" not in hasil.columns:
        hasil["tandai_outlier"] = False
    else:
        hasil["tandai_outlier"] = hasil["tandai_outlier"].fillna(False).astype(bool)

    if "tandai_proyeksi_who" not in hasil.columns:
        hasil["tandai_proyeksi_who"] = False
    else:
        hasil["tandai_proyeksi_who"] = hasil["tandai_proyeksi_who"].fillna(False).astype(bool)

    return hasil


def pilih_satu_nilai_per_sel(silver: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Terapkan aturan pemilihan satu nilai per sel Gold dan hitung baris tidak terpilih."""
    df = tandai_patahan_wilayah(silver)
    total_awal = len(df)

    # Aturan 1: Snapshot kanonik (BPS memakai berkas JSON; sumber lain tetap dipertahankan)
    mask_snapshot = (df["sumber"] != "bps") | df["_berkas_raw"].astype(str).str.endswith(".json")
    ditolak_snapshot = int((~mask_snapshot).sum())
    df_s1 = df.loc[mask_snapshot].copy()

    # Aturan 2: Rincian sebanding (agregat total; pisahkan FEMALE/MALE WHO ke Silver saja)
    mask_rincian = df_s1["rincian"].isin(RINCIAN_SEBANDING)
    ditolak_rincian = int((~mask_rincian).sum())
    df_s2 = df_s1.loc[mask_rincian].copy()

    # Aturan 3: Periode tahunan baku (YYYY) dan kecualikan proyeksi WHO masa depan
    mask_periode = (df_s2["jenis_periode"] == "tahun") & (~df_s2["tandai_proyeksi_who"])
    ditolak_periode = int((~mask_periode).sum())
    df_terpilih = df_s2.loc[mask_periode].copy()

    # Verifikasi keunikan tepat satu nilai per sel (wilayah_kode x periode x seri_kode)
    kunci_sel = ["wilayah_kode", "periode", "seri_kode"]
    duplikat_sisa = int(df_terpilih.duplicated(subset=kunci_sel).sum())
    if duplikat_sisa > 0:
        raise ValueError(f"Masih terdapat {duplikat_sisa} sel ganda pada kunci {kunci_sel}")

    ringkasan = {
        "total_silver_awal": total_awal,
        "ditolak_snapshot_csv_bps": ditolak_snapshot,
        "ditolak_rincian_tidak_sebanding": ditolak_rincian,
        "ditolak_proyeksi_dan_periode": ditolak_periode,
        "total_tidak_terpilih": total_awal - len(df_terpilih),
        "total_terpilih_gold": len(df_terpilih),
        "outlier_terbawa": int(df_terpilih["tandai_outlier"].sum()),
        "patahan_wilayah_terbawa": int(df_terpilih["tandai_patahan_wilayah"].sum()),
    }
    return df_terpilih, ringkasan