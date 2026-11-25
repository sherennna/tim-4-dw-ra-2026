"""Tahap 4–6 — Reshape, integrasi, dan penyimpanan ke Gold (Sprint 2)."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
from src.gold.aturan import pilih_satu_nilai_per_sel

JALUR_SILVER_DEFAULT = Path("data/silver/silver.parquet")
JALUR_KANDIDAT_GOLD = Path("data/gold/silver_terpilih_gold.parquet")


def jalankan(silver: pd.DataFrame | None = None) -> dict:
    """Pilih satu nilai per sel Gold dari Silver dan tulis keluaran seleksi."""
    if silver is None:
        silver = pd.read_parquet(JALUR_SILVER_DEFAULT)

    df_terpilih, ringkasan = pilih_satu_nilai_per_sel(silver)
    JALUR_KANDIDAT_GOLD.parent.mkdir(parents=True, exist_ok=True)
    df_terpilih.to_parquet(JALUR_KANDIDAT_GOLD, index=False)

    print(
        f"gold       : {ringkasan['total_terpilih_gold']} / {ringkasan['total_silver_awal']} baris terpilih "
        f"(disaring: snapshot={ringkasan['ditolak_snapshot_csv_bps']}, "
        f"rincian={ringkasan['ditolak_rincian_tidak_sebanding']}, "
        f"periode/proyeksi={ringkasan['ditolak_proyeksi_dan_periode']}; "
        f"outlier_terbawa={ringkasan['outlier_terbawa']}, "
        f"patahan_terbawa={ringkasan['patahan_wilayah_terbawa']})"
    )
    return {
        "silver_terpilih": df_terpilih,
        "ringkasan_aturan": ringkasan,
    }