# Quickstart : valider la déduplication et la séparation de corpus

Date : 2026-10-27 — Phase 1 du plan (`plan.md`). Guide de validation
exécutable de bout en bout sur les jeux réels (exigence de la spec) :
`Examples/Exemple-complement1` (déduplication, entrées document — 232
sources, vérité terrain mesurée) et `Examples/Exemple-complement2`
(déduplication des entrées corpus, `info-corpus`, `corpus-split` — 51 et
232 sources). Contrats : `contracts/cli.md`, `contracts/file-formats.md`.

## Prérequis

- Python 3.11+ local ; pas de réseau requis à l'exécution.
- Dépôt cloné ; `pip install -e .` (crée `corpus`, `info-corpus`,
  `corpus-split`).
- Les commandes ci-dessous partent de la racine du dépôt.

## Scénario 1 — Déduplication des entrées document (P1)

Empreinte du dossier d'entrée, exécution, vérifications :

```text
git hash-object Examples/Exemple-complement1/*.json | sort > /tmp/avant.txt
corpus Examples/Exemple-complement1 --output-folder /tmp/out1 \
  --suppr-doublons
git hash-object Examples/Exemple-complement1/*.json | sort > /tmp/apres.txt
diff /tmp/avant.txt /tmp/apres.txt
```

Attendu : code retour 0 ; `diff` vide (aucune entrée modifiée, FR-008) ;
le rapport stdout affiche des « Doublons exclus — groupe N » ; le bilan
compte 232 sources analysées et strictement moins de 232 conservées ;
la section « Paires proches non fusionnées » n'est pas vide (quasi-doublons
web/revue à 74, SC-002).

Vérification du noyau sûr (vérité terrain, FR-003) :

```text
corpus Examples/Exemple-complement1 --output-folder /tmp/out1b \
  --suppr-doublons --seuil-doublons 100
```

Attendu : à seuil 100, les 30 groupes à contexte strictement identique
mesurés en recherche sont tous détectés (certains textes parfaitement
identiques fusionnent aussi, à score 100) ; au total : 35 groupes,
42 sources exclues, 190 sources conservées — garde-fou de calibrage
(mesures de research.md).

## Scénario 2 — Déduplication des entrées corpus (P2)

```text
corpus Examples/Exemple-complement2 --output-folder /tmp/out2 \
  --suppr-doublons
```

Attendu : les corpus d'entrée sont inchangés ; le corpus de sortie
regroupe les sources par `chunkingid` et exclut les doublons — au moins
le doublon inter-corpus mesuré (la source présente à la fois dans
`059650007.json` et `143800006.json` n'apparaît qu'une fois) ; la
section « Paires proches » du rapport liste les quasi-doublons non
fusionnés. Vérification d'alignement (contrat 001, FR-023) :

```text
python -c "import json,numpy as np,glob;
s=glob.glob('/tmp/out2/*.json')[0];
print(len(json.load(open(s))), np.load(s[:-5]+'.npy').shape[0])"
```

Attendu : les deux nombres sont égaux.

## Scénario 3 — Audit d'un corpus (P3)

```text
info-corpus Examples/Exemple-complement2/059650007.json edit
info-corpus Examples/Exemple-complement2/143800006.json aut
info-corpus Examples/Exemple-complement2 date
```

Attendu (effectifs mesurés en recherche, SC-003) : 4 éditeurs distincts
pour le premier corpus (dont l'entrée vide dédiée) ; 124 auteurs distincts
pour le second (dont l'entrée « sans auteur » couvrant 14 sources) ; pour
les dates, au plus 6 buckets couvrant la plage 1991-2026 plus la ligne
« sans date », et un bilan consolidé quand les deux fichiers sont passés
ensemble. `info-corpus` ne crée aucun fichier.

## Scénario 4 — Découpage et réingestion (P4)

```text
corpus-split Examples/Exemple-complement2 edit --output-folder /tmp/split
corpus /tmp/split --output-folder /tmp/retour
```

Attendu : à plat dans `/tmp/split`, un couple de fichiers
`<9 chiffres>-<slug>.json` et `.npy` par éditeur (29 valeurs sur le
grand corpus ; les sources sans éditeur dans le sous-corpus
`sans-editeur`) ; aucun sous-dossier ; noms suffixés, jamais préfixés.
Chaque sous-corpus réingéré sans rejet ni erreur (SC-004) ; le corpus de
retour contient toutes les lignes des sous-corpus (aucune perte) ;
`counter.txt` a consommé une occurrence par sous-corpus écrit.

## Scénario 5 — Déterminisme (SC-006)

```text
corpus Examples/Exemple-complement1 --output-folder /tmp/d1 --suppr-doublons
corpus Examples/Exemple-complement1 --output-folder /tmp/d2 --suppr-doublons
```

Attendu : rapport de déduplication identique au caractère près (hors
chemins de sortie) ; contenus des JSON identiques ; seules les parties
aléatoire et occurrence des titres diffèrent, conformément au contrat
001 (FR-017) — c'est la seule source d'écart admise.

## Scénario 6 — Garde-fous d'erreur

```text
corpus Examples/Exemple-complement1 --suppr-doublons --seuil-doublons 42
info-corpus Examples/Exemple-complement1
```

Attendu : code 2 pour le seuil hors 60-100, aucun fichier écrit ni
consommé ; pour `info-corpus`, les couples document de complement1 sont
signalés sur stderr et ignorés (FR-013) — l'exécution échoue avec le
code 1 (aucun corpus valide en entrée).
