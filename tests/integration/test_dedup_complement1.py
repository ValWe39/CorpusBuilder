"""T009 — US-1 : déduplication sur complement1 (vérité terrain research).

Scénario 1 du quickstart : entrées jamais modifiées, 30 groupes à
contexte identique à seuil 100, section « Paires proches » au défaut 75,
comportement inchangé sans l'option (FR-001).
"""

import json
from pathlib import Path

import pytest

from corpusbuilder import cli
from tests.integration.conftest import exemples_disponibles

COMPLEMENT1 = Path(__file__).resolve().parents[2] / "Examples" / "Exemple-complement1"

requires_examples = pytest.mark.skipif(
    not exemples_disponibles() or not COMPLEMENT1.is_dir(),
    reason="dossier Examples/ absent",
)


def _empreinte(dossier):
    """Empreinte déterministe des fichiers d'entrée (FR-008)."""
    return sorted(
        (p.name, p.stat().st_size, p.read_bytes()[:64])
        for p in sorted(dossier.iterdir())
    )


@requires_examples
def test_suppr_doublons_exclut_sans_altérer(tmp_path, counter_file, capsys):
    avant = _empreinte(COMPLEMENT1)
    out = tmp_path / "out"
    code = cli.run(
        [COMPLEMENT1],
        out,
        counter_file=counter_file,
        random_part="12345",
        suppr_doublons=True,
        seuil_doublons=75,
    )
    assert code == 0
    assert _empreinte(COMPLEMENT1) == avant  # FR-008 : entrées inchangées

    rows = json.loads(next(out.glob("*.json")).read_text(encoding="utf-8"))
    nb_entrant = len(list(COMPLEMENT1.glob("*.json")))
    nb_sortie = len({r["chunkingid"] for r in rows})
    # 232 sources en entrée, strictement moins en sortie (SC-001)
    assert nb_sortie < nb_entrant
    assert nb_sortie == 232 - 56  # mesure : 42 groupes, 56 exclusions

    rapport = capsys.readouterr().out
    assert "Doublons exclus — groupe 1" in rapport
    assert "Paires proches non fusionnées" in rapport
    assert "Bilan : 232 sources analysées" in rapport


@requires_examples
def test_seuil_100_verite_terrain_contexte(tmp_path, counter_file, capsys):
    out = tmp_path / "out"
    code = cli.run(
        [COMPLEMENT1],
        out,
        counter_file=counter_file,
        random_part="12345",
        suppr_doublons=True,
        seuil_doublons=100,
    )
    assert code == 0
    rapport = capsys.readouterr().out
    # Les 30 groupes à contexte strictement identique mesurés en
    # recherche sont tous détectés (35 groupes au total à seuil 100,
    # textes parfaitement identiques inclus — 42 exclusions, 190
    # sources conservées).
    assert rapport.count("(règle : contexte identique)") == 30
    rows = json.loads(next(out.glob("*.json")).read_text(encoding="utf-8"))
    nb_sortie = len({r["chunkingid"] for r in rows})
    assert nb_sortie == 190


@requires_examples
def test_sans_option_comportement_inchange(tmp_path, counter_file, capsys):
    out = tmp_path / "out"
    code = cli.run(
        [COMPLEMENT1],
        out,
        counter_file=counter_file,
        random_part="12345",
    )
    assert code == 0
    assert "Doublons exclus" not in capsys.readouterr().out
    rows = json.loads(next(out.glob("*.json")).read_text(encoding="utf-8"))
    nb_sortie = len({r["chunkingid"] for r in rows})
    assert nb_sortie == 232  # aucune exclusion sans l'option (FR-001)
