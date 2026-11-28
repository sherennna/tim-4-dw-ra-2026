"""Pengujian otomatis aturan validasi Gold & rekonsiliasi pada keluaran aktual pipeline."""

import unittest
import pandas as pd

from src.validasi import jalankan
from src.validasi.gold import validasi_gold_dan_rekonsiliasi


class TestValidasiGoldAktual(unittest.TestCase):
    def test_validasi_gold_dan_rekonsiliasi_aktual(self):
        silver = pd.read_parquet("data/silver/silver.parquet")
        panel = pd.read_parquet("data/gold/panel_provinsi.parquet")
        nasional = pd.read_parquet("data/gold/nasional.parquet")
        rekon = pd.read_csv("data/gold/rekonsiliasi_nasional.csv")

        hasil = jalankan(
            silver=silver,
            gold={"panel_provinsi": panel, "nasional": nasional, "rekonsiliasi": rekon},
        )

        self.assertEqual(hasil["aturan_validasi"], 9)
        self.assertEqual(hasil["aturan_lolos"], 9)
        self.assertEqual(hasil["aturan_gold_validasi"], 4)
        self.assertEqual(hasil["aturan_gold_lolos"], 4)
        self.assertEqual(hasil["status_rekonsiliasi"], "tervalidasi")
        self.assertTrue(all(hasil["rincian_aturan_gold"].values()))

    def test_validasi_menolak_duplikat_dan_kategori_kosong(self):
        silver = pd.read_parquet("data/silver/silver.parquet")
        panel = pd.read_parquet("data/gold/panel_provinsi.parquet")
        rekon = pd.read_csv("data/gold/rekonsiliasi_nasional.csv")

        panel_dup = pd.concat([panel, panel.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "G1"):
            validasi_gold_dan_rekonsiliasi(silver, {"panel_provinsi": panel_dup, "rekonsiliasi": rekon})

        rekon_rusak = rekon.copy()
        idx_pasangan = rekon_rusak[rekon_rusak["status_pasangan"] == "berpasangan"].index[0]
        rekon_rusak.loc[idx_pasangan, "kategori_penjelasan"] = ""
        with self.assertRaisesRegex(ValueError, "G4"):
            validasi_gold_dan_rekonsiliasi(silver, {"panel_provinsi": panel, "rekonsiliasi": rekon_rusak})


if __name__ == "__main__":
    unittest.main(verbosity=2)