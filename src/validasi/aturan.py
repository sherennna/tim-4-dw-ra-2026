"""Aturan validasi dasar tabel Silver (pandera) untuk Kasus 04.

Mencakup:
1. Skema dasar Silver (kolom wajib, tipe data, format periode, SHA-256 64 karakter, dan kunci unik).
2. Rentang nilai prevalensi (0..100) untuk hipertensi (var1480) dan merokok (var1435, M_Est_tob_curr_std).
3. Insidens malaria (var1393, MALARIA_EST_INCIDENCE, SH.MLR.INCD.P3) >= 0; outlier ekstrem ditandai, tidak dihapus.
4. Baris proyeksi WHO (periode > 2025) ditandai agar tidak ikut masuk ke tabel rekonsiliasi.
5. Konsistensi satu satuan per seri (seri_kode).
"""
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa

from src.common.skema import JENIS_PERIODE, KOLOM, KUNCI

SERI_PREVALENSI = {"var1480", "var1435", "M_Est_tob_curr_std"}
SERI_MALARIA = {"var1393", "MALARIA_EST_INCIDENCE", "SH.MLR.INCD.P3"}
SERI_PTM = {"NCDMORT3070"}
SERI_KASUS_04 = SERI_PREVALENSI | SERI_MALARIA | SERI_PTM


def tandai_silver(df: pd.DataFrame) -> pd.DataFrame:
    """Tambahkan/pastikan kolom penanda outlier malaria & proyeksi WHO tanpa menghapus baris."""
    hasil = df.copy()

    if "tandai_outlier" not in hasil.columns:
        nilai_num = pd.to_numeric(hasil["nilai"], errors="coerce")
        is_malaria = hasil["seri_kode"].isin(SERI_MALARIA)
        hasil["tandai_outlier"] = is_malaria & (nilai_num > 20.0)
    else:
        hasil["tandai_outlier"] = hasil["tandai_outlier"].fillna(False).astype(bool)

    if "tandai_proyeksi_who" not in hasil.columns:
        tahun_angka = pd.to_numeric(hasil["periode"].astype(str).str.slice(0, 4), errors="coerce")
        is_who = hasil["sumber"].astype(str).str.lower().isin({"who", "who_gho"})
        hasil["tandai_proyeksi_who"] = is_who & (tahun_angka > 2025)
    else:
        hasil["tandai_proyeksi_who"] = hasil["tandai_proyeksi_who"].fillna(False).astype(bool)

    return hasil


def _cek_rentang_prevalensi(df: pd.DataFrame) -> pd.Series:
    mask = df["seri_kode"].isin(SERI_PREVALENSI)
    ok = (df["nilai"] >= 0.0) & (df["nilai"] <= 100.0)
    return (~mask) | ok


def _cek_malaria_non_negatif(df: pd.DataFrame) -> pd.Series:
    mask = df["seri_kode"].isin(SERI_MALARIA)
    ok = df["nilai"] >= 0.0
    return (~mask) | ok


def _cek_satu_satuan_per_seri(df: pd.DataFrame) -> pd.Series:
    return df.groupby("seri_kode")["satuan"].transform("nunique") == 1


def _cek_penanda_proyeksi_who(df: pd.DataFrame) -> pd.Series:
    tahun_angka = pd.to_numeric(df["periode"].astype(str).str.slice(0, 4), errors="coerce")
    is_who_proyeksi = df["sumber"].astype(str).str.lower().isin({"who", "who_gho"}) & (tahun_angka > 2025)
    return (~is_who_proyeksi) | df["tandai_proyeksi_who"].astype(bool)


def skema_silver() -> pa.DataFrameSchema:
    """Bangun skema pandera lengkap untuk tabel Silver Kasus 04."""
    pola_periode = "|".join(f"(?:{p})" for p in JENIS_PERIODE.values())
    return pa.DataFrameSchema(
        {
            "sumber": pa.Column(str, nullable=False),
            "seri_kode": pa.Column(str, pa.Check.isin(sorted(SERI_KASUS_04)), nullable=False),
            "wilayah_kode": pa.Column(int, nullable=False),
            "nama_wilayah": pa.Column(str, nullable=False),
            "periode": pa.Column(str, pa.Check.str_matches(pola_periode), nullable=False),
            "jenis_periode": pa.Column(str, pa.Check.isin(list(JENIS_PERIODE)), nullable=False),
            "rincian": pa.Column(str, nullable=False),
            "nilai": pa.Column(float, nullable=False),
            "satuan": pa.Column(str, nullable=False),
            "_berkas_raw": pa.Column(str, nullable=False),
            "_sha256_raw": pa.Column(str, pa.Check.str_length(64, 64), nullable=False),
            "tandai_outlier": pa.Column(bool, nullable=False),
            "tandai_proyeksi_who": pa.Column(bool, nullable=False),
        },
        checks=[
            pa.Check(_cek_rentang_prevalensi, name="rentang_prevalensi_0_100"),
            pa.Check(_cek_malaria_non_negatif, name="malaria_non_negatif"),
            pa.Check(_cek_satu_satuan_per_seri, name="satu_satuan_per_seri"),
            pa.Check(_cek_penanda_proyeksi_who, name="penanda_proyeksi_who"),
        ],
        unique=KUNCI,
        strict=False,
    )


DAFTAR_ATURAN = [
    ("skema_dasar_dan_kunci_unik", f"kolom wajib {KOLOM}, tipe data, format periode, SHA-256, dan kunci unik {KUNCI}"),
    ("rentang_prevalensi_0_100", "nilai prevalensi (var1480, var1435, M_Est_tob_curr_std) wajib berada pada [0, 100]"),
    ("malaria_non_negatif_dan_flag_outlier", "insidens malaria (var1393, MALARIA_EST_INCIDENCE, SH.MLR.INCD.P3) >= 0; outlier ditandai tanpa dihapus"),
    ("penanda_proyeksi_who", "baris proyeksi WHO (tahun > 2025) ditandai di tandai_proyeksi_who untuk dikecualikan di rekonsiliasi"),
    ("satu_satuan_per_seri", "setiap seri_kode hanya memiliki satu satuan baku"),
]