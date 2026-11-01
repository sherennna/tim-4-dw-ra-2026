# Laporan Modul 05 — Latihan 5.1: Sensitivitas terhadap Skala

| Komponen | Isi |
|---|---|
| Nama | Talitha Justine |
| NIM | 124450076 |
| Tanggal pengumpulan | 28 Oktober 2026 |
| Seed dan ukuran data | seed 2026, ukuran kecil |
| Versi Python dan pandas | (isi sendiri) |

## 1. Ringkasan

Saya membandingkan lima perlakuan skala (`tanpa_skala`, `minmax`, `zscore`, `robust`, `acuan`) pada delapan fitur numerik pelanggan, lalu menjalankan k-means (k = 4) dan pencarian 10 tetangga terdekat pada tiap perlakuan. Tanpa skala, klaster hampir seluruhnya ditentukan `omzet`. Pada `robust`, `nilai_batal` malah menguasai seluruh ragam. Saya memilih `acuan` karena tidak ada satu fitur pun yang mendominasi jarak.

## 2. Data yang Dipakai

Fitur pelanggan dari Bagian A–D (6.170 baris) dan kolom `t_` dari `fitur_pelanggan_m05.parquet`. Delapan fitur yang diskalakan: `frekuensi`, `omzet`, `nilai_rata_pesanan`, `jumlah_unit`, `n_kategori`, `rata_diskon`, `nilai_batal`, `recency_hari`. Hasilnya ada di `keluaran/sensitivitas_skala_m05.csv` dan `keluaran/05_sensitivitas_skala.png`.

## 3. Temuan dan Bukti

Tabel berikut berasal dari `hasil_skala` di sel Latihan 5.1.

| skala | fitur dominan | porsi ragam | klaster terkecil | klaster terbesar | silhouette | ARI vs acuan | irisan tetangga |
|---|---|---:|---:|---:|---:|---:|---:|
| tanpa_skala | omzet | 0,7415 | 21 | 4.587 | 0,6064 | 0,0513 | 0,0295 |
| minmax | rata_diskon | 0,3589 | 1.023 | 2.082 | 0,3183 | 0,3800 | 0,0661 |
| zscore | frekuensi | 0,1250 | 52 | 3.326 | 0,2584 | 0,2801 | 0,1020 |
| robust | nilai_batal | 1,0000 | 3 | 5.922 | 0,9259 | 0,0009 | 0,1017 |
| acuan | t_rata_diskon | 0,1055 | 1.049 | 2.075 | 0,1210 | 1,0000 | 1,0000 |

Tanpa skala, `omzet` menyumbang 74,15% ragam, jadi jarak Euclid pada dasarnya hanya mengukur rupiah dan klaster terkecil cuma berisi 21 entitas. Pada `robust`, IQR `nilai_batal` bernilai 0 (3.237 dari 4.201 entitas latih bernilai nol), sehingga kolom itu tidak ikut terskala dan memegang 100% ragam. Hasilnya satu klaster hanya berisi 3 entitas. `minmax` dan `zscore` lebih seimbang, tetapi `zscore` tanpa log masih menyisakan klaster kecil (52 entitas) karena ekor kanan belum dijinakkan. Pada `acuan`, klasternya 1.049 dan 2.075 entitas, dan porsi ragam terbesar hanya 10,55%. Irisan tetangga antara perlakuan lain dan `acuan` rendah (0,03–0,10), artinya pilihan skala mengubah siapa yang dianggap "dekat".

## 4. Keputusan

Saya memakai `acuan` (`log1p` untuk fitur berekor kanan lalu z-score, parameter dari bagian latih), sesuai K-05-005 dan K-05-006. `minmax` tidak dipilih karena minimum dan maksimumnya ditentukan dua entitas grosir (K-05-003). `robust` tidak dipilih karena IQR `nilai_batal` nol. Keputusan latihan ini masih perlu saya tambahkan ke `log-keputusan.csv` sebagai baris `K-05-0xx` baru.

## 5. Rekonsiliasi Jumlah Baris

| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| Saring baris tanpa NaN | 6.170 | 6.170 | 0 | Fitur numerik tidak punya NaN (asersi di Bagian A.3). Kode latihan tidak mencetak jumlah baris yang disaring. |

## 6. Jawaban Pertanyaan Analisis

Dua perlakuan klasternya ditentukan satu fitur: `tanpa_skala` oleh `omzet` (74,15% ragam) dan `robust` oleh `nilai_batal` (100%). Pada `robust` penyebabnya IQR nol yang diganti pembagi 1, jadi satu klaster hanya berisi 3 entitas sementara yang terbesar berisi 5.922.

Silhouette tertinggi (0,926 pada `robust`, 0,606 pada `tanpa_skala`) tidak berarti segmentasinya terbaik. Nilai itu tinggi karena hampir semua titik menumpuk di satu klaster besar dan beberapa pencilan membentuk klaster sendiri. Silhouette hanya mengukur keterpisahan bentuk, bukan apakah segmennya berguna. ARI `robust` terhadap `acuan` cuma 0,0009, jadi pembagiannya hampir tidak mirip. Silhouette `acuan` memang paling rendah (0,121), tetapi ukuran klasternya paling seimbang.

Saya memakai `acuan`: tidak ada fitur yang menguasai jarak, ekor kanan sudah ditangani `log1p`, dan parameternya tersimpan dari bagian latih sehingga bisa dipakai lagi pada data baru.

## 7. Keterbatasan

Ada beberapa hal yang belum sesuai instruksi soal. Pertama, kode mendeteksi DataFrame secara otomatis dan memakai `fitur` (6.170 baris, latih + uji), padahal soal meminta bagian latih (4.201 entitas), jadi angkanya perlu dijalankan ulang dengan `latih`. Kedua, perlakuan `acuan` memakai semua 37 kolom `t_` (termasuk one-hot), bukan delapan kolom `t_` numerik, sehingga perbandingan ARI dan irisan tetangga dengan perlakuan lain tidak sepenuhnya setara. Ketiga, `parameter_skala` dan `skalakan` dari notebook gagal dengan `ValueError`, jadi skala dihitung dengan versi manual yang rumusnya sama; penyebab galatnya belum saya telusuri. Terakhir, k-means hanya diuji pada k = 4.

## 8. Pengungkapan Penggunaan Alat Bantu

Saya memakai Claude untuk membantu menyusun kerangka kode latihan dan draf laporan ini. Semua angka diambil dari output notebook yang saya jalankan.
