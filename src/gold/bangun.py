"""Tahap 4: panel provinsi dan tabel nasional (Gold) dari Silver."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from .config import NASIONAL_KODE, SERI_LOG, SERI_NASIONAL, SERI_PANEL

SILVER = Path("data/silver/silver.parquet")
GOLD = Path("data/gold")


def _baca_silver() -> pd.DataFrame:
    s = pd.read_parquet(SILVER).reset_index(drop=True)
    s["silver_row_id"] = s.index.astype("int64")
    return s


def _dedup(df: pd.DataFrame, kunci: list[str]) -> pd.DataFrame:
    """Berkas json dan csv memuat observasi yang sama: nilai wajib identik, sisakan satu."""
    beda = df.groupby(kunci)["nilai"].nunique() > 1
    assert not beda.any(), f"Nilai berbeda untuk kunci yang sama:\n{beda[beda].head()}"
    df = df.sort_values(kunci + ["_berkas_raw"]).copy()
    df["silver_row_id_setara"] = (
        df.groupby(kunci)["silver_row_id"].transform(lambda x: ",".join(map(str, x))))
    return df.drop_duplicates(kunci, keep="first")


def _tambah_aturan_sel(df: pd.DataFrame) -> pd.DataFrame:
    df["flag_sel"] = np.where(
        df["tandai_proyeksi_who"], "proyeksi_who",
        np.where(df["tandai_outlier"], "outlier_dipertahankan", "ok"))
    df["nilai_log1p"] = np.where(
        df["indikator"].isin(SERI_LOG), np.log1p(df["nilai"].clip(lower=0)), np.nan)
    return df.rename(columns={"_berkas_raw": "berkas_raw", "_sha256_raw": "sha256_raw"})


def bangun_panel(s: pd.DataFrame) -> pd.DataFrame:
    p = s[s["seri_kode"].isin(SERI_PANEL) & (s["wilayah_kode"] != NASIONAL_KODE)]
    assert (p["rincian"] == "total").all(), "Ada rincian selain 'total' di seri utama"
    p = _dedup(p, ["seri_kode", "wilayah_kode", "periode", "rincian"])
    p = p.rename(columns={"seri_kode": "indikator", "wilayah_kode": "provinsi_kode",
                          "nama_wilayah": "provinsi"})
    p["nama_indikator"] = p["indikator"].map(lambda k: SERI_PANEL[k]["nama"])
    p["periode"] = p["periode"].astype(int)
    p = _tambah_aturan_sel(p)
    kolom = ["provinsi_kode", "provinsi", "periode", "indikator", "nama_indikator",
             "nilai", "satuan", "nilai_log1p", "flag_sel",
             "silver_row_id", "silver_row_id_setara", "berkas_raw", "sha256_raw"]
    return p[kolom].sort_values(["indikator", "provinsi_kode", "periode"]).reset_index(drop=True)


def bangun_nasional(s: pd.DataFrame) -> pd.DataFrame:
    n = s[s["seri_kode"].isin(SERI_NASIONAL)
          | (s["seri_kode"].isin(SERI_PANEL) & (s["wilayah_kode"] == NASIONAL_KODE))]
    assert (n["wilayah_kode"] == NASIONAL_KODE).all(), "Ada wilayah non-nasional"
    n = _dedup(n, ["sumber", "seri_kode", "rincian", "periode"])
    n = n.rename(columns={"seri_kode": "indikator"})
    n["periode"] = n["periode"].astype(int)
    n["asal_angka_nasional"] = np.where(n["sumber"] == "bps", "baris Indonesia", "pembanding")
    n = _tambah_aturan_sel(n)
    kolom = ["sumber", "indikator", "rincian", "periode", "nilai", "satuan",
             "asal_angka_nasional", "nilai_log1p", "flag_sel",
             "silver_row_id", "silver_row_id_setara", "berkas_raw", "sha256_raw"]
    return n[kolom].sort_values(["sumber", "indikator", "rincian", "periode"]).reset_index(drop=True)


def _validasi(g: pd.DataFrame, kunci: list[str], s: pd.DataFrame, satuan_per: list[str]) -> None:
    assert not g.duplicated(kunci).any(), f"Kunci kembar: {kunci}"
    assert g["nilai"].notna().all(), "Ada nilai kosong"
    assert (g.groupby(satuan_per)["satuan"].nunique() == 1).all(), "Satuan campur"
    # jejak: setiap baris Gold harus cocok dengan baris Silver asalnya
    m = g.merge(s[["silver_row_id", "nilai", "_sha256_raw", "_berkas_raw"]],
                on="silver_row_id", how="left", suffixes=("", "_silver"))
    assert m["nilai_silver"].notna().all(), "silver_row_id tidak ditemukan di Silver"
    assert (m["nilai"] == m["nilai_silver"]).all(), "Nilai Gold berbeda dari Silver"
    assert (m["sha256_raw"] == m["_sha256_raw"]).all(), "sha256 tidak cocok"


def tulis_gold() -> dict:
    s = _baca_silver()
    for k, c in SERI_PANEL.items():  # satuan baku harus sama dengan Silver
        assert set(s.loc[s["seri_kode"] == k, "satuan"]) == {c["satuan"]}, f"Satuan {k} berubah"
    panel, nas = bangun_panel(s), bangun_nasional(s)
    _validasi(panel, ["provinsi_kode", "periode", "indikator"], s, ["indikator"])
    _validasi(nas, ["sumber", "indikator", "rincian", "periode"], s, ["sumber", "indikator"])
    GOLD.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(GOLD / "panel_provinsi.parquet", index=False)
    nas.to_parquet(GOLD / "nasional.parquet", index=False)
    return {"seri_panel": panel["indikator"].nunique(), "baris_panel": len(panel),
            "baris_nasional": len(nas), "baris_gold": len(panel) + len(nas)}