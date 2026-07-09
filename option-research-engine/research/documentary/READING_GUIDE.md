# Guide de lecture — résultats de recherche

Date : 2026-07-06
Statut : `active`

## Si tu veux juste savoir où on en est

Lis dans cet ordre :

1. `PHASE_1_REPORT.md` — synthèse générale de la phase documentaire.
2. `CLEAN_USABLE_RULESET_2026.md` — version nettoyée : règles utilisables, bruit exclu, veto 2026.
3. `CURRENTNESS_AUDIT_2026.md` — ce qui est encore actuel / ce qui est obsolète.
4. `STRATEGY_READINESS_MATRIX.md` — ce qu'on peut construire maintenant et ce qui manque.
5. `SOURCE_GAPS.md` — ce qu'il faut encore fournir, ou pas.
6. `CANDIDATE_INDEX.md` — index des règles candidates et revues visuelles.

## Si tu veux relire par livre

### Natenberg — socle volatilité / Greeks / risques

- `visual_reviews/B-NATENBERG-1994-CH04.md` — volatilité, IV, annualisation, distributions.
- `visual_reviews/B-NATENBERG-1994-CH05.md` — edge théorique, delta hedge, coûts.
- `visual_reviews/B-NATENBERG-1994.md` — figures Greeks chapitre 6.
- `visual_reviews/B-NATENBERG-1994-CH08.md` — volatility spreads.
- `visual_reviews/B-NATENBERG-1994-CH09.md` — risk/reward, marge d'erreur, ajustements.
- `visual_reviews/B-NATENBERG-1994-CH13.md` — hedging, collars/fences, portfolio insurance.

### Passarelli — gamma scalping / IV vs RV

- `visual_reviews/B-PASSARELLI-2012-CH13.md` — long gamma, short gamma, theta, hedge deltas.
- `visual_reviews/B-PASSARELLI-2012-VOL-CHARTS.md` — configurations implied/realized volatility.

### McMillan — structures concrètes

- `visual_reviews/B-MCMILLAN-2012-CH03.md` — achat de calls.
- `visual_reviews/B-MCMILLAN-2012-CH07.md` — bull spreads.
- `visual_reviews/B-MCMILLAN-2012-CH09.md` — calendar spreads, revue partielle.
- `visual_reviews/B-MCMILLAN-2012-CH10.md` — butterflies.
- `visual_reviews/B-MCMILLAN-2012-CH11.md` — ratio call spreads, revue partielle.
- `visual_reviews/B-MCMILLAN-2012-CH25.md` — LEAPS.

### Mauboussin — thèse sous-jacent / attentes implicites

- `visual_reviews/B-MAUBOUSSIN-RAPPAPORT-2001.md` — reverse DCF, scénarios, buybacks, M&A.

### Grinold/Kahn — portefeuille, contraintes, coûts

- `visual_reviews/B-GRINOLD-KAHN-1999-CORE.md` — information ratio, contraintes, turnover, coûts.

## Lecture recommandée avant de coder IBKR

1. `STRATEGY_READINESS_MATRIX.md`
2. `CLEAN_USABLE_RULESET_2026.md`
3. `CURRENTNESS_AUDIT_2026.md`
4. `TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md` — cahier des charges appliqué à TTWO / GTA VI.
5. `PHASE_1_REPORT.md`, section “Données minimales à prévoir pour la phase IBKR”
5. Les fiches Natenberg/Passarelli pour définir Greeks, IV/RV et hedge policy
6. Les fiches McMillan pour définir les familles de structures
7. La fiche Mauboussin pour la couche thèse / sous-jacent

## Statut réel

Le corpus est bon pour réfléchir et spécifier. Il n'est pas encore bon pour trader.

La prochaine bonne étape n'est pas “envoyer des ordres”, mais :

```text
contrat de données → moteur read-only → explications → backtest → paper trading → validation humaine
```

## Lecture recommandée pour le cas TTWO / GTA VI

Lis dans cet ordre :

1. `TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md`
2. `STRATEGY_READINESS_MATRIX.md`
3. `CURRENTNESS_AUDIT_2026.md`
4. `visual_reviews/B-MAUBOUSSIN-RAPPAPORT-2001.md`
5. `visual_reviews/B-NATENBERG-1994-CH04.md`
6. `visual_reviews/B-NATENBERG-1994-CH08.md`
7. `visual_reviews/B-PASSARELLI-2012-VOL-CHARTS.md`
8. `visual_reviews/B-MCMILLAN-2012-CH03.md`
9. `visual_reviews/B-MCMILLAN-2012-CH07.md`
