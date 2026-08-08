# Plan intégral français — validation quantitative TTWO, phases 0 à 11

Date : 2026-08-08  
Plan canonique détaillé :
[`superpowers/plans/2026-08-08-ttwo-quantitative-validation-v10.md`](superpowers/plans/2026-08-08-ttwo-quantitative-validation-v10.md)  
État : toutes les phases exécutées ; release de recherche uniquement

## Objectif

Transformer le dépôt en moteur de recherche quantitative auditable et fermé par défaut. Le but
n’est pas de fabriquer une recommandation de trading, mais de garantir que chaque nombre possède
des conventions, une provenance, une incertitude, un niveau de preuve et une limite explicites.

## Contraintes permanentes

- aucun ordre, aucune transmission et aucune automatisation de courtage ;
- `cash/NO_TRADE` toujours possible ;
- séparation obligatoire entre mesure empirique `P` et valorisation `Q` ;
- données, événements et variables disponibles avant la décision ;
- fixtures synthétiques clairement séparées des preuves réelles ;
- niveau final égal au maillon de preuve le plus faible ;
- aucune extension complexe sans gain matériel mesuré.

## Phase 0 — audit du corpus et baseline

### Entrées

Bibliothèque PDF locale, dépôt existant, anciens résultats V7–V9 et outils d’extraction.

### Travaux

1. Résoudre prudemment le chemin `BOOK` vers le candidat `/Users/insular/Desktop/book 📙`.
2. Inventorier récursivement les documents, pages, SHA-256, doublons et avertissements PDF.
3. Regrouper correctement les fragments d’une même œuvre.
4. Établir les registres initiaux de sources, formules et errata.
5. Capturer la baseline logicielle sans ouvrir de holdout.

### Sorties et porte

Inventaire Markdown/JSON, 138 chemins, 133 payloads PDF uniques, aucun PDF modifié. La phase se
termine uniquement si le corpus est traçable et les métadonnées inconnues restent inconnues.

## Phase 1 — fondations quantitatives

### Travaux

Créer des types pour mesures, unités, taux, temps, observations et transitions. Centraliser les
conventions. Ajouter erreurs absolue/relative, tolérances et convergence par grille. Comparer
Black–Scholes européen à QuantLib et tester la parité call-put.

### Porte de sortie

Une incohérence `P/Q`, une convention de temps ambiguë ou un échec numérique doit être rejeté ou
rapporté explicitement ; aucun succès silencieux.

## Phase 2 — IV et SVI

### Travaux

Remplacer les scalaires d’IV opaques par un solveur diagnostiqué. Ajuster SVI par procédure
déterministe multi-départs. Contrôler arbitrage papillon et calendrier. Supprimer toute volatilité
par défaut silencieuse. Créer une porte eSSVI.

### Porte de sortie

Récupération synthétique des paramètres, échecs d’encadrement structurés et violations d’arbitrage
détectées. Aucune promotion empirique sans chaîne TTWO réelle point-in-time.

## Phase 3 — calibration et séries temporelles

### Travaux

Implémenter EWMA et GARCH(1,1) reproductibles, diagnostics résiduels, persistance et comparateur de
prévisions rolling/EWMA/GARCH sur suffixe chronologique intact. Évaluer l’éligibilité Heston sans
le calibrer prématurément.

### Porte de sortie

Pas de look-ahead, résultats synthétiques reproductibles, avertissements de persistance visibles et
Heston bloqué si surfaces réelles insuffisantes.

## Phase 4 — protocole d’expérience et holdout

### Travaux

Lier code/config/dataset/split/essais/seed dans un manifeste hashé. Séparer entraînement,
validation chronologique et holdout final. Ajouter purge, embargo, journal hash-chaîné, PBO
corrigé, DSR explicite et placebo valide.

### Porte de sortie

Le holdout ne révèle aucun identifiant avant autorisation. Une fois évalué, tout tuning est
interdit. V7–V9 restent contaminés. Aucun manifeste fictif ne peut être créé depuis une fixture.

## Phase 5 — simulation de trajectoires et sorties

### Travaux

Formaliser les sorties par machine d’état chronologique. Publier les événements terminaux et
coûts. Ajouter Wilson, ESS, variables de contrôle, antithétiques, bootstrap par blocs et
comparaison de discrétisation. Garder Longstaff–Schwartz derrière une porte matérielle.

### Porte de sortie

Aucune lecture du futur, aucune transition après terminaison, comptes de réplications corrects et
incertitude explicite même lorsque zéro événement rare est observé.

## Phase 6 — incertitude de croyance et de modèle

### Travaux

Renommer sémantiquement le pseudo-Bayes comme croyance heuristique configurée, sans casser la
compatibilité. Identifier les jeux de paramètres. Décomposer variance interne, variance entre
modèles et erreur Monte Carlo. Ajouter Brier, log-loss, ECE et bins avec intervalles.

### Porte de sortie

Les poids diagnostiques ne peuvent être marqués OOS sans lineage. Aucune vraisemblance ou
calibration statistique n’est inventée.

## Phase 7 — allocation robuste et Pareto

### Travaux

Versionner l’objectif, les pénalités et la sémantique des poids. Énumérer toutes les allocations
entières réalisables dans les caps. Calculer la dominance directe, la frontière complète et le
classement scalaire. Conserver l’allocation zéro.

### Porte de sortie

Les contraintes dures ne peuvent être compensées par un score. La frontière est exacte dans
l’univers énuméré et `NO_TRADE` reste disponible.

## Phase 8 — événements et décision séquentielle

### Travaux

Créer un graphe de preuves acyclique avec disponibilité, relation et décote. Neutraliser doublons
et dérivations, traiter les facteurs communs, distinguer origine de probabilité et mesure `P/Q`,
propager des boîtes de croyance et calculer les seuils de bascule.

### Porte de sortie

Les événements futurs, graphes cycliques et origines de probabilité incohérentes sont rejetés.
L’ordre est normalisé chronologiquement. Toute sortie reste consultative et non exécutable.

## Phase 9 — preuve et reporting

### Travaux

Construire un sidecar final contenant données, modèle, validation, simulation, exécution, risques,
formules et décision. Calculer un grade monotone au maillon faible. Produire Markdown et HTML
statiques sans réseau. Valider automatiquement la traçabilité des registres.

### Porte de sortie

Aucune probabilité sans intervalle/diagnostic, aucune validation empirique sans hash de dataset,
aucune validation holdout sans journal scellé et aucune validation paper sans manifeste.

## Phase 10 — audit de release

### Travaux

Rejouer toutes les validations disponibles, inspecter manifestes, données, fixtures, holdouts,
registres et limites. Comparer descriptivement la suite à la baseline. Générer une décision de
release déterministe et vérifiable octet par octet.

### Résultat

- logiciel de recherche : `READY_RESEARCH_ONLY` ;
- promotion financière : `BLOCKED_MISSING_REAL_EVIDENCE` ;
- affirmation maximale de chaîne : `software_tested_only` ;
- exécution : interdite.

## Phase 11 — extensions avancées

### Travaux

Examiner Bergomi, rough Bergomi, filtrage bayésien, taux stochastiques, eSSVI, régimes appris,
Bayes hiérarchique événementiel, Longstaff–Schwartz, AAD/Greeks supérieurs, Sobol/QMC/distribué et
surfaces neuronales. Pour chaque extension, enregistrer données nécessaires, identifiabilité,
baseline, métrique OOS, matérialité, coût et risque.

### Résultat

Huit extensions différées, trois rejetées uniquement pour le périmètre actuel, aucune intégrée.
Chaque classement est réversible par une porte mesurable et exige ensuite une phase
d’implémentation séparée.

## Validation finale exécutée

- 194 tests réussis ;
- Ruff réussi ;
- mypy strict réussi sur 144 fichiers source ;
- dépendances cohérentes ;
- six schémas vérifiés ;
- artefacts offline vérifiés comme fixtures seulement ;
- 25 formules et 36 sources vérifiées ;
- audits des phases 10 et 11 déterministes ;
- 138 fichiers Python inspectés par la porte de sécurité ;
- zéro import interdit, zéro `transmit=True`, exécution interdite partout.

## Suite autorisée par les preuves

1. acquérir un jeu TTWO point-in-time licencié et aligné ;
2. enregistrer provenance, disponibilité et hash ;
3. créer un manifeste actif préenregistré ;
4. calibrer et comparer des baselines simples chronologiquement ;
5. ouvrir une fois un holdout final scellé ;
6. conduire un paper run avec fills, rejets, spreads, commissions et slippage ;
7. réexaminer ensuite seulement les extensions dont la porte matérielle devient vraie.

