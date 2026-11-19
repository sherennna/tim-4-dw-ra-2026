# Laporan Modul 07 — Latihan 7.2: Etika dan Hukum Scraping

| Komponen | Isi |
|---|---|
| Nama | Talitha Justine |
| NIM | 124450076 |
| Tanggal pengumpulan | 11 November 2026 |
| Seed dan ukuran data | seed 2026, ukuran kecil |
| Versi Python dan pandas | ‹Python x.y.z› / ‹pandas x.y.z› (cetak dengan `sys.version` dan `pd.__version__`) |

## 1. Ringkasan

Latihan ini menganalisis permintaan perusahaan rintisan untuk memantau harga, rating, dan ulasan seluruh toko pesaing setiap hari, termasuk mengambil nama dan nomor WhatsApp penjual. Temuan terpenting: nama dan nomor penjual adalah data pribadi yang tidak boleh diambil (UU No. 27/2022, pembatasan tujuan), dan ToS pesaing melarang pengambilan otomatis. Keputusan yang direkomendasikan: memantau lewat API mitra berbayar atau izin tertulis, memakai ulasan dalam bentuk agregat, dan menjangkau penjual lewat jalur *opt-in*, karena risiko hukum dan reputasi scraping lebih mahal daripada biaya API.

## 2. Data yang Dipakai

Latihan ini berupa analisis tertulis dan tidak memakai dataset baru. Rujukan empiris diambil dari keluaran Bagian B modul: `robots.txt` situs tiruan (sel B.1), direktori dan penyaringan tautan (sel B.2), pengurai profil (sel B.3), `keluaran/etl_log_m07.csv` (log permintaan), dan `keluaran/halaman_gagal_m07.csv`.

## 3. Temuan dan Bukti

**Temuan 1 — perilaku Bagian B (sel B.1–B.3).**

- `robots.txt` melarang `/situs/pemilik/` dan menetapkan `Request-rate: 5/1`, sehingga jeda antarpermintaan 0,25 detik.
- Direktori memuat 354 tautan: 177 profil toko dan 177 tautan kontak pemilik yang dilarang. Log permintaan mencatat 0 permintaan ke `/situs/pemilik/`.
- Dari 177 profil yang diminta, 175 terurai dan 2 berstatus 404 (`T068`, `T140`), tercatat pada `halaman_gagal_m07.csv`.
- Halaman kontak pemilik memuat nama dan nomor WhatsApp, yaitu data pribadi.

**Temuan 2 — pengelompokan data menurut tiga sumber aturan.**

| Kategori | Data | Dasar |
|---|---|---|
| Boleh | Harga, stok, rating agregat lewat API mitra atau izin tertulis | Jalur yang disediakan pemilik data; hak pakai diatur lisensi |
| Boleh dengan syarat | Harga dan rating agregat pada halaman publik; jumlah ulasan | Bukan data pribadi, tetapi ToS melarang pengambilan otomatis sehingga perlu izin tertulis; patuhi robots.txt dan jeda |
| Boleh dengan syarat | Isi ulasan | Hanya agregat atau anonim; identitas pengulas tidak disimpan |
| Tidak boleh | Nama dan WhatsApp penjual | Data pribadi; UU No. 27/2022 mensyaratkan pembatasan tujuan dan dasar pemrosesan yang sah (Pasal 16 dan 20) |
| Tidak boleh | Halaman `Disallow`, di balik login, atau melewati pembatas laju | Mengabaikan sinyal eksplisit pemilik situs |

**Temuan 3 — alternatif rancangan.** API mitra berbayar untuk harga, rating, jumlah ulasan, dan stok dengan pola inkremental; ulasan dalam bentuk agregat; penjual dijangkau lewat formulir *opt-in*, kampanye di platform, atau kontak bisnis yang dipublikasikan penjual sendiri. Biayanya langganan atau tarif per panggilan serta waktu integrasi; besaran pastinya harus ditanyakan ke penyedia.

## 4. Keputusan

**Keputusan 1 — jalur pengambilan data.** Pemantauan lewat API mitra atau izin tertulis. Alternatif: scraping langsung, tidak dipilih karena ToS melarang pengambilan otomatis dan membuka risiko wanprestasi, pemblokiran IP, dan sanksi.

**Keputusan 2 — data kontak penjual tidak diambil.** Sejalan dengan K-07-005 pada `log-keputusan.csv` (halaman kontak pemilik dilarang robots.txt dan memuat data pribadi). Alternatif: mengambil kontak untuk tim sales, tidak dipilih karena melanggar pembatasan tujuan: penjual mencantumkan kontak agar dihubungi pembeli, bukan untuk pemasaran pesaing.

**Keputusan 3 — ulasan hanya agregat.** Alternatif: menyimpan teks ulasan beserta pengulas, tidak dipilih karena memuat identitas orang dan tidak diperlukan untuk memantau rating.

## 5. Rekonsiliasi Jumlah Baris

Latihan ini tidak menghasilkan tabel data. Rekonsiliasi di bawah berasal dari bukti perilaku Bagian B yang dijadikan rujukan.

| Langkah | Baris sebelum | Baris sesudah | Selisih | Penjelasan |
|---|---:|---:|---:|---|
| Tautan direktori disaring `RobotFileParser.can_fetch` | 354 | 177 | −177 | 177 tautan kontak pemilik dilarang robots.txt |
| Profil toko diminta menjadi profil terurai | 177 | 175 | −2 | 2 halaman 404 (`T068`, `T140`), dicatat pada `halaman_gagal_m07.csv` |
| Permintaan ke `/situs/pemilik/` pada log | 177 tautan | 0 | −177 | Tidak ada permintaan ke jalur terlarang |

## 6. Jawaban Pertanyaan Analisis

1. **Data apa yang boleh, tidak boleh, dan boleh dengan syarat?** Lihat tabel pada bagian 3 (Temuan 2); rincian pada `latihan-etika.md` bagian 1.
2. **Apa yang saya lakukan di Bagian B dan mengapa?** Membaca robots.txt lebih dulu, berjeda 0,25 detik, memakai `User-Agent` jujur, menyaring 177 tautan terlarang sebelum diminta, dan tidak mengumpulkan kontak pemilik, karena data itu tidak diperlukan untuk analisis toko (minimisasi data).
3. **Rancangan alternatif dan biayanya?** API mitra, ulasan agregat, dan jalur *opt-in* (bagian 3, Temuan 3). Biayanya lebih rendah daripada risiko hukum dan reputasi yang ditanggung bila scraping dilanjutkan.
4. **Daftar periksa kepatuhan sepuluh butir?** Tersedia pada `latihan-etika.md` bagian 4.

## 7. Keterbatasan

- Analisis hukum bersifat akademik dan bukan nasihat hukum; penerapan pasal pada kasus nyata memerlukan tinjauan ahli hukum.
- Biaya API mitra tidak diketahui sehingga hanya dibahas secara kualitatif.
- Bukti empiris berasal dari situs tiruan Lapak Sumatera, bukan lokapasar sungguhan; ToS dan robots.txt pesaing nyata perlu dibaca langsung.
- Status robots.txt sebagai dasar hukum tidak dibahas mendalam; ia diperlakukan sebagai sinyal kehendak pemilik situs.

## 8. Pengungkapan Penggunaan Alat Bantu

Asisten AI Claude (Anthropic) dipakai untuk menyusun draf analisis etika agar pembahasan lebih runtut dan rinci.  Sumber lain: keluaran Bagian B modul praktikum.
