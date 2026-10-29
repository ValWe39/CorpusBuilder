"""T020 — US-4 : corpus-split sur complement2 (réingestion sans rejet).

Scénario 4 du quickstart : sous-corpus suffixés à plats, sous-ensemble
dédié, réingération par `corpus` sans rejet, compteur consommé par
sous-corpus écrit.
"""

import json
import re
from pathlib import Path

import pytest

from corpusbuilder import cli, split

COMPLEMENT2 = Path(__file__).resolve().parents[2] / "Examples" / "Exemple-complement2"
PETIT = COMPLEMENT2 / "059650007.json"
TITRE = re.compile(r"^\d{9}(-[a-z0-9-]{1,10})?$")

requires_examples = pytest.mark.skipif(
    not COMPLEMENT2.is_dir(), reason="dossier Examples/ absent"
)


@requires_examples
def test_split_edit_suffixes_et_sans_edit(tmp_path, counter_file, capsys):
    out = tmp_path / "split"
    code = split.run_split(
        [str(PETIT)], "edit", out, counter_file=counter_file, random_part="11111"
    )
    assert code == 0

    jsons = sorted(out.glob("*.json"))
    npys = sorted(out.glob("*.npy"))
    # à plat, un couple par valeur (3 éditeurs nommés + sans editeur)
    assert len(jsons) == 4
    assert len(npys) == 4
    for p in jsons + npys:
        assert TITRE.match(p.stem), f"titre non conforme : {p.name}"
        assert "-" in p.stem  # suffixé, jamais préfixé (FR-025)

    stems = {p.stem for p in jsons}
    assert any(s.endswith("-la-tribune") for s in stems)  # slug tronqué à 10
    assert any(s.endswith("-sans-edit") for s in stems)  # FR-023

    # une occurrence consommée par sous-corpus écrit
    assert counter_file.read_text(encoding="utf-8").strip() == "0004"

    sortie = capsys.readouterr().out
    assert "Bilan : 4 sous-corpus écrits" in sortie


@requires_examples
def test_split_reingestion_sans_rejet(tmp_path, counter_file):
    out = tmp_path / "split"
    retour = tmp_path / "retour"
    split.run_split(
        [str(PETIT)], "edit", out, counter_file=counter_file, random_part="11111"
    )
    code = cli.run([out], retour, counter_file=counter_file, random_part="22222")
    assert code == 0  # SC-004 : réingéré sans rejet ni erreur
    rows = json.loads(next(retour.glob("*.json")).read_text(encoding="utf-8"))
    # aucune perte : 405 lignes d'origine toutes présentes
    assert len(rows) == 405


@requires_examples
def test_split_aut_multi_auteurs(tmp_path, counter_file):
    out = tmp_path / "split"
    code = split.run_split(
        [str(PETIT)], "aut", out, counter_file=counter_file, random_part="33333"
    )
    assert code == 0
    jsons = list(out.glob("*.json"))
    # 23 auteurs distincts + 9 sources sans auteur -> 24 sous-corpus
    assert len(jsons) == 24
    assert any(p.stem.endswith("-sans-aut") for p in jsons)
    total = 0
    for p in jsons:
        rows = json.loads(p.read_text(encoding="utf-8"))
        total += len(rows)
    # multi-auteurs : le total peut dépasser 405 (sources dupliquées, FR-024)
    assert total >= 405


@requires_examples
def test_split_aucun_corpus_valide(tmp_path, counter_file, capsys):
    complement1 = COMPLEMENT2.parent / "Exemple-complement1"
    if not complement1.is_dir():
        pytest.skip("Exemple-complement1 absent")
    code = cli.main_split(
        [str(complement1), "edit", "--output-folder", str(tmp_path / "out")]
    )
    assert code == 1
    assert "aucun corpus valide" in capsys.readouterr().err
