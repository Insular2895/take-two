# R-GREEKS-004 — Normaliser les conventions de signe

## Titre
Conserver la valeur brute et normaliser chaque Greek avant agrégation.

## Description
Les sources et fournisseurs peuvent afficher une exposition signée ou seulement une magnitude. Les
figures 6-24 à 6-26 de Natenberg utilisent elles-mêmes des présentations différentes. Une somme de
Greeks n'est fiable qu'après identification de la convention, de l'unité et du sens de position.

## Condition
`greek_reçu = vrai`

## Variables nécessaires
`valeur brute`, `Greek`, `type call/put`, `sens long/short`, `quantité`, `multiplicateur`,
`convention de signe`, `unité`, `horizon du theta`, `source`.

## Action
Stocker la valeur brute et ses métadonnées, convertir vers la convention interne, puis vérifier les
signes économiques avant toute agrégation.

## Justification
Pour une position longue, call et put ont gamma et vega positifs et theta négatif ; leurs deltas ont
des signes opposés. Les positions courtes inversent ces signes.

## Risques
Une erreur de convention peut inverser le risque, particulièrement pour delta et theta.

## Exceptions
Aucune normalisation ne doit être effectuée si la convention ou l'unité du fournisseur est inconnue ;
la donnée devient `to_review`.

## Exemple
Un delta de put affiché comme magnitude `37` doit être distingué d'une exposition signée `-37`
avant multiplication par une quantité.

## Auteur
Sheldon Natenberg.

## Livre
`B-NATENBERG-1994` — *Option Volatility and Pricing*.

## Chapitre
6 — Option Values and Changing Market Conditions.

## Page
Pages imprimées 121–125, particulièrement figure 6-26 p. 124.

## Niveau de confiance
4 — conventions explicites et testables ; adaptation au fournisseur IBKR à vérifier.

## Modules concernés
simulation, scoring, robustesse, maintenance.

## Références croisées
`→ R-GREEKS-001`, `≈ C-009`.

## Tags
greeks, signes, unités, normalisation, données.

## Revue 2026
Statut 2026 : `valide_comme_principe`, `non_active_si_convention_inconnue`.

Le principe reste actuel : comparer des Greeks sans convention commune est dangereux. En 2026, les
fournisseurs peuvent différer sur les unités de vega, theta, rho, le signe des positions short, le
modèle, la devise, le multiplicateur et l'horodatage. Le moteur doit conserver la valeur brute,
la convention source et la valeur normalisée.

Contrôle obligatoire avant scoring : aucune somme ou comparaison de Greeks si `source_convention`,
`unit`, `currency`, `multiplier`, `model`, `timestamp` ou `position_sign` manque.

Sources 2026 : documentation du fournisseur de Greeks ; OCC contract specs ; IBKR contract details.

## Historique
- 2026-07-06 — EXTRAITE — incohérence de présentation identifiée dans les figures 6-24 et 6-25.
- 2026-07-06 — NORMALISÉE — convention économique confirmée par les figures 6-26 à 6-28.
