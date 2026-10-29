# Decision: Déduplication à seuil réglable + info-corpus + corpus-split

- **Slug**: dedup-corpus-split
- **Decided**: 2026-10-27
- **Verdict**: go
- **Artifacts reviewed**: intake.md | research.md | problem.md | concept.md (+
  mesures supplémentaires de seuil, cette session)

## Scorecard

| Critère | Note | Justification (résumée) |
| --- | --- | --- |
| Problem validity | strong | 28 % de doublons mesurés dans complement1 |
| Evidence strength | strong | Vérité terrain mesurée sur 232 + 283 documents |
| Value vs. inaction | strong | Statu quo coûteux ; coût de build faible |
| Feasibility / appetite | strong | Approches déjà prototypées en recherche |
| Strategic fit | strong | 100 % local et déterministe ; flux continu exigé |
| Risk posture | adequate | 2 à 4 faux positifs à seuil 75, assumés |

Détail des justifications :

- Problem validity : 28 % des documents de complement1 partagent un contexte
  identique ; cas d'école réel à 4 versions ; aucune visibilité sur les corpus.
- Evidence strength : similarités, temps de calcul, formats de date et couverture
  des champs tous mesurés localement ; aucun chiffre issu d'une supposition non
  étiquetée.
- Value vs. inaction : statu quo documenté (dédup manuelle, chunks dupliqués dans
  le RAG) ; les scripts de recherche font déjà le travail en environ 1 seconde.
- Feasibility / appetite : détection, similarité et bucketing prototypés pendant
  la recherche ; pipeline existant réutilisable ; appétit medium.
- Strategic fit : 100 % local et déterministe (constitution) ; la contrainte
  « brique dans un pipe plus large, flux continu sans coupure » est une exigence
  explicite de l'utilisateur, tranchée en sa faveur.
- Risk posture : le risque principal — faux positif destructif (suppression en
  place) — est **accepté explicitement par l'utilisateur** avec deux
  atténuations : seuil réglable `--seuil-doublons` (60-100) et rapport
  informatif. L'évaluation du seuil 75 (annexe) chiffre le risque restant :
  2 à 4 faux positifs probables
  sur 232 documents réels.

## Verdict & Rationale

**Go.** Le problème est réel, mesuré et coûteux à ignorer ; l'évidence est
solide ; une approche tient dans l'appétit. L'utilisateur a arbitré le compromis
central du concept : il choisit l'**Option B** (suppression automatique, flux
continu sans étape de confirmation) parce que l'outil doit s'insérer comme
brique dans un pipeline plus large — une interruption pour validation humaine
casserait ce flux. Le risque de faux positif est assumé et atténué par un seuil
réglable (`--seuil-doublons`, 60 à 100, défaut 75) et un rapport informatif en
sortie. Le « risque posture » n'est pas noté `strong` : à seuil 75, l'évaluation
sur données réelles (annexe) montre 2 à 4 suppressions probablement erronées sur
232 documents — c'est le prix connu et consenti du flux continu ; le verdict le
documente pour qu'il reste auditable.

## Décisions de l'utilisateur (session 2026-10-27)

1. **Option B** : suppression automatique en flux continu (pas de liste « à
  confirmer » — incompatible avec un usage de brique de pipeline), accompagnée
  d'un rapport informatif.
2. **`--seuil-doublons`** : seuil de similarité réglable de 60 à 100, **défaut
  75**, interprété en points de pourcentage de similarité de texte (Jaccard sur
  shingles).
3. Évaluer la pertinence du défaut 75 sur les exemples réels — fait, voir annexe.
4. (Héritées de problem.md) jour absent → 1er du mois ; champ vide/inexistant →
  bucket vide.

## Annexe — Évaluation du seuil 75 (complement1, 232 documents)

Balayage de seuils sur les 96 paires de texte Jaccard ≥ 0,70, chaque paire
classée (VRAI doublon / SUSPECT titres réels différents / INCERTAIN) :

| Seuil | Paires | Vrais doublons | Suspects | Incertains |
| --- | --- | --- | --- | --- |
| 70 | 96 | 78 | 12 | 6 |
| 74 | 85 | 74 | 5 | 6 |
| **75 (défaut)** | **80** | **70** | **4** | **6** |
| 80 | 73 | 65 | 2 | 6 |
| 85 | 58 | 54 | 1 | 3 |

- **Faux positifs probables à 75** (àinspecter en spécification pour décider
  s'ils sont tolérables) : 0,784 les deux articles « Budget 2026 » ; 0,770 « Les
  prélèvements obligatoires ont baissé sous Macron » vs « Comment les impôts ont
  baissé sous l'ère Macron » (même auteur) ; 0,818 les deux articles « Héritage
  » du même auteur.
- **Limite du défaut 75** : les cas web/revue à placeholder vivent à partir de
  **0,742** ; à 75, le cas d'école « Taxe sur les transactions financières »
  (famille 000003822565460155-158 vs version web) **échappe au seuil**
  (0,742-0,749 < 0,75). Le cas Chunké 4-versions descend à **2 sources** (les 3
  revue fusionnent par contexte identique ; la version web survit au seuil 75).
  Pour fusionner revue+web automatiquement, il faut un seuil ≤ 74 — au prix d'un
  suspect supplémentaire.
- **Conclusion de l'évaluation** : 75 est un défaut défendable (majorité des
  vrais doublons capturés, suspects limités), mais il rate le cas fondateur de
  la demande d'un cheveu. La spécification devra : (a) documenter ce
  comportement dans le rapport (la paire 0,742-0,749 visible en information),
  (b) éventuellement recommander 74 dans la documentation du flag. La mesure de
  similarité exacte retenue en spécification pourra faire varier ces chiffres
  d'un point.

## If go — Handoff to `/speckit-specify`

- **Problem** : les corpus assemblés contiennent des sources dupliquées (28 %
  mesurés) qui dégradent le RAG en aval, et l'utilisateur ne peut ni auditer
  (auteurs/éditeurs/dates) ni découper ses corpus.
- **Chosen approach** : Option B amendée — trois commandes nouvelles :
  `--suppr-doublons` (option de `corpus`) avec détection à deux règles
  déterministes : (1) contexte strictement identique, (2) similarité de texte
  (Jaccard sur shingles de mots) ≥ seuil `--seuil-doublons` (60-100, défaut 75)
  ; suppression automatique en flux continu du perdant (règle : contexte le plus
  précis gagne, à égalité le premier apparu) ; rapport informatif terminal
  listant doublons détectés, similarités, gagnants et perdants. Plus
  `info-corpus` (rapport lecture seule : auteurs / éditeurs / buckets temporels
  ≤ 6, politiques de dates de problem.md) et `corpus-split` (sous-corpus par
  critère aut / edit (défaut) / date, écrits au format corpus existant).
- **In scope** : entrées document (chunking) et entrées corpus ; suppression en
  place selon l'option B ; dates aux trois précisions observées (jour paddé/non
  paddé, mois-année → 1er du mois, vide → bucket vide) ; rapport en français sur
  stdout/stderr selon les conventions existantes ; tests sur les trois dossiers
  d'exemples fournis.
- **Out of scope** : LLM et tout non-déterminisme (phase 2 éventuelle) ;
  correction des métadonnées ; MinHash/LSH ; modification du chunker amont ou
  des règles FR existantes ; dédup inter-dossiers en phase 1 ; interface
  interactive de confirmation (flux continu exigé).
- **Success metrics** : 30 groupes à contexte identique détectés sur complement1
  ; cas Chunké → 2 sources à défaut 75 (documenté dans le rapport) ; zéro rejet
  à la réingestion des sous-corpus de corpus-split ; effectifs exacts sur
  complement2 (4/29 éditeurs, 23/124 auteurs, buckets ≤ 6) ; exécution en
  secondes à l'échelle des exemples ; déterminisme bit à bit.
- **Carried-forward open questions**:
  - [À trancher en spécification : sémantique de suppression en place —
    suppression physique des fichiers .json+.npy du dossier d'entrée en mode
    document ; en mode corpus : réécriture du corpus en place ou nouveau corpus
    via le compteur ? Ordre des opérations, gestion des erreurs à mi-course.]
  - [À trancher : formalisation déterministe du « contexte le plus précis »
    (ordre des champs, poids de la Référence remplie vs Titre placeholder).]
  - [À trancher : traitement des paires « VRAI par contexte identique » qui
    échappent au seuil texte (le contexte identique reste une règle de détection
    indépendante du seuil — confirmer).]
  - [À trancher : alignement des buckets temporels (calendaire vs fenêtre
    glissante), sémantique du cas « moins de 6 mois ».]
  - [À trancher : corpus-split — un document multi-auteur éclaté dans plusieurs
    sous-corpus ? structure de sortie et nommage ; info-corpus multi-corpus
    (union vs par corpus).]
  - [À trancher : formats de date imprévus → bucket vide (décision par défaut
    héritée de problem.md, à confirmer dans la spec).]
