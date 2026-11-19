"""Tahap 1 (ekstraksi): pembaca WHO GHO, CSV 'datadot' dan JSON metadata indikator.

Aturan: pembaca hanya mengubah berkas mentah menjadi tabel panjang dan menempelkan lineage
(_berkas_raw, _sha256_raw). Tidak ada baris yang dibuang, dibetulkan, atau ditafsirkan.
Kolom DIM_* yang kosong artinya "dimensi tidak berlaku"; di sini tetap kosong, tidak diisi.

Uji cepat:  python -m src.ekstraksi.who
"""
import json
import warnings
from pathlib import Path

import pandas as pd

from src.common.manifest import sha256_raw

RAW = Path("data/raw")
SNAPSHOT = "who_gho/2026-10-20"
SERI = ["MALARIA_EST_INCIDENCE", "NCDMORT3070", "M_Est_tob_curr_std"]

# kolom standar (huruf kecil) di depan; semua kolom asli WHO (huruf besar) ikut di belakangnya
STANDAR = [
    "sumber", "seri_kode", "kolom_nilai", "nilai_teks", "nilai", "batas_bawah_teks", "batas_bawah",
    "batas_atas_teks", "batas_atas", "dim_terisi", "format", "baris_asal", "_berkas_raw", "_sha256_raw",
]


def ke_angka(teks):
    """Teks -> float ('1,5' dan '1.234,5' ditangani). Kosong atau tidak terbaca -> NaN;
    teks aslinya tetap tersimpan di kolom *_teks."""
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


def seri_dari_nama(berkas):
    """'.../442CEA8_MALARIA_EST_INCIDENCE.csv' -> 'MALARIA_EST_INCIDENCE' (awalan = sidik unduhan)."""
    stem = Path(berkas).stem
    return stem.split("_", 1)[1] if "_" in stem else stem


def uuid_dari_nama(berkas):
    """'.../442CEA8_MALARIA_EST_INCIDENCE.csv' -> '442CEA8' (sama dengan kolom IND_UUID di CSV dan
    kolom UrlName di metadata DDI; dipakai untuk mencocokkan metadata dengan seri)."""
    return Path(berkas).stem.split("_", 1)[0]


def kolom_nilai(kolom):
    """Cari kelompok kolom nilai: PREFIX_N (nilai), PREFIX_NL (batas bawah), PREFIX_NU (batas atas).
    Nama PREFIX menyebut skalanya (mis. RATE_PER_1000). Kolom DIM_* tidak pernah dianggap nilai."""
    hasil = []
    for k in kolom:
        if k.endswith("_N") and not k.startswith("DIM_"):
            p = k[:-2]
            hasil.append((p, k, p + "_NL" if p + "_NL" in kolom else None,
                          p + "_NU" if p + "_NU" in kolom else None))
    return hasil


# ---------------------------------------------------------------- CSV datadot
def baca_csv(berkas):
    """Satu CSV WHO -> tabel panjang: satu baris per baris asal per kelompok kolom nilai."""
    # dtype=str dan keep_default_na=False: sel kosong tetap '' (bukan NaN), tidak ada nilai berubah.
    # utf-8-sig: CSV WHO sering diawali BOM.
    asli = pd.read_csv(RAW / berkas, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    kelompok = kolom_nilai(list(asli.columns))
    if not kelompok:
        raise ValueError(f"{berkas}: tidak ada kolom nilai berakhiran _N; kolom: {list(asli.columns)[:15]}")
    dim = [k for k in asli.columns if k.startswith("DIM_")]
    kode_cocok = True
    if "IND_CODE" in asli.columns:      # kode di isi berkas harus sama dengan kode di nama berkas
        kode_cocok = set(asli["IND_CODE"]) == {seri_dari_nama(berkas)}
        if not kode_cocok:
            warnings.warn(f"{berkas}: IND_CODE {sorted(set(asli['IND_CODE']))} berbeda dari nama berkas")
    asli["baris_asal"] = range(2, len(asli) + 2)                    # baris 1 = header
    asli["dim_terisi"] = asli[dim].apply(                            # hanya dimensi yang berlaku
        lambda r: "|".join(f"{k}={v}" for k, v in r.items() if str(v).strip() != ""), axis=1) if dim else ""
    bagian = []
    for prefix, kn, kl, ku in kelompok:
        d = asli.copy()
        d["kolom_nilai"] = kn
        d["nilai_teks"] = d[kn]
        d["batas_bawah_teks"] = d[kl] if kl else ""
        d["batas_atas_teks"] = d[ku] if ku else ""
        bagian.append(d)
    df = pd.concat(bagian, ignore_index=True)
    for dasar in ("nilai", "batas_bawah", "batas_atas"):
        df[dasar] = df[dasar + "_teks"].map(ke_angka)
    df["sumber"], df["format"] = "who_gho", "csv"
    df["seri_kode"] = seri_dari_nama(berkas)
    df["_berkas_raw"], df["_sha256_raw"] = berkas, sha256_raw(berkas)   # jangan ditulis tangan
    asli_kolom = [k for k in asli.columns if k not in ("baris_asal", "dim_terisi")]
    return df[STANDAR + asli_kolom], {"baris_berkas": len(asli), "kolom_nilai": [k[1] for k in kelompok],
                                      "jumlah_dim": len(dim), "kode_cocok": kode_cocok}


# ---------------------------------------------------------------- JSON metadata
def _daftar_catatan(obj):
    """Cari daftar catatan (list berisi dict) terpanjang di JSON, apa pun pembungkusnya
    (OData: {'value': [...]}, larik langsung, atau bersarang)."""
    ditemukan = []

    def jelajah(x):
        if isinstance(x, list):
            if x and all(isinstance(i, dict) for i in x):
                ditemukan.append(x)
            for i in x:
                jelajah(i)
        elif isinstance(x, dict):
            for v in x.values():
                jelajah(v)
    jelajah(obj)
    if ditemukan:
        return max(ditemukan, key=len)
    return [obj] if isinstance(obj, dict) else []


def _ratakan(rec):
    """dict bersarang -> kolom 'induk_anak'; daftar -> teks JSON (tidak ada informasi yang hilang)."""
    datar = {}
    for k, v in rec.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                datar[f"{k}_{k2}"] = v2 if not isinstance(v2, (dict, list)) else json.dumps(v2, ensure_ascii=False)
        elif isinstance(v, list):
            datar[k] = json.dumps(v, ensure_ascii=False)
        else:
            datar[k] = v
    return datar


def baca_json(berkas):
    """Satu JSON metadata WHO -> tabel, satu baris per catatan indikator."""
    with open(RAW / berkas, encoding="utf-8-sig") as f:
        obj = json.load(f)
    catatan = _daftar_catatan(obj)
    if not catatan:
        raise ValueError(f"{berkas}: tidak ada daftar catatan yang terbaca")
    df = pd.DataFrame([_ratakan(r) for r in catatan]).astype(object).fillna("").astype(str)
    df.insert(0, "sumber", "who_gho")
    df["format"] = "json"
    df["baris_asal"] = range(1, len(df) + 1)
    df["_berkas_raw"], df["_sha256_raw"] = berkas, sha256_raw(berkas)
    return df, {"baris_berkas": len(df)}


def cocok_seri(df, pasangan):
    """Untuk tiap seri {kode: sidik}: jumlah baris metadata yang memuat kode atau sidiknya persis
    sama dengan satu sel, dan jumlah baris yang teksnya mengandung kode. Hanya menghitung."""
    teks = df.astype(str)
    hasil = {}
    for kode, sidik in pasangan.items():
        persis = teks.eq(kode).any(axis=1) | teks.eq(sidik).any(axis=1)
        ada = teks.apply(lambda kol: kol.str.contains(kode, regex=False)).any(axis=1)
        hasil[kode] = (int(persis.sum()), int((persis | ada).sum()))
    return hasil


# ---------------------------------------------------------------- semuanya
def daftar_berkas():
    """Daftar berkas WHO GHO menurut MANIFEST.csv (bukan menurut isi folder), supaya berkas nyasar
    di data/raw/ (mis. sisa unduhan kasus lain) tidak ikut terbaca. Jalur relatif terhadap data/raw/."""
    m = pd.read_csv(RAW / "MANIFEST.csv", dtype=str)
    kol = "berkas" if "berkas" in m.columns else m.columns[0]
    semua = [b.replace("\\", "/") for b in m[kol]]
    awal = SNAPSHOT + "/"
    csv = sorted(b for b in semua if b.startswith(awal + "datadot/") and b.endswith(".csv"))
    js = sorted(b for b in semua if b.startswith(awal) and b.endswith(".json"))
    return csv, js


def baca_semua(seri=SERI):
    """Baca semua berkas WHO GHO. Mengembalikan dict: data (CSV), metadata (JSON), rekap."""
    berkas_csv, berkas_json = daftar_berkas()
    if not berkas_csv and not berkas_json:
        raise FileNotFoundError(f"MANIFEST.csv tidak memuat berkas {SNAPSHOT}; jalankan unduh_data.py --kasus 4")
    pasangan = {seri_dari_nama(b): uuid_dari_nama(b) for b in berkas_csv}
    data, meta, rekap = [], [], []
    for b in berkas_csv:
        df, info = baca_csv(b)
        data.append(df)
        rekap.append({"berkas": b, "jenis": "csv", "baris_berkas": info["baris_berkas"], "baris_tabel": len(df),
                      "kolom_nilai": ",".join(info["kolom_nilai"]), "kolom_dim": info["jumlah_dim"],
                      "kode_cocok": "ya" if info["kode_cocok"] else "TIDAK", "cocok_seri_persis/terkandung": ""})
    for b in berkas_json:
        df, info = baca_json(b)
        meta.append(df)
        c = cocok_seri(df, pasangan)
        rekap.append({"berkas": b, "jenis": "json", "baris_berkas": info["baris_berkas"], "baris_tabel": len(df),
                      "kolom_nilai": "", "kolom_dim": "", "kode_cocok": "",
                      "cocok_seri_persis/terkandung": "; ".join(f"{k}: {p}/{t}" for k, (p, t) in c.items())})
    return {"data": pd.concat(data, ignore_index=True) if data else pd.DataFrame(columns=STANDAR),
            "metadata": pd.concat(meta, ignore_index=True) if meta else pd.DataFrame(),
            "rekap": pd.DataFrame(rekap)}


if __name__ == "__main__":
    h = baca_semua()
    print("Baris per berkas (salin ke komentar tugas):")
    print(h["rekap"].to_string(index=False))
    d = h["data"]
    print(f"\nTotal CSV: {len(d)} baris; seri terbaca: {sorted(d['seri_kode'].unique())}")
    print("Baris per seri:", d.groupby("seri_kode").size().to_dict())
    print("Nilai kosong per seri:", d[d['nilai'].isna()].groupby('seri_kode').size().to_dict())
    print(f"Total metadata JSON: {len(h['metadata'])} baris")