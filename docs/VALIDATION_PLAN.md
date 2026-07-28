# Plan de validation V11.1

## Séparation des preuves

- Unit/integration/property tests prouvent les invariants logiciels.
- Les fixtures prouvent la mécanique et la reproductibilité, pas la performance.
- La calibration in-sample estime des paramètres, sans prouver le pouvoir prédictif.
- Le walk-forward et le holdout mesurent le comportement hors échantillon.
- Le paper trading mesure les écarts entre décision, quote, remplissage et coûts.
- Une décision de promotion exige une validation humaine explicite.

## Matrice de validation

| Domaine | Test actuel | Preuve attendue avant promotion |
| --- | --- | --- |
| Données | schéma, timezone, cutoff, unités, doublons, hash | historique autorisé, audit de disponibilité, politique corporate actions |
| Événements | règles déterministes, preuve, expiry, contradictions | revue annotée, faux positifs/négatifs, stabilité temporelle |
| Bayes | bornes, somme à 1, waterfall, caps, sensibilité | calibration des likelihoods, Brier, log-loss, ECE |
| Modèles | seeds, erreurs numériques, convergence, arbitrage local vol | erreurs de calibration, stabilité paramètres, diagnostics Heston |
| Stratégies | payoff, coûts prudents, Greeks, structures bornées | quotes réelles, contrats disponibles à la date, coûts réels |
| Allocation | énumération entière, budget, pertes, concentration, Greeks | objectifs validés, limites risk approuvées, stabilité des rangs |
| Monitoring | replay multi-date, règles et actions explicatives | trajectoires paper, qualité des données, latence et incidents |
| Sécurité | scan global d’exécution, secrets, HTML sans réseau | revue indépendante, threat model, procédure d’incident |

## Protocole historique

1. Geler le dataset avec hash, version, licence, timezone et cutoff.
2. Exclure toute observation connue après la décision.
3. Construire des fenêtres rolling ou expanding avec embargo.
4. Garder le holdout final verrouillé ; aucune sélection de paramètre dessus.
5. Évaluer cash, sous-jacent, call ATM, call à delta fixe, spread standard,
   stratégie aléatoire admissible, modèle et `NO_TRADE`.
6. Conserver l’oracle hindsight comme borne descriptive, jamais comme stratégie
   exploitable ni comme critère du holdout.
7. Mesurer rendement moyen/médian, profit, perte totale, drawdown, VaR/CVaR,
   Brier, log-loss, ECE, turnover, coûts et rejets pour données insuffisantes.

## Seuils à valider

Les seuils d’acceptation, tailles d’échantillon, tolérances de calibration, durée paper
et limites de risque sont `draft_to_validate`. Le logiciel les expose mais ne les
transforme pas en décision projet.
