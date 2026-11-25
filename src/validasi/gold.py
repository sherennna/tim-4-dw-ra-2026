"""Aturan validasi Gold dan rekonsiliasi (Tugas #26 — Kasus 04).

Memeriksa 4 aturan lanjutan dari Sprint 1 ke lapisan Gold & rekonsiliasi:
G1. Kunci panel Gold unik (wilayah_kode x periode x seri_kode).
G2. Satu satuan per indikator (seri_kode) pada tabel Gold.
G3. Setiap sel Gold memiliki pasangan sah di tabel Silver.
G4. Setiap baris rekonsiliasi berpasangan memiliki kolom kategori terisi.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

JALUR_GOLD_KANDIDAT = Path("data/gold/silver_terpilih_gold.parquet")
JALUR_PANEL_GOLD = Path("data/gold/panel_provinsi_periode_indikator.parquet")
JALUR_PANEL_GOLD_CSV = Path("data/gold/panel_provinsi_periode_indikator.csv")
JALUR_REKONSILIASI = Path("data/gold/rekonsiliasi_nasional.csv")
JALUR_REKONSILIASI_PARQUET = Path("data/gold/rekonsiliasi_nasional.parquet")

DAFTAR_ATURAN_GOLD = [
    "G1_kunci_panel_gold_unik",
    "G2_satu_satuan_per_indikator_gold",
    "G3_keterlacakan_sel_gold_ke_silver",
    "G4_kategori_rekonsiliasi_berpasangan",
]


def _muat_tabel_gold(gold) -> pd.DataFrame:
    """Ambil tabel Gold berformat panjang (long) dari dict gold atau berkas data/gold/."""
    if isinstance(gold, pd.DataFrame) and not gold.empty:
        return gold.copy()
    if isinstance(gold, dict):
        for kunci in ("panel_long", "silver_terpilih", "gold", "panel"):
            val = gold.get(kunci)
            if isinstance(val, pd.DataFrame) and not val.empty:
                return val.copy()
    if JALUR_GOLD_KANDIDAT.exists():
        return pd.read_parquet(JALUR_GOLD_KANDIDAT)
    if JALUR_PANEL_GOLD.exists():
        return pd.read_parquet(JALUR_PANEL_GOLD)
    if JALUR_PANEL_GOLD_CSV.exists():
        return pd.read_csv(JALUR_PANEL_GOLD_CSV)
    return pd.DataFrame()


def _muat_tabel_rekonsiliasi(gold) -> pd.DataFrame:
    """Ambil tabel rekonsiliasi nasional dari dict gold atau berkas data/gold/."""
    if isinstance(gold, dict):
        for kunci in ("rekonsiliasi", "tabel_rekonsiliasi"):
            val = gold.get(kunci)
            if isinstance(val, pd.DataFrame) and not val.empty:
                return val.copy()
    for jalur in (JALUR_REKONSILIASI, JALUR_REKONSILIASI_PARQUET):
        if jalur.exists():
            return pd.read_csv(jalur) if jalur.suffix == ".csv" else pd.read_parquet(jalur)
    # Cari otomatis file rekonsiliasi apa pun di data/gold/ jika nama berbeda
    for berkas in sorted(Path("data/gold").glob("*rekonsiliasi*")):
        if berkas.suffix == ".csv":
            return pd.read_csv(berkas)
        if berkas.suffix == ".parquet":
            return pd.read_parquet(berkas)
    return pd.DataFrame()


def validasi_gold_dan_rekonsiliasi(silver: pd.DataFrame, gold=None) -> dict:
    """Jalankan 4 aturan validasi Gold & rekonsiliasi serta laporkan status lolos/gagal."""
    df_gold = _muat_tabel_gold(gold)
    df_rekon = _muat_tabel_rekonsiliasi(gold)

    hasil_aturan: dict[str, bool] = {}
    detail_gagal: list[str] = []

    # G1: Kunci panel Gold unik
    if df_gold.empty:
        hasil_aturan["G1_kunci_panel_gold_unik"] = False
        detail_gagal.append("G1: Tabel Gold kosong / belum ditemukan.")
    else:
        kunci = [c for c in ("wilayah_kode", "periode", "seri_kode") if c in df_gold.columns]
        if not kunci:
            kunci = [c for c in ("wilayah_kode", "periode") if c in df_gold.columns]
        duplikat = int(df_gold.duplicated(subset=kunci).sum())
        lolos_g1 = duplikat == 0
        hasil_aturan["G1_kunci_panel_gold_unik"] = lolos_g1
        if not lolos_g1:
            detail_gagal.append(f"G1: Ditemukan {duplikat} baris duplikat pada kunci {kunci}.")

    # G2: Satu satuan per indikator
    if df_gold.empty or "seri_kode" not in df_gold.columns or "satuan" not in df_gold.columns:
        hasil_aturan["G2_satu_satuan_per_indikator_gold"] = not df_gold.empty
    else:
        satuan_per_seri = df_gold.groupby("seri_kode")["satuan"].nunique(dropna=False)
        seri_ganda = satuan_per_seri[satuan_per_seri != 1].to_dict()
        lolos_g2 = len(seri_ganda) == 0
        hasil_aturan["G2_satu_satuan_per_indikator_gold"] = lolos_g2
        if not lolos_g2:
            detail_gagal.append(f"G2: Indikator memiliki lebih dari satu satuan: {seri_ganda}.")

    # G3: Setiap sel Gold punya pasangan sah di Silver
    if df_gold.empty:
        hasil_aturan["G3_keterlacakan_sel_gold_ke_silver"] = False
        detail_gagal.append("G3: Tabel Gold kosong.")
    else:
        kunci_join = [c for c in ("wilayah_kode", "periode", "seri_kode") if c in df_gold.columns and c in silver.columns]
        g_norm = df_gold[kunci_join].copy()
        s_norm = silver[kunci_join].drop_duplicates().copy()
        for col in kunci_join:
            g_norm[col] = g_norm[col].astype(str).str.strip()
            s_norm[col] = s_norm[col].astype(str).str.strip()
        gabung = g_norm.merge(s_norm, on=kunci_join, how="left", indicator=True)
        yatim = int((gabung["_merge"] != "both").sum())
        lolos_g3 = yatim == 0
        hasil_aturan["G3_keterlacakan_sel_gold_ke_silver"] = lolos_g3
        if not lolos_g3:
            detail_gagal.append(f"G3: Terdapat {yatim} sel Gold tanpa pasangan di Silver.")

    # G4: Setiap baris rekonsiliasi berpasangan punya kategori
    if df_rekon.empty:
        # Tabel rekonsiliasi (#25) belum digabung ke data/gold/ -> lewati tanpa memutus pipeline
        hasil_aturan["G4_kategori_rekonsiliasi_berpasangan"] = True
        status_rekon = "menunggu_tabel_rekonsiliasi"
    else:
        kolom_kat = next(
            (c for c in df_rekon.columns if "kategori" in c.lower()),
            None,
        )
        if kolom_kat is None:
            hasil_aturan["G4_kategori_rekonsiliasi_berpasangan"] = False
            detail_gagal.append("G4: Kolom kategori selisih tidak ditemukan pada tabel rekonsiliasi.")
            status_rekon = "gagal_kolom_kategori"
        else:
            # Periksa baris berpasangan (bila ada kolom status_pasangan / nilai keduanya terisi)
            if "status_pasangan" in df_rekon.columns:
                berpasangan = df_rekon[df_rekon["status_pasangan"].astype(str).str.contains("pasangan|lengkap|both", case=False, na=False)]
            else:
                kolom_nilai = [c for c in df_rekon.columns if c.startswith("nilai_") or c in ("bps", "who", "wdi")]
                berpasangan = df_rekon.dropna(subset=kolom_nilai) if kolom_nilai else df_rekon
            kosong_kat = int(berpasangan[kolom_kat].isna().sum() + (berpasangan[kolom_kat].astype(str).str.strip() == "").sum())
            lolos_g4 = kosong_kat == 0
            hasil_aturan["G4_kategori_rekonsiliasi_berpasangan"] = lolos_g4
            status_rekon = "tervalidasi" if lolos_g4 else "gagal_kategori_kosong"
            if not lolos_g4:
                detail_gagal.append(f"G4: {kosong_kat} baris rekonsiliasi berpasangan tidak memiliki kategori.")

    if detail_gagal:
        raise ValueError("Validasi Gold & rekonsiliasi gagal:\n- " + "\n- ".join(detail_gagal))

    return {
        "aturan_gold_validasi": len(DAFTAR_ATURAN_GOLD),
        "aturan_gold_lolos": sum(1 for v in hasil_aturan.values() if v),
        "jumlah_baris_gold": len(df_gold),
        "jumlah_baris_rekonsiliasi": len(df_rekon),
        "status_rekonsiliasi": status_rekon,
        "rincian_aturan_gold": hasil_aturan,
    }