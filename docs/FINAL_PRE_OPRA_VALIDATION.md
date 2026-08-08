# Validation finale pré-OPRA — clôtures C1 à C13

Résultat au 8 août 2026 : `PRE_OPRA_RESEARCH_COMPLETE`,
`NO_POSITION_RECOMMENDED` et verdict dérivé
`ENGINE_NOT_PROVEN_SUPERIOR`.

Le moteur a exploité les données non-OPRA localement accessibles : 20 884 observations
options uniques sur 250 dates, 631 barres TTWO, 385 courbes de taux, 283 taux EUR/USD et
14 événements point-in-time. Les données sous licence restent privées et hors Git.

Le panel comparable contient neuf stratégies et 25 observations alignées. Dix résultats
futurs non chevauchants alimentent le walk-forward de développement. V10 produit
−90,4 % composé OOS contre +25,1 % pour buy-and-hold ; aucune supériorité ne survit à
la correction de Holm. Ce constat n'a pas déclenché de retuning.

Les cinq scores `pre-opra-v2` sont calculés : opportunité 37,1 (couverture 100 %),
risque 49,5 (100 %), preuve 40,3 (80 %), accord modèles 31,5 (50 %) et qualité
d'exécution 50,5 (75 %). Les composants absents gardent leurs poids ; aucune note
neutre ni renormalisation n'est appliquée.

À lire en priorité :

- dashboard autonome : `reports/pre_opra/final_pre_opra_report_2026-08-08.html` ;
- rapport lisible : `reports/pre_opra/final_pre_opra_report_2026-08-08.md` ;
- rapport machine A–N : `reports/pre_opra/final_pre_opra_report_2026-08-08.json` ;
- verdict V10 : `reports/pre_opra/engine_verdict_2026-08-08.json` ;
- scores : `reports/pre_opra/five_scores_2026-08-08.json` ;
- sévérité et gates : `reports/pre_opra/severity_and_gate_sensitivity_2026-08-08.json` ;
- registre des clôtures : `docs/audits/PRE_OPRA_BLOCKER_CLOSURE.md`.

Limites irréductibles actuelles : confirmation humaine des droits du compte historique,
nouvel échantillon réellement futur pour atteindre le minimum formel et conserver un
holdout intact, puis entitlement/identifiants OPRA pour la Phase M. Le holdout reste
`UNOPENED`, la Phase M n'est pas démarrée et les invariants sont
`transmit=false`, `what_if=true`, `order_capability=forbidden`.
