# examples/ — Cas pratiques

## Rôle
Stocker des cas complets, chiffrés et traçables illustrant le fonctionnement attendu du moteur :
de la chaîne d'options brute à la proposition justifiée, puis à la maintenance simulée.

## Ce qui y sera stocké
- Cas d'école par module : sélection, scoring, conflit de règles arbitré, rolling, garde-fou déclenché.
- Exemples extraits des livres (repris des champs Exemple des règles) recontextualisés.
- Plus tard : journaux de décision anonymisés servant de tests d'acceptation pour Codex.

## Format attendu
Un fichier par cas : Contexte / Données / Règles applicables (IDs) / Déroulé / Résultat attendu /
Justification. Tout chiffre est vérifiable.

## Conventions
Un exemple n'invente jamais une règle : il ne cite que des `R-XXX-NNN` existants.

## Dépendances
`rules/`, `decision_engine/`, `templates/journal_decision.md`.
