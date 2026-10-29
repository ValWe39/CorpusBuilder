"""Parsing des dates françaises et buckets temporels (FR-016 à FR-019, D9).

Formats reconnus (inventaire des exemples du dépôt) : « J mois AAAA »
(jour paddé ou non) et « mois AAAA » (rangé au premier jour du mois).
Tout le reste est « sans date ».
"""

import re

MOIS = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}

_DATE_JOUR = re.compile(
    r"^(\d{1,2})\s+(" + "|".join(MOIS) + r")\s+(\d{4})$", re.IGNORECASE
)
_DATE_MOIS = re.compile(r"^(" + "|".join(MOIS) + r")\s+(\d{4})$", re.IGNORECASE)

# Tranches croissantes en mois : 6 mois à 1000 ans (FR-016).
TRANCHES = (6, 12, 24, 60, 120, 240, 600, 1200, 12000)

_LIBELLE_TRANCHE = {
    6: "6 mois",
    12: "1 an",
    24: "2 ans",
    60: "5 ans",
    120: "10 ans",
    240: "20 ans",
    600: "50 ans",
    1200: "100 ans",
    12000: "1000 ans",
}


def parse_date(value: object) -> tuple[int, int, int] | None:
    """(année, mois, jour) ou None si absente, vide ou non interprétable.

    Une date sans jour est rangée au premier jour du mois (politique
    utilisateur, FR-018).
    """
    if not isinstance(value, str):
        return None
    texte = value.strip()
    match = _DATE_JOUR.match(texte)
    if match:
        jour = int(match.group(1))
        mois = MOIS[match.group(2).lower()]
        return (int(match.group(3)), mois, jour)
    match = _DATE_MOIS.match(texte)
    if match:
        mois = MOIS[match.group(1).lower()]
        return (int(match.group(2)), mois, 1)
    return None


def _en_mois(date: tuple[int, int, int]) -> int:
    """Position calendaire en mois (alignement des tranches, D9)."""
    annee, mois, _ = date
    return annee * 12 + (mois - 1)


def _libelle_borne(total_mois: int, tranche: int) -> str:
    annee, mois = divmod(total_mois, 12)
    if tranche >= 12:
        return str(annee)
    return f"{annee:04d}-{mois + 1:02d}"


def choose_tranche(dates: list[tuple[int, int, int]]) -> int | None:
    """La plus petite tranche dont le découpage tient en 6 buckets au
    plus (FR-016 corrigée) ; None si aucune date."""
    if not dates:
        return None
    positions = [_en_mois(d) for d in dates]
    bas, haut = min(positions), max(positions)
    for tranche in TRANCHES:
        buckets = haut // tranche - bas // tranche + 1
        if buckets <= 6:
            return tranche
    return TRANCHES[-1]


def fenetre_courte(dates: list[tuple[int, int, int]]) -> bool:
    """Vrai si toutes les dates tiennent dans une fenêtre de 6 mois ou
    moins (FR-019) — les dates vides ne comptent pas."""
    if not dates:
        return True
    positions = [_en_mois(d) for d in dates]
    return max(positions) - min(positions) <= 6


def build_buckets(
    dates: list[tuple[int, int, int]], tranche: int
) -> list[tuple[str, int]]:
    """Répartition calendaire : (libellé « borne..borne », effectif),
    bornes alignées, gauche incluse, droite exclusive (D9)."""
    effectifs: dict[int, int] = {}
    for date in dates:
        position = _en_mois(date)
        index = position // tranche
        effectifs[index] = effectifs.get(index, 0) + 1
    resultat: list[tuple[str, int]] = []
    for index in sorted(effectifs):
        bas = index * tranche
        haut = bas + tranche
        libelle = f"{_libelle_borne(bas, tranche)}..{_libelle_borne(haut, tranche)}"
        resultat.append((libelle, effectifs[index]))
    return resultat


def libelle_bucket(date: tuple[int, int, int], tranche: int) -> str:
    """Libellé « borne..borne » du bucket calendaire d'une date."""
    bas = (_en_mois(date) // tranche) * tranche
    return f"{_libelle_borne(bas, tranche)}..{_libelle_borne(bas + tranche, tranche)}"


def libelle_tranche(tranche: int) -> str:
    """Libellé français de la taille de tranche."""
    return _LIBELLE_TRANCHE.get(tranche, f"{tranche} mois")
