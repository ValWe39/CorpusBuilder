"""T019 — US4 : tests unitaires du compteur (FR-018 à FR-021)."""

import pytest

from corpusbuilder import counter
from corpusbuilder.models import CorpusError


def test_fichier_absent_repart_a_zero(tmp_path):
    assert counter.read_last_used(tmp_path / "counter.txt") == 0


def test_lecture_numero_valide(tmp_path):
    chemin = tmp_path / "counter.txt"
    chemin.write_text("0007\n", encoding="utf-8")
    assert counter.read_last_used(chemin) == 7


@pytest.mark.parametrize("corrompu", ["abc", "12", "12345", "", "00 7", "12x4"])
def test_fichier_corrompu_echec_rapide(tmp_path, corrompu):
    chemin = tmp_path / "counter.txt"
    chemin.write_text(corrompu, encoding="utf-8")
    with pytest.raises(CorpusError, match="corrompu"):
        counter.read_last_used(chemin)


def test_cycle_occurrence():
    # FR-020 : premier usage 0001, +1 par document, 9999 -> 0000
    assert counter.next_occurrence(0) == 1
    assert counter.next_occurrence(7) == 8
    assert counter.next_occurrence(9998) == 9999
    assert counter.next_occurrence(9999) == 0


def test_persistance_format_quatre_chiffres(tmp_path):
    chemin = tmp_path / "counter.txt"
    counter.persist(chemin, 8)
    assert chemin.read_text(encoding="utf-8").strip() == "0008"
    counter.persist(chemin, 0)
    assert chemin.read_text(encoding="utf-8").strip() == "0000"
