"""Contrôles par couple et intercouples (FR-006 à FR-010).

Par couple (bloquants — rejet du couple, FR-008) : alignement du nombre
de chunks/vecteurs (FR-006) et correspondance des titres (FR-007).
Intercouples : dimension de vecteur bloquante avant écriture (FR-009),
nature des float informative (FR-010).
"""

import sys

from .discovery import Candidate
from .models import ChunkRow, CorpusError, Couple, CoupleKind, CoupleRejected


def check_couple(candidate: Candidate, rows: list[ChunkRow]) -> None:
    """FR-006 et FR-007 — KO : le couple est rejeté, pas l'exécution."""
    matrix = candidate.matrix
    if matrix.ndim != 2:
        raise CoupleRejected(
            f"matrice non conforme : {matrix.ndim} dimension(s), attendu N×P"
        )
    if len(rows) != matrix.shape[0]:
        raise CoupleRejected(
            f"désynchronisation : {len(rows)} chunks pour {matrix.shape[0]} vecteurs"
        )
    if candidate.kind is CoupleKind.DOCUMENT:
        attendu = candidate.json_path.stem[:18]
        if candidate.npy_path.stem[:18] != attendu:
            raise CoupleRejected("titres non appariés (18 premiers caractères)")
    elif candidate.npy_path.stem != candidate.json_path.stem:
        raise CoupleRejected("titres non appariés (9 chiffres)")


def check_dimensions(couples: list[Couple]) -> None:
    """FR-009 — échec avant toute écriture, couples incompatibles listés."""
    dims = {couple.matrix.shape[1] for couple in couples}
    if len(dims) > 1:
        details = "; ".join(
            f"{couple.json_path.name} -> P={couple.matrix.shape[1]}"
            for couple in couples
        )
        raise CorpusError(
            "dimensions de vecteur incompatibles entre couples "
            f"({', '.join(str(d) for d in sorted(dims))}) : {details}"
        )


def check_dtypes(couples: list[Couple]) -> bool:
    """FR-010 — avertissement non bloquant si natures de float hétérogènes."""
    dtypes = {couple.matrix.dtype for couple in couples}
    if len(dtypes) > 1:
        noms = ", ".join(str(dtype) for dtype in dtypes)
        print(
            "Avertissement : natures de float hétérogènes "
            f"({noms}) — promotion automatique au dtype commun.",
            file=sys.stderr,
        )
        return True
    return False
