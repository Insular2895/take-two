# Baselines comparables et tests multiples — phase G

Statut : `BLOCKED_INCOMPARABLE_DATA` pour TTWO ; mécanique testée sur fixtures uniquement.

La comparaison impose le même capital, horizon, calendrier, points d'entrée/sortie,
frais, spread et politique de change. Les neuf séries obligatoires sont : cash,
absence de position, sous-jacent, buy-and-hold, call ATM, call à delta fixe, bull call
spread standard, stratégie admissible aléatoire et candidat du moteur. Une ligne
manquante bloque la conclusion au lieu d'être remplacée par une valeur illustrative.

Les écarts candidat-baseline sont appariés par identifiant d'observation. Le rapport
publie rendement, espérance, CVaR 95 %, drawdown, probabilités de profit/cible/perte
forte, Sharpe, Sortino et coûts. L'intervalle bootstrap et le test de permutation sont
appariés ; Holm corrige la famille des huit comparaisons. Le DSR et le PBO sont
rapportés avec l'espace de recherche effectif et sa borne cartésienne déclarée.

La significativité statistique et la matérialité économique sont deux champs séparés.
Le holdout final reste fermé. La licence, l'absence de deltas/IV historiques fiables et
l'absence de trajectoires comparables de toutes les stratégies bloquent l'évaluation
TTWO. Le moteur ne possède aucune capacité d'ordre.
