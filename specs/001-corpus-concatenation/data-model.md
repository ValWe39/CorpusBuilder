# Data Model : Corpus Concaténation (CorpusBuilder)

Date : 2026-10-08 — Phase 1 du plan (`plan.md`). Champs obligatoires marqués
`*`. Conventions : les clés absentes ou nulles sont omises en sortie
(spec, « Clés nulles omises ») ; `ref` est conservée sans renumérotation
(clarification du 2026-10-08).

## Relations

```text
InputFolder 1..* ──< Couple
Couple 1 ── 1 DocumentIndex | CorpusRows (jamais les deux)
Couple 1 ── 1 Matrix (NumPy N×P)
CorpusOutput 1 ── * ChunkRow
CorpusOutput 1 ── 1 Matrix (NumPy N×P, alignée ligne à ligne)
OccurrenceCounter 1 ── 1 CorpusOutput (via le titre)
```

## Entités

### Couple (entrée, abstraite)

- `kind`* : `document` ou `corpus` (déterminé par la structure du JSON,
  décision D4 de `research.md`).
- `json_path`*, `npy_path`* : chemins des deux fichiers appariés.
- `sort_key`* : radical de titre du `.json` (18 premiers caractères pour un
  document, titre à 9 chiffres pour un corpus) — clé du tri FR-014.
- `rows`* : liste ordonnée de `ChunkRow` (aplaties).
- `matrix`* : matrice NumPy N×P, N = `len(rows)` (contrôle FR-006).

### DocumentIndex (racine du JSON d'un couple document)

- `schema_version`* : chaîne (valeur observée « 1.0 ») ; requis pour la
  reconnaissance du format (FR-004).
- `document`* : `DocumentMetadata`.
- `params` : dictionnaire libre ; non repris en sortie (hypothèse spec).
- `chunks`* : liste non vide de `Chunk`, ordre = ordre des vecteurs.

### DocumentMetadata

- `path`* : chemin du document source — repris dans chaque ligne de sortie.
- `title` : repris dans chaque ligne de sortie si présent.
- `structure`, `typologie` : lus pour validation, non repris en sortie.
- `context`, `chunkingid` : repris dans chaque ligne de sortie si présents.

### Chunk (entrée document)

- `ref`* : entier, conservé tel quel en sortie.
- `text`* : chaîne.
- `length`, `boundary`, `part`, `page`, `position_in_part`, `atomic` :
  optionnels ; seuls `part` et `page` sont repris en sortie (FR-011).

### CorpusRows (racine du JSON d'un couple corpus)

- Liste non vide de `ChunkRow` ; structure et ordre préservés (FR-013).

### ChunkRow (ligne plat, entrée corpus et sortie)

- `text`*, `ref`*, `path`* : obligatoires (FR-011).
- `part`, `page`, `title`, `context`, `chunkingid` : optionnels.
- En sortie, chaque ligne embarque les métadonnées de son document
  d'origine.

### Matrix (NumPy)

- Forme N×P : N = nombre de chunks/rows du couple, P = dimension des
  vecteurs (identique entre couples, contrôle bloquant FR-009).
- Dtype : nature des float ; hétérogénéité entre couples = avertissement non
  bloquant (FR-010), promotion automatique au dtype commun lors de
  l'empilement (décision D2).

### CorpusOutput (sortie)

- `title`* : 9 chiffres = 5 chiffres aléatoires (une fois par exécution) +
  occurrence à 4 chiffres (FR-017).
- `rows`* : liste de `ChunkRow`, ordre de collage FR-014 à FR-016.
- `matrix`* : N×P, N = `len(rows)`, i-ème ligne = i-ème row (FR-015).
- Contrôle final avant écriture : égalité N rows/N vecteurs et titres
  identiques `.json`/`.npy` (FR-023).

### OccurrenceCounter (`counter.txt`, racine de l'outil)

- Contenu : exactement 4 chiffres `NNNN` + retour à la ligne final toléré.
- Transitions (FR-018 à FR-021) :
  - fichier absent -> premier numéro utilisé 0001, fichier créé ;
  - fichier lisible `NNNN` -> numéro suivant (9999 -> 0000, nouveau cycle) ;
  - fichier présent mais corrompu -> ERREUR, arrêt immédiat, aucune sortie ;
  - numéro consommé uniquement après écriture réussie des sorties
    (décision D8) — jamais réutilisé en cas d'interruption.

## Règles de validation (rappel exécutoire)

- FR-006 : `len(chunks)` du JSON = N de la matrice, sinon rejet du couple.
- FR-007 : titres appariés selon le format (18 caractères ou 9 chiffres),
  sinon rejet du couple.
- FR-008 : un couple rejeté est exclu du corpus mais n'interrompt pas les
  autres.
- FR-009 : P identique entre couples, sinon échec avant écriture.
- FR-023 : contrôle final N rows = N vecteurs et titres identiques, sinon
  erreur sans écriture.
