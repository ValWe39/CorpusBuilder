"""Dataclasses partagées de CorpusBuilder (cf. data-model.md)."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np


class CorpusError(Exception):
    """Erreur bloquante : l'exécution échoue avant toute écriture."""


class CoupleRejected(Exception):
    """Erreur non bloquante : le couple est rejeté, les autres continuent."""


class CoupleKind(Enum):
    DOCUMENT = "document"
    CORPUS = "corpus"


@dataclass
class DocumentMetadata:
    """Métadonnées du document source (FR-004)."""

    path: str
    title: str | None = None
    structure: str | None = None
    typologie: str | None = None
    context: str | None = None
    chunkingid: str | None = None


@dataclass
class Chunk:
    """Fragment d'un document d'entrée (FR-004)."""

    ref: int
    text: str
    length: int | None = None
    boundary: str | None = None
    part: str | None = None
    page: int | None = None
    position_in_part: int | None = None
    atomic: bool | None = None


@dataclass
class ChunkRow:
    """Ligne plate autoporteuse — sortie et réingération (FR-011, FR-013)."""

    text: str
    ref: int
    path: str
    part: str | None = None
    page: int | None = None
    title: str | None = None
    context: str | None = None
    chunkingid: str | None = None

    def to_dict(self) -> dict:
        """Sérialise en omettant les clés absentes ou nulles."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Couple:
    """Couple validé, prêt pour le collage (FR-014 à FR-016)."""

    kind: CoupleKind
    json_path: Path
    npy_path: Path
    sort_key: str
    rows: list[ChunkRow]
    matrix: np.ndarray
