# Implementation Plan: Déduplication et séparation de corpus (CorpusBuilder)

**Branch**: `003-doublons-split` | **Date**: 2026-10-27
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-doublons-split/spec.md`
(handoff de l'assessment `dedup-corpus-split`, mesures de similarité et
vérité terrain issues de `.specify/assessments/dedup-corpus-split/`).

## Summary

Étendre CorpusBuilder avec la déduplication déterministe à seuil réglable
(`--suppr-doublons`, `--seuil-doublons` 60-100, défaut 75 : contexte
strictement identique, ou similarité de texte Jaccard sur shingles ≥ seuil),
appliquée à toutes les sources de l'exécution, entrées jamais altérées, les
sources perdantes étant exclues du corpus de sortie assemblé, avec rapport
terminal ; plus deux commandes d'analyse : `info-corpus` (auteurs, éditeurs,
buckets temporels ≤ 6 alignés calendaires) et `corpus-split` (sous-corpus
réingérables par valeur de critère). Le calibrage et les tests reposent
obligatoirement sur les jeux réels : `Examples/Exemple-complement1`
(déduplication sur entrées document, 232 sources, vérité terrain mesurée) et
`Examples/Exemple-complement2` (déduplication sur entrées corpus, 51 + 232
sources ; `info-corpus` et `corpus-split`).

## Technical Context

**Language/Version**: Python 3.11+ (minimum 3.10) — continuité de la
spécification 001.

**Primary Dependencies**: numpy (BSD-3, déjà requise) ; argparse, json,
pathlib, re, unicodedata (stdlib). Aucune nouvelle dépendance.

**Storage**: système de fichiers uniquement — JSON + `.npy` en sortie,
`counter.txt` inchangé.

**Testing**: pytest — tests unitaires par module ; tests d'intégration sur
`Examples/Exemple-complement1` et `Examples/Exemple-complement2` (jeux réels
servant au calibrage, conformément à la spec), réingération des sorties,
vérification du déterminisme.

**Target Platform**: machine locale — Windows, macOS ou Linux, hors-ligne.

**Project Type**: cli.

**Performance Goals**: détection par paires en O(n²) sur les sources —
mesuré en assessment à 1,1 s pour 232 sources en pur Python ; ≤ 30 s pour
une exécution complète sur les jeux d'exemple (SC-005).

**Constraints**: 100 % local et déterministe (Constitution II, spec) ;
aucun appel réseau ni LLM en phase 1 ; messages utilisateur en français ;
aucune écriture dans les dossiers d'entrée.

**Scale/Scope**: quelques centaines à quelques milliers de sources par
exécution ; au-delà, l'optimisation (MinHash/LSH) est hors périmètre.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Vérification contre la Constitution (`.specify/memory/constitution.md`) :

- **I. Isolation des secrets** : aucun secret, aucune clé manipulée — PASS.
- **II. Local-first & confidentialité** : tout le traitement, les rapports et
  les sorties restent locaux ; aucun appel réseau — PASS.
- **III. Open-source & sans trackers** : numpy (BSD-3) et pytest (MIT)
  uniquement ; aucune nouvelle dépendance — PASS.
- **IV. Simplicité (YAGNI)** : trois interfaces CLI en argparse ; réutilisation
  du pipeline existant (discovery, validation, collage, écriture, compteur) ;
  pas de MinHash/LSH (injustifié à l'échelle visée), pas de LLM, pas de
  configuration — PASS.
- **Path Isolation** : chemins fournis par l'utilisateur ; les jeux d'exemples
  sont référencés en chemins relatifs (jamais absolus) ; défauts de sortie
  relatifs (`output`) — PASS.
- **Data Retention** : aucune copie cachée — les entrées ne sont jamais
  modifiées (FR-008) ; `info-corpus` ne produit aucun fichier ; les sorties
  vont exclusivement dans le dossier demandé — PASS.
- **Ré-évaluation post-Phase 1** : les contrats produits (suffixe de
  sous-corpus, extension de la règle d'appariement) ne modifient aucun
  comportement existant sans l'option ou les nouvelles commandes — PASS.

## Project Structure

### Documentation (this feature)

```text
specs/002-doublons-split/
├── plan.md              # Ce fichier
├── research.md          # Phase 0 : décisions D1 à D13
├── data-model.md        # Phase 1 : entités Source, Groupe, Bucket, SousCorpus
├── quickstart.md        # Phase 1 : validation sur les jeux réels
├── contracts/
│   ├── cli.md           # Interfaces des 3 commandes + formats de rapports
│   └── file-formats.md  # Suffixe des sous-corpus, appariement étendu
└── tasks.md             # Phase 2 (/speckit-tasks — non créé ici)
```

### Source Code (repository root)

```text
src/corpusbuilder/
├── cli.py          # Étendu : --suppr-doublons, --seuil-doublons ;
│                   #   main_info / main_split pour les nouveaux scripts
├── sources.py      # Source (contexte canonique, texte, précision FR-007)
├── similarity.py   # Shingles 5-mots, Jaccard tronqué ×100, union-find
├── dedup.py        # Détection, choix du gagnant, exclusion, rapport
├── dates.py        # Parsing FR (3 précisions) + buckets calendaires FR-016
├── infocorpus.py   # Rapport auteurs / éditeurs / dates consolidé (FR-020)
├── split.py        # Regroupement par valeur + écriture des sous-corpus
└── (existant) assemble, counter, discovery, models, output, transform,
    validation — réutilisés sans modification de comportement hors nouvelles
    commandes (une seule exception : regex d'appariement des corpus étendue,
    cf. contracts/file-formats.md)

tests/
├── unit/
│   ├── test_similarity.py    # shingles, jaccard, troncature, union-find
│   ├── test_sources.py       # contexte canonique, précision, placeholders
│   ├── test_dedup.py         # règles FR-003/004/006/007, rapport
│   ├── test_dates.py         # 3 précisions, sans-date, choix de tranche
│   └── test_split.py         # slug/suffixe, collisions, multi-auteurs
├── integration/
│   ├── test_dedup_complement1.py   # vérité terrain : 30 groupes contexte
│   ├── test_dedup_complement2.py   # exclusion corpus, alignement matrice
│   ├── test_infocorpus_complement2.py  # 4/29 éditeurs, 23/124 auteurs
│   └── test_split_complement2.py    # réingestion sans rejet (SC-004)

pyproject.toml     # + [project.scripts] info-corpus, corpus-split
```

**Structure Decision**: un module par famille de responsabilité, calqué sur
la structure existante (un module = un domaine du data-model). Les modules
existants ne sont pas réorganisés ; seule la regex `CORPUS_TITLE` de
`discovery.py` est étendue (contrat approuvé dans
`contracts/file-formats.md`) pour accepter le suffixe des sous-corpus.

## Suivi de complexité

> Aucune violation de la Constitution à justifier.
