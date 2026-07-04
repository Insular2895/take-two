# Conflits entre règles et vote multi-livres

## 1. Cas nominal — vote pondéré

Pour une décision donnée, toutes les règles `ACTIVE` dont la condition est vraie « votent » pour
leur action. Le poids de chaque vote = poids de la règle (`docs/04_ponderation_des_regles.md`).
Plusieurs livres peuvent ainsi voter pour une même décision : la convergence augmente
mécaniquement le poids total de l'action.

## 2. Conflit en cours d'exécution

Si deux actions incompatibles reçoivent des votes :
1. Vérifier la spécificité des conditions — la règle la plus spécifique au contexte l'emporte
   sur la règle générale (principe documenté, pas heuristique cachée).
2. Sinon, comparer les poids agrégés ; un écart minimal (documenté dans `scoring/`) est requis
   pour trancher.
3. Sinon, la décision est simulée : les deux branches passent en Monte Carlo et la meilleure
   espérance ajustée du risque l'emporte.
4. Le conflit, son arbitrage et son résultat sont journalisés et remontent dans
   `knowledge_base/registre_conflits.md`.

## 3. Conflits de fond

Les contradictions structurelles entre auteurs sont traitées en amont, en phase de recherche
(`docs/03_contradictions_et_doublons.md`). Le moteur ne doit jamais découvrir en production un
conflit qui était détectable dans la base.
