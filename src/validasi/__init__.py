"""Tahap 8 — Validasi dasar Silver (pandera) untuk Kasus 04."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandera.pandas as pa

from src.common.skema import periksa_silver
from src.validasi.aturan import DAFTAR_ATURAN, skema_silver, tandai_silver

JALUR_SILVER_DEFAULT = Path("data/silver/silver.parquet")


def validasi_silver(df: pd.DataFrame) -> dict:
    """Jalankan pemeriksaan lantai skema.py + validasi pandera Kasus 04."""
    pelanggaran_lantai = periksa_silver(df)
    if pelanggaran_lantai:
        raise ValueError(f"Tabel Silver gagal pemeriksaan dasar skema.py: {pelanggaran_lantai}")

    df_bertanda = tandai_silver(df)
    skema = skema_silver()

    try:
        df_valid = skema.validate(df_bertanda, lazy=True)
    except pa.errors.SchemaErrors as err:
        raise ValueError(f"Validasi pandera Silver gagal:\n{err.failure_cases}") from err

    return {
        "df_silver": df_valid,
        "aturan_validasi": len(DAFTAR_ATURAN),
        "aturan_lolos": len(DAFTAR_ATURAN),
        "jumlah_baris": len(df_valid),
        "baris_outlier_malaria": int(df_valid["tandai_outlier"].sum()),
        "baris_proyeksi_who": int(df_valid["tandai_proyeksi_who"].sum()),
    }


def jalankan(silver: pd.DataFrame | None = None, gold=None) -> dict:
    """Titik masuk dari pipeline.py (tidak bergantung pada Gold Sprint 3 bila silver sudah ada)."""
    if silver is None:
        if not JALUR_SILVER_DEFAULT.exists():
            raise FileNotFoundError(
                f"{JALUR_SILVER_DEFAULT} belum ditemukan. Pastikan tahap Silver sudah menghasilkan berkas parquet."
            )
        silver = pd.read_parquet(JALUR_SILVER_DEFAULT)

    ringkasan = validasi_silver(silver)
    print(
        f"validasi   : {ringkasan['aturan_lolos']}/{ringkasan['aturan_validasi']} aturan lolos "
        f"({ringkasan['jumlah_baris']} baris; outlier_malaria={ringkasan['baris_outlier_malaria']}, "
        f"proyeksi_who={ringkasan['baris_proyeksi_who']})"
    )
    return ringkasan


def _contoh_uji_sintetis() -> pd.DataFrame:
    """Data uji mandiri bila data/silver/silver.parquet belum digabungkan ke main."""
    sha_dummy = "a" * 64
    return pd.DataFrame(
        [
            {
                "sumber": "bps",
                "seri_kode": "var1393",
                "wilayah_kode": 9400,
                "nama_wilayah": "PAPUA",
                "periode": "2021",
                "jenis_periode": "tahun",
                "rincian": "total",
                "nilai": 80.05,
                "satuan": "per 1.000 penduduk",
                "_berkas_raw": "bps/2026-10-20/sdg3_3_3_3_v1393.csv",
                "_sha256_raw": sha_dummy,
            },
            {
                "sumber": "bps",
                "seri_kode": "var1480",
                "wilayah_kode": 9999,
                "nama_wilayah": "INDONESIA",
                "periode": "2018",
                "jenis_periode": "tahun",
                "rincian": "total",
                "nilai": 34.1,
                "satuan": "persen",
                "_berkas_raw": "bps/2026-10-20/sdg3_3_4_1_b_v1480.csv",
                "_sha256_raw": sha_dummy,
            },
            {
                "sumber": "who_gho",
                "seri_kode": "M_Est_tob_curr_std",
                "wilayah_kode": 9999,
                "nama_wilayah": "Indonesia",
                "periode": "2030",
                "jenis_periode": "tahun",
                "rincian": "jenis_kelamin=TOTAL",
                "nilai": 36.2,
                "satuan": "persen",
                "_berkas_raw": "who_gho/2026-10-20/datadot/75DDA77_M_Est_tob_curr_std.csv",
                "_sha256_raw": sha_dummy,
            },
        ]
    )


if __name__ == "__main__":
    if JALUR_SILVER_DEFAULT.exists():
        jalankan()
    else:
        print("Info: data/silver/silver.parquet belum ada di branch ini; menjalankan uji mandiri skema validasi...")
        hasil = validasi_silver(_contoh_uji_sintetis())
        print(
            f"Uji mandiri LOLOS: {hasil['aturan_lolos']}/{hasil['aturan_validasi']} aturan, "
            f"outlier_malaria={hasil['baris_outlier_malaria']}, proyeksi_who={hasil['baris_proyeksi_who']}"
        )