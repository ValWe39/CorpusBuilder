"""Tests unitaires de dates.py (formats, buckets calendaires, fenetre)."""

from corpusbuilder.dates import (
    TRANCHES,
    build_buckets,
    choose_tranche,
    fenetre_courte,
    parse_date,
)


class TestParseDate:
    def test_jour_non_padde(self):
        assert parse_date("9 septembre 2026") == (2026, 9, 9)

    def test_jour_padde(self):
        assert parse_date("09 octobre 2026") == (2026, 10, 9)

    def test_sans_jour_premier_du_mois(self):
        assert parse_date("avril 2025") == (2025, 4, 1)

    def test_accents_mois(self):
        assert parse_date("1 décembre 1995") == (1995, 12, 1)
        assert parse_date("août 2020") == (2020, 8, 1)

    def test_formats_imprevus(self):
        assert parse_date("13 bidule 2026") is None
        assert parse_date("2026-09-10") is None
        assert parse_date("") is None
        assert parse_date(None) is None


class TestChooseTranche:
    def test_plage_1991_2026_donne_10_ans(self):
        dates = [(1991, 1, 1), (2026, 9, 10)]
        assert choose_tranche(dates) == 120  # 10 ans en mois

    def test_plage_12_ans_donne_5_ans(self):
        # 6 mois -> 62 b., 1 an -> 13, 2 ans -> 7, 5 ans -> 3 (<= 6)
        dates = [(1995, 3, 1), (2006, 6, 15)]
        assert choose_tranche(dates) == 60  # 5 ans

    def test_transches_croissantes(self):
        assert TRANCHES[0] == 6
        assert TRANCHES[-1] == 12000


class TestFenetreCourte:
    def test_fenetre_inferieure_6_mois(self):
        assert fenetre_courte([(2026, 3, 1), (2026, 6, 15)]) is True

    def test_fenetre_exacte_6_mois(self):
        assert fenetre_courte([(2026, 1, 1), (2026, 7, 1)]) is True

    def test_fenetre_longue(self):
        assert fenetre_courte([(2026, 1, 1), (2026, 8, 1)]) is False

    def test_date_unique(self):
        assert fenetre_courte([(2026, 5, 12)]) is True


class TestBuildBuckets:
    def test_plage_1991_2026_trois_buckets_occupes(self):
        dates = [(1991, 1, 1), (1995, 6, 1), (2005, 1, 1), (2026, 9, 10)]
        buckets = build_buckets(dates, 120)
        assert len(buckets) == 3
        assert buckets[0][0] == "1990..2000"
        assert buckets[0][1] == 2
        assert buckets[1][0] == "2000..2010"
        assert buckets[-1][0] == "2020..2030"
        assert sum(c for _, c in buckets) == len(dates)

    def test_borne_gauche_inclusive(self):
        # 2000-01-01 tombe sur la borne du bucket 2000..2010
        buckets = build_buckets([(2000, 1, 1)], 120)
        assert buckets[0][0] == "2000..2010"

    def test_semestres(self):
        buckets = build_buckets([(2026, 1, 1), (2026, 8, 1)], 6)
        assert [b[0] for b in buckets] == ["2026-01..2026-07", "2026-07..2027-01"]
        assert [c for _, c in buckets] == [1, 1]

    def test_labels_de_tranche(self):
        buckets = build_buckets([(1994, 1, 1), (1997, 1, 1)], 24)
        assert buckets[0][0] == "1994..1996"
        assert buckets[1][0] == "1996..1998"
