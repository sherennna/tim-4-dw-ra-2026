# Latihan 8.1 — Pesanan sebagai dokumen: embed atau reference

## Yang dilakukan
Dari `lapak_m08.sqlite` dibangun dua model dokumen pesanan di mongomock.

- **Embed:** satu dokumen per pesanan (15.744 dokumen), dengan baris pesanan di dalam array `baris`.
- **Reference:** dua koleksi, yaitu kepala pesanan (15.744 dokumen) dan baris pesanan (23.923 dokumen) yang merujuk `id_pesanan`.

Ketiga cara (SQL, embed, reference) dipakai untuk menghitung omzet per provinsi tujuan pada pesanan berstatus selesai.

## Hasil pengukuran
| Model | Jumlah dokumen/baris | Ukuran (KiB) | Waktu median (ms) | Omzet total | Sama dengan SQL |
|---|---:|---:|---:|---:|---|
| sql_3nf | 39.667 | 7.128,0 | 33,05 | Rp 8.010.787.975 | Ya |
| embed | 15.744 | 8.812,7 | 11.189,51 | Rp 8.010.787.975 | Ya |
| reference | 39.667 | 9.391,1 | 17.822,68 | Rp 8.010.787.975 | Ya |

Catatan membaca tabel: pada `sql_3nf`, jumlah 39.667 adalah baris tabel `pesanan` (15.744) ditambah `baris_pesanan` (23.923), dan ukurannya
adalah seluruh berkas SQLite, termasuk tabel ulasan dan indeks, sehingga tidak sebanding langsung dengan ukuran JSON kedua model dokumen.

## Pembahasan
**Hasil sama.** Omzet per provinsi dari SQL, pipeline agregasi pada model embed, dan penggabungan pada model reference identik di semua
provinsi, dengan total Rp 8.010.787.975. Jadi ketiga cara menjawab pertanyaan yang sama dengan angka yang sama.

**Ukuran.** Model embed (8.813 KiB) sekitar 6% lebih kecil dari model reference (9.391 KiB). Pada model reference setiap baris pesanan
membawa `id_pesanan` sendiri, sedangkan pada embed id itu cukup ditulis sekali di kepala. Selisihnya kecil karena rata-rata satu pesanan
hanya berisi 1.52 baris (maksimum 3).

**Waktu.** Pada percobaan ini SQL jauh lebih cepat (sekitar 33 ms) daripada embed (sekitar 11,2 detik) dan reference (sekitar 17,8 detik).
Angka ini tidak boleh dibaca sebagai "MongoDB lebih lambat dari SQL". mongomock berjalan murni di Python dan di memori, tanpa indeks
dan tanpa optimasi, sedangkan SQLite adalah mesin yang dioptimalkan. Yang bisa disimpulkan dari data ini hanyalah perbandingan antara
dua model dokumen: model embed lebih cepat daripada reference karena cukup satu pipeline (`$unwind` lalu `$group`), sedangkan
reference harus mengumpulkan status dari kepala pesanan lalu menggabungkannya dengan hasil agregasi baris di sisi aplikasi. Penggabungan
itu sengaja tidak memakai `$lookup`, sebab `$lookup` di mongomock tidak memakai indeks.

## Keputusan per bagian pesanan
| Bagian | Pilihan | Alasan dan angka pendukung |
|---|---|---|
| Baris pesanan | Embed | Selalu dibaca bersama kepala pesanan dan tidak dipakai pesanan lain. Rata-rata 1.52 baris per pesanan, maksimum 3, sehingga array kecil dan terbatas. |
| Produk | Reference (kode saja) | Satu produk muncul di rata-rata 28,1 pesanan. Menyalin atribut produk (harga katalog, kategori, toko) berarti memperbarui sebanyak itu salinan setiap ada perubahan. |
| Pelanggan | Reference (`id_pelanggan`) | Atribut akun bisa berubah dan dipakai lintas pesanan, rata-rata 2,89 pesanan per pelanggan. Ada 268 pesanan tamu yang tidak punya akun. |
| Ulasan | Reference (embed ringkas `id` dan `bintang` bila diperlukan) | Ulasan lahir belakangan dari penulis yang berbeda, bentuknya berubah antara v1 dan v2, dan hanya 8973 ulasan untuk 23.923 baris pesanan. Meng-embed seluruh ulasan akan memaksa dokumen pesanan diubah setiap ada ulasan baru. |

## Catatan
- Model embed memudahkan pembacaan satu pesanan lengkap dan agregasi omzet, tetapi menggandakan data jika bagian yang di-embed dipakai
  bersama. Itu sebabnya hanya baris yang di-embed.
- 39 pesanan tidak memiliki baris karena baris-barisnya ditolak constraint di Bagian A. Pada model embed mereka berarray
  `baris` kosong dan tidak ikut omzet, sehingga omzet kedua model dokumen sama dengan SQL.
- Waktu bergantung pada mesin dan pada mongomock, jadi yang dinilai di sini adalah perbedaan cara kerja kedua model, bukan angka mutlaknya.
