# R-VALUATION-001 — Expliciter les attentes intégrées au prix

## Titre
Déduire le scénario que le prix du sous-jacent suppose déjà.

## Description
Un bon actif n'est pas nécessairement un bon achat si son prix anticipe déjà d'excellents résultats.
Mauboussin et Rappaport proposent de partir du prix pour estimer le niveau et la durée des flux
attendus. La règle produit un scénario de référence, pas une recommandation.

## Condition
`prix_du_sous_jacent_disponible = vrai ET modèle_de_valorisation_documenté = vrai`

## Variables nécessaires
`prix`, `flux de trésorerie`, `coût du capital`, `croissance`, `marge`, `durée de l'avantage
concurrentiel`, `dette nette`.

## Action
Calculer ou consigner les attentes implicites compatibles avec le prix, puis comparer le scénario de
recherche à ce scénario de référence.

## Justification
Le rendement excédentaire dépend d'une évolution que le prix actuel ne reflète pas déjà.

## Risques
Le résultat dépend fortement du modèle, du taux d'actualisation et des hypothèses terminales.

## Exceptions
Si les données ne permettent pas une valorisation raisonnable, classer l'analyse `to_review`.

## Exemple
Le livre indique que la plupart des sociétés nécessitent plus de dix années de flux créateurs de
valeur pour justifier leur prix.

## Auteur
Michael J. Mauboussin et Alfred Rappaport.

## Livre
`B-MAUBOUSSIN-RAPPAPORT-2001` — *Expectations Investing*.

## Chapitre
1 — The Expectations Investing Process.

## Page
PDF p. 27, page imprimée 10.

## Niveau de confiance
4 — méthode de valorisation testable, avec hypothèses explicitables.

## Modules concernés
sélection, simulation, scoring, robustesse.

## Références croisées
`→ R-DECISION-001`.

## Tags
attentes implicites, reverse dcf, sous-jacent, scénario.

## Revue 2026
Statut 2026 : `valide_comme_principe`, `non_active_sans_donnees_fondamentales_actuelles`.

Le principe reste actuel : partir du prix pour remonter aux attentes implicites est utile. Pour une
thèse 2026, il faut utiliser filings récents, guidance, consensus si disponible, dette, dilution,
SBC, buybacks, taxes, WACC, comparables, calendrier catalyseur et scénarios contradictoires. Les
discussions anciennes sur stock-options/buybacks ne suffisent pas telles quelles.

Contrôle obligatoire avant scoring : modèle reverse DCF horodaté, hypothèses explicites, sources
fondamentales actuelles, probabilités justifiées, invalidation, et lien direct entre thèse
fondamentale et structure option.

Sources 2026 : SEC EDGAR/company filings ; U.S. Treasury curve ; SEC SAB Topic 14/SAB 120/ASC 718 ;
IRS Section 4501 ; données fondamentales actuelles.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, preuve retrouvée sur la page PDF.
- 2026-07-05 — NORMALISÉE — contexte relu ; aucune recommandation automatique.
