# Quickstart : valider la concaténation de corpus

Date : 2026-10-08 — Phase 1 du plan (`plan.md`). Guide de validation
exécutable de bout en bout. Contrats : `contracts/cli.md` et
`contracts/file-formats.md`. Modèle de données : `data-model.md`.

## Prérequis

- Python 3.11+ disponible localement ; connexion réseau non requise pour
  l'exécution (uniquement pour l'installation initiale des dépendances).
- Dépôt cloné ; exemples d'entrée : `Examples/Exemple1` (1 couple document),
  `Examples/Exemple2` (3 couples document).

## Installation

```text
pip install -e .
```

Crée le script console `corpus` (numpy installé comme dépendance).

## Scénario 1 — Concaténation basique (P1)

```text
corpus Examples/Exemple1
```

Attendu : code retour 0 ; deux fichiers `output/<9 chiffres>.json` et
`output/<9 chiffres>.npy` portant le même titre ; nombre de lignes du JSON =
nombre de lignes de la matrice ; `counter.txt` apparaît à la racine de
l'outil et contient `0001` (première exécution).

Vérification de l'alignement :

```text
python -c "import json,numpy as np,glob; s=glob.glob('output/*.json')[0];
print(len(json.load(open(s))), np.load(s[:-5]+'.npy').shape)"
```

Attendu : les deux nombres de lignes sont égaux.

## Scénario 2 — Multi-dossiers (P1)

```text
corpus Examples/Exemple1 Examples/Exemple2
```

Attendu : corpus unique ; nombre total de chunks = somme des chunks des 4
couples valides (SC-005) ; occurrence incrémentée dans `counter.txt`
(`0002`).

## Scénario 3 — Réingestion (P3, SC-006)

```text
corpus output --output-folder corpus-fusion
```

Attendu : le corpus fusionné contient l'intégralité des chunks du corpus
réingéré, sans perte ni duplication ; occurrence `0003`.

## Scénario 4 — Rejet d'un couple désynchronisé (P2)

Dans un dossier temporaire, copier un couple de `Examples/Exemple1` et
tronquer le JSON d'un chunk (ou la matrice d'une ligne), puis :

```text
corpus <dossier temporaire>
```

Attendu : code retour 1 avec un message identifiant le fichier ; aucune
sortie écrite ; `counter.txt` inchangé.

## Scénario 5 — Compteur (P2)

- Exécuter deux fois de suite : occurrences consécutives dans les titres et
  dans `counter.txt` (SC-004).
- Corrompre `counter.txt` (ex. contenu `abc`) : la prochaine exécution
  échoue immédiatement, sans écriture (FR-021).
- Supprimer `counter.txt` : la prochaine exécution repart à `0001`.

## Scénario 6 — Tests automatisés

```text
pytest
```

Attendu : suite verte — unitaires (counter, validation, transform,
discovery, assemble) et intégration (exemples réels, réingestion,
avertissements dtype, échecs de dimension).
