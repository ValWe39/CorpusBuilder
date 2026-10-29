# Contrat CLI : `corpus` (options dédup), `info-corpus`, `corpus-split`

Date : 2026-10-27 — Phase 1 du plan (`plan.md`). Décisions D7, D11, D12, D13
de `research.md`. Ce contrat étend `specs/001-corpus-concatenation/
contracts/cli.md` (conventions stdout/stderr, codes retour) sans le modifier.

## Usage

```text
corpus DOSSIER [DOSSIER ...] [--output-folder CHEMIN]
      [--suppr-doublons] [--seuil-doublons N]

info-corpus CIBLE [CIBLE ...] [all | aut | edit | date]

corpus-split CIBLE [CIBLE ...] [aut | edit | date] [--output-folder CHEMIN]
```

## `corpus` — options de déduplication

- `--suppr-doublons` (drapeau) : active la détection et l'exclusion des
  doublons de la sortie. Sans le drapeau, comportement strictement
  inchangé (FR-001).
- `--seuil-doublons N` : entier 60 à 100, défaut 75 ; n'agit qu'avec
  `--suppr-doublons` ; toute valeur hors bornes est une erreur d'usage
  (code 2, aucun traitement, FR-005).
- Portée : toutes les sources valides de l'exécution, dossiers confondus
  (FR-010). Les fichiers d'entrée ne sont jamais modifiés (FR-008).

### Rapport de déduplication (stdout, avec `--suppr-doublons`)

```text
Doublons exclus — groupe 1 (règle : contexte identique)
  conservé : 000003823787100050.json
  exclus : 000003822565460051.json, 000003822565460052.json
Doublons exclus — groupe 2 (règle : similarité 78)
  conservé : 000000141791800070.json
  exclus : 000003822565460146.json
Paires proches non fusionnées (score >= 60 et < 75) :
  74 : 000003822565460155.json <-> 000003823787100154.json
Bilan : 232 sources analysées, 30 groupes, 36 sources exclues,
196 sources conservées
```

- Une source de couple corpus est identifiée par `fichier::chunkingid`.
- La section « Paires proches » est vide (et le reste) si aucune paire ne
  remplit la condition ; elle rend visible les quasi-doublons laissés par
  le seuil (SC-002).
- Le résumé d'assemblage existant (couples valides/rejetés/ignorés,
  corpus écrit) suit le rapport, sans changement.

## `info-corpus` — audit en lecture seule

- `CIBLE` : fichier corpus ou dossier ; les dossiers sont scannés comme
  pour `corpus` ; seuls les couples corpus sont retenus — tout couple
  document ou fichier inconnu est signalé sur stderr et ignoré
  (FR-013).
- Critère positionnel optionnel : `all` (défaut), `aut`, `edit`, `date`.
- Sortie : rapport texte sur stdout, aucune écriture de fichier
  (FR-013 à FR-020). Rapport consolidé sur l'union des corpus (FR-020),
  effectifs comptés en sources.

### Formats de sortie

- `aut` : une ligne par auteur distinct — `Auteur (N sources)`, tri
  alphabétique insensible à la casse ; une source multi-auteurs compte
  +1 par auteur.
- `edit` : idem pour les éditeurs.
- `date` : tableau de buckets — une ligne par bucket
  `AAAA..AAAA (tranche : T) : N sources` ; bornes gauche incluse,
  droite exclusive ; le bucket `sans date : N sources` est toujours
  affiché ; si la plage tient en ≤ 6 mois, exactement deux lignes :
  `avec date` et `sans date` (FR-019) ; en tête : plage couverte.
- `all` : les trois sections à la suite, dans cet ordre.

## `corpus-split` — découpage

- `CIBLE` : corpus (fichiers ou dossiers), mêmes règles d'acceptation
  que `info-corpus`.
- Critère positionnel optionnel : `edit` (défaut), `aut`, `date` —
  buckets identiques à `info-corpus date` (FR-021).
- `--output-folder` : défaut `output`.
- Sortie : un couple `<titre>-<slug>.json` + `.npy` par valeur, à plat
  dans le dossier de sortie (FR-025) ; le titre suit les règles
  existantes (9 chiffres, occurrence du compteur consommée par
  sous-corpus écrit) ; aucun sous-corpus vide n'est écrit ; les sources
  sans valeur forment le sous-corpus `sans-auteur` / `sans-editeur` /
  `sans-date` (FR-023) ; une source multi-auteurs est dupliquée dans le
  sous-corpus de chacun de ses auteurs (FR-024).
- stdout : une ligne par sous-corpus écrit (valeur, slug, effectif,
  chemin) puis un bilan ; stderr : avertissements (couples ignorés,
  dates non interprétées).

## Codes retour (communs aux trois commandes)

- `0` : succès (avertissements non bloquants possibles).
- `1` : erreur d'exécution — corpus illisible, sortie non inscriptible,
  aucune source après exclusion, aucune source valide en entrée.
- `2` : erreur d'usage — arguments invalides, seuil hors 60-100.
- Tous les messages utilisateur en français ; erreurs et avertissements
  sur stderr.
