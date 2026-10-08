# Implementation Plan: Corpus Concaténation (CorpusBuilder)

**Branch**: `002-corpus-concat` | **Date**: 2026-10-08
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-corpus-concatenation/spec.md`

## Summary

Concaténer localement des couples (JSON d'index + matrice NumPy) — documents
découpés en chunks ou corpus déjà aplatis — en un couple corpus unique
réingérable : un JSON plat (une ligne autoporteuse par chunk) et une matrice
NumPy empilée verticalement dans le même ordre déterministe. CLI Python
`corpus` avec contrôles par couple (bloquants), contrôles intercouples
(dimension bloquante, nature des float informative), titre à 9 chiffres
(5 chiffres aléatoires + occurrence persistée dans un fichier compteur),
sortie dans `output/` par défaut ou `--output-folder`.

## Technical Context

**Language/Version**: Python 3.11+ (minimum 3.10).

**Primary Dependencies**: numpy (unique dépendance d'exécution, BSD-3) ;
argparse, json, pathlib, secrets, logging (stdlib).

**Storage**: système de fichiers uniquement — JSON + `.npy` en sortie, fichier
compteur texte `counter.txt` à la racine de l'outil.

**Testing**: pytest — tests unitaires par module, tests d'intégration sur
`Examples/Exemple1` et `Examples/Exemple2`, réingestion des sorties.

**Target Platform**: machine locale — Windows, macOS ou Linux, hors-ligne.

**Project Type**: cli.

**Performance Goals**: exécution complète sur les exemples (moins d'une
centaine de documents) en moins de 30 s (SC-007).

**Constraints**: 100 % local — aucun appel réseau, aucun tracker, aucune
télémétrie (Constitution II et III) ; messages utilisateur en français.

**Scale/Scope**: ordre de grandeur visé — centaines de couples, quelques
millions de vecteurs au total lors de l'empilement en mémoire.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Vérification contre la Constitution v1.4.0 (`.specify/memory/constitution.md`)
:

- **I. Isolation des secrets** : aucun secret requis, aucune clé manipulée —
  PASS.
- **II. Local-first & confidentialité** : traitement, stockage et logs 100 %
  locaux, aucun appel réseau en exécution normale — PASS.
- **III. Open-source & sans trackers** : numpy (BSD-3-Clause) et pytest (MIT)
  sont open-source et sans télémétrie — PASS.
- **IV. Simplicité (YAGNI)** : CLI unique, argparse de la stdlib, un seul
  paquet Python, pas de GUI, pas de plugins — PASS.
- **Path Isolation** : chemins d'entrée fournis par l'utilisateur, sortie par
  défaut relative (`output/`), aucun chemin personnel codé en dur — PASS.
- **Data Retention** : aucune copie cachée ; seules les sorties et
  `counter.txt` persistent — PASS.
- **Sovereign Tools Preference** : aucune alternative souveraine pertinente
  n'existe pour lire/écrire le format `.npy` ; numpy retenu par nécessité de
  format, sous licence permissive — PASS avec note.

Aucune violation. Re-check post-Phase 1 (design : `research.md`,
`data-model.md`, `contracts/`, `quickstart.md`) : pas de nouvelle dépendance,
pas de réseau, pas d'abstraction prématurée — PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-corpus-concatenation/
├── plan.md              # ce fichier (/speckit-plan)
├── research.md          # Phase 0 (/speckit-plan)
├── data-model.md        # Phase 1 (/speckit-plan)
├── quickstart.md        # Phase 1 (/speckit-plan)
├── contracts/           # Phase 1 (/speckit-plan)
│   ├── cli.md           # contrat d'interface CLI
│   └── file-formats.md  # contrats de formats de fichiers
└── tasks.md             # Phase 2 (/speckit-tasks — à venir)
```

### Source Code (repository root)

```text
src/corpusbuilder/
├── __init__.py
├── __main__.py         # python -m corpusbuilder
├── cli.py              # argparse : corpus DOSSIERS... [--output-folder P]
├── discovery.py        # scan des dossiers, appariement document/corpus
├── models.py           # dataclasses : couples, chunks, lignes de corpus
├── validation.py       # contrôles par couple et intercouples
├── transform.py        # document -> lignes de chunks aplaties
├── assemble.py         # ordre de collage déterministe, empilement
├── counter.py           # compteur d'occurrence persistant
└── output.py           # écriture des sorties et contrôle final

tests/
├── unit/               # counter, validation, transform, discovery, assemble
└── integration/        # Examples/, réingestion, compteur, --output-folder

pyproject.toml          # packaging + script console `corpus`
counter.txt             # créé à la première exécution (racine de l'outil)
output/                 # sorties par défaut (gitignoré)
```

**Structure Decision**: paquet Python unique et plat, un module par
responsabilité (Option 1 du template). Les données transitent en dataclasses
simples entre modules ; aucune base de données, aucun service. Point d'entrée
: script console `corpus` (pyproject.toml), doublé de `python -m
corpusbuilder`. `counter.txt` est résolu à la racine de l'outil (répertoire
parent du paquet, là où réside `pyproject.toml`).

## Suivi de complexité

Aucune violation de la Constitution à justifier.
