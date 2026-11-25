"""Tahap 2–4 — Profil, pembersihan, dan penyeragaman ke Silver (pertemuan II–VII).

Keluaran: data/silver/silver.parquet dengan skema minimal di src/common/skema.py
serta aturan validasi Pandera Kasus 04 di src/validasi/aturan.py.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from src.common.skema import KOLOM, KUNCI
from src.validasi.aturan import tandai_silver

JALUR_KELUARAN = Path("data/silver/silver.parquet")

SATUAN_BAKU = {
    "var1393": "per 1.000 penduduk",
    "var1480": "persen",
    "var1435": "persen",
    "MALARIA_EST_INCIDENCE": "per 1.000 penduduk berisiko",
    "NCDMORT3070": "persen",
    "M_Est_tob_curr_std": "persen",
    "SH.MLR.INCD.P3": "per 1.000 penduduk berisiko",
}

KOLOM_NILAI_WHO = {
    "MALARIA_EST_INCIDENCE": "RATE_PER_1000_N",
    "NCDMORT3070": "RATE_PER_100_N",
    "M_Est_tob_curr_std": "PERCENT_POP_N",
}


def _bersihkan_bps(df_bps: pd.DataFrame) -> pd.DataFrame:
    df = df_bps.copy()
    df["nilai"] = pd.to_numeric(df["nilai"], errors="coerce")
    df = df[df["nilai"].notna()].copy()

    df["sumber"] = "bps"
    df["wilayah_kode"] = df["wilayah_id"].astype(str).str.strip().astype(int)
    df["nama_wilayah"] = df["wilayah"].astype(str).str.strip()
    df["periode"] = df["tahun"].astype(str).str.strip()
    df["jenis_periode"] = "tahun"

    rincian_raw = df["turvar"].astype(str).str.strip()
    df["rincian"] = rincian_raw.where(rincian_raw.str.lower() != "tidak ada", "total")
    df["satuan"] = df["seri_kode"].map(SATUAN_BAKU)

    df = df[KOLOM].drop_duplicates(subset=KUNCI, keep="last")
    return df


def _format_rincian_who(row: pd.Series) -> str:
    bagian = []
    sex = str(row.get("DIM_SEX", "")).strip()
    age = str(row.get("DIM_AGE", "")).strip()
    if sex and sex.lower() != "nan":
        bagian.append(f"jenis_kelamin={sex}")
    if age and age.lower() != "nan":
        bagian.append(f"usia={age}")
    return "|".join(bagian) if bagian else "total"


def _bersihkan_who(df_who: pd.DataFrame) -> pd.DataFrame:
    df = df_who.copy()
    if "seri_kode" not in df.columns and "IND_CODE" in df.columns:
        df["seri_kode"] = df["IND_CODE"].astype(str).str.strip()

    df = df[df["seri_kode"].isin(KOLOM_NILAI_WHO)].copy()

    nilai_list = []
    for seri, kol_nilai in KOLOM_NILAI_WHO.items():
        sub = df[df["seri_kode"] == seri].copy()
        if kol_nilai in sub.columns:
            sub["nilai"] = pd.to_numeric(sub[kol_nilai], errors="coerce")
        else:
            sub["nilai"] = pd.to_numeric(sub["nilai"], errors="coerce")
        nilai_list.append(sub)
    df = pd.concat(nilai_list, ignore_index=True)
    df = df[df["nilai"].notna()].copy()

    df["sumber"] = "who_gho"
    df["wilayah_kode"] = 9999
    df["nama_wilayah"] = df["GEO_NAME_SHORT"].astype(str).str.strip().replace("", "Indonesia")
    df["periode"] = df["DIM_TIME"].astype(str).str.strip()
    df["jenis_periode"] = "tahun"
    df["rincian"] = df.apply(_format_rincian_who, axis=1)
    df["satuan"] = df["seri_kode"].map(SATUAN_BAKU)

    df = df[KOLOM].drop_duplicates(subset=KUNCI, keep="last")
    return df


def _bersihkan_wdi(df_wdi: pd.DataFrame) -> pd.DataFrame:
    df = df_wdi.copy()
    df = df[df["indicator_id"] == "SH.MLR.INCD.P3"].copy()
    if "countryiso3code" in df.columns:
        df = df[df["countryiso3code"].astype(str).str.upper() == "IDN"].copy()

    df["nilai"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["nilai"].notna()].copy()

    df["sumber"] = "wdi"
    df["seri_kode"] = "SH.MLR.INCD.P3"
    df["wilayah_kode"] = 9999
    df["nama_wilayah"] = "Indonesia"
    df["periode"] = df["date"].astype(str).str.strip()
    df["jenis_periode"] = "tahun"
    df["rincian"] = "total"
    df["satuan"] = df["seri_kode"].map(SATUAN_BAKU)

    df = df[KOLOM].drop_duplicates(subset=KUNCI, keep="last")
    return df


def susun_silver(mentah: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Gabungkan hasil pembersihan BPS, WHO GHO, dan WDI sesuai skema baku Silver."""
    bagian = [
        _bersihkan_bps(mentah["bps"]),
        _bersihkan_who(mentah["who_gho"]),
        _bersihkan_wdi(mentah["wdi"]),
    ]
    silver = pd.concat(bagian, ignore_index=True)

    silver["wilayah_kode"] = silver["wilayah_kode"].astype(int)
    silver["nilai"] = silver["nilai"].astype(float)
    for kol in ["sumber", "seri_kode", "nama_wilayah", "periode", "jenis_periode", "rincian", "satuan", "_berkas_raw", "_sha256_raw"]:
        silver[kol] = silver[kol].astype(str)

    silver = (
        silver.sort_values(["sumber", "seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"])
        .drop_duplicates(subset=["sumber", "seri_kode", "wilayah_kode", "periode", "rincian"], keep="first")
        .reset_index(drop=True)
    )
    silver = tandai_silver(silver)
    return silver

def ringkas(silver: pd.DataFrame) -> dict[str, int]:
    """Hitung metrik Silver untuk results/<nim>/metrics.json."""
    return {
        "seri_silver": int(silver["seri_kode"].nunique()),
        "rincian_dienkode": int(silver["rincian"].nunique()),
        "baris_silver": int(len(silver)),
    }


def jalankan(mentah: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Terima keluaran tahap 1, tulis data/silver/silver.parquet, dan kembalikan DataFrame Silver."""
    if mentah is None:
        from src.ekstraksi import jalankan as jalankan_ekstraksi
        mentah = jalankan_ekstraksi()

    silver = susun_silver(mentah)
    JALUR_KELUARAN.parent.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(JALUR_KELUARAN, index=False)

    r = ringkas(silver)
    print(f"silver     : {r['baris_silver']} baris, {r['seri_silver']} seri, {r['rincian_dienkode']} rincian -> {JALUR_KELUARAN}")
    return silver


if __name__ == "__main__":
    df_silver = jalankan()
    r = ringkas(df_silver)
    print("\nSalin ke terminal untuk metrics.json:")
    print("python -m src.common.hasil 124450023 " + " ".join(f"{k}={v}" for k, v in r.items()))
