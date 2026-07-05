# Extraction documentaire — B-PASSARELLI-2012

## Mission

Extraire uniquement des règles testables explicitement soutenues par le bloc OCR fourni de
*Trading Option Greeks* de Dan Passarelli.

Tu ne résumes pas. Tu n'ajoutes aucune pratique de marché externe. Tu ne proposes aucun trade
actuel. Tu ne transformes pas une illustration pédagogique en seuil universel.

## Cibles

- Delta et moneyness selon l'objectif ;
- interaction Gamma/Theta selon le temps restant ;
- Vega et événements ;
- critères de surveillance, vente et rolling ;
- variables de bascule explicites ;
- exemples numériques complets.

## Traçabilité OCR

- Utilise exclusivement les marqueurs `# Page N`.
- Pour chaque phrase source, remonte jusqu'au marqueur `# Page N` immédiatement précédent.
- `## Page` contient `PDF_PAGE: N` ou `PDF_PAGES: N-M`. N'utilise jamais la pagination imprimée.
- Le chapitre doit être identifiable dans le bloc.
- Conserve les unités et conventions de signe.
- Tout symbole, décimale, formule ou tableau ambigu doit être marqué `to_review`.
- Ne crée pas de croisement avec IV Rank si le bloc ne fournit pas cette variable.
- N'ajoute aucun risque, exception ou mécanisme venant de tes connaissances.
- Un comportement descriptif n'est conservé que s'il devient une alerte, une interdiction ou une
  condition de sélection testable.

## Sortie

Sans règle complète et traçable, réponds exactement :

```text
AUCUNE_REGLE_EXPLOITABLE
```

Sinon, produis des blocs `R-GREEKS-TEMP-NN` ou `R-OPTIONS-TEMP-NN`.

```markdown
# R-<CAT>-TEMP-NN — Titre court et actif

## Titre
Une phrase avec un verbe d'action.

## Description
Contexte et portée en 3 à 6 phrases.

## Condition
Condition testable, avec variable de bascule si elle existe.

## Variables nécessaires
Variables, types, unités, plages et conventions de signe.

## Action
Action d'analyse, de sélection, de surveillance, de vente, de rolling ou d'alerte.

## Justification
Mécanisme décrit par Passarelli.

## Risques
Uniquement les limites et risques explicitement présents. Sinon :
`Aucun risque explicite dans ce bloc`.

## Exceptions
Cas explicites. Sinon : `Aucune connue dans ce bloc`.

## Exemple
Exemple numérique lisible. Sinon : `Aucun exemple chiffré fiable dans ce bloc`.

## Auteur
Dan Passarelli

## Livre
B-PASSARELLI-2012 — Trading Option Greeks

## Chapitre
Numéro et titre visibles dans le bloc.

## Page
`PDF_PAGE: N` ou `PDF_PAGES: N-M`, issu des marqueurs immédiatement précédant les passages.

## Preuve source
Une phrase OCR exacte de 8 à 20 mots provenant de la page revendiquée, sans la corriger.

## Niveau de confiance
1 à 5 pour la fidélité documentaire, avec mention de toute incertitude OCR.

## Modules concernés
Uniquement parmi : sélection, strikes, échéances, sizing, gestion_gains, gestion_pertes, vente,
trailing_stop, rolling, simulation, scoring, robustesse, alertes, maintenance.

## Références croisées
`À établir lors de la consolidation`.

## Tags
Mots-clés minuscules.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, prompt pilote B-PASSARELLI-2012 v1
```

## Rejet obligatoire

Une définition isolée d'un Greek, une table des matières, un symbole illisible ou un passage sans
condition/action exploitable produit `AUCUNE_REGLE_EXPLOITABLE`.

La preuve source doit apparaître textuellement dans la page PDF revendiquée. Sinon, rejette la
règle.
