"""Tahap 1 (ekstraksi): pembaca berkas WHO GHO (CSV datadot, JSON katalog datadot, JSON OData).

Tiga CSV data punya kolom nilai berbeda (RATE_PER_100_N, RATE_PER_1000_N, PERCENT_POP_N, ...).
Kolom asal dipertahankan apa adanya; kolom yang tidak ada di suatu berkas bernilai kosong (NaN)
pada baris berkas itu. Penyeragaman nama dan satuan dikerjakan di Silver.

Uji cepat:  python -m src.ekstraksi.who_gho
"""
import json
from pathlib import Path

import pandas as pd

from src.common.manifest import RAW
from src.ekstraksi.umum import tabel_dari_rekaman, tempel_lineage

SNAPSHOT = "who_gho/2026-10-20"

# Berkas data (CSV datadot), satu per indikator.
CSV_DATA = [
    "datadot/1F96863_NCDMORT3070.csv",
    "datadot/442CEA8_MALARIA_EST_INCIDENCE.csv",
    "datadot/75DDA77_M_Est_tob_curr_std.csv",
]
JSON_DDI = "datadot/ddiindicators_skip0000.json"     # katalog metadata indikator datadot
JSON_INDIKATOR = "odata/Indicator.json"              # daftar kode dan nama indikator GHO


def baca_csv(nama):
    berkas = f"{SNAPSHOT}/{nama}"
    # dtype=str dan keep_default_na=False: tidak ada nilai yang diubah atau hilang diam-diam.
    df = pd.read_csv(Path(RAW) / berkas, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return tempel_lineage(df, "who_gho", berkas, "csv")


def baca_data():
    """Gabungkan tiga CSV data WHO GHO. Kolom = gabungan kolom asal ketiga berkas."""
    return pd.concat([baca_csv(n) for n in CSV_DATA], ignore_index=True, sort=False)


def _baca_value(nama):
    """Berkas OData/datadot: {'@odata.context': ..., 'value': [rekaman, ...]}."""
    berkas = f"{SNAPSHOT}/{nama}"
    with open(Path(RAW) / berkas, encoding="utf-8-sig") as f:
        obj = json.load(f)
    if "value" not in obj or not obj["value"]:
        raise ValueError(f"{berkas}: tidak ada daftar 'value' yang terbaca")
    return berkas, obj["value"]


def baca_ddi():
    berkas, isi = _baca_value(JSON_DDI)
    return tempel_lineage(tabel_dari_rekaman(isi), "who_gho", berkas, "json")


def baca_indikator():
    berkas, isi = _baca_value(JSON_INDIKATOR)
    return tempel_lineage(tabel_dari_rekaman(isi), "who_gho", berkas, "json")


def baca_semua():
    """{nama_tabel: DataFrame} untuk semua berkas WHO GHO."""
    return {"who_gho": baca_data(), "who_gho_ddi": baca_ddi(), "who_gho_indikator": baca_indikator()}


if __name__ == "__main__":
    for nama, df in baca_semua().items():
        print(f"{nama}: {df['_berkas_raw'].nunique()} berkas, {len(df)} baris, {df.shape[1]} kolom")
