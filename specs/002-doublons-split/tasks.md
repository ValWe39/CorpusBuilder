---
description: "Task list template for feature implementation"
---

# Tasks: Déduplication et séparation de corpus (CorpusBuilder)

**Input**: Design documents from `/specs/002-doublons-split/`
(plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Prerequisites**: plan.md (structure des modules), spec.md (US-1 à US-4),
research.md (D1 à D13), data-model.md, contracts/cli.md,
contracts/file-formats.md.

**Tests**: inclus — la structure de tests figure dans plan.md et les
scénarios de quickstart.md servent de validation réelle sur
`Examples/Exemple-complement1` et `Examples/Exemple-complement2`.

**Organization**: tâches groupées par user story, chaque story étant
implémentable et testable indépendamment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: exécutable en parallèle (fichiers différents, aucune dépendance)
- **[Story]**: user story concernée (US-1 à US-4)
- Chemins exacts dans chaque description

## Path Conventions

Projet unique : `src/corpusbuilder/`, `tests/` à la racine du dépôt.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: point de départ propre avant toute modification.

- [ ] T001 Vérifier la baseline : `pytest` et `pre-commit run
  --all-files` passent sur l'état courant du dépôt (aucun fix nécessaire,
  sinon s'arrêter et le signaler)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modules partagés par toutes les user stories — sources,
similarité, dates, noyau de déduplication (research.md D1 à D5, D9 ;
data-model.md).

**CRITICAL**: aucune user story ne peut commencer avant la fin de cette
phase.

- [ ] T002 [P] Créer `src/corpusbuilder/sources.py` : construction des
  `Source` (clé : radical document, `chunkingid` pour un corpus —
  regroupement global à l'exécution), contexte canonisé (JSON trié ;
  un contexte absent n'est « jamais égal » à un autre, D2), texte
  complet, précision FR-007 (nombre de champs renseignés parmi les sept,
  puis « référence bibliographique renseignée », puis « titre réel
  (non placeholder "Nom de la source", avec ou sans marquage de gras) »,
  puis date, puis premier apparu), libellé `fichier::chunkingid`
- [ ] T003 [P] Créer `src/corpusbuilder/similarity.py` : tokens
  (`\w+` minuscules Unicode), shingles de 5 mots, score = troncature
  entière de `100 × |A ∩ B| / |A ∪ B|` (0 si un ensemble est vide),
  union-find (D1, D3)
- [ ] T004 [P] Créer `src/corpusbuilder/dates.py` : parsing
  `J mois AAAA` (jour « paddé ou non », mois français accentués) et
  `mois AAAA` (rangé au premier jour du mois) ; tout le reste est
  « sans date » ; choix de tranche — « la plus petite des tranches
  (1000, 100, 50, 20, 10, 5, 2 ans, 1 an, 6 mois) dont le découpage de
  la plage couverte tient en 6 buckets au plus » (FR-016), bornes
  calendaires (gauche incluse, droite exclue), fenêtre ≤ 6 mois →
  « exactement 2 buckets : un pour les sources datées, un pour les
  sources sans date » (FR-019) (D9)
- [ ] T005 [P] Tests unitaires `tests/unit/test_sources.py` : canon
  contexte (égalité stricte, absent jamais égal, placeholder), précision
  (ordre complet D5), libellés
- [ ] T006 [P] Tests unitaires `tests/unit/test_similarity.py` :
  tokenisation, shingles, troncature (0,7487 → 74), union-find
  transitif, texte vide jamais similaire par défaut
- [ ] T007 [P] Tests unitaires `tests/unit/test_dates.py` : 3 formats
  réels inventoriés (paddé « 09 octobre 2026 », non paddé
  « 9 septembre 2026 », sans jour « avril 2025 »), sans-date, choix de
  tranche (plage 1991-2026 → tranche 10 ans, 4 buckets), bornes
  inclusives/exclusives, fenêtre ≤ 6 mois
- [ ] T008 Créer `src/corpusbuilder/dedup.py` : détection (paires à
  contexte identique + paires au score ≥ seuil), groupes union-find
  (FR-006), gagnant par précision puis premier apparu (FR-007),
  structures du rapport (groupes, paires proches 60 ≤ score < seuil,
  bilan) (D3, D5, D11) — dépend de T002, T003

**Checkpoint**: socle prêt — les user stories peuvent commencer.

---

## Phase 3: User Story 1 - Exclure les doublons (Priority: P1) — MVP

**Goal**: `corpus ... --suppr-doublons [--seuil-doublons N]` produit le
corpus de sortie habituel sans les sources perdantes, entrées
inchangées, rapport terminal complet (FR-001 à FR-012).

**Independent Test**: quickstart Scénario 1 sur
`Examples/Exemple-complement1` — entrées inchangées (empreintes), 30
groupes à contexte identique à seuil 100, section « Paires proches »
non vide au défaut 75.

### Tests for User Story 1

- [ ] T009 [P] [US-1] Tests d'intégration
  `tests/integration/test_dedup_complement1.py` : à seuil 100, les 30
  groupes à contexte identique (66 sources) sont réduits à 30 sources
  conservées (196 au total) ; au défaut 75, le rapport contient la
  section « Paires proches non fusionnées » (paires à 74) ; aucune
  entrée modifiée ; sans l'option, sortie identique à l'existant (FR-001)

### Implementation for User Story 1

- [ ] T010 [US-1] Étendre `src/corpusbuilder/cli.py` : options
  `--suppr-doublons` et `--seuil-doublons N` — « N est un entier entre
  60 et 100, avec 75 comme valeur par défaut ; toute valeur hors bornes
  DOIT produire une erreur d'usage sans aucun traitement ni écriture »
  (FR-005, code 2)
- [ ] T011 [US-1] Orchestrer dans `src/corpusbuilder/cli.py` : sources de
  toutes les paires valides de l'exécution (« tous dossiers d'entrée
  confondus », FR-010), détection avant collage, exclusion des couples
  document perdants entiers, échec sans écriture si « aucune source ne
  subsiste après exclusion des doublons » (FR-012) — dépend de T002,
  T003, T008
- [ ] T012 [US-1] Rapport stdout dans `src/corpusbuilder/dedup.py` selon
  contracts/cli.md : trois sections (« Doublons exclus — groupe N »
  avec règle et score, « Paires proches non fusionnées » 60 ≤ score <
  seuil, « Bilan » chiffré) ; le résumé d'assemblage existant suit le
  rapport sans changement (FR-009, SC-007)
- [ ] T013 [US-1] Exécuter `pytest tests/unit tests/integration/
  test_dedup_complement1.py` et corriger jusqu'au vert

**Checkpoint**: US-1 fonctionnelle et testable seule (MVP livrable).

---

## Phase 4: User Story 2 - Exclure les doublons corpus (Priority: P2)

**Goal**: la déduplication s'applique aux sources des couples corpus
(groupées par `chunkingid`, régoupement global), exclusion conjointe des
lignes JSON et des vecteurs, corpus d'entrée inchangés (FR-008,
FR-011).

**Independent Test**: quickstart Scénario 2 sur
`Examples/Exemple-complement2` — doublon inter-corpus mesuré exclu,
alignement JSON/matrice vérifié, entrées inchangées.

### Tests for User Story 2

- [ ] T014 [P] [US-2] Tests d'intégration
  `tests/integration/test_dedup_complement2.py` : la source dupliquée
  inter-corpus (présente dans `059650007.json` et `143800006.json`,
  même `chunkingid`) n'apparaît qu'une fois en sortie ; chaque ligne
  JSON reste alignée avec le vecteur de même rang ; corpus d'entrée
  inchangés ; rapports identifiés par `fichier::chunkingid`

### Implementation for User Story 2

- [ ] T015 [US-2] Étendre l'exclusion dans `src/corpusbuilder/dedup.py`
  et `src/corpusbuilder/cli.py` : couple corpus réduit aux lignes et
  vecteurs des sources survivantes (sélection par indices, matrice par
  lignes), « NE DOIT PAS modifier, réécrire ni supprimer les fichiers
  d'entrée » (FR-008), alignement garanti (FR-011, contrôle final
  FR-023 existant) — dépend de T008, T011

**Checkpoint**: US-1 et US-2 fonctionnelles indépendamment.

---

## Phase 5: User Story 3 - Auditer la composition d'un corpus (Priority: P3)

**Goal**: `info-corpus CIBLE... [all|aut|edit|date]` — rapport
consolidé en lecture seule, aucun fichier écrit (FR-013 à FR-020).

**Independent Test**: quickstart Scénario 3 sur
`Examples/Exemple-complement2` — 4 éditeurs (dont l'entrée vide dédiée)
et 23 auteurs pour `059650007.json`, 29 et 124 pour `143800006.json`,
buckets ≤ 6 couvrant 1991-2026, ligne « sans date » toujours affichée.

### Tests for User Story 3

- [ ] T016 [P] [US-3] Tests d'intégration
  `tests/integration/test_infocorpus_complement2.py` : effectifs
  mesurés (éditeurs, auteurs, entrées vides dédiées), buckets ≤ 6,
  « sans date » toujours présent, consolidation sur l'union (FR-020),
  aucun fichier créé, code 1 quand aucun corpus valide

### Implementation for User Story 3

- [ ] T017 [US-3] Créer `src/corpusbuilder/infocorpus.py` : collecte des
  corpus depuis les cibles (fichiers ou dossiers ; « seuls les couples
  corpus sont retenus », FR-013), effectifs « comptés en sources »
  (multi-auteurs : +1 par auteur), rapports `aut`/`edit`/`date`/`all`
  au format contracts/cli.md — dépend de T002, T004
- [ ] T018 [US-3] Ajouter `main_info` dans `src/corpusbuilder/cli.py` et
  le script `info-corpus` dans `pyproject.toml` ; critère positionnel
  optionnel (`all` par défaut) ; codes retour 0/1/2 selon contracts/
  cli.md — dépend de T017
- [ ] T019 [US-3] Exécuter `pytest tests/integration/
  test_infocorpus_complement2.py` et corriger jusqu'au vert

**Checkpoint**: US-1, US-2 et US-3 fonctionnelles indépendamment.

---

## Phase 6: User Story 4 - Découper un corpus en sous-corpus (Priority: P4)

**Goal**: `corpus-split CIBLE... [aut|edit|date] [--output-folder]` —
sous-corpus suffixés à plats, réingérables, sources sans valeur dans le
sous-ensemble dédié (FR-021 à FR-025).

**Independent Test**: quickstart Scénario 4 sur
`Examples/Exemple-complement2` — couples `<9 chiffres>-<slug>.json`/
`.npy` à plat, 29 éditeurs, réingestion sans rejet, une occurrence du
compteur par sous-corpus écrit.

### Tests for User Story 4

- [ ] T020 [P] [US-4] Tests d'intégration
  `tests/integration/test_split_complement2.py` : noms suffixés jamais
  préfixés (« tronqué à 10 caractères », FR-025), aucun sous-dossier,
  sous-corpus `sans-editeur` pour les sources sans valeur, source
  multi-auteurs dupliquée dans le sous-corpus de chacun de ses auteurs
  (FR-024), réingestion de tous les sous-corpus sans rejet (SC-004),
  compteur consommé par sous-corpus écrit

### Implementation for User Story 4

- [ ] T021 [US-4] Étendre la regex `CORPUS_TITLE` dans
  `src/corpusbuilder/discovery.py` en `^\d{9}(-[a-z0-9-]{1,10})?$`
  (contracts/file-formats.md section 2) — les corpus existants à 9
  chiffres restent valides ; ajouter le test unitaire de réingération
  d'un titre suffixé dans `tests/unit/test_discovery_suffix.py`
- [ ] T022 [US-4] Créer `src/corpusbuilder/split.py` : regroupement par
  valeur (buckets identiques à `info-corpus date`), slug (minuscules
  sans accents, séparateurs « - », « tronqué à 10 caractères »,
  suffixe numérique déterministe en cas de collision), écriture via le
  chemin existant `output.write_corpus` avec titre suffixé, « aucun
  sous-corpus vide n'est écrit », bilan stdout — dépend de T002, T004,
  T021
- [ ] T023 [US-4] Ajouter `main_split` dans `src/corpusbuilder/cli.py` et
  le script `corpus-split` dans `pyproject.toml` ; critère positionnel
  optionnel (`edit` par défaut), `--output-folder` défaut `output` ;
  codes retour 0/1/2 — dépend de T022
- [ ] T024 [US-4] Exécuter `pytest tests/integration/
  test_split_complement2.py` et corriger jusqu'au vert

**Checkpoint**: les quatre user stories sont indépendamment
fonctionnelles.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: documentation, validation réelle de bout en bout,
garde-fous.

- [ ] T025 [P] Mettre à jour `README.md` : usage des trois commandes
  (options de déduplication, critères, sortie), conformément à
  contracts/cli.md
- [ ] T026 Exécuter en réel les scénarios 1 à 6 de `quickstart.md` sur
  `Examples/Exemple-complement1` et `Examples/Exemple-complement2` et
  vérifier chaque valeur attendue (vérité terrain, effectifs,
  réingestion, codes d'erreur)
- [ ] T027 Vérifier le déterminisme (SC-006) : deux exécutions
  identiques — rapports stdout identiques au caractère près, contenus
  JSON identiques, seules les parties aléatoire et occurrence des
  titres diffèrent (contrat 001 FR-017)
- [ ] T028 Passe finale : `pytest` vert au complet, `pre-commit run
  --all-files` (constitution, secrets, lint) vert, aucune ligne de
  plus de 80 caractères dans les nouveaux `.md`, aucun chemin absolu
  dans les fichiers committés

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** : aucune dépendance — démarrage immédiat.
- **Phase 2** : dépend de la Phase 1 — BLOQUE toutes les user stories.
- **Phases 3 à 6 (US-1 à US-4)** : dépendent de la Phase 2 ; chaque story
  est indépendante des autres (US-2 réutilise le pipeline posé par US-1
  mais reste testable seule ; US-3 et US-4 ne dépendent que du socle).
- **Phase 7** : dépend de toutes les stories livrées souhaitées.

### User Story Dependencies

- **US-1 (P1)** : après la Phase 2 uniquement — MVP.
- **US-2 (P2)** : après la Phase 2 ; s'appuie sur l'orchestration
  d'US-1 (T011) sans la modifier.
- **US-3 (P3)** : après la Phase 2 — indépendante.
- **US-4 (P4)** : après la Phase 2 — indépendante ; la réingestion
  suppose la regex étendue (T021) livrée dans la même story.

### Within Each User Story

- Tests d'abord (ils doivent échouer avant l'implémentation).
- Modules avant orchestration CLI ; CLI avant bilans.
- Story complète et verte avant de passer à la suivante.

### Parallel Opportunities

- T002, T003, T004 puis T005, T006, T007 : six tâches à fichiers
  distincts, parallélisables.
- T009, T014, T016, T020 : les quatre suites d'intégration sont
  parallélisables entre stories.
- T025 parallélisable avec T026.

---

## Parallel Example: User Story 1

```bash
# Lancer ensemble les tests de US-1 (après la Phase 2) :
Task: "T009 [P] [US-1] Tests d'intégration test_dedup_complement1.py"
Task: "T005 [P] Tests unitaires tests/unit/test_sources.py"

# Puis l'implémentation séquentielle (même fichier cli.py) :
Task: "T010 [US-1] Options de déduplication dans src/corpusbuilder/cli.py"
Task: "T011 [US-1] Orchestration de l'exclusion avant collage"
Task: "T012 [US-1] Rapport stdout dans src/corpusbuilder/dedup.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 : baseline verte.
2. Phase 2 : socle sources/similarité/dates/dédup.
3. Phase 3 : US-1 complète.
4. **STOP et VALIDER** : quickstart Scénario 1 sur complement1.
5. La déduplication seule livre déjà la valeur fondatrice.

### Incremental Delivery

1. Socle
2. US-1 (dédup documents)
3. US-2 (dédup corpus)
4. US-3 (audit)
5. US-4 (découpage)
6. Phase 7 (validation réelle complète sur les deux jeux d'exemples)

### Parallel Team Strategy

1. L'équipe livre ensemble Phases 1 et 2.
2. Puis : développeur A → US-1 puis US-2 ; développeur B → US-3 ;
   développeur C → US-4 (regex T021 d'abord pour C).

---

## Notes

- [P] = fichiers différents, aucune dépendance en cours.
- [Story] = traçabilité vers spec.md (US-1 à US-4).
- Chaque story est livrable et démontrable seule (checkpoints).
- Vérifier que les tests échouent avant d'implémenter.
- Committer après chaque tâche ou groupe logique.
- Les valeurs attendues des tests proviennent des mesures réelles de
  research.md et quickstart.md — ne pas les inventer.
