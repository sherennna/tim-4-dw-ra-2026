"""Tahap 4–6 — Reshape, integrasi, dan penyimpanan ke Gold (Sprint 2)."""
from .bangun import tulis_gold


def jalankan(silver=None):
    """Tahap 4: tulis panel provinsi dan tabel nasional Gold dari data/silver/silver.parquet."""
    r = tulis_gold()
    print(f"gold       : {r['baris_panel']} baris panel ({r['seri_panel']} seri) + "
          f"{r['baris_nasional']} baris nasional -> data/gold/")
    return r