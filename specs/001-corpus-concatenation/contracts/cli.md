# Contrat CLI : commande `corpus`

Date : 2026-10-08 — Phase 1 du plan (`plan.md`). Interface exposée à
l'utilisateur ; les formats de fichiers sont contractés dans
`file-formats.md`.

## Usage

```text
corpus DOSSIER [DOSSIER ...] [--output-folder CHEMIN]
```

## Arguments et options

- `DOSSIER` (1..n, requis) : chemins de dossiers d'entrée, traités dans
  l'ordre fourni (FR-001, FR-014). Tout chemin qui n'est pas un dossier
  existant est une erreur d'usage.
- `--output-folder CHEMIN` : dossier de sortie, créé si nécessaire. Défaut :
  `output` (relatif au répertoire courant) (FR-022).

## Comportement

1. Scan de chaque dossier : seuls les couples complets et reconnaissables
   sont retenus ; fichiers orphelins et formats inconnus ignorés et
   signalés (FR-003).
2. Contrôles par couple (bloquants par couple) : FR-006, FR-007 — les
   couples KO sont rejetés avec un message identifiant le fichier (FR-008).
3. Contrôle intercouples : dimension de vecteur P identique — sinon échec
   avant toute écriture avec la liste des couples incompatibles (FR-009) ;
   nature des float hétérogène — avertissement non bloquant (FR-010).
4. Collage déterministe JSON + matrice (FR-014 à FR-016), contrôle final
   (FR-023), écriture des deux fichiers de sortie portant le même titre à
   9 chiffres (FR-017), mise à jour de `counter.txt` (FR-019).

## Flux de sortie

- stdout : résumé d'exécution — nombre de couples valides, rejetés et
  ignorés ; chemins des fichiers produits.
- stderr : erreurs bloquantes et avertissements (rejets par couple,
  dimension incohérente, dtype hétérogène).

## Codes retour

- `0` : succès — corpus écrit (des avertissements non bloquants peuvent
  être présents).
- `1` : erreur d'exécution — aucun couple valide (FR-003/edge cases),
  dimension incohérente (FR-009), compteur corrompu (FR-021), sortie non
  inscriptible ou conflit de titre (edge cases).
- `2` : erreur d'usage — arguments invalides (argparse).

## Exemples

```text
corpus Examples/Exemple1
corpus Examples/Exemple1 Examples/Exemple2
corpus Examples/Exemple2 --output-folder /tmp/corpus-test
```

## Messages

Tous les messages utilisateur sont en français (hypothèse spec). Chaque
rejet identifie le fichier concerné ; chaque échec bloquant liste les
couples en cause et leurs caractéristiques (dimensions, chemins).
