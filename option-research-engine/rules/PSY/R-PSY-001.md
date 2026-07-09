# R-PSY-001 — Tracer toute dérogation au plan

## Titre
Comparer la transaction exécutée au scénario préparé.

## Description
Douglas oppose le processus structuré aux trades improvisés et insiste sur l'acceptation préalable
des issues défavorables. Cette source soutient un garde-fou de processus, pas un signal de marché.
Une dérogation doit rester visible et attribuable.

## Condition
`ordre_envisagé = vrai`

## Variables nécessaires
`identifiant du plan`, `motif d'entrée`, `perte maximale prévue`, `scénarios défavorables`,
`dérogation`, `justification`, `horodatage`.

## Action
Alerter si l'ordre ne correspond pas au plan ; exiger une justification journalisée de la
dérogation avant transmission. Le blocage automatique nécessite une décision projet séparée.

## Justification
Le suivi entre intention et exécution rend les écarts auditables et limite le trading aléatoire.

## Risques
La journalisation peut devenir une formalité et ne garantit ni discipline ni rentabilité.

## Exceptions
Une procédure d'urgence validée peut autoriser une dérogation avec justification a posteriori.

## Exemple
Douglas décrit des traders qui préparaient leurs opérations puis exécutaient à la place des idées
non planifiées venues de tiers.

## Auteur
Mark Douglas.

## Livre
`B-DOUGLAS-2000` — *Trading in the Zone*.

## Chapitre
2 — The Lure (and the Dangers) of Trading.

## Page
PDF p. 34 et 40.

## Niveau de confiance
3 — mécanisme qualitatif crédible, effet à mesurer.

## Modules concernés
robustesse, alertes, maintenance.

## Références croisées
`≈ R-DECISION-001`.

## Tags
plan, dérogation, journal, risque accepté.

## Revue 2026
Statut 2026 : `valide_comme_principe`, `non_active_sans_journal_et_controles`.

Le principe reste actuel : distinguer qualité de décision, qualité d'exécution, résultat et chance
est indispensable. En 2026, cela doit devenir un garde-fou logiciel : plan pré-trade, risque accepté,
actions autorisées, log des écarts, justification des rolls/hedges/closures et post-mortem.

Contrôle obligatoire avant scoring : aucun ordre préparé sans `plan_id`, `accepted_risk`,
`invalidation`, `review_status`, journal d'exécution et règle d'escalade humaine si la taille, le
risque non borné ou la structure changent.

Sources 2026 : journal interne, logs broker/paper trading, checklist humaine, règles projet.

## Historique
- 2026-07-05 — EXTRAITE — passages relus dans la source.
- 2026-07-05 — NORMALISÉE — action limitée à l'alerte et à la traçabilité.
