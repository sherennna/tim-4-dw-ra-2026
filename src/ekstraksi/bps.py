"""Tahap 1 (ekstraksi): pembaca berkas BPS, CSV datar dan JSON WebAPI.

Aturan: pembaca hanya mengubah berkas mentah menjadi tabel panjang dan menempelkan
lineage (_berkas_raw, _sha256_raw). Tidak ada baris yang dibuang, dibetulkan, atau
ditafsirkan di sini; semua itu urusan tahap 2-4 dan dicatat di log-keputusan.csv.

Uji cepat:  python -m src.ekstraksi.bps
"""
import json
from pathlib import Path

import pandas as pd

from src.common.manifest import sha256_raw

RAW = Path("data/raw")
SNAPSHOT = "bps/2026-10-20"

# (kode seri, nama berkas tanpa ekstensi). Jalur berkas relatif terhadap data/raw/.
SERI = [
    ("var1393", "sdg3_3_3_3_v1393"),      # kejadian malaria per 1.000 orang
    ("var1480", "sdg3_3_4_1_b_v1480"),    # prevalensi tekanan darah tinggi
    ("var1435", "sdg3_3_a_1_v1435"),      # prevalensi merokok
]

KOLOM = [
    "sumber", "seri_kode", "var_id", "wilayah_id", "wilayah", "turvar_id", "turvar",
    "tahun_id", "tahun", "periode_id", "periode", "nilai_teks", "nilai", "satuan",
    "format", "halaman", "baris_asal", "_berkas_raw", "_sha256_raw",
]


def ke_angka(teks):
    """Teks -> float. Menangani '1,5' (koma desimal) dan '1.234,5' (titik ribuan).
    Teks kosong atau tidak dapat dibaca menjadi NaN; teks aslinya tetap ada di nilai_teks."""
    t = str(teks).strip()
    if t == "":
        return float("nan")
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return float("nan")


def _lengkapi(df, seri_kode, berkas, fmt):
    """Tempelkan kolom asal dan lineage. Tidak mengubah nilai apa pun."""
    df = df.copy()
    df["sumber"] = "bps"
    df["seri_kode"] = seri_kode
    df["nilai"] = df["nilai_teks"].map(ke_angka)
    df["format"] = fmt
    df["_berkas_raw"] = berkas
    df["_sha256_raw"] = sha256_raw(berkas)   # jangan ditulis tangan
    return df[KOLOM]


# ---------------------------------------------------------------- CSV datar
def baca_csv(seri_kode, nama):
    berkas = f"{SNAPSHOT}/{nama}.csv"
    # dtype=str dan keep_default_na=False: tidak ada nilai yang diubah atau hilang diam-diam.
    # utf-8-sig: aman bila berkas diawali BOM.
    df = pd.read_csv(RAW / berkas, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df = df.rename(columns={"nilai": "nilai_teks"})
    df["halaman"] = 0
    df["baris_asal"] = range(2, len(df) + 2)      # nomor baris di berkas (baris 1 = header)
    return _lengkapi(df, seri_kode, berkas, "csv")


# ---------------------------------------------------------------- JSON WebAPI
def _cari_respons(obj):
    """Kumpulkan semua objek yang memuat 'datacontent' (satu per halaman tahun),
    apa pun pembungkusnya: satu dict, daftar dict, atau dict berisi daftar."""
    if isinstance(obj, dict):
        if "datacontent" in obj:
            yield obj
        else:
            for v in obj.values():
                yield from _cari_respons(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _cari_respons(v)


def _peta(daftar):
    """[{'val': 1100, 'label': 'ACEH'}, ...] -> {'1100': 'ACEH'} (urutan dipertahankan)."""
    return {str(x["val"]): x.get("label", "") for x in daftar}


def _baris_dari_respons(resp, halaman):
    vervar, turvar = _peta(resp["vervar"]), _peta(resp["turvar"])
    tahun, turtahun = _peta(resp["tahun"]), _peta(resp["turtahun"])
    isi = resp["datacontent"]
    baris, dipakai = [], {}
    # Kunci datacontent = vervar + var + turvar + tahun + turtahun (kode digabung, panjangnya
    # beragam). Jangan dipotong per posisi: bangun semua kombinasi lalu cocokkan ke kuncinya.
    for var in resp["var"]:
        var_id = str(var["val"])
        for v, nama_v in vervar.items():
            for tv, nama_tv in turvar.items():
                for th, nama_th in tahun.items():
                    for tt, nama_tt in turtahun.items():
                        kunci = f"{v}{var_id}{tv}{th}{tt}"
                        if kunci not in isi:
                            continue
                        if kunci in dipakai:
                            raise ValueError(f"kunci ganda/ambigu di datacontent: {kunci}")
                        dipakai[kunci] = True
                        baris.append({
                            "var_id": var_id, "wilayah_id": v, "wilayah": nama_v,
                            "turvar_id": tv, "turvar": nama_tv, "tahun_id": th,
                            "tahun": nama_th, "periode_id": tt, "periode": nama_tt,
                            "nilai_teks": "" if isi[kunci] is None else str(isi[kunci]),
                            "satuan": var.get("unit", "") or "", "halaman": halaman,
                        })
    yatim = set(isi) - set(dipakai)
    if yatim:   # ada sel yang tidak terpetakan -> struktur kunci belum dipahami
        raise ValueError(f"{len(yatim)} kunci datacontent tidak cocok dengan daftar kode, contoh: {sorted(yatim)[:3]}")
    return baris


def baca_json(seri_kode, nama):
    berkas = f"{SNAPSHOT}/json/{nama}.json"
    with open(RAW / berkas, encoding="utf-8-sig") as f:
        obj = json.load(f)
    semua = []
    for i, resp in enumerate(_cari_respons(obj)):
        semua += _baris_dari_respons(resp, i)
    if not semua:
        raise ValueError(f"{berkas}: tidak ada 'datacontent' yang terbaca")
    df = pd.DataFrame(semua)
    df["baris_asal"] = range(1, len(df) + 1)      # urutan sel di JSON
    return _lengkapi(df, seri_kode, berkas, "json")


# ---------------------------------------------------------------- metadata dan uji silang
def baca_catatan_unduhan():
    """manifest_asal.json: judul, satuan katalog, jumlah baris, sha256 JSON asal per tabel.
    Ini metadata, bukan data; dipakai untuk uji silang dan untuk menetapkan satuan nanti."""
    with open(RAW / SNAPSHOT / "manifest_asal.json", encoding="utf-8-sig") as f:
        tabel = json.load(f)["tabel"]
    return {nama: tabel[nama] for _, nama in SERI}


def uji_silang(csv_df, json_df, catatan):
    """Bandingkan jumlah baris CSV, JSON, dan catatan unduhan, lalu nilai sel per sel."""
    kunci = ["wilayah_id", "turvar_id", "tahun_id", "periode_id"]
    laporan = []
    for seri_kode, nama in SERI:
        a = csv_df[csv_df.seri_kode == seri_kode]
        b = json_df[json_df.seri_kode == seri_kode]
        m = a.merge(b, on=kunci, how="outer", suffixes=("_csv", "_json"), indicator=True)
        hanya_csv = int((m["_merge"] == "left_only").sum())
        hanya_json = int((m["_merge"] == "right_only").sum())
        ada = m[m["_merge"] == "both"]
        beda = int(((ada["nilai_csv"] - ada["nilai_json"]).abs() > 1e-9).sum())
        laporan.append({
            "seri": seri_kode, "baris_csv": len(a), "baris_json": len(b),
            "baris_catatan": catatan[nama]["baris"], "hanya_csv": hanya_csv,
            "hanya_json": hanya_json, "nilai_beda": beda,
        })
    return pd.DataFrame(laporan)


def baca_semua():
    """Baca semua berkas data BPS kasus ini (CSV dan JSON), tanpa membersihkan apa pun."""
    bagian = []
    for seri_kode, nama in SERI:
        bagian.append(baca_csv(seri_kode, nama))
        bagian.append(baca_json(seri_kode, nama))
    return pd.concat(bagian, ignore_index=True)


if __name__ == "__main__":
    df = baca_semua()
    print("Baris per berkas (salin ke komentar tugas):")
    print(df.groupby("_berkas_raw").size().to_string())
    print(f"\nTotal: {df['_berkas_raw'].nunique()} berkas, {len(df)} baris")
    cat = baca_catatan_unduhan()
    print("\nUji silang CSV vs JSON vs catatan unduhan:")
    print(uji_silang(df[df.format == 'csv'], df[df.format == 'json'], cat).to_string(index=False))