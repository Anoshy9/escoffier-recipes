import unittest

from estimateur import Comparable, EstimationMarche, estimer_marche, quantile_pondere, recommander


def marche(loyer):
    return EstimationMarche(loyer, loyer * 0.9, loyer * 1.1, 5, loyer)


class TestEstimateur(unittest.TestCase):
    def test_quantile_pondere_symetrique(self):
        self.assertEqual(quantile_pondere([1000, 2000, 3000], [1, 1, 1], 0.5), 2000)

    def test_proximite_tire_la_mediane(self):
        comps = [
            Comparable("proche", "1ch", 2000, 0.0, "", ""),
            Comparable("loin", "1ch", 1500, 2.0, "", ""),
        ]
        self.assertGreater(estimer_marche(comps, "1ch", 0).loyer_marche, 1750)

    def test_sous_le_marche_vise_marche_moins_marge(self):
        r = recommander(1650, marche(1850), cpi=0.03, hausse_locale=0.04, marge_fidelisation=0.03)
        self.assertEqual(r.loyer_recommande, 1795)

    def test_plancher_inflation(self):
        r = recommander(1800, marche(1850), cpi=0.03, hausse_locale=0.04, marge_fidelisation=0.03)
        self.assertEqual(r.loyer_recommande, 1850)  # CPI = 1854, plafonné au marché

    def test_pas_de_hausse_au_dessus_du_marche(self):
        r = recommander(1900, marche(1850), cpi=0.03, hausse_locale=0.04, marge_fidelisation=0.03)
        self.assertEqual(r.hausse_pcm, 0)


if __name__ == "__main__":
    unittest.main()
