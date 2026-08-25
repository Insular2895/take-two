# Opportunity score — `pre-opra-v2`

Échelle 0–100, plus haut = opportunité mesurée plus forte. Les entrées prévues sont
rendement espéré et médian, P(profit), P(cible), convexité et écart à chaque baseline.
Chaque métrique est bornée, normalisée et affichée brute. La formule mécanique validée
utilise rendement espéré (25 %), médiane (20 %), P(profit) (20 %), P(cible) (10 %) et
uplift contre buy-and-hold (25 %). Les bornes sont testées en sensibilité ±10 % sur les
poids. La validation concerne le calcul, pas la rentabilité future ; la confiance reste
`LOW` avec dix observations OOS.
