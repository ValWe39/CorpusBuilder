"""Collage déterministe JSON + matrice (FR-014 à FR-016)."""

from itertools import chain
from operator import attrgetter

import numpy as np

from .models import ChunkRow, Couple


def order_couples(per_folder: list[list[Couple]]) -> list[Couple]:
    """FR-014 : dossiers dans l'ordre fourni par l'utilisateur ; tri
    alphabétique du radical de titre au sein de chaque dossier. La même
    règle régit JSON et matrice (FR-015)."""
    ordered: list[Couple] = []
    for couples in per_folder:
        ordered.extend(sorted(couples, key=attrgetter("sort_key")))
    return ordered


def assemble(ordered: list[Couple]) -> tuple[list[ChunkRow], np.ndarray]:
    """FR-016 : concaténation verticale des matrices dans l'ordre de
    collage ; le i-ème vecteur correspond à la i-ème ligne du JSON
    (FR-015). Promotion automatique au dtype commun (D2, FR-010)."""
    rows: list[ChunkRow] = list(chain.from_iterable(c.rows for c in ordered))
    matrix = np.vstack([c.matrix for c in ordered])
    return rows, matrix
