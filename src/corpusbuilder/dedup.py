"""Détection des doublons et rapport (FR-003 à FR-009, D3, D5, D11).

Deux règles déterministes : contexte strictement identique (tous champs
égaux, indépendamment du seuil) et similarité de texte au score ≥ seuil.
Regroupement transitif par union-find ; le gagnant est la source au
contexte le plus précis, à égalité la première apparue.
"""

from dataclasses import dataclass, field

from .similarity import UnionFind, jaccard_max_possible, score, shingles
from .sources import Source, build_sources

SCORE_PLANCHER = 60  # bande « paires proches » du rapport (D11, SC-002)


def _cle_paire_proche(paire):
    """Tri des paires proches : score décroissant, puis ordre stable."""
    return (-paire[2], paire[0], paire[1])


@dataclass
class GroupeDoublons:
    """Un groupe de doublons réduit à une source conservée."""

    numero: int
    regle: str
    score: int | None
    winner: Source
    excluded: list = field(default_factory=list)


@dataclass
class Resultat:
    """Résultat de la détection sur l'ensemble des sources."""

    total: int
    groups: list = field(default_factory=list)
    near_pairs: list = field(default_factory=list)
    excluded_keys: set = field(default_factory=set)

    @property
    def exclus(self) -> int:
        return len(self.excluded_keys)


def detect(sources: list[Source], seuil: int) -> Resultat:
    """Détection complète : groupes, paires proches, exclusions."""
    total = len(sources)
    uf = UnionFind(total)
    liens_ctx: list[tuple[int, int]] = []
    liens_sim: list[tuple[int, int, int]] = []

    # Règle 1 — contexte strictement identique (jamais pour un contexte
    # absent : une source sans contexte n'est déclarée doublon que par
    # le seuil de texte, D2).
    par_canon: dict[str, list[int]] = {}
    for indice, source in enumerate(sources):
        if source.canon is not None:
            par_canon.setdefault(source.canon, []).append(indice)
    for indices in par_canon.values():
        for position in range(1, len(indices)):
            uf.union(indices[0], indices[position])
            liens_ctx.append((indices[0], indices[position]))

    # Règle 2 — similarité de texte au score tronqué ≥ seuil.
    empreintes = [shingles(source.text) for source in sources]
    tailles = [len(e) for e in empreintes]
    for i in range(total):
        for j in range(i + 1, total):
            petit, grand = sorted((tailles[i], tailles[j]))
            if grand == 0 or jaccard_max_possible(petit, grand) < seuil:
                continue
            valeur = score(empreintes[i], empreintes[j])
            if valeur >= seuil:
                uf.union(i, j)
                liens_sim.append((i, j, valeur))

    # Paires proches non fusionnées (information, D11).
    proches: list[tuple[int, int, int]] = []
    for i in range(total):
        for j in range(i + 1, total):
            petit, grand = sorted((tailles[i], tailles[j]))
            if grand == 0 or jaccard_max_possible(petit, grand) < SCORE_PLANCHER:
                continue
            if uf.find(i) == uf.find(j):
                continue
            valeur = score(empreintes[i], empreintes[j])
            if SCORE_PLANCHER <= valeur < seuil:
                proches.append((i, j, valeur))
    proches.sort(key=_cle_paire_proche)

    # Groupes transitifs de plus d'un membre.
    contextes = {i for paire in liens_ctx for i in paire}
    scores_groupe: dict[int, list[int]] = {}
    for i, j, valeur in liens_sim:
        racine = uf.find(i)
        scores_groupe.setdefault(racine, []).append(valeur)
    result = Resultat(total=total)
    for membres in uf.components():
        if len(membres) < 2:
            continue
        regle_ctx = any(i in contextes for i in membres)
        racine = uf.find(membres[0])
        scores = scores_groupe.get(racine, [])
        regle = "contexte identique" if regle_ctx else "similarité"
        regle = f"{regle} {min(scores)}" if scores and not regle_ctx else regle
        winner = membres[0]
        for i in membres[1:]:
            if sources[i].precision > sources[winner].precision:
                winner = i
        excluded = [i for i in membres if i != winner]
        groupe = GroupeDoublons(
            numero=len(result.groups) + 1,
            regle=regle,
            score=min(scores) if scores else None,
            winner=sources[winner],
            excluded=[sources[i] for i in excluded],
        )
        result.groups.append(groupe)
        result.excluded_keys.update(sources[i].key for i in excluded)

    result.near_pairs = [(sources[i], sources[j], valeur) for i, j, valeur in proches]
    return result


def appliquer_exclusion(couples, seuil: int):
    """Exclut les sources perdantes avant le collage (FR-008, FR-010).

    Retourne (couples conservés — lignes et vecteurs filtrés —, résultat
    de la détection). Les fichiers d'entrée ne sont jamais modifiés.
    """
    from dataclasses import replace

    sources = build_sources(couples)
    resultat = detect(sources, seuil)
    if not resultat.excluded_keys:
        return list(couples), resultat
    garder: dict[int, list[int]] = {}
    for source in sources:
        if source.key in resultat.excluded_keys:
            continue
        for couple_index, row_index in source.refs:
            garder.setdefault(couple_index, []).append(row_index)
    conserves = []
    for couple_index, couple in enumerate(couples):
        indices = garder.get(couple_index)
        if not indices:
            continue  # toutes les sources du couple sont exclues
        indices = sorted(indices)  # ordre de traitement conservé
        if len(indices) == len(couple.rows):
            conserves.append(couple)
            continue
        conserves.append(
            replace(
                couple,
                rows=[couple.rows[i] for i in indices],
                matrix=couple.matrix[indices],
            )
        )
    return conserves, resultat


def rapport(resultat: Resultat, seuil: int) -> list[str]:
    """Lignes du rapport terminal (contracts/cli.md, FR-009)."""
    lignes: list[str] = []
    if resultat.groups:
        for groupe in resultat.groups:
            lignes.append(
                f"Doublons exclus — groupe {groupe.numero} (règle : {groupe.regle})"
            )
            lignes.append(f"  conservé : {groupe.winner.display}")
            lignes.append("  exclus : " + ", ".join(s.display for s in groupe.excluded))
    else:
        lignes.append("Aucun doublon détecté.")
    if resultat.near_pairs:
        lignes.append(
            f"Paires proches non fusionnées (score >= {SCORE_PLANCHER} et < {seuil}) :"
        )
        for a, b, valeur in resultat.near_pairs:
            lignes.append(f"  {valeur} : {a.display} <-> {b.display}")
    conserves = resultat.total - resultat.exclus
    lignes.append(
        f"Bilan : {resultat.total} sources analysées, "
        f"{len(resultat.groups)} groupes, {resultat.exclus} sources "
        f"exclues, {conserves} sources conservées"
    )
    return lignes
