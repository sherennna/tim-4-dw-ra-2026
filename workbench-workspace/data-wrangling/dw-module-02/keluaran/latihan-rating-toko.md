ZANNUBA ARIFAH ILMAN
124450112
RA

LATIHAN 2.2
produk = pd.read_csv(RAW / "produk.csv", dtype=str, keep_default_na=False)
# TODO: jumlah 0,0; nilai positif terkecil; rata-rata dengan/tanpa 0,0
# TODO: uji_chi2 terhadap kategori (dibakukan sementara) dan provinsi_toko
# TODO: apakah rating toko konsisten di dalam satu id_toko?
# TODO: catat_keputusan([{"id": "K-02-0..", ...}])  # sumber_kolom "produk.rating_toko"

produk = pd.read_csv(RAW / "produk.csv", dtype=str, keep_default_na=False)
produk["rating_num"] = pd.to_numeric(produk.rating_toko, errors="coerce")

# TODO: jumlah 0,0; nilai positif terkecil; rata-rata dengan/tanpa 0,0
#input
nol = produk.rating_num.eq(0)
positif = produk.rating_num[produk.rating_num > 0]
print("jumlah 0,0:", nol.sum(), f"({nol.sum() / produk.rating_num.notna().sum():.2%} dari yang terisi)")
print("positif terkecil:", positif.min(), "| 10 terkecil:", positif.sort_values().head(10).tolist())
print("maksimum:", produk.rating_num.max())
print("rata-rata DENGAN 0,0 :", round(produk.rating_num.mean(), 3))
print("rata-rata TANPA 0,0  :", round(positif.mean(), 3))
print(produk.rating_num.round(1).value_counts().sort_index().head(12))
#output
jumlah 0,0: 61 (7.18% dari yang terisi)
positif terkecil: 3.2 | 10 terkecil: [3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2]
maksimum: 5.0
rata-rata DENGAN 0,0 : 3.819
rata-rata TANPA 0,0  : 4.114
rating_num
0.0    61
3.2    21
3.3    44
3.4    38
3.5    36
3.6    51
3.7    38
3.8    40
3.9    52
4.0    50
4.1    44
4.2    47
Name: count, dtype: int64

# TODO: uji_chi2 terhadap kategori (dibakukan sementara) dan provinsi_toko
#input
produk["kategori_uji"] = produk.kategori.str.strip().str.lower()
produk["provinsi_uji"] = produk.provinsi_toko.str.strip().str.lower()
produk["rating_nol"] = nol.where(produk.rating_num.notna())   # baris kosong dikeluarkan
 
def chi2_nol(kol):
    d = produk.dropna(subset=["rating_nol"])
    tab = pd.crosstab(d[kol], d.rating_nol.astype(bool))
    chi2, p, dof, _ = stats.chi2_contingency(tab)
    n = tab.to_numpy().sum()
    v = np.sqrt(chi2 / (n * (min(tab.shape) - 1)))            # Cramer's V (kekuatan hubungan)
    print(f"\n{kol}: chi2={chi2:.2f}, dof={dof}, p={p:.4g}, Cramer's V={v:.3f}")
    persen = (tab[True] / tab.sum(axis=1)).sort_values(ascending=False)
    print("persentase 0,0 per kelompok (tertinggi):")
    print(persen.head(8).round(3))
    return p, v
 
p_kat, v_kat = chi2_nol("kategori_uji")
p_prov, v_prov = chi2_nol("provinsi_uji")
#output
kategori_uji: chi2=6.33, dof=6, p=0.3876, Cramer's V=0.086
persentase 0,0 per kelompok (tertinggi):
kategori_uji
kain tenun              0.133
olahan ikan             0.095
kerajinan               0.079
sayur dan buah segar    0.075
makanan ringan          0.057
kopi                    0.056
rempah                  0.053
dtype: float64

provinsi_uji: chi2=3.89, dof=9, p=0.9188, Cramer's V=0.068
persentase 0,0 per kelompok (tertinggi):
provinsi_uji
kepulauan riau      0.107
aceh                0.091
sumatera barat      0.088
bengkulu            0.071
sumatera selatan    0.067
riau                0.063
lampung             0.062
jambi               0.058
dtype: float64


# TODO: apakah rating toko konsisten di dalam satu id_toko?
#input
per_toko = produk.groupby("id_toko").rating_num
ringkas = pd.DataFrame({
    "n_produk": per_toko.size(),
    "n_rating_berbeda": per_toko.nunique(),
    "ada_nol": per_toko.apply(lambda x: x.eq(0).any()),
    "ada_positif": per_toko.apply(lambda x: (x > 0).any()),
})
print("\ntoko:", len(ringkas))
print("toko dengan >1 nilai rating berbeda:", (ringkas.n_rating_berbeda > 1).sum())
print("toko campuran (ada 0,0 DAN positif):", (ringkas.ada_nol & ringkas.ada_positif).sum())
print("toko yang SEMUA produknya 0,0:", (ringkas.ada_nol & ~ringkas.ada_positif).sum())
print(ringkas[ringkas.n_rating_berbeda > 1].head(10))
 
#output
toko: 177
toko dengan >1 nilai rating berbeda: 168
toko campuran (ada 0,0 DAN positif): 49
toko yang SEMUA produknya 0,0: 1
         n_produk  n_rating_berbeda  ada_nol  ada_positif
id_toko                                                  
T001            3                 3    False         True
T002            5                 5     True         True
T003            4                 4    False         True
T004            4                 4    False         True
T005            4                 4     True         True
T006            4                 4    False         True
T007            7                 7     True         True
T008            3                 3    False         True
T009            5                 4    False         True
T010            2                 2    False         True

# TODO: catat_keputusan([{"id": "K-02-0..", ...}])  # sumber_kolom "produk.rating_toko"
#input
catat_keputusan([{
    "id": "K-02-0X",   
    "sumber_kolom": "produk.rating_toko",
    "keputusan": "Perlakukan rating_toko = 0,0 sebagai penanda (tidak ada rating), ubah menjadi NaN. Tidak diisi dari rating produk lain di toko yang sama.",
    "bukti": "0,0 sebanyak ... baris; positif terkecil = ...; rata-rata dengan 0,0 = ..., tanpa 0,0 = ...; chi2 kategori p = ..., provinsi p = ...; dalam satu id_toko, ... toko konsisten.",
}])
#output
id	modul	sumber_kolom	temuan	bukti	tindakan	alasan	baris_terdampak	id_anomali
0	K-02-001	2	transaksi.ongkir	ongkir tidak dapat dipakai sebagai angka: sel ...	kosong 1075, token '-' 36 (seluruhnya Pos Indo...	kedua bentuk diubah menjadi NaN; asal-usulnya ...	token '-' membuat kolom terbaca teks; keduanya...	1111	A-01;A-02
1	K-02-002	2	transaksi.ongkir	ongkir hilang MAR: 90,7% pada kanal app 1 Sep-...	uji sembunyi 10% (2317 baris): deduktif MAE Rp...	ongkir = total_bayar - jumlah*harga_satuan*(1-...	nilai dapat diturunkan dari identitas akuntans...	1049	A-01
2	K-02-003	2	transaksi.ongkir	sisa ongkir hilang yang identitasnya tidak dap...	62 baris gagal prasyarat (jumlah<1, diskon pec...	diisi median ongkir teramati per provinsi_tuju...	ongkir ditentukan jarak tujuan; median tahan t...	62	A-01
3	K-02-004	2	transaksi.lama_kirim_hari	angka penanda 999 dan -1 pada lama kirim	127 baris (0,60% baris berlaku); chi2 terhadap...	penanda menjadi NaN, lama_kirim_hari_status=pe...	konsisten dengan MCAR dan kecil, sehingga anal...	127	A-04
4	K-02-005	2	transaksi.lama_kirim_hari;transaksi.rating_ulasan	kekosongan struktural: lama kirim dan rating t...	lama kirim kosong 3239 baris, seluruhnya dibat...	tetap NaN dengan <kolom>_status=tidak_berlaku;...	nilai memang tidak ada, bukan tidak tercatat; ...	0	-
5	K-02-006	2	transaksi.rating_ulasan	kanal app menulis 0 untuk rating yang tidak diisi	2805 rating 0, seluruhnya app; laju hilang app...	0 menjadi NaN, rating_ulasan_status=penanda	skala 1-5; setelah diungkap laju kehilangan ke...	2805	A-03
6	K-02-007	2	transaksi.rating_ulasan	rating tidak diisi diduga MNAR	6085 baris (30,32% pesanan selesai); laju hila...	tidak diimputasi; laporan kepuasan disertai an...	median/mean mengasumsikan MCAR dan menambah ra...	0	A-03
7	K-02-008	2	transaksi.id_pelanggan	id_pelanggan kosong pada pembelian tamu kanal web	418 baris, seluruhnya web; diizinkan kamus data	string kosong menjadi NA, ditambah kolom pembe...	konstanta 'TAMU' menciptakan satu pelanggan fi...	418	-
0	K-02-0X	NaN	produk.rating_toko	NaN	0,0 sebanyak ... baris; positif terkecil = ......	NaN	NaN	NaN	Na