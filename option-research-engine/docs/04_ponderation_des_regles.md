# Pondération des règles et des auteurs

## 1. Poids d'une règle

Le poids effectif d'une règle dans le moteur est le produit de quatre facteurs :

`poids = confiance_source × convergence × validation × spécificité`

| Facteur | Définition | Échelle |
|---|---|---|
| `confiance_source` | Niveau de confiance de la fiche livre (autorité de l'auteur dans SA catégorie) | 1–5 normalisé |
| `convergence` | Nombre de sources indépendantes recommandant la même action | 1.0 (une source) → bonus par source additionnelle, plafonné |
| `validation` | 0 si invalidée par simulation, 1 si non testée, >1 si confirmée par simulation | 0 / 1 / 1.5 |
| `spécificité` | Une règle chiffrée et conditionnelle pèse plus qu'une règle vague | 0.5–1.5 |

Les coefficients exacts seront calibrés en phase de validation ; ce document fixe la **structure**
de la pondération, pas ses constantes (aucune constante arbitraire ne doit être codée en dur).

## 2. Poids des auteurs

Un auteur n'a pas un poids global : il a un poids **par catégorie**. Exemple : Natenberg pèse
fortement en `VOL` et `OPTIONS`, pas en `VALUATION`. Le poids par catégorie est fixé dans la fiche
livre et révisé quand les simulations valident ou invalident ses règles (boucle de rétroaction du
journal de décision, cf. `docs/06_moteur_maintenance.md`).

## 3. Vote multi-livres

Quand plusieurs règles s'appliquent à une même décision, le moteur agrège les poids par action
candidate (mécanisme de vote pondéré, spécifié dans `decision_engine/05_conflits_et_vote.md`).
