"""Scan des dossiers et appariement des couples (FR-003 à FR-005, D2, D4).

Décisions de research.md : D2 (numpy.load avec allow_pickle=False),
D4 (distinction document/corpus par la structure du JSON).
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .models import CoupleKind, CoupleRejected

DOC_STEM_LEN = 18
NPY_STEM_TOTAL = 23  # 18 caractères + "-" + 4 caractères (FR-005)
CORPUS_TITLE = re.compile(r"^\d{9}$")


@dataclass
class Candidate:
    """Couple apparié en attente de validation (contenu chargé)."""

    kind: CoupleKind
    json_path: Path
    npy_path: Path
    sort_key: str
    data: object  # dict (document) ou list (corpus)
    matrix: np.ndarray


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_matrix(path: Path) -> np.ndarray:
    try:
        # D2 : allow_pickle=False empêche l'exécution de code embarqué
        return np.load(path, allow_pickle=False)
    except (ValueError, OSError) as exc:
        raise CoupleRejected(f"matrice illisible ({exc})") from exc


def _detect_kind(data: object) -> CoupleKind | None:
    """D4 : objet à clés schema_version/document/chunks = document,
    tableau = corpus, tout le reste n'est pas reconnu (ignoré, FR-003)."""
    if isinstance(data, dict) and {"schema_version", "document", "chunks"} <= set(data):
        return CoupleKind.DOCUMENT
    if isinstance(data, list):
        return CoupleKind.CORPUS
    return None


def _pair_document(folder: Path, json_stem: str) -> Path | None:
    """FR-005 : .npy à radical identique sur 18 caractères + `-XXXX`."""
    if len(json_stem) < DOC_STEM_LEN:
        return None
    prefix = json_stem[:DOC_STEM_LEN]
    matches = sorted(
        p
        for p in folder.glob("*.npy")
        if len(p.stem) == NPY_STEM_TOTAL
        and p.stem[DOC_STEM_LEN] == "-"
        and p.stem[:DOC_STEM_LEN] == prefix
    )
    if not matches:
        return None
    if len(matches) > 1:
        raise CoupleRejected(
            f"plusieurs matrices candidates pour {prefix} : "
            + ", ".join(p.name for p in matches)
        )
    return matches[0]


def _pair_corpus(folder: Path, json_stem: str) -> Path | None:
    """FR-005 : corpus apparié par titre à 9 chiffres strictement identique."""
    if not CORPUS_TITLE.match(json_stem):
        return None
    candidate = folder / f"{json_stem}.npy"
    return candidate if candidate.exists() else None


def scan_folder(folder: Path) -> tuple[list[Candidate], list[str], list[str]]:
    """Scanne un dossier : (candidats, rejets, ignorés).

    Rejets : couples identifiables en erreur (JSON ou matrice illisible,
    plusieurs matrices candidates) — FR-008, cas limites.
    Ignorés : fichiers orphelins et formats non reconnus, signalés sans
    faire échouer l'exécution (FR-003).
    """
    candidates: list[Candidate] = []
    rejetes: list[str] = []
    ignored: list[str] = []
    matched_npy: set[Path] = set()

    json_paths = sorted(folder.glob("*.json"), key=_name_key)
    for json_path in json_paths:
        try:
            data = _load_json(json_path)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            rejetes.append(f"{json_path.name} : JSON illisible ({exc})")
            continue
        kind = _detect_kind(data)
        if kind is None:
            ignored.append(f"{json_path.name} : format non reconnu")
            continue
        if kind is CoupleKind.DOCUMENT:
            npy_path = _pair_document(folder, json_path.stem)
        else:
            npy_path = _pair_corpus(folder, json_path.stem)
        if npy_path is None:
            ignored.append(
                f"{json_path.name} : aucune matrice appariée "
                "(titre divergent ou matrice absente)"
            )
            continue
        try:
            matrix = _load_matrix(npy_path)
        except CoupleRejected as exc:
            rejetes.append(f"{npy_path.name} : matrice illisible ({exc})")
            continue
        matched_npy.add(npy_path)
        candidates.append(
            Candidate(
                kind=kind,
                json_path=json_path,
                npy_path=npy_path,
                sort_key=(
                    json_path.stem[:DOC_STEM_LEN]
                    if kind is CoupleKind.DOCUMENT
                    else json_path.stem
                ),
                data=data,
                matrix=matrix,
            )
        )

    for npy_path in sorted(folder.glob("*.npy"), key=_name_key):
        if npy_path not in matched_npy:
            ignored.append(f"{npy_path.name} : matrice orpheline")

    return candidates, rejetes, ignored


def _name_key(path: Path) -> str:
    """Clé de tri alphabétique par nom de fichier (sans expression anonyme)."""
    return path.name
