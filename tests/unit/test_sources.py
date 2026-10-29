"""Tests unitaires de sources.py (contexte canonique, precision, sources)."""

import numpy as np

from corpusbuilder.models import ChunkRow, Couple, CoupleKind
from corpusbuilder.sources import (
    build_sources,
    canon_context,
    context_precision,
    is_placeholder_title,
)

CTX_PLACEHOLDER = {
    "Typologie": "Article",
    "Auteur(s)": ["Jean-Victor Semeraro"],
    "Titre": "Nom de la source",
    "Editeur": "La Tribune",
    "Date": "9 septembre 2026",
    "Référence": "",
    "Citation": 'Jean-Victor Semeraro, "Nom de la source", La Tribune, '
    "9 septembre 2026",
}

CTX_WEB = {
    "Typologie": "Article",
    "Auteur(s)": ["Jean-Victor Semeraro"],
    "Titre": "Taxe sur les transactions financieres",
    "Editeur": "La Tribune (France)",
    "Date": "10 septembre 2026",
    "Référence": "news-20260910-TR-article_3832214",
    "Citation": "Citation complete",
}


def _couple_doc(rows, name="doc1", ctx=CTX_PLACEHOLDER):
    return Couple(
        kind=CoupleKind.DOCUMENT,
        json_path=_p(name + ".json"),
        npy_path=_p(name + "-0001.npy"),
        sort_key=name[:18],
        rows=[
            ChunkRow(
                text=r["text"],
                ref=r.get("ref", 1),
                path=r.get("path", "source.md"),
                title=r.get("title"),
                context=r.get("context", ctx),
                chunkingid=r.get("chunkingid", name),
            )
            for r in rows
        ],
        matrix=np.zeros((len(rows), 2)),
    )


def _p(nom):
    from pathlib import Path

    return Path("input") / nom


class TestCanonContext:
    def test_ordre_des_cles_indifferent(self):
        assert canon_context({"a": 1, "b": 2}) == canon_context({"b": 2, "a": 1})

    def test_context_absent(self):
        assert canon_context(None) is None

    def test_context_egal(self):
        assert canon_context(CTX_PLACEHOLDER) == canon_context(dict(CTX_PLACEHOLDER))


class TestPlaceholder:
    def test_nom_de_la_source(self):
        assert is_placeholder_title("Nom de la source") is True

    def test_nom_de_la_source_gras(self):
        assert is_placeholder_title("**Nom de la source**") is True

    def test_titre_reel(self):
        assert is_placeholder_title("Un vrai titre") is False

    def test_titre_vide(self):
        assert is_placeholder_title("") is False


class TestPrecision:
    def test_web_bat_placeholder(self):
        # cas d'ecole du Chunke : 7 champs dont reference + titre reel
        assert context_precision(CTX_WEB) > context_precision(CTX_PLACEHOLDER)

    def test_champ_supplementaire_compte(self):
        enrichi = dict(CTX_WEB, Extra="note")
        assert context_precision(enrichi) > context_precision(CTX_WEB)

    def test_context_absent_de_precision_minimale(self):
        assert context_precision(None) == (0, False, False, False)

    def test_reference_pesant_au_departage(self):
        sans_ref = {k: v for k, v in CTX_WEB.items() if k != "Référence"}
        avec_ref_vide = dict(sans_ref, Référence="")
        assert context_precision(CTX_WEB) > context_precision(avec_ref_vide)


class TestBuildSources:
    def test_document_une_source(self):
        couple = _couple_doc(
            [
                {"text": "alpha", "ref": 1},
                {"text": "beta", "ref": 2},
            ]
        )
        sources = build_sources([couple])
        assert len(sources) == 1
        assert sources[0].kind is CoupleKind.DOCUMENT
        assert sources[0].text == "alpha\nbeta"
        assert len(sources[0].refs) == 2

    def test_corpus_groupe_par_chunkingid(self):
        rows = [
            {"text": "un", "chunkingid": "A", "ref": 1, "path": "x"},
            {"text": "deux", "chunkingid": "B", "ref": 1, "path": "x"},
            {"text": "trois", "chunkingid": "A", "ref": 2, "path": "x"},
        ]
        couple = Couple(
            kind=CoupleKind.CORPUS,
            json_path=_p("123450001.json"),
            npy_path=_p("123450001.npy"),
            sort_key="123450001",
            rows=[
                ChunkRow(
                    text=r["text"],
                    ref=r["ref"],
                    path=r["path"],
                    chunkingid=r["chunkingid"],
                )
                for r in rows
            ],
            matrix=np.zeros((3, 2)),
        )
        sources = build_sources([couple])
        assert len(sources) == 2
        par_id = {s.key: s for s in sources}
        assert par_id["A"].text == "un\ntrois"
        assert len(par_id["A"].refs) == 2
        assert par_id["B"].text == "deux"

    def test_meme_chunkingid_deux_corpus_meme_source(self):
        def corpus(nom, cid):
            rows = [{"text": "texte " + nom, "chunkingid": cid, "ref": 1, "path": "x"}]
            return Couple(
                kind=CoupleKind.CORPUS,
                json_path=_p(nom + ".json"),
                npy_path=_p(nom + ".npy"),
                sort_key=nom,
                rows=[
                    ChunkRow(
                        text=r["text"],
                        ref=r["ref"],
                        path=r["path"],
                        chunkingid=r["chunkingid"],
                    )
                    for r in rows
                ],
                matrix=np.zeros((1, 2)),
            )

        sources = build_sources([corpus("111110001", "X"), corpus("222220001", "X")])
        assert len(sources) == 1
        assert len(sources[0].refs) == 2
        assert "X" in sources[0].display

    def test_ordre_preserve(self):
        c1 = _couple_doc([{"text": "a"}], name="aaa")
        c2 = _couple_doc([{"text": "b"}], name="bbb")
        sources = build_sources([c1, c2])
        assert [s.text for s in sources] == ["a", "b"]
        assert [s.order for s in sources] == [0, 1]
