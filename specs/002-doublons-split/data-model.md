# Data Model : Déduplication et séparation de corpus (CorpusBuilder)

Date : 2026-10-27 — Phase 1 du plan (`plan.md`). Décisions de référence :
`research.md` D1 à D13. Les entités existantes (`ChunkRow`, `Couple`,
`Candidate` — `specs/001-corpus-concatenation/data-model.md`) sont
inchangées et réutilisées.

## Relations

```text
Couple 1 ──1..* Source (document : 1 source ; corpus : 1 par chunkingid)
Source 1 ──0..1 GroupeDoublon (via union-find)
GroupeDoublon 1 ──1 SourceGagnante ; 0..* SourceExclue
Source 1 ──0..1 Contexte (dict canonisé ; absent => vide)
Source 1 ──0..1 DateInterpretee (3 précisions : jour, mois, aucune)
BucketTemporel 1..6 ──* Source (répartition par date interprétée)
SousCorpus 1 ──1..* Source ; 1 ──1 CoupleFichiers (JSON + matrice)
```

## Entités

### Source (unité de déduplication, de comptage et de découpage)

- `key`* : identité stable — pour un couple document : le radical de titre
  du `.json` (18 premiers caractères) ; pour un couple corpus : la valeur de
  `chunkingid` (regroupement global à l'exécution, D10).
- `kind`* : `document` ou `corpus` (hérité du couple).
- `origin`* : chemin du couple + indices des lignes dans la liste aplatie
  du couple (document : toutes les lignes ; corpus : le sous-ensemble du
  `chunkingid`).
- `text`* : texte complet pour la similarité — concaténation des `text`
  des lignes dans l'ordre.
- `context` : dict canonisé (clés absentes ⇒ chaîne vide) ; `None` si le
  champ est absent du document d'origine (D2).
- `display`* : libellé du rapport — nom de fichier + `chunkingid` le cas
  échéant.

### Contexte (canonique, D2/D5)

- Sept champs inventoriés : `Typologie`, `Auteur(s)` (liste),
  `Titre`, `Editeur`, `Date`, `Référence`, `Citation` — les champs
  supplémentaires observés sont conservés dans la sérialisation canonique
  mais comptent comme un seul champ renseigné de plus.
- `canon`* : sérialisation JSON triée (UTF-8) — clé de l'égalité stricte
  (FR-003). Un contexte absent n'est jamais « égal » à un autre (D2).
- `precision`* : score de départage FR-007 (D5) — nombre de champs
  renseignés, puis référence, puis titre réel (non placeholder
  « Nom de la source », avec ou sans marquage de gras), puis date, puis
  premier apparu.

### Similarité (D1)

- `shingles`* : ensemble des 5-grammes de mots (tokens `\w+` minuscules,
  Unicode) du texte de la source.
- `score(paire)`* : troncature entière de `100 × |A ∩ B| / |A ∪ B|`
  (0 si l'un des ensembles est vide — texte vide jamais déclaré
  similaire par défaut).

### GroupeDoublon (D3, FR-006)

- `members`* : sources de la composante union-find.
- `rule`* : `contexte` (au moins une paire à contexte identique) ou
  `similarite` (toutes les paires retenues par le seuil), avec le score
  maximal de la paire la plus faible reliant le groupe (information du
  rapport).
- `winner`* : membre de précision maximale (D5) ; premier apparu à
  égalité (D4).
- `excluded`* : les autres membres — retirés de l'assemblage (D10).

### DateInterpretee (D9, FR-018)

- `day`, `month`, `year`* : entiers — jour forcé à 1 pour une précision
  « mois année » ; les deux formats paddés ou non sont équivalents.
- `status`* : `jour` | `mois` | `sans-date` (absente, vide ou non
  interprétable).

### BucketTemporel (D9, FR-016 à FR-019)

- `tranche`* : une des neufs tailles normalisées (1000, 100, 50, 20, 10,
  5, 2, 1 an(s), 6 mois) — la plus petite dont le découpage de la plage
  tient en 6 buckets au plus.
- `lower_inclusive`, `upper_exclusive`* : bornes calendaires alignées
  (borne gauche incluse, borne droite exclue).
- `count`* : effectif de sources datées du bucket ; le bucket
  « sans date » est toujours présent dans le tableau, même d'effectif
  nul ; si la plage tient en ≤ 6 mois : exactement 2 buckets
  « avec date » / « sans date ».

### SousCorpus (D8/D13, FR-021 à FR-025)

- `criterion`* : `aut`, `edit` ou `date` (critère de découpage).
- `value`* : valeur du critère (auteur, éditeur, ou borne du bucket) ;
  le bucket « sans valeur » regroupe les sources sans auteur, éditeur ou
  date.
- `slug`* : forme normalisée de `value` (minuscules, sans accents,
  séparateurs « - »), tronquée à 10 caractères ; suffixe numérique
  déterministe en cas de collision.
- `title`* : 9 chiffres (règles existantes : partie aléatoire unique par
  exécution, occurrence du compteur consommée par sous-corpus écrit)
  suivis de « - » et du `slug`.
- `rows`*, `matrix`* : lignes et vecteurs des sources du groupe, ordre de
  traitement conservé (FR-011 : alignement ligne à ligne).

## Règles de validation (issues de la spec)

- Une source sans contexte ne peut être doublon que par le seuil de
  texte (D2, FR-003).
- Le seuil hors 60-100 est une erreur d'usage (FR-005) ; aucun fichier
  n'est écrit en cas d'échec (FR-012).
- Une source multi-auteurs appartient à autant de sous-corpus que
  d'auteurs (FR-024) et compte +1 par auteur dans `info-corpus` (D12).
- Les entrées ne sont jamais modifiées ; les sorties vont exclusivement
  dans le dossier de sortie demandé (FR-008, Constitution).
