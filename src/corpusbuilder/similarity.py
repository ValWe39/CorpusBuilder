"""Similarité de texte et regroupement transitif (decision D1, FR-004, FR-006).

Shingles de 5 mots sur tokens normalisés ; score = troncature entière de
`100 × |A ∩ B| / |A ∪ B|` ; union-find pour les groupes transitifs.
"""

import re

TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokens(text: str) -> list[str]:
    """Tokens normalisés : minuscules, séquences de mots Unicode."""
    return TOKEN_RE.findall(text.lower())


def shingles(text: str, size: int = 5) -> set[tuple[str, ...]]:
    """Ensemble des shingles de `size` mots consécutifs."""
    words = tokens(text)
    return {tuple(words[i : i + size]) for i in range(len(words) - size + 1)}


def score(a: set, b: set) -> int:
    """Similarité en points : troncature de 100 × inter/union (D1).

    Un ensemble vide ne peut jamais être similaire (défaut 0).
    """
    union = len(a | b)
    if union == 0:
        return 0
    return int(100 * len(a & b) / union)


class UnionFind:
    """Union-find minimal pour le regroupement transitif (FR-006)."""

    def __init__(self, size: int) -> None:
        self._parent = list(range(size))

    def find(self, item: int) -> int:
        racine = item
        while self._parent[racine] != racine:
            racine = self._parent[racine]
        while self._parent[item] != racine:
            self._parent[item], item = racine, self._parent[item]
        return racine

    def union(self, a: int, b: int) -> None:
        racine_a, racine_b = self.find(a), self.find(b)
        if racine_a != racine_b:
            self._parent[racine_b] = racine_a

    def components(self) -> list[list[int]]:
        """Composantes ordonnées par plus petit membre, membres triés."""
        groupes: dict[int, list[int]] = {}
        for item in range(len(self._parent)):
            groupes.setdefault(self.find(item), []).append(item)
        return [sorted(membres) for _, membres in sorted(groupes.items())]


def jaccard_max_possible(petit: int, grand: int) -> int:
    """Borne supérieure du score pour pré-filtrage : min/max en points."""
    if grand == 0:
        return 0
    return int(100 * petit / grand)
