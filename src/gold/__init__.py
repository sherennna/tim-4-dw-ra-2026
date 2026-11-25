"""Tahap 4–6 — Reshape, integrasi, dan penyimpanan ke Gold (Sprint 2)."""
import pandas as pd

from src.gold.bangun import tulis_gold
from src.gold.nasional import bangun_tabel_nasional

JALUR_SILVER = "data/silver/silver.parquet"


def jalankan(silver: pd.DataFrame | None = None, out_dir: str = "data/gold"):
    """Tahap 4: panel provinsi Gold (bangun.py) + tabel nasional periode x seri (nasional.py)."""
    r = tulis_gold()
    print(f"gold       : {r['baris_panel']} baris panel ({r['seri_panel']} seri) + "
          f"{r['baris_nasional']} baris nasional -> data/gold/")

    if silver is None:
        silver = pd.read_parquet(JALUR_SILVER)
    r["nasional_gold"] = bangun_tabel_nasional(silver, out_dir=out_dir)
    return r