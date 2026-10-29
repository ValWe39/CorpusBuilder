"""Découpage d'un ou plusieurs corpus en sous-corpus (FR-021 à FR-025).

Un sous-corpus par valeur du critère (auteurs, éditeurs, dates), écrit
à plat dans le dossier de sortie avec un titre suffixé (D8) ;
réingérable par la commande `corpus` (SC-004).
"""

import re
import unicodedata
from pathlib import Path

import numpy as np

from . import counter, dates, infocorpus, output
from .infocorpus import collect_couples
from .models import CorpusError
from .sources import Source

CRITERES = ("aut", "edit", "date")
SLUG_VIDE = {"aut": "sans-aut", "edit": "sans-edit", "date": "sans-date"}


def slug(valeur: str) -> str:
    """Forme normalisée : minuscules sans accents, séparateurs « - »,
    tronquée à 10 caractères (FR-025, D8)."""
    decompose = unicodedata.normalize("NFKD", valeur)
    sans_accent = "".join(c for c in decompose if not unicodedata.combining(c))
    nettoyage = re.sub(r"[^a-z0-9]+", "-", sans_accent.lower()).strip("-")
    return nettoyage[:10] or "sans"


def _contexte(source: Source) -> dict:
    return source.context if isinstance(source.context, dict) else {}


def _valeurs_brutes(source: Source, critere: str) -> list[str]:
    """Valeurs auteur/éditeur d'une source (liste vide = sans valeur)."""
    context = _contexte(source)
    brut = context.get("Auteur(s)" if critere == "aut" else "Editeur")
    if isinstance(brut, list):
        return [v.strip() for v in brut if isinstance(v, str) and v.strip()]
    if isinstance(brut, str) and brut.strip():
        return [brut.strip()]
    return []


def groupes_criteres(sources, critere: str) -> list[tuple[str, list[Source]]]:
    """Groupes (valeur, sources) dans l'ordre de première apparition.

    `date` : même schéma temporel qu'`info-corpus` (FR-021) — fenêtre
    ≤ 6 mois : un groupe « avec date » (FR-019) ; sinon un groupe par
    bucket calendaire. Les sources sans valeur forment le sous-ensemble
    dédié (FR-023).
    """
    groupes: dict[str, list[Source]] = {}

    def ajouter(valeur: str, source: Source) -> None:
        groupes.setdefault(valeur, []).append(source)

    if critere == "date":
        validees: list[tuple[Source, tuple]] = []
        sans_date: list[Source] = []
        for source in sources:
            date = dates.parse_date(_contexte(source).get("Date"))
            if date is None:
                sans_date.append(source)
            else:
                validees.append((source, date))
        if not validees:
            for source in sans_date:
                ajouter(SLUG_VIDE["date"], source)
            return _finaliser(groupes, critere)
        if dates.fenetre_courte([d for _, d in validees]):
            for source, _ in validees:
                ajouter("avec date", source)
        else:
            tranche = dates.choose_tranche([d for _, d in validees])
            for source, date in validees:
                ajouter(dates.libelle_bucket(date, tranche), source)
        for source in sans_date:
            ajouter(SLUG_VIDE["date"], source)
        return _finaliser(groupes, critere)

    for source in sources:
        valeurs = _valeurs_brutes(source, critere)
        if valeurs:
            for valeur in valeurs:  # multi-auteurs : FR-024
                ajouter(valeur, source)
        else:
            ajouter(SLUG_VIDE[critere], source)
    return _finaliser(groupes, critere)


def _finaliser(groupes: dict, critere: str) -> list[tuple[str, list[Source]]]:
    """Ordre déterministe : première apparition, sous-ensemble vide en fin."""
    ordonnes = list(groupes.items())
    vide = SLUG_VIDE[critere]
    return [(valeur, membres) for valeur, membres in ordonnes if valeur != vide] + (
        [(vide, groupes[vide])] if vide in groupes else []
    )


def _base_slug(valeur: str) -> str:
    """Slug de base d'une valeur ; les sous-ensembles dédiés sont
    réservés tels quels (déjà ≤ 10 caractères)."""
    if valeur in SLUG_VIDE.values():
        return valeur
    return slug(valeur)


def run_split(
    cibles,
    critere: str,
    output_folder,
    counter_file=None,
    random_part=None,
) -> int:
    """Découpe les corpus en sous-corpus suffixés (contracts/cli.md).

    Une occurrence du compteur est consommée par sous-corpus écrit ;
    le compteur n'est persisté qu'après succès de toutes les écritures
    (contrat 001, D8) ; aucun sous-corpus vide n'est écrit.
    """
    couples, sources, signaux = collect_couples(cibles)
    infocorpus.afficher_signaux(signaux)
    if not sources:
        raise CorpusError("aucun corpus valide en entrée — aucune sortie produite")
    groupes = groupes_criteres(sources, critere)

    if counter_file is None:
        counter_file = counter.counter_path()
    counter_file = Path(counter_file)
    occurrence = counter.read_last_used(counter_file)
    digits = random_part if random_part is not None else output.random_digits()
    sortie = Path(output_folder)

    pris: set[str] = set()
    ecrits = 0
    for valeur, membres in groupes:
        base = _base_slug(valeur)
        if base in pris:
            numero = 2
            while f"{base[:7]}-{numero}" in pris:
                numero += 1
            base = f"{base[:7]}-{numero}"
        pris.add(base)

        indices: dict[int, list[int]] = {}
        for source in membres:
            for couple_index, row_index in source.refs:
                indices.setdefault(couple_index, []).append(row_index)
        rows = []
        morceaux = []
        for couple_index in sorted(indices):
            liste = sorted(indices[couple_index])
            rows.extend(couples[couple_index].rows[i] for i in liste)
            morceaux.append(couples[couple_index].matrix[liste])
        matrix = morceaux[0] if len(morceaux) == 1 else np.vstack(morceaux)

        occurrence = counter.next_occurrence(occurrence)
        titre = f"{output.build_title(digits, occurrence)}-{base}"
        json_path, _ = output.write_corpus(rows, matrix, titre, sortie)
        ecrits += 1
        print(f"Sous-corpus {critere} : {valeur} -> {json_path} ({len(rows)} lignes)")
    counter.persist(counter_file, occurrence)
    print(f"Bilan : {ecrits} sous-corpus écrits dans {sortie}")
    return 0
