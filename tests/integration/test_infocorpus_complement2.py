"""T016 — US-3 : info-corpus sur complement2 (effectifs mesurés).

Scénario 3 du quickstart : 3+1 éditeurs et 23 auteurs (dont entrées
vides dédiées) pour le corpus de 51 sources, 124 auteurs pour le grand,
buckets ≤ 6, consolidation sur l'union, aucun fichier écrit.
"""

from pathlib import Path

import pytest

from corpusbuilder import cli

COMPLEMENT2 = Path(__file__).resolve().parents[2] / "Examples" / "Exemple-complement2"
PETIT = COMPLEMENT2 / "059650007.json"
GRAND = COMPLEMENT2 / "143800006.json"

requires_examples = pytest.mark.skipif(
    not COMPLEMENT2.is_dir(), reason="dossier Examples/ absent"
)


@requires_examples
def test_edit_effectifs_mesures(tmp_path, capsys):
    code = cli.main_info([str(PETIT), "edit"])
    assert code == 0
    sortie = capsys.readouterr().out
    assert "Éditeurs (3 distincts, 1 sans editeur)" in sortie
    assert "sans editeur (1 sources)" in sortie
    assert "La Tribune (France) (23 sources)" in sortie


@requires_examples
def test_aut_effectifs_mesures(tmp_path, capsys):
    code = cli.main_info([str(GRAND), "aut"])
    assert code == 0
    sortie = capsys.readouterr().out
    assert "Auteurs (124 distincts, 14 sans auteur)" in sortie


@requires_examples
def test_date_buckets_max_six(tmp_path, capsys):
    code = cli.main_info([str(GRAND), "date"])
    assert code == 0
    sortie = capsys.readouterr().out
    lignes_bucket = [l for l in sortie.splitlines() if "tranche :" in l]
    assert 1 <= len(lignes_bucket) <= 6
    assert "sans date : 0 sources" in sortie  # toujours affiché (FR-018)


@requires_examples
def test_all_trois_sections_consolidees(tmp_path, capsys):
    code = cli.main_info([str(COMPLEMENT2)])
    assert code == 0
    sortie = capsys.readouterr().out
    assert "Auteurs (" in sortie
    assert "Éditeurs (" in sortie
    assert "Dates :" in sortie
    # consolidation sur l'union (FR-020)
    assert "Auteurs (1" in sortie  # >= 124


@requires_examples
def test_aucun_corpus_valide_code_1(tmp_path, capsys):
    complement1 = COMPLEMENT2.parent / "Exemple-complement1"
    if not complement1.is_dir():
        pytest.skip("Exemple-complement1 absent")
    code = cli.main_info([str(complement1)])
    assert code == 1
    erreurs = capsys.readouterr().err
    assert "couple document ignoré" in erreurs
    assert "aucun corpus valide" in erreurs
