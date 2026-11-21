# Latihan 4.1 — Parser Tanggal Daftar Pelanggan Web

## 1. Ringkasan

Latihan ini menganalisis pola penulisan `tgl_daftar` pada data pelanggan web dan membandingkan hasil parsing menggunakan `format="mixed"` dengan `format="mixed", dayfirst=True`. Hasil pengelompokan menunjukkan tiga pola penulisan tanggal, yaitu `9999-99-99`, `99/99/9999`, dan `99-AAA-9999`. Bukti pada pola bergaris miring mendukung urutan hari/bulan/tahun karena nilai maksimum bagian pertama adalah 31, bagian kedua adalah 12, dan terdapat 616 baris dengan bagian pertama lebih besar dari 12. Perbedaan interpretasi tanggal dapat memengaruhi pencocokan data pelanggan web dengan aplikasi pada Bagian D.

## 2. Data yang Dipakai

- Data utama: tabel pelanggan web (`wu`), khususnya kolom `tgl_daftar`.
- Data pembanding: tabel pelanggan aplikasi (`app`), khususnya kolom tanggal registrasi.
- Kolom hasil pengolahan: `pola`, `tgl_web`, `p_mixed`, dan `p_dayfirst`.
- Keluaran yang diminta: `keluaran/parser_tanggal_m04.csv`.
- Jumlah baris dan kolom setiap dataset dicatat dari hasil pemeriksaan notebook sebelum pengolahan.

## 3. Temuan dan Bukti

### A. Pola penulisan tanggal

Hasil pengelompokan berdasarkan pola penulisan:

| Pola | Jumlah baris | Contoh |
|---|---:|---|
| `9999-99-99` | 1633 | `2024-04-27` |
| `99/99/9999` | 1000 | `07/07/2024` |
| `99-AAA-9999` | 627 | `10-Nov-2024` |

Total ketiga kelompok adalah 3260 baris.

### B. Bukti urutan hari dan bulan

Untuk pola `99/99/9999`, hasil pemeriksaan menunjukkan:

- Nilai maksimum bagian pertama: 31.
- Nilai maksimum bagian kedua: 12.
- Jumlah baris dengan bagian pertama lebih besar dari 12: 616.

Karena angka 17 sampai 31 tidak mungkin menjadi bulan, bukti ini mendukung format DD/MM/YYYY, bukan MM/DD/YYYY.

### C. Perbandingan parser

Hasil notebook menunjukkan jumlah tanggal yang berbeda antara kedua parser:

| Pola | `beda_mixed` | `beda_mixed_dayfirst` |
|---|---:|---:|
| `99-AAA-9999` | 0 | 0 |
| `99/99/9999` | 354 | 0 |
| `9999-99-99` | 0 | 640 |

Parser `mixed` dapat menafsirkan tanggal numerik yang ambigu dengan urutan bulan/hari. Penggunaan `dayfirst=True` mengutamakan hari sebagai komponen pertama. Perbedaan interpretasi ini dapat menghasilkan tanggal kalender yang berbeda.

Angka di atas mengikuti kolom ringkasan notebook. Definisi perbedaan dan cara menghitungnya perlu diperiksa pada kode pembentuk tabel agar dapat dijelaskan secara tepat.

## 4. Keputusan

1. Mengelompokkan tanggal berdasarkan pola penulisan agar setiap format dapat diperiksa secara terpisah.
2. Menggunakan bukti data untuk menentukan urutan hari dan bulan pada pola garis miring.
3. Membandingkan hasil parser `mixed` dan `mixed, dayfirst=True`, bukan langsung menganggap salah satu hasil selalu benar.
4. Mempertahankan tanggal asli sebagai bukti dan menggunakan hasil parsing terpisah untuk validasi serta pencocokan.
5. Tidak menetapkan persentase kecocokan Bagian D sebelum hasil pencocokan aktual diperiksa.

Alternatif yang tidak dipilih adalah menggunakan satu asumsi format untuk seluruh data tanpa memeriksa pola, karena pendekatan tersebut dapat menghasilkan interpretasi tanggal yang keliru.

## 5. Rekonsiliasi Jumlah Baris

| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| Data pelanggan web | 3260 | 3260 | 0 | Jumlah dari tiga kelompok pola tanggal |
| Pengelompokan pola | 3260 | 3260 | 0 | Pengelompokan tidak menghapus baris |
| Parsing tanggal | Periksa hasil aktual | Periksa hasil aktual | Periksa hasil aktual | Tanggal gagal parsing perlu dihitung |
| Pencocokan Bagian D | Periksa hasil aktual | Periksa hasil aktual | Periksa hasil aktual | Bergantung pada aturan pencocokan |

## 6. Jawaban Pertanyaan Analisis

### Mengapa urutan tanggal garis miring adalah hari/bulan?

Nilai maksimum bagian pertama adalah 31, sedangkan bagian kedua hanya 12. Selain itu, 616 baris memiliki bagian pertama lebih besar dari 12. Nilai-nilai tersebut tidak mungkin menjadi bulan, sehingga urutan DD/MM/YYYY lebih masuk akal berdasarkan bukti data.

### Mengapa parser dapat menghasilkan tanggal berbeda?

Format tanggal numerik seperti `05/10/2024` bersifat ambigu tanpa aturan format. Tanggal tersebut dapat dibaca sebagai 5 Oktober atau 10 Mei. Pengaturan `dayfirst=True` mengutamakan interpretasi hari/bulan, sedangkan parser `mixed` dapat menggunakan interpretasi berbeda.

### Apa dampaknya pada pencocokan Bagian D?

Jika tanggal yang sama ditafsirkan menjadi tanggal kalender yang berbeda, pencocokan berdasarkan tanggal dapat gagal atau menghasilkan pasangan yang salah. Persentase kecocokan harus dihitung dari hasil pencocokan aktual untuk setiap konfigurasi parser, termasuk kondisi tanggal aplikasi dibiarkan dalam UTC.

## 7. Keterbatasan

Analisis ini bergantung pada pola tanggal yang tersedia dan asumsi tentang format yang digunakan. Tanggal yang ambigu tidak selalu dapat dipastikan hanya dari teksnya. Selain itu, angka persentase kecocokan Bagian D belum dicantumkan karena hasil lengkap pencocokan dan penyebut perhitungannya perlu diverifikasi dari notebook.

## 8. Pengungkapan Penggunaan Alat Bantu

Asisten berbasis kecerdasan buatan digunakan untuk membantu menyusun struktur laporan Markdown, menjelaskan interpretasi hasil parser, dan merapikan tabel temuan. Pengolahan data dan angka hasil analisis harus tetap berasal dari kode serta keluaran notebook yang dijalankan.