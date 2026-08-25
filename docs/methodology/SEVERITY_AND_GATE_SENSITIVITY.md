# Sévérité du payoff et sensibilité des gates — phase K

La severe-loss ladder publie toujours, lorsqu'une distribution admissible existe,
P(perte > 10 %, 25 %, 50 %, 70 %, 90 % et 99 %), avec moyenne, médiane, pire retour,
CVaR 95 % et P(profit). Les probabilités doivent décroître avec la sévérité.

La sensibilité réévalue le même ensemble de candidats sous plusieurs seuils explicites
d'opportunité, risque, preuve et exécution. Elle montre les candidats passants, le
meilleur candidat et la fréquence de `NO_POSITION_RECOMMENDED`. Les seuils sont
`draft_to_validate`, non des décisions.

Pour TTWO, aucune distribution candidat comparable n'existe. Le meilleur candidat
bloqué est donc explicitement `UNAVAILABLE`, avec ses gates indisponibles : choisir un
ancien candidat de fixture serait trompeur. La grille structurelle sur ensemble vide
produit 100 % de no-position, étiqueté `pipeline_blocked_empty_candidate_pool`; ce n'est
pas une estimation de performance financière. Holdout fermé, ordres interdits.
