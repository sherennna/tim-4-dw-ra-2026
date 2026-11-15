"""Pembantu bersama pembaca tahap 1: lineage dan perataan JSON.

Aturan tahap 1 tetap: tidak ada baris yang dibuang, dibetulkan, atau ditafsirkan.
"""
import json

import pandas as pd

from src.common.manifest import sha256_raw


def tempel_lineage(df, sumber, berkas, fmt):
    """Tambahkan sumber, format, baris_asal, _berkas_raw, _sha256_raw. Nilai kolom lain tidak diubah.

    baris_asal = urutan baris data di berkas (mulai 1); untuk CSV artinya baris ke-n setelah header.
    """
    df = df.copy()
    df["sumber"] = sumber
    df["format"] = fmt
    df["baris_asal"] = range(1, len(df) + 1)
    df["_berkas_raw"] = berkas
    df["_sha256_raw"] = sha256_raw(berkas)   # jangan ditulis tangan
    return df


def ratakan(rekaman, pisah="_"):
    """Ratakan dict bersarang satu tingkat demi satu: {'a': {'b': 1}} -> {'a_b': 1}.

    Daftar tidak diratakan; disimpan sebagai teks JSON agar tidak ada isi yang hilang.
    """
    hasil = {}
    for k, v in rekaman.items():
        if isinstance(v, dict):
            for k2, v2 in ratakan(v, pisah).items():
                hasil[f"{k}{pisah}{k2}"] = v2
        elif isinstance(v, list):
            hasil[k] = json.dumps(v, ensure_ascii=False)
        else:
            hasil[k] = v
    return hasil


def tabel_dari_rekaman(daftar):
    """Daftar dict (mungkin bersarang) -> DataFrame, semua kolom asal dipertahankan."""
    return pd.DataFrame([ratakan(r) for r in daftar])
