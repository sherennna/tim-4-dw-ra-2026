"""Tahap 4-6 - Reshape, integrasi, dan penyimpanan ke Gold (Sprint 2)."""

from pathlib import Path
import pandas as pd

from src.gold.nasional import bangun_tabel_nasional


def jalankan(silver: pd.DataFrame, out_dir: str = "data/gold"):
    tabel_nasional = bangun_tabel_nasional(silver, out_dir=out_dir)
    return {"nasional_gold": tabel_nasional}

