"""T027 — US5 : dossier de sortie (FR-022, quickstart scénario 2)."""

from corpusbuilder import cli, counter
from tests.integration.conftest import read_corpus


def test_dossier_par_defaut_output(tmp_path, counter_file, make_couple, monkeypatch):
    make_couple("A" * 18, n_chunks=2)

    # isolation du compteur (D9) : le compteur réel n'est pas consommé
    def chemin_compteur_isole():
        return counter_file

    monkeypatch.setattr(counter, "counter_path", chemin_compteur_isole)
    # le répertoire courant est isolé : `output` y sera créé par défaut
    monkeypatch.chdir(tmp_path)
    code = cli.main([str(tmp_path / "in")])
    assert code == 0
    out = tmp_path / "output"
    assert out.is_dir()
    rows, matrix, _ = read_corpus(out)
    assert matrix.shape[0] == len(rows) == 2
    assert counter_file.read_text(encoding="utf-8").strip() == "0001"


def test_output_folder_personnalise(tmp_path, counter_file, make_couple):
    make_couple("A" * 18, n_chunks=3)
    out = tmp_path / "ailleurs" / "profond"
    code = cli.run([tmp_path / "in"], out, counter_file=counter_file)
    assert code == 0
    assert out.is_dir()  # créé si nécessaire
    rows, _, title = read_corpus(out)
    assert len(rows) == 3
    assert len(title) == 9 and title.isdigit()
