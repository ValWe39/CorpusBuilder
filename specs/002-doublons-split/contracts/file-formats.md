# Contrat de formats : addendum sous-corpus et appariement étendu

Date : 2026-10-27 — Phase 1 du plan (`plan.md`). Décisions D8, D9, D10 de
`research.md`. Ce contrat est un addendum à
`specs/001-corpus-concatenation/contracts/file-formats.md`, qui reste
applicable sans changement pour tout le reste.

## 1. Suffixe des sous-corpus (corpus-split)

- Fichiers produits : `<titre>.json` et `<titre>.npy` où
  `<titre>` = 9 chiffres (règles existantes, section 4 de 001) + `-` +
  `<slug>`.
- `<slug>` : forme normalisée de la valeur du critère — minuscules sans
  accents, tout caractère non alphanumérique remplacé par `-`, pléthore
  de `-` réduite à un seul, tronqué à 10 caractères ; valeurs réservées
  `sans-auteur`, `sans-editeur`, `sans-date` (sources sans valeur) ;
  collision entre deux valeurs après troncature : `-2`, `-3`… apposés
  de façon déterministe (ordre de traitement).
- Le contenu de chaque sous-corpus est un tableau plat de lignes
  `ChunkRow` au format existant (section 5 de 001) ; la matrice suit le
  format existant (section 6) ; l'ordre des lignes est l'ordre de
  traitement (FR-011, FR-012 de la spec 001 conservés).

## 2. Extension de la règle d'appariement (réingestion)

- La règle d'appariement d'un couple corpus (FR-007 de 001 : `.json` et
  `.npy` portent strictement le même titre) est étendue : le titre d'un
  corpus est désormais un radical à 9 chiffres suivi facultativement de
  `-<slug>` (1 à 10 caractères `[a-z0-9-]`).
- Regex d'acceptation : `^\d{9}(-[a-z0-9-]{1,10})?$`.
- Le radical de tri (FR-014) reste le titre complet du fichier ; deux
  sous-corpus du même lot se trient donc par slug — ordre stable et
  déterministe.
- Impact : les corpus existants à 9 chiffres restent valides (branche
  facultative absente) ; aucun comportement existant ne change en
  dehors de l'acceptation des titres suffixés.

## 3. Sources et contexte (déduplication, info-corpus, corpus-split)

- Les sept champs du contexte reconnus pour la détection et les critères :
  `Typologie`, `Auteur(s)` (liste), `Titre`, `Editeur`, `Date`,
  `Référence`, `Citation` (valeurs textuelles, encodage UTF-8).
- Dates acceptées (inventaire exhaustif des exemples du dépôt) :
  `J mois AAAA` (jour paddé ou non, mois français accentués) et
  `mois AAAA` (rangé au premier jour du mois) ; toute autre valeur,
  absente ou vide, est « sans date ».
- Identité d'une source dans un couple corpus : la valeur de
  `chunkingid` ; le regroupement est global à l'exécution (D10) — deux
  lignes de deux corpus différents portant le même `chunkingid`
  appartiennent à la même source.
- Le champ `context` d'un document d'entrée peut être un objet (dict)
  ou absent ; il est canonisé (JSON trié) pour la comparaison stricte ;
  une source sans contexte n'est jamais déclarée doublon par la seule
  règle du contexte (D2).

## 4. Compteur

- `counter.txt` : format inchangé ; `corpus-split` consomme une
  occurrence par sous-corpus écrit, `corpus --suppr-doublons` une seule
  comme aujourd'hui, `info-corpus` aucune.
