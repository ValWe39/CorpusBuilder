"""Tests unitaires de dedup.py (regles, transitivite, gagnant, rapport)."""

from corpusbuilder.dedup import SCORE_PLANCHER, detect, rapport
from corpusbuilder.models import CoupleKind
from corpusbuilder.sources import Source


def _source(key, context=None, text="", order=None, kind=CoupleKind.DOCUMENT):
    return Source(
        key=key,
        kind=kind,
        context=context,
        canon=None
        if context is None
        else __import__("json").dumps(context, sort_keys=True, ensure_ascii=False),
        precision=(
            len(context),
            bool(context.get("Référence", "")),
            False,
            False,
        )
        if isinstance(context, dict)
        else (0, False, False, False),
        text=text,
        order=order if order is not None else 0,
    )


CTX_A = {"Titre": "A", "Référence": ""}
CTX_B = {"Titre": "B", "Référence": "ref"}


class TestDetectionContexte:
    def test_contexte_identique_fusionne(self):
        s1 = _source("s1", CTX_A, "texte un", 0)
        s2 = _source("s2", CTX_A, "texte deux", 1)
        resultat = detect([s1, s2], seuil=75)
        assert len(resultat.groups) == 1
        assert resultat.excluded_keys == {"s2"}

    def test_contexte_absent_jamais_fusionne_par_contexte(self):
        s1 = _source("s1", None, "texte un", 0)
        s2 = _source("s2", None, "texte deux", 1)
        resultat = detect([s1, s2], seuil=100)
        assert len(resultat.groups) == 0

    def test_contexte_absent_fusionne_par_seuil(self):
        mots = [f"mot{i}" for i in range(25)]
        s1 = _source("s1", None, " ".join(mots), 0)
        s2 = _source("s2", None, " ".join(mots[:-1] + ["change"]), 1)
        resultat = detect([s1, s2], seuil=60)
        assert len(resultat.groups) == 1


class TestDetectionSimilarite:
    def test_seuil_atteint_fusionne(self):
        texte = "un deux trois quatre cinq six sept"
        s1 = _source("s1", CTX_A, texte, 0)
        s2 = _source("s2", CTX_B, texte + " huit", 1)
        resultat = detect([s1, s2], seuil=60)
        assert len(resultat.groups) == 1

    def test_paire_proche_non_fusionnee_listee(self):
        mots = [f"mot{i}" for i in range(25)]
        s1 = _source("s1", CTX_A, " ".join(mots), 0)
        s2 = _source("s2", CTX_B, " ".join(mots[:12] + ["change"] + mots[13:]), 1)
        resultat = detect([s1, s2], seuil=90)
        assert len(resultat.groups) == 0
        assert len(resultat.near_pairs) == 1
        assert resultat.near_pairs[0][2] >= SCORE_PLANCHER

    def test_texte_vide_jamais_similaire(self):
        s1 = _source("s1", CTX_A, "", 0)
        s2 = _source("s2", CTX_B, "", 1)
        resultat = detect([s1, s2], seuil=60)
        assert len(resultat.groups) == 0


class TestTransitivite:
    def test_chaine_contexte_plus_similarite_un_seul_groupe(self):
        # s1-s2 relies par contexte identique, s2-s_trois par similarite.
        mots = [f"mot{i}" for i in range(25)]
        texte = " ".join(mots)
        s1 = _source("s1", CTX_A, "texte totalement different ici", 0)
        s2 = _source("s2", CTX_A, texte, 1)
        s_trois = _source("s_trois", CTX_B, " ".join(mots[:-1] + ["change"]), 2)
        resultat = detect([s1, s2, s_trois], seuil=60)
        assert len(resultat.groups) == 1
        assert len(resultat.groups[0].excluded) == 2


class TestGagnant:
    def test_contexte_plus_precis_gagne(self):
        texte = " ".join(f"mot{i}" for i in range(25))
        s1 = _source("s1", CTX_A, texte, 0)
        s2 = _source("s2", CTX_B, texte, 1)
        resultat = detect([s1, s2], seuil=60)
        assert len(resultat.groups) == 1
        assert resultat.groups[0].winner.key == "s2"

    def test_egalite_premier_apparu_gagne(self):
        s1 = _source("s1", CTX_A, "texte identique", 0)
        s2 = _source("s2", dict(CTX_A), "texte identique", 1)
        resultat = detect([s1, s2], seuil=100)
        assert resultat.groups[0].winner.key == "s1"


class TestRapport:
    def test_sections_et_bilan(self):
        s1 = _source("s1", CTX_A, "texte un deux trois quatre cinq", 0)
        s2 = _source("s2", CTX_A, "texte un deux trois quatre six", 1)
        s_trois = _source("s_trois", CTX_B, "a b c d e f g h", 2)
        s4 = _source("s4", {"Titre": "D"}, "a b c d e f g z", 3)
        resultat = detect([s1, s2, s_trois, s4], seuil=90)
        lignes = rapport(resultat, seuil=90)
        texte = "\n".join(lignes)
        assert "Doublons exclus — groupe 1" in texte
        assert "Paires proches non fusionnées" in texte
        assert "Bilan : 4 sources analysées" in texte

    def test_aucun_doublon_explicite(self):
        s1 = _source("s1", CTX_A, "texte un", 0)
        resultat = detect([s1], seuil=75)
        lignes = rapport(resultat, seuil=75)
        assert "Aucun doublon détecté." in lignes
