# Latihan 8.2 — Migrasi skema ulasan v1 → v2

## Yang dilakukan
Seluruh 9.000 dokumen ulasan disalin ke koleksi baru `ulasan_migrasi`, sedangkan koleksi `ulasan` dari Bagian C tidak disentuh.
Sebanyak 3.892 dokumen berskema v1 diubah ke bentuk v2: `id_pesanan` menjadi `pesanan.id`, `kode_produk` menjadi `produk.kode`,
`id_pelanggan` menjadi `pelanggan.id`, `rating` menjadi `penilaian.bintang`, dan `foto` (array nama berkas) menjadi `media`
(array objek berisi `jenis` dan `url`, sama seperti bentuk media pada dokumen v2 asli). Field lama dihapus, `versi_skema` diubah menjadi 2,
dan setiap dokumen hasil migrasi ditandai `migrasi.dari_versi = 1`.

Sesudah itu `pesanan.kanal` dan `produk.kategori` dilengkapi dari basis data SQLite. Id pesanan yang berpola 9xxxxx dipetakan lebih dulu
lewat `duplikat_transaksi_m04.csv`, dan produk yang tidak ada di katalog diberi kategori `null`, seperti pada dokumen v2 asli.
Field yang tidak pernah direkam v1 (aspek penilaian, tag, balasan penjual) tidak diisi.

## Catatan cara migrasi
`update_many` dengan pipeline (`$set` dan `$map`) ditolak mongomock dengan `NotImplementedError`. Karena itu langkah pertama
dikerjakan dengan cadangan: dokumen v1 dibaca, diubah bentuknya di Python dengan aturan pemetaan yang sama, lalu diganti di koleksi
`ulasan_migrasi`. Langkah melengkapi kanal dan kategori memakai `update_many` biasa, dikelompokkan per nilai dengan `$in`.
Pada MongoDB sungguhan, pipeline yang sama dapat dijalankan langsung dengan satu `update_many`.

## Hasil
| Langkah | Cocok | Diubah | Diubah jalan kedua |
|---|---:|---:|---:|
| migrasi_v1_ke_v2 | 3.892 | 3.892 | 0 |
| lengkapi_kanal | 3.892 | 3.892 | 0 |
| lengkapi_kategori | 3.892 | 3.892 | 0 |

Setelah kanal dilengkapi, 2.078 dokumen berkanal web dan 1.814 berkanal app. Kategori terbanyak pada dokumen hasil migrasi adalah
Makanan Ringan (763), Kopi (717), dan Rempah (596).

## Validasi
- Tidak ada lagi field v1 (`id_pesanan`, `kode_produk`, `id_pelanggan`, `rating`, `foto`) di tingkat atas dokumen, dan tidak ada dokumen
  berskema 1 yang tersisa.
- Jumlah dokumen tetap 9.000, sama dengan koleksi asli.
- Sebaran bintang per nilai sama dengan koleksi asli (dihitung dengan `$ifNull` agar membaca kedua bentuk).
- Koleksi `ulasan` asli tidak berubah: dokumen v1 di sana tetap 3.892.
- Jalan kedua tidak mengubah dokumen apa pun pada ketiga langkah, jadi migrasinya idempoten. Setiap langkah hanya memproses dokumen yang
  belum diproses (`versi_skema = 1`, `pesanan.kanal` belum ada, `produk.kategori` belum ada).
- Pandangan terpadu dari `bingkai_terpadu()` atas koleksi hasil migrasi sama dengan pandangan terpadu Bagian C pada 13 dari 17 kolom
  (id ulasan, id pesanan, kode produk, id pelanggan, bintang, aspek, teks, jumlah media, jumlah tag, dan seterusnya).

## Kolom yang berubah makna
Empat kolom berbeda dari aslinya untuk dokumen hasil migrasi: `versi_skema`, `ada_balasan`, `kanal_dok`, dan `kategori_dok`.

- **`versi_skema`** berubah dari 1 menjadi 2 pada 3.892 dokumen. Asal dokumen kini hanya bisa diketahui dari `migrasi.dari_versi`.
- **`ada_balasan`** semula kosong karena v1 tidak merekam balasan penjual. Setelah migrasi, nilainya menjadi `False` pada seluruh 3.892 dokumen.
  Maknanya bergeser dari "tidak diketahui" menjadi "tidak ada balasan", padahal v1 tidak pernah mencatatnya. Ini perubahan yang paling
  berisiko karena terlihat seperti data sungguhan dan bisa memengaruhi hitungan, misalnya persentase ulasan yang dibalas.
- **`kanal_dok`** dan **`kategori_dok`** semula kosong dan kini terisi dari SQLite. Isinya sesuai basis data, tetapi bukan hasil rekaman
  dokumen ulasan itu sendiri.

Kolom aspek (`aspek_kualitas`, `aspek_pengiriman`) dan tag tidak berubah maknanya: pada dokumen migrasi keduanya tetap kosong,
karena memang tidak pernah direkam oleh v1.

## Kesimpulan
Migrasi menyeragamkan bentuk dokumen sehingga satu kueri cukup membaca satu bentuk (misalnya `penilaian.bintang <= 2` kini menemukan
semua ulasan rendah, bukan hanya yang berskema v2). Namun migrasi tidak menambah pengetahuan. Yang tidak pernah dicatat v1 tetap harus
dibaca sebagai tidak diketahui, dan setiap nilai yang diisi dari sumber lain perlu dicatat asalnya, seperti penanda `migrasi.dari_versi`.
