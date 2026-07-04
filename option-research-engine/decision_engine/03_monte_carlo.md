# Monte Carlo dans le moteur de décision

## 1. Rôle

Pour chaque structure candidate, générer des milliers de trajectoires du sous-jacent et de la
volatilité afin d'obtenir la **distribution** des résultats (pas une moyenne unique).

## 2. Variables simulées

Évolution du prix, évolution de la volatilité, temps, scénarios de baisse / hausse / stagnation,
événements (earnings), retards et accélérations de thèse.

## 3. Exigences documentées (à alimenter par `monte_carlo/` et les livres)

- Choix des processus (GBM de base ; Heston/SABR si la littérature et les benchmarks le justifient).
- Techniques de réduction de variance (antithétiques, control variates) — cf. Glasserman.
- Nombre de trajectoires : déterminé par un critère de convergence documenté, pas par une constante.
- Repricing de l'option le long des trajectoires (modèle de pricing cohérent avec `valuation/` et
  `research/benchmarks/financial-models-numerical-methods.md`).

## 4. Sorties par stratégie

Espérance de gain, probabilité de gain, quantiles de perte (dont perte maximale), distribution des
temps de sortie selon les règles de maintenance simulées, sensibilité aux hypothèses (stress).

## 5. Scénarios déterministes complémentaires

Une grille de scénarios fixes (ex. ±10 %, ±20 %, IV ±X points, à T+7/T+30/échéance) est toujours
calculée en complément, pour l'explicabilité humaine des propositions.
