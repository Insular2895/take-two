# Risk score — `pre-opra-v1`

Échelle 0–100, 0 = risque mesuré le plus faible, 100 = extrême. Les entrées prévues
sont probabilités de pertes sévères, CVaR 95 %, perte maximale, drawdown, gap, theta,
incertitude modèle et stress de liquidité. Les métriques brutes et la severe-loss ladder
restent prioritaires. Bornes et poids sont `draft_to_validate`; aucune moyenne avec
l'opportunity score n'est autorisée.
