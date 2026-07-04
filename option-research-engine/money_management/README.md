# money_management/ — Gestion du capital

## Rôle
Centraliser sizing et gestion du capital : Kelly (et fractions), Fixed Fraction, Risk Budget,
Conviction Sizing, pyramiding, scaling in/out, récupération du capital, prise de bénéfices,
drawdown maximum, allocation optimale entre structures.

## Ce qui y sera stocké
- Index des règles `R-MM-NNN` (sources : Vince, Tharp, Sinclair).
- Contraintes officielles de sizing que l'optimiseur doit respecter (plafonds sourcés).
- Interaction sizing ↔ maintenance (la récupération du capital dépend du sizing initial).

## Format attendu
Notes de synthèse + index. Toute formule de sizing exprime sa sortie en fraction du budget.

## Dépendances
`rules/MM/`, `risk/`, `decision_engine/01` (répartition du budget comme dimension d'optimisation).
