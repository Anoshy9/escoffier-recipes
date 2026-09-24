#!/usr/bin/env python3
"""Estimateur de loyer — Barrington Road, Brixton (SW9).

Analyse les loyers demandés pour des biens comparables autour de Barrington
Road, les combine avec l'inflation (CPI) et la hausse des loyers à Lambeth
(ONS), puis propose un nouveau loyer mensuel et la hausse correspondante.

Aucune dépendance externe : Python 3.9+ suffit.

Exemples :
    python3 estimateur.py --loyer-actuel 1650
    python3 estimateur.py --loyer-actuel 1400 --type studio
    python3 estimateur.py --type 1ch            # estimation marché seule
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

TYPES = {"studio": "studio", "1ch": "appartement 1 chambre"}


@dataclass
class Comparable:
    adresse: str
    type: str
    loyer_pcm: float
    distance_miles: float
    source: str
    releve: str
    notes: str = ""

    @property
    def poids(self) -> float:
        # Plus le bien est proche de Barrington Road, plus il compte.
        # 0 mile -> 4, 0.5 mile -> 1.33, 1 mile -> 0.8, 1.3 mile -> 0.65
        return 1.0 / (0.25 + self.distance_miles)


@dataclass
class EstimationMarche:
    loyer_marche: float
    bas: float
    haut: float
    nb_comparables: int
    mediane_brute: float


@dataclass
class Recommandation:
    loyer_actuel: float
    loyer_inflation: float
    loyer_tendance_locale: float
    loyer_marche: float
    loyer_recommande: float

    @property
    def hausse_pcm(self) -> float:
        return self.loyer_recommande - self.loyer_actuel

    @property
    def hausse_pct(self) -> float:
        return self.hausse_pcm / self.loyer_actuel


def charger_comparables(chemin: Path) -> list[Comparable]:
    with chemin.open(encoding="utf-8") as f:
        return [
            Comparable(
                adresse=r["adresse"],
                type=r["type"],
                loyer_pcm=float(r["loyer_pcm"]),
                distance_miles=float(r["distance_miles"]),
                source=r["source"],
                releve=r["releve"],
                notes=r.get("notes") or "",
            )
            for r in csv.DictReader(f)
        ]


def charger_indicateurs(chemin: Path) -> dict:
    with chemin.open(encoding="utf-8") as f:
        return json.load(f)


def quantile_pondere(valeurs: list[float], poids: list[float], q: float) -> float:
    """Quantile pondéré avec interpolation linéaire entre les points médians.

    Les valeurs identiques sont fusionnées (poids additionnés) pour que le
    résultat ne dépende pas de l'ordre des annonces."""
    fusion: dict[float, float] = {}
    for v, p in zip(valeurs, poids):
        fusion[v] = fusion.get(v, 0.0) + p
    paires = sorted(fusion.items())
    total = sum(p for _, p in paires)
    cumul = 0.0
    positions = []
    for v, p in paires:
        positions.append(((cumul + p / 2) / total, v))
        cumul += p
    if q <= positions[0][0]:
        return positions[0][1]
    for (q0, v0), (q1, v1) in zip(positions, positions[1:]):
        if q <= q1:
            return v0 + (v1 - v0) * (q - q0) / (q1 - q0)
    return positions[-1][1]


def mediane(valeurs: list[float]) -> float:
    s = sorted(valeurs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def estimer_marche(
    comparables: list[Comparable], type_bien: str, decote_negociation: float
) -> EstimationMarche:
    """Loyer de marché = médiane pondérée par la proximité des loyers demandés,
    corrigée d'une décote (les loyers signés sont un peu sous les prix affichés)."""
    retenus = [c for c in comparables if c.type == type_bien]
    if not retenus:
        raise ValueError(f"Aucun comparable de type '{type_bien}' dans les données.")
    loyers = [c.loyer_pcm for c in retenus]
    poids = [c.poids for c in retenus]
    facteur = 1 - decote_negociation
    return EstimationMarche(
        loyer_marche=quantile_pondere(loyers, poids, 0.5) * facteur,
        bas=quantile_pondere(loyers, poids, 0.25) * facteur,
        haut=quantile_pondere(loyers, poids, 0.75) * facteur,
        nb_comparables=len(retenus),
        mediane_brute=mediane(loyers),
    )


def arrondir(montant: float, pas: int = 5, plafond: float | None = None) -> float:
    """Arrondit au pas le plus proche, sans dépasser le plafond éventuel."""
    arrondi = round(montant / pas) * pas
    if plafond is not None and arrondi > plafond:
        arrondi = (plafond // pas) * pas
    return arrondi


def recommander(
    loyer_actuel: float,
    marche: EstimationMarche,
    cpi: float,
    hausse_locale: float,
    marge_fidelisation: float,
) -> Recommandation:
    """Combine marché et inflation.

    - Plancher : le loyer actuel indexé sur l'inflation (CPI), pour ne pas
      perdre de pouvoir d'achat.
    - Cible : le loyer de marché moins une petite marge de fidélisation
      (garder un bon locataire évite vacance, frais d'agence et travaux).
    - Plafond : le loyer de marché. Depuis le Renters' Rights Act, un
      locataire peut contester une hausse devant le First-tier Tribunal, qui
      ne peut pas fixer un loyer supérieur au loyer de marché.
    """
    loyer_inflation = loyer_actuel * (1 + cpi)
    loyer_tendance = loyer_actuel * (1 + hausse_locale)
    cible = marche.loyer_marche * (1 - marge_fidelisation)

    if loyer_actuel >= marche.loyer_marche:
        recommande = loyer_actuel  # déjà au prix du marché : pas de hausse défendable
    else:
        recommande = min(marche.loyer_marche, max(loyer_inflation, cible))

    return Recommandation(
        loyer_actuel=loyer_actuel,
        loyer_inflation=loyer_inflation,
        loyer_tendance_locale=loyer_tendance,
        loyer_marche=marche.loyer_marche,
        loyer_recommande=recommande if recommande == loyer_actuel
        else arrondir(recommande, plafond=marche.loyer_marche),
    )


# --------------------------------------------------------------------- sortie

def gbp(x: float) -> str:
    return f"£{x:,.0f}".replace(",", " ")


def pct(x: float) -> str:
    return f"{x * 100:+.1f} %"


def afficher_rapport(
    comparables: list[Comparable],
    type_bien: str,
    marche: EstimationMarche,
    ind: dict,
    reco: Recommandation | None,
    decote: float,
    marge: float,
) -> None:
    cpi = ind["cpi_12_mois"]
    lambeth = ind["loyers_lambeth_12_mois"]
    londres = ind["loyers_londres_12_mois"]

    print("=" * 70)
    print(f" ESTIMATION DE LOYER — Barrington Road, Brixton SW9 ({TYPES[type_bien]})")
    print("=" * 70)

    print("\n1. Biens comparables (loyers demandés)")
    print(f"   {'Adresse':<40}{'Loyer':>9}{'Dist.':>8}{'Poids':>7}")
    for c in sorted(
        (c for c in comparables if c.type == type_bien), key=lambda c: c.distance_miles
    ):
        print(
            f"   {c.adresse[:39]:<40}{gbp(c.loyer_pcm):>9}"
            f"{c.distance_miles:>6.1f}mi{c.poids:>7.2f}"
        )

    print("\n2. Indicateurs économiques (ONS)")
    print(f"   Inflation CPI, 12 mois ({cpi['periode']}) : {pct(cpi['valeur'])}")
    print(f"   Loyers Lambeth, 12 mois ({lambeth['periode']}) : {pct(lambeth['valeur'])}"
          f"  (moyenne tous biens {gbp(lambeth['moyenne_pcm'])})")
    print(f"   Loyers Londres, 12 mois ({londres['periode']}) : {pct(londres['valeur'])}")

    print("\n3. Loyer de marché estimé")
    print(f"   Médiane simple des annonces      : {gbp(marche.mediane_brute)} / mois")
    print(f"   Médiane pondérée − {decote:.0%} négociation : {gbp(marche.loyer_marche)} / mois")
    print(f"   Fourchette probable (25e–75e)    : {gbp(marche.bas)} – {gbp(marche.haut)} / mois")

    if reco is None:
        print("\n   Indiquez --loyer-actuel pour obtenir la hausse recommandée.")
        return

    print("\n4. Scénarios pour le nouveau loyer")
    lignes = [
        ("Indexation sur l'inflation (CPI)", reco.loyer_inflation),
        ("Tendance des loyers à Lambeth", reco.loyer_tendance_locale),
        ("Alignement complet sur le marché", reco.loyer_marche),
    ]
    for nom, montant in lignes:
        hausse = montant - reco.loyer_actuel
        print(f"   {nom:<34}{gbp(montant):>9}  ({'+' if hausse >= 0 else '−'}"
              f"{gbp(abs(hausse))}, {pct(hausse / reco.loyer_actuel)})")

    print("\n" + "-" * 70)
    print(f"   LOYER ACTUEL        : {gbp(reco.loyer_actuel)} / mois")
    print(f"   LOYER RECOMMANDÉ    : {gbp(reco.loyer_recommande)} / mois")
    print(f"   HAUSSE              : +{gbp(reco.hausse_pcm)} / mois ({pct(reco.hausse_pct)})"
          f"  soit +{gbp(reco.hausse_pcm * 12)} / an")
    print("-" * 70)

    if reco.hausse_pcm <= 0:
        print("   Le loyer actuel est déjà au niveau du marché ou au-dessus :")
        print("   une hausse risquerait d'être annulée par le tribunal en cas de contestation.")
    else:
        print(f"   Logique : loyer de marché moins {marge:.0%} de marge de fidélisation,")
        print("   jamais sous l'indexation CPI ni au-dessus du loyer de marché.")

    print("\n   Rappels (Angleterre, Renters' Rights Act) : une seule hausse par an,")
    print("   notifiée par formulaire « section 13 » avec 2 mois de préavis. Le")
    print("   locataire peut la contester devant le First-tier Tribunal.")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--loyer-actuel", type=float, help="loyer mensuel actuel en £")
    p.add_argument("--type", choices=TYPES, default="1ch",
                   help="studio ou 1ch (1 chambre + séjour). Défaut : 1ch")
    p.add_argument("--decote", type=float, default=0.02,
                   help="écart moyen entre loyer affiché et loyer signé (défaut 0.02)")
    p.add_argument("--marge-fidelisation", type=float, default=0.03,
                   help="remise sous le marché pour garder le locataire (défaut 0.03)")
    p.add_argument("--comparables", type=Path, default=DATA_DIR / "comparables.csv")
    p.add_argument("--indicateurs", type=Path, default=DATA_DIR / "indicateurs.json")
    args = p.parse_args(argv)

    comparables = charger_comparables(args.comparables)
    ind = charger_indicateurs(args.indicateurs)
    marche = estimer_marche(comparables, args.type, args.decote)
    reco = None
    if args.loyer_actuel:
        reco = recommander(
            args.loyer_actuel,
            marche,
            ind["cpi_12_mois"]["valeur"],
            ind["loyers_lambeth_12_mois"]["valeur"],
            args.marge_fidelisation,
        )
    afficher_rapport(comparables, args.type, marche, ind, reco,
                     args.decote, args.marge_fidelisation)


if __name__ == "__main__":
    main()
