## Nama tim dan avatar
Nama tim: Data Nusantara Sehat
Avatar tim: ikon stetoskop yang tersambung ke alur data (pipeline), warna hijau tosca.

## Komponen tiap anggota
| Anggota | Komponen (pilihan di kartu Tim saya) | Isi pekerjaan | Alasan |
| --- | --- | --- | --- |
|  | Ekstraksi dan lineage | `python unduh_data.py --kasus 4`, cek sha256, ingest seri BPS dan pembanding (WHO GHO, WDI), catatan asal data (lineage) | Pintu masuk data mentah, dikerjakan paling awal |
| Sherena Florencia | Profil dan pembersihan | Profiling tiga seri BPS (`var1393`, `var1480`, `var1435`), standardisasi provinsi, tahun, dan satuan, hingga `silver.parquet` | Mengubah data mentah menjadi Silver yang bersih |
|  | Transformasi dan panel | Jendela analisis bersama, penanganan outlier malaria, tabel Gold panel provinsi × periode × indikator, `log-keputusan.csv` | Keputusan epidemiologis harus terdokumentasi dan konsisten |
| Talitha Justine | Integrasi, penyimpanan, dan skala | Tabel rekonsiliasi dengan pembanding nasional (termasuk prevalensi merokok BPS vs WHO), penyimpanan Silver dan Gold, arsip WDI 142 rilis | Bergantung pada Silver dan Gold, paling aktif di Sprint 2 |
|  | Validasi dan dokumentasi | Skema validasi (pandera/Great Expectations), data dictionary, `python pipeline.py` yang mengulang semuanya dari data mentah | Memastikan hasil bisa diulang dan terdokumentasi |

## Tugas sampingan tiap anggota
Koordinator / Penjaga Data & Evaluasi / Integrator / Analis Utama / Reproduksi & Demo — siapa apa, dan mengapa.

| Anggota | Tugas sampingan | Alasan |
| --- | --- | --- |
| Djofy Prianda Banu | Koordinator | Memimpin rapat sprint, memantau Papan Tim, dan melapor ke pembimbing bila perlu |
| Jacinda Kesya Alvara | Integrator | Mengurus penggabungan lewat pull request ke `main` dan menyelesaikan konflik |
| Sherena Florencia | Penjaga Data & Evaluasi | Memeriksa kualitas data, checksum sha256, dan konsistensi keputusan penanganan outlier |
| Talitha Justine | Analis Utama | Menyusun interpretasi hasil rekonsiliasi dan ringkasan temuan untuk Profil Galeri |
| Jihan Putri Yani | Reproduksi & Demo | Memastikan `python pipeline.py` jalan dari nol, serta merekam dan mengirim Demo Sprint |

## Standup mingguan dan kanal komunikasi
**Hari/jam standup:** Rabu, 19.30 WIB, maksimal 15 menit. Rapat perencanaan awal sprint (Tujuan Sprint dan pembagian tugas) dilakukan terpisah pada hari pertama sprint.
 
**Kanal:**
 
- Grup chat untuk koordinasi cepat. Pesan dibalas maksimal 24 jam.
- Komentar di kartu tugas dan Log Sprint untuk hambatan, supaya pembimbing ikut melihat.
- Panggilan daring untuk kendala teknis yang sulit dijelaskan lewat teks.
Setiap standup menjawab tiga hal: apa yang sudah selesai, apa yang dikerjakan berikutnya, dan apa hambatannya.

## Jika ada anggota yang menghilang
Tim bertindak lebih dulu pada sprint pertama anggota tidak muncul, lalu melapor ke pembimbing bila berlanjut ke sprint kedua.
 
**Sprint pertama tidak muncul** (tanpa Log Sprint dan tanpa jejak):
 
1. Koordinator menghubungi anggota lewat chat pribadi dalam 24 jam.
2. Tim mengingatkan batas penutupan jendela Log Sprint. Log kosong tidak bisa disusulkan setelah jendela ditutup.
3. Tugas yang berisiko menghambat tim dialihkan sementara ke anggota lain dan dicatat di kartu tugas, tanpa diklaim sebagai pekerjaan penerimanya.
4. Hambatan dicatat di Log Sprint tim.
**Sprint kedua berturut-turut tidak muncul** (lampu merah dua kali):
 
1. Sistem memberi bendera, dan koordinator melapor ke pembimbing beserta bukti upaya menghubungi.
2. Tugas dibagi ulang secara tetap agar target sprint tetap tercapai.
3. Penilaian kontribusi mengikuti bukti yang tercatat. Tidak ada anggota yang boleh mencatat bukti atas pekerjaan yang bukan miliknya.
4. Anggota boleh bergabung kembali kapan saja dengan komponen yang disesuaikan.
