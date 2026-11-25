"""Tahap 4-6 - Reshape, integrasi, rekonsiliasi, dan penyimpanan ke Gold (Sprint 2)."""
import pandas as pd

from src.gold.bangun import tulis_gold
from src.gold.rekonsiliasi import bangun_tabel_rekonsiliasi

JALUR_SILVER = "data/silver/silver.parquet"


def jalankan(silver: pd.DataFrame | None = None, out_dir: str = "data/gold"):
    """Tahap 4 & 6: panel provinsi + tabel nasional + tabel rekonsiliasi nasional Gold."""
    r = tulis_gold()
    df_rekon, info_rekon = bangun_tabel_rekonsiliasi(out_dir=out_dir)
    r.update(info_rekon)
    r["rekonsiliasi"] = df_rekon
    print(
        f"gold       : {r['baris_panel']} baris panel ({r['seri_panel']} seri) + "
        f"{r['baris_nasional']} baris nasional + {r['baris_rekonsiliasi']} baris rekonsiliasi "
        f"({r['pasangan_rekonsiliasi']} berpasangan) -> {out_dir}/"
    )
    return r
