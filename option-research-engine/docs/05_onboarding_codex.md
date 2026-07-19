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
- Aucune décision sans dossier de preuve dans `evidence/` : sources, règles, contradictions,
  simulations favorables/défavorables et blocages live/broker.
- Aucun chiffre provenant d'un tableau, d'une formule ou d'un graphique technique ne doit être
  utilisé si son sidecar est `blocked`, `human_review_required`, `unextractable` ou `image_only`.

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
- Ne jamais utiliser une règle en statut `DRAFT`, `EXTRACTED`, `CONTRADICTED` ou `DEPRECATED`.
  Seules les règles `VALIDATED`, puis non bloquées par les données live/broker, alimentent le moteur.
- La pondération (`docs/04_ponderation_des_regles.md`) fournit le poids de chaque règle dans les votes.
- La hiérarchie des sources (`references/source_weighting.md`) indique pourquoi livres spécialistes,
  sources officielles, repos GitHub et blogs ne pèsent pas pareil.

## 6. Ordre de lecture

1. `/README.md` puis `/CONVENTIONS.md`
2. `tool_usage.md`
3. `evidence/README.md`
4. `rules/FORMAT_REGLE.md`
5. `references/source_weighting.md`
6. `decision_engine/01` → `06`
7. `docs/06_moteur_maintenance.md`
8. `scoring/`, `monte_carlo/`, `simulations/`, `validation/`
9. `research/benchmarks/` (ce que l'open source fait mieux / ce qu'on réutilise)
10. Dossiers de catégories (`greeks/`, `volatility/`, …) selon le module développé

Pour toute transcription PDF, insérer avant l'étape 6 :

1. `docs/07_transcription_pdf_technique_v2.md`
2. `docs/08_plan_implementation_transcription_v2.md`
3. `schemas/README.md`
4. `prompts/pdf_visual_verifier_gemini_v2.md`
5. `validation/pdf_transcription_v2_tests.md`

Le pipeline choisit seul page, crop, DPI, rotation, contexte et besoin de revue visuelle. Il ne
demande une intervention utilisateur que si la source est absente/corrompue, la dépendance
indispensable manque, la clé est invalide, l'API est indisponible sans alternative, ou une ambiguïté
critique persiste après tous les fallbacks.

## 7. Critère d'achèvement de la phase de recherche

Le développement ne commence que lorsque : la bibliothèque est traitée, les conflits majeurs sont
tranchés, les protocoles de validation existent, et chaque module du moteur possède une
spécification documentaire complète.
