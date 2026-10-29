# Idea Intake: Suppression de doublons et séparation de corpus

- **Slug**: dedup-corpus-split
- **Created**: 2026-10-27
- **Source**: pasted text (utilisateur, session du 2026-10-27) + pointeurs de
  codebase vers `Examples/Exemple .json/Chunké`, `Examples/Exemple-complement1`,
  `Examples/Exemple-complement2`
- **Type**: new-capability

## Idea (as captured)

> Je souhaite améliorer mon outil en rajoutant les fonctionnalités suivantes :
>
> ### 1. Reconnaissance - suppression de doublons
>
> Je souhaite que l'outil dispose de la commande optionnelle "--suppr-doublons"
> qui permette, uniquement lorsque les *conditions* sont réunies, de supprimer
> les sources en doublons.
>
> #### *Conditions*
>
> Doit être réalisé que sur les .json d'entrée issue du chunking.
>
> On envisagera, si c'est possible pour un coût raisonnable de le faire aussi
> sur les entrées en mode sortie de corpus.
>
> #### Comment reconnaître une source en doublon ?
>
> Tu trouveras un exemple dans le dossier du dépôt
> `Examples/Exemple .json/Chunké` (l'original citait un chemin local
> absolu, relativisé ici)
>
> C'est un exemple très concret : dans une recherche documentaire, le même
> article est apparu 4 fois sous des formes différentes ("la Tribune" ou le site
> web de "La tribune"). Tu verras que le texte est très similaire. Imprègne toi
> de cet exemple pour voir comment identifier les doublons et à quel coût.
>
> Le cas échéant, si la similarité par texte est trop lourde ou incertaine,
> faire avec le champ "contexte" comme ci-dessous.
>
> Exemples de champs "context" cités par l'utilisateur (4 occurrences du même
> article) :
>
> - Trois occurrences identiques de :
> `"context": { "Typologie": "Article", "Auteur(s)": ["Jean-Victor Semeraro"],
> "Titre": "Nom de la source", "Editeur": "La Tribune", "Date": "9 septembre
> 2026", "Référence": "", "Citation": "Jean-Victor Semeraro, \"Nom de la
> source\", La Tribune, 9 septembre 2026" }`
> - Une quatrième occurrence, plus complète, du même article :
> `"context": { "Typologie": "Article", "Auteur(s)": ["Jean-Victor Semeraro"],
> "Titre": "Taxe sur les transactions financières : un dispositif qui rapporte à
> l'État, mais aux multiples failles", "Editeur": "La Tribune (France)", "Date":
> "10 septembre 2026", "Référence": "news-20260910-TR-article_3832214",
> "Citation": "Jean-Victor Semeraro, \"Taxe sur les transactions financières :
> un dispositif qui rapporte à l'État, mais aux multiples failles\",
> news-20260910-TR-article_3832214, La Tribune (France), 10 septembre 2026" }`
>
> Considère que si elle est identique, tu peux supprimer les doublons.
>
> Sinon, propose moi un degré de similarité du champ contexte au delà duquel on
> considère les articles en doublons.
>
> Ici ce sont les mêmes articles mais comme certains sont publiés sur internet,
> c'est plus tôt que la revue.
>
> Il me faut à la fin un rapport des articles considérés comme doublons et des
> suppressions en terminal pour informer l'utilisateur.
>
> Je suis pour une solution 100% locale et déterministe. On verra dans un second
> temps s'il faut un appel LLM pour affiner.
>
> #### Lequel des deux (ou plus) sources à supprimer ?
>
> Choisi celui dont le contexte est le plus précis (possède le plus de champs
> complétés, les plus crédibles). A défaut, on garde le premier qui apparaît.
>
> ### 2. Séparation de corpus en sous ensembles
>
> Je souhaite que l'outil dispose de 2 nouvelles commandes "info-corpus" et
> "corpus-split" permettant :
>
> #### 2.1 "info-corpus"
>
> N'accepte en entrée qu'un (ou plusieurs) format "corpus", ou dossiers de
> format corpus.
>
> Commande permettant à l'utilisateur de solliciter des informations sur
> l'ensemble d'entrées :
>
> - Liste des auteurs (champ "Auteur(s)" de "context")
> - Liste des éditeurs (champ "Editeur" de "context")
> - tableau de la plage temporelle (champ "Date" de "context") couverte par les
>   éléments, par bucket adaptées pour qu'il n'y ait que 6 buckets max, mais en
>   maximisant le nombre de bucket pour tenter d'atteindre 6 :
>   - tranches de 1000 ans
>   - tranches de 100 ans
>   - tranches de 50 ans
>   - tranches de 20 ans
>   - tranches de 10 ans
>   - tranches de 5 ans
>   - tranches de 2 ans
>   - tranches de 1 an
>   - tranches de 6 mois
>
> si tout tient en moins de 6 mois, seulement 2 bucket, avec date et date vide.
>
> Un champ vide fait office de bucket ou de sous ensemble dédié.
>
> Dans chaque bucket doit être indiqué le nombre d'éléments constitutifs (nombre
> de documents)
>
> La commande "info-corpus" est suivi de :
>
> - "all" pour les trois types d'infos précédentes (valeur par défaut)
> - "aut" pour les auteurs
> - "edit" pour les éditeurs
> - "date" pour les dates
>
> #### 2.2 "corpus-split"
>
> N'accepte en entrée qu'un (ou plusieurs) format "corpus", ou dossiers de
> format corpus.
>
> Commande permettant à l'utilisateur de générer des sorties "corpus" de
> l'ensemble d'entrées par critère demandé.
>
> La commande "corpus-split" est suivi de :
>
> - "aut" pour les auteurs
> - "edit" pour les éditeurs (par défaut)
> - "date" pour les dates, selon le schéma donné précédemment.
>
> ### Exemples
>
> Tu *dois* utiliser les exemples pour le design, le calibrage et le test en
> réel des nouvelles fonctionnalités.
>
> - "CorpusBuilder\Examples\Exemple-complement1" : c'est un ensemble de .json /
>   .npy d'entrée classique de l'outil. Tu pourras l'utiliser pour le
>   développement et le test de la fonctionnalité 1 (reconnaissance et
>   suppression de doublons).
> - "CorpusBuilder\Examples\Exemple-complement2" : c'est un ensemble de .json /
>   .npy de sortie classique de l'outil. Tu pourras l'utiliser pour le
>   développement et le test de la fonctionnalité 1 sur le format de sortie, ET
>   pour le développement et le test de la fonctionnalité 2 (séparation de
>   corpus en sous ensembles, 2.1 et 2.2).

## Restated

L'utilisateur veut ajouter à CorpusBuilder trois nouvelles commandes : une
option `--suppr-doublons` de détection/suppression déterministe et locale des
sources dupliquées (basée sur le texte puis, le cas échéant, sur une similarité
du champ `context`), et deux commandes d'analyse et de découpage de corpus
(`info-corpus` pour lister auteurs, éditeurs et distribution temporelle en
buckets ; `corpus-split` pour générer des sous-corpus par critère auteur,
éditeur ou date).

## Origin & Context

- **Raised by**: l'utilisateur (propriétaire du projet CorpusBuilder), session
  du 2026-10-27.
- **Trigger**: constat concret lors d'une recherche documentaire où le même
  article (La Tribune) est apparu 4 fois sous des formes différentes dans les
  entrées chunkées, et besoin de découper les corpus de sortie en sous-ensembles
  par auteur / éditeur / date.
- **Contraintes explicites** : solution 100% locale et déterministe (pas d'appel
  LLM dans un premier temps) ; les exemples fournis doivent servir au design, au
  calibrage et au test réel des nouvelles fonctionnalités ; rapport terminal des
  doublons détectés et supprimés.

## First-Glance Unknowns

- [NEEDS CLARIFICATION: format exact des .json d'entrée "issue du chunking" vs
  format de sortie "corpus" — quels champs distinguent les deux, et où le flag
  `--suppr-doublons` se branche-t-il dans le pipeline existant ?]
- [NEEDS CLARIFICATION: la suppression `--suppr-doublons` s'applique-t-elle aux
  fichiers d'entrée (.json/.npy) eux-mêmes, ou produit-elle un jeu de fichiers
  nettoyé ? Destruction physique ou copie ?]
- [NEEDS CLARIFICATION: seuil de similarité du champ `context` en dessous de
  l'identité stricte — un degré doit être proposé, mais sur quelles comparaisons
  (Titre ? Editeur normalisé ? Date ? Citation entière ?) et comment normaliser
  "La Tribune" vs "La Tribune (France)" ?]
- [NEEDS CLARIFICATION: quel coût (temps de traitement) est jugé "raisonnable"
  pour la détection par similarité de texte sur les exemples ?]
- [NEEDS CLARIFICATION: pour `corpus-split`, structure de sortie attendue des
  sous-corpus (un dossier par valeur de critère ? arborescence par bucket
  temporel ?) et convention de nommage.]
- [NEEDS CLARIFICATION: comment interpréter les dates hétérogènes du champ
  "Date" (ex. "9 septembre 2026" en texte libre) — plage de formats à accepter,
  et comportement en cas d'échec de parsing (bucket "date vide" ?).]
- [NEEDS CLARIFICATION: pour `info-corpus`/`corpus-split`, définition exacte du
  "format corpus" accepté en entrée (structure de dossier, extensions).]
