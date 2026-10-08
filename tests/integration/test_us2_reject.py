"""T018 — US2 : rejets en intégration (quickstart scénario 4, SC-003)."""

import numpy as np
import pytest

from corpusbuilder import cli
from corpusbuilder.models import CorpusError
from tests.integration.conftest import read_corpus


def test_couple_desynchronise_aucune_sortie(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=10, n_vectors=9)
    dossier = tmp_path / "in"
    with pytest.raises(CorpusError, match="aucun couple valide"):
        cli.run([dossier], tmp_path / "out", counter_file=counter_file)
    # aucune sortie, aucun numéro consommé
    assert not (tmp_path / "out").exists()
    assert not counter_file.exists()


def test_rejet_sans_interruption(tmp_path, counter_file, make_couple, capsys):
    make_couple("B" * 18, n_chunks=10, n_vectors=9)  # KO
    make_couple("A" * 18, n_chunks=3)  # OK
    code = cli.run(
        [tmp_path / "in"],
        tmp_path / "out",
        counter_file=counter_file,
        random_part="12345",
    )
    assert code == 0
    rows, matrix, _ = read_corpus(tmp_path / "out")
    assert len(rows) == 3
    assert matrix.shape[0] == 3
    stderr = capsys.readouterr().err
    assert "BBBB" in stderr  # le couple KO est identifié
    assert "désynchronisation" in stderr


def test_dimensions_incompatibles_echec_avant_ecriture(
    tmp_path, counter_file, make_couple
):
    make_couple("A" * 18, n_chunks=2, dim=4)
    make_couple("B" * 18, n_chunks=3, dim=8)
    with pytest.raises(CorpusError, match="dimensions.*incompatibles"):
        cli.run([tmp_path / "in"], tmp_path / "out", counter_file=counter_file)
    assert not (tmp_path / "out").exists()
    assert not counter_file.exists()


def test_dimensions_message_liste_les_couples(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=2, dim=4)
    make_couple("B" * 18, n_chunks=3, dim=8)
    with pytest.raises(CorpusError) as infos:
        cli.run([tmp_path / "in"], tmp_path / "out", counter_file=counter_file)
    message = str(infos.value)
    assert "P=4" in message and "P=8" in message
    assert "AAAAAAAAAA" in message and "BBBBBBBBBB" in message


def test_dtypes_heterogenes_non_bloquant(tmp_path, counter_file, make_couple, capsys):
    make_couple("A" * 18, n_chunks=2, dim=4, dtype=np.float32)
    make_couple("B" * 18, n_chunks=3, dim=4, dtype=np.float64)
    code = cli.run(
        [tmp_path / "in"],
        tmp_path / "out",
        counter_file=counter_file,
        random_part="12345",
    )
    assert code == 0
    _, matrix, _ = read_corpus(tmp_path / "out")
    assert matrix.dtype == np.float64  # promotion au dtype commun
    assert "hétérogènes" in capsys.readouterr().err


def test_json_illisible_rejetee(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=2)
    # corruption du JSON : le couple est rejeté, identifié par son nom
    json_path = tmp_path / "in" / f"{'A' * 18}.json"
    json_path.write_text("{ pas du json", encoding="utf-8")
    with pytest.raises(CorpusError, match="aucun couple valide"):
        cli.run([tmp_path / "in"], tmp_path / "out", counter_file=counter_file)


def test_matrice_illisible_rejetee(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=2)
    npy_path = tmp_path / "in" / f"{'A' * 18}-0001.npy"
    npy_path.write_bytes(b"ceci n est pas un npy")
    with pytest.raises(CorpusError, match="aucun couple valide"):
        cli.run([tmp_path / "in"], tmp_path / "out", counter_file=counter_file)


def test_fichiers_orphelins_ignores_non_bloquants(
    tmp_path, counter_file, make_couple, capsys
):
    make_couple("A" * 18, n_chunks=2)
    # orphelins : un .json seul et un .npy seul, formats inattendus
    dossier = tmp_path / "in"
    (dossier / "orphan123456789012.json").write_text("[]", encoding="utf-8")
    np.save(dossier / "987654321.npy", np.zeros((1, 4)))
    (dossier / "note.txt").write_text("ignore", encoding="utf-8")
    code = cli.run(
        [dossier],
        tmp_path / "out",
        counter_file=counter_file,
        random_part="12345",
    )
    assert code == 0
    rows, _, _ = read_corpus(tmp_path / "out")
    assert len(rows) == 2  # seul le couple complet est intégré
    stderr = capsys.readouterr().err
    assert "orphan" in stderr or "orpheline" in stderr


def test_titres_divergents_couple_non_integre(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=2)
    dossier = tmp_path / "in"
    # retire la matrice appariée et la remplace par un titre divergent :
    # le couple est identifiable mais non appariable -> non intégré
    (dossier / f"{'A' * 18}-0001.npy").unlink()
    np.save(dossier / f"{'B' * 18}-0001.npy", np.zeros((2, 4)))
    with pytest.raises(CorpusError, match="aucun couple valide"):
        cli.run([dossier], tmp_path / "out", counter_file=counter_file)
