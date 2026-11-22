# Laporan Modul 07 — Latihan 7.1: Endpoint Flask Ringkasan per Provinsi

| Komponen | Isi |
|---|---|
| Nama | Talitha Justine |
| NIM | 124450076 |
| Tanggal pengumpulan | 11 November 2026 |
| Seed dan ukuran data | seed 2026, ukuran kecil |
| Versi Python dan pandas | ‹Python x.y.z› / ‹pandas x.y.z› (cetak dengan `sys.version` dan `pd.__version__`) |

## 1. Ringkasan

Latihan ini membangun endpoint Flask `GET /api/v1/ringkasan-provinsi` yang meringkas katalog per provinsi **toko** (`n_produk`, `n_toko`, `median_harga_katalog_rp`, `rata_rating_toko`), dengan parameter opsional `?provinsi=`. Temuan terpenting: kolom `provinsi_toko` pada katalog berbeda-beda di antara produk satu toko (166 dari 177 toko memiliki lebih dari satu provinsi), sehingga provinsi diambil dari tabel `toko`, bukan dari katalog. Endpoint lulus uji untuk status 200, 401, 403, dan 404, serta uji rekonsiliasi bahwa jumlah `n_produk` dan `n_toko` seluruh provinsi sama dengan isi katalog.

## 2. Data yang Dipakai

- `data/acuan/produk_m04.parquet`: katalog acuan Modul 4, ‹N_baris_katalog› baris × ‹N_kolom_katalog› kolom (`katalog.shape` pada sel C.1), mencakup 177 toko.
- `keluaran/toko_m07.parquet`: keluaran Bagian D (tabel `toko` hasil integrasi API, web, dan katalog), 179 toko dan 16 kolom (sel D.4). Kolom yang dipakai: `id_toko`, `provinsi`, `rating_toko`.

## 3. Temuan dan Bukti

**Temuan 1 — provinsi katalog bukan atribut toko (sel C.3).** Sebanyak 166 dari 177 toko katalog memiliki lebih dari satu provinsi di antara produknya (sebaran 1–9 provinsi). Jika `groupby("provinsi_toko")` dipakai langsung, satu toko dihitung di beberapa provinsi: jumlah `n_toko` menjadi ‹nilai dari `katalog.groupby("provinsi_toko").id_toko.nunique().sum()`› padahal tokonya 177. Provinsi API sama dengan modus katalog pada 174 dari 174 toko dan sama dengan web pada 169 dari 169 halaman berlokasi, sehingga tabel `toko` adalah sumber provinsi yang konsisten.

**Temuan 2 — hasil endpoint (sel `l1`, `keluaran/ringkasan_provinsi_m07.json`).**

| provinsi | n_produk | n_toko | median_harga_katalog_rp | rata_rating_toko |
|---|---:|---:|---:|---:|
| Aceh | 97 | 19 | 62000.0 | 4.09 |
| Bengkulu | 87 | 19 | 595000.0 | 4.06 |
| Jambi | 116 | 18 | 66250.0 | 4.09 |
| Kepulauan Bangka Belitung | 112 | 25 | 70000.0 | 4.25 |
| Kepulauan Riau | 80 | 14 | 66000.0 | 4.10 |
| Lampung | 64 | 12 | 69000.0 | 4.09 |
| Riau | 68 | 17 | 58250.0 | 4.01 |
| Sumatera Barat | 90 | 21 | 58750.0 | 4.14 |
| Sumatera Selatan | 80 | 17 | 57000.0 | 4.17 |
| Sumatera Utara | 56 | 15 | 68500.0 | 4.19 |

**Temuan 3 — uji status dan rekonsiliasi (sel `l1`).**

| Uji | Diharapkan | Didapat |
|---|---:|---:|
| GET dengan kunci benar | 200 | 200 |
| GET tanpa `X-API-Key` | 401 | 401 |
| 401GET dengan kunci salah | 403 | 403 |
| GET `?provinsi=Atlantis` | 404 | 404 |
| GET `?provinsi=<provinsi dikenal>` (huruf besar) | 200 | 200 |

Σ `n_produk` = ‹nilai› = jumlah baris katalog (‹N_baris_katalog›); Σ `n_toko` = ‹nilai› = 177 toko berbeda di katalog. Kedua `assert` rekonsiliasi lulus.

## 4. Keputusan

**Keputusan 1 — provinsi toko diambil dari tabel `toko`.** Terkait K-07-008 pada `log-keputusan.csv`. Alternatif: (a) `groupby("provinsi_toko")` pada katalog, tidak dipilih karena menghitung satu toko di beberapa provinsi sehingga Σ `n_toko` melebihi jumlah toko; (b) modus provinsi katalog, tidak dipilih karena mengabaikan API yang menjadi sumber utama (sumber kebenaran C.5) dan hanya menjadi cadangan terakhir. Tabel `toko` sudah menerapkan urutan API, web, lalu modus katalog dengan satu provinsi per toko.

**Keputusan 2 — rating dirata-ratakan per toko, bukan per produk.** Alternatif: rata-rata `rating_toko` pada baris produk, tidak dipilih karena toko berproduk banyak berbobot lebih dan kolom itu memuat penanda 0,0 serta bervariasi di dalam satu toko (simpangan baku median 0,49; sel C.3). Toko tanpa rating dilewati dan hasil `null` bila semua kosong.

**Keputusan 3 — kode status.** 401 untuk kunci hilang dan 403 untuk kunci salah, mengikuti `server_lapak.py`. Provinsi tidak dikenal dijawab 404 (bukan 200 dengan data kosong) disertai daftar pilihan; pencocokan tidak peka huruf besar-kecil.

## 5. Rekonsiliasi Jumlah Baris

| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| Baca katalog `produk_m04.parquet` | ‹N_baris_katalog› | ‹N_baris_katalog› | 0 | Dibaca apa adanya |
| Petakan provinsi dari tabel `toko` (`id_toko`) | ‹N_baris_katalog› | ‹N_baris_katalog› | 0 | `assert`: tidak ada toko katalog tanpa provinsi |
| Σ `n_produk` seluruh provinsi | ‹N_baris_katalog› | ‹Σ n_produk› | 0 | Ringkasan menutup katalog tanpa tumpang tindih (`assert` lulus) |
| Σ `n_toko` seluruh provinsi | 177 | ‹Σ n_toko› | 0 | Setiap toko tepat satu provinsi (`assert` lulus) |

## 6. Jawaban Pertanyaan Analisis

**Dari mana provinsi toko diambil, dan bagaimana memeriksanya?** Dari tabel `toko` (API sebagai sumber utama, cadangan web yang dinormalkan, lalu modus katalog), karena `provinsi_toko` katalog berbeda-beda di antara produk satu toko. Pemeriksaan: Σ `n_toko` seluruh provinsi harus sama dengan jumlah toko berbeda pada katalog (177). Jika provinsi katalog dipakai langsung, jumlah itu melebihi 177, yang membuktikan toko terhitung ganda.

## 7. Keterbatasan

- Endpoint diuji dengan `app.test_client()` pada data edisi 1; perilaku di bawah beban atau pembatasan laju tidak diuji.
- Provinsi yang tidak memiliki produk pada katalog menghasilkan 404, bukan baris berisi nol.
- `rata_rating_toko` berasal dari tabel `toko` (API); toko tanpa rating dilewati sehingga rata-rata dihitung dari toko yang berating saja.
- Median dapat berupa bilangan pecahan (.5) dan disajikan apa adanya.

## 8. Pengungkapan Penggunaan Alat Bantu

Asisten AI Claude (Anthropic) dipakai untuk menyusun bahasa rinci dan runtut dalam laporan. Seluruh kode dijalankan ulang pada notebook saya dan angka pada laporan diambil dari keluaran sel tersebut. Sumber kode lain: fungsi Bagian A–D dari modul praktikum.
