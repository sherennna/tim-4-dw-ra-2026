"""Aturan validasi Gold dan rekonsiliasi (Tugas #26 — Kasus 04).

Memeriksa 4 aturan lanjutan dari Sprint 1 pada keluaran aktual Gold & rekonsiliasi:
G1. Kunci panel Gold unik (provinsi_kode x periode x indikator pada panel provinsi,
    serta sumber x indikator x rincian x periode pada tabel nasional).
G2. Satu satuan per indikator (indikator / seri_kode) pada tabel Gold.
G3. Setiap sel Gold memiliki pasangan sah di tabel Silver (terlacak via kunci & silver_row_id).
G4. Setiap baris rekonsiliasi berpasangan memiliki kolom kategori_penjelasan terisi.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

JALUR_PANEL_PROVINSI = Path("data/gold/panel_provinsi.parquet")
JALUR_NASIONAL = Path("data/gold/nasional.parquet")
JALUR_SILVER_TERPILIH = Path("data/gold/silver_terpilih_gold.parquet")
JALUR_REKONSILIASI_CSV = Path("data/gold/rekonsiliasi_nasional.csv")
JALUR_REKONSILIASI_PARQUET = Path("data/gold/rekonsiliasi_nasional.parquet")

DAFTAR_ATURAN_GOLD = [
    "G1_kunci_panel_gold_unik",
    "G2_satu_satuan_per_indikator_gold",
    "G3_keterlacakan_sel_gold_ke_silver",
    "G4_kategori_rekonsiliasi_berpasangan",
]


def _muat_panel_provinsi(gold) -> pd.DataFrame:
    if isinstance(gold, pd.DataFrame) and not gold.empty:
        return gold.copy()
    if isinstance(gold, dict):
        for kunci in ("panel_provinsi", "panel_long", "gold", "panel"):
            val = gold.get(kunci)
            if isinstance(val, pd.DataFrame) and not val.empty:
                return val.copy()
    for jalur in (JALUR_PANEL_PROVINSI, JALUR_SILVER_TERPILIH):
        if jalur.exists():
            return pd.read_parquet(jalur)
    return pd.DataFrame()


def _muat_tabel_nasional(gold) -> pd.DataFrame:
    if isinstance(gold, dict) and isinstance(gold.get("nasional"), pd.DataFrame):
        return gold["nasional"].copy()
    if JALUR_NASIONAL.exists():
        return pd.read_parquet(JALUR_NASIONAL)
    return pd.DataFrame()


def _muat_tabel_rekonsiliasi(gold) -> pd.DataFrame:
    if isinstance(gold, dict):
        for kunci in ("rekonsiliasi", "tabel_rekonsiliasi"):
            val = gold.get(kunci)
            if isinstance(val, pd.DataFrame) and not val.empty:
                return val.copy()
    if JALUR_REKONSILIASI_PARQUET.exists():
        return pd.read_parquet(JALUR_REKONSILIASI_PARQUET)
    if JALUR_REKONSILIASI_CSV.exists():
        return pd.read_csv(JALUR_REKONSILIASI_CSV)
    return pd.DataFrame()


def validasi_gold_dan_rekonsiliasi(silver: pd.DataFrame, gold=None) -> dict:
    """Jalankan 4 aturan validasi Gold & rekonsiliasi pada keluaran aktual dan cetak rinciannya."""
    df_panel = _muat_panel_provinsi(gold)
    df_nasional = _muat_tabel_nasional(gold)
    df_rekon = _muat_tabel_rekonsiliasi(gold)

    hasil_aturan: dict[str, bool] = {}
    ringkasan_detail: dict[str, str] = {}
    detail_gagal: list[str] = []

    # G1: Kunci panel Gold unik
    if df_panel.empty:
        hasil_aturan["G1_kunci_panel_gold_unik"] = False
        ringkasan_detail["G1_kunci_panel_gold_unik"] = "GAGAL (panel_provinsi kosong)"
        detail_gagal.append("G1: Tabel panel provinsi Gold kosong / belum ditemukan.")
    else:
        kol_wil = "provinsi_kode" if "provinsi_kode" in df_panel.columns else "wilayah_kode"
        kol_seri = "indikator" if "indikator" in df_panel.columns else "seri_kode"
        kunci_panel = [kol_wil, "periode", kol_seri]
        dup_panel = int(df_panel.duplicated(subset=kunci_panel).sum())

        dup_nas = 0
        if not df_nasional.empty:
            kunci_nas = [c for c in ("sumber", "indikator", "rincian", "periode") if c in df_nasional.columns]
            dup_nas = int(df_nasional.duplicated(subset=kunci_nas).sum())

        lolos_g1 = (dup_panel == 0) and (dup_nas == 0)
        hasil_aturan["G1_kunci_panel_gold_unik"] = lolos_g1
        ringkasan_detail["G1_kunci_panel_gold_unik"] = (
            f"{'LULUS' if lolos_g1 else 'GAGAL'} "
            f"(panel_provinsi={len(df_panel)} baris, duplikat={dup_panel}; "
            f"nasional={len(df_nasional)} baris, duplikat={dup_nas})"
        )
        if not lolos_g1:
            detail_gagal.append(f"G1: Duplikat kunci Gold (panel={dup_panel}, nasional={dup_nas}).")

    # G2: Satu satuan per indikator
    if df_panel.empty:
        hasil_aturan["G2_satu_satuan_per_indikator_gold"] = False
        ringkasan_detail["G2_satu_satuan_per_indikator_gold"] = "GAGAL (panel kosong)"
    else:
        kol_seri = "indikator" if "indikator" in df_panel.columns else "seri_kode"
        gabung_satuan = df_panel[[kol_seri, "satuan"]].copy()
        if not df_nasional.empty and "indikator" in df_nasional.columns and "satuan" in df_nasional.columns:
            gabung_satuan = pd.concat([gabung_satuan, df_nasional[["indikator", "satuan"]]], ignore_index=True)
        satuan_per_ind = gabung_satuan.groupby(kol_seri)["satuan"].nunique(dropna=False)
        seri_ganda = satuan_per_ind[satuan_per_ind != 1].to_dict()
        lolos_g2 = len(seri_ganda) == 0
        hasil_aturan["G2_satu_satuan_per_indikator_gold"] = lolos_g2
        ringkasan_detail["G2_satu_satuan_per_indikator_gold"] = (
            f"{'LULUS' if lolos_g2 else 'GAGAL'} "
            f"({len(satuan_per_ind)} indikator diperiksa, pelanggaran={len(seri_ganda)})"
        )
        if not lolos_g2:
            detail_gagal.append(f"G2: Indikator memiliki lebih dari satu satuan: {seri_ganda}.")

    # G3: Setiap sel Gold punya pasangan sah di Silver
    if df_panel.empty:
        hasil_aturan["G3_keterlacakan_sel_gold_ke_silver"] = False
        ringkasan_detail["G3_keterlacakan_sel_gold_ke_silver"] = "GAGAL (panel kosong)"
        detail_gagal.append("G3: Tabel panel Gold kosong.")
    else:
        # Periksa keterlacakan via silver_row_id bila tersedia, serta kecocokan kunci wilayah x periode x seri_kode
        yatim_id = 0
        if "silver_row_id" in df_panel.columns:
            id_valid = set(range(len(silver)))
            yatim_id = int((~df_panel["silver_row_id"].isin(id_valid)).sum())

        p_norm = pd.DataFrame(
            {
                "wilayah_kode": df_panel["provinsi_kode" if "provinsi_kode" in df_panel.columns else "wilayah_kode"].astype(str).str.strip(),
                "periode": df_panel["periode"].astype(str).str.strip(),
                "seri_kode": df_panel["indikator" if "indikator" in df_panel.columns else "seri_kode"].astype(str).str.strip(),
            }
        )
        s_norm = pd.DataFrame(
            {
                "wilayah_kode": silver["wilayah_kode"].astype(str).str.strip(),
                "periode": silver["periode"].astype(str).str.strip(),
                "seri_kode": silver["seri_kode"].astype(str).str.strip(),
            }
        ).drop_duplicates()

        gabung = p_norm.merge(s_norm, on=["wilayah_kode", "periode", "seri_kode"], how="left", indicator=True)
        yatim_kunci = int((gabung["_merge"] != "both").sum())
        lolos_g3 = (yatim_id == 0) and (yatim_kunci == 0)
        hasil_aturan["G3_keterlacakan_sel_gold_ke_silver"] = lolos_g3
        ringkasan_detail["G3_keterlacakan_sel_gold_ke_silver"] = (
            f"{'LULUS' if lolos_g3 else 'GAGAL'} "
            f"({len(df_panel)}/{len(df_panel) - yatim_kunci} sel terlacak ke Silver, yatim={yatim_kunci})"
        )
        if not lolos_g3:
            detail_gagal.append(f"G3: Terdapat sel Gold tanpa pasangan di Silver (yatim_kunci={yatim_kunci}, yatim_id={yatim_id}).")

    # G4: Setiap baris rekonsiliasi berpasangan punya kategori_penjelasan terisi
    if df_rekon.empty:
        hasil_aturan["G4_kategori_rekonsiliasi_berpasangan"] = False
        ringkasan_detail["G4_kategori_rekonsiliasi_berpasangan"] = "GAGAL (rekonsiliasi_nasional belum tersedia)"
        detail_gagal.append("G4: Tabel rekonsiliasi_nasional tidak ditemukan / kosong.")
    else:
        kolom_kat = next((c for c in df_rekon.columns if "kategori" in c.lower()), None)
        if kolom_kat is None:
            hasil_aturan["G4_kategori_rekonsiliasi_berpasangan"] = False
            ringkasan_detail["G4_kategori_rekonsiliasi_berpasangan"] = "GAGAL (kolom kategori tidak ada)"
            detail_gagal.append("G4: Kolom kategori penjelasan tidak ditemukan pada tabel rekonsiliasi.")
        else:
            if "status_pasangan" in df_rekon.columns:
                berpasangan = df_rekon[df_rekon["status_pasangan"].astype(str).str.strip().str.lower() == "berpasangan"]
            else:
                berpasangan = df_rekon.dropna(subset=["nilai_seri_utama", "nilai_pembanding"])
            kosong_kat = int(
                berpasangan[kolom_kat].isna().sum()
                + (berpasangan[kolom_kat].astype(str).str.strip() == "").sum()
            )
            lolos_g4 = (len(berpasangan) > 0) and (kosong_kat == 0)
            hasil_aturan["G4_kategori_rekonsiliasi_berpasangan"] = lolos_g4
            ringkasan_detail["G4_kategori_rekonsiliasi_berpasangan"] = (
                f"{'LULUS' if lolos_g4 else 'GAGAL'} "
                f"({len(berpasangan)} baris berpasangan dari {len(df_rekon)} total baris rekonsiliasi, "
                f"kategori_kosong={kosong_kat})"
            )
            if not lolos_g4:
                detail_gagal.append(f"G4: {kosong_kat} dari {len(berpasangan)} baris rekonsiliasi berpasangan tidak memiliki kategori.")

    for nama_aturan in DAFTAR_ATURAN_GOLD:
        print(f"  - {nama_aturan}: {ringkasan_detail.get(nama_aturan, 'TIDAK DIJALANKAN')}")

    if detail_gagal:
        raise ValueError("Validasi Gold & rekonsiliasi gagal:\n- " + "\n- ".join(detail_gagal))

    return {
        "aturan_gold_validasi": len(DAFTAR_ATURAN_GOLD),
        "aturan_gold_lolos": sum(1 for v in hasil_aturan.values() if v),
        "jumlah_baris_gold": len(df_panel),
        "jumlah_baris_nasional": len(df_nasional),
        "jumlah_baris_rekonsiliasi": len(df_rekon),
        "status_rekonsiliasi": "tervalidasi",
        "rincian_aturan_gold": hasil_aturan,
        "detail_log_gold": ringkasan_detail,
    }