# Onboarding Codex — Point d'entrée officiel du projet

> Ce document est destiné à Codex, qui développera le logiciel **après** la fin de la phase de
> recherche. Le repository est la documentation officielle du projet : le moteur doit pouvoir être
> développé presque uniquement en le lisant.

## 1. Ce que tu construiras

Un moteur d'optimisation d'options (Calls) — pas une IA d'opinion. Quatre piliers :

1. **Règles** extraites de la littérature (`knowledge_base/`, `rules/`).
2. **Données de marché** temps réel (spécification : section 4).
3. **Simulations** — Monte Carlo + scénarios déterministes (`monte_carlo/`, `simulations/`).
4. **Scoring** objectif et explicable (`scoring/`, `decision_engine/04_scoring.md`).

## 2. Interdits absolus

- Aucune règle codée en dur (pas de « trailing stop 20 % », pas de « récupérer la mise à x2 »).
  Tous les paramètres proviennent du moteur d'optimisation alimenté par la base de connaissances.
- Aucune structure de sortie imposée : ni nombre de Calls, ni répartition « proche/moyen/éloigné »,
  ni type (ITM/ATM/OTM/spread). La structure est un **résultat** de l'optimisation.
- Aucun ordre IBKR envoyé sans validation humaine explicite.
- Aucune décision inexplicable : chaque recommandation cite ses règles, scores et hypothèses.

## 3. Architecture logique attendue (spécifiée, non codée)

```
Données marché ─┐
Base de règles ─┼→ Générateur de candidats → Simulateur (MC + déterministe)
Budget         ─┘            ↓                        ↓
                       Moteur de scoring  ←───────────┘
                              ↓
                    Classement des stratégies
                              ↓
              Proposition + justification complète
                              ↓ (validation humaine)
                   Préparation ordre IBKR
                              ↓
              Moteur de maintenance (règles optimisées)
                              ↓
                     Journal de décision → rétroaction sur la base de règles
```

Chaque bloc est spécifié dans `decision_engine/` et `docs/06_moteur_maintenance.md`.

## 4. Données à collecter (Module 3 du cahier des charges)

- **Action** : prix, historique.
- **Options** : strike, échéance, bid, ask, spread, volume, open interest, Delta, Gamma, Theta,
  Vega, volatilité implicite.
- **Entreprise** : résultats, calendrier, SEC, earnings, guidance.
- **Marché** : taux, VIX, volatilité historique.

## 5. Comment lire la base de connaissances

- Format unique des règles : `rules/FORMAT_REGLE.md`. Chaque règle est machine-exploitable :
  Condition (testable) → Variables → Action (exécutable) → Exceptions.
- Ne jamais utiliser une règle en statut `EXTRAITE`, `CONFLIT-OUVERT` ou `REJETÉE`.
  Seules les règles `ACTIVE` (validées ou convergentes) alimentent le moteur.
- La pondération (`docs/04_ponderation_des_regles.md`) fournit le poids de chaque règle dans les votes.

## 6. Ordre de lecture

1. `/README.md` puis `/CONVENTIONS.md`
2. `rules/FORMAT_REGLE.md`
3. `decision_engine/01` → `06`
4. `docs/06_moteur_maintenance.md`
5. `scoring/`, `monte_carlo/`, `simulations/`, `validation/`
6. `research/benchmarks/` (ce que l'open source fait mieux / ce qu'on réutilise)
7. Dossiers de catégories (`greeks/`, `volatility/`, …) selon le module développé

## 7. Critère d'achèvement de la phase de recherche

Le développement ne commence que lorsque : la bibliothèque est traitée, les conflits majeurs sont
tranchés, les protocoles de validation existent, et chaque module du moteur possède une
spécification documentaire complète.
