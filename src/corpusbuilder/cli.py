"""CLI `corpus` — interface et pipeline complet (contracts/cli.md).

Arguments : `corpus DOSSIER [DOSSIER ...] [--output-folder CHEMIN]`.
Codes retour : 0 succès, 1 erreur d'exécution, 2 erreur d'usage.
Messages en français ; résumé sur stdout, erreurs et avertissements
sur stderr (FR-001, FR-022, FR-024).
"""

import argparse
import sys
from pathlib import Path

from . import (
    assemble,
    counter,
    dedup,
    discovery,
    infocorpus,
    output,
    split,
    transform,
    validation,
)
from .models import CorpusError, Couple, CoupleRejected

CRITERES_INFO = ("all", "aut", "edit", "date")
CRITERES_SPLIT = ("aut", "edit", "date")


def _separer_critere(
    elements: list[str], permis: tuple, defaut: str
) -> tuple[list[str], str]:
    """Sépare les cibles du critère positionnel optionnel.

    `elements` est glouton (nargs="+") : si le dernier élément est un
    critère permis et qu'il reste au moins une cible, il est détaché.
    """
    if len(elements) > 1 and elements[-1] in permis:
        return elements[:-1], elements[-1]
    return list(elements), defaut


def _seuil_doublons(valeur: str) -> int:
    """FR-005 : entier entre 60 et 100, sinon erreur d'usage (code 2)."""
    try:
        seuil = int(valeur)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"seuil invalide : {valeur!r} — attendu : entier entre 60 et 100"
        ) from None
    if not 60 <= seuil <= 100:
        raise argparse.ArgumentTypeError(
            f"seuil hors bornes : {seuil} — attendu : entier entre 60 et 100"
        )
    return seuil


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="corpus",
        description=(
            "Concatène des couples JSON + matrice NumPy (documents ou "
            "corpus) en un couple corpus unique, 100 % localement."
        ),
    )
    parser.add_argument(
        "folders",
        nargs="+",
        metavar="DOSSIER",
        help="dossiers d'entrée (un ou plusieurs)",
    )
    parser.add_argument(
        "--output-folder",
        metavar="CHEMIN",
        default="output",
        help="dossier de sortie (défaut : output)",
    )
    parser.add_argument(
        "--suppr-doublons",
        action="store_true",
        help="exclure les sources en doublon du corpus de sortie "
        "(les entrées ne sont jamais modifiées)",
    )
    parser.add_argument(
        "--seuil-doublons",
        type=_seuil_doublons,
        metavar="N",
        default=None,
        help="seuil de similarité de texte, entier 60 à 100 (défaut : 75)",
    )
    return parser


def run(
    folder_paths,
    output_folder,
    counter_file=None,
    random_part=None,
    suppr_doublons=False,
    seuil_doublons=75,
) -> int:
    """Pipeline complet : scan, contrôles, collage, écriture.

    `counter_file` et `random_part` sont injectables pour les tests
    (isolation du compteur du développeur, titres déterministes).
    Avec `suppr_doublons` : détection sur toutes les sources de
    l'exécution puis exclusion avant le collage (FR-008, FR-010).
    """
    # FR-021 : lecture du compteur avant tout traitement — échec rapide,
    # aucune sortie, aucune consommation de numéro.
    if counter_file is None:
        counter_file = counter.counter_path()
    counter_file = Path(counter_file)
    last_used = counter.read_last_used(counter_file)

    per_folder: list[list[Couple]] = []
    rejets: list[str] = []
    ignores: list[str] = []

    for folder_path in folder_paths:
        folder = Path(folder_path)
        # FR-001 : chaque chemin doit obligatoirement désigner un dossier
        if not folder.is_dir():
            raise CorpusError(f"le chemin n'est pas un dossier : {folder}")
        candidates, folder_rejets, ignored = discovery.scan_folder(folder)
        rejets.extend(f"{folder.name}/{msg}" for msg in folder_rejets)
        ignores.extend(f"{folder.name}/{msg}" for msg in ignored)
        valid: list[Couple] = []
        for candidate in candidates:
            try:
                rows = transform.build_rows(candidate)
                validation.check_couple(candidate, rows)
            except CoupleRejected as exc:
                rejets.append(f"{candidate.json_path.name} : {exc}")
                continue
            valid.append(
                Couple(
                    kind=candidate.kind,
                    json_path=candidate.json_path,
                    npy_path=candidate.npy_path,
                    sort_key=candidate.sort_key,
                    rows=rows,
                    matrix=candidate.matrix,
                )
            )
        per_folder.append(valid)

    # FR-008 : les rejets sont signalés sans interrompre l'exécution
    for rejet in rejets:
        print(f"Couple rejeté - {rejet}", file=sys.stderr)
    for message in ignores:
        print(f"Fichier ignoré - {message}", file=sys.stderr)

    couples = assemble.order_couples(per_folder)
    if not couples:
        raise CorpusError("aucun couple valide en entrée — aucune sortie produite")

    if suppr_doublons:
        couples, resultat = dedup.appliquer_exclusion(couples, seuil_doublons)
        for ligne in dedup.rapport(resultat, seuil_doublons):
            print(ligne)
        if not couples:
            raise CorpusError(
                "aucune source ne subsiste après exclusion des doublons "
                "— aucune sortie produite"
            )

    # FR-009 : dimension bloquante avant toute écriture ; FR-010 :
    # nature des float informative.
    validation.check_dimensions(couples)
    validation.check_dtypes(couples)

    rows, matrix = assemble.assemble(couples)

    occurrence = counter.next_occurrence(last_used)
    digits = random_part if random_part is not None else output.random_digits()
    title = output.build_title(digits, occurrence)
    json_path, npy_path = output.write_corpus(rows, matrix, title, Path(output_folder))
    # D8 : le numéro n'est consommé qu'après l'écriture réussie
    counter.persist(counter_file, occurrence)

    print(f"Couples valides : {len(couples)}")
    print(f"Couples rejetés : {len(rejets)}")
    print(f"Fichiers ignorés : {len(ignores)}")
    print(f"Corpus écrit : {json_path}")
    print(f"Matrice écrite : {npy_path}")
    return 0


def build_info_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="info-corpus",
        description=(
            "Auditer la composition d'un ou plusieurs corpus, "
            "en lecture seule (auteurs, éditeurs, dates)."
        ),
    )
    parser.add_argument(
        "elements",
        nargs="+",
        metavar="CIBLE",
        help="corpus (fichier ou dossier), puis critère optionnel",
    )
    return parser


def main_info(argv: list[str] | None = None) -> int:
    """`info-corpus` : 0 succès, 1 erreur, 2 usage (contracts/cli.md)."""
    parser = build_info_parser()
    args = parser.parse_args(argv)
    cibles, critere = _separer_critere(args.elements, CRITERES_INFO, "all")
    sources, signaux = infocorpus.collect_corpus(cibles)
    infocorpus.afficher_signaux(signaux)
    if not sources:
        print("Erreur : aucun corpus valide en entrée.", file=sys.stderr)
        return 1
    for ligne in infocorpus.rapport(sources, critere):
        print(ligne)
    return 0


def build_split_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="corpus-split",
        description=(
            "Découper un ou plusieurs corpus en sous-corpus "
            "réingérables, par critère (auteurs, éditeurs, dates)."
        ),
    )
    parser.add_argument(
        "elements",
        nargs="+",
        metavar="CIBLE",
        help="corpus (fichier ou dossier), puis critère optionnel",
    )
    parser.add_argument(
        "--output-folder",
        metavar="CHEMIN",
        default="output",
        help="dossier de sortie (défaut : output)",
    )
    return parser


def main_split(argv: list[str] | None = None) -> int:
    """`corpus-split` : 0 succès, 1 erreur, 2 usage (contracts/cli.md)."""
    parser = build_split_parser()
    args = parser.parse_args(argv)
    cibles, critere = _separer_critere(args.elements, CRITERES_SPLIT, "edit")
    try:
        return split.run_split(cibles, critere, args.output_folder)
    except CorpusError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée : 0 succès, 1 erreur d'exécution, 2 erreur d'usage."""
    args = build_parser().parse_args(argv)
    seuil = 75 if args.seuil_doublons is None else args.seuil_doublons
    if args.seuil_doublons is not None and not args.suppr_doublons:
        print(
            "Avertissement : --seuil-doublons ignoré sans --suppr-doublons.",
            file=sys.stderr,
        )
    try:
        return run(
            args.folders,
            args.output_folder,
            suppr_doublons=args.suppr_doublons,
            seuil_doublons=seuil,
        )
    except CorpusError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
