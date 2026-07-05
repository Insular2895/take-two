# Extraction documentaire — B-NATENBERG-1994

## Mission

Extraire uniquement des règles testables explicitement soutenues par le bloc OCR fourni de
*Option Volatility and Pricing* de Sheldon Natenberg.

Tu ne résumes pas. Tu n'utilises aucune connaissance externe. Tu ne corriges pas silencieusement
un symbole ou un nombre OCR incertain. Tu ne proposes aucun trade actuel.

## Cibles

- theoretical edge et volatilité prévue contre volatilité implicite ;
- Greeks selon moneyness et maturité ;
- choix entre options courtes et longues ;
- skew et structure par terme ;
- conditions où un spread domine un Call sec ;
- erreurs opérationnelles documentées.

Ignore les passages historiques sur les pits et les futures sans conséquence directe pour
l'analyse d'options sur actions.

## Traçabilité OCR

- Utilise exclusivement les marqueurs `# Page N`.
- Pour chaque phrase source, remonte jusqu'au marqueur `# Page N` immédiatement précédent.
- `## Page` contient `PDF_PAGE: N` ou `PDF_PAGES: N-M`. N'utilise jamais le numéro imprimé dans le
  pied ou l'en-tête du livre.
- Le chapitre doit être visible ou identifiable dans le bloc.
- Tout nombre, tableau, formule ou symbole ambigu impose `to_review` dans le niveau de confiance.
- N'invente jamais une cellule manquante d'un tableau.
- Une relation qualitative ne devient pas un seuil numérique.
- N'ajoute aucun risque, exception ou mécanisme venant de tes connaissances.
- Un comportement descriptif de trader n'est conservé que s'il devient une alerte, une
  interdiction ou une condition de sélection testable.

## Sortie

Sans règle complète et traçable, réponds exactement :

```text
AUCUNE_REGLE_EXPLOITABLE
```

Sinon, produis des blocs `R-<CAT>-TEMP-NN`, où `<CAT>` vaut `OPTIONS`, `VOL` ou `GREEKS`.

```markdown
# R-<CAT>-TEMP-NN — Titre court et actif

## Titre
Une phrase avec un verbe d'action.

## Description
Contexte et portée en 3 à 6 phrases.

## Condition
Condition testable, sans seuil inventé.

## Variables nécessaires
Variables, types, unités et plage.

## Action
Action d'analyse, de sélection, d'alerte ou d'interdiction.

## Justification
Mécanisme décrit dans le bloc.

## Risques
Uniquement les limites, hypothèses et risques explicitement présents. Sinon :
`Aucun risque explicite dans ce bloc`.

## Exceptions
Cas explicites. Sinon : `Aucune connue dans ce bloc`.

## Exemple
Exemple chiffré lisible. Sinon : `Aucun exemple chiffré fiable dans ce bloc`.

## Auteur
Sheldon Natenberg

## Livre
B-NATENBERG-1994 — Option Volatility and Pricing

## Chapitre
Numéro et titre visibles dans le bloc.

## Page
`PDF_PAGE: N` ou `PDF_PAGES: N-M`, issu des marqueurs immédiatement précédant les passages.

## Preuve source
Une phrase OCR exacte de 8 à 20 mots provenant de la page revendiquée, sans la corriger.

## Niveau de confiance
1 à 5 pour la fidélité documentaire, avec mention explicite de toute incertitude OCR.

## Modules concernés
Uniquement parmi : sélection, strikes, échéances, sizing, gestion_gains, gestion_pertes, vente,
trailing_stop, rolling, simulation, scoring, robustesse, alertes, maintenance.

## Références croisées
`À établir lors de la consolidation`.

## Tags
Mots-clés minuscules.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, prompt pilote B-NATENBERG-1994 v1
```

## Rejet obligatoire

Une table des matières, une définition isolée, une formule illisible ou un passage sans action
testable produit `AUCUNE_REGLE_EXPLOITABLE`.

Avant de répondre, vérifie chaque `## Page` en retrouvant le marqueur immédiatement précédent la
phrase utilisée. Une règle dont la page n'est pas certaine doit être rejetée.

La preuve source doit apparaître textuellement dans la page PDF revendiquée. Sinon, rejette la
règle.
