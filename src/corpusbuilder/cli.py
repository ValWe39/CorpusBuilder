"""CLI `corpus` — interface et pipeline complet (contracts/cli.md).

Arguments : `corpus DOSSIER [DOSSIER ...] [--output-folder CHEMIN]`.
Codes retour : 0 succès, 1 erreur d'exécution, 2 erreur d'usage.
Messages en français ; résumé sur stdout, erreurs et avertissements
sur stderr (FR-001, FR-022, FR-024).
"""

import argparse
import sys
from pathlib import Path

from . import assemble, counter, discovery, output, transform, validation
from .models import CorpusError, Couple, CoupleRejected


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
    return parser


def run(
    folder_paths,
    output_folder,
    counter_file=None,
    random_part=None,
) -> int:
    """Pipeline complet : scan, contrôles, collage, écriture.

    `counter_file` et `random_part` sont injectables pour les tests
    (isolation du compteur du développeur, titres déterministes).
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


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée : 0 succès, 1 erreur d'exécution, 2 erreur d'usage."""
    args = build_parser().parse_args(argv)
    try:
        return run(args.folders, args.output_folder)
    except CorpusError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1
