"""Audit d'un ou plusieurs corpus en lecture seule (FR-013 à FR-020, D12).

Rapport consolidé sur l'union des corpus fournis, effectifs comptés en
sources ; aucune écriture de fichier.
"""

import json
import sys
from pathlib import Path

import numpy as np

from . import dates
from .discovery import Candidate, CoupleKind, _load_json, scan_folder
from .models import Couple, CoupleRejected
from .sources import Source, build_sources
from .transform import corpus_rows


def _cle_candidat(candidat):
    """Ordre de traitement des candidats : radical de titre."""
    return candidat.sort_key


def _cle_valeur(valeur):
    """Tri alphabétique insensible à la casse, stable."""
    return (valeur.lower(), valeur)


def _candidat_fichier(path: Path) -> Candidate | None:
    """Cible fichier : JSON racine-liste + matrice de même radical."""
    try:
        data = _load_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return None
    if not isinstance(data, list):
        return None
    npy = path.with_suffix(".npy")
    if not npy.exists():
        return None
    try:
        matrix = np.load(npy, allow_pickle=False)
    except (ValueError, OSError):
        return None
    return Candidate(
        kind=CoupleKind.CORPUS,
        json_path=path,
        npy_path=npy,
        sort_key=path.stem,
        data=data,
        matrix=matrix,
    )


def collect_couples(cibles) -> tuple[list[Couple], list[Source], list[str]]:
    """Collecte les couples corpus et leurs sources : (couples, sources,
    signaux). Les cibles dossier sont scannées comme pour `corpus` ;
    seuls les couples corpus sont retenus, tout le reste est signalé et
    ignoré (FR-013).
    """
    candidats: list[Candidate] = []
    signaux: list[str] = []
    for cible in cibles:
        chemin = Path(cible)
        if not chemin.exists():
            signaux.append(f"{cible} : chemin introuvable")
            continue
        if chemin.is_file():
            candidat = _candidat_fichier(chemin)
            if candidat is None:
                signaux.append(f"{chemin.name} : pas un corpus (ou matrice absente)")
            else:
                candidats.append(candidat)
            continue
        trouves, _, _ = scan_folder(chemin)
        for candidat in trouves:
            if candidat.kind is not CoupleKind.CORPUS:
                signaux.append(
                    f"{candidat.json_path.name} : couple document ignoré "
                    "(seuls les corpus sont acceptés)"
                )
                continue
            candidats.append(candidat)

    couples: list[Couple] = []
    for candidat in sorted(candidats, key=_cle_candidat):
        try:
            rows = corpus_rows(candidat.data)
        except CoupleRejected as exc:
            signaux.append(f"{candidat.json_path.name} : {exc}")
            continue
        if len(rows) != candidat.matrix.shape[0]:
            signaux.append(
                f"{candidat.json_path.name} : désynchronisation "
                f"({len(rows)} lignes pour {candidat.matrix.shape[0]} vecteurs)"
            )
            continue
        couples.append(
            Couple(
                kind=CoupleKind.CORPUS,
                json_path=candidat.json_path,
                npy_path=candidat.npy_path,
                sort_key=candidat.sort_key,
                rows=rows,
                matrix=candidat.matrix,
            )
        )
    sources = build_sources(couples)
    return couples, sources, signaux


def collect_corpus(cibles) -> tuple[list[Source], list[str]]:
    """Variante lecture seule de `collect_couples` (info-corpus)."""
    _, sources, signaux = collect_couples(cibles)
    return sources, signaux


def _compter(sources, cle, vide):
    """Effectifs par valeur du champ (une source compte +1 par valeur)."""
    comptes: dict[str, int] = {}
    sans = 0
    for source in sources:
        context = source.context if isinstance(source.context, dict) else {}
        valeurs: set[str] = set()
        brut = context.get(cle)
        if isinstance(brut, list):
            valeurs = {v.strip() for v in brut if isinstance(v, str) and v.strip()}
        elif isinstance(brut, str) and brut.strip():
            valeurs = {brut.strip()}
        if not valeurs:
            sans += 1
            continue
        for valeur in valeurs:
            comptes[valeur] = comptes.get(valeur, 0) + 1
    lignes = [
        f"{valeur} ({comptes[valeur]} sources)"
        for valeur in sorted(comptes, key=_cle_valeur)
    ]
    lignes.append(f"{vide} ({sans} sources)")
    return lignes, sans


def rapport_auteurs(sources: list[Source]) -> list[str]:
    lignes, sans = _compter(sources, "Auteur(s)", "sans auteur")
    return [f"Auteurs ({len(lignes) - 1} distincts, {sans} sans auteur) :"] + [
        f"  {ligne}" for ligne in lignes
    ]


def rapport_editeurs(sources: list[Source]) -> list[str]:
    lignes, sans = _compter(sources, "Editeur", "sans editeur")
    return [f"Éditeurs ({len(lignes) - 1} distincts, {sans} sans editeur) :"] + [
        f"  {ligne}" for ligne in lignes
    ]


def rapport_dates(sources: list[Source]) -> list[str]:
    validees: list[tuple[int, int, int]] = []
    sans_date = 0
    for source in sources:
        context = source.context if isinstance(source.context, dict) else {}
        date = dates.parse_date(context.get("Date"))
        if date is None:
            sans_date += 1
        else:
            validees.append(date)
    lignes = ["Dates :"]
    if not validees:
        lignes.append(f"  sans date : {sans_date} sources")
        return lignes
    if dates.fenetre_courte(validees):
        lignes.append(f"  avec date : {len(validees)} sources")
        lignes.append(f"  sans date : {sans_date} sources")
        return lignes
    tranche = dates.choose_tranche(validees)
    libelle = dates.libelle_tranche(tranche)
    for borne, effectif in dates.build_buckets(validees, tranche):
        lignes.append(f"  {borne} (tranche : {libelle}) : {effectif} sources")
    lignes.append(f"  sans date : {sans_date} sources")
    return lignes


def rapport(sources: list[Source], critere: str) -> list[str]:
    """Rapport consolidé : `all` (défaut), `aut`, `edit`, `date`."""
    if critere == "aut":
        return rapport_auteurs(sources)
    if critere == "edit":
        return rapport_editeurs(sources)
    if critere == "date":
        return rapport_dates(sources)
    return (
        rapport_auteurs(sources)
        + [""]
        + rapport_editeurs(sources)
        + [""]
        + rapport_dates(sources)
    )


def afficher_signaux(signaux: list[str]) -> None:
    for signal in signaux:
        print(f"Fichier ignoré - {signal}", file=sys.stderr)
