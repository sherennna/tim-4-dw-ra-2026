#!/usr/bin/env python3
"""Server tiruan Lapak Sumatera untuk Modul 07 -- Ekstraksi Data: API, Web Scraping, ETL.

Satu berkas, hanya Flask dan pustaka standar Python. Seluruh isi server
diturunkan secara deterministik dari ``data/raw/produk.csv`` dan seed 2026,
sehingga setiap mahasiswa melihat data yang sama.

Server menyediakan dua sumber data baru tentang toko penjual Lapak Sumatera:

* **API JSON** ``/api/v1/toko`` dan ``/api/v2/toko`` (butuh header
  ``X-API-Key``), dengan pagination, pembatasan laju, dan perubahan skema
  antarversi;
* **situs web** ``/situs/`` berisi halaman profil toko dan etalase produknya,
  beserta ``robots.txt``.

Dokumentasi endpoint tersedia di ``GET /`` setelah server berjalan.

Pemakaian di notebook (server berjalan di thread latar, port acak)::

    srv = server_lapak.mulai_server(RAW / "produk.csv")
    srv.base_url          # misalnya 'http://127.0.0.1:54321'
    ...
    srv.stop()

Pemakaian di terminal::

    python server_lapak.py --port 8007
    python server_lapak.py --port 8007 --produk data/raw/produk.csv --edisi 2

``--edisi 2`` menyajikan keadaan data satu minggu kemudian (dipakai pada Tugas).

Perlakukan server ini sebagai sistem milik pihak lain. Pelajari perilakunya
dari respons, kode status, header, dan dokumentasi di ``GET /``, seperti yang
Anda lakukan terhadap API sungguhan. Server tidak menulis berkas apa pun.
"""
from __future__ import annotations

import argparse
import atexit
import collections
import csv
import html
import logging
import random
import re
import threading
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from flask import Flask, Response, jsonify, request

__all__ = ["SEED", "KUNCI_PRAKTIKUM", "bangun_dunia", "buat_app", "mulai_server", "ServerLapak"]

SEED = 2026
KUNCI_PRAKTIKUM = "praktikum-dw"
BATAS_PER_DETIK = 5            # permintaan per detik per klien, per area (api/situs)
PER_PAGE_BAWAAN = 20
PER_PAGE_MAKS = 50
PER_HALAMAN_DIREKTORI = 50
EDISI = {1: "2026-07-01T00:00:00Z", 2: "2026-07-08T00:00:00Z"}
JUMLAH_TOKO = 179

KOTA = {
    "Aceh": "Banda Aceh", "Sumatera Utara": "Medan", "Sumatera Barat": "Padang",
    "Riau": "Pekanbaru", "Jambi": "Jambi", "Sumatera Selatan": "Palembang",
    "Bengkulu": "Bengkulu", "Lampung": "Bandar Lampung",
    "Kepulauan Bangka Belitung": "Pangkalpinang", "Kepulauan Riau": "Batam",
}
SEBUTAN_LAMA = {
    "Aceh": "NAD", "Sumatera Utara": "Sumut", "Sumatera Barat": "Sumbar",
    "Sumatera Selatan": "Sumsel", "Kepulauan Bangka Belitung": "Babel",
    "Kepulauan Riau": "Kepri",
}
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
NAMA_DEPAN = ["Siti", "Ahmad", "Budi", "Dewi", "Rina", "Andi", "Putri", "Rizky",
              "Fajar", "Nurul", "Agus", "Wulan", "Hendra", "Indah", "Yusuf",
              "Rahmat", "Sari", "Dian", "Ilham", "Lestari", "Taufik", "Maya"]
NAMA_BELAKANG = ["Siregar", "Nasution", "Lubis", "Harahap", "Saputra", "Pratama",
                 "Wijaya", "Hasibuan", "Sinaga", "Rahmawati", "Putra", "Susanti",
                 "Hidayat", "Kurniawan", "Tanjung", "Ginting", "Sembiring"]
KATEGORI_BARU = ["Kopi", "Rempah", "Makanan Ringan", "Kerajinan"]


# ---------------------------------------------------------------------------
# Pembangkitan dunia data (deterministik)
# ---------------------------------------------------------------------------
def cari_produk_csv(mulai: Path | None = None) -> Path:
    """Cari data/raw/produk.csv dari direktori kerja dan dari lokasi berkas ini ke atas."""
    titik = [Path.cwd(), Path(__file__).resolve().parent] if mulai is None else [Path(mulai)]
    for awal in titik:
        for p in [awal, *awal.parents]:
            f = p / "data" / "raw" / "produk.csv"
            if f.is_file():
                return f
    raise FileNotFoundError(
        "data/raw/produk.csv tidak ditemukan. Siapkan dataset lebih dulu, atau "
        "berikan path-nya: mulai_server('data/raw/produk.csv').")


def _angka_rupiah(teks: str) -> int | None:
    """Teks rupiah berformat Indonesia menjadi bilangan bulat (dipakai server sendiri)."""
    t = teks.replace("Rp", "").replace(" ", "")
    t = re.sub(r",00$", "", t)
    t = t.replace(".", "")
    return int(t) if t.isdigit() else None


def _waktu_z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _acak_waktu(rng: random.Random, awal: str, akhir: str) -> str:
    a = datetime.strptime(awal, "%Y-%m-%dT%H:%M:%SZ")
    b = datetime.strptime(akhir, "%Y-%m-%dT%H:%M:%SZ")
    return _waktu_z(a + timedelta(seconds=rng.randrange(1, int((b - a).total_seconds()))))


def _bulat500(x: float) -> int:
    return max(500, int(round(x / 500)) * 500)


def bangun_dunia(produk_csv: Path | str | None = None, edisi: int = 1) -> dict:
    """Bangun seluruh isi server untuk satu edisi data.

    Urutan pengambilan bilangan acak tetap sama untuk kedua edisi, sehingga
    edisi 2 adalah edisi 1 ditambah perubahan selama satu minggu.
    """
    if edisi not in EDISI:
        raise ValueError(f"edisi harus salah satu dari {sorted(EDISI)}")
    path = Path(produk_csv) if produk_csv else cari_produk_csv()
    with open(path, encoding="utf-8", newline="") as f:
        katalog = list(csv.DictReader(f))
    rng = random.Random(SEED)

    per_toko: dict[str, list[dict]] = collections.defaultdict(list)
    for baris in katalog:
        per_toko[baris["id_toko"]].append(baris)
    semua_id = [f"T{i:03d}" for i in range(1, JUMLAH_TOKO + 1)]
    di_katalog = sorted(per_toko)

    # --- profil dasar setiap toko ------------------------------------------
    toko: dict[str, dict] = {}
    for tid in semua_id:
        produk = per_toko.get(tid, [])
        if produk:
            hitung = collections.Counter(b["provinsi_toko"] for b in produk)
            tertinggi = max(hitung.values())
            provinsi = next(b["provinsi_toko"] for b in produk
                            if hitung[b["provinsi_toko"]] == tertinggi)
            nama = produk[0]["nama_toko"]
        else:
            provinsi = rng.choice(sorted(KOTA))
            nama = f"Toko {tid[1:]}"
        positif = [float(b["rating_toko"]) for b in produk if float(b["rating_toko"]) > 0]
        bergabung = date(2024, 7, 1) + timedelta(days=rng.randrange(0, 700))
        ulasan = rng.randrange(3, 640)
        diperbarui = _acak_waktu(rng, "2026-01-01T00:00:00Z", "2026-06-30T23:59:59Z")
        toko[tid] = {
            "id_toko": tid, "nama_toko": nama, "provinsi": provinsi, "kota": KOTA[provinsi],
            "rating": round(sum(positif) / len(positif), 1) if positif else None,
            "jumlah_ulasan": ulasan if positif else 0,
            "status": "aktif", "tanggal_bergabung": bergabung.isoformat(),
            "updated_at": diperbarui,
        }

    tanpa_api = sorted(rng.sample(di_katalog, 3))
    id_api = [t for t in semua_id if t not in tanpa_api]
    for tid in rng.sample(id_api, 4):
        toko[tid]["status"] = "libur"

    # --- keanehan API v1 -----------------------------------------------------
    posisi_ganda = rng.randrange(20, len(id_api) - 20)
    rating_teks = sorted(rng.sample([t for t in id_api if toko[t]["rating"] is not None], 3))
    halaman_gangguan = rng.randrange(2, 5)

    # --- situs web -----------------------------------------------------------
    rusak = sorted([rng.choice(tanpa_api),
                    rng.choice([t for t in di_katalog if t not in tanpa_api])])
    id_web = [t for t in di_katalog if t not in rusak]
    calon_lama = [t for t in id_web if t in id_api and toko[t]["rating"] is not None
                  and toko[t]["provinsi"] in SEBUTAN_LAMA]
    markup_lama = rng.choice(calon_lama)
    sisa = [t for t in id_web if t != markup_lama]
    tanpa_lokasi = sorted(rng.sample(sisa, 4))
    rating_basi = sorted(rng.sample([t for t in sisa if t in id_api and toko[t]["rating"] is not None
                                     and t not in tanpa_lokasi], 4))
    geser_rating = {t: rng.choice([0.2, 0.3, 0.4]) for t in rating_basi}

    halaman: dict[str, dict] = {}
    for tid in id_web:
        daftar = []
        for b in per_toko[tid]:
            harga = _angka_rupiah(b["harga_katalog"])
            sembunyi = rng.random() < 0.04
            gaya = rng.randrange(4)
            stok = rng.randrange(0, 51)
            u_promo, u_beda = rng.random(), rng.random()
            f_promo, f_beda = rng.uniform(0.80, 0.95), rng.uniform(1.05, 1.15)
            if sembunyi:
                continue
            tayang, coret = harga, None
            if tid == markup_lama:          # templat lama tidak dapat menampilkan harga coret
                pass
            elif u_promo < 0.06:
                tayang, coret = min(_bulat500(harga * f_promo), harga - 500), harga
            elif u_beda < 0.03:
                tayang = max(_bulat500(harga * f_beda), harga + 500)
            daftar.append({"kode_produk": b["kode_produk"], "nama_produk": b["nama_produk"],
                           "harga_tayang": tayang, "harga_coret": coret, "gaya": gaya,
                           "stok": stok, "di_katalog": True})
        rating_web = toko[tid]["rating"]
        if tid in geser_rating:
            rating_web = round(rating_web - geser_rating[tid], 1)
        halaman[tid] = {"id_toko": tid, "markup": "lama" if tid == markup_lama else "baru",
                        "lokasi": tid not in tanpa_lokasi, "rating": rating_web,
                        "profil": dict(toko[tid]), "produk": daftar}

    for i, tid in enumerate(sorted(rng.sample([t for t in id_web if t != markup_lama], 2)), start=1):
        kat = rng.choice(KATEGORI_BARU)
        halaman[tid]["produk"].append({
            "kode_produk": f"LS-{kat[:3].upper()}-{9000 + i}",
            "nama_produk": f"{kat} Baru {9000 + i}",
            "harga_tayang": _bulat500(rng.uniform(15_000, 150_000)), "harga_coret": None,
            "gaya": rng.randrange(4), "stok": rng.randrange(1, 51), "di_katalog": False})
    terdaftar = [(t, j) for t in id_web if halaman[t]["markup"] == "baru"
                 for j in range(len(halaman[t]["produk"])) if halaman[t]["produk"][j]["di_katalog"]]
    for t, j in rng.sample(terdaftar, 3):
        halaman[t]["produk"][j]["harga_tayang"] = None
        halaman[t]["produk"][j]["harga_coret"] = None

    pemilik = {tid: {"nama": f"{rng.choice(NAMA_DEPAN)} {rng.choice(NAMA_BELAKANG)}",
                     "telepon": "08" + "".join(str(rng.randrange(10)) for _ in range(10)),
                     "nama_toko": toko[tid]["nama_toko"]}
               for tid in di_katalog}

    # --- perubahan satu minggu (edisi 2) -------------------------------------
    stabil = [t for t in id_api if toko[t]["status"] == "aktif"]
    berating = [t for t in stabil if toko[t]["rating"] is not None]
    ubah_rating = rng.sample(berating, 10)
    sisa2 = [t for t in stabil if t not in ubah_rating]
    ganti_nama, *nonaktif, pindah = rng.sample(sisa2, 4)
    profil_baru = rng.choice([t for t in tanpa_api if t not in rusak])
    perubahan = []
    for tid in ubah_rating:
        perubahan.append((tid, {"rating": round(min(5.0, max(1.0, toko[tid]["rating"]
                                + rng.choice([-0.3, -0.2, -0.1, 0.1, 0.2]))), 1),
                                "jumlah_ulasan": toko[tid]["jumlah_ulasan"] + rng.randrange(5, 41)}))
    perubahan.append((ganti_nama, {"nama_toko": f"{toko[ganti_nama]['nama_toko']} Official"}))
    for tid in nonaktif:
        perubahan.append((tid, {"status": "nonaktif"}))
    prov_baru = rng.choice([p for p in sorted(KOTA) if p != toko[pindah]["provinsi"]])
    perubahan.append((pindah, {"provinsi": prov_baru, "kota": KOTA[prov_baru]}))
    baru = []
    for n in range(JUMLAH_TOKO + 1, JUMLAH_TOKO + 4):
        prov = rng.choice(sorted(KOTA))
        baru.append({"id_toko": f"T{n:03d}", "nama_toko": f"Toko {n:03d}", "provinsi": prov,
                     "kota": KOTA[prov], "rating": None, "jumlah_ulasan": 0, "status": "aktif",
                     "tanggal_bergabung": f"2026-07-0{rng.randrange(1, 8)}", "updated_at": None})
    waktu_ubah = {tid: _acak_waktu(rng, EDISI[1], "2026-07-07T23:59:59Z")
                  for tid in [t for t, _ in perubahan] + [profil_baru] + [b["id_toko"] for b in baru]}

    if edisi == 2:
        for tid, isi in perubahan:
            toko[tid].update(isi)
            toko[tid]["updated_at"] = waktu_ubah[tid]
        for b in baru:
            b["updated_at"] = waktu_ubah[b["id_toko"]]
            toko[b["id_toko"]] = b
        toko[profil_baru]["updated_at"] = waktu_ubah[profil_baru]
        id_api = sorted([*id_api, profil_baru, *[b["id_toko"] for b in baru]])

    daftar_v1 = list(id_api)
    daftar_v1.insert(posisi_ganda + 1, daftar_v1[posisi_ganda])
    return {
        "edisi": edisi, "data_per": EDISI[edisi], "toko": toko, "id_api": id_api,
        "daftar_v1": daftar_v1, "rating_teks": rating_teks,
        "halaman_gangguan": halaman_gangguan, "di_katalog": di_katalog,
        "id_web": id_web, "rusak": rusak, "halaman": halaman, "pemilik": pemilik,
    }


# ---------------------------------------------------------------------------
# Representasi
# ---------------------------------------------------------------------------
def rekam_v1(d: dict, tid: str) -> dict:
    t = d["toko"][tid]
    rating = t["rating"]
    if tid in d["rating_teks"] and rating is not None:
        rating = f"{rating:.1f}".replace(".", ",")
    return {"id_toko": t["id_toko"], "nama_toko": t["nama_toko"], "provinsi": t["provinsi"],
            "kota": t["kota"], "rating": rating, "jumlah_ulasan": t["jumlah_ulasan"],
            "status": t["status"], "tanggal_bergabung": t["tanggal_bergabung"]}


def rekam_v2(d: dict, tid: str) -> dict:
    t = d["toko"][tid]
    return {"kode_toko": t["id_toko"], "nama": t["nama_toko"],
            "wilayah": {"provinsi": t["provinsi"], "kota": t["kota"]},
            "ulasan": {"rating_rata": t["rating"], "jumlah": t["jumlah_ulasan"]},
            "status": t["status"], "bergabung": t["tanggal_bergabung"],
            "updated_at": t["updated_at"]}


def _tanggal_id(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


def _rupiah(n: int, gaya: int) -> str:
    ribuan = f"{n:,}".replace(",", ".")
    if gaya == 0:
        return f"Rp{ribuan}"
    if gaya == 1:
        return f"Rp {ribuan}"
    if gaya == 2:
        return f"Rp{ribuan},-"
    return f"Rp {n // 1000}rb" if n % 1000 == 0 else f"Rp{ribuan}"


def _kerangka(judul: str, isi: str) -> str:
    return ("<!doctype html>\n<html lang=\"id\">\n<head>\n<meta charset=\"utf-8\">\n"
            f"<title>{html.escape(judul)} — Lapak Sumatera</title>\n</head>\n<body>\n{isi}\n</body>\n</html>\n")


def halaman_toko(d: dict, tid: str) -> str:
    h = d["halaman"][tid]
    t = h["profil"]
    e = html.escape
    if h["markup"] == "lama":
        baris = "".join(
            f"<tr><td>{e(p['kode_produk'])}</td><td>{e(p['nama_produk'])}</td>"
            f"<td>{e(_rupiah(p['harga_tayang'], 1)) if p['harga_tayang'] else '-'}</td></tr>\n"
            for p in h["produk"])
        isi = (f"<div id=\"toko\">\n<h2>{e(t['nama_toko'])}</h2>\n"
               f"<div class=\"info\">Provinsi: {e(SEBUTAN_LAMA[t['provinsi']])} | "
               f"Rating: {h['rating']}/5 | Ulasan: {t['jumlah_ulasan']}</div>\n"
               "<table class=\"tbl-produk\">\n<tr><th>Kode</th><th>Nama</th><th>Harga</th></tr>\n"
               f"{baris}</table>\n<p><a href=\"../\">kembali</a></p>\n</div>")
        return _kerangka(t["nama_toko"], isi)

    lokasi = (f"  <p class=\"lokasi\"><span class=\"kota\">{e(t['kota'])}</span>, "
              f"<span class=\"provinsi\">{e(t['provinsi'])}</span></p>\n") if h["lokasi"] else ""
    if h["rating"] is None:
        rating = "  <p class=\"rating kosong\">Belum ada ulasan</p>\n"
    else:
        nilai = f"{h['rating']:.1f}".replace(".", ",")
        rating = (f"  <p class=\"rating\">&#9733; <span class=\"nilai\">{nilai}</span> "
                  f"<span class=\"jumlah\">({t['jumlah_ulasan']} ulasan)</span></p>\n")
    item = []
    for p in h["produk"]:
        if p["harga_tayang"] is None:
            harga = "<span class=\"harga\">Hubungi penjual</span>"
        elif p["harga_coret"]:
            harga = (f"<span class=\"harga\"><s class=\"harga-coret\">{e(_rupiah(p['harga_coret'], p['gaya']))}</s> "
                     f"<b class=\"harga-promo\">{e(_rupiah(p['harga_tayang'], p['gaya']))}</b></span>")
        else:
            harga = f"<span class=\"harga\">{e(_rupiah(p['harga_tayang'], p['gaya']))}</span>"
        stok = f"Stok {p['stok']}" if p["stok"] else "Stok habis"
        item.append(f"   <li class=\"produk\" data-kode=\"{e(p['kode_produk'])}\">"
                    f"<span class=\"nama-produk\">{e(p['nama_produk'])}</span> {harga} "
                    f"<span class=\"stok\">{stok}</span></li>")
    isi = ("<header><nav><a href=\"../\">Direktori toko</a></nav></header>\n<main>\n"
           f"<article class=\"profil-toko\" data-id-toko=\"{e(tid)}\">\n"
           f"  <h1 class=\"nama-toko\">{e(t['nama_toko'])}</h1>\n{lokasi}{rating}"
           f"  <p class=\"bergabung\">Bergabung sejak <time datetime=\"{t['tanggal_bergabung']}\">"
           f"{_tanggal_id(t['tanggal_bergabung'])}</time></p>\n"
           f"  <p class=\"kontak\"><a href=\"../pemilik/{e(tid)}.html\">Hubungi pemilik</a></p>\n"
           "</article>\n<section class=\"etalase\">\n  <h2>Produk</h2>\n  <ul class=\"daftar-produk\">\n"
           + "\n".join(item) + "\n  </ul>\n</section>\n</main>")
    return _kerangka(t["nama_toko"], isi)


def halaman_direktori(d: dict, hal: int) -> str | None:
    n = PER_HALAMAN_DIREKTORI
    semua = d["di_katalog"]
    akhir = max(1, -(-len(semua) // n))
    if not 1 <= hal <= akhir:
        return None
    e = html.escape
    item = "\n".join(
        f"  <li class=\"toko\"><a href=\"toko/{e(t)}.html\">{e(d['pemilik'][t]['nama_toko'])}</a>"
        f" &middot; <a class=\"kontak\" href=\"pemilik/{e(t)}.html\">kontak pemilik</a></li>"
        for t in semua[(hal - 1) * n: hal * n])
    nav = f"<li class=\"next\"><a href=\"?hal={hal + 1}\">Berikutnya</a></li>" if hal < akhir else ""
    isi = (f"<h1>Direktori Toko Lapak Sumatera</h1>\n<p>Halaman {hal} dari {akhir}</p>\n"
           f"<ul class=\"direktori\">\n{item}\n</ul>\n<ul class=\"pager\">{nav}</ul>")
    return _kerangka("Direktori toko", isi)


ROBOTS = """# Situs Lapak Sumatera (tiruan untuk praktikum Data Wrangling)
User-agent: *
Disallow: /situs/pemilik/
Request-rate: 5/1
"""


# ---------------------------------------------------------------------------
# Aplikasi Flask
# ---------------------------------------------------------------------------
class _Pembatas:
    """Jendela geser satu detik per (area, klien). Hanya permintaan yang diterima dihitung."""

    def __init__(self, batas: int):
        self.batas = batas
        self.jejak: dict[tuple, collections.deque] = collections.defaultdict(collections.deque)
        self.kunci = threading.Lock()

    def izinkan(self, kunci: tuple) -> bool:
        kini = time.monotonic()
        with self.kunci:
            q = self.jejak[kunci]
            while q and kini - q[0] >= 1.0:
                q.popleft()
            if len(q) >= self.batas:
                return False
            q.append(kini)
            return True


def buat_app(dunia: dict) -> Flask:
    app = Flask("server_lapak")
    app.json.ensure_ascii = False
    app.json.sort_keys = False
    pembatas = _Pembatas(BATAS_PER_DETIK)
    hitung_gangguan: collections.Counter = collections.Counter()
    kunci_gangguan = threading.Lock()
    catatan: list[dict] = []
    app.config["CATATAN_PERMINTAAN"] = catatan

    def galat(kode: int, pesan: str, **header) -> Response:
        r = jsonify({"error": pesan, "status": kode})
        r.status_code = kode
        for k, v in header.items():
            r.headers[k.replace("_", "-")] = v
        return r

    @app.after_request
    def _catat(resp: Response) -> Response:
        catatan.append({"waktu": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                        "metode": request.method, "path": request.full_path.rstrip("?"),
                        "status": resp.status_code,
                        "user_agent": request.headers.get("User-Agent", "")})
        return resp

    def batasi(area: str) -> Response | None:
        if not pembatas.izinkan((area, request.remote_addr)):
            return galat(429, f"terlalu banyak permintaan: maksimal {BATAS_PER_DETIK} per detik",
                         Retry_After="1")
        return None

    def periksa_kunci() -> Response | None:
        kunci = request.headers.get("X-API-Key")
        if not kunci:
            return galat(401, "header X-API-Key wajib diisi")
        if kunci != KUNCI_PRAKTIKUM:
            return galat(403, "X-API-Key tidak dikenal")
        return None

    def halaman_param() -> tuple[int, int] | Response:
        try:
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", PER_PAGE_BAWAAN))
        except ValueError:
            return galat(400, "page dan per_page harus bilangan bulat")
        if page < 1 or per_page < 1:
            return galat(400, "page dan per_page minimal 1")
        if per_page > PER_PAGE_MAKS:
            return galat(400, f"per_page maksimal {PER_PAGE_MAKS}")
        return page, per_page

    def gangguan(versi: str, page: int) -> Response | None:
        if page != dunia["halaman_gangguan"]:
            return None
        with kunci_gangguan:
            hitung_gangguan[versi] += 1
            ke = hitung_gangguan[versi]
        if ke <= 2:
            return galat(500, "gangguan sementara pada server data; coba lagi")
        return None

    @app.get("/")
    def dokumentasi():
        return jsonify({
            "nama": "Lapak Sumatera Data API (tiruan untuk praktikum)",
            "edisi": dunia["edisi"], "data_per": dunia["data_per"],
            "autentikasi": "header X-API-Key pada setiap permintaan /api/",
            "pembatasan_laju": f"{BATAS_PER_DETIK} permintaan per detik per klien; "
                               "melebihi batas dijawab 429 dengan header Retry-After (detik)",
            "endpoint": [
                {"path": "/api/v1/toko", "parameter": {"page": "mulai 1",
                 "per_page": f"bawaan {PER_PAGE_BAWAAN}, maksimal {PER_PAGE_MAKS}"},
                 "respons": "data, page, per_page, total, next"},
                {"path": "/api/v1/toko/<id_toko>", "respons": "satu toko"},
                {"path": "/api/v2/toko", "parameter": {"page": "mulai 1",
                 "per_page": f"bawaan {PER_PAGE_BAWAAN}, maksimal {PER_PAGE_MAKS}",
                 "updated_since": "opsional, ISO 8601 UTC, misalnya 2026-06-30T00:00:00Z; "
                                  "hanya toko dengan updated_at sesudah waktu itu"},
                 "respons": "items, meta, links"},
                {"path": "/situs/", "keterangan": "situs web toko (HTML), lihat /situs/robots.txt"},
            ],
            "catatan_versi": "v1 dipertahankan untuk klien lama; v2 menamai ulang field dan "
                             "menambah updated_at",
        })

    @app.get("/api/v1/toko")
    def toko_v1():
        for cek in (periksa_kunci, lambda: batasi("api")):
            r = cek()
            if r is not None:
                return r
        hp = halaman_param()
        if isinstance(hp, Response):
            return hp
        page, per_page = hp
        r = gangguan("v1", page)
        if r is not None:
            return r
        daftar = dunia["daftar_v1"]
        potong = daftar[(page - 1) * per_page: page * per_page]
        lanjut = (f"/api/v1/toko?{urlencode({'page': page + 1, 'per_page': per_page})}"
                  if page * per_page < len(daftar) else None)
        return jsonify({"data": [rekam_v1(dunia, t) for t in potong], "page": page,
                        "per_page": per_page, "total": len(daftar), "next": lanjut})

    @app.get("/api/v1/toko/<tid>")
    def satu_toko_v1(tid: str):
        for cek in (periksa_kunci, lambda: batasi("api")):
            r = cek()
            if r is not None:
                return r
        if tid not in dunia["id_api"]:
            return galat(404, f"toko {tid} tidak ditemukan")
        return jsonify({"data": rekam_v1(dunia, tid)})

    @app.get("/api/v2/toko")
    def toko_v2():
        for cek in (periksa_kunci, lambda: batasi("api")):
            r = cek()
            if r is not None:
                return r
        hp = halaman_param()
        if isinstance(hp, Response):
            return hp
        page, per_page = hp
        sejak = request.args.get("updated_since")
        daftar = dunia["id_api"]
        if sejak:
            try:
                datetime.strptime(sejak, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                return galat(400, "updated_since harus berformat YYYY-MM-DDTHH:MM:SSZ (UTC)")
            daftar = [t for t in daftar if dunia["toko"][t]["updated_at"] > sejak]
        r = gangguan("v2", page)
        if r is not None:
            return r
        potong = daftar[(page - 1) * per_page: page * per_page]
        q = {"page": page + 1, "per_page": per_page, **({"updated_since": sejak} if sejak else {})}
        lanjut = f"/api/v2/toko?{urlencode(q)}" if page * per_page < len(daftar) else None
        return jsonify({"items": [rekam_v2(dunia, t) for t in potong],
                        "meta": {"page": page, "per_page": per_page, "total": len(daftar)},
                        "links": {"next": lanjut}})

    def html_resp(teks: str, kode: int = 200) -> Response:
        return Response(teks, status=kode, mimetype="text/html")

    @app.get("/robots.txt")
    @app.get("/situs/robots.txt")
    def robots():
        return Response(ROBOTS, mimetype="text/plain")

    @app.get("/situs/")
    def direktori():
        r = batasi("situs")
        if r is not None:
            return r
        try:
            hal = int(request.args.get("hal", 1))
        except ValueError:
            hal = 0
        teks = halaman_direktori(dunia, hal)
        if teks is None:
            return html_resp(_kerangka("Tidak ditemukan", "<h1>Halaman tidak ditemukan</h1>"), 404)
        return html_resp(teks)

    @app.get("/situs/toko/<nama>")
    def profil(nama: str):
        r = batasi("situs")
        if r is not None:
            return r
        tid = nama.removesuffix(".html")
        if not nama.endswith(".html") or tid not in dunia["halaman"]:
            return html_resp(_kerangka("Tidak ditemukan", "<h1>Halaman tidak ditemukan</h1>"), 404)
        return html_resp(halaman_toko(dunia, tid))

    @app.get("/situs/pemilik/<nama>")
    def kontak(nama: str):
        r = batasi("situs")
        if r is not None:
            return r
        tid = nama.removesuffix(".html")
        if tid not in dunia["pemilik"]:
            return html_resp(_kerangka("Tidak ditemukan", "<h1>Halaman tidak ditemukan</h1>"), 404)
        p = dunia["pemilik"][tid]
        isi = (f"<h1>Kontak pemilik {html.escape(p['nama_toko'])}</h1>\n"
               f"<p class=\"pemilik\">Nama: {html.escape(p['nama'])}</p>\n"
               f"<p class=\"telepon\">WhatsApp: {p['telepon']}</p>")
        return html_resp(_kerangka("Kontak pemilik", isi))

    return app


# ---------------------------------------------------------------------------
# Menjalankan server
# ---------------------------------------------------------------------------
class ServerLapak:
    """Server werkzeug di thread latar. Hentikan dengan ``stop()``."""

    def __init__(self, app: Flask, host: str = "127.0.0.1", port: int = 0):
        from werkzeug.serving import make_server
        self.app = app
        self._srv = make_server(host, port, app, threaded=True)
        self._srv.daemon_threads = True
        self.host, self.port = host, self._srv.server_port
        self.base_url = f"http://{host}:{self.port}"
        self._thread = threading.Thread(target=self._srv.serve_forever, name="server_lapak",
                                        daemon=True)
        self._thread.start()
        self._berjalan = True
        atexit.register(self.stop)

    def permintaan(self) -> list[dict]:
        """Salinan catatan permintaan yang diterima server (untuk pemeriksaan)."""
        return list(self.app.config["CATATAN_PERMINTAAN"])

    def stop(self) -> None:
        if self._berjalan:
            self._berjalan = False
            self._srv.shutdown()
            self._srv.server_close()
            self._thread.join(timeout=5)

    def __repr__(self) -> str:
        status = "berjalan" if self._berjalan else "berhenti"
        return f"<ServerLapak {self.base_url} edisi {self.app.config['EDISI']} {status}>"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stop()


def mulai_server(produk_csv: Path | str | None = None, edisi: int = 1,
                 port: int = 0, host: str = "127.0.0.1") -> ServerLapak:
    """Jalankan server di thread latar dan kembalikan objek dengan ``base_url`` dan ``stop()``.

    ``port=0`` memilih port bebas secara acak.
    """
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app = buat_app(bangun_dunia(produk_csv, edisi))
    app.config["EDISI"] = edisi
    return ServerLapak(app, host, port)


def main() -> None:
    ap = argparse.ArgumentParser(description="Server tiruan Lapak Sumatera (Modul 07)")
    ap.add_argument("--port", type=int, default=8007)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--produk", type=Path, default=None, help="path data/raw/produk.csv")
    ap.add_argument("--edisi", type=int, default=1, choices=sorted(EDISI))
    args = ap.parse_args()
    app = buat_app(bangun_dunia(args.produk, args.edisi))
    app.config["EDISI"] = args.edisi
    print(f"Server Lapak Sumatera edisi {args.edisi} di http://{args.host}:{args.port}/ (Ctrl+C berhenti)")
    from werkzeug.serving import run_simple
    run_simple(args.host, args.port, app, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
