# Laporan Modul 02: Penanganan Nilai Hilang

#ZANNUBA ARIFAH ILMAN
#124450112
#30/09/2026

## 1. Ringkasan

Modul ini mendiagnosis mekanisme nilai hilang pada tiga kolom tabel transaksi (ongkir, lama_kirim_hari, rating_ulasan) dan memutuskan cara menanganinya, serta mengevaluasi interpolasi untuk data sensor gudang. Temuan terpenting: ongkir hilang 90,7% pada kanal app selama 1 Sep sampai 15 Okt 2025 (jendela itu menyumbang 75,4% dari seluruh kekosongan), sedangkan rating_ulasan hilang 30,32% dari baris yang berlaku dan diduga MNAR karena rating hilang makin sering saat rating teramati makin rendah. Keputusan terpenting adalah mengimputasi ongkir secara deduktif dari total_bayar (MAE 140,1 vs 9.355,9 untuk rata-rata global) tetapi tidak mengimputasi rating_ulasan; rating dilaporkan sebagai kasus lengkap disertai analisis sensitivitas, karena imputasi pada data MNAR akan membiaskan hasil ke atas.

## 2. Data yang Dipakai

- Berkas masukan: transaksi_m02.parquet, 24.288 baris (Gambar 1 dan rekonsiliasi_nilai_hilang.csv); 12 kolom
- Berkas sensor: sensor_m02.parquet (3 gudang: GDG-BDL, GDG-MDN, GDG-PLM; variabel suhu_c dan kelembapan_persen, interval 10 menit)
- Keluaran modul sebelumnya: tidak ada
- Kolom kunci pada analisis: ongkir, lama_kirim_hari, rating_ulasan, id_pelanggan, total_bayar, kanal, kurir, provinsi_tujuan, status
- Keluaran modul ini: mekanisme_nilai_hilang.csv, rekonsiliasi_nilai_hilang.csv, evaluasi_imputasi_ongkir.csv, evaluasi_interpolasi_sensor.csv, sensitivitas_rating.csv, log-keputusan.csv, dan grafik 01 sampai 05

## 3. Temuan dan Bukti

Temuan 1: Kekosongan ongkir terkonsentrasi pada satu kanal dan satu jendela waktu (MAR). 
Pada kanal app, 90,7% ongkir hilang selama 1 Sep sampai 15 Okt 2025, dan jendela ini menyumbang 75,4% dari seluruh kekosongan. Di luar jendela laju hilang hanya 1,17% dan tidak berhubungan dengan kanal, kurir, provinsi, maupun status (uji chi-kuadrat, p ≥ 0,38). Token `-` seluruhnya berasal dari kurir Pos Indonesia, sehingga token itu MAR menurut kurir. Sumber: Gambar 2 ( 02_ongkir_hilang_harian.png ), mekanisme_nilai_hilang.csv .

Temuan 2: Nilai hilang pada lama_kirim_hari konsisten dengan MCAR. 
Terdapat 127 penanda ( 999 dan -1 ), setara 0,60% dari 21.049 baris yang berlaku, dan tidak berhubungan dengan kurir, kanal, atau provinsi (p ≥ 0,17). Sebanyak 3.239 sel kosong bersifat struktural (status dibatalkan atau diproses) dan bukan data hilang. Sumber: rekonsiliasi_nilai_hilang.csv , Gambar 1.

Temuan 3: rating_ulasan hilang dalam jumlah besar dan mengarah ke MNAR. 
Dari 20.072 baris yang berlaku, 6.085 (30,32%) hilang: 3.280 kosong dan 2.805 berupa penanda. Setelah nilai 0 diungkap sebagai penanda, laju hilang app 30,58% vs web 30,10% (p = 0,47), jadi kanal bukan penjelasannya. Namun laju hilang naik dari 29,7% (lama kirim 1-2 hari) menjadi 54,4% (8-30 hari), sementara rata-rata rating teramati turun dari 4,29 menjadi 2,97. Ini pola yang konsisten dengan MNAR, tetapi tetap dugaan dan tidak dapat dibuktikan dari data. Sumber: Gambar 3 ( 03_rating_hilang_lama_kirim.png ).

Temuan 4: Imputasi deduktif jauh lebih akurat daripada imputasi sederhana untuk ongkir . 
Pada 2.317 titik uji:

| Metode | MAE | Bias | % tepat | Rasio SD |
|---|---:|---:|---:|---:|
| Rata-rata global | 9.355,9 | 544,4 | 0,00 | 0,928 |
| Median global | 7.110,5 | -4.615,0 | 0,35 | 0,931 |
| Median provinsi | 5.724,4 | -5.724,4 | 73,20 | 0,932 |
| Deduktif lalu median provinsi | 140,1 | -19,2 | 98,83 | 1,007 |

Rasio SD mendekati 1 pada metode deduktif berarti sebaran data tidak menyusut. Pada Gambar 4, rata-rata ongkir kanal app bulan Sep 2025 turun ke sekitar 16.000 bila diisi median global, sedangkan hasil keputusan akhir mengikuti pola nilai teramati. Sumber: evaluasi_imputasi_ongkir.csv , Gambar 4 ( 04_dampak_imputasi_ongkir.png ).

Temuan 5: Kesimpulan tentang rating sensitif terhadap asumsi data hilang, khususnya untuk kanal web. 
Dengan hanya kasus lengkap (δ = 0), rata-rata rating semua kanal 3,567, app 2,956, web 4,212. Bila rating yang hilang lebih rendah 1,0 poin dari rata-rata teramati (δ = -1,0), rata-rata web turun menjadi 3,997, yaitu jatuh di bawah target 4,0; pada δ = -2,0 rata-rata semua kanal menjadi 3,332. Rata-rata app tidak berubah di semua δ (2,956); penyebabnya tidak tampak dari keluaran ini dan perlu dicek di kode. Sumber: sensitivitas_rating.csv , Gambar 5 ( 05_sensitivitas_rating.png ).

Temuan 6: Galat interpolasi sensor tidak naik teratur menurut panjang celah, dan RMSE jauh lebih besar dari MAE untuk suhu. 
Untuk kelembapan_persen , MAE berkisar 2,6 sampai 3,2 di semua panjang celah (1 sampai 12 langkah, 10 sampai 120 menit) dan di ketiga gudang. Untuk suhu_c , MAE 0,15 sampai 0,90, tetapi RMSE bisa 4 sampai 10 kali MAE (mis. GDG-BDL, celah 3: MAE 0,898, RMSE 8,794), yang menandakan segelintir galat sangat besar (kemungkinan lonjakan atau nilai ekstrem). Sumber: evaluasi_interpolasi_sensor.csv .

## 4. Keputusan

Isi keputusan di bawah dirujuk dari file `log-keputusan.csv`:

Keputusan 1 ( log-keputusan.csv , baris 1 ): Imputasi ongkir secara deduktif dari total_bayar ; sisanya memakai median per provinsi_tujuan ; tambahkan kolom ongkir_metode untuk menandai asal nilai.
- Alternatif yang dipertimbangkan: rata-rata global, median global, dan median provinsi saja.
- Mengapa tidak dipilih: MAE 9.355,9 (rata-rata global), 7.110,5 (median global), dan 5.724,4 (median provinsi), semuanya jauh di atas 140,1 milik metode terpilih. Median global juga menekan rata-rata bulanan kanal app pada jendela kekosongan (Gambar 4). Penghapusan baris tidak dipilih karena kekosongan terkonsentrasi pada satu kanal dan periode, sehingga akan menghilangkan 75,4% dari seluruh data hilang.

Keputusan 2 ( log-keputusan.csv , baris 2 ): Ubah penanda 999 dan -1 pada lama_kirim_hari menjadi NaN, tidak diimputasi, dan analisis memakai kasus tersedia.
- Alternatif yang dipertimbangkan: imputasi median atau rata-rata.
- Mengapa tidak dipilih: penanda hanya 0,60% dari baris yang berlaku dan konsisten dengan MCAR (p ≥ 0,17), jadi kasus tersedia tidak membiaskan hasil. Selain itu, 3.239 sel kosong bersifat struktural sehingga memang tidak seharusnya diisi.

Keputusan 3 ( log-keputusan.csv , baris 3 ): Tidak mengimputasi rating_ulasan ; laporkan kasus lengkap disertai analisis sensitivitas.
- Alternatif yang dipertimbangkan: imputasi (rata-rata atau model) dan penghapusan baris tanpa rating.
- Mengapa tidak dipilih: bila mekanismenya MNAR, imputasi dari nilai teramati mengisi rating yang hilang dengan angka yang terlalu tinggi (rating teramati 4,29 pada pengiriman cepat vs 2,97 pada pengiriman lambat, sedangkan laju hilang justru tertinggi di kelompok lambat). Analisis sensitivitas dengan δ dari 0 sampai -2,0 menunjukkan seberapa jauh kesimpulan bergeser.

Keputusan 4 ( log-keputusan.csv , baris 4 ): Metode interpolasi sensor menggunakan Interpolasi Linier (Linear Interpolation).
- Alternatif yang dipertimbangkan: Imputasi Rata-rata Global / Forward Fill (LOCF).
- Mengapa tidak dipilih: Interpolasi linier mempertahankan kontinuitas tren waktu untuk variabel sensor, serta menghasilkan MAE yang paling stabil (2,6–3,2 untuk kelembapan_persen dan 0,15–0,90 untuk suhu_c) di seluruh rentang celah (10 hingga 120 menit).

## 5. Rekonsiliasi Jumlah Baris

Pada modul ini tidak ada baris yang dibuang: seluruh penanganan berupa pengisian, penandaan, atau pembiaran nilai, sehingga jumlah baris tetap.

| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| Data mentah dimuat ( transaksi_m02.parquet ) | – | 24.288 | – | Berkas asal |
| Imputasi ongkir (deduktif, lalu median provinsi) | 24.288 | 24.288 | 0 | 1.111 sel terisi, baris tidak dibuang |
| Penanda lama_kirim_hari menjadi NaN | 24.288 | 24.288 | 0 | 127 penanda, baris dipertahankan |
| rating_ulasan dibiarkan (kasus lengkap) | 24.288 | 24.288 | 0 | 6.085 hilang, tidak diimputasi |
| Akhir | | 24.288 | 0 | Cocok dengan bagian 2 |

Rekonsiliasi sel per kolom ( rekonsiliasi_nilai_hilang.csv ):

| Kolom | Baris | Teramati | Kosong | Penanda | Tidak berlaku | Berlaku | Hilang | % hilang dari berlaku |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ongkir | 24.288 | 23.177 | 1.075 | 36 | 0 | 24.288 | 1.111 | 4,57 |
| lama_kirim_hari | 24.288 | 20.922 | 0 | 127 | 3.239 | 21.049 | 127 | 0,60 |
| rating_ulasan | 24.288 | 13.987 | 3.280 | 2.805 | 4.216 | 20.072 | 6.085 | 30,32 |
| id_pelanggan | 24.288 | 23.870 | 0 | 0 | 418 | 23.870 | 0 | 0,00 |

Pemeriksaan: untuk setiap kolom, teramati + hilang = berlaku (mis. rating_ulasan : 13.987 + 6.085 = 20.072; ongkir : 23.177 + 1.111 = 24.288). Kolom tidak_berlaku pada rating_ulasan berjumlah 4.216 karena pesanan belum selesai/terkirim (dibatalkan atau diproses).

## 6. Jawaban Pertanyaan Analisis

Pertanyaan: "Apakah rata-rata rating pesanan selesai mencapai target 4,0?"

Jawaban: Belum dapat dipastikan tercapai. Rata-rata rating dari kasus lengkap adalah 3,567 untuk semua kanal (app 2,956; web 4,212), sehingga secara keseluruhan di bawah target 4,0. Kanal web hanya melewati target bila rating yang hilang tidak lebih rendah dari rata-rata teramati sebesar 1,0 poin atau lebih; pada δ = -1,0 rata-rata web sudah 3,997. Didukung Temuan 3 dan 5. Tingkat keyakinan: sedang untuk kesimpulan bahwa semua kanal di bawah target, rendah untuk kanal web , karena 30,32% rating hilang dan mekanisme MNAR tidak dapat diuji dari data.

## 7. Keterbatasan

- Mekanisme MNAR pada rating_ulasan adalah dugaan. Pola pada Gambar 3 konsisten dengan MNAR, tetapi data yang hilang tidak dapat diamati, sehingga hubungan itu tidak dapat dibuktikan. Besaran δ pada analisis sensitivitas adalah skenario, bukan estimasi.
- Evaluasi imputasi ongkir dilakukan pada 2.317 titik uji. Hasilnya baik (98,83% tepat), tetapi bergantung pada asumsi bahwa hubungan total_bayar dan ongkir di baris yang hilang sama dengan baris yang teramati. Untuk jendela app 1 Sep sampai 15 Okt 2025 yang hampir seluruhnya hilang, asumsi ini tidak dapat diuji langsung.
- Interpolasi sensor: RMSE suhu jauh di atas MAE, artinya ada galat besar yang jarang terjadi. Belum diperiksa apakah galat itu berasal dari lonjakan nyata atau anomali sensor; disarankan memeriksa titik dengan galat terbesar sebelum interpolasi dipakai untuk analisis lanjutan.
- Analisis sensitivitas rating: rata-rata app tidak berubah terhadap δ (2,956). Penyebabnya belum diverifikasi dan perlu dicek di kode sebelum angka ini dipakai.
- Rujukan nomor baris log keputusan telah disesuaikan penuh mengacu pada tabel log-keputusan.csv yang disertakan.