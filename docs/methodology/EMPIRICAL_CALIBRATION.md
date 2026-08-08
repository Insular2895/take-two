# Calibration empirique — phase D

Le rapport `reports/pre_opra/empirical_calibration_2026-08-08.json` est un diagnostic
sur données de développement, pas une preuve hors échantillon.

Méthode :

- rendements simples et logarithmiques, volatilité annualisée sur 252 séances ;
- skewness et kurtosis excédentaire par moments empiriques ;
- gaps extrêmes et drawdown sur la trajectoire observée ;
- intervalles descriptifs par bootstrap en blocs de cinq rendements, 1 000 tirages,
  seed `20260808` ;
- GARCH(1,1) et GJR-GARCH(1,1), innovations gaussiennes et Student-t standardisée ;
- grille stationnaire déterministe, log-vraisemblance, AIC, BIC, Ljung-Box à 10
  retards sur résidus standardisés et carrés, et couverture VaR 95 % in-sample.

La grille n'est pas un solveur continu et ne fournit pas de Hessienne fiable. Les
erreurs standards sont donc enregistrées `not_calculable`, jamais fabriquées. AIC,
BIC, Ljung-Box et couverture VaR sont in-sample ; ils ne valident ni la prévision ni
une stratégie. Les modèles doivent encore être figés et testés chronologiquement en
phase E.

Résultat descriptif actuel : 615 rendements, volatilité réalisée annualisée 29,66 %,
kurtosis excédentaire 6,96, plus grand gap négatif -8,68 %, positif +14,05 %, drawdown
maximal 27,66 %. Le bootstrap du rendement logarithmique annualisé traverse zéro
(-19,85 % à +51,02 %), ce qui interdit une lecture confiante de la moyenne historique.

Le meilleur AIC in-sample est celui du GJR-GARCH Student-t, mais ce constat ne choisit
pas le modèle final. Les quatre fits restent `diagnostic_fit_license_blocked`. Heston
reste `BLOCKED_INSUFFICIENT_CALIBRATION_DATA` car l'historique disponible ne contient
aucune IV fournisseur exploitable et n'a pas encore passé les contrôles de surface.
