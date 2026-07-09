# research/benchmarks/ — Analyses comparatives des repositories

## Rôle
Un fichier par repository open source de référence. Chaque fichier répond obligatoirement à
cinq questions :
1. Ce que ce projet fait mieux que nous.
2. Ce qu'il ne fait pas.
3. Ce que nous pouvons réutiliser.
4. Ce que nous devons améliorer.
5. Pourquoi notre architecture sera différente.

## Contenu
`awesome-quant.md`, `qlib.md`, `gs-quant.md`, `machine-learning-for-trading.md`,
`financial-models-numerical-methods.md`, `optrade.md`, `graphvega.md`, `keeks.md`
— puis un fichier par nouveau repo étudié.

## Candidats prioritaires ajoutés

| Repository | Priorité | Statut | Usage envisagé |
|---|---:|---|---|
| OpTrade | 5/5 | `candidate_to_verify` | Recherche options, sélection de contrats, moneyness, expirations, volatilité, pipeline data, expérimentation ML. |
| GraphVega | 4/5 | `candidate_to_verify` | Visualisation P/L, Greeks, scénarios et future UI ; pas candidat moteur. |
| Keeks | 4/5 | `candidate_to_verify` | Kelly, bankroll, drawdown, allocation ; enrichissement du module sizing. |

## Format attendu
Les cinq sections ci-dessus, précédées d'un en-tête d'identification (licence, maturité, techno).
La fiche d'étude détaillée (architecture, algorithmes…) vit à côté, au format
`templates/fiche_repository.md`, et le benchmark s'y réfère.
