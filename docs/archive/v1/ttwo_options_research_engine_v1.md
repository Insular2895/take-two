# Architecture — TTWO options research engine V1

Statut : `implemented_read_only_to_validate`

## Objectif

Transformer un paquet de données horodatées en comparaison auditable de structures TTWO sans
produire de recommandation, taille réelle ou instruction d'ordre.

```text
fixture / futur adaptateur IBKR read-only
                |
                v
       MarketDataBundle typé
                |
                v
       génération des candidats
                |
                v
    pricing + coûts + risques + Greeks
                |
                v
 scénarios déterministes + Monte-Carlo seedé
                |
                v
       veto explicables avant score
                |
                v
 score décomposé des seuls candidats non bloqués
                |
                v
 JSON canonique + rapport Markdown + journal
```

## Modules

- `domain.py` : modèles Pydantic, enums et statuts.
- `data.py` : provider de fixture et frontière broker read-only.
- `candidates.py` : `no-trade`, action, calls, puts et verticals bornés.
- `pricing.py` : Black-Scholes indicatif, bid/ask, coûts, payoff, max gain/perte, break-even et
  Greeks agrégés avec le multiplicateur du contrat.
- `scenarios.py` : temps/spot/IV, gaps, IV crush, délai, ex-dividende, liquidité et Monte-Carlo.
- `validation.py` : provenance, fraîcheur, contrat, liquidité, événement, coût, marge, perte
  maximale, risque non borné et couverture du catalyseur.
- `fundamentals.py` : adéquation thèse/catalyseur, séparée de la mécanique optionnelle.
- `scoring.py` : seize composantes visibles, moyenne simple et front de Pareto.
- `engine.py`, `reporting.py`, `cli.py` : orchestration et artefacts.

## Invariants de sécurité

1. Le veto est appliqué avant le score ; un candidat `blocked` n'a pas de score.
2. Le multiplicateur n'est jamais supposé égal à 100 : il vient de `OptionContract`.
3. Une jambe longue paie l'ask ; une jambe courte reçoit le bid ; coûts et slippage sont séparés.
4. Les structures à risque non borné sont bloquées.
5. Toute structure avec jambe courte requiert marge connue et revue assignment/pin risk.
6. Le gateway broker lève `ForbiddenOperation` sur submit/modify/cancel.
7. Aucun statut `live_order_ready` n'existe dans le domaine ou les rapports.

## Score V1

Le total est la moyenne non pondérée de : thèse, couverture catalyseur, payoff attendu, qualité du
payoff, perte maximale, sensibilité aux hypothèses, liquidité, coûts, complexité,
assignment/early exercise, contexte IV/RV, skew/term structure, marge, carry, robustesse adverse
et confiance des données. Il sert à comparer les hypothèses après veto, jamais à autoriser une
action. Le rapport expose aussi les candidats non dominés sur huit dimensions risque/rendement.

La liquidité est une heuristique documentée : 55 % spread relatif, 20 % open interest, 15 % volume
et 10 % taille affichée. Un spread relatif supérieur à 35 %, un volume nul ou un open interest nul
déclenche un veto V1.

## Séparation des responsabilités

La thèse fondamentale ne modifie jamais les payoffs ou Greeks. Elle n'agit que sur les composantes
`thesis_fit` et `catalyst_coverage`. Le pricing ne connaît ni IBKR ni les règles de classement.
