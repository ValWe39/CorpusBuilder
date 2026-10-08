---
description: "Liste des tâches pour l'implémentation de la concaténation de corpus"
---

# Tasks: Corpus Concaténation (CorpusBuilder)

**Input**: Design documents from `/specs/001-corpus-concatenation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/cli.md, contracts/file-formats.md, quickstart.md

**Tests**: inclus — la spec définit un « Independent Test » par user story
et plan.md impose une suite pytest (unitaires + intégration). Écrire les
tests listés AVANT l'implémentation de leur story et vérifier leur échec
initial.

**Organization**: tâches groupées par user story (US1..US5 de spec.md),
priorités P1 puis P2 (US2, US4) puis P3 (US 3, US5).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallélisable (fichiers différents, pas de dépendance)
- **[Story]**: user story concernée ; absent en Setup, Foundational et Polish
- Chemins exacts dans chaque description

## Path Conventions

Projet unique : `src/` et `tests/` à la racine du dépôt (cf. plan.md,
« Structure Decision »).

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: initialisation du projet Python et de la structure de tests.

- [x] T001 Créer `pyproject.toml` : packaging du paquet
  `corpusbuilder`, dépendance d'exécution `numpy`, script console
  `corpus` pointant vers `corpusbuilder.cli:main`, configuration pytest
  et ruff (plan.md, Technical Context).
- [x] T002 [P] Créer le squelette du paquet `src/corpusbuilder/__init__.py`
  et `src/corpusbuilder/__main__.py` (délégation vers
  `corpusbuilder.cli.main`, exécutable via `python -m corpusbuilder`).
- [x] T003 [P] Créer le squelette de tests : `tests/unit/__init__.py`,
  `tests/integration/__init__.py` et `tests/integration/conftest.py`
  (fixtures : `Examples/Exemple1` et `Examples/Exemple2` en lecture
  seule, répertoire temporaire isolé pour `counter.txt`, génération de
  couples d'erreur — décision D9 de research.md).

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: infrastructures partagées bloquantes pour toutes les user
stories. Aucune story ne peut démarrer avant la fin de cette phase.

- [x] T004 Implémenter `src/corpusbuilder/models.py` : dataclasses
  `Couple` (kind, json_path, npy_path, sort_key, rows, matrix),
  `Chunk` (ref*, text*, length, boundary, part, page, position_in_part,
  atomic), `DocumentMetadata` (path*, title, structure, typologie,
  context, chunkingid), `ChunkRow` (text*, ref*, path*, part, page,
  title, context, chunkingid) — champs et cardinalités strictement
  conformes à data-model.md.
- [x] T005 [P] Implémenter `src/corpusbuilder/counter.py` : lecture du
  compteur (fichier absent -> premier numéro 0001 ; contenu conforme à
  `^\d{4}$` avec retour à la ligne final toléré, sinon échec rapide sans
  écriture — FR-021), incrément avec cycle 9999 -> 0000 (FR-020),
  persistance par fichier temporaire puis remplacement (décision D6 de
  research.md). Résolution du chemin : racine de l'outil, répertoire
  parent du paquet où réside `pyproject.toml`.
- [x] T006 Implémenter le squelette `src/corpusbuilder/cli.py` :
  argparse `corpus DOSSIERS... [--output-folder CHEMIN]`, DOSSIERS
  requis (1..n), défaut `output` (FR-001, FR-022), codes retour 0/1/2,
  messages en français, résumé sur stdout, erreurs et avertissements
  sur stderr (contracts/cli.md).

## Phase 3: User Story 1 - Concaténer des documents en un corpus unique (P1) — MVP

**Goal**: produire un couple corpus unique (JSON plat + matrice empilée)
à partir d'un ou plusieurs dossiers de couples document valides.

**Independent Test**: `corpus Examples/Exemple1` écrit deux fichiers au
même titre à 9 chiffres, nombre de lignes du JSON = nombre de lignes de
la matrice, `counter.txt` créé avec `0001` (quickstart.md, scénario 1).

### Tests for User Story 1 (écrire d'abord, vérifier l'échec initial)

- [x] T007 [P] [US1] Écrire `tests/integration/test_us1_basic.py` :
  exécution sur `Examples/Exemple1` -> code 0, un `.json` et un `.npy`
  au même titre à 9 chiffres dans `output/`, alignement lignes/vecteurs
  (SC-001), `counter.txt` = `0001`.
- [x] T008 [P] [US1] Écrire `tests/integration/test_us1_multi.py` :
  exécution sur `Examples/Exemple1` puis `Examples/Exemple2` -> corpus
  unique dont le total de chunks = somme des chunks des 4 couples
  valides (SC-005).

### Implementation for User Story 1

- [x] T009 [US1] Implémenter `src/corpusbuilder/discovery.py` : scan
  d'un dossier, appariement des couples document (18 premiers caractères
  du `.json` + `-XXXX.npy`, FR-005), lecture JSON UTF-8 et matrice via
  `numpy.load(..., allow_pickle=False)` (décision D2 de research.md).
- [x] T010 [US1] Implémenter `src/corpusbuilder/transform.py` :
  transformation document -> liste ordonnée de `ChunkRow` (FR-011,
  FR-012) — `text`, `ref` (conservée sans renumérotation), `path`
  obligatoires ; `part`, `page`, `title`, `context`, `chunkingid`
  repris si présents et non nuls ; clés absentes ou nulles omises.
- [x] T011 [US1] Implémenter `src/corpusbuilder/assemble.py` : tri
  déterministe (dossiers dans l'ordre fourni, puis alphabétique du
  radical de titre — FR-014), empilement vertical `numpy.vstack`
  (FR-016), même ordre appliqué au JSON et à la matrice (FR-015).
- [x] T012 [US1] Implémenter `src/corpusbuilder/output.py` : titre à
  9 chiffres = 5 chiffres aléatoires (`secrets`, une fois par exécution
  — décision D7, FR-017) + occurrence issue du compteur ; contrôle
  final avant écriture (nombre de rows = nombre de vecteurs, titres
  identiques — FR-023) ; écriture du `.json` puis du `.npy` ; mise à
  jour de `counter.txt` seulement après écriture réussie (décision D8).
- [x] T013 [US1] Câbler `src/corpusbuilder/cli.py` : pipeline complet
  découverte -> transformation -> assemblage -> écriture, avec création
  du dossier de sortie par défaut `output/` (FR-022).

**Checkpoint**: US1 fonctionnel et testable seul (MVP).

## Phase 4: User Story 2 - Contrôler et rejeter les entrées invalides (P2)

**Goal**: contrôles par couple (bloquants) et intercouples (dimension
bloquante, dtype informatif), avec rejets explicites sans interrompre
les couples valides.

**Independent Test**: un couple désynchronisé (10 chunks / 9 vecteurs)
est rejeté avec message identifiant le fichier, les autres couples sont
traités (quickstart.md, scénario 4 ; spec.md US2).

### Tests for User Story 2

- [x] T014 [P] [US2] Écrire `tests/unit/test_validation.py` : cas par
  couple FR-006/FR-007, rejet sans interruption FR-008, échec de
  dimension FR-009, avertissement dtype FR-010.

### Implementation for User Story 2

- [x] T015 [US2] Implémenter `src/corpusbuilder/validation.py` :
  contrôles par couple — nombre de chunks du JSON = nombre de vecteurs
  (FR-006), correspondance des titres selon le format du couple
  (FR-007), rejet du couple avec message identifiant le fichier sans
  interrompre les autres (FR-008).
- [x] T016 [US2] Étendre `src/corpusbuilder/validation.py` :
  contrôle intercouples — échec avant toute écriture avec liste des
  couples incompatibles et leurs dimensions si P diffère (FR-009) ;
  avertissement non bloquant si les natures de float diffèrent
  (FR-010).
- [x] T017 [US2] Étendre `src/corpusbuilder/discovery.py` et
  `src/corpusbuilder/validation.py` : JSON illisible ou malformé et
  matrice illisible -> rejet du couple avec message identifiant le
  fichier ; fichiers orphelins (`.json` sans `.npy` ou inverse)
  ignorés et signalés, non bloquants (FR-003, Edge Cases).
- [x] T018 [P] [US2] Écrire `tests/integration/test_us2_reject.py` :
  couple désynchronisé -> code 1, message identifiant le fichier,
  aucune sortie écrite, `counter.txt` inchangé ; deux couples de
  dimensions différentes -> échec listant les couples incompatibles.

**Checkpoint**: US1 et US2 fonctionnels indépendamment.

## Phase 5: User Story 4 - Nommer et persister les sorties (P2)

**Goal**: garanties du titre à 9 chiffres et du compteur d'occurrence
persistant, y compris en cas d'interruption ou de corruption.

**Independent Test**: deux exécutions consécutives -> occurrences
consécutives dans les titres et `counter.txt` (SC-004) ; compteur
corrompu -> échec immédiat sans sortie (quickstart.md, scénario 5).

### Tests for User Story 4

- [x] T019 [P] [US4] Écrire `tests/unit/test_counter.py` : compteur à
  `0007` -> numéro `0008` utilisé et persisté ; `9999` -> `0000` ;
  fichier absent -> `0001` ; contenu corrompu -> erreur, aucune écriture
  (FR-018 à FR-021).
- [x] T020 [P] [US4] Écrire
  `tests/integration/test_us4_counter.py` : deux exécutions
  consécutives -> occurrences consécutives (SC-004) ; échec en cours
  d'exécution (sortie non inscriptible) -> numéro non consommé,
  jamais réutilisé ensuite (décision D8, FR-019).

### Implementation for User Story 4

- [x] T021 [US4] Étendre `src/corpusbuilder/output.py` : conflit de
  titre (fichier cible déjà existant) -> échec sans écraser l'existant
  (Edge Cases) ; consommation de l'occurrence strictement après
  écriture réussie des deux fichiers (FR-019).
- [x] T022 [US4] Câbler `src/corpusbuilder/cli.py` : compteur corrompu
  -> échec rapide avant tout traitement, aucune sortie (FR-021).

**Checkpoint**: US1, US2 et US4 fonctionnels indépendamment.

## Phase 6: User Story 3 - Réingérer des corpus existants (P3)

**Goal**: accepter en entrée les couples au format corpus et les mixer
avec des couples document dans la même exécution.

**Independent Test**: deux corpus produits sont fusionnés en un corpus
plus grand sans perte ni duplication (SC-006 ; quickstart.md, scénario
3).

### Tests for User Story 3

- [x] T023 [P] [US 3] Écrire
  `tests/integration/test_us_3_reingestion.py` : fusion de deux corpus
  produits -> intégralité des chunks sans perte ni duplication (SC-006)
  ; dossier mixte documents + corpus -> collage déterministe.

### Implementation for User Story 3

- [x] T024 [US 3] Étendre `src/corpusbuilder/discovery.py` : détection
  du format par structure (racine objet avec `schema_version`,
  `document`, `chunks` = document ; racine tableau = corpus — décision
  D4) et appariement corpus par titre à 9 chiffres strictement
  identique (FR-005, FR-007).
- [x] T025 [US 3] Étendre `src/corpusbuilder/transform.py` :
  conservation de la structure et de l'ordre des lignes des corpus
  réingérés (FR-013).
- [x] T026 [US 3] Étendre `src/corpusbuilder/assemble.py` : collage mixte
  documents + corpus avec la même règle de tri et le même ordre
  JSON/matrice (FR-002, FR-014 à FR-016).

**Checkpoint**: toutes les stories P1/P2/P3 de lecture implémentées.

## Phase 7: User Story 5 - Choisir le dossier de sortie (P3)

**Goal**: sortie par défaut `output/` créée si nécessaire, ou dossier
désigné via `--output-folder`, avec échec propre si non inscriptible.

**Independent Test**: exécution avec et sans `--output-folder` place les
sorties au bon endroit (spec.md US5).

### Tests for User Story 5

- [x] T027 [P] [US5] Écrire
  `tests/integration/test_us5_output_folder.py` : sans option -> sorties
  dans `output/` créé ; avec `--output-folder` -> sorties dans le
  dossier désigné créé si nécessaire (FR-022).

### Implementation for User Story 5

- [x] T028 [US5] Étendre `src/corpusbuilder/output.py` et
  `src/corpusbuilder/cli.py` : résolution et création du dossier de
  sortie ; chemin non inscriptible -> échec rapide avec message
  explicite, aucune sortie partielle (Edge Cases).

**Checkpoint**: US1 à US5 fonctionnels indépendamment.

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: validation transverse et finitions.

- [x] T029 [P] Exécuter les 6 scénarios de
  `specs/001-corpus-concatenation/quickstart.md` sur les exemples réels
  et consigner les résultats attendus/obtenus.
- [x] T030 [P] Mettre à jour le README du dépôt : installation
  (`pip install -e .`), usage CLI (`corpus`, `--output-folder`),
  formats d'entrée/sortie en renvoi vers
  `specs/001-corpus-concatenation/contracts/`.
- [x] T031 Vérifier la performance : exécution complète sur
  `Examples/` en moins de 30 s (SC-007).
- [x] T032 Nettoyage transverse : `ruff check` et `ruff format` sur
  `src/` et `tests/`, `pre-commit run --all-files` au vert.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sans dépendance, démarrage immédiat.
- **Foundational (Phase 2)**: dépend de Phase 1 — BLOQUE toutes les
  stories.
- **User Stories (Phases 3-7)**: dépendent de Phase 2 ; ensuite
  parallélisables entre elles, ou séquentielles par priorité
  (US1 -> US2 -> US4 -> US 3 -> US5).
- **Polish (Phase 8)**: dépend de toutes les stories livrées.

### User Story Dependencies

- **US1 (P1)**: démarre après Phase 2 ; sans dépendance vers les autres
  stories.
- **US2 (P2)**: démarre après Phase 2 ; s'appuie sur discovery.py de
  US1 mais reste testable seule.
- **US4 (P2)**: démarre après Phase 2 ; s'appuie sur counter.py et
  output.py déjà présents, testable seule.
- **US 3 (P3)**: démarre après Phase 2 ; étend discovery/transform/
  assemble, testable seule.
- **US5 (P3)**: démarre après Phase 2 ; testable seule.

### Within Each User Story

- Tests d'abord (échec initial vérifié), puis models, puis services,
  puis câblage CLI, puis intégration.
- Une story complète avant de passer à la priorité suivante.

### Parallel Opportunities

- T002 et T003 en parallèle ; T005 et T006 en parallèle après T001 ;
  T007/T008, T014/T018, T019/T020 et T023/T027 en parallèle par paires
  au sein de leur story ; US2, US4, US 3 et US5 en parallèle entre
  équipes après US1.

## Parallel Example: User Story 1

```bash
# Lancer les tests US1 ensemble :
Task: "T007 tests/integration/test_us1_basic.py"
Task: "T008 tests/integration/test_us1_multi.py"

# Puis l'implémentation sur fichiers distincts :
Task: "T009 src/corpusbuilder/discovery.py"
Task: "T010 src/corpusbuilder/transform.py"
Task: "T011 src/corpusbuilder/assemble.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Compléter Phase 1 (Setup) et Phase 2 (Foundational).
2. Compléter Phase 3 (US1) — tests T007/T008 écrits et rouges d'abord.
3. **STOP et VALIDER** : US1 testé seul via quickstart.md scénario 1.

### Incremental Delivery

1. Setup + Foundational -> socle prêt.
2. US1 -> test indépendant -> MVP.
3. US2 -> test indépendant -> rejets fiables.
4. US4 -> test indépendant -> nommage et compteur garantis.
5. US 3 -> test indépendant -> réingestion.
6. US5 -> test indépendant -> dossier de sortie.
7. Phase 8 -> validation quickstart, README, performance.

## Notes

- [P] = fichiers différents, pas de dépendance envers une tâche
  incomplète.
- [Story] = traçabilité vers spec.md.
- Les contraintes citées (FR-xxx, SC-xxx, D x) renvoient à spec.md,
  research.md et data-model.md — les respecter verbatim.
- Committer après chaque tâche ou groupe logique ; valider à chaque
  checkpoint de story.
