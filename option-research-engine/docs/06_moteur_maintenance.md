# Moteur de maintenance — Spécification documentaire

> Aucun code. Ce document décrit le comportement attendu du moteur qui gère une position **après achat**.

## 0. Principe

Après achat, le moteur ne réanalyse pas toute la stratégie : il applique **uniquement les règles
optimisées** retenues au moment de la décision (et enregistrées dans le journal). Aucun paramètre
n'est codé en dur : seuils de stops, niveaux de récupération, fréquences de surveillance
proviennent tous de l'optimisation initiale et des règles `ACTIVE` de la base.

## 1. Surveillance continue

Variables surveillées : prix du sous-jacent, valeur du Call, Delta, Gamma, Theta, Vega,
volatilité implicite, temps restant, événements (earnings, guidance, SEC, news majeures).
La fréquence de surveillance de chaque variable est elle-même une règle extraite/validée.

## 2. Trailing stop

- Le moteur documente ici : définitions (trailing sur prix du sous-jacent vs sur valeur de l'option),
  méthodes d'ancrage (plus haut atteint, ATR, volatilité), et conditions d'activation.
- Le pourcentage/la méthode ne sont jamais fixes : ils sont sélectionnés par l'optimiseur parmi les
  variantes documentées dans `rules/TRADSYS/` et validées dans `validation/`.

## 3. Stop loss

- Familles à documenter : stop sur perte de prime (%), stop sur invalidation de thèse,
  stop temporel (Theta), stop sur Greeks (ex. Delta sous un seuil), stop sur événement.
- Chaque famille référence ses règles sources et ses conditions d'exception.

## 4. Récupération du capital

- Définition : vente partielle ramenant le risque résiduel à zéro (ou à un niveau cible).
- À documenter depuis la littérature : niveaux déclencheurs, fraction vendue, interaction avec
  le sizing initial (`money_management/`), effets sur l'espérance résiduelle.

## 5. Sortie partielle / totale

- Critères candidats : objectif de score atteint, dégradation de l'espérance ajustée du risque,
  IV Crush imminent, liquidité dégradée, meilleure opportunité détectée (coût d'opportunité).

## 6. Rolling (revue hebdomadaire — Module 9)

Chaque semaine, le moteur compare : position actuelle ↔ nouvelle échéance candidate, sur
coût, Theta, Delta, espérance, score. Recommandation ∈ {conserver, rouler, clôturer}, toujours justifiée.
Les critères de rolling proviennent de `rules/OPTIONS/` et `rules/GREEKS/`.

## 7. Alertes (Module 10)

Déclencheurs : variation forte des Greeks, variation forte de l'IV, earnings proche, événement
majeur détecté, règle de gestion atteinte, opportunité supérieure détectée. Chaque alerte cite la
règle déclencheuse et propose l'action associée.

## 8. Journal de décision (Module 11)

Modèle : `templates/journal_decision.md`.
- **Avant achat** : stratégie choisie, score, hypothèses, règles utilisées, alternatives rejetées.
- **Pendant** : décisions, modifications, alertes, contexte de marché.
- **Après clôture** : résultat réel vs simulation, règles validées, règles invalidées.

Rétroaction : les validations/invalidations remontent dans la pondération des règles
(`docs/04_ponderation_des_regles.md`) — c'est ainsi que le moteur s'améliore opération après opération.
