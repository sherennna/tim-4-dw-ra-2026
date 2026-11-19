"""Tahap 1 (ekstraksi): catatan unduhan BPS (manifest_asal.json) sebagai tabel.

Satu baris per tabel BPS yang diunduh (termasuk yang bukan milik kasus ini): judul, satuan katalog,
jumlah baris, sha256 JSON asal. Ini metadata; dipakai untuk uji silang dan menetapkan satuan nanti.
"""
import json
from pathlib import Path

import pandas as pd

from src.common.manifest import RAW
from src.ekstraksi.umum import tabel_dari_rekaman, tempel_lineage

BERKAS = "bps/2026-10-20/manifest_asal.json"


def baca_katalog():
    with open(Path(RAW) / BERKAS, encoding="utf-8-sig") as f:
        obj = json.load(f)
    df = tabel_dari_rekaman([{"nama_tabel": nama, **isi} for nama, isi in obj["tabel"].items()])
    if obj.get("gagal"):
        raise ValueError(f"{BERKAS}: ada unduhan gagal: {list(obj['gagal'])[:5]}")
    return tempel_lineage(df, "bps", BERKAS, "json")
