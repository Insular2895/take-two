# Risk score — `pre-opra-v2`

Échelle 0–100, 0 = risque mesuré le plus faible, 100 = extrême. Les entrées prévues
sont CVaR 95 % (25 %), drawdown (20 %), probabilités de pertes 25/50/70/90 % (10 %
chacune), perte quasi totale (10 %) et coût d'exécution/capital (5 %). Les métriques
brutes et la severe-loss ladder restent prioritaires. La formule et sa monotonie sont
testées ; aucune moyenne avec l'opportunity score n'est autorisée.
