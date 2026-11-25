"""Tahap 6: Tabel rekonsiliasi seri utama nasional vs pembanding WHO/WDI (Gold)."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

GOLD_DIR = Path("data/gold")
NASIONAL_PARQUET = GOLD_DIR / "nasional.parquet"
TAHUN_BERJALAN = 2026


def _ambil_seri(nas: pd.DataFrame, sumber: str, indikator: str, rincian: str | None = None) -> pd.DataFrame:
    sub = nas[(nas["sumber"] == sumber) & (nas["indikator"] == indikator)].copy()
    if rincian is not None and "rincian" in sub.columns:
        sub = sub[sub["rincian"] == rincian].copy()
    elif "rincian" in sub.columns and sub["periode"].duplicated().any():
        # Ambil agregat total jika tersedia agar satu nilai per periode
        total_mask = sub["rincian"].astype(str).str.contains("total", case=False, na=False)
        if total_mask.any():
            sub = sub[total_mask].copy()
    sub["periode"] = pd.to_numeric(sub["periode"], errors="coerce").astype("Int64")
    sub = sub.dropna(subset=["periode"]).drop_duplicates(subset=["periode"], keep="first")
    return sub[["periode", "nilai", "satuan", "flag_sel"]].copy()


def _pasangkan_dua_seri(
    df_utama: pd.DataFrame,
    df_pembanding: pd.DataFrame,
    kode_pasangan: str,
    nama_utama: str,
    nama_pembanding: str,
    kategori_default: str,
    penjelasan_default: str,
    cek_proyeksi: bool = False,
) -> pd.DataFrame:
    gabung = pd.merge(
        df_utama.rename(columns={"nilai": "nilai_seri_utama", "satuan": "satuan_utama", "flag_sel": "flag_utama"}),
        df_pembanding.rename(columns={"nilai": "nilai_pembanding", "satuan": "satuan_pembanding", "flag_sel": "flag_pembanding"}),
        on="periode",
        how="outer",
    ).sort_values("periode").reset_index(drop=True)

    gabung["pasangan"] = kode_pasangan
    gabung["seri_utama"] = nama_utama
    gabung["seri_pembanding"] = nama_pembanding
    gabung["selisih"] = gabung["nilai_seri_utama"] - gabung["nilai_pembanding"]

    berpasangan = gabung["nilai_seri_utama"].notna() & gabung["nilai_pembanding"].notna()
    proyeksi_mask = (gabung["periode"] > TAHUN_BERJALAN) | (gabung["flag_pembanding"] == "proyeksi_who")

    gabung["jenis_nilai_pembanding"] = np.where(
        gabung["nilai_pembanding"].isna(),
        "tidak_tersedia",
        np.where(proyeksi_mask, "proyeksi", "estimasi_historis"),
    )

    gabung["status_pasangan"] = np.where(
        berpasangan,
        "berpasangan",
        np.where(gabung["nilai_seri_utama"].notna(), "hanya_seri_utama", "hanya_pembanding"),
    )

    kategori = pd.Series(pd.NA, index=gabung.index, dtype="object")
    catatan = pd.Series("", index=gabung.index, dtype="object")

    kategori.loc[berpasangan] = kategori_default
    catatan.loc[berpasangan] = penjelasan_default

    if cek_proyeksi:
        # Untuk periode proyeksi WHO (> tahun berjalan) tanpa data BPS, tandai jenis nilainya secara eksplisit
        hanya_proyeksi = (~berpasangan) & proyeksi_mask & gabung["nilai_pembanding"].notna()
        catatan.loc[hanya_proyeksi] = (
            "Periode WHO melewati tahun berjalan (proyeksi model WHO GHO); belum ada pasangan observasi BPS."
        )

    gabung["kategori_penjelasan"] = kategori
    gabung["penjelasan_dan_bukti"] = catatan

    kolom = [
        "pasangan",
        "seri_utama",
        "seri_pembanding",
        "periode",
        "nilai_seri_utama",
        "satuan_utama",
        "nilai_pembanding",
        "satuan_pembanding",
        "selisih",
        "status_pasangan",
        "jenis_nilai_pembanding",
        "kategori_penjelasan",
        "penjelasan_dan_bukti",
    ]
    return gabung[kolom]


def bangun_tabel_rekonsiliasi(nasional: pd.DataFrame | None = None, out_dir: str | Path = GOLD_DIR) -> tuple[pd.DataFrame, dict]:
    """Bangun tabel rekonsiliasi nasional Gold untuk 3 kelompok pasangan Panduan Bagian 3."""
    if nasional is None:
        nasional = pd.read_parquet(NASIONAL_PARQUET)

    s_var1393 = _ambil_seri(nasional, "bps", "var1393")
    s_who_mal = _ambil_seri(nasional, "who_gho", "MALARIA_EST_INCIDENCE")
    s_wdi_mal = _ambil_seri(nasional, "wdi", "SH.MLR.INCD.P3")

    s_var1435 = _ambil_seri(nasional, "bps", "var1435")
    s_who_tob = _ambil_seri(nasional, "who_gho", "M_Est_tob_curr_std")

    s_var1480 = _ambil_seri(nasional, "bps", "var1480")
    s_who_ncd = _ambil_seri(nasional, "who_gho", "NCDMORT3070")

    # 1a. var1393 (BPS) vs WHO MALARIA_EST_INCIDENCE
    p1_who = _pasangkan_dua_seri(
        s_var1393,
        s_who_mal,
        kode_pasangan="malaria_bps_vs_who",
        nama_utama="bps:var1393",
        nama_pembanding="who_gho:MALARIA_EST_INCIDENCE",
        kategori_default="cakupan berbeda",
        penjelasan_default=(
            "BPS var1393 (API) memakai penyebut seluruh penduduk nasional, sedangkan WHO MALARIA_EST_INCIDENCE "
            "memakai penyebut penduduk berisiko malaria (population at risk) dan penyesuaian pelaporan kasus."
        ),
    )

    # 1b. var1393 (BPS) vs WDI SH.MLR.INCD.P3
    p1_wdi = _pasangkan_dua_seri(
        s_var1393,
        s_wdi_mal,
        kode_pasangan="malaria_bps_vs_wdi",
        nama_utama="bps:var1393",
        nama_pembanding="wdi:SH.MLR.INCD.P3",
        kategori_default="cakupan berbeda",
        penjelasan_default=(
            "BPS var1393 (API) berbasis laporan rutin fasilitas kesehatan dengan penyebut seluruh penduduk, "
            "sedangkan WDI SH.MLR.INCD.P3 mereplikasi estimasi insidens per 1.000 penduduk berisiko."
        ),
    )

    # 2. var1435 (BPS) vs WHO M_Est_tob_curr_std (estimasi vs proyeksi > tahun berjalan)
    p2_tob = _pasangkan_dua_seri(
        s_var1435,
        s_who_tob,
        kode_pasangan="merokok_bps_vs_who",
        nama_utama="bps:var1435",
        nama_pembanding="who_gho:M_Est_tob_curr_std",
        kategori_default="metode berbeda",
        penjelasan_default=(
            "BPS var1435 adalah prevalensi kasar (crude) penduduk usia >=15 tahun dari Susenas, sedangkan WHO "
            "M_Est_tob_curr_std adalah estimasi terstandar umur (age-standardized) hasil pemodelan Bayesian (2000-2030)."
        ),
        cek_proyeksi=True,
    )

    # 3. var1480 (BPS) vs WHO NCDMORT3070
    p3_ncd = _pasangkan_dua_seri(
        s_var1480,
        s_who_ncd,
        kode_pasangan="ptm_bps_vs_who",
        nama_utama="bps:var1480",
        nama_pembanding="who_gho:NCDMORT3070",
        kategori_default="definisi berbeda",
        penjelasan_default=(
            "Kode SDG 3.4 sama, namun BPS var1480 mengukur prevalensi hipertensi hasil pengukuran (%), "
            "sedangkan WHO NCDMORT3070 mengukur probabilitas kematian usia 30-70 tahun akibat 4 PTM utama (%)."
        ),
    )

    df_rekon = pd.concat([p1_who, p1_wdi, p2_tob, p3_ncd], ignore_index=True)

    # Validasi aturan wajib Tahap 6: setiap baris berpasangan harus punya kategori
    berpasangan_df = df_rekon.dropna(subset=["nilai_seri_utama", "nilai_pembanding"])
    assert berpasangan_df["kategori_penjelasan"].notna().all(), "Ada baris berpasangan tanpa kategori!"

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    df_rekon.to_parquet(out_path / "rekonsiliasi_nasional.parquet", index=False)
    df_rekon.to_csv(out_path / "rekonsiliasi_nasional.csv", index=False)

    ringkasan = {
        "baris_rekonsiliasi": int(len(df_rekon)),
        "pasangan_rekonsiliasi": int(len(berpasangan_df)),
        "selisih_median": round(float(berpasangan_df["selisih"].median()), 4),
    }
    return df_rekon, ringkasan
