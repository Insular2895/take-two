# research/ — Travaux de recherche

## Rôle
Espace des travaux en cours : notes d'étude, analyses comparatives, questions ouvertes, et surtout
`benchmarks/` — l'étude rigoureuse des repositories open source de finance quantitative.

## Principe
Les repositories open source ne remplacent JAMAIS la littérature scientifique. Ils servent
uniquement à : accélérer le développement, identifier les bonnes architectures, réutiliser des
algorithmes éprouvés, éviter de réinventer des composants standards, comparer notre implémentation
à l'état de l'art. Leur contenu est étudié avec le même niveau de rigueur que les livres.

## Contenu
- `benchmarks/` — un fichier par repository étudié (voir son README).
- Fiches d'étude complètes de repos : utiliser `templates/fiche_repository.md`.

## Format attendu
Markdown. Toute affirmation sur un repo doit être vérifiable (lien vers le fichier/module concerné).

## Classification des connaissances issues de la fusion (Dixième mission)
Chaque information intégrée à la base est classée :
`THÉORIQUE` (livre) · `MATHÉMATIQUE` (ex. modèle Heston) · `IMPLÉMENTATION` (ex. GS Quant) ·
`ARCHITECTURE` (ex. Qlib) · `ALGORITHMIQUE` (ex. Monte Carlo optimisé).

## Framework propriétaire (Onzième mission)
L'objectif final n'est pas de réutiliser ces repos mais de construire un framework propriétaire.
Chaque composant candidat répond à UNE question : « Apporte-t-il un avantage objectif à notre
moteur de décision ? » Oui → on documente pourquoi. Non → on documente pourquoi il est rejeté.
Aucune intégration par popularité ; toute intégration est justifiée, documentée et si possible
validée par simulation/benchmark.
