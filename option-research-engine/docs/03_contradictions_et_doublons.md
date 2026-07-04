# Contradictions et doublons

## 1. Détection des doublons

Deux règles sont candidates au doublon si elles partagent : même catégorie + mêmes variables
nécessaires + actions équivalentes. Procédure :

1. Comparaison des conditions (équivalence logique, pas équivalence textuelle).
2. Si équivalentes → **fusion** : une seule règle consolidée, qui liste **toutes** les sources
   (chaque auteur/livre/page est conservé en référence croisée).
3. La fusion **augmente** le niveau de confiance (convergence multi-auteurs, cf. pondération).
4. Les règles d'origine restent dans `rules/` avec statut `FUSIONNÉE → R-XXX-NNN`.

## 2. Détection des contradictions

Deux règles sont contradictoires si, pour une même condition, elles recommandent des actions
incompatibles (ex. « vendre avant earnings » vs « conserver avant earnings »).

Procédure d'arbitrage (dans cet ordre) :

1. **Contexte** — vérifier si les conditions sont réellement identiques (souvent la contradiction
   disparaît quand on précise le régime de volatilité, l'horizon, ou le type d'option).
2. **Confiance** — comparer les niveaux de confiance et le poids des auteurs.
3. **Simulation** — si la contradiction persiste, elle est tranchée par un protocole dans
   `validation/` (Monte Carlo / backtest). Le résultat est documenté.
4. **Conservation** — la règle « perdante » n'est pas supprimée : elle passe en statut `REJETÉE`
   avec la justification et le lien vers la simulation. Une contradiction non tranchée est
   marquée `CONFLIT-OUVERT` et les deux règles sont inutilisables par le moteur jusqu'à arbitrage.

## 3. Registre

`knowledge_base/registre_conflits.md` liste tous les conflits (ouverts et tranchés), avec dates,
règles concernées et méthode d'arbitrage.
