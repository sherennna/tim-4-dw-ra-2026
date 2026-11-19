"""Tahap 1 (ekstraksi): pembaca berkas World Bank WDI (JSON WebAPI v2).

Setiap berkas berbentuk [kepala_halaman, [rekaman, ...]]. Kepala memuat 'total' (jumlah rekaman
di seluruh halaman); pembaca memastikan jumlah rekaman yang dibaca sama dengan total itu, sehingga
halaman yang hilang ketahuan. Nilai kosong (null) dipertahankan sebagai NaN, tidak dibuang.

Uji cepat:  python -m src.ekstraksi.wdi
"""
import json
from pathlib import Path

import pandas as pd

from src.common.manifest import RAW
from src.ekstraksi.umum import tabel_dari_rekaman, tempel_lineage

SNAPSHOT = "wdi/2026-10-20"

JSON_DATA = ["data/kelompok-05-hal-01.json"]
JSON_SUMBER = "metadata/sumber.json"
JSON_INDIKATOR = ["metadata/sumber2_indikator.json", "metadata/sumber46_indikator.json"]


def _baca_halaman(nama):
    berkas = f"{SNAPSHOT}/{nama}"
    with open(Path(RAW) / berkas, encoding="utf-8-sig") as f:
        obj = json.load(f)
    if not (isinstance(obj, list) and len(obj) == 2 and isinstance(obj[1], list)):
        raise ValueError(f"{berkas}: bentuk bukan [kepala, rekaman]; kemungkinan respons galat API")
    kepala, rekaman = obj
    total, halaman = int(kepala["total"]), int(kepala["pages"])
    if halaman != 1:
        raise ValueError(f"{berkas}: {halaman} halaman, tetapi hanya satu berkas per halaman tersedia")
    if len(rekaman) != total:
        raise ValueError(f"{berkas}: {len(rekaman)} rekaman terbaca, kepala menyatakan total {total}")
    return berkas, rekaman


def _baca_tabel(nama):
    berkas, rekaman = _baca_halaman(nama)
    return tempel_lineage(tabel_dari_rekaman(rekaman), "wdi", berkas, "json")


def baca_data():
    """Data indikator (negara x indikator x tahun). Semua indikator di berkas dipertahankan."""
    return pd.concat([_baca_tabel(n) for n in JSON_DATA], ignore_index=True)


def baca_sumber():
    return _baca_tabel(JSON_SUMBER)


def baca_indikator():
    return pd.concat([_baca_tabel(n) for n in JSON_INDIKATOR], ignore_index=True)


def baca_semua():
    """{nama_tabel: DataFrame} untuk semua berkas WDI."""
    return {"wdi": baca_data(), "wdi_sumber": baca_sumber(), "wdi_indikator": baca_indikator()}


if __name__ == "__main__":
    for nama, df in baca_semua().items():
        print(f"{nama}: {df['_berkas_raw'].nunique()} berkas, {len(df)} baris, {df.shape[1]} kolom")
