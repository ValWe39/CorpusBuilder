# Idea Research: Suppression de doublons et séparation de corpus

- **Slug**: dedup-corpus-split
- **Created**: 2026-10-27
- **Evidence confidence (overall)**: high (mesures locales sur les exemples
  fournis ; prior art externe confirmé mais non approfondi)

## Users & Demand

- **Demande réelle, observée, du propriétaire unique de l'outil** : lors d'une
  recherche documentaire réelle, le même article La Tribune (Jean-Victor
  Semeraro) est apparu 4 fois sous des formes différentes dans `Examples/Exemple
  .json/Chunké` — 3 versions quasi identiques (contexte identique, texte Jaccard
  5-shingles 0,977 à 1,000) et 1 version web (contexte différent sur tous les
  champs, texte Jaccard 0,75). — [source: mesure locale, ce document]
  (confidence: high)
- **Le phénomène n'est pas anecdotique** : dans `Examples/Exemple-complement1`
  (232 documents d'entrée), on mesure **30 groupes de contexte strictement
  identique couvrant 66 documents (28 % du jeu)**, et 112 paires de texte
  Jaccard ≥ 0,5. Dans `Examples/Exemple-complement2` (2 corpus de sortie, 51 +
  232 documents), mêmes 30 groupes de contexte identique dans `143800006.json`
  et **1 doublon inter-corpus** (`059650007.json` contient un document identique
  à Jaccard 1,0 avec un document de `143800006.json`). — [source: mesure locale,
  scripts ad hoc de cette session] (confidence: high)
- **Signal observé, pas seulement déclaré** : les doublons existent déjà dans
  les jeux de données de test de l'utilisateur, donc la fonctionnalité aura une
  utilité immédiate sur ses données réelles. — [source: mesure locale]
  (confidence: high)
- [NEEDS CLARIFICATION: volume maximal attendu en production (nombre de
  documents par exécution) — conditionne le choix du coût algorithmique.]

## Prior Art

### Interne

- **Aucune fonctionnalité de déduplication ni de découpage n'existe dans
  CorpusBuilder** : les modules `src/corpusbuilder/` (assemble, cli, counter,
  discovery, models, output, transform, validation) n'implémentent que le
  collage déterministe de couples JSON+NPY. — [source: lecture de
  `src/corpusbuilder/cli.py` et liste des modules] (confidence: high)
- **La distinction document/corpus est déjà contractée et robuste** : un JSON
  racine-objet avec `schema_version`/`document`/`chunks` = document ; un JSON
  racine-liste = corpus (décision D4 de
  `specs/001-corpus-concatenation/research.md`). Le `chunkingid` identifie de
  façon unique chaque document source et est conservé en sortie. — [source:
  `specs/001-corpus-concatenation/contracts/file-formats.md`, sections 1, 3, 5]
  (confidence: high)
- **Contrainte forte pour la dédup en mode corpus** : la sortie est un couple
  JSON plat + matrice NumPy où la i-ème ligne de la matrice correspond à la
  i-ème ligne JSON (FR-015). Supprimer un document en mode corpus suppose de
  retirer conjointement des lignes JSON **et** des lignes de matrice. — [source:
  `specs/001-corpus-concatenation/contracts/file-formats.md` sections 5-6]
  (confidence: high)
- **La barre d'entrée du projet est posée par la spec 001** : Python 3.10+
  stdlib + NumPy uniquement, argparse, messages en français, déterminisme total
  (décisions D1 à D6 de `specs/001-corpus-concatenation/research.md`). —
  [source: lecture] (confidence: high)

### Externe (recherche web, résultats non ouverts — snippets uniquement)

- **MinHash + shingling (Jaccard) est la méthode de référence pour la dédup
  locale de corpus textuels** : Broder 1997 (signatures min-wise comme
  estimateur non biaisé de la similarité Jaccard sur n-grams/shingles) ;
  utilisée par GPT-3 pour la dédup floue (« MinHashLSH with 10 hashes ») et par
  Milvus pour la dédup de corpus LLM (13-token shingles, seuil Jaccard fixe). —
  [source: recherche web, snippets de
  `https://blog.nelhage.com/post/fuzzy-dedup/` (host: blog.nelhage.com) et
  `https://milvus.io/blog/minhash-lsh-in-milvus-the-secret-weapon-for-fighting-duplicates-in-llm-training-data.md`
  (host: milvus.io), policy: résultats de recherche web, pages non ouvertes]
  (confidence: medium)
- **SimHash (Charikar 2002) et Manku/Jain/Das Sarma (WWW 2007)** : Google
  détectait les quasi-doublons du web (8 milliards de pages) avec des empreintes
  SimHash 64 bits et une distance de Hamming ≤ 3. — [source: recherche web,
  snippets de `https://moz.com/devblog/near-duplicate-detection` (host: moz.com)
  et `https://github.com/codinglombok/LombokSimHash` (host: github.com), policy:
  résultats de recherche web, pages non ouvertes] (confidence: medium)
- **Seuil usuel de Jaccard pour « quasi-doublon » dans l'industrie : ~0,8**
  (GPT-3, Milvus, exemples de pipelines RAG). Le hachage exact (SHA) ne capte
  que les doublons binaires exacts. — [source: recherche web, snippets
  `blog.nelhage.com`, `github.com/codinglombok/LombokSimHash` ; policy:
  résultats de recherche web] (confidence: medium)
- **Architecture type « exact d'abord, flou ensuite »** : SHA exact → skip ;
  SimHash Hamming faible ou MinHash/LSH candidat + Jaccard ≥ seuil →
  quasi-doublon. — [source: recherche web, snippet
  `github.com/codinglombok/LombokSimHash` ; policy: résultats de recherche web]
  (confidence: medium)

## Market & Context

- **Alternative actuelle de l'utilisateur** : déduplication manuelle, dossier
  par dossier (aucune automatisation n'existe aujourd'hui dans l'outil). Coût du
  statu quo : 28 % des documents du jeu d'exemple complement1 sont des doublons
  de contexte, ce qui dégrade tout corpus en aval (RAG) avec des chunks
  redondants. — [source: mesure locale + lecture du code] (confidence: high)
- **Coût de traitement mesuré — la solution déterministe est trivial à cette
  échelle** : un scan par paires complet (26 796 paires sur 232 documents,
  shingles de 5 mots, Jaccard exact) s'exécute en **1,1 s** en pur Python ; 283
  documents (complement2) en **1,4 s**. MinHash/LSH ne se justifierait qu'à
  plusieurs milliers de documents. — [source: mesure locale, cette session]
  (confidence: high)
- **Le besoin de découpage (info-corpus / corpus-split) est servi aujourd'hui
  par rien** : aucun outil local du dépôt ne sait répondre « quels
  auteurs/éditeurs/dates couvre ce corpus ». — [source: lecture du code]
  (confidence: high)

## Data & Constraints

### Mesures sur le cas d'école Chunké (4 versions du même article)

- Les 3 versions « revue » (051, 052, 053) : contexte **strictement identique**
  (Titre « Nom de la source », Editeur « La Tribune », Date « 9 septembre 2026
  », Référence vide) ; texte quasi identique — Jaccard 5-shingles 0,977 à 1,000
  ; écarts type OCR (« 832 » vs « 831 », « du » vs « de », mot « macron »
  absent). — [source: mesure locale] (confidence: high)
- La version « web » (050) : contexte **différent sur tous les champs** (Titre
  complet réel, Editeur « La Tribune (France) », Date « 10 septembre 2026 »,
  Référence remplie) ; texte Jaccard 5-shingles **0,749-0,75** (ratio
  SequenceMatcher sur tokens 0,844). Écarts de contenu : en-tête présent/absent,
  légende photo insérée (~110 tokens), marqueurs « page 1 2 », pied d'article
  avec URL supprimé, réécritures ponctuelles. — [source: mesure locale]
  (confidence: high)
- **Conséquence critique** : l'identité de contexte capte les 3 versions revue
  mais **manque la version web** ; la similarité de texte capte la version web
  mais à un niveau (0,75) où vivent aussi des articles distincts. — [source:
  mesure locale] (confidence: high)

### Mesures sur `Examples/Exemple-complement1` (232 documents d'entrée)

- 0 contexte vide ; **30 groupes de contexte identique (66 documents)** ; sur
  les 43 paires à contexte identique testées, **100 % ont un texte Jaccard ≥
  0,8** — l'identité de contexte est un signal de doublon fiable sur ce jeu. —
  [source: mesure locale] (confidence: high)
- Distribution des paires par similarité texte (Jaccard 5-shingles) : ≥ 0,5 :
  112 ; ≥ 0,6 : 107 ; ≥ 0,7 : 96 ; ≥ 0,8 : 73 ; ≥ 0,9 : 58 ; ≥ 0,99 : 44. —
  [source: mesure locale] (confidence: high)
- **30 paires ont un texte ≥ 0,8 mais un contexte différent** (variantes
  web/revue ou métadonnées divergentes) : la dédup par contexte seul manquerait
  ces cas. — [source: mesure locale] (confidence: high)
- **Bande ambiguë 0,6-0,8** : on y trouve À LA FOIS de vrais doublons (ex. «
  Taxation des holdings » 0,833 ; « Associations et syndicats fustigent la
  méthode Bayrou » 0,803 ; « Bouclier fiscal: Hollande… » 0,787 — mêmes titres,
  mêmes auteurs) ET des articles **distincts** sur le même sujet (ex. 0,784 «
  Budget 2026 : impôts, taxes, exonérations… Ce que les députés… » vs « Impôts,
  taxes, exonérations… Ce que les députés ont déjà voté » ; 0,770 « Les
  prélèvements obligatoires ont baissé sous Macron » vs « Comment les impôts ont
  baissé sous l'ère Macron », même auteur ; 0,723 « La taxe holding suscite la
  polémique » vs « Budget 2026 : cette taxe holding qui suscite déjà la
  polémique »). — [source: mesure locale] (confidence: high)
- Le cas d'école « web vs revue » du Chunké (0,75) tombe pile dans cette bande
  ambiguë. — [source: mesure locale] (confidence: high)

### Mesures sur complement2 (corpus de sortie, 51 + 232 documents)

- Format de sortie confirmé : liste plate de lignes `{text, ref, path, part,
  title, context, chunkingid}` ; `context` est un dict (Typologie, Auteur(s),
  Titre, Editeur, Date, Référence, Citation) présent sur 100 % des lignes ; les
  documents sont regroupables par `chunkingid` (51 et 232 groupes). — [source:
  mesure locale + `contracts/file-formats.md` section 5] (confidence: high)
- Couverture des champs pour info-corpus/corpus-split dans complement2 : dates
  **100 % présentes** au format « j mois aaaa » ; éditeurs : 4 valeurs
  distinctes (1 vide) / 29 valeurs distinctes (0 vide) ; auteurs : 23 / 124
  valeurs distinctes ; documents sans auteur : 9 / 14. — [source: mesure locale]
  (confidence: high)
- **Mise en garde : complement2 n'est PAS représentatif de la variété des
  dates** (note utilisateur 2026-10-27). Inventaire exhaustif de **tous** les
  exemples du dépôt (251 JSON, 486 contextes) : **483 × « j mois aaaa »** (jour
  non paddé), **2 × « 09 octobre 2026 »** (jour paddé — `Examples/Complement`,
  compte-rendus de l'Assemblée nationale), **1 × « avril 2025 »** (précision
  mois-année seulement, sans jour —
  `Examples/Complement/023386082319610021.json`, un ouvrage chez Odile Jacob).
  Par ailleurs `Examples/Exemple1`, `Examples/Exemple2`, `Examples/Exemple3` et
  1 document de `Examples/Complement` n'ont **aucun champ `context`** (donc
  aucune date). — [source: mesure locale, inventaire récursif de `Examples/`,
  cette session] (confidence: high)
- **La précision de la date dépend de la typologie de source** : articles
  web/presse → jour exact ; ouvrages → mois-année (voire année seule attendue
  pour des ouvrages plus anciens, non observée dans les exemples mais plausible)
  ; documents sans contexte → pas de date du tout. — [source: mesure locale +
  ASSUMPTION sur l'année seule] (confidence: medium)
- **1 doublon inter-corpus à Jaccard 1,0** : le document `000003652121260301` de
  `059650007.json` est identique au document `000000142121260142` de
  `143800006.json` — si les deux corpus sont passés ensemble à
  info-corpus/corpus-split, la dédup doit opérer sur l'union. — [source: mesure
  locale] (confidence: high)

### Contraintes techniques héritées

- Déterminisme total exigé (constitution du projet, spec 001) ; pas de LLM en
  phase 1 (contrainte utilisateur explicite). — [source:
  `specs/001-corpus-concatenation/research.md` + intake] (confidence: high)
- En mode corpus, supprimer un document = retirer ses lignes JSON **et** les
  lignes de matrice correspondantes, sans casser l'alignement (FR-015). —
  [source: contracts] (confidence: high)

## Evidence Against the Idea

- **Aucun seuil de texte seul ne sépare proprement vrais et faux doublons sur
  les données réelles** : la bande 0,6-0,8 mélange variantes d'un même article
  et articles distincts du même sujet. Un seuil à 0,8 (standard industrie)
  raterait le cas d'école même de l'utilisateur (version web à 0,75) ; un seuil
  à 0,7 supprimerait des articles distincts (mesures ci-dessus). — [source:
  mesure locale] (confidence: high)
- **La dédup par contexte identique seule ne résout pas le cas motivant la
  demande** : la version web du Chunké a un contexte différent sur tous les
  champs. — [source: mesure locale] (confidence: high)
- **La suppression est destructive et asymétrique selon le mode** : en mode
  document, supprimer = effacer des fichiers d'entrée (.json + .npy) appartenant
  à l'utilisateur ; en mode corpus, supprimer = amputer des lignes JSON et
  matrice d'un corpus déjà assemblé. Sans mode « simulation » (rapport seul), le
  risque de perte de données sur faux positif est réel. — [ASSUMPTION : le
  caractère destructif est inferé de la commande « --suppr-doublons » ; la
  question copie vs suppression physique est ouverte dans l'intake] (confidence:
  medium)
- **Portée de la fonctionnalité 1 en mode corpus non prouvée à coût raisonnable
  par le jeu d'exemples** : les documents y sont reconstituables par
  `chunkingid`, mais aucune mesure de ce document ne couvre la suppression
  conjointe lignes JSON + matrice ; le coût est probablement faible, la
  complexité d'implémentation et le risque d'alignement ne sont pas nuls. —
  [source: contracts + ASSUMPTION] (confidence: medium)
- **Fonctionnalité 2 (split) : le volume de sorties explose linéairement avec le
  critère** — 29 éditeurs ou 124 auteurs distincts dans un seul corpus de 232
  documents ⇒ autant de sous-corpus potentiels (29 à 124 fichiers JSON+NPY),
  dont certains quasi vides (9-14 documents sans auteur). — [source: mesure
  locale] (confidence: high)

## Gaps & Open Questions

- [NEEDS CLARIFICATION: suppression physique des fichiers d'entrée, ou écriture
  d'un dossier « nettoyé » ? L'intake n'est pas explicite ; c'est la question de
  sécurité n° 1.]
- [NEEDS CLARIFICATION: en mode corpus, la suppression produit-elle un nouveau
  corpus (via le pipeline existant, nouveau titre 9 chiffres, consommation de
  counter.txt) ou réécrit-elle le corpus en place ?]
- [NEEDS CLARIFICATION: seuil et règle de décision finale — les mesures
  suggèrent que contexte identique (fiable à 100 % sur le jeu) + texte ≥ ~0,8
  forment le noyau sûr, et que la bande 0,6-0,8 exige soit confirmation
  utilisateur, soit un signal combiné (même auteur + titre proche) ; qui décide
  de la politique : proposition à valider en /speckit-assess-define.]
- [NEEDS CLARIFICATION: la règle « garder le contexte le plus précis » doit être
  formalisée — sur le jeu d'exemple, les versions « Nom de la source »
  (Référence vide, Titre placeholder) sont les moins précises et la version web
  la plus complète, ce qui colle à la règle utilisateur ; ordre de priorité
  exact des champs à définir.]
- [NEEDS CLARIFICATION: un document multi-auteur apparaît-il dans plusieurs
  sous-corpus en corpus-split "aut" (éclatement par auteur), ou un seul ?]
- [NEEDS CLARIFICATION: format de sortie de corpus-split (dossier par valeur ?
  arborescence par bucket de date ? nommage) et gestion du bucket « champ vide
  ».]
- [NEEDS CLARIFICATION: bornes des buckets de date — inclusives/exclusives,
  alignement (millénaires/siècles/années calendaires vs fenêtres glissantes
  depuis la date min), et comportement exact quand les données tiennent en moins
  de 6 mois (« seulement 2 buckets, avec date et date vide » — sémantique à
  préciser).]
- [NEEDS CLARIFICATION: **formats de date hétérogènes confirmés** (note
  utilisateur 2026-10-27) — le parseur doit accepter au minimum : « j mois aaaa
  » (paddé ou non), « mois aaaa » (sans jour), et l'absence totale de date
  (contexte absent ou champ vide). Politique à définir pour les dates à
  précision réduite : « avril 2025 » tombe-t-il dans le bucket du mois d'avril
  (jour par défaut ?), du bucket annuel, ou dans un sous-ensemble « date
  imprécise » dédié ? La référence d'implémentation s'inspirera des anciens
  exemples (`Examples/Exemple1/2/3` : pas de contexte ; `Examples/Complement` :
  les 3 variantes de format).]
- [NEEDS CLARIFICATION: info-corpus sur plusieurs corpus — listes fusionnées
  (union) ou par corpus d'origine ? Un doublon inter-corpus est compté deux fois
  ?]

## Sources

- `Examples/Exemple .json/Chunké/` — mesure directe (lecture seule), host: local
  (confidence: high)
- `Examples/Exemple1/`, `Examples/Exemple2/`, `Examples/Exemple3/`,
  `Examples/Complement/` — mesure directe (lecture seule), host: local, pour
  l'inventaire des formats de date (confidence: high)
- `Examples/Exemple-complement1/` — mesure directe (lecture seule), host: local
  (confidence: high)
- `Examples/Exemple-complement2/` — mesure directe (lecture seule), host: local
  (confidence: high)
- `src/corpusbuilder/cli.py`,
  `specs/001-corpus-concatenation/contracts/{cli,file-formats}.md`,
  `specs/001-corpus-concatenation/research.md` — lecture directe, host: local
- `https://blog.nelhage.com/post/fuzzy-dedup/` (host: blog.nelhage.com, policy:
  recherche web — snippet, page non ouverte)
- `https://milvus.io/blog/minhash-lsh-in-milvus-the-secret-weapon-for-fighting-duplicates-in-llm-training-data.md`
  (host: milvus.io, policy: recherche web — snippet, page non ouverte)
- `https://moz.com/devblog/near-duplicate-detection` (host: moz.com, policy:
  recherche web — snippet, page non ouverte)
- `https://github.com/codinglombok/LombokSimHash` (host: github.com, policy:
  recherche web — snippet, page non ouverte)

*Note méthode : toutes les mesures de similarité locales utilisent des shingles
de 5 mots (tokens normalisés `\w+` en minuscules) et la similarité Jaccard
exacte, calculées en lecture seule pendant cette session ; les scripts ad hoc
n'ont rien modifié dans le dépôt.*
