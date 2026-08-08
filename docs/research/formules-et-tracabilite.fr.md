# Formules et traçabilité — version française

Date : 2026-08-08  
Registres canoniques : [`formula_registry.yaml`](formula_registry.yaml) et
[`formula_lineage_matrix.md`](formula_lineage_matrix.md)  
Couverture : 25 formules, chacune reliée à une source, une implémentation et un test

## Règles de lecture

- `P` désigne la mesure empirique/réelle utilisée pour les observations et prévisions.
- `Q` désigne la mesure risque-neutre utilisée pour la valorisation sans arbitrage.
- `testé` signifie que le comportement logiciel est couvert ; cela ne signifie pas que le modèle
  prédit correctement TTWO.
- `validé numériquement` signifie qu’une comparaison ou convergence numérique explicite a été
  passée dans le périmètre déclaré.
- Les formules exactes, hypothèses détaillées, pages et symboles restent dans le YAML canonique.

## Fondations, prix et volatilité implicite

| ID | Sens français et formule | Source principale | Code et tests | Niveau |
| --- | --- | --- | --- | --- |
| `FORM-MEASURE-CHANGE-001` | Frontière de mesure : valoriser sous `Q`, prévoir empiriquement sous `P`, sans conversion implicite | Björk ; Andersen–Piterbarg | `quantitative/contracts.py`, `intelligence/stochastic.py`, `simulation/legacy_models.py` ; `test_quantitative_foundations.py` | testé |
| `FORM-DISCOUNT-FACTOR-001` | Facteur d’actualisation continu : `D(t,T)=exp(-r(T-t))` avec convention Actual/365 Fixed | Björk ; Andersen–Piterbarg | `quantitative/contracts.py::discount_factor` ; `test_quantitative_foundations.py` | testé |
| `FORM-BS-PRICE-001` | Prix et Greeks de premier ordre d’une option européenne Black–Scholes sous `Q` | Björk, ch. 12.2 | `pricing.py`, `american.py` ; parité call-put et comparaison QuantLib | validé numériquement |
| `FORM-FD-CONVERGENCE-001` | Une différence finie n’est acceptée qu’après raffinement strict de grille et accord successif dans une tolérance déclarée | Süli–Mayers ; Andersen–Piterbarg | `quantitative/numerical_validation.py` ; `test_quantitative_foundations.py` | testé |
| `FORM-IV-ROOT-001` | Volatilité implicite comme racine de `prix_modèle(vol)-prix_cible=0` dans un intervalle vérifié | Süli–Mayers, §1.6 | `quantitative/implied_volatility.py`, `american.py` ; `test_implied_volatility_svi.py` | validé numériquement |

## Surface de volatilité et séries temporelles

| ID | Sens français et formule | Source principale | Code et tests | Niveau |
| --- | --- | --- | --- | --- |
| `FORM-SVI-RAW-001` | Variance totale SVI brute : `w(k)=a+b(ρ(k-m)+sqrt((k-m)^2+σ²))` | Gatheral–Jacquier, équation 3.1 | `quantitative/svi.py` ; `test_implied_volatility_svi.py` | testé synthétiquement |
| `FORM-SVI-ARBITRAGE-001` | Contrôles : densité papillon `g(k)>=0` et variance totale non décroissante avec l’échéance | Gatheral–Jacquier | `quantitative/svi.py` ; cas de violations connus | testé sur grille finie |
| `FORM-EWMA-001` | Variance conditionnelle exponentielle : `h_t=λh_(t-1)+(1-λ)r_(t-1)²` | Tsay | `quantitative/calibration.py` ; `test_quantitative_calibration.py` | testé |
| `FORM-GARCH-001` | GARCH(1,1) : `h_t=ω+αε_(t-1)²+βh_(t-1)`, avec `α+β<1` | Tsay, équation 3.16 | `quantitative/calibration.py` ; récupération synthétique et diagnostics | testé |

## Incertitude, Monte Carlo et rééchantillonnage

| ID | Sens français et formule | Source principale | Code et tests | Niveau |
| --- | --- | --- | --- | --- |
| `FORM-WILSON-001` | Intervalle de Wilson pour une proportion binomiale ; un zéro observé ne prouve pas un risque nul | Wilson | `research_statistics.py`, `simulation/uncertainty.py` ; tests statistiques et simulation | testé |
| `FORM-MC-SE-001` | Erreur standard de moyenne Monte Carlo calculée sur des réplications indépendantes | Glasserman | `intelligence/valuation.py`, `simulation/uncertainty.py` | testé |
| `FORM-MC-CI-001` | Intervalle Monte Carlo asymptotique ; il couvre l’erreur de simulation, pas l’erreur de modèle | Glasserman | `intelligence/valuation.py` ; `test_intelligence_v11.py` | testé |
| `FORM-BOOTSTRAP-001` | Intervalle bootstrap percentile iid | Wasserman | `research_statistics.py` ; `test_research_statistics.py` | testé |
| `FORM-CONTROL-VARIATE-001` | Estimateur `Y-b(X-E[X])`, avec coefficient de variance minimale estimé | Glasserman, §4.1 | `simulation/uncertainty.py` ; mesure avant/après | testé |
| `FORM-ANTITHETIC-001` | Estimateur par paires antithétiques ; la moyenne de paire est l’unité indépendante | Glasserman, §4.2 | `simulation/uncertainty.py` | testé |
| `FORM-BLOCK-BOOTSTRAP-001` | Bootstrap circulaire par blocs pour conserver une dépendance locale | Künsch | `simulation/uncertainty.py` ; seed et taille de bloc explicites | testé |

## Incertitude de modèle et probabilités

| ID | Sens français et formule | Source principale | Code et tests | Niveau |
| --- | --- | --- | --- | --- |
| `FORM-PREDICTIVE-MIXTURE-001` | Décomposition d’un mélange prédictif entre variance interne aux modèles, dispersion entre modèles et erreur Monte Carlo | McElreath | `quantitative/model_uncertainty.py`, `intelligence/valuation.py` | testé, diagnostic seulement |
| `FORM-PROBABILITY-CALIBRATION-001` | Score de Brier, log-loss, classes de calibration, ECE et intervalles de Wilson | Brier ; McElreath | `quantitative/probability_calibration.py`, `intelligence/backtesting.py` | testé synthétiquement |
| `FORM-SCENARIO-MIXTURE-001` | Espérance de scénario conditionnel issue de la loi des probabilités totales | Blitzstein–Hwang | `intelligence/event_scenarios.py` ; `test_sequential_event_decision.py` | testé |
| `FORM-BELIEF-SWITCH-001` | Seuil linéaire d’indifférence lorsque la croyance d’un scénario varie et que les autres restent proportionnelles | Blitzstein–Hwang | `intelligence/event_scenarios.py` | testé |

## Optimisation et validation de recherche

| ID | Sens français et formule | Source principale | Code et tests | Niveau |
| --- | --- | --- | --- | --- |
| `FORM-PARETO-DOMINANCE-001` | Une allocation domine une autre si elle n’est pire sur aucun objectif et meilleure sur au moins un | Boyd–Vandenberghe | `optimization/allocation_pareto.py` ; frontière exhaustive | testé |
| `FORM-ROBUST-ALLOCATION-OBJECTIVE-001` | Objectif scalaire versionné, pondéré ou pire cas, utilisé pour classer sans remplacer la frontière de Pareto | Boyd–Vandenberghe | `optimization/allocation_pareto.py`, `intelligence/optimizer.py` | testé |
| `FORM-PBO-001` | Diagnostic de probabilité de surapprentissage du backtest, avec rangs moyens et gagnants ex æquo moyennés | Bailey et al. | `validation/pbo.py` ; `test_validation_protocol_v10.py` | testé, conformité intégrale à revoir |
| `FORM-PLACEBO-001` | Placebo par permutation des signaux relativement aux rendements et test de signaux retardés | Wasserman | `validation/placebo.py` ; `test_validation_protocol_v10.py` | testé |
| `FORM-DSR-001` | Probabilité de Sharpe déflaté corrigeant approximativement essais multiples et non-normalité | Bailey–López de Prado | `research_statistics.py` ; `test_research_statistics.py` | testé, approximation déclarée |

## Ce que la traçabilité garantit

Le validateur CI vérifie que :

1. chaque `Formula ID` est unique et présent dans les registres attendus ;
2. chaque source référencée existe ;
3. chaque fichier d’implémentation et de test existe ;
4. les symboles déclarés sont retrouvables ;
5. le niveau de preuve ne dépasse pas le niveau autorisé par ses dépendances.

La traçabilité garantit qu’une affirmation est reliée à une provenance et à une vérification
logicielle. Elle ne garantit ni l’adéquation du modèle au marché TTWO, ni la qualité de données
futures, ni la rentabilité d’une stratégie.

