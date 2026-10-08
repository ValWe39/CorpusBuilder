"""T020/T021/T022 — US4 : garanties du titre et du compteur (SC-004)."""

import pytest

from corpusbuilder import cli
from corpusbuilder.models import CorpusError
from tests.integration.conftest import read_corpus


def test_premiere_execution_numero_0001(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=2)
    cli.run(
        [tmp_path / "in"],
        tmp_path / "out",
        counter_file=counter_file,
        random_part="12345",
    )
    _, _, title = read_corpus(tmp_path / "out")
    assert title == "123450001"
    assert counter_file.read_text(encoding="utf-8").strip() == "0001"


def test_occurrences_consecutives_deux_executions(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=2)
    cli.run(
        [tmp_path / "in"],
        tmp_path / "out",
        counter_file=counter_file,
        random_part="12345",
    )
    cli.run(
        [tmp_path / "in"],
        tmp_path / "out2",
        counter_file=counter_file,
        random_part="12345",
    )
    _, _, titre1 = read_corpus(tmp_path / "out")
    _, _, titre2 = read_corpus(tmp_path / "out2")
    assert titre1 == "123450001" and titre2 == "123450002"
    assert counter_file.read_text(encoding="utf-8").strip() == "0002"


def test_cycle_apres_9999(tmp_path, counter_file, make_couple):
    counter_file.write_text("9999\n", encoding="utf-8")
    make_couple("A" * 18, n_chunks=2)
    cli.run(
        [tmp_path / "in"],
        tmp_path / "out",
        counter_file=counter_file,
        random_part="12345",
    )
    _, _, title = read_corpus(tmp_path / "out")
    assert title == "123450000"  # retour à 0000 (FR-020)
    assert counter_file.read_text(encoding="utf-8").strip() == "0000"


def test_compteur_corrompu_echec_immediat_sans_sortie(
    tmp_path, counter_file, make_couple, capsys
):
    counter_file.write_text("corrompu", encoding="utf-8")
    make_couple("A" * 18, n_chunks=2)
    with pytest.raises(CorpusError, match="corrompu"):
        cli.run([tmp_path / "in"], tmp_path / "out", counter_file=counter_file)
    assert not (tmp_path / "out").exists()
    # le compteur corrompu n'est pas modifié
    assert counter_file.read_text(encoding="utf-8") == "corrompu"


def test_numero_non_consomme_si_echec(tmp_path, counter_file, make_couple):
    counter_file.write_text("0007\n", encoding="utf-8")
    make_couple("A" * 18, n_chunks=2)
    # sortie non inscriptible : un fichier occupe le chemin du dossier
    bloquant = tmp_path / "bloquant"
    bloquant.write_text("occupé", encoding="utf-8")
    with pytest.raises(CorpusError, match="écriture"):
        cli.run([tmp_path / "in"], bloquant, counter_file=counter_file)
    # le numéro n'a pas été consommé : compteur inchangé (FR-019, D8)
    assert counter_file.read_text(encoding="utf-8").strip() == "0007"
    # deuxième tentative avec sortie valide : numéro suivant = 0008
    cli.run(
        [tmp_path / "in"],
        tmp_path / "ok",
        counter_file=counter_file,
        random_part="12345",
    )
    _, _, title = read_corpus(tmp_path / "ok")
    assert title == "123450008"


def test_conflit_de_titre_sans_ecrasement(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=2)
    out = tmp_path / "out"
    out.mkdir()
    existant = out / "123450001.json"
    existant.write_text("précieux", encoding="utf-8")
    with pytest.raises(CorpusError, match="conflit de titre"):
        cli.run(
            [tmp_path / "in"],
            out,
            counter_file=counter_file,
            random_part="12345",
        )
    # l'existant est intact et le numéro n'est pas consommé
    assert existant.read_text(encoding="utf-8") == "précieux"
    assert not counter_file.exists()
