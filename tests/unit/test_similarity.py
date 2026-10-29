"""Tests unitaires de similarity.py (shingles, Jaccard tronqué, union-find)."""

from corpusbuilder.similarity import (
    UnionFind,
    score,
    shingles,
    tokens,
)


class TestTokens:
    def test_minuscules_et_ponctuation(self):
        assert tokens("Hello, World!") == ["hello", "world"]

    def test_accents_preserves(self):
        assert tokens("Été à Paris") == ["été", "à", "paris"]

    def test_texte_vide(self):
        assert tokens("") == []


class TestShingles:
    def test_nombre_de_shingles(self):
        # 7 tokens -> 3 shingles de 5 mots
        assert len(shingles("a b c d e f g")) == 3

    def test_texte_court_sans_shingle(self):
        assert shingles("a b c") == set()

    def test_insensible_a_la_casse(self):
        assert shingles("A B C D E") == shingles("a b c d e")


class TestScore:
    def test_identiques(self):
        a = shingles("un deux trois quatre cinq six")
        assert score(a, a) == 100

    def test_disjoints(self):
        assert score({(1,)}, {(2,)}) == 0

    def test_troncature_entiere(self):
        # 74 communs, 99 au total -> 74,74... tronque a 74 (decision D1)
        a = set(range(74))
        b = set(range(99))
        assert score(a, b) == 74

    def test_ensembles_vides(self):
        assert score(set(), set()) == 0
        assert score(shingles("a b c d e"), set()) == 0

    def test_pas_de_faux_positif_sur_texte_vide(self):
        assert score(shingles("court"), set()) == 0


class TestUnionFind:
    def test_composantes_transitives(self):
        uf = UnionFind(4)
        uf.union(0, 1)
        uf.union(1, 2)
        comps = uf.components()
        assert len(comps) == 2
        membres = sorted(sorted(c) for c in comps)
        assert membres[0] == [0, 1, 2]
        assert membres[1] == [3]

    def test_isole_reste_seul(self):
        uf = UnionFind(2)
        comps = uf.components()
        assert comps == [[0], [1]]

    def test_reunion_idempotente(self):
        uf = UnionFind(3)
        uf.union(0, 1)
        uf.union(1, 0)
        assert len(uf.components()) == 2
