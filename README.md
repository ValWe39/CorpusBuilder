# CorpusBuilder

Un outil de concaténation, de déduplication et de découpage de corpus
vectorisés, 100 % local et déterministe.

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

### Concaténation

```text
corpus DOSSIER [DOSSIER ...] [--output-folder CHEMIN]
      [--suppr-doublons] [--seuil-doublons N]
```

- `DOSSIER` : dossiers d'entrée (un ou plusieurs), traités dans l'ordre
  fourni ; chaque dossier peut mélanger des couples au format document
  et au format corpus (sortie d'une exécution précédente).
- `--output-folder CHEMIN` : dossier de sortie (défaut : `output`).
- `--suppr-doublons` : exclut du corpus de sortie les sources en
  doublon (contexte strictement identique, ou similarité de texte au
  seuil) ; les fichiers d'entrée ne sont jamais modifiés. Un rapport
  terminal liste chaque groupe, la source conservée (le contexte le plus
  précis, à égalité la première apparue), les sources exclues et les
  paires proches non fusionnées.
- `--seuil-doublons N` : seuil de similarité de texte, entier 60 à 100
  (défaut : 75) ; toute valeur hors bornes est une erreur d'usage.

Exemples :

```text
corpus Examples/Exemple1
corpus Examples/Exemple1 Examples/Exemple2 --output-folder /tmp/corpus
corpus Examples/Exemple-complement1 --suppr-doublons
corpus Examples/Exemple-complement1 --suppr-doublons --seuil-doublons 80
```

Sortie : un JSON plat (une ligne autoporteuse par chunk) et une matrice
NumPy portant le même titre à 9 chiffres (5 chiffres aléatoires +
numéro d'occurrence persisté dans `counter.txt` à la racine de
l'outil), éventuellement suivi du rapport de déduplication.

### Audit d'un corpus

```text
info-corpus CIBLE [CIBLE ...] [all | aut | edit | date]
```

- `CIBLE` : corpus (fichier ou dossier) ; seuls les couples corpus sont
  retenus, tout le reste est signalé sur stderr et ignoré.
- Critère positionnel optionnel : `all` (défaut), `aut` (auteurs),
  `edit` (éditeurs), `date` (buckets temporels d'au plus 6, alignés sur
  le calendrier ; dates sans jour rangées au premier du mois ; entrée
  « sans date » toujours affichée).
- Rapport consolidé sur l'union des corpus ; lecture seule : aucun
  fichier écrit.

```text
info-corpus Examples/Exemple-complement2/143800006.json edit
```

### Découpage d'un corpus

```text
corpus-split CIBLE [CIBLE ...] [aut | edit | date] [--output-folder CHEMIN]
```

- Critère positionnel optionnel : `edit` (défaut), `aut`, `date` (même
  schéma temporel qu'`info-corpus`).
- Sortie : à plat dans le dossier demandé, un couple
  `<9 chiffres>-<slug>.json` + `.npy` par valeur du critère (slug en
  minuscules sans accents, 10 caractères au maximum) — chaque
  sous-corpus est directement réingérable par `corpus`. Les sources sans
  valeur forment le sous-corpus dédié (`sans-aut`, `sans-edit`,
  `sans-date`) ; une source multi-auteurs apparaît dans le sous-corpus
  de chacun de ses auteurs. Une occurrence du compteur est consommée par
  sous-corpus écrit.

```text
corpus-split Examples/Exemple-complement2 --output-folder /tmp/split
corpus /tmp/split --output-folder /tmp/retour
```

## Tests

```text
pytest
```

## Détails des formats

Les formats d'entrée/sortie et les règles de validation sont contractés
dans `specs/001-corpus-concatenation/contracts/` (concaténation) et
`specs/002-doublons-split/contracts/` (déduplication et découpage).
