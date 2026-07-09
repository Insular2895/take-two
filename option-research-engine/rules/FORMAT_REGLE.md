# Format officiel d'une règle

Toute règle du repository DOIT respecter exactement cette structure. Tous les champs sont
obligatoires (écrire « Aucun(e) connue » plutôt que laisser vide).

```markdown
# R-<CAT>-<NNN> — <Titre court et actif>

## Titre
Formulation en une phrase, verbe d'action.

## Statut
Un des statuts de cycle de vie suivants : `DRAFT`, `EXTRACTED`, `VALIDATED`, `CONTRADICTED`,
`DEPRECATED`.

Une règle `VALIDATED` peut rester non active si les données live, la marge, l'exécution ou la
validation humaine manquent. Le statut de cycle de vie ne remplace pas les blocages opérationnels.

## Description
Ce que la règle fait et dans quel contexte elle s'applique. 3–6 phrases maximum.

## Condition
Condition testable par une machine. Utiliser les variables ci-dessous.
Ex. : `IV_Rank > 80 ET jours_avant_earnings <= 5`

## Variables nécessaires
Liste des variables avec type et unité.
Ex. : `IV_Rank (0–100)`, `jours_avant_earnings (jours)`, `Delta (0–1)`

## Action
Action exécutable par le moteur (acheter, vendre X %, rouler vers échéance E, alerter, interdire…).

## Justification
Pourquoi cette règle fonctionne, selon l'auteur. Mécanisme, pas opinion.

## Risques
Ce qui peut mal se passer si la règle est appliquée.

## Exceptions
Cas où la règle ne s'applique pas ou s'inverse.

## Exemple
Exemple chiffré, idéalement repris du livre.

## Auteur
Nom de l'auteur.

## Livre
Identifiant `B-<AUTEUR>-<ANNEE>` + titre.

## Chapitre
Numéro et titre du chapitre.

## Page
Page(s) exacte(s).

## Niveau de confiance
1–5, selon l'échelle de `CONVENTIONS.md`, avec une ligne de justification.

## Modules concernés
Parmi : sélection, strikes, échéances, sizing, gestion_gains, gestion_pertes, vente,
trailing_stop, rolling, simulation, scoring, robustesse, alertes, maintenance.

## Références croisées
Règles liées : convergences (`≈ R-XXX-NNN`), contradictions (`≠ R-XXX-NNN`), dépendances (`→`).

## Tags
Mots-clés libres en minuscules.

## Historique
- AAAA-MM-JJ — statut — commentaire (ex. `2026-07-04 — EXTRACTED — Gemini, prompt v2`)
```

## Cycle de vie des statuts

| Statut | Usage |
|---|---|
| `DRAFT` | règle esquissée, non sourcée ou encore ambiguë |
| `EXTRACTED` | règle extraite avec provenance, mais non encore validée |
| `VALIDATED` | source vérifiée, contradictions traitées et validation/simulation suffisante pour son domaine |
| `CONTRADICTED` | règle contredite ou dangereuse telle quelle |
| `DEPRECATED` | règle remplacée ou obsolète |

Les anciens libellés d'historique (`EXTRAITE`, `NORMALISÉE`, etc.) peuvent rester dans les lignes
d'historique, mais le champ `Statut` doit utiliser les cinq statuts canoniques ci-dessus.

## Critères de rejet automatique
Une règle est rejetée si : condition non testable, action non exécutable, source incomplète
(auteur/livre/chapitre/page), ou si elle constitue un résumé plutôt qu'une règle.
