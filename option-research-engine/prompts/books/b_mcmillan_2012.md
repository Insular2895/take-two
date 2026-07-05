# Extraction documentaire — B-MCMILLAN-2012

## Mission

Extraire uniquement des règles opérationnelles explicitement soutenues par le bloc fourni de
*Options as a Strategic Investment*, 5e édition, de Lawrence G. McMillan.

Tu ne résumes pas le chapitre. Tu ne complètes pas le livre avec tes connaissances. Tu ne proposes
aucun trade actuel. Tu ne valides pas la rentabilité d'une règle.

## Cibles

- achat de Calls ;
- choix du strike, de la moneyness et de l'échéance ;
- comparaison Call sec et spread ;
- sections « Follow-Up Action » ;
- sortie, réduction, rolling up, rolling out et protection des gains ;
- erreurs documentées des acheteurs de Calls ;
- exceptions et exemples chiffrés.

Ignore la vente nue d'options, sauf comparaison explicitement utile à une structure d'achat.

## Traçabilité

- Utilise exclusivement les marqueurs `# Page N` présents dans le contenu.
- `## Page` contient le numéro PDF visible dans le marqueur, jamais un numéro inventé.
- Le chapitre doit être identifiable dans le bloc. Sinon, réponds
  `AUCUNE_REGLE_EXPLOITABLE`.
- Ne transforme pas un exemple en règle générale si l'auteur ne généralise pas le mécanisme.
- Recopie les nombres avec leur unité. Au moindre doute OCR, marque la règle `to_review`.
- N'ajoute aucun risque, exception ou justification générique venant de tes connaissances.
- Un comportement d'arbitreur, de courtier ou de chambre de compensation n'est pas une action du
  futur moteur. Conserve-le seulement s'il déclenche une alerte ou une interdiction testable.
- Toute procédure de marché susceptible d'avoir changé depuis l'édition est marquée
  `to_review_current_rule` dans `## Niveau de confiance`.

## Sortie

S'il n'existe aucune règle complète et traçable :

```text
AUCUNE_REGLE_EXPLOITABLE
```

Sinon, produis un ou plusieurs blocs complets. Utilise un identifiant provisoire
`R-OPTIONS-TEMP-NN`.

```markdown
# R-OPTIONS-TEMP-NN — Titre court et actif

## Titre
Une phrase avec un verbe d'action.

## Description
Contexte et portée en 3 à 6 phrases.

## Condition
Condition testable. N'invente aucun seuil.

## Variables nécessaires
Variables, types et unités.

## Action
Action déterministe ou alerte. Aucune recommandation de marché actuelle.

## Justification
Mécanisme décrit par McMillan.

## Risques
Uniquement les limites et conséquences explicitement présentes. Sinon :
`Aucun risque explicite dans ce bloc`.

## Exceptions
Cas d'inapplication explicitement soutenus. Sinon : `Aucune connue dans ce bloc`.

## Exemple
Exemple du bloc, paraphrasé et chiffré. Sinon : `Aucun exemple chiffré dans ce bloc`.

## Auteur
Lawrence G. McMillan

## Livre
B-MCMILLAN-2012 — Options as a Strategic Investment, 5e édition

## Chapitre
Numéro et titre visibles dans le bloc.

## Page
Numéro ou plage issue des marqueurs `# Page N`.

## Niveau de confiance
1 à 5 pour la fidélité documentaire, avec justification. Ce niveau ne valide pas la rentabilité.

## Modules concernés
Uniquement parmi : sélection, strikes, échéances, sizing, gestion_gains, gestion_pertes, vente,
trailing_stop, rolling, simulation, scoring, robustesse, alertes, maintenance.

## Références croisées
`À établir lors de la consolidation`.

## Tags
Mots-clés minuscules.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, prompt pilote B-MCMILLAN-2012 v1
```

## Rejet obligatoire

Réponds `AUCUNE_REGLE_EXPLOITABLE` si la condition, l'action, le chapitre ou la page manque. Une
définition, une anecdote, une table des matières ou une description générale de stratégie n'est
pas une règle exploitable.
