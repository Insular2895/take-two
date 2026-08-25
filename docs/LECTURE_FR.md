# Guide de lecture français — moteur de recherche quantitative TTWO

Date : 2026-08-08  
Statut : `guide_humain`  
Source de vérité technique : fichiers canoniques anglais, YAML/JSON et code du dépôt

## Commencer ici

Ce guide donne un accès entièrement francophone aux résultats des phases 0 à 11. Les versions
françaises expliquent le contenu sans modifier les identifiants, les formules, les chemins de code
ou les statuts utilisés par les validations automatiques.

| Besoin | Document français |
| --- | --- |
| Comprendre le résultat final et ses limites | [Handoff final français](final-quantitative-validation-handoff.fr.md) |
| Voir tous les livres retrouvés et leur état | [Inventaire des livres](research/book_inventory.md) — déjà rédigé en français |
| Comprendre ce qui a été extrait phase par phase | [Synthèse française des recherches 1 à 11](research/recherche-documentaire-phases-1-a-11.fr.md) |
| Voir les 36 sources et leur rôle | [Registre des sources expliqué en français](research/sources.fr.md) |
| Voir les 25 formules, le code et les tests associés | [Formules et traçabilité en français](research/formules-et-tracabilite.fr.md) |
| Comprendre l’enchaînement complet des travaux | [Plan intégral français des phases 0 à 11](plan-quantitatif-phases-0-a-11.fr.md) |
| Lire le détail exact de chaque fichier ajouté/modifié | [Manifest du handoff canonique](final-quantitative-validation-handoff.md#8-exact-repository-file-manifest) |

## Ce qui a réellement été extrait des livres

Les livres n’ont pas été résumés indistinctement. Des passages ciblés ont servi à établir des
contrats précis, avec pages, hypothèses, mesure `P` ou `Q`, unités, implémentation et tests :

- Björk et Andersen–Piterbarg : séparation entre dynamique empirique sous `P` et valorisation
  sans arbitrage sous `Q`, actualisation et conventions de temps ;
- Süli–Mayers : encadrement robuste, erreurs absolue/relative et convergence par raffinement ;
- Gatheral–Jacquier et travaux SSVI/eSSVI : variance totale SVI et contrôles d’arbitrage ;
- Tsay : EWMA, GARCH, diagnostics résiduels et comparaison chronologique ;
- Glasserman : erreur Monte Carlo, intervalles, variables de contrôle et antithétiques ;
- Künsch et Wasserman : bootstrap adapté aux données indépendantes ou dépendantes ;
- McElreath : prédiction postérieure, incertitude de modèle et limites du langage bayésien ;
- Blitzstein–Hwang : conditionnement, indépendance et mises à jour séquentielles ;
- Boyd–Vandenberghe : dominance et frontière de Pareto ;
- Bergomi, Särkkä et Andersen–Piterbarg avancé : conditions minimales avant d’ajouter des modèles
  plus complexes.

Chaque formule retenue est reliée à une source, à un symbole de code et à au moins un test dans
[formules-et-tracabilite.fr.md](research/formules-et-tracabilite.fr.md).

## Ce qui a été ajouté ou modifié

Le travail a notamment ajouté :

- des contrats quantitatifs explicites pour unités, temps et mesures `P/Q` ;
- un solveur de volatilité implicite diagnostiqué et une surface SVI contrôlée ;
- des calibrations EWMA/GARCH et des comparaisons chronologiques ;
- un protocole d’expérience, de purge, d’embargo et de holdout final scellé ;
- une machine d’état chronologique pour les sorties de position ;
- des diagnostics séparant erreur Monte Carlo, incertitude paramétrique et risque de modèle ;
- une allocation entière robuste, une frontière de Pareto et l’option `NO_TRADE` ;
- un graphe de dépendance des événements et des mises à jour séquentielles auditables ;
- un grade de preuve au maillon le plus faible, des rapports statiques et des portes de release ;
- une évaluation documentaire de onze extensions avancées sans intégrer prématurément de modèle.

Le détail technique exact reste dans le diff Git et dans le handoff canonique. Les traductions
françaises sont des vues de lecture : elles ne remplacent ni les registres structurés, ni les
tests, ni les décisions machine.

## Vocabulaire des statuts

| Statut technique | Sens français |
| --- | --- |
| `proposed` | proposé, pas encore suffisamment sourcé |
| `sourced` | source inspectée et provenance enregistrée |
| `implemented` | implémenté, sans implication de validité empirique |
| `tested` | comportement logiciel testé |
| `numerically_validated` | cohérence numérique contrôlée dans le périmètre déclaré |
| `empirically_validated` | validé sur données réelles hors échantillon |
| `holdout_validated` | validé une fois sur un holdout final scellé |
| `paper_validated` | confirmé par une campagne de paper trading gouvernée |

Le dépôt s’arrête actuellement à `READY_RESEARCH_ONLY` et `software_tested_only` pour la chaîne de
décision complète. Il ne contient ni stratégie de trading validée, ni autorisation d’exécution.

