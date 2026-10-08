"""T023 — US 3 : réingestion de corpus et collage mixte (SC-006, FR-002)."""

import json
import shutil

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


@requires_examples
def test_reingestion_corpus_produits(tmp_path, counter_file):
    # deux exécutions produisent deux corpus au format de sortie
    cli.run(
        [EXAMPLES_1],
        tmp_path / "corpus_a",
        counter_file=counter_file,
        random_part="11111",
    )
    cli.run(
        [EXAMPLES_2],
        tmp_path / "corpus_b",
        counter_file=counter_file,
        random_part="22222",
    )
    rows_a, mat_a, _ = read_corpus(tmp_path / "corpus_a")
    rows_b, mat_b, _ = read_corpus(tmp_path / "corpus_b")

    # réingestion des deux corpus dans un dossier unique
    fusion_in = tmp_path / "fusion_in"
    fusion_in.mkdir()
    for source in ("corpus_a", "corpus_b"):
        for fichier in (tmp_path / source).iterdir():
            shutil.copy(fichier, fusion_in / fichier.name)

    code = cli.run(
        [fusion_in],
        tmp_path / "fusion_out",
        counter_file=counter_file,
        random_part="33333",
    )
    assert code == 0

    rows, matrix, _ = read_corpus(tmp_path / "fusion_out")
    # SC-006 : intégralité des chunks, sans perte ni duplication
    attendu = rows_a + rows_b  # tri alphabétique : 111... < 222...
    assert rows == attendu
    assert matrix.shape == (len(attendu), mat_a.shape[1])
    assert matrix.shape[0] == mat_a.shape[0] + mat_b.shape[0]


def test_collage_mixte_documents_et_corpus(tmp_path, counter_file, make_couple):
    # un couple document + un couple corpus (sortie d'une première passe)
    make_couple("A" * 18, n_chunks=2, dim=4)
    cli.run(
        [tmp_path / "in"],
        tmp_path / "premiere_sortie",
        counter_file=counter_file,
        random_part="99999",
    )
    rows_doc_attendus, _, _ = read_corpus(tmp_path / "premiere_sortie")

    # corpus réingéré copié dans le même dossier que le document B
    mixte = tmp_path / "mixte"
    mixte.mkdir()
    make_couple("B" * 18, n_chunks=3, dim=4, subfolder="mixte")
    for fichier in (tmp_path / "premiere_sortie").iterdir():
        shutil.copy(fichier, mixte / fichier.name)

    code = cli.run(
        [mixte],
        tmp_path / "mixte_out",
        counter_file=counter_file,
        random_part="88888",
    )
    assert code == 0
    rows, matrix, _ = read_corpus(tmp_path / "mixte_out")
    # FR-014 : tri alphabétique du radical — le corpus 999990001 est
    # collé avant le document B (9 chiffres < "B"), puis les 3 chunks de B
    assert len(rows) == 3 + len(rows_doc_attendus)
    assert matrix.shape[0] == len(rows)
    assert rows[len(rows_doc_attendus)]["text"] == "chunk 1 de " + "B" * 18


def test_corpus_non_reingere_si_desynchronise(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=2, dim=4)
    cli.run(
        [tmp_path / "in"],
        tmp_path / "sortie",
        counter_file=counter_file,
        random_part="11111",
    )
    # le corpus est désynchronisé : on retire une ligne du JSON
    corpus_in = tmp_path / "corpus_in"
    corpus_in.mkdir()
    for fichier in (tmp_path / "sortie").iterdir():
        shutil.copy(fichier, corpus_in / fichier.name)
    json_path = next(corpus_in.glob("*.json"))
    rows = json.loads(json_path.read_text(encoding="utf-8"))
    json_path.write_text(json.dumps(rows[:-1], ensure_ascii=False), encoding="utf-8")

    from corpusbuilder.models import CorpusError

    with pytest.raises(CorpusError, match="aucun couple valide"):
        cli.run([corpus_in], tmp_path / "out2", counter_file=counter_file)
