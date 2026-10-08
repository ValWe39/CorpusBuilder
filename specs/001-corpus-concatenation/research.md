# Research : Corpus Concaténation (CorpusBuilder)

Date : 2026-10-08 — Phase 0 du plan (`plan.md`). Chaque décision est motivée
et référencée aux exigences de la spec (`spec.md`).

## D1 — Langage et version

- Decision : Python 3.11+ (minimum 3.10).
- Rationale : écosystème NumPy natif pour le format `.npy` ; stdlib suffisante
  pour JSON et le CLI ; outillage du dépôt déjà Python (ruff, pip-audit).
- Alternatives considered : Rust (maintenance plus lourde pour un outil
  local ponctuel), Node.js (pas d'écosystème NumPy équivalent).

## D2 — Manipulation des matrices NumPy

- Decision : `numpy.load(..., allow_pickle=False)` en lecture,
  `numpy.vstack` pour l'empilement, `numpy.save` en écriture.
- Rationale : lecture/écriture natives du format `.npy` ; `allow_pickle=False`
  empêche l'exécution de code arbitraire embarqué (sécurité locale) ;
  `vstack` préserve l'ordre des lignes.
- Alternatives considered : `numpy.concatenate(axis=0)` (équivalent, moins
  explicite), lecture binaire manuelle (réinvention de NumPy).
- Note dtype : `vstack` promeut automatiquement vers le dtype commun le plus
  large (ex. float32 + float64 -> float64). Le contrôle FR-010 reste
  informatif ; le dtype de sortie est documenté dans le contrat de formats
  (`contracts/file-formats.md`).

## D3 — CLI

- Decision : `argparse` (stdlib) — `corpus DOSSIERS... [--output-folder P]`.
- Rationale : Constitution IV (simplicité) ; deux options ne justifient pas
  une dépendance tierce ; messages d'usage en français.
- Alternatives considered : click, typer (dépendance non justifiée — YAGNI).

## D4 — Distinction document / corpus en entrée

- Decision : le JSON est lu à sa racine — un objet portant les clés
  `schema_version`, `document` et `chunks` est un document ; un tableau
  (liste) est un corpus. Tout le reste est ignoré (FR-003).
- Rationale : distinction structurelle robuste, sans heuristique de nom ;
  cohérente avec les deux règles d'appariement (FR-005, FR-007).
- Alternatives considered : détection par nom de fichier (ambiguïté entre
  titres à 18 caractères et titres à 9 chiffres).

## D5 — Règle d'ordre de collage

- Decision : dossiers traités dans l'ordre fourni par l'utilisateur (FR-014)
  ; au sein d'un dossier, tri alphabétique du radical de titre du `.json`
  (18 premiers caractères pour les documents, titre à 9 chiffres pour les
  corpus) ; le même ordre est appliqué au JSON et à la matrice (FR-015,
  FR-016).
- Rationale : déterministe, reproductible, testable ; le tri des chaînes
  Python est stable et total.
- Alternatives considered : tri par date de fichier (non déterministe entre
  machines), ordre de listing de l'OS (non portable).

## D6 — Compteur d'occurrence

- Decision : fichier `counter.txt` à la racine de l'outil, contenant
  exactement 4 chiffres (`NNNN`). Lecture au démarrage : absent -> 0001 ;
  contenu non conforme à `^\d{4}$` (retour à la ligne final toléré) ->
  échec rapide sans écriture (FR-021). Écriture immédiate après chaque
  document produit (FR-019), via fichier temporaire puis remplacement.
- Rationale : persistance minimale exigée par la spec ; échec explicite sur
  corruption ; le remplacement atomique évite un compteur tronqué en cas
  d'interruption.
- Alternatives considered : SQLite (hors YAGNI), compteur dérivé des
  fichiers de sortie (non fiable si sortie supprimée).

## D7 — Partie aléatoire du titre

- Decision : 5 chiffres tirés avec le module `secrets` (générateur système,
  non semé), générés une fois par exécution.
- Rationale : unicité des titres entre exécutions ; la reproductibilité n'est
  pas souhaitée (l'occurrence persistante assure la traçabilité).
- Alternatives considered : PRNG semé (briserait l'unicité entre
  exécutions).

## D8 — Écriture des sorties et consommation du compteur

- Decision : construction complète en mémoire (lignes + matrice empilée),
  contrôles FR-023 exécutés avant toute écriture, puis écriture du `.json`
  puis du `.npy`. Le numéro d'occurrence n'est consommé (écrit dans
  `counter.txt`) qu'après le succès de l'écriture des deux fichiers.
- Rationale : aucun fichier partiel en cas d'échec ; cohérent avec les cas
  limites « aucun couple valide », « dimension incohérente » et « sortie non
  inscriptible » (aucun numéro consommé).
- Alternatives considered : écriture en streaming (complexité inutile à
  l'échelle visée — YAGNI).

## D9 — Testabilité et fixtures

- Decision : tests pytest ; `Examples/Exemple1` et `Examples/Exemple2`
  servent de fixtures d'intégration en lecture seule ; les jeux de données
  d'erreur (désynchronisation, titres divergents, dtype mixtes, compteur
  corrompu) sont générés dans des répertoires temporaires par les tests.
- Rationale : les exemples réels valident les formats ; les erreurs ne
  polluent pas le dépôt ; les tests du compteur utilisent un répertoire
  temporaire isolé pour ne pas consommer le compteur réel du développeur.
- Alternatives considered : copies statiques des exemples dans `tests/`
  (duplication inutile).

## NEEDS CLARIFICATION résolus

Aucun marqueur NEEDS CLARIFICATION ne subsiste dans la spec (clarifications
de la session 2026-10-08 intégrées) ; la présente recherche tranche les
choix techniques restés ouverts au niveau du plan.
