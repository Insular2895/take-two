# Plan — TTWO / GTA VI options research engine V1

Date : 2026-07-18
Statut : `implemented_read_only_to_validate`
Portée : repo `/Users/insular/take two/take-two`

## Inventaire de l'existant

- Le repo est d'abord un corpus documentaire `option-research-engine/` sur options, Greeks,
  volatilité, scoring, evidence et moteur de décision.
- Le worktree contient des modifications utilisateur non commitées dans `README.md`,
  `option-research-engine/README.md`, `tool_usage.md`, `evidence/README.md` et plusieurs docs de
  transcription PDF. Ces changements doivent être préservés.
- Aucun stack applicatif engagé n'est présent : pas de `pyproject.toml`, pas de package `src/`, pas
  de tests exécutables existants.
- `CONVENTIONS.md` n'existe pas à la racine ; la convention effective lue est
  `option-research-engine/CONVENTIONS.md`.
- Le corpus utile pour la V1 est :
  `CLEAN_USABLE_RULESET_2026.md`, `STRATEGY_READINESS_MATRIX.md`, `CURRENTNESS_AUDIT_2026.md`,
  `TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md`, `RULES_2026_REVIEW_INDEX.md`,
  `ATOMIC_RULE_BACKLOG_PLAN.md`, `references/source_weighting.md`, les règles atomiques
  `R-*`, `decision_engine/01_selection_strategie.md` à `06_classement.md`, et les revues
  Natenberg, Passarelli, McMillan, Mauboussin/Rappaport et Grinold/Kahn.

## Décision de stack

- Python `>=3.11`, car aucun stack n'est déjà engagé et la demande l'indique comme défaut.
- `pyproject.toml` avec package `src/take_two_options`.
- Pydantic v2 pour les contrats de données typés et sérialisables.
- Typer pour la CLI.
- pytest pour les tests offline.
- Ruff pour lint/format check.
- mypy pour typecheck.
- Pas de dépendance numérique lourde en V1 : Black-Scholes, payoff, scénarios et Monte-Carlo simple
  sont implémentés avec la bibliothèque standard pour garder l'installation petite et auditée.

Justification : la V1 doit être déterministe, lisible, read-only et indépendante d'IBKR. Les
connecteurs broker/live seront des adaptateurs, pas le cœur métier.

## Architecture proposée

```text
src/take_two_options/
  domain.py          modèles Pydantic et enums
  data.py            interfaces read-only + fixtures
  validation.py      veto explicables avant scoring
  pricing.py         payoff, Greeks, coûts, max gain/loss, break-even
  scenarios.py       scénarios déterministes + Monte-Carlo reproductible
  fundamentals.py    couche thèse/valuation séparée
  candidates.py      génération no-trade, action, call, put, verticals
  scoring.py         score décomposé + classement Pareto simple
  reporting.py       sortie JSON, Markdown et journal de décision
  cli.py             commandes analyze/report/schema
```

## Contrats de données

Modèles minimaux :

- `UnderlyingSnapshot`
- `FundamentalSnapshot`
- `OptionContract`
- `OptionQuote`
- `CorporateAction`
- `MarketEvent`
- `PortfolioState`
- `StrategyLeg`
- `StrategyCandidate`
- `RiskMetrics`
- `ExecutionEstimate`
- `RuleEvaluation`
- `EvidenceReference`
- `DecisionReport`

Règles de contrat :

- Le multiplicateur vient toujours de `OptionContract.multiplier`.
- Le statut `adjusted_contract` et le `deliverable` sont obligatoires pour tout contrat option.
- Toute donnée instable porte `timestamp`, `as_of`, `freshness` et `is_stale`.
- Les règles documentaires non `VALIDATED` ou bloquées ne peuvent pas scorer activement.
- Une donnée provenant d'un sidecar PDF `blocked`, `human_review_required`, `unextractable` ou
  `image_only` déclenche un veto.

## Modules et dépendances

- `data` ne dépend pas de `pricing` ni de `scoring`.
- `validation` dépend seulement des modèles et des règles lues/encodées.
- `pricing` ne connaît pas IBKR.
- `candidates` compose les contrats et quotes disponibles.
- `scoring` reçoit uniquement des candidats déjà validés.
- `reporting` consomme des `DecisionReport` sérialisables.
- `cli` orchestre les fixtures et écrit les sorties.

## Phases d'implémentation

1. Créer `pyproject.toml`, package, modèles et exceptions `ForbiddenOperation`.
2. Ajouter fixtures TTWO reproductibles hors ligne.
3. Implémenter payoff, debit/credit executable, max gain/loss, break-even et Greeks agrégés.
4. Implémenter les veto avant scoring.
5. Générer no-trade, action, achat call, achat put, bull/bear vertical spread.
6. Ajouter scénarios spot/temps/IV, IV crush/expansion, gap, delay, ex-dividend, stress liquidité et
   Monte-Carlo seedé.
7. Ajouter scoring décomposé, classement et statuts finaux.
8. Ajouter CLI JSON/Markdown/journal.
9. Ajouter tests unitaires, intégration et propriétés simples offline.
10. Mettre à jour README, architecture, contrat de données, guide fixtures/IBKR read-only, limites,
    stratégie de tests, changelog et exemple de rapport.

## Stratégie de tests

- Unitaires : payoff par stratégie, debit/credit, coûts, Greeks, break-even, max gain/loss.
- Veto : stale, quote absente, multiplicateur/deliverable inconnu, contrat ajusté, marge inconnue,
  earnings/dividendes non traités, risque non borné, règle non validée, provenance manquante.
- Intégration : scénario TTWO fixture complet, sortie JSON, rapport Markdown.
- Propriétés simples : payoff long call monotone en spot, long put monotone inverse, vertical call
  borné par ses strikes, Monte-Carlo reproductible par seed.
- Sécurité : aucune méthode d'ordre opérationnelle ; `ForbiddenOperation` est levée.

## Risques et limites

- La V1 utilise des fixtures et ne fournit aucune donnée live TTWO.
- Le pricing Black-Scholes sert à la recherche européenne indicative ; les options actions US,
  dividendes, early exercise, assignment et pin risk restent explicitement séparés et signalés.
- Les thresholds de liquidité/score sont conservateurs et documentés comme heuristiques V1, pas
  comme règles de trading validées.
- Le corpus documentaire est `draft_to_validate` pour TTWO ; les résultats restent
  `research_candidate`, `human_review_required`, `blocked` ou `no_trade`.
- Aucune recommandation, taille réelle, ordre réel ou `live_order_ready` n'est produit.

## Critères d'acceptation

- Un scénario TTWO complet fonctionne avec fixtures.
- Le moteur compare au minimum no-trade, action, call, put et vertical.
- Chaque résultat contient règles, preuves, hypothèses, données d'entrée, veto ou score.
- Les données incomplètes déclenchent un veto explicable.
- Aucun multiplicateur n'est hardcodé.
- Aucun ordre ne peut être envoyé.
- Tests, lint et typecheck passent localement ou les limites d'environnement sont documentées.
- Installation, CLI et sorties JSON/Markdown sont documentées.
- Les limites et données manquantes sont visibles dans les rapports.

## Hors scope explicite

- Envoi d'ordres réels.
- Sizing réel de portefeuille.
- Activation automatique de short gamma, ratio/backspread, gamma scalping live ou risque non borné.
- Connexion IBKR live obligatoire en V1.
- Backtest historique complet.
- UI web.
- Promotion automatique des 216 candidats documentaires ou des 365 blocs `to_review`.

## Résultat d'implémentation

Implémenté le 2026-07-18 dans `src/take_two_options/` avec fixture offline, CLI, rapports
JSON/Markdown/journal et documentation. Validation finale locale : 29 tests, Ruff et mypy passent.
Le moteur reste sans donnée live, sans sizing réel et sans capacité d'ordre.
