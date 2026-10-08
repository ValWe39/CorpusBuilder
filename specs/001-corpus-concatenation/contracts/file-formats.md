# Contrats de formats de fichiers

Date : 2026-10-08 — Phase 1 du plan (`plan.md`). Encodage JSON : UTF-8.
Conventions : `*` = obligatoire ; clés absentes ou nulles omises.

## 1. Couple document (entrée) — JSON d'index

```json
{
  "schema_version": "1.0",
  "document": {
    "path": "C:/.../Corsen_AI.md",
    "title": "Introduction aux Embeddings",
    "structure": "sections",
    "typologie": "documentation",
    "context": "...",
    "chunkingid": "..."
  },
  "params": { "chunk_min": 100 },
  "chunks": [
    {
      "ref": 1,
      "text": "...",
      "length": 981,
      "boundary": "section",
      "part": "Introduction > ...",
      "position_in_part": 1,
      "atomic": false
    }
  ]
}
```

- `chunks` : liste ordonnée ; l'ordre est l'ordre des vecteurs de la
  matrice (FR-004, FR-012).
- Seuls `ref`*, `text`*, `part`, `page` sont repris en sortie (FR-011) ;
  `params`, `length`, `boundary`, `position_in_part`, `atomic`,
  `structure`, `typologie` ne le sont pas.

## 2. Couple document — matrice NumPy

- Titre exact : `<18 caractères>-<XXXX>.npy` où `<18 caractères>` = les 18
  premiers caractères du titre du `.json` (FR-005).
- Matrice N×P : N = nombre de chunks du `.json` (contrôle bloquant FR-006) ;
  i-ème ligne = vecteur du i-ème chunk.

## 3. Couple corpus (entrée réingérée = format de sortie)

- JSON : tableau plat de lignes `ChunkRow` (voir section 5).
- Matrice : même matrice que la sortie d'origine.
- Appariement : `.json` et `.npy` portent strictement le même titre à 9
  chiffres (FR-005, FR-007).

## 4. Titre des sorties

- 9 chiffres : 5 chiffres aléatoires (une fois par exécution) + occurrence
  à 4 chiffres issue de `counter.txt` (FR-017 à FR-021).
- Le `.json` et le `.npy` de sortie portent exactement le même titre.

## 5. Ligne ChunkRow (sortie, et entrée corpus)

```json
{
  "text": "...",
  "ref": 1,
  "path": "C:/.../Corsen_AI.md",
  "part": "Introduction > ...",
  "page": 3,
  "title": "Introduction aux Embeddings",
  "context": "...",
  "chunkingid": "..."
}
```

- `text`*, `ref`*, `path`* obligatoires ; `ref` conservée sans
  renumérotation (clarification 2026-10-08).
- `part`, `page`, `title`, `context`, `chunkingid` repris si présents et non
  nuls à l'origine.
- Ordre : chunks d'un même document consécutifs dans leur ordre d'entrée
  (FR-012) ; corpus réingérés préservés (FR-013).

## 6. Matrice de sortie

- Concaténation verticale des matrices d'entrée dans l'ordre de collage
  (FR-016) ; i-ème ligne = i-ème `ChunkRow` (FR-015).
- Dtype : promotion au dtype commun le plus large en cas de dtypes mixtes
  (avertissement non bloquant FR-010, décision D2 de `research.md`).

## 7. Fichier compteur `counter.txt`

- Racine de l'outil ; contenu : exactement 4 chiffres `NNNN` (retour à la
  ligne final toléré).
- Absent -> premier usage 0001 ; illisible/corrompu -> échec rapide sans
  écriture (FR-021).

## 8. Règle d'ordre de collage (référence)

- Dossiers dans l'ordre fourni par l'utilisateur ; au sein d'un dossier,
  tri alphabétique du radical de titre du `.json` (FR-014). La même règle
  régit JSON et matrice (FR-015).
