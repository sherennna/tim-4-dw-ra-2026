# Laporan Modul 05 — Latihan 5.2: Label atau One-Hot

| Komponen | Isi |
|---|---|
| Nama | Talitha Justine |
| NIM | 124450076 |
| Tanggal pengumpulan | 28 Oktober 2026 |
| Seed dan ukuran data | seed 2026, ukuran kecil |
| Versi Python dan pandas | (isi sendiri) |

## 1. Ringkasan

Saya memprediksi `log1p(nilai_rata_pesanan)` dari empat kolom kategorik dengan dua encoding (label menurut abjad dan one-hot) dan dua model (regresi linear dan pohon keputusan `max_depth=8`). Kombinasi label + regresi linear paling buruk (R² 0,3914), sedangkan pohon hampir sama untuk kedua encoding (0,5424 dan 0,5395). Hasil ini belum bisa dianggap valid untuk generalisasi karena R² latih dan uji identik (lihat bagian 7).

## 2. Data yang Dipakai

Kolom kategorik: `kanal`, `kategori_favorit`, `metode_bayar_utama`, `provinsi`. Target: `log1p(nilai_rata_pesanan)`. Kode otomatis memilih `fitur` (6.170 baris) dan `fitur_m05` (6.170 baris) sebagai data latih dan uji. Encoder (`OrdinalEncoder` untuk label, `OneHotEncoder` dengan `handle_unknown="ignore"`) dan model di-`fit` hanya pada DataFrame yang dianggap latih. Hasilnya ada di `keluaran/encoding_model_m05.csv`.

## 3. Temuan dan Bukti

Tabel berikut dari `hasil_enc` di sel Latihan 5.2.

| encoding | model | n_kolom | R² latih | R² uji |
|---|---|---:|---:|---:|
| label | LinearRegression | 4 | 0,3914 | 0,3914 |
| label | DecisionTreeRegressor | 4 | 0,5424 | 0,5424 |
| onehot | LinearRegression | 26 | 0,5176 | 0,5176 |
| onehot | DecisionTreeRegressor | 26 | 0,5395 | 0,5395 |

Regresi linear naik dari 0,3914 (label) ke 0,5176 (one-hot), selisih 0,1262. Pohon hampir tidak berubah: 0,5424 untuk label dan 0,5395 untuk one-hot, selisih 0,0029. Dengan one-hot, regresi linear sudah mendekati pohon. One-hot mengubah empat kolom menjadi 26 kolom.

## 4. Keputusan

Pipeline Bagian D tetap memakai one-hot untuk kolom kategorik nominal (K-05-007), ordinal dengan urutan eksplisit untuk `kelompok_usia` (K-05-008), dan frequency encoding untuk `produk_favorit` yang kardinalitasnya tinggi (K-05-009). Latihan ini hanya membahas empat kolom berkardinalitas rendah, jadi `produk_favorit` tidak diuji. Keputusan dari latihan ini masih perlu saya tambahkan ke `log-keputusan.csv` sebagai baris `K-05-0xx` baru.

## 5. Rekonsiliasi Jumlah Baris

| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| Data latih dan uji untuk model | 6.170 | 6.170 | 0 | Tidak ada baris dibuang. Kedua DataFrame terdeteksi berukuran sama (lihat bagian 7). |

## 6. Jawaban Pertanyaan Analisis

Kombinasi yang paling rugi adalah label encoding dengan regresi linear (R² 0,3914). Label encoding memberi kode 0, 1, 2, dan seterusnya menurut abjad, sehingga regresi linear dipaksa menganggap efek kategori naik atau turun mengikuti kode itu, padahal urutan abjad tidak bermakna. Di Bagian D.1 terlihat Aceh–Sumatera Utara berjarak 9 sedangkan Aceh–Bengkulu berjarak 1. One-hot menghilangkan asumsi itu dan menaikkan R² menjadi 0,5176.

Pohon hampir tidak terpengaruh karena ia memisahkan data dengan aturan "kode ≤ ambang". Dengan kedalaman 8, pohon bisa memotong beberapa kali pada kolom yang sama untuk memisahkan kategori tertentu, jadi urutan kodenya tidak lagi menentukan. Itu sebabnya hasilnya hampir sama (0,5424 dan 0,5395).

Untuk Bagian D, saya tetap memakai one-hot pada kanal, kategori, metode bayar, dan provinsi. Label encoding berisiko untuk model linear dan model berbasis jarak seperti k-means, dan keuntungan kecilnya pada pohon (0,0029) tidak sebanding.

## 7. Keterbatasan

Masalah utamanya, R² latih dan uji sama persis di keempat baris, yang tidak wajar untuk pembagian latih-uji yang benar. Kemungkinan besar kode memakai dua DataFrame yang memuat baris yang sama (`fitur` dan `fitur_m05`, masing-masing 6.170 baris), bukan `latih` (4.201) dan `uji` (1.969). Jadi model dievaluasi pada data yang sama dengan data pelatihannya, dan kolom `r2_uji` belum menunjukkan kemampuan generalisasi. Pohon dengan kapasitas tinggi bisa terlihat lebih baik dari sebenarnya. Latihan ini perlu dijalankan ulang dengan `DF_LATIH_MANUAL = latih` dan `DF_UJI_MANUAL = uji`. Selain itu, perbandingan hanya memakai satu `max_depth` (8) dan satu seed (2026) tanpa validasi silang, dan kesimpulannya hanya berlaku untuk kolom berkardinalitas rendah.

## 8. Pengungkapan Penggunaan Alat Bantu

Saya memakai Claude untuk membantu menyusun kerangka kode latihan dan draf laporan ini. Semua angka diambil dari output notebook yang saya jalankan.
