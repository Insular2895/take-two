# Opportunity score — `pre-opra-v1`

Échelle 0–100, plus haut = opportunité mesurée plus forte. Les entrées prévues sont
rendement espéré et médian, P(profit), P(cible), convexité et écart à chaque baseline.
Chaque métrique est bornée, normalisée et affichée brute. Les poids doivent totaliser
un et restent `draft_to_validate` tant que corrélations, double comptage et sensibilité
n'ont pas été évalués sur le dataset de développement. Aucun score TTWO n'est publié
avant cette validation ; un fort score ne masque jamais le risque.
