# Problem Definition: Doublons de sources et maîtrise des corpus

- **Slug**: dedup-corpus-split
- **Created**: 2026-10-27
- **Inputs used**: intake.md + research.md + directives utilisateur du
  2026-10-27 (politique des dates)

## Problem Statement

Le propriétaire de CorpusBuilder assemble des corpus destinés à un RAG
documentaire à partir de documents collectés lors de recherches documentaires ;
ces collectes introduisent des sources dupliquées (mesuré : 28 % des documents
du jeu d'exemple complement1 partagent un contexte strictement identique avec au
moins un autre document), ce qui ennuage le corpus en aval de chunks redondants,
et il ne dispose aujourd' d'aucun moyen local de détecter ces doublons, ni de
savoir qui (auteurs, éditeurs) et quand (dates) composent réellement ses corpus,
ni d'en extraire des sous-ensembles homogènes.

## Affected Users & Stakeholders

- **Users**: le propriétaire du projet, seul utilisateur de l'outil — il
  déduplique aujourd'hui manuellement, document par document, et ne peut pas
  répondre à des questions simples (« quels éditeurs couvre ce corpus ? », « sur
  quelle plage de dates s'étale-t-il ? »). — [source: intake + lecture du code,
  aucune fonctionnalité existante]
- **Stakeholders**: les consommateurs en aval du corpus (le RAG documentaire de
  l'utilisateur), impactés par la redondance des chunks issus de doublons. —
  [ASSUMPTION : l'existence d'un usage RAG en aval est documentée dans le README
  du projet, pas le détail de son impact]
- [NEEDS CLARIFICATION: existence d'autres utilisateurs que le propriétaire — le
  dépôt est public sur GitHub, un usage externe est possible mais non mesuré.]

## Goals

- Éliminer les sources en doublon des entrées documentées, par un procédé 100 %
  local et déterministe, avec un rapport terminal informant l'utilisateur de ce
  qui a été détecté et supprimé.
- La règle de conservation est fixée par l'utilisateur : conserver la source
  dont le contexte est le plus précis (le plus de champs complétés, les plus
  crédibles) ; à égalité, conserver la première apparue. — [source: intake]
- Rendre visible la composition d'un corpus assemblé : liste des auteurs (champ
  « Auteur(s) »), liste des éditeurs (champ « Editeur »), distribution
  temporelle (champ « Date ») en buckets adaptatifs (6 maximum, en maximisant
  leur nombre).
- Permettre de générer des sorties corpus homogènes par critère : auteur,
  éditeur (défaut), date.
- Politique de dates fixée par l'utilisateur (2026-10-27) : jour absent (« avril
  2025 ») → premier jour du mois par défaut ; champ « Date » vide ou contexte
  absent/incomplet → bucket « vide » dédié.

## Non-Goals

- Aucun appel LLM ni méthode non déterministe en phase 1 (l'affinage par LLM est
  explicitement reporté). — [source: intake]
- Pas de déduplication sémantique au-delà des similarités mesurables localement
  (identité de contexte, similarité de texte par shingles).
- Pas de modification de l'outil de chunking amont (MD_Chunking) ni du pipeline
  de concaténation existant au-delà de l'ajout des nouvelles commandes.
- Pas de correction des métadonnées (les contextes « Nom de la source » restent
  tels quels ; on choisit seulement la meilleure source).
- Pas de gestion des corpus hétérogènes en dimension de vecteurs (règles FR-009
  existantes inchangées).

## Success Metrics

- Sur `Examples/Exemple-complement1` (232 documents, vérité terrain mesurée en
  research) : 100 % des 30 groupes à contexte strictement identique détectés ;
  le cas d'école « Exemple .json/Chunké » (4 versions du même article) se réduit
  à 1 seule source conservée — la version web au contexte le plus complet.
  (baseline : 0 % détecté aujourd'hui)
- Zéro faux positif sur les paires d'articles distincts du même sujet
  identifiées en research (ex. les deux articles « Budget 2026 » à Jaccard
  0,784) — suppression sans confirmation humaine interdite sur cette bande
  ambiguë. (baseline : inexistante)
- Sur `Examples/Exemple-complement2` : `info-corpus` retourne 4 et 29 éditeurs
  distincts, 23 et 124 auteurs distincts, et un tableau temporel à ≤ 6 buckets
  avec les bons effectifs — vérifiable à la main. (baseline : aucune
  introspection possible)
- `corpus-split` produit des sous-corpus conformes au contrat existant (JSON
  plat + matrice alignée ligne à ligne, FR-015) — testable par réingestion dans
  `corpus` sans rejet. (baseline : inexistante)
- Coût de traitement à l'échelle des exemples : quelques secondes maximum
  (baseline mesurée : un scan par paires complet de 232 documents prend déjà 1,1
  s en pur Python). (qualitatif + quantitatif)
- Déterminisme total : deux exécutions sur les mêmes entrées produisent des
  sorties identiques. (qualitatif — exigence constitutionnelle du projet)

## Cost of Inaction

- La redondance mesurée (28 % de doublons dans complement1, dont des variantes
  web/revue du même article) continue de polluer chaque corpus assemblé et de
  dégrader le RAG documentaire en aval avec des chunks dupliqués.
- La déduplication reste manuelle, donc lente et non reproductible ; elle ne
  passera pas à l'échelle de recherches documentaires plus larges.
- Aucune visibilité sur la composition des corpus (auteurs, éditeurs, plages de
  dates) : l'utilisateur ne peut ni auditer un corpus avant usage, ni en
  extraire des sous-ensembles par critère — chaque nouveau besoin de ce type
  repart d'un script ad hoc jetable.
- Les doublons inter-corpus (mesuré : 1 document à Jaccard 1,0 partagé entre les
  deux corpus de complement2) restent invisibles même quand l'utilisateur
  combine plusieurs corpus.

## Open Questions

- [NEEDS CLARIFICATION: la suppression « --suppr-doublons » détruit-elle
  physiquement les fichiers d'entrée (.json + .npy), ou produit-elle un dossier
  nettoyé ? Question de sécurité n° 1 — à trancher en /speckit-assess-shape.]
- [NEEDS CLARIFICATION: en mode corpus, la déduplication produit-elle un nouveau
  corpus (nouveau titre 9 chiffres, consommation du compteur) ou réécrit-elle en
  place ?]
- [NEEDS CLARIFICATION: politique de la bande ambiguë 0,6-0,8 (vrais doublons
  web/revue ET articles distincts cohabitent, mesures en research) — seuil
  exact, signaux combinés (même auteur ?), ou file « à confirmer » laissée à
  l'utilisateur ?]
- [NEEDS CLARIFICATION: formalisation de « contexte le plus précis » — ordre de
  priorité exact des champs (Référence remplie > Titre réel > placeholder « Nom
  de la source » > Date > Editeur ?).]
- [NEEDS CLARIFICATION: structure de sortie de corpus-split (dossier par valeur
  de critère ? arborescence par bucket de date ? nommage des sous-corpus) et
  effet d'un doublon inter-corpus sur les effectifs.]
- [NEEDS CLARIFICATION: alignement des buckets temporels — tranches calendaires
  (millénaires, siècles, années) ou fenêtres depuis la date min ; sémantique
  exacte du cas « tout tient en moins de 6 mois » (2 buckets : une date, une
  date vide).]
- [NEEDS CLARIFICATION: un document multi-auteur alimente-t-il plusieurs
  sous-corpus en corpus-split « aut » ?]
- [NEEDS CLARIFICATION: info-corpus sur plusieurs corpus en entrée — listes
  fusionnées (union, doublons comptés une fois ?) ou rapport par corpus
  d'origine ?]
- [NEEDS CLARIFICATION: volume maximal attendu en production (si des milliers de
  documents, le scan par paires O(n²) devra être remplacé par MinHash/LSH — non
  justifié à l'échelle des exemples).]

## Decided by User (recorded from session 2026-10-27)

- Jour absent dans la date (« avril 2025 ») : prendre par défaut le premier du
  mois.
- Champ « Date » vide ou inexistant (contexte absent) : ranger dans un bucket «
  vide » dédié.
