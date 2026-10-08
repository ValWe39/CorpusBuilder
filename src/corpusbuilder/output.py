"""Écriture des sorties, titres et contrôle final (FR-017, FR-022,
FR-023, décisions D7 et D8)."""

import json
import secrets
from pathlib import Path

import numpy as np

from .models import ChunkRow, CorpusError


def random_digits() -> str:
    """D7 : 5 chiffres aléatoires tirés une fois par exécution."""
    return f"{secrets.randbelow(100000):05d}"


def build_title(digits: str, occurrence: int) -> str:
    """FR-017 : titre à 9 chiffres = 5 aléatoires + occurrence à 4 chiffres."""
    return f"{digits}{occurrence:04d}"


def write_corpus(
    rows: list[ChunkRow],
    matrix: np.ndarray,
    title: str,
    output_folder: Path,
) -> tuple[Path, Path]:
    """Écrit le couple corpus après le contrôle final FR-023.

    Conflit de titre : échec sans écraser l'existant (Edge Cases).
    """
    # FR-023 : contrôle final avant toute écriture
    if len(rows) != matrix.shape[0]:
        raise CorpusError(
            f"contrôle final en échec : {len(rows)} lignes pour "
            f"{matrix.shape[0]} vecteurs"
        )
    output_folder = Path(output_folder)
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        # sortie non inscriptible : échec rapide, aucune sortie partielle
        raise CorpusError(
            f"échec d'écriture : dossier de sortie inutilisable "
            f"({output_folder}) : {exc}"
        ) from exc
    json_path = output_folder / f"{title}.json"
    npy_path = output_folder / f"{title}.npy"
    if json_path.exists() or npy_path.exists():
        raise CorpusError(
            f"conflit de titre : {json_path.name} existe déjà — aucun fichier écrasé"
        )
    payload = [row.to_dict() for row in rows]
    try:
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        np.save(npy_path, matrix)
    except OSError as exc:
        raise CorpusError(f"échec d'écriture ({output_folder}) : {exc}") from exc
    return json_path, npy_path
