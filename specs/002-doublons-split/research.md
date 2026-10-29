# Research : Déduplication et séparation de corpus (CorpusBuilder)

Date : 2026-10-27 — Phase 0 du plan (`plan.md`). Chaque décision est motivée
par les mesures de l'assessment
(`.specify/assessments/dedup-corpus-split/research.md`, `decision.md`) et par
les jeux réels `Examples/Exemple-complement1` (232 sources document) et
`Examples/Exemple-complement2` (51 + 232 sources corpus), qui servent aussi au
calibrage et aux tests (exigence de la spec).

## D1 — Mesure de similarité de texte

- Décision : Jaccard sur ensembles de shingles de 5 mots — tokens
  normalisés (minuscules, `re.findall(r'\w+')` Unicode) — pourcentage =
  troncature entière de `100 × |A ∩ B| / |A ∪ B|`.
- Rationale : mesuré sur complement1 — 100 % des 43 paires à contexte
  identique ont un texte ≥ 0,80 ; les paires web/revue vivent à 0,742-0,84 ;
  les articles distincts du même sujet à 0,65-0,78 ; scan complet de 232
  sources en 1,1 s. La troncature (et non l'arrondi) est conservative : la
  paire d'école à 0,7487 donne 74, pas 75 — le seuil par défaut 75 fusionne
  donc à partir de 0,75 exactement (tableau de `decision.md`, annexe).
- Alternatives : SequenceMatcher (ratio dépendant des blancs, lent),
  embeddings de phrases (non local, non déterministe), SimHash (complexité
  injustifiée à moins de quelques milliers de sources).

## D2 — Identité de contexte

- Décision : le contexte est sérialisé canoniquement (JSON trié, UTF-8,
  clés absentes normalisées à vide) ; deux contextes canoniquement égaux
  sont identiques (FR-003). **Une source sans contexte ne peut pas être
  déclarée doublon par la seule règle du contexte** : elle reste soumise au
  seuil de texte.
- Rationale : les exemples historiques `Examples/Exemple1/2/3` n'ont aucun
  champ contexte — les regrouper « vides = vides » supprimerait des
  documents sans rapport (faux positif massif). Les contextes placeholder
  identiques (« Nom de la source », référence vide), eux, SONT de vrais
  doublons — mesuré : 30 groupes, 66 sources, 100 % de texte ≥ 0,8.
- Alternatives : traiter le vide comme valeur ordinaire (rejeté :
  contre-exemple réel Exemple1/Exemple2).

## D3 — Regroupement transitif des doublons

- Décision : union-find sur les paires retenues (FR-006) ; chaque composante
  est un groupe ; le gagnant est désigné dans le groupe (D5) et les autres
  sources sont exclues de l'assemblage.
- Rationale : mesuré dans complement1 — familles à 3-4 membres reliées par
  paires (placeholder ↔ web ↔ OCR) ; un traitement par paires isolées
  laisserait plusieurs survivants d'un même groupe.
- Alternatives : cliques strictes (casse les chaînes réelles), groupement
  par clé de hachage du texte (rate les variantes OCR).

## D4 — Ordre de traitement et « premier apparu »

- Décision : l'ordre de collage existant (FR-014 : dossiers dans l'ordre
  fourni, tri alphabétique du radical de titre au sein d'un dossier) définit
  l'ordre des sources ; « premier apparu » = première source dans cet
  ordre ; le rapport et l'assemblage suivent le même ordre (déterminisme).
- Rationale : réutilise une règle existante, testée, sans en introduire de
  nouvelle ; cohérent avec SC-006 (exécutions identiques).
- Alternatives : ordre de découverte du système de fichiers (non portable,
  non déterministe).

## D5 — Précision du contexte (formalisation de FR-007)

- Décision : score de précision déterministe par source, départage par
  ordre croissant :
  1. nombre de champs renseignés parmi les sept du contexte (typologie,
     auteurs — liste non vide —, titre, éditeur, date, référence, citation) ;
  2. référence bibliographique renseignée ;
  3. titre réel (différent du placeholder « Nom de la source », avec ou
     sans marquage de gras) ;
  4. date renseignée ;
  5. premier apparu (D4).
- Rationale : calibré sur le cas d'école Chunké — la version web (7 champs,
  référence `news-20260910-TR-article_3832214`, titre réel) bat les
  placeholders (référence vide, titre placeholder) à chaque départage ; à
  précision égale (les 3 versions placeholder), le premier apparu gagne.
- Alternatives : pondération par champ (arbitraire), score de « crédibilité »
  libre (non déterministe).

## D6 — Seuil et option

- Décision : `--seuil-doublons N`, N entier 60 à 100, défaut 75 ; hors
  bornes : erreur d'usage (code 2), aucun traitement. Le pourcentage est
  celui de D1 ; la comparaison est `>=`.
- Rationale : décision utilisateur (decision.md) ; l'évaluation sur
  complement1 donne 70 vrais doublons / 4 suspects à 75, et le défaut 75
  rate la paire d'école (0,742-0,749) d'un cheveu — comportement documenté
  dans le rapport (D11) et réglable par l'option.
- Alternatives : seuil hors bornes rejeté silencieusement (contredit
  FR-005), défaut 74 (plus de faux positifs mesurés).

## D7 — Interfaces en ligne de commande

- Décision : trois points d'entrée (scripts `pyproject`) :
  - `corpus DOSSIER... [--output-folder P] [--suppr-doublons]
    [--seuil-doublons N]` — comportement inchangé sans les options ;
  - `info-corpus CIBLE... [all|aut|edit|date]` (critère positionnel
    optionnel, défaut `all`) — CIBLE = fichier corpus ou dossier ;
  - `corpus-split CIBLE... [aut|edit|date] [--output-folder P]` (défaut
    `edit`, sortie défaut `output`).
- Rationale : l'utilisateur exige un flux continu en pipeline — pas de
  sous-commande interactive ; argparse stdlib (constitution IV) ; les deux
  nouvelles commandes n'acceptent que des corpus : tout couple document ou
  fichier inconnu est signalé sur stderr et ignoré (FR-013).
- Alternatives : une méga-commande à sous-commandes (casse le contrat CLI
  existant), paramètres nommés pour le critère (verbeux en pipeline).

## D8 — Suffixe et titres des sous-corpus

- Décision : chaque sous-corpus porte le titre standard à 9 chiffres
  (partie aléatoire unique par exécution, une occurrence du compteur
  consommée par sous-corpus écrit) suivi de « - » et du slug de la valeur
  du critère : minuscules sans accents, séparateurs normalisés en « - »,
  tronqué à 10 caractères ; collision entre deux valeurs → suffixe
  numérique déterministe (« -2 », « -3 »…). La regex d'appariement des
  corpus dans `discovery.py` est étendue en conséquence
  (`contracts/file-formats.md`) : `^\d{9}(-[a-z0-9-]{1,10})?$`.
- Rationale : FR-025 exige des fichiers à plats suffixés et réingérables ;
  la regex actuelle `^\d{9}$` (constate dans `discovery.py`) REJETTERAIT les
  sous-corpus suffixés — l'extension du contrat est donc obligatoire pour
  SC-004 ; un slug court et lisible reste exploitable en aval de pipeline.
- Alternatives : sous-dossiers (rejeté par clarification du 2026-10-27),
  préfixe (rejeté : suffixe exigé), compteur de collision aléatoire (non
  déterministe).

## D9 — Dates : parsing et buckets

- Décision : deux formats reconnus (inventaire exhaustif des exemples) :
  « jour mois année » (jour paddé ou non, mois français accentués) et
  « mois année » (rangé au premier jour du mois — politique utilisateur) ;
  tout le reste (absent, vide, imprévu) va au bucket « sans date ».
  Tranches calendaires alignées : 1000 ans (millénaires), 100 (siècles),
  50, 20, 10, 5, 2 ans (multiples), 1 an, 6 mois (semestres S1/S2). La
  plus petite tranche dont le découpage de la plage tient en 6 buckets
  au plus est retenue (FR-016 corrigée) ; bornes à gauche inclusives,
  à droite exclusives. Si la plage des dates interprétables tient en
  6 mois ou moins (max ≤ min + 6 mois calendaires) : exactement 2 buckets
  « avec date » / « sans date » (FR-019). Le bucket « sans date » est
  toujours affiché, même d'effectif nul.
- Rationale : inventaire mesuré sur les 251 JSON des exemples — 483 ×
  « j mois aaaa » non paddé, 2 × « 09 octobre 2026 » paddé (Complement),
  1 × « avril 2025 » sans jour (Complement, ouvrage) ; Exemple1/2/3 sans
  contexte. Alignement calendaire = rapports stables et lisibles ; la
  fenêtre ≤ 6 mois évite le bucket unique, contraire à l'intake.
- Alternatives : fenêtres glissantes depuis min (instable d'un jeu à
  l'autre), parsing exhaustif multilingue (YAGNI), bucket vide masqué
  (contredit FR-018/FR-019).

## D10 — Exclusion et assemblage

- Décision : la déduplication s'applique après la validation des couples et
  avant le collage (FR-010 : toutes les sources valides de l'exécution,
  dossiers confondus). Identité d'une source : un couple document entier ;
  pour un couple corpus, l'ensemble des lignes de même `chunkingid` —
  regroupement global à l'exécution (le doublon inter-corpus mesuré dans
  complement2 doit être capturé). Les perdants sont retirés de l'assemblage
  : couple document écarté en entier ; couple corpus réduit aux lignes et
  vecteurs des sources survivantes (sélection par indices, matrice
  reconstruite par lignes). Les fichiers d'entrée ne sont jamais écrits.
- Rationale : FR-008 (exclusion à l'écriture) ; la sélection par indices
  préserve l'alignement JSON/matrice (FR-011) en réutilisant le contrôle
  final FR-023 existant ; le regroupement global capture le cas mesuré
  (`059650007.json::000003652121260301` ≡ `143800006.json::000000142121260142`,
  Jaccard 1,0).
- Alternatives : dédup par dossier (rejeté par clarification du 2026-10-27),
  réécriture des entrées (rejetée : FR-008).

## D11 — Rapport terminal de déduplication

- Décision : rapport en français sur stdout, trois sections :
  1. « Doublons exclus » — par groupe : règle (contexte identique ou
     similarité), score le cas échéant, source conservée, sources exclues
     (identifiées par nom de fichier et, pour un corpus, par `chunkingid`) ;
  2. « Paires proches non fusionnées » — paires de score ≥ 60 et < seuil,
     listées à titre d'information (titres ou identifiants) — c'est cette
     section qui rend visible la paire d'école (0,742-0,749) au défaut 75 ;
  3. « Bilan » — sources analysées, groupes, sources exclues, sources
     conservées.
- Rationale : FR-009 et SC-002/SC-007 ; les avertissements et erreurs restent
  sur stderr selon les conventions existantes (contrat CLI 001).
- Alternatives : rapport sur stderr (contrairement au contrat 001 : le
  rapport est le résultat attendu, pas un avertissement), fichier de
  rapport (copie cachée, contrarié Data Retention).

## D12 — `info-corpus` consolidé

- Décision : rapport unique sur l'union des corpus fournis (FR-020) ;
  effectifs comptés en sources (pas en lignes) ; une source multi-auteurs
  compte +1 pour chacun de ses auteurs ; liste des éditeurs avec effectifs ;
  tableau temporel selon D9 avec la plage couverte. Sortie texte sur stdout
  uniquement ; aucune écriture de fichier ; codes retour conformes au
  contrat CLI (0 succès, 1 erreur, 2 usage).
- Rationale : FR-013 à FR-020 ; effectifs sources mesurables sur
  complement2 (4 et 29 éditeurs ; 23 et 124 auteurs — en union : à
  calculer et à inscrire dans les tests d'intégration).
- Alternatives : rapport par corpus d'origine (verbeux, contrarié FR-020),
  effectifs en lignes (détourne la notion de « documents » de l'intake).

## D13 — `corpus-split` : regroupement et écriture

- Décision : sources groupées par valeur du critère (chaque auteur pour
  `aut` — FR-024 ; éditeur pour `edit` ; bucket de date pour `date`,
  même schéma que D9) ; les sources sans valeur forment le sous-ensemble
  dédié (slug « sans-date », « sans-auteur », « sans-editeur ») ; chaque
  groupe est écrit via le chemin existant `output.write_corpus` avec le
  titre suffixé (D8) et son propre lot de lignes/vecteurs ; aucun
  sous-corpus vide n'est écrit ; l'ordre d'écriture suit l'ordre de
  traitement (D4) ; à la fin, un bilan stdout liste les sous-corpus
  écrits.
- Rationale : FR-021 à FR-025 ; réingérabilité garantie par D8 ;
  « une seule valeur → un seul sous-corpus contenant tout » (edge case de
  la spec) tombe naturellement de cette règle.
- Alternatives : écriture par dossier de valeur (rejetée par
  clarification), arborescence à deux niveaux (rejetée : plus complexe,
  aucune valeur ajoutée à plat).
