# Concept: Déduplication sûre et introspection/découpage des corpus

- **Slug**: dedup-corpus-split
- **Created**: 2026-10-27
- **Recommended option**: Option A — « Rapport d'abord, sortie nettoyée ensuite
  »

## Options

### Option A — « Rapport d'abord, sortie nettoyée ensuite » (le plus petit sûr)

- **Sketch**: `--suppr-doublons` ne détruit jamais rien. La commande analyse les
  entrées, écrit dans le terminal un rapport des doublons détectés, puis produit
  une **sortie nettoyée** (dossier de couples document ou nouveau corpus, selon
  le mode d'entrée) d'où les doublons sûrs sont exclus — le survivant étant la
  source au contexte le plus précis, à égalité la première apparue. La détection
  est à deux étages : (1) contexte strictement identique — signal mesuré fiable
  à 100 % sur les exemples ; (2) texte quasi identique à seuil élevé (~0,8,
  standard industrie). Les paires de la **bande ambiguë 0,6-0,8** (où les
  mesures montrent à la fois de vrais doublons web/revue et des articles
  distincts du même sujet) ne sont **pas** supprimées automatiquement : elles
  figurent dans le rapport comme « doublons probables — à confirmer ».
  `info-corpus` est purement en lecture (rapport auteurs / éditeurs / buckets
  temporels) ; `corpus-split` écrit des sous-corpus conformes au format
  existant.
- **Appetite**: medium (budget : quelques semaines tout compris, tests inclus —
  l'échelle des exemples est déjà couverte par des scripts de recherche
  fonctionnels)
- **Trade-offs**:
  - Gagne : zéro risque de perte de données ; le but « zéro faux positif » de
    problem.md est atteignable par construction ; le rapport terminal exigé par
    l'utilisateur est natif.
  - Sacrifie : le cas d'école « Chunké 4 → 1 » n'est atteint qu'à moitié en
    automatique (les 3 versions revue → 1 par identité de contexte ; la fusion
    revue+web à Jaccard 0,75 reste dans la liste « à confirmer », car cette
    bande contient aussi des articles distincts). La suppression physique
    demandée initialement (« supprimer les sources en doublons ») devient une
    exclusion à l'écriture.
  - Risques : l'utilisateur peut juger la liste « à confirmer » trop manuelle si
    elle est longue ; la définition exacte du « contexte le plus précis » doit
    être formalisée en spécification.
- **Rabbit holes**:
  - Chercher à faire disparaître la bande ambiguë par des signaux combinés
    toujours plus fins (même auteur + titre proche + date proche) — chaque
    signal ajouté multiplie les faux positifs mesurables ; c'est exactement le
    rôle du futur affinage LLM (hors périmètre).
  - Mode corpus : la suppression conjointe de lignes JSON et de lignes de
    matrice doit réutiliser le pipeline d'écriture existant, sinon on réinvente
    l'alignement FR-015.
  - corpus-split par auteur (124 valeurs distinctes sur un seul corpus) : la
    prolifération de micro-fichiers doit être bornée par une convention de
    sortie simple, pas paramétrable à l'infini.

### Option B — « Suppression en place, seuil texte unique »

- **Sketch**: `--suppr-doublons` supprime physiquement les fichiers dupliqués du
  dossier d'entrée (ou réécrit le corpus en place), sur la base d'un seul seuil
  de similarité de texte (~0,75, calibré pour capter le cas web/revue). Rapport
  terminal après action.
- **Appetite**: medium
- **Trade-offs**:
  - Gagne : le cas d'école 4 → 1 est entièrement automatique ; interface
    conceptuellement simple (un seuil).
  - Sacrifie : irréversible — les mesures de research montrent que la bande
    0,6-0,8 contient des articles **distincts** (ex. les deux articles « Budget
    2026 » à 0,784, ou deux prises de vue du même sujet par le même auteur à
    0,770) ; tout seuil assez bas pour capter le cas web/revue supprimera aussi
    certains de ces articles. Le but « zéro faux positif » de problem.md est
    **non atteignable** avec un seuil unique.
  - Risques : perte de données utilisateur réelles ; confiance détruite après un
    premier mauvais retrait.
- **Rabbit holes**: corbeille/sauvegarde des fichiers supprimés (il faudra
  réinventer une poubelle) ; réécriture en place du mode corpus avec alignement
  matriciel.

### Option C — « Ne pas construire : scripts ad hoc »

- **Sketch**: statu quo — l'utilisateur continue d'écrire des scripts jetables
  ponctuels (comme ceux produits pendant la recherche) pour dédupliquer ou
  compter les auteurs, corpus par corpus.
- **Appetite**: nul (rien à construire)
- **Trade-offs**:
  - Gagne : zéro maintenance, zéro dette dans l'outil.
  - Sacrifie : non reproductible, non déterministe, aucun rapport standard,
    aucune garantie de conservation « contexte le plus précis » ; la redondance
    (28 % mesurée) continue d'alimenter le RAG ; chaque nouveau corpus repart de
    zéro.
- **Rabbit holes**: aucun — c'est précisément le problème.

## Recommendation

**Option A.** C'est la seule qui satisfait simultanément les trois buts
mesurables de `problem.md` : détection complète du noyau sûr (30 groupes à
contexte identique, 100 % vérifiables sur complement1), zéro faux positif (par
construction : la bande ambiguée n'est jamais supprimée sans confirmation), et
rapport terminal natif. Elle respecte la contrainte « 100 % locale et
déterministe » et prépare l'affinage LLM futur sans le nécessiter. Son principal
sacrifice — le cas revue+web laissé « à confirmer » — est assumé par l'évidence
: aucune donnée de mesure ne permet de séparer automatiquement, sans risque, les
vrais doublons de cette bande des articles distincts du même sujet. Si
l'utilisateur refuse ce compromis, c'est Option B (avec perte de données
possible) ou un affinage LLM (hors périmètre de phase 1) — l'arbitrage lui
revient en `/speckit-assess-decide`.

## Out of Scope (for the recommended option)

- Tout appel LLM ou méthode non déterministe (reporté, intake explicite).
- Suppression physique des fichiers d'entrée ou réécriture en place des corpus
  existants (hors Option B).
- Correction/réécriture des métadonnées (« Nom de la source » reste en l'état ;
  on ne garde que la meilleure source).
- MinHash/LSH ou toute optimisation au-delà du scan par paires (coût mesuré :
  1,1 s pour 232 documents ; justifié jusqu'à quelques milliers).
- Modification de l'outil de chunking amont ou des règles de collage/validation
  existantes (FR-005 à FR-021).
- Détection de doublons inter-corpus dans `--suppr-doublons` en phase 1 (mesuré
  comme possible — 1 cas à Jaccard 1,0 entre les corpus de complement2 — mais
  chaque dossier d'entrée est traité isolément, comme le fait déjà la commande
  `corpus`).

## Assumptions to Validate

- L'utilisateur accepte que « suppression » signifie « exclusion à l'écriture
  d'une sortie nettoyée » plutôt que destruction des fichiers d'entrée (c'est
  l'écart le plus visible avec la demande initiale ; à faire valider en
  /speckit-assess-decide).
- L'utilisateur accepte une liste « doublons probables — à confirmer » pour la
  bande 0,6-0,8 au lieu d'une suppression automatique (le cas d'école Chunké
  descendra à 2 sources, pas 1, sans confirmation manuelle).
- Le jeu de formats de date inventorié (« j mois aaaa » paddé ou non, « mois
  aaaa », absent) couvre le monde réel ; tout format imprévu tombera dans le
  bucket « vide » — prix acceptable selon les décisions enregistrées dans
  problem.md.
- Les volumes réels restent dans la zone « quelques milliers de documents »
  (sinon le scan par paires O(n²) devra être repensé — MinHash/LSH documenté en
  research).
- La règle « contexte le plus précis » peut être formalisée de façon
  déterministe par un ordre de priorité des champs (à préciser en spécification
  ; les exemples suggèrent : Référence remplie > Titre réel (non placeholder) >
  Date > Editeur).
- corpus-split produit un sous-corpus par valeur de critère via le chemin
  d'écriture existant (titre 9 chiffres + compteur) ; l'utilisateur n'a pas
  besoin de contrôle fin du nommage en phase 1.
