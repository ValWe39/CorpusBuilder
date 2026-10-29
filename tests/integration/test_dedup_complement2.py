"""T014 — US-2 : déduplication des entrées corpus (complement2).

Scénario 2 du quickstart : exclusion conjointe des lignes JSON et des
vecteurs, doublon inter-corpus capturé, corpus d'entrée inchangés.
"""

import json
from pathlib import Path

import numpy as np
import pytest

from corpusbuilder import cli
from tests.integration.conftest import exemples_disponibles

COMPLEMENT2 = Path(__file__).resolve().parents[2] / "Examples" / "Exemple-complement2"
CROSS_A = "000003652121260301"  # source de 059650007.json
CROSS_B = "000000142121260142"  # source de 143800006.json

requires_examples = pytest.mark.skipif(
    not exemples_disponibles() or not COMPLEMENT2.is_dir(),
    reason="dossier Examples/ absent",
)


def _empreinte(dossier):
    return sorted(
        (p.name, p.stat().st_size, p.read_bytes()[:64])
        for p in sorted(dossier.iterdir())
    )


@requires_examples
def test_dedup_corpus_exclut_et_aligne(tmp_path, counter_file, capsys):
    avant = _empreinte(COMPLEMENT2)
    out = tmp_path / "out"
    code = cli.run(
        [COMPLEMENT2],
        out,
        counter_file=counter_file,
        random_part="54321",
        suppr_doublons=True,
        seuil_doublons=75,
    )
    assert code == 0
    assert _empreinte(COMPLEMENT2) == avant  # corpus d'entrée inchangés

    json_out = next(out.glob("*.json"))
    rows = json.loads(json_out.read_text(encoding="utf-8"))
    matrix = np.load(json_out.with_suffix(".npy"))

    # FR-011 : alignement ligne à ligne après exclusion
    assert len(rows) == matrix.shape[0]

    ids = {r["chunkingid"] for r in rows}
    assert len(ids) < 51 + 232  # des sources ont été exclues

    # Doublon inter-corpus mesuré : exactement une des deux sources survit
    assert CROSS_A in ids or CROSS_B in ids
    assert not (CROSS_A in ids and CROSS_B in ids)

    rapport = capsys.readouterr().out
    assert "Doublons exclus — groupe 1" in rapport
    assert "::" in rapport  # sources corpus identifiées fichier::chunkingid


@requires_examples
def test_dedup_corpus_aucun_doublon_sortie_identique(tmp_path, counter_file, capsys):
    """Sans doublon (seuil 100 sur corpus sans contexte identique), la
    sortie reste complète et le rapport l'indique."""
    out = tmp_path / "out"
    code = cli.run(
        [COMPLEMENT2],
        out,
        counter_file=counter_file,
        random_part="54321",
        suppr_doublons=True,
        seuil_doublons=100,
    )
    assert code == 0
    rapport = capsys.readouterr().out
    rows = json.loads(next(out.glob("*.json")).read_text(encoding="utf-8"))
    assert len(rows) > 0
    assert "Bilan :" in rapport
