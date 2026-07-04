# Construction du score

## 1. Chaîne officielle

```
Espérance de gain → Probabilité de gain → Risque → Liquidité → Coût → Robustesse → Score final
```

Chaque composant est calculé indépendamment, normalisé, puis agrégé.

## 2. Composants

| Composant | Définition | Source |
|---|---|---|
| Espérance | Moyenne de la distribution simulée, ajustée des coûts | Monte Carlo |
| Probabilité | P(gain > 0) et P(gain > seuil de règle) | Monte Carlo |
| Risque | Perte maximale, quantiles de perte, drawdown simulé | Monte Carlo + `risk/` |
| Liquidité | Spread relatif, volume, open interest | Données marché + règles `OPTIONS` |
| Coût | Prime, frictions, coût des maintenances anticipées | `02_comparaison_options.md` |
| Robustesse | Stabilité du score sous perturbation des hypothèses | Stress tests (`validation/`) |

## 3. Pondérations

Les pondérations entre composants ne sont **pas** arbitraires : elles sont déduites de la
littérature (`rules/DECISION/`, `rules/MM/`) puis calibrées et validées par simulation
(`validation/`). Toute pondération est documentée et versionnée dans `scoring/`.

## 4. Exigences

- Deux exécutions sur les mêmes données donnent le même score (reproductibilité, graine fixée).
- Le score est décomposable : l'interface doit pouvoir afficher la contribution de chaque composant.
- Le score intègre l'espérance **ajustée du risque** comme objectif premier (principe fondamental).
