# validation/ — Protocoles de validation

## Rôle
Définir COMMENT une règle ou une stratégie passe du statut « extraite » au statut « validée » :
out-of-sample, Walk-Forward (Pardo), corrections de data mining (Aronson), stress tests.

## Ce qui y sera stocké
- Protocoles normés (checklists exécutables) : walk-forward, OOS, tests multiples, stress.
- Comptes-rendus d'exécution : règle testée, données, protocole, résultat, décision de statut.
- Critères officiels de rejet d'une stratégie (signes d'overfitting).

## Format attendu
Protocole : Objectif / Prérequis / Étapes numérotées / Critères de succès / Critères de rejet.
Compte-rendu : Règle(s) / Données / Protocole / Résultats chiffrés / Décision / Date.

## Conventions
Un résultat de validation est immuable : une re-validation crée un nouveau compte-rendu.

## Dépendances
`backtesting/`, `rules/`, `docs/04_ponderation_des_regles.md` (facteur validation du poids).
