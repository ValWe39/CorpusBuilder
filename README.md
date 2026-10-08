# CorpusBuilder

Un outil de concaténation de corpus vectorisés, 100 % local et
déterministe.

CorpusBuilder assemble des couples (JSON de métadonnées + matrice NumPy
de vecteurs) — documents découpés en chunks ou corpus déjà aplatis — en
un couple corpus unique, directement consommable par un RAG
documentaire. L'alignement entre les lignes du JSON et les vecteurs de
la matrice est garanti par un ordre de collage déterministe.

## Installation

```text
pip install -e .
```

## Usage

```text
corpus DOSSIER [DOSSIER ...] [--output-folder CHEMIN]
```

- `DOSSIER` : dossiers d'entrée (un ou plusieurs), traités dans l'ordre
  fourni ; chaque dossier peut mélanger des couples au format document
  et au format corpus (sortie d'une exécution précédente).
- `--output-folder CHEMIN` : dossier de sortie (défaut : `output`).

Exemples :

```text
corpus Examples/Exemple1
corpus Examples/Exemple1 Examples/Exemple2 --output-folder /tmp/corpus
```

Sortie : un JSON plat (une ligne autoporteuse par chunk) et une matrice
NumPy portant le même titre à 9 chiffres (5 chiffres aléatoires +
numéro d'occurrence persisté dans `counter.txt` à la racine de
l'outil).

## Tests

```text
pytest
```

## Détails des formats

Les formats d'entrée/sortie et les règles de validation sont contractés
dans `specs/001-corpus-concatenation/contracts/`.
