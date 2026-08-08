# Surfaces historiques de volatilité — phase H

Statut TTWO : `BLOCKED_MISSING_GOVERNED_INPUTS`.

Chaque quote doit être disponible avant le cutoff de décision. L'IV est convertie en
variance totale, les tranches SVI sont ajustées avec diagnostic d'erreur et test de
papillon, puis le calendrier est contrôlé entre maturités. Les interpolations sont
comptées ; les extrapolations restent uniquement diagnostiques. La stabilité des cinq
paramètres SVI est suivie entre tranches et dates.

Le cache privé contient des bid/ask, mais pas d'IV/delta historiques. Sans courbe de
taux, dividendes/corporate actions point-in-time, convention de forward et licence
validée, une reconstruction fiable serait une invention. Le rapport réel ne publie donc
aucun paramètre SVI ou Heston. Le gate Heston exige au moins 20 dates, quatre maturités,
cinq strikes et un diagnostic d'optimisation contrainte multi-start ; il reste fermé.

Les fixtures synthétiques prouvent seulement la mécanique de fit, les exclusions
anti-lookahead et les contrôles d'arbitrage. Le holdout final et la capacité d'ordre
restent respectivement inutilisé et interdite.
