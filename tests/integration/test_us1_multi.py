"""T008 — US1 : multi-dossiers (quickstart scénario 2, SC-005, SC-002)."""

import json
from pathlib import Path

import pytest

from corpusbuilder import cli
from tests.integration.conftest import (
    EXAMPLES_1,
    EXAMPLES_2,
    exemples_disponibles,
    read_corpus,
)

requires_examples = pytest.mark.skipif(
    not exemples_disponibles(), reason="dossier Examples/ absent"
)


def key_de_tri(p: Path) -> str:
    """Clé de tri alphabétique du radical de titre (FR-014)."""
    return p.stem[:18]


# `sorted` avec une fonction clé nommée (pas d'expression anonyme)
def _sorted_jsons(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.json"), key=key_de_tri)


@requires_examples
def test_corpus_multi_dossiers(tmp_path, counter_file):
    out = tmp_path / "out"
    code = cli.run(
        [EXAMPLES_1, EXAMPLES_2],
        out,
        counter_file=counter_file,
        random_part="99999",
    )
    assert code == 0

    rows, matrix, title = read_corpus(out)
    assert title == "999990001"

    sources = _sorted_jsons(EXAMPLES_1) + _sorted_jsons(EXAMPLES_2)
    total = sum(
        len(json.loads(p.read_text(encoding="utf-8"))["chunks"]) for p in sources
    )
    assert len(rows) == total
    assert matrix.shape[0] == total


@requires_examples
def test_ordre_de_collage_deterministe(tmp_path, counter_file):
    out = tmp_path / "out"
    cli.run(
        [EXAMPLES_1, EXAMPLES_2],
        out,
        counter_file=counter_file,
        random_part="99999",
    )
    rows, _, _ = read_corpus(out)

    # FR-012/FR-014 : dossiers dans l'ordre fourni, alphabétique au sein
    # du dossier, chunks d'un même document consécutifs dans l'ordre source.
    sources = _sorted_jsons(EXAMPLES_1) + _sorted_jsons(EXAMPLES_2)
    attendus: list[str] = []
    for path in sources:
        data = json.loads(path.read_text(encoding="utf-8"))
        attendus.extend(chunk["text"] for chunk in data["chunks"])
    obtenus = [row["text"] for row in rows]
    assert obtenus == attendus
