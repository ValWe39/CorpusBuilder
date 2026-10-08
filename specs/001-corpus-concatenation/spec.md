# Feature Specification: Corpus Concaténation (CorpusBuilder)

**Feature Branch**: `001-corpus-concatenation`

**Created**: 2026-10-08

**Status**: Draft

**Input**: User description: "Outil 100% local de concaténation d'éléments
vectorisés (couple JSON de métadonnées + matrice NumPy de vecteurs) en vue d'une
utilisation dans un RAG documentaire. Compile plusieurs documents en un couple
unique corpus (JSON plat + matrice NumPy), en garantissant un ordre déterministe
et infailible entre chunks du JSON et lignes de la matrice. CLI `corpus`,
contrôles par couple et intercouples, titres à 9 chiffres avec compteur
d'occurrence persistant, dossier de sortie configurable."

## Clarifications

### Session 2026-10-08

- Q: Dans le corpus de sortie, les identifiants `ref` des chunks doivent-ils
  être renumérotés séquentiellement (1 à N sur tout le corpus) ou conservés tels
  quels depuis chaque document d'origine ? → A: Conserver la `ref` d'origine de
  chaque chunk (pas de renumérotation ; les doublons entre documents sont
  acceptés).
- Q: Pour les couples au format corpus (déjà produits par l'outil), comment le
  JSON et la matrice NumPy doivent-ils être appariés, puisque leur titre à 9
  chiffres ne suit pas le format d'appariement des documents (18 caractères +
  `-XXXX.npy`) ? → A: Deux règles distinctes : documents appariés par les 18
  premiers caractères, corpus appariés par titre à 9 chiffres strictement
  identique.
- Q: Si des couples valides ont des dimensions de vecteur différentes (ex. 1024
  vs 768), que doit faire l'outil après l'avertissement non bloquant, puisque
  l'empilement vertical de matrices de dimensions différentes est physiquement
  impossible ? → A: Échouer avant toute écriture avec un message listant les
  couples incompatibles et leurs dimensions (le contrôle de dimension devient
  bloquant, par dérogation explicite au caractère non bloquant initialement
  prévu).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Concaténer des documents en un corpus unique (Priority: P1)

Un utilisateur possède plusieurs documents découpés en chunks, chacun sous forme
d'un couple JSON (métadonnées + chunks) / matrice NumPy (vecteurs des chunks,
dans le même ordre). Il lance la commande `corpus` en désignant un ou plusieurs
dossiers d'entrée. L'outil lit tous les couples valides, les contrôle, et
produit **un couple unique de sortie** : un JSON plat (tableau de chunks
enrichis de leur document d'origine) et une matrice NumPy (empilement des
vecteurs), dans un ordre strictement aligné. L'utilisateur peut ensuite brancher
ce corpus dans son RAG documentaire.

**Why this priority**: C'est la valeur cœur de l'outil : produire un corpus
unique directement consommable par un RAG, sans désynchronisation entre
métadonnées et vecteurs.

**Independent Test**: Peut être testé seul en lançant `corpus <dossier>` sur les
exemples du dossier `Examples/` et en vérifiant que le JSON et la matrice de
sortie sont alignés (même nombre d'éléments, même ordre).

**Acceptance Scenarios**:

1. **Given** un dossier contenant 2 couples document valides (JSON + .npy),
   **When** l'utilisateur lance `corpus <dossier>`, **Then** l'outil produit
   dans le dossier de sortie un JSON `<titre>.json` et une matrice `<titre>.npy`
   portant le même titre à 9 chiffres, le JSON contenant tous les chunks des
   deux documents, et la matrice le même nombre de vecteurs que de chunks.
2. **Given** le JSON d'entrée du document A contient 12 chunks et sa matrice 12
   vecteurs, du document B 8 chunks et 8 vecteurs, **When** la concaténation est
   exécutée, **Then** le JSON de sortie contient 20 lignes de chunks (les 12 de
   A puis les 8 de B) et la matrice de sortie 20 vecteurs, dans le même ordre.
3. **Given** un dossier contenant des fichiers non conformes (autres extensions,
   JSON sans matrice associée, etc.), **When** l'utilisateur lance la commande,
   **Then** ces fichiers sont ignorés sans faire échouer l'exécution, et seuls
   les couples complets et valides sont intégrés.

---

### User Story 2 - Contrôler et rejeter les entrées invalides (Priority: P2)

L'utilisateur fournit des données dont certaines sont incohérentes. Pour chaque
couple, l'outil vérifie que (a) le nombre de chunks du JSON est strictement égal
au nombre de vecteurs (lignes) de la matrice, et (b) que les titres du `.json`
et du `.npy` correspondent selon la règle du format du couple (18 premiers
caractères pour un document, titre identique à 9 chiffres pour un corpus). Tout
couple en KO est **rejeté en erreur** (exclu du corpus, signalé à
l'utilisateur). Entre couples valides, l'outil vérifie la dimension de vecteur
(P) : en cas d'écart, il échoue avant toute écriture en listant les couples
incompatibles ; la nature des float est vérifiée de façon **non bloquante**
(information de l'utilisateur, poursuite de l'exécution).

**Why this priority**: La fiabilité du RAG dépend de l'intégrité de l'alignement
chunks/vecteurs ; sans ces contrôles, le corpus produit serait corrompu en
silence.

**Independent Test**: Peut être testé en fournissant volontairement un couple
désynchronisé (JSON à 10 chunks, matrice à 9 vecteurs) et en vérifiant que le
couple est rejeté avec un message explicite, tandis que les autres couples sont
traités.

**Acceptance Scenarios**:

1. **Given** un couple dont le JSON compte 10 chunks mais la matrice 9 vecteurs,
   **When** l'outil s'exécute, **Then** le couple est rejeté avec un message
   d'erreur identifiant le fichier concerné, et les autres couples valides sont
   traités.
2. **Given** un couple dont le `.npy` est nommé `ABCDEFGHIJKLMNOPQR-0001.npy` et
   le `.json` `ABCDEFGHJKLMNPQRS.json`, **When** les contrôles s'exécutent,
   **Then** le couple est rejeté (les 18 premiers caractères diffèrent).
3. **Given** deux couples valides dont les matrices ont des dimensions de
   vecteur différentes (ex. 1024 vs 768), **When** l'outil s'exécute, **Then**
   l'outil échoue avant toute écriture avec un message listant les couples
   incompatibles et leurs dimensions (l'empilement de matrices de dimensions
   différentes étant impossible).
4. **Given** deux couples valides dont les matrices utilisent des natures de
   float différentes, **When** l'outil s'exécute, **Then** l'utilisateur est
   informé par un avertissement non bloquant.

---

### User Story 3 - Réingérer des corpus existants (format de sortie) (Priority: P3)

L'utilisateur possède déjà des corpus produits par l'outil (couple JSON plat /
matrice NumPy, format de sortie) et souhaite les fusionner en un corpus plus
grand — ou mixer corpus existants et documents bruts (format d'entrée) au sein
de la même exécution. L'outil applique une logique identique : chaque entrée,
document ou corpus, apporte ses chunks et ses vecteurs dans l'ordre déterministe
du collage, et le résultat est un couple corpus unique au même format.

**Why this priority**: Étend l'outil au cas d'usage incrémental (constitution
progressive d'un corpus), mais n'est nécessaire qu'après le cas d'usage de base.

**Independent Test**: Peut être testé en exécutant deux fois l'outil sur des
documents différents, puis en relançant l'outil sur les deux corpus produits :
le corpus final contient l'ensemble des chunks/vecteurs d'origine dans un ordre
cohérent.

**Acceptance Scenarios**:

1. **Given** deux couples au format corpus (sortie de l'outil), **When**
   l'utilisateur lance `corpus <dossier>`, **Then** l'outil les reconnaît comme
   entrées valides et produit un corpus fusionné unique.
2. **Given** un dossier mélangeant couples au format document (entrée) et
   couples au format corpus (sortie), **When** l'utilisateur lance la commande,
   **Then** les deux types sont intégrés au corpus final selon la même logique
   de collage déterministe.
3. **Given** un couple corpus et un couple document dont les dimensions de
   vecteur diffèrent, **When** l'outil s'exécute, **Then** l'outil échoue avant
   toute écriture avec un message listant les couples incompatibles, comme pour
   les documents.

---

### User Story 4 - Nommer et persister les sorties de façon fiable (Priority: P2)

Les sorties JSON et NumPy portent le **même titre à 9 chiffres** : 5 chiffres
aléatoires générés à chaque exécution, suivis d'un numéro d'occurrence à 4
chiffres. Le numéro d'occurrence est attribué séquentiellement à chaque document
produit, sans doublon au sein d'une exécution, et persisté après chaque document
produit dans un fichier texte à la racine de l'outil contenant uniquement ce
numéro. Le cycle démarre à 0001, progresse d'une unité, et repasse à 0000 après
9999. Si le fichier de compteur est absent, l'exécution repart à 0001 ; s'il est
présent mais illisible ou corrompu, l'outil échoue rapidement avec un message
explicite, sans écrire de sortie.

**Why this priority**: Le titre est la clé de jointure entre JSON et matrice et
la garantie d'unicité du corpus ; sa gestion défaillante rendrait les sorties
inutilisables ou écraserait des corpus existants.

**Independent Test**: Peut être testé en exécutant l'outil deux fois de suite et
en vérifiant (a) que les deux corpus produits portent des titres différents avec
des numéros d'occurrence consécutifs, (b) que le fichier compteur à la racine
contient le dernier numéro utilisé, (c) que la suppression du fichier compteur
fait repartir le numéro à 0001.

**Acceptance Scenarios**:

1. **Given** le fichier compteur contient `0007`, **When** l'outil produit un
   document, **Then** le titre de sortie se termine par `0008` et le fichier
   compteur est mis à jour à `0008`, même en cas d'interruption de l'exécution
   juste après la production du document.
2. **Given** le fichier compteur contient `9999`, **When** l'outil produit un
   document, **Then** le numéro d'occurrence utilisé est `0000` (nouveau cycle).
3. **Given** le fichier compteur est absent, **When** l'outil s'exécute,
   **Then** le premier document produit porte le numéro `0001`.
4. **Given** le fichier compteur est présent mais corrompu (contenu illisible),
   **When** l'outil démarre, **Then** il échoue immédiatement avec un message
   explicite et n'écrit aucune sortie.

---

### User Story 5 - Choisir le dossier de sortie (Priority: P3)

Par défaut, l'outil crée (si nécessaire) un dossier `output` et y écrit les
sorties. L'utilisateur peut désigner un autre chemin via l'option
`--output-folder`.

**Why this priority**: Confort d'utilisation et conformité au principe
d'isolation des chemins ; sans impact sur la logique de collage.

**Independent Test**: Peut être testé en exécutant la commande avec et sans
`--output-folder` et en vérifiant l'emplacement des fichiers produits.

**Acceptance Scenarios**:

1. **Given** aucune option de sortie fournie, **When** l'outil s'exécute avec
   succès, **Then** les sorties sont écrites dans un dossier `output` créé à cet
   effet.
2. **Given** l'option `--output-folder <chemin>`, **When** l'outil s'exécute,
   **Then** les sorties sont écrites dans le dossier désigné, créé s'il n'existe
   pas.

---

### Edge Cases

- **Aucun couple valide** dans l'ensemble des dossiers d'entrée : l'outil ne
  produit pas de sortie et le signale explicitement ; aucun numéro d'occurrence
  n'est consommé.
- **Tous les couples rejetés en erreur de contrôle** : comportement identique —
  échec explicite, pas de sortie, pas de consommation du compteur.
- **JSON illisible ou malformé** pour un couple donné : le couple est rejeté en
  erreur avec un message identifiant le fichier ; les autres couples sont
  traités.
- **Matrice NumPy illisible ou corrompue** : le couple est rejeté en erreur avec
  un message identifiant le fichier.
- **Dossier d'entrée inexistant ou n'étant pas un dossier** : erreur explicite,
  échec rapide ; les chemins fournis doivent obligatoirement être des dossiers.
- **Dossiers contenant des fichiers orphelins** (un `.json` sans `.npy`, ou
  inversement) : ignorés, signalés à l'utilisateur, non bloquant.
- **Chunks avec clés optionnelles absentes** (`page`, `position_in_part`,
  `context`, `chunkingid`, etc.) : les clés absentes ou nulles sont omises dans
  la sortie plutôt que présentes avec une valeur vide.
- **Un seul couple en entrée** : l'outil produit un corpus correspondant à ce
  document seul, transformé au format de sortie.
- **Conflit de titre** (un fichier de sortie existe déjà au même nom) : le
  numéro d'occurrence persistant et les 5 chiffres aléatoires rendent le cas
  improbable ; si malgré tout le fichier cible existe déjà, l'outil échoue sans
  écraser l'existant.
- **Dimension de vecteur incohérente entre couples** : échec avant toute
  écriture, avec un message listant les couples incompatibles et leurs
  dimensions ; aucun numéro d'occurrence n'est consommé.
- **Chemin de sortie non inscriptible** : échec rapide avec un message
  explicite, sans écrire de sortie partielle.

## Requirements *(mandatory)*

### Functional Requirements

#### Lecture et sélection des entrées

- **FR-001**: L'outil DOIT accepter en entrée un ou plusieurs chemins de
  dossiers via la commande `corpus` ; chaque chemin DOIT obligatoirement
  désigner un dossier, sinon l'outil échoue avec un message explicite.
- **FR-002**: L'outil DOIT accepter comme entrée, au sein de ces dossiers, des
  couples au format document (JSON d'index + matrice NumPy) ET des couples au
  format corpus (format de sortie de l'outil), selon une logique de collage
  identique.
- **FR-003**: L'outil DOIT ignorer sans échec tout fichier d'un dossier d'entrée
  qui n'appartient pas à un couple complet et reconnaissable (autre extension,
  JSON orphelin, .npy orphelin).
- **FR-004**: Pour chaque couple document, le JSON d'entrée DOIT être reconnu
  par sa structure : `schema_version`, `document` (path, title, structure,
  typologie, et le cas échéant context, chunkingid), `params`, et `chunks` —
  liste ordonnée dont chaque entrée porte au minimum `ref` et `text`.
- **FR-005**: Pour chaque couple document, la matrice NumPy DOIT être reconnue
  par son titre au format exact : 18 premiers caractères identiques aux 18
  premiers caractères du titre du `.json`, suivis de `-XXXX` (4 caractères) et
  de l'extension `.npy`. Pour chaque couple corpus (format de sortie réingéré),
  le `.json` et le `.npy` DOIVENT porter strictement le même titre à 9 chiffres
  (titre sans extension identique).

#### Contrôles par couple (bloquants — rejet du couple)

- **FR-006**: Pour chaque couple, l'outil DOIT vérifier que le nombre de chunks
  du JSON est exactement égal au nombre de vecteurs (lignes) de la matrice NumPy
  ; en cas d'écart, le couple est rejeté en erreur avec un message identifiant
  le couple concerné.
- **FR-007**: Pour chaque couple, l'outil DOIT vérifier la correspondance des
  titres selon le format du couple : pour un couple document, les 18 premiers
  caractères du titre du `.npy` doivent correspondre aux 18 premiers caractères
  du titre du `.json` ; pour un couple corpus, le titre du `.npy` doit être
  strictement identique à celui du `.json` (9 chiffres) ; en cas d'écart, le
  couple est rejeté en erreur.
- **FR-008**: Un couple rejeté NE DOIT PAS être intégré au corpus de sortie NI
  interrompre le traitement des autres couples valides.

#### Contrôles intercouples (dimension bloquante, nature des float non bloquante)

- **FR-009**: L'outil DOIT vérifier que toutes les matrices à coller ont la même
  dimension de vecteur (P) ; en cas d'écart, l'outil DOIT échouer avant toute
  écriture avec un message listant les couples incompatibles et leurs dimensions
  (l'empilement vertical de matrices de dimensions différentes étant
  impossible).
- **FR-010**: L'outil DOIT informer l'utilisateur, sans bloquer l'exécution, si
  les matrices à coller n'ont pas toutes la même nature de float constituant les
  vecteurs.

#### Transformation au format de sortie

- **FR-011**: Le JSON de sortie DOIT être un tableau plat (JSON array) dont
  chaque ligne représente un chunk et porte : `text` (obligatoire), `ref`
  (obligatoire, conservée telle quelle depuis l'entrée — sans renumérotation,
  les doublons entre documents étant acceptés), `path` du document d'origine
  (obligatoire), et le cas échéant `part`, `page`, `title`, `context`,
  `chunkingid` du document ou du chunk d'origine ; toute clé absente ou nulle
  dans l'entrée est omise dans la sortie.
- **FR-012**: Dans le JSON de sortie, les chunks d'un même document DOIVENT se
  suivre dans leur ordre d'apparition dans le JSON d'entrée de ce document
  (l'ordre de `chunks` est préservé).
- **FR-013**: Pour les entrées au format corpus, l'outil DOIT préserver la
  structure et l'ordre des chunks déjà aplatis.

#### Collage déterministe

- **FR-014**: L'outil DOIT appliquer une règle de collage déterministe,
  identique pour les JSON et pour les matrices : les couples sont ordonnés par
  ordre alphabétique du radical de titre de leur JSON (18 premiers caractères
  pour les documents, titre à 9 chiffres pour les corpus), les dossiers d'entrée
  étant traités dans l'ordre fourni par l'utilisateur ; en cas de titre
  identique entre dossiers distincts, l'ordre des dossiers fournis fait foi.
- **FR-015**: L'ordre de collage DOIT être le même pour le JSON et pour la
  matrice : le i-ème chunk du JSON de sortie correspond obligatoirement à la
  i-ème ligne de la matrice de sortie, et réciproquement.
- **FR-016**: La matrice de sortie DOIT être la concaténation verticale des
  matrices d'entrée dans l'ordre de collage (matrice 1, puis matrice 2, puis
  matrice 3...), sans réordonnancement inverse ou alterné.

#### Titre et compteur d'occurrence

- **FR-017**: Le JSON et la matrice de sortie DOIVENT porter exactement le même
  titre : un nombre à 9 chiffres composé de 5 chiffres générés aléatoirement à
  chaque exécution, suivis du numéro d'occurrence à 4 chiffres.
- **FR-018**: Le numéro d'occurrence DOIT être attribué séquentiellement à
  chaque document produit (un par corpus écrit), sans doublon au sein d'une
  exécution.
- **FR-019**: Le dernier numéro d'occurrence utilisé DOIT être mémorisé dans un
  fichier texte à la racine de l'outil contenant uniquement ce numéro, et
  persisté après chaque document produit : un numéro consommé n'est jamais
  réutilisé, même en cas d'interruption de l'exécution.
- **FR-020**: Le numéro d'occurrence DOIT suivre un cycle : premier usage à
  0001, progression d'une unité par document, retour à 0000 après 9999, puis
  nouveau cycle.
- **FR-021**: Si le fichier de compteur est absent, l'outil DOIT repartir à 0001
  ; s'il est présent mais illisible ou corrompu, l'outil DOIT échouer rapidement
  avec un message explicite, sans écrire de sortie.

#### Sortie et contrôle final

- **FR-022**: Par défaut, l'outil DOIT créer si nécessaire un dossier `output`
  et y inscrire les sorties ; l'option `--output-folder` DOIT permettre à
  l'utilisateur de désigner un autre dossier de sortie.
- **FR-023**: Avant toute écriture, l'outil DOIT vérifier que le nombre de
  chunks du JSON de sortie est égal au nombre de vecteurs de la matrice de
  sortie, et que le titre du `.json` est identique au titre du `.npy` ; en cas
  d'échec, erreur explicite et aucune sortie écrite.
- **FR-024**: L'outil DOIT fonctionner 100 % en local : aucune donnée, résultat
  ou log ne quitte la machine ; aucun appel réseau n'est effectué en exécution
  normale.

### Key Entities *(include if feature involves data)*

- **Couple document (entrée)** : JSON d'index (métadonnées du document + chunks
  ordonnés) + matrice NumPy N×P (un vecteur par chunk, même ordre). Identifié
  par un préfixe de titre commun de 18 caractères.
- **Chunk** : fragment de texte d'un document, portant `ref` (identifiant
  séquentiel), `text`, et des attributs optionnels (`length`, `boundary`,
  `part`, `page`, `position_in_part`, `atomic`).
- **Document (métadonnées)** : `path`, `title`, `structure`, `typologie`, et le
  cas échéant `context`, `chunkingid`.
- **Couple corpus (sortie)** : JSON plat (tableau de lignes de chunks enrichis,
  chaque ligne autoporteuse : text, ref, path, title, part, page, context,
  chunkingid au besoin) + matrice NumPy N×P (un vecteur par ligne du JSON, même
  ordre). Format réingérable comme entrée.
- **Compteur d'occurrence** : fichier texte à la racine de l'outil contenant
  uniquement le dernier numéro d'occurrence à 4 chiffres utilisé.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Pour toute exécution sur des entrées valides, l'alignement
  JSON/matrice de sortie est vérifiable : le nombre de lignes du JSON de sortie
  est strictement égal au nombre de vecteurs de la matrice de sortie (contrôle
  automatique interne, échec explicite sinon).
- **SC-002**: La traçabilité est totale : pour chaque position i dans la matrice
  de sortie, le i-ème chunk du JSON de sortie provient du document et de la
  position d'origine attendus selon l'ordre de collage déterministe documenté
  (vérifiable sur les exemples du dossier `Examples/`).
- **SC-003**: 100 % des couples invalides (désynchronisation chunks/vecteurs ou
  non-correspondance des 18 premiers caractères) sont rejetés avec un message
  d'erreur identifiant le fichier, sans jamais polluer le corpus de sortie.
- **SC-004**: Aucun numéro d'occurrence n'est réutilisé entre deux exécutions
  tant que le cycle 0001-9999/0000 n'est pas complété : vérifiable en comparant
  le fichier compteur avant/après exécution.
- **SC-005**: Une exécution sur les dossiers `Examples/Exemple1` et
  `Examples/Exemple2` produit un corpus unique dont le nombre total de chunks
  est égal à la somme des chunks des documents valides des deux dossiers.
- **SC-006**: Les corpus produits par l'outil sont réingérables : une seconde
  exécution prenant ces corpus en entrée produit un corpus final contenant
  l'intégralité des chunks d'origine, sans perte ni duplication.
- **SC-007**: L'exécution complète sur les exemples fournis (moins d'une
  centaine de documents) se termine en moins de 30 secondes sur une machine
  standard.

## Assumptions

- **Une exécution = un corpus** : une invocation de la commande produit un seul
  couple de sortie (fusion de toutes les entrées valides), et consomme donc un
  seul numéro d'occurrence. Le mécanisme de compteur reste conçu pour supporter
  plusieurs documents produits par exécution.
- **Partie aléatoire du titre** : les 5 chiffres aléatoires sont générés une
  fois par exécution et partagés par l'ensemble des documents produits durant
  cette exécution.
- **Ordre entre dossiers** : les dossiers d'entrée sont traités dans l'ordre
  fourni par l'utilisateur sur la ligne de commande ; au sein d'un dossier, les
  couples sont ordonnés alphabétiquement par les 18 premiers caractères du titre
  du JSON.
- **Entrées document et corpus distinguées par structure** : un couple au format
  corpus (tableau plat de lignes de chunks autoporteuses) est distingué d'un
  couple document (objet avec `schema_version`, `document`, `params`, `chunks`)
  par sa structure JSON, les deux étant acceptés dans les mêmes dossiers ; leurs
  règles d'appariement des fichiers sont distinctes (18 premiers caractères pour
  les documents, titre à 9 chiffres strictement identique pour les corpus).
- **Clés nulles omises** : conformément au schéma d'entrée (clés nulles omises,
  ex. `page`), toute clé absente ou nulle est omise dans la sortie plutôt que
  sérialisée avec une valeur vide.
- **Fusion des métadonnées document** : dans le JSON de sortie, chaque ligne de
  chunk embarque les métadonnées de son document d'origine (`path`, `title`,
  `context`, `chunkingid` le cas échéant) ; les sections `params` et
  `document.structure` des entrées ne sont pas reprises dans la sortie.
- **`ref` préservée** : la `ref` d'origine de chaque chunk est conservée telle
  quelle dans la sortie, sans renumérotation (décision clarifiée) ; les doublons
  de `ref` entre documents sont acceptés, l'unicité d'une ligne du corpus étant
  assurée par sa position (alignement matrice/JSON) et par la combinaison ref +
  document d'origine.
- **Fichier compteur** : le fichier texte du compteur réside à la racine de
  l'outil (là où l'outil est installé), contient uniquement le numéro à 4
  chiffres, et son format de référence est une ligne texte `NNNN`.
- **Langue et plateforme** : l'outil est un CLI local ; les messages utilisateur
  sont en français.
- **Hors périmètre v1** : pas de renumérotation globale des chunks, pas
  d'interface graphique, pas de serveur, pas de télémétrie, pas de compression
  des sorties.
