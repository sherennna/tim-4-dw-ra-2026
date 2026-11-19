"""Tahap 1 — Ekstraksi (pertemuan X). Milik tim.

Baca setiap berkas di data/raw/ (CSV, JSON WebAPI BPS, JSON WDI, CSV dan JSON WHO GHO) menjadi
DataFrame mentah yang setia pada sumbernya: jangan membersihkan di sini, cukup ratakan struktur
dan catat asal tiap baris (`_berkas_raw` relatif data/raw/, `_sha256_raw` dari src.common.manifest).

Pembaca per sumber: bps.py (+ bps_katalog.py), who_gho.py, wdi.py. Pembantu bersama: umum.py.
Ringkasan angka untuk bukti artefak:  python -m src.ekstraksi
"""
from src.common.manifest import RAW, baca
from src.ekstraksi import bps, bps_katalog, who_gho, wdi


def jalankan():
    """Kembalikan {nama_tabel: DataFrame mentah}.

    Tabel data (dipakai Silver): "bps", "who_gho", "wdi".
    Tabel metadata (katalog, untuk satuan dan nama): "bps_katalog", "who_gho_ddi",
    "who_gho_indikator", "wdi_sumber", "wdi_indikator".

    Galat bila ada berkas di MANIFEST.csv yang tidak terbaca (atau sebaliknya).
    """
    tabel = {"bps": bps.baca_semua(), "bps_katalog": bps_katalog.baca_katalog()}
    tabel.update(who_gho.baca_semua())
    tabel.update(wdi.baca_semua())
    _periksa_kelengkapan(tabel)
    return tabel


def _periksa_kelengkapan(tabel):
    """Cocokkan berkas yang terbaca dengan MANIFEST.csv: tidak boleh ada yang terlewat."""
    dibaca = set()
    for df in tabel.values():
        dibaca |= set(df["_berkas_raw"])
    manifest = set(baca(RAW))
    terlewat, tak_dikenal = sorted(manifest - dibaca), sorted(dibaca - manifest)
    if terlewat or tak_dikenal:
        raise RuntimeError(f"ekstraksi tidak cocok dengan MANIFEST.csv; terlewat: {terlewat}; "
                           f"tidak ada di manifest: {tak_dikenal}")


def ringkas(tabel):
    """Angka untuk results/<nim>/metrics.json: berkas_dibaca, baris_mentah, format."""
    berkas = set().union(*(set(df["_berkas_raw"]) for df in tabel.values()))
    formats = set().union(*(set(df["format"]) for df in tabel.values()))
    return {"berkas_dibaca": len(berkas), "baris_mentah": sum(len(df) for df in tabel.values()),
            "format": len(formats)}
