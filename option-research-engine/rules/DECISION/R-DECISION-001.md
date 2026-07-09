# R-DECISION-001 — Exiger une thèse falsifiable sur le sous-jacent

## Titre
Documenter scénario, catalyseur, risques et preuve contradictoire.

## Description
Lynch demande une explication courte de ce qui doit arriver et des obstacles. Mauboussin et
Rappaport recommandent de rechercher les éléments qui contredisent la thèse. Klarman demande une
valorisation indépendante plutôt qu'une confiance exclusive dans le jugement d'un tiers.

## Condition
`transaction_envisagée = vrai`

## Variables nécessaires
`thèse`, `catalyseur`, `horizon`, `attentes implicites`, `risques`, `condition d'invalidation`,
`sources contradictoires`, `valorisation indépendante`.

## Action
Classer `to_review` toute transaction sans thèse concise, condition d'invalidation, analyse
contradictoire et valorisation indépendante documentées.

## Justification
Une thèse explicite et falsifiable réduit le risque de confondre récit, consensus et analyse
propriétaire.

## Risques
Une checklist formellement remplie peut rester biaisée ou reposer sur de mauvaises données.

## Exceptions
Les stratégies purement microstructurelles nécessitent un dossier adapté, mais leurs hypothèses
doivent également être falsifiables.

## Exemple
Le test de Lynch demande d'expliquer en deux minutes l'intérêt, ce qui doit réussir et les pièges.

## Auteur
Peter Lynch ; Michael J. Mauboussin et Alfred Rappaport ; Seth A. Klarman.

## Livre
`B-LYNCH-2000` — *One Up On Wall Street* ; `B-MAUBOUSSIN-RAPPAPORT-2001` —
*Expectations Investing* ; `B-KLARMAN-1991` — *Margin of Safety*.

## Chapitre
Lynch, chapitre 11 ; Mauboussin et Rappaport, chapitre 5 ; Klarman, chapitre 10.

## Page
PDF p. 165 ; PDF p. 119 ; PDF p. 173.

## Niveau de confiance
4 — convergence de trois auteurs ; efficacité opérationnelle à mesurer.

## Modules concernés
sélection, scoring, robustesse, maintenance.

## Références croisées
`→ R-VALUATION-001`, `≈ R-PSY-001`.

## Tags
thèse, falsification, biais de confirmation, valorisation.

## Revue 2026
Statut 2026 : `valide_comme_principe`, `non_active_sans_these_validee`.

Le principe reste actuel : aucune structure option ne doit être choisie sans thèse falsifiable,
horizon, catalyseur, niveau d'invalidation et comparaison avec les alternatives. Pour TTWO/GTA VI,
la règle impose de comparer action, option simple, vertical, calendar ou absence de trade selon la
distribution prix/temps, IV, liquidité, coûts et timing du catalyseur.

Contrôle obligatoire avant scoring : fiche thèse `draft_to_validate`, sources actuelles, scénario
central/haussier/baissier, conditions de sortie, contradiction active, et décision humaine avant
toute promotion en `candidate_trade`.

Sources 2026 : filings SEC récents, calendrier catalyseur/earnings, données marché live, notes
internes validées.

## Historique
- 2026-07-05 — DÉDUPLIQUÉE — convergence de trois candidates sourcées.
- 2026-07-05 — NORMALISÉE — contextes relus manuellement.
