"""Sources : unités de déduplication et de comptage (FR-002, D2, D5).

Une source = un couple document entier, ou l'ensemble des lignes
d'un même identifiant de chunking dans les couples corpus (regroupement
global à l'exécution, D10).
"""

import json
from dataclasses import dataclass, field

from .models import ChunkRow, Couple, CoupleKind

TITRE_PLACEHOLDER = "nom de la source"


@dataclass
class Source:
    """Une source, avec ses références de lignes dans les couples.

    `refs` est une liste de (indice de couple, indice de ligne) ; une
    source corpus peut s'étendre sur plusieurs couples (même
    `chunkingid` réparti sur plusieurs fichiers, D10).
    """

    key: str
    kind: CoupleKind
    refs: list[tuple[int, int]] = field(default_factory=list)
    context: object = None
    canon: str | None = None
    precision: tuple = (0, False, False, False)
    text: str = ""
    order: int = 0
    chunkingid: str | None = None
    files: list = field(default_factory=list)

    @property
    def display(self) -> str:
        """Libellé de la source : fichier document, ou fichiers::cid."""
        if self.chunkingid is None:
            return self.key
        fichiers = ", ".join(dict.fromkeys(self.files))
        return f"{fichiers}::{self.chunkingid}"


def canon_context(context: object) -> str | None:
    """Sérialisation canonique (D2) ; un contexte absent reste None."""
    if context is None:
        return None
    return json.dumps(context, sort_keys=True, ensure_ascii=False)


def is_placeholder_title(title: object) -> bool:
    """Titre placeholder « Nom de la source » (avec ou sans gras, D5)."""
    if not isinstance(title, str):
        return False
    nettoye = title.strip().strip("*").strip()
    return nettoye.lower() == TITRE_PLACEHOLDER


def _rempli(valeur: object) -> bool:
    if isinstance(valeur, str):
        return bool(valeur.strip())
    if isinstance(valeur, list):
        return len(valeur) > 0
    return bool(valeur)


def context_precision(context: object) -> tuple:
    """Score de précision FR-007 : (champs renseignés, référence,
    titre réel, date) — comparaison lexicographique des tuples."""
    if not isinstance(context, dict):
        return (0, False, False, False)
    champs = sum(1 for valeur in context.values() if _rempli(valeur))
    reference = _rempli(context.get("Référence"))
    titre = context.get("Titre")
    titre_reel = _rempli(titre) and not is_placeholder_title(titre)
    date = _rempli(context.get("Date"))
    return (champs, reference, titre_reel, date)


def _source_context(rows: list[ChunkRow]) -> object:
    """Premier contexte non nul des lignes (déterministe)."""
    for row in rows:
        if row.context is not None:
            return row.context
    return None


def build_sources(ordered_couples: list[Couple]) -> list[Source]:
    """Construit les sources de l'exécution, dans l'ordre de traitement.

    Document : un couple = une source (clé = chemin du JSON). Corpus :
    lignes regroupées par `chunkingid` globalement à l'exécution (D10) ;
    une ligne sans `chunkingid` forme une source propre, jamais
    regroupée (clé = fichier::#indice).
    """
    sources: list[Source] = []
    par_chunkingid: dict[str, Source] = {}
    for couple_index, couple in enumerate(ordered_couples):
        if couple.kind is CoupleKind.DOCUMENT:
            rows = couple.rows
            context = _source_context(rows)
            sources.append(
                Source(
                    key=couple.json_path.name,
                    kind=couple.kind,
                    refs=[(couple_index, i) for i in range(len(rows))],
                    context=context,
                    canon=canon_context(context),
                    precision=context_precision(context),
                    text="\n".join(row.text for row in rows),
                    order=len(sources),
                )
            )
            continue
        for row_index, row in enumerate(couple.rows):
            cid = row.chunkingid
            if cid is None:
                cid = f"{couple.json_path.name}::#{row_index}"
                source = Source(
                    key=cid,
                    kind=couple.kind,
                    refs=[(couple_index, row_index)],
                    context=row.context,
                    canon=canon_context(row.context),
                    precision=context_precision(row.context),
                    text=row.text,
                    order=len(sources),
                    chunkingid=cid,
                    files=[couple.json_path.name],
                )
                sources.append(source)
                continue
            source = par_chunkingid.get(cid)
            if source is None:
                source = Source(
                    key=str(cid),
                    kind=couple.kind,
                    refs=[],
                    context=row.context,
                    canon=canon_context(row.context),
                    precision=context_precision(row.context),
                    text="",
                    order=len(sources),
                    chunkingid=str(cid),
                    files=[],
                )
                par_chunkingid[cid] = source
                sources.append(source)
            source.refs.append((couple_index, row_index))
            if couple.json_path.name not in source.files:
                source.files.append(couple.json_path.name)
            if source.context is None and row.context is not None:
                source.context = row.context
                source.canon = canon_context(row.context)
                source.precision = context_precision(row.context)
            source.text = f"{source.text}\n{row.text}" if source.text else row.text
    return sources
