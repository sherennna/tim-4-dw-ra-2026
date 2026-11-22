# Jawaban Latihan 4.2 — Duplikat Produk dan Toko

## 1. Ringkasan

Latihan ini memeriksa keunikan `kode_produk` dan `nama_produk`, mencari kandidat produk duplikat, serta memvalidasi konsistensi komponen nama produk terhadap kategori, provinsi toko, dan nomor pada kode produk. Selanjutnya, atribut toko diringkas berdasarkan `id_toko` dan disimpan ke `keluaran/konsistensi_toko_m04.csv`. Keputusan mengenai apakah tabel toko dapat diturunkan dari katalog dibuat berdasarkan konsistensi nama toko, provinsi, dan rating untuk setiap ID toko.

## 2. Data yang Dipakai

- **Berkas masukan:** `data/raw/produk.csv`.
- **Kolom utama:** `kode_produk`, `nama_produk`, `id_toko`, `kategori`, `provinsi_toko`, `nama_toko`, dan `rating_toko`.
- **Berkas keluaran:** `dw-module-04/keluaran/konsistensi_toko_m04.csv`.
- **Berkas keputusan:** `dw-module-04/log-keputusan.csv`.

Jumlah baris dan kolom dicatat berdasarkan hasil pemeriksaan DataFrame pada notebook.

## 3. Temuan dan Bukti

### A. Keunikan produk

Hasil pemeriksaan mencakup jumlah baris katalog, jumlah `kode_produk` unik, jumlah `nama_produk` unik, serta jumlah kode dan nama yang berulang. Produk dengan nama mirip diperiksa sebagai kandidat duplikat, tetapi kemiripan nama tidak langsung membuktikan bahwa produknya identik.

### B. Konsistensi nama produk

Komponen nama produk dibandingkan dengan kolom `kategori`, `provinsi_toko`, dan nomor pada `kode_produk`. Ketidaksesuaian dicatat sebagai kandidat inkonsistensi yang perlu ditinjau, terutama jika nama kategori atau wilayah terdiri atas beberapa kata.

### C. Ringkasan konsistensi toko

Ringkasan dibuat berdasarkan `id_toko` dan mencakup jumlah produk, banyaknya variasi nama toko, banyaknya variasi provinsi, serta nilai minimum dan maksimum rating. Hasilnya disimpan dalam `konsistensi_toko_m04.csv`.

Angka jumlah ketidaksesuaian dan variasi atribut dilaporkan berdasarkan keluaran kode pada notebook.

## 4. Keputusan

Keputusan mengenai tabel toko didasarkan pada apakah setiap `id_toko` memiliki atribut nama toko, provinsi, dan rating yang konsisten.

Jika terdapat beberapa nama toko atau provinsi untuk satu ID, atribut tersebut perlu diperiksa sebelum menentukan satu nilai per toko. Jika rating bervariasi, aturan pemilihan rating juga harus ditetapkan.

Alternatif membuat tabel toko dengan langsung mengambil satu baris pertama per `id_toko` tidak dipilih tanpa pemeriksaan, karena dapat menyembunyikan konflik atribut. Keputusan akhir dan alasan pemilihannya dicatat pada `log-keputusan.csv`.

## 5. Rekonsiliasi Jumlah Baris

| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| Membaca katalog | Isi dari notebook | Isi dari notebook | Hitung | Data awal |
| Pemeriksaan duplikat | Isi dari notebook | Isi dari notebook | Hitung | Pemeriksaan tidak otomatis menghapus baris |
| Ringkasan per toko | Isi dari notebook | Isi dari notebook | Hitung | Satu baris untuk setiap `id_toko` |

## 6. Jawaban Pertanyaan Analisis

**Apakah `kode_produk` unik?**  
Jawab berdasarkan jumlah kode unik dibandingkan jumlah baris katalog dan hasil pemeriksaan kode berulang.

**Apakah `nama_produk` unik?**  
Jawab berdasarkan jumlah nama unik dan hasil pemeriksaan nama yang berulang. Nama yang sama belum tentu membuktikan produk identik tanpa membandingkan atribut lainnya.

**Apakah bagian nama produk konsisten?**  
Jawab berdasarkan jumlah kategori, provinsi, dan nomor kode yang cocok maupun tidak cocok. Ambiguitas pemisahan nama perlu diperhatikan ketika komponennya memiliki lebih dari satu kata.

**Dapatkah tabel toko diturunkan dari katalog?**  
Keputusan dibuat berdasarkan konsistensi atribut per `id_toko`. Jika ada konflik, konflik harus diselesaikan sebelum satu baris per toko ditetapkan.

## 7. Keterbatasan

Kemiripan nama tidak selalu berarti dua produk adalah duplikat. Pemisahan nama berdasarkan spasi dapat menghasilkan interpretasi yang keliru apabila kategori atau wilayah terdiri atas beberapa kata. Selain itu, perbedaan rating bisa mencerminkan perubahan nilai atau inkonsistensi data sehingga perlu aturan penanganan yang jelas.

## 8. Pengungkapan Penggunaan Alat Bantu

Asisten berbasis kecerdasan buatan digunakan untuk membantu menyusun kode pemeriksaan dan merapikan struktur laporan. Seluruh angka temuan dan keputusan akhir harus diverifikasi berdasarkan hasil kode dan keluaran notebook.