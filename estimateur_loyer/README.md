# Estimateur de loyer : Barrington Road, Brixton (SW9)

Petit outil en ligne de commande (Python 3.9+, sans dépendance externe). Il estime
le loyer de marché d'un studio ou d'un appartement d'une chambre autour de Barrington
Road, le combine avec l'inflation et propose un nouveau loyer.

## Utilisation

```bash
python3 estimateur.py --loyer-actuel 1650            # appartement 1 chambre (défaut)
python3 estimateur.py --loyer-actuel 1300 --type studio
python3 estimateur.py                                 # estimation du marché seule
```

Options : `--decote` (écart entre loyer affiché et loyer signé, 2 % par défaut),
`--marge-fidelisation` (remise sous le marché pour garder le locataire, 3 % par défaut).

## Méthode

1. **Marché** : médiane des loyers demandés dans `data/comparables.csv`, pondérée
   par la proximité (poids = 1 / (0,25 + distance en miles)), moins la décote de négociation.
2. **Inflation** : loyer actuel × (1 + CPI sur 12 mois, ONS).
3. **Recommandation** : loyer de marché moins la marge de fidélisation. Le résultat
   ne descend jamais sous l'indexation CPI et ne dépasse jamais le loyer de marché.
   Le tribunal peut en effet ramener au loyer de marché une hausse contestée.
   Si le loyer actuel atteint déjà le marché, l'outil ne propose aucune hausse.

## Mettre à jour les données

- `data/comparables.csv` : ajoutez ou retirez des annonces (Rightmove, Zoopla, OpenRent…).
  Les distances à Barrington Road sont des approximations à vol d'oiseau.
- `data/indicateurs.json` : CPI et indice des loyers ONS. L'ONS les publie chaque mois.

Données relevées en septembre 2026. Il s'agit d'une aide à la décision, pas d'une expertise.
