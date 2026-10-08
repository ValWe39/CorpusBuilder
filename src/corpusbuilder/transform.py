"""Transformation document/corpus -> lignes ChunkRow (FR-011 à FR-013)."""

from .discovery import Candidate
from .models import ChunkRow, CoupleKind, CoupleRejected


def build_rows(candidate: Candidate) -> list[ChunkRow]:
    """Construit les lignes aplaties selon le format du couple."""
    if candidate.kind is CoupleKind.DOCUMENT:
        return document_rows(candidate.data)
    return corpus_rows(candidate.data)


def document_rows(data: dict) -> list[ChunkRow]:
    """FR-011, FR-012 : une ligne par chunk, ordre des chunks préservé.

    `ref` est conservée telle quelle (clarification 2026-10-08) ; les
    clés absentes ou nulles sont omises ; `params`, `length`,
    `boundary`, `position_in_part`, `atomic`, `structure` et
    `typologie` ne sont pas repris.
    """
    document = data.get("document")
    chunks = data.get("chunks")
    if not isinstance(document, dict) or not document.get("path"):
        raise CoupleRejected("document sans 'path' obligatoire")
    if not isinstance(chunks, list) or not chunks:
        raise CoupleRejected("document sans chunks")
    rows: list[ChunkRow] = []
    for chunk in chunks:
        if not isinstance(chunk, dict) or "ref" not in chunk or "text" not in chunk:
            raise CoupleRejected("chunk sans 'ref' ou 'text'")
        rows.append(
            ChunkRow(
                text=chunk["text"],
                ref=chunk["ref"],
                path=document["path"],
                part=chunk.get("part"),
                page=chunk.get("page"),
                title=document.get("title"),
                context=document.get("context"),
                chunkingid=document.get("chunkingid"),
            )
        )
    return rows


def corpus_rows(data: list) -> list[ChunkRow]:
    """FR-013 : structure et ordre des lignes d'un corpus réingéré préservés."""
    if not data:
        raise CoupleRejected("corpus vide")
    rows: list[ChunkRow] = []
    for item in data:
        if not isinstance(item, dict):
            raise CoupleRejected("ligne de corpus invalide (pas un objet)")
        manquantes = [cle for cle in ("text", "ref", "path") if item.get(cle) is None]
        if manquantes:
            raise CoupleRejected(
                f"ligne de corpus incomplète ({', '.join(manquantes)})"
            )
        rows.append(
            ChunkRow(
                text=item["text"],
                ref=item["ref"],
                path=item["path"],
                part=item.get("part"),
                page=item.get("page"),
                title=item.get("title"),
                context=item.get("context"),
                chunkingid=item.get("chunkingid"),
            )
        )
    return rows
