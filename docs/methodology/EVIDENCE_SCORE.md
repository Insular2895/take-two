# Evidence score — `pre-opra-v2`

Échelle 0–100 de qualité de preuve. Les composants prévus couvrent données réelles,
intégrité point-in-time, calibration, taille OOS, stabilité walk-forward, holdout,
largeur d'intervalle, couverture de régimes, validation des modèles, qualité des données
et pénalité de tests multiples. La formule validée couvre données réelles, intégrité
point-in-time, taille OOS, stabilité/PBO, holdout, DSR, surfaces, calibration et droits.
Un champ bloqué reste indisponible : ses points ne sont ni imputés ni redistribués.
`score_coverage` expose donc directement la fraction calculable.
