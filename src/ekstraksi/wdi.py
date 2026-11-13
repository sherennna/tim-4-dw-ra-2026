from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.common.manifest import RAW, sha256_raw

SERI = ("SH.MLR.INCD.P3",)
SNAPSHOT = "2026-10-20"

KOLOM = [
    "sumber",
    "seri_kode",
    "var_id",
    "wilayah_id",
    "wilayah",
    "turvar_id",
    "turvar",
    "tahun_id",
    "tahun",
    "periode_id",
    "periode",
    "nilai_teks",
    "nilai",
    "satuan",
    "format",
    "halaman",
    "baris_asal",
    "jenis_berkas",
    "nama_indikator",
    "sumber_id",
    "sumber_nama",
    "catatan_sumber",
    "organisasi_sumber",
    "topik",
    "_berkas_raw",
    "_sha256_raw",
]


def _daftar_berkas_wdi() -> list[str]:
    manifest_path = RAW / "MANIFEST.csv"
    df_manifest = pd.read_csv(manifest_path, dtype=str)
    kolom_berkas = df_manifest.columns[0]
    berkas = [
        b.strip()
        for b in df_manifest[kolom_berkas].dropna().tolist()
        if b.strip().startswith(f"wdi/{SNAPSHOT}/")
    ]
    return sorted(berkas)


def _muat_katalog_sumber(berkas_sumber: str | None) -> dict[str, str]:
    if not berkas_sumber:
        return {}
    path = RAW / berkas_sumber
    if not path.exists():
        return {}
    muatan = json.loads(path.read_text(encoding="utf-8-sig"))
    daftar = muatan[1] if isinstance(muatan, list) and len(muatan) > 1 else []
    katalog: dict[str, str] = {}
    for item in daftar:
        if isinstance(item, dict) and item.get("id") is not None:
            katalog[str(item["id"])] = str(item.get("name", ""))
    return katalog


def baca_satu_berkas(
    rel_path: str,
    seri_target: tuple[str, ...] = SERI,
    katalog_sumber: dict[str, str] | None = None,
) -> pd.DataFrame:
    path = RAW / rel_path
    digest = sha256_raw(rel_path)
    muatan = json.loads(path.read_text(encoding="utf-8-sig"))

    meta_hal = muatan[0] if isinstance(muatan, list) and len(muatan) > 0 and isinstance(muatan[0], dict) else {}
    halaman = str(meta_hal.get("page", 1))
    daftar = muatan[1] if isinstance(muatan, list) and len(muatan) > 1 and isinstance(muatan[1], list) else []

    katalog_sumber = katalog_sumber or {}
    baris_keluar: list[dict[str, object]] = []

    for idx, item in enumerate(daftar, start=1):
        if not isinstance(item, dict):
            continue

        # 1. JSON data observasi WDI: punya objek 'indicator': {'id': ...}
        if isinstance(item.get("indicator"), dict):
            ind = item["indicator"]
            ind_id = str(ind.get("id", ""))
            if seri_target and ind_id not in seri_target:
                continue

            negara = item.get("country") if isinstance(item.get("country"), dict) else {}
            wilayah_nama = str(negara.get("value", ""))
            wilayah_kode = str(item.get("countryiso3code") or negara.get("id") or "")
            tahun_str = str(item.get("date", ""))
            val = item.get("value")
            nilai_teks = "" if val is None else str(val)
            nilai_num = float(val) if isinstance(val, (int, float)) else pd.NA

            baris_keluar.append(
                {
                    "sumber": "wdi",
                    "seri_kode": ind_id,
                    "var_id": ind_id,
                    "wilayah_id": wilayah_kode,
                    "wilayah": wilayah_nama,
                    "turvar_id": "",
                    "turvar": "",
                    "tahun_id": tahun_str,
                    "tahun": tahun_str,
                    "periode_id": tahun_str,
                    "periode": tahun_str,
                    "nilai_teks": nilai_teks,
                    "nilai": nilai_num,
                    "satuan": str(item.get("unit") or ""),
                    "format": "json",
                    "halaman": halaman,
                    "baris_asal": idx,
                    "jenis_berkas": "data",
                    "nama_indikator": str(ind.get("value", "")),
                    "sumber_id": "",
                    "sumber_nama": "",
                    "catatan_sumber": "",
                    "organisasi_sumber": "",
                    "topik": "",
                    "_berkas_raw": rel_path,
                    "_sha256_raw": digest,
                }
            )

        # 2. JSON metadata indikator WDI (*_indikator.json): punya kunci 'id' dan 'sourceNote'
        elif "sourceNote" in item or "sourceOrganization" in item:
            ind_id = str(item.get("id", ""))
            if seri_target and ind_id not in seri_target:
                continue

            src_obj = item.get("source") if isinstance(item.get("source"), dict) else {}
            src_id = str(src_obj.get("id", ""))
            src_nama = str(src_obj.get("value") or katalog_sumber.get(src_id, ""))
            topik_list = item.get("topics") if isinstance(item.get("topics"), list) else []
            topik_teks = "; ".join(
                str(t.get("value", "")).strip()
                for t in topik_list
                if isinstance(t, dict) and t.get("value")
            )

            baris_keluar.append(
                {
                    "sumber": "wdi",
                    "seri_kode": ind_id,
                    "var_id": ind_id,
                    "wilayah_id": "",
                    "wilayah": "",
                    "turvar_id": "",
                    "turvar": "",
                    "tahun_id": "",
                    "tahun": "",
                    "periode_id": "",
                    "periode": "",
                    "nilai_teks": "",
                    "nilai": pd.NA,
                    "satuan": str(item.get("unit") or ""),
                    "format": "json",
                    "halaman": halaman,
                    "baris_asal": idx,
                    "jenis_berkas": "metadata_indikator",
                    "nama_indikator": str(item.get("name", "")),
                    "sumber_id": src_id,
                    "sumber_nama": src_nama,
                    "catatan_sumber": str(item.get("sourceNote") or ""),
                    "organisasi_sumber": str(item.get("sourceOrganization") or ""),
                    "topik": topik_teks,
                    "_berkas_raw": rel_path,
                    "_sha256_raw": digest,
                }
            )

    return pd.DataFrame(baris_keluar, columns=KOLOM)


def baca_semua(seri_target: tuple[str, ...] = SERI) -> tuple[pd.DataFrame, pd.DataFrame]:
    daftar = _daftar_berkas_wdi()
    berkas_sumber = next((b for b in daftar if b.endswith("/sumber.json")), None)
    katalog_sumber = _muat_katalog_sumber(berkas_sumber)

    kumpulan_df: list[pd.DataFrame] = []
    ringkasan: list[dict[str, object]] = []

    for rel_path in daftar:
        df_berkas = baca_satu_berkas(rel_path, seri_target=seri_target, katalog_sumber=katalog_sumber)
        kumpulan_df.append(df_berkas)
        ringkasan.append(
            {
                "berkas": rel_path,
                "jumlah_baris": len(df_berkas),
                "sha256_raw": sha256_raw(rel_path)[:16] + "...",
            }
        )

    df_gabung = pd.concat(kumpulan_df, ignore_index=True) if kumpulan_df else pd.DataFrame(columns=KOLOM)
    df_ringkasan = pd.DataFrame(ringkasan)
    return df_gabung, df_ringkasan


if __name__ == "__main__":
    df, laporan = baca_semua()
    print("=== Ringkasan Pembacaan WDI (4 JSON) ===")
    print(laporan.to_string(index=False))
    print(f"\nTotal baris hasil saringan {SERI}: {len(df)}")
    print("Kolom lineage ada & tidak kosong:", df[["_berkas_raw", "_sha256_raw"]].notna().all().to_dict())
    print("\nContoh 5 baris pertama:")
    print(df[["jenis_berkas", "seri_kode", "wilayah", "tahun", "nilai_teks", "_berkas_raw"]].head(5).to_string(index=False))