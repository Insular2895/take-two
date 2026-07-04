# valuation/ — Valorisation et attentes

## Rôle
Centraliser les méthodes déterminant si le marché sous-estime ou surestime l'entreprise :
attentes implicites, DCF inversé, multiples, scénarios, consensus, surprises, révisions de
bénéfices, création de valeur — et leur traduction en décisions d'options (sous-jacent, horizon).

## Ce qui y sera stocké
- Index des règles `R-VALUATION-NNN` (source pivot : Mauboussin/Rappaport).
- Séquence officielle de lecture des attentes (règles chaînées) et données requises (Module 3).
- Règles de liaison catalyseur → échéance minimale du Call.

## Format attendu
Notes de synthèse + index + séquences de règles chaînées.

## Dépendances
`rules/VALUATION/`, `simulations/` (scénarios haut/bas), `docs/06_moteur_maintenance.md` (triggers → alertes).
