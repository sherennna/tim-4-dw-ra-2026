# Laporan Modul 08 — Struktur Penyimpanan Data: SQL vs NoSQL

| Komponen | Isi |
|---|---|
| Nama | Talitha Justine |
| NIM | 124450076 |
| Tanggal pengumpulan | 2026-11-18 |
| Seed dan ukuran data | seed 2026, ukuran kecil |
| Versi Python dan pandas | Python 3.13.7, pandas 3.0.5 |

## 1. Ringkasan

Modul ini memuat transaksi ke SQLite berskema 3NF dan ulasan ke koleksi dokumen (mongomock), lalu menguji apakah keduanya tetap sepakat.
Temuan terpenting: constraint menolak 77 baris pesanan dan 27 ulasan sehingga angka SQL berbeda dari pandas sebesar Rp 18.276.600;
dokumen pesanan sepakat dengan SQL pada 9 ukuran di tahap awal tetapi berselisih pada n_pesanan_selesai, omzet_selesai begitu SQL berubah.
Keputusan terpenting: baris pesanan di-embed, sedangkan produk, pelanggan, dan ulasan dirujuk, karena yang dipakai bersama tidak boleh disalin.

## 2. Data yang Dipakai

`transaksi_m04`, `produk_m04`, `pelanggan_m04` (acuan Modul 4), `toko_m07` (bila ada), `duplikat_transaksi_m04.csv`, dan `ulasan.jsonl`
(9000 dokumen: v1 3892, v2 5108). Transaksi: 24,000 baris.

## 3. Temuan dan Bukti

(Tulis temuan Anda sendiri dengan rujukan ke sel notebook; angka di bawah berasal dari kode.)
- Omzet SQL = embed = reference = Rp 8.010.787.975 (Latihan 8.1, `model_dokumen_m08.csv`).
- Migrasi v1 -> v2: 3892 dokumen, jalan kedua mengubah 0 (Latihan 8.2, `migrasi_m08.csv`).
- Konsistensi awal selisih 0 pada semua ukuran; setelah perubahan SQL berselisih pada n_pesanan_selesai, omzet_selesai (`konsistensi_m08.csv`).

## 4. Keputusan

Lihat `log-keputusan.csv` baris K-08-011 sampai K-08-013 (selain K-08-001 sampai K-08-010 dari prosedur terbimbing).
(Tambahkan alternatif yang dipertimbangkan dan alasan penolakannya dengan kata-kata Anda sendiri.)

## 5. Rekonsiliasi Jumlah Baris

| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| transaksi_m04 -> baris_pesanan | 24.000 | 23.923 | -77 | 77 baris ditolak constraint (FK produk. NOT NULL jumlah) |
| koleksi ulasan -> tabel ulasan | 9.000 | 8.973 | -27 | 27 ulasan berkode produk yatim |
| tabel pesanan -> dokumen pesanan | 15.744 | 15.744 | +0 | satu dokumen per pesanan |
| baris_pesanan -> baris di dokumen | 23.923 | 23.923 | +0 | array baris di dalam dokumen |
| ulasan -> ulasan di dokumen | 8.973 | 8.973 | +0 | ulasan dirujuk ke pesanan kanonik |

## 6. Jawaban Pertanyaan Analisis

(Tulis jawaban Anda sendiri di sini.)

## 7. Keterbatasan

(Contoh: mongomock bukan MongoDB sungguhan, waktu kueri bergantung mesin, data berukuran kecil, ulasan kembar dipertahankan karena tidak ada bukti mana yang asli.)

## 8. Pengungkapan Penggunaan Alat Bantu

Kerangka kode Latihan 8.1, Latihan 8.2, dan Tugas Individu disusun dengan bantuan asisten AI (Claude), kemudian dijalankan,
diperiksa angkanya, dan dipahami oleh penulis. (Sesuaikan kalimat ini dengan kenyataan penggunaan Anda.)
