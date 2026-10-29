"""T021 — US-4 : appariement des corpus à titre suffixé (contrat formats).

La regex d'appariement accepte le suffixe de sous-corpus (contracts/
file-formats.md section 2) ; les corpus à 9 chiffres restent valides.
"""

import json

import numpy as np

from corpusbuilder.discovery import scan_folder
from corpusbuilder.transform import build_rows
from corpusbuilder.validation import check_couple


def _ecrire(folder, stem, n_rows=2):
    rows = [
        {"text": f"texte {i}", "ref": i, "path": "source.md"}
        for i in range(1, n_rows + 1)
    ]
    (folder / f"{stem}.json").write_text(
        json.dumps(rows, ensure_ascii=False), encoding="utf-8"
    )
    np.save(folder / f"{stem}.npy", np.zeros((n_rows, 3)))


def test_corpus_suffixe_apparie(tmp_path):
    _ecrire(tmp_path, "111110001-la-tribune")
    candidats, rejets, _ = scan_folder(tmp_path)
    assert len(candidats) == 1
    assert len(rejets) == 0
    couple = candidats[0]
    assert couple.json_path.stem == "111110001-la-tribune"
    # validation et construction des lignes passent (réingérable)
    rows = build_rows(couple)
    check_couple(couple, rows)


def test_corpus_neuf_chiffres_toujours_valide(tmp_path):
    _ecrire(tmp_path, "222220001")
    candidats, rejets, _ = scan_folder(tmp_path)
    assert len(candidats) == 1
    assert len(rejets) == 0


def test_suffixe_trop_long_rejete(tmp_path):
    # suffixe de 13 caractères : hors contrat (1 à 10)
    _ecrire(tmp_path, "333330001-trop-long-titre")
    candidats, _, _ = scan_folder(tmp_path)
    assert len(candidats) == 0
