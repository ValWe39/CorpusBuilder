"""T014 — US2 : tests unitaires des contrôles (FR-006 à FR-010)."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from corpusbuilder import transform, validation
from corpusbuilder.models import (
    CorpusError,
    Couple,
    CoupleKind,
    CoupleRejected,
)


def _candidate(
    kind: CoupleKind = CoupleKind.DOCUMENT,
    json_name: str = "ABCDEFGHIJKLMNOPQR.json",
    npy_name: str = "ABCDEFGHIJKLMNOPQR-0001.npy",
    matrix=None,
):
    return SimpleNamespace(
        kind=kind,
        json_path=Path(json_name),
        npy_path=Path(npy_name),
        matrix=np.zeros((3, 4)) if matrix is None else matrix,
    )


def _couple(name: str, shape: tuple, dtype=np.float64):
    return Couple(
        kind=CoupleKind.DOCUMENT,
        json_path=Path(f"{name}.json"),
        npy_path=Path(f"{name}-0001.npy"),
        sort_key=name,
        rows=[],
        matrix=np.zeros(shape, dtype=dtype),
    )


class TestCheckCouple:
    def test_desynchronisation_rejetee(self):
        candidat = _candidate(matrix=np.zeros((9, 4)))
        rows = ["x"] * 10
        with pytest.raises(CoupleRejected, match="désynchronisation"):
            validation.check_couple(candidat, rows)

    def test_alignement_accepte(self):
        candidat = _candidate()
        validation.check_couple(candidat, ["x"] * 3)

    def test_matrice_1d_rejetee(self):
        candidat = _candidate(matrix=np.zeros(12))
        with pytest.raises(CoupleRejected, match="non conforme"):
            validation.check_couple(candidat, ["x"] * 12)

    def test_titres_document_divergents(self):
        candidat = _candidate(
            npy_name="ABCDEFGHJKLMNPQRS-0001.npy", matrix=np.zeros((3, 4))
        )
        with pytest.raises(CoupleRejected, match="18 premiers caractères"):
            validation.check_couple(candidat, ["x"] * 3)

    def test_titres_corpus_divergents(self):
        candidat = _candidate(
            kind=CoupleKind.CORPUS,
            json_name="123450001.json",
            npy_name="123450002.npy",
            matrix=np.zeros((3, 4)),
        )
        with pytest.raises(CoupleRejected, match="9 chiffres"):
            validation.check_couple(candidat, ["x"] * 3)


class TestDimensions:
    def test_dimensions_incompatibles_bloquantes(self):
        couples = [_couple("A" * 18, (3, 4)), _couple("B" * 18, (2, 8))]
        with pytest.raises(CorpusError, match="incompatibles"):
            validation.check_dimensions(couples)

    def test_dimensions_identiques_acceptees(self):
        couples = [_couple("A" * 18, (3, 4)), _couple("B" * 18, (2, 4))]
        validation.check_dimensions(couples)


class TestDtypes:
    def test_dtypes_heterogenes_avertissent(self, capsys):
        couples = [
            _couple("A" * 18, (3, 4), np.float32),
            _couple("B" * 18, (2, 4), np.float64),
        ]
        heterogene = validation.check_dtypes(couples)
        assert heterogene is True
        stderr = capsys.readouterr().err
        assert "hétérogènes" in stderr

    def test_dtypes_homogenes_silencieux(self, capsys):
        couples = [_couple("A" * 18, (3, 4)), _couple("B" * 18, (2, 4))]
        assert validation.check_dtypes(couples) is False
        assert capsys.readouterr().err == ""


class TestTransform:
    def test_document_rows_omet_cles_nulles(self):
        data = {
            "schema_version": "1.0",
            "document": {"path": "doc.md"},
            "chunks": [{"ref": 1, "text": "contenu"}],
        }
        rows = transform.document_rows(data)
        assert rows[0].to_dict() == {"text": "contenu", "ref": 1, "path": "doc.md"}

    def test_document_rows_ref_conservee(self):
        data = {
            "schema_version": "1.0",
            "document": {"path": "doc.md", "title": "Titre"},
            "chunks": [
                {"ref": 7, "text": "a", "part": "P"},
                {"ref": 9, "text": "b", "page": 3},
            ],
        }
        rows = transform.document_rows(data)
        assert [r.ref for r in rows] == [7, 9]
        assert rows[1].to_dict()["page"] == 3
        assert "part" not in rows[1].to_dict()

    def test_document_sans_path_rejete(self):
        data = {
            "schema_version": "1.0",
            "document": {},
            "chunks": [{"ref": 1, "text": "a"}],
        }
        with pytest.raises(CoupleRejected, match="path"):
            transform.document_rows(data)

    def test_chunk_incomplet_rejete(self):
        data = {
            "schema_version": "1.0",
            "document": {"path": "doc.md"},
            "chunks": [{"ref": 1}],
        }
        with pytest.raises(CoupleRejected, match="ref.*text|text"):
            transform.document_rows(data)

    def test_corpus_rows_preserve_ordre(self):
        data = [
            {"text": "a", "ref": 1, "path": "p1", "title": "T"},
            {"text": "b", "ref": 2, "path": "p1", "context": "C"},
        ]
        rows = transform.corpus_rows(data)
        assert [r.text for r in rows] == ["a", "b"]
        assert rows[0].to_dict()["title"] == "T"

    def test_corpus_ligne_incomplete_rejetee(self):
        with pytest.raises(CoupleRejected, match="incomplète"):
            transform.corpus_rows([{"text": "a", "ref": 1}])
