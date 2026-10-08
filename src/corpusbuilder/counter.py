"""Compteur d'occurrence persistant (FR-018 à FR-021, décision D6)."""

import re
from pathlib import Path

from .models import CorpusError

PATTERN = re.compile(r"^\d{4}$")


def counter_path() -> Path:
    """Racine de l'outil : répertoire où réside pyproject.toml."""
    return Path(__file__).resolve().parent.parent.parent / "counter.txt"


def read_last_used(path: Path) -> int:
    """Dernier numéro utilisé ; 0 si le fichier est absent (FR-021)."""
    if not path.exists():
        return 0
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CorpusError(f"compteur illisible ({path}) : {exc}") from exc
    stripped = content.strip()
    if not PATTERN.match(stripped):
        extrait = stripped[:20] if stripped else "(vide)"
        raise CorpusError(
            f"compteur corrompu ({path}) : contenu illisible "
            f"'{extrait}' — attendu : 4 chiffres (NNNN)"
        )
    return int(stripped)


def next_occurrence(last_used: int) -> int:
    """Cycle : premier usage 0001, +1 par document, 9999 -> 0000 (FR-020)."""
    if last_used >= 9999:
        return 0
    return last_used + 1


def persist(path: Path, value: int) -> None:
    """Persiste le numéro consommé : fichier temporaire puis remplacement."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(f"{value:04d}\n", encoding="utf-8")
    tmp.replace(path)
