# Feature Specification: Déduplication des sources et séparation de corpus

**Feature Branch**: `003-doublons-split`

**Created**: 2026-10-27

**Status**: Draft

**Input**: Décision d'assessment `go` de
`.specify/assessments/dedup-corpus-split` (handoff de `decision.md`) :
`--suppr-doublons` à seuil réglable en flux continu, `info-corpus` et
`corpus-split`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Exclure les doublons de la sortie (Priority: P1)

L'utilisateur exécute la commande existante avec l'option `--suppr-doublons`
sur un dossier de documents issus du chunking. L'outil détecte les sources en
doublon (contexte strictement identique, ou similarité de texte au-delà du
seuil), produit le corpus de sortie habituel ne contenant qu'une source par
groupe (la meilleure), laisse les fichiers d'entrée strictement inchangés,
et imprime un rapport terminal complet : chaque groupe de doublons, la règle
de détection, le score de similarité, la source conservée et les sources
exclues.

**Why this priority**: la redondance mesurée (28 % des documents du jeu
d'exemple) dégrade directement le RAG en aval ; c'est le besoin fondateur.

**Independent Test**: exécutable seul sur `Examples/Exemple-complement1` ;
vérifiable en comptant les sources du corpus de sortie, en vérifiant que le
dossier d'entrée est inchangé, et en confrontant le rapport au sol de mesure
établi pendant la recherche (30 groupes à contexte identique).

**Acceptance Scenarios**:

1. **Given** un dossier contenant 232 documents dont 66 partagent un contexte
   strictement identique, **When** l'utilisateur exécute la commande avec
   `--suppr-doublons`, **Then** le corpus de sortie contient exactement une
   source par groupe de doublons, le dossier d'entrée est inchangé, et le
   rapport liste chaque exclusion.
2. **Given** un dossier contenant 4 versions du même article (3 à contexte
   identique + 1 version web plus complète), **When** l'utilisateur exécute
   avec `--suppr-doublons`, **Then** les 3 versions identiques fusionnent en 1
   source, la version web étant conservée comme la plus précise.
3. **Given** un dossier sans aucun doublon, **When** l'utilisateur exécute
   avec `--suppr-doublons`, **Then** le corpus de sortie est identique à celui
   d'une exécution sans l'option et le rapport l'indique explicitement.

---

### User Story 2 - Exclure les doublons des entrées corpus (Priority: P2)

L'utilisateur réingère un corpus (ou plusieurs) avec `--suppr-doublons`.
L'outil regroupe les lignes par source (identifiant de chunking), applique la
même détection, produit le corpus de sortie sans les lignes ni les vecteurs
des sources perdantes, et laisse les corpus d'entrée strictement inchangés.

**Why this priority**: étend la déduplication au second format d'entrée
accepté par l'outil, mesuré nécessaire (1 doublon inter-corpus dans les
exemples).

**Independent Test**: exécutable seul sur `Examples/Exemple-complement2` ;
vérifiable par le nombre de lignes du JSON de sortie et par l'absence de
toute modification des corpus d'entrée.

**Acceptance Scenarios**:

1. **Given** un corpus de 2459 lignes contenant des sources en doublon,
   **When** l'utilisateur exécute avec `--suppr-doublons`, **Then** le corpus
   de sortie ne contient plus les lignes des sources perdantes et la matrice
   reste alignée ligne à ligne avec le JSON, et le corpus d'entrée est
   inchangé.
2. **Given** un corpus sans doublon, **When** l'utilisateur exécute avec
   `--suppr-doublons`, **Then** le corpus de sortie est identique à celui
   d'une exécution sans l'option et le rapport indique zéro exclusion.

---

### User Story 3 - Auditer la composition d'un corpus (Priority: P3)

L'utilisateur exécute `info-corpus` sur un ou plusieurs corpus (fichiers ou
dossiers) et obtient : la liste des auteurs, la liste des éditeurs, et un
tableau temporel à 6 buckets maximum, chacun avec ses effectifs, plus un
bucket dédié aux documents sans date.

**Why this priority**: réponse à un besoin d'audit sans aucune alternative
dans l'outil ; prérequis naturel du découpage.

**Independent Test**: exécutable seul sur `Examples/Exemple-complement2` ;
vérifiable contre les effectifs mesurés en recherche (4 et 29 éditeurs,
23 et 124 auteurs, dates sur 1991-2026).

**Acceptance Scenarios**:

1. **Given** le corpus de 51 sources de l'exemple, **When** l'utilisateur
   exécute `info-corpus` avec le critère éditeurs, **Then** la sortie liste
   4 éditeurs distincts avec leurs effectifs.
2. **Given** un corpus de sources datées de 1995 à 2026, **When**
   l'utilisateur demande la distribution des dates, **Then** la sortie
   présente au plus 6 buckets recouvrant toute la plage, chacun avec son
   effectif, plus un bucket « sans date » si applicable.

---

### User Story 4 - Découper un corpus en sous-corpus (Priority: P4)

L'utilisateur exécute `corpus-split` sur un ou plusieurs corpus avec un
critère (auteurs, éditeurs par défaut, dates). L'outil génère un sous-corpus
par valeur du critère, chacun directement réingérable par la commande
existante.

**Why this priority**: transformation des corpus audités en sous-ensembles
homogènes ; dépend de la même lecture que `info-corpus` mais produit des
fichiers.

**Independent Test**: exécutable seul sur `Examples/Exemple-complement2` ;
vérifiable en réingérant chaque sous-corpus produit sans rejet.

**Acceptance Scenarios**:

1. **Given** un corpus contenant 29 éditeurs distincts, **When**
   l'utilisateur exécute `corpus-split` sur les éditeurs, **Then** chaque
   source se retrouve dans le sous-corpus de son éditeur, et chaque
   sous-corpus est un couple JSON + matrice alignés réingérable sans rejet.
2. **Given** des sources sans date, **When** l'utilisateur découpe par
   dates, **Then** ces sources forment un sous-ensemble dédié.

### Edge Cases

- Que se passe-t-il quand plusieurs sources d'un même groupe ont un contexte
  de précision égale ? (le premier apparu dans l'ordre de traitement gagne)
- Comment traiter une source sans aucun champ contexte ? (considérée comme
  un contexte entièrement vide, comparable aux autres)
- Comment traiter un champ Date dans un format imprévu ? (rangé dans le
  bucket « sans date », signalé dans le rapport)
- Comment traiter une date sans jour (« avril 2025 ») ? (premier jour du
  mois, conformément à la politique utilisateur)
- Comment traiter un dossier d'entrée ne contenant aucun couple valide ?
  (comportement d'erreur existant inchangé)
- Comment traiter un seuil hors bornes 60-100 ? (erreur d'usage, aucun
  traitement)
- Que se passe-t-il si le dossier contient des fichiers .json sans leur
  matrice .npy ? (règles de rejet existantes inchangées, pas de dédup)
- Que se passe-t-il quand un critère de découpe ne produit qu'une seule
  valeur ? (un seul sous-corpus contenant tout, signalé dans le rapport)
- Que se passe-t-il en cas de collision de nom entre deux sous-corpus ?
  (nommage déterministe garantissant l'unicité)
- Que se passe-t-il quand une date tombe exactement sur une borne entre deux
  buckets ? (elle appartient au bucket qui commence à cette date — borne
  gauche incluse, borne droite exclue)

## Requirements *(mandatory)*

### Functional Requirements

Détection et exclusion — `--suppr-doublons` :

- **FR-001**: L'outil DOIT fournir une option `--suppr-doublons` activant la
  déduplication ; sans cette option, le comportement existant de la commande
  est strictement inchangé.
- **FR-002**: Le système DOIT considérer comme source : un document d'entrée
  au format document, ou l'ensemble des lignes partageant le même identifiant
  de chunking dans une entrée au format corpus.
- **FR-003**: Le système DOIT considérer comme doublons deux sources dont le
  champ contexte est strictement identique (tous champs égaux), quel que soit
  le seuil.
- **FR-004**: Le système DOIT considérer comme doublons deux sources dont la
  similarité de texte — mesurée de façon déterministe sur le texte complet de
  chaque source, exprimée en points de 0 à 100 — est supérieure ou égale au
  seuil.
- **FR-005**: Le système DOIT fournir une option `--seuil-doublons N` où N
  est un entier entre 60 et 100, avec 75 comme valeur par défaut ; toute
  valeur hors bornes DOIT produire une erreur d'usage sans aucun traitement
  ni écriture.
- **FR-006**: Le système DOIT regrouper les doublons transitivement : si A
  est en doublon avec B et B avec C, A, B et C forment un seul groupe.
- **FR-007**: Pour chaque groupe, le système DOIT conserver la source au
  contexte le plus précis — le plus de champs renseignés, puis à égalité une
  référence bibliographique renseignée, puis à égalité un titre réel (non
  indicateur de source non identifiée) — et à parfaite égalité la première
  source dans l'ordre de traitement.
- **FR-008**: Le système NE DOIT PAS modifier, réécrire ni supprimer les
  fichiers d'entrée ; les sources perdantes DOIVENT être exclues du corpus de
  sortie assemblé, qui ne contient qu'une source par groupe de doublons.
- **FR-009**: Le système DOIT imprimer un rapport terminal listant, pour
  chaque groupe de doublons : les sources concernées, la règle de détection
  (contexte identique ou similarité), le score de similarité le cas échéant,
  la source conservée et les sources exclues ; le rapport DOIT conclure par
  un bilan chiffré.
- **FR-010**: Le système DOIT appliquer la détection à l'ensemble des sources
  valides de l'exécution en cours, tous dossiers d'entrée confondus ; chaque
  exécution est indépendante et aucune mémoire des exécutions précédentes
  n'est utilisée.
- **FR-011**: Le système DOIT garantir que chaque ligne du JSON de sortie
  reste alignée avec le vecteur de même rang de la matrice, y compris après
  exclusion des doublons.
- **FR-012**: Le système DOIT échouer sans aucune écriture si un des fichiers
  concernés ne peut être lu, ou si le dossier de sortie ne peut être écrit,
  en identifiant le fichier en cause ; de même si aucune source ne subsiste
  après exclusion des doublons.

Audit — `info-corpus` :

- **FR-013**: L'outil DOIT fournir une commande `info-corpus` acceptant un ou
  plusieurs corpus (fichiers ou dossiers) et un argument parmi `all`
  (défaut), `aut`, `edit`, `date` ; tout contenu non corpus DOIT être signalé
  et ignoré.
- **FR-014**: Pour `aut`, le système DOIT lister chaque auteur distinct du
  champ dédié du contexte, avec le nombre de sources qui lui sont rattachées.
- **FR-015**: Pour `edit`, le système DOIT lister chaque éditeur distinct du
  champ dédié du contexte, avec le nombre de sources qui lui sont rattachées.
- **FR-016**: Pour `date`, le système DOIT produire un tableau de buckets
  temporels : la plus petite des tranches (1000, 100, 50, 20, 10, 5, 2 ans,
  1 an, 6 mois) dont le découpage de la plage couverte tient en 6 buckets au
  plus — c'est-à-dire le découpage qui maximise le nombre de buckets sans
  dépasser 6 ; chaque bucket indique ses bornes et le nombre de sources
  qu'il contient.
- **FR-017**: Le système DOIT aligner les buckets sur le calendrier
  (tranches qui débutent aux bornes calendaires naturelles de leur taille).
- **FR-018**: Le système DOIT interpréter les dates au format jour mois
  année (jour paddé ou non) ; une date sans jour DOIT être rangée au premier
  jour du mois ; toute date absente, vide ou non interprétable DOIT être
  comptée dans un bucket dédié « sans date ».
- **FR-019**: Si toutes les dates interprétables tiennent dans une fenêtre
  de 6 mois ou moins, le système DOIT produire exactement 2 buckets : un pour
  les sources datées, un pour les sources sans date.
- **FR-020**: Avec plusieurs corpus en entrée, le système DOIT produire un
  rapport consolidé sur l'union des corpus.

Découpage — `corpus-split` :

- **FR-021**: L'outil DOIT fournir une commande `corpus-split` acceptant un
  ou plusieurs corpus et un critère parmi `aut`, `edit` (défaut), `date`,
  selon le même schéma temporel que `info-corpus`.
- **FR-022**: Le système DOIT générer un sous-corpus par valeur du critère,
  chacun au format corpus de l'outil, directement réingérable par la commande
  existante.
- **FR-023**: Le système DOIT ranger les sources sans valeur pour le critère
  (auteur absent, éditeur absent, date absente ou non interprétable) dans un
  sous-ensemble dédié.
- **FR-024**: Le système DOIT inclure une source multi-auteurs dans le
  sous-corpus de chacun de ses auteurs.
- **FR-025**: Le système DOIT écrire tous les sous-corpus directement dans le
  dossier de sortie demandé, sans sous-dossier ; chaque couple de fichiers
  DOIT porter le titre standard du sous-corpus suivi d'un suffixe reprenant
  la valeur du critère (forme normalisée, 10 caractères au maximum) ; le
  nommage DOIT être déterministe et garantir l'unicité des noms.

### Key Entities *(include if feature involves data)*

- **Source**: unité de déduplication et de comptage — un document d'entrée
  (format document) ou l'ensemble des lignes d'un même identifiant de
  chunking (format corpus).
- **Contexte**: métadonnées d'une source (typologie, auteurs, titre,
  éditeur, date, référence, citation) ; sert à la détection par identité, au
  choix de la source conservée, et aux critères d'audit et de découpage.
- **Doublon**: groupe de sources jugées équivalentes (contexte identique ou
  similarité de texte au-delà du seuil), réduit à une seule source.
- **Bucket temporel**: intervalle calendaire de taille normalisée
  (1000/100/50/20/10/5/2/1 an(s), 6 mois) contenant un effectif de sources.
- **Sous-corpus**: sortie du découpage — couple de fichiers (données
  aplaties + vecteurs alignés) regroupant les sources d'une même valeur du
  critère.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Sur le jeu d'exemple de 232 documents, l'exécution avec
  `--suppr-doublons` au seuil par défaut détecte les 30 groupes de sources au
  contexte strictement identique mesurés en recherche, le corpus de sortie ne
  contenant qu'une source par groupe et le dossier d'entrée restant inchangé.
- **SC-002**: Sur le cas d'école à 4 versions du même article, l'exécution au
  seuil par défaut 75 produit un corpus de sortie contenant 2 sources (les
  3 versions à contexte identique fusionnées ; la version web conservée
  comme la plus précise) ; le rapport DOIT mentionner les paires non
  fusionnées de la bande ambiguë.
- **SC-003**: `info-corpus` sur les deux corpus d'exemple retourne
  exactement 4 et 29 éditeurs distincts, 23 et 124 auteurs distincts, et un
  tableau temporel d'au plus 6 buckets couvrant la plage 1991-2026.
- **SC-004**: Tout sous-corpus produit par `corpus-split` est réingéré par
  la commande existante sans aucun rejet ni erreur.
- **SC-005**: Une exécution complète de chaque commande sur les jeux
  d'exemple (moins de 300 sources) se termine en moins de 30 secondes sur la
  machine de l'utilisateur.
- **SC-006**: Deux exécutions successives sur les mêmes entrées produisent
  des sorties identiques (mêmes fichiers, mêmes rapports), sans réseau ni
  aléa.
- **SC-007**: Toute exclusion effective figure explicitement dans le rapport
  terminal : 100 % des sources exclues de la sortie y sont listées.

## Clarifications

### Session 2026-10-27

- Q: Avec `--suppr-doublons`, l'outil produit-il aussi le corpus de sortie
  habituel à partir des entrées nettoyées ? → A: Oui — l'outil rend une
  sortie classique nettoyée des doublons, **sans altérer les entrées** :
  les fichiers d'entrée ne sont ni modifiés, ni réécrits, ni supprimés.
- Q: Les doublons sont-ils détectés entre toutes les sources de l'exécution,
  dossiers confondus ? → A: Oui — détection sur l'union de toutes les
  entrées de l'exécution en cours ; chaque exécution est indépendante et
  aucune mémoire des exécutions précédentes n'est utilisée.
- Q: Quand toutes les dates tiennent dans une fenêtre de 6 mois ou moins,
  que contiennent les 2 buckets exigés ? → A: Un bucket « avec date »
  (toute la fenêtre) + un bucket « sans date ».
- Q: Comment les sous-corpus de corpus-split sont-ils organisés dans le
  dossier de sortie ? → A: Tous les couples à plat dans le dossier de
  sortie ; le titre du sous-corpus est suivi d'un suffixe reprenant la
  valeur du critère (forme normalisée, 10 caractères au maximum), jamais
  d'un préfixe.
- Q: Un document multi-auteur apparaît-il dans le sous-corpus de chacun de
  ses auteurs lors d'un découpage par auteurs ? → A: Oui — la source
  apparaît dans le sous-corpus de chacun de ses auteurs.

## Assumptions

- « Suppression des doublons » signifie exclusion des sources perdantes du
  corpus de sortie assemblé ; les fichiers d'entrée ne sont jamais modifiés
  ni supprimés (clarification utilisateur du 2026-10-27).
- « Contexte le plus précis » (FR-007) est évalué par le nombre de champs
  renseignés du contexte, puis la présence d'une référence bibliographique,
  puis un titre réel ; l'ordre exact est affinable en planification sans
  changer la structure du besoin.
- La similarité de texte est calculée localement de façon déterministe ;
  l'algorithme exact (mesuré en recherche : similarité de Jaccard sur des
  séquences de mots) est un choix de planification, pas de spécification.
- Les seuls formats de date à supporter sont ceux inventoriés dans les
  exemples : « jour mois année » (jour paddé ou non) et « mois année » ;
  tout autre format va au bucket « sans date ».
- Les sous-corpus produits par `corpus-split` portent des titres générés
  selon les règles existantes de l'outil (consommation du compteur) ; le
  suffixe de valeur du critère (FR-025) est une forme normalisée du libellé
  (casse, séparateurs, accents normalisés) tronquée à 10 caractères, avec
  disambiguisation déterministe en cas de collision entre deux valeurs.
- La bande ambiguë de similarité (scores 60-78 où cohabitent vrais
  doublons et articles distincts mesurés en recherche) est assumée par
  l'utilisateur ; le seuil par défaut 75 en est le compromis, réglable par
  `--seuil-doublons`, et le rapport doit rendre chaque fusion vérifiable.
- Les volumes réels restent de l'ordre de quelques centaines à quelques
  milliers de sources par exécution ; au-delà, un chantier d'optimisation
  serait nécessaire (hors périmètre).
