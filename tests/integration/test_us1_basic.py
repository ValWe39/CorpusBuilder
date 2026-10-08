"""T007 — US1 : concaténation basique (quickstart scénario 1, SC-001)."""

import pytest

from corpusbuilder import cli
from tests.integration.conftest import (
    EXAMPLES_1,
    exemples_disponibles,
    read_corpus,
)

requires_examples = pytest.mark.skipif(
    not exemples_disponibles(), reason="dossier Examples/ absent"
)


@requires_examples
def test_corpus_basique(tmp_path, counter_file):
    out = tmp_path / "out"
    code = cli.run([EXAMPLES_1], out, counter_file=counter_file, random_part="12345")
    assert code == 0

    rows, matrix, title = read_corpus(out)
    assert title == "123450001"
    assert matrix.shape[0] == len(rows)
    assert counter_file.read_text(encoding="utf-8").strip() == "0001"


@requires_examples
def test_lignes_autoporteuses(tmp_path, counter_file):
    out = tmp_path / "out"
    cli.run([EXAMPLES_1], out, counter_file=counter_file)

    rows, _, _ = read_corpus(out)
    assert len(rows) > 0
    for row in rows:
        # FR-011 : champs obligatoires sur chaque ligne
        assert {"text", "ref", "path"} <= set(row)
        # FR-011 : clés nulles omises
        assert row.get("page") is None or isinstance(row["page"], int)
