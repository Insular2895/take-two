# Politique de statut des règles V1

Une règle ou preuve ne peut participer au moteur read-only que si son statut vaut :

- `validated` : validée pour l'usage déclaré ;
- `read_only_gate` : autorisée comme garde-fou de recherche, sans décision de trade.

Les statuts suivants déclenchent un veto lorsqu'ils sont utilisés pour une décision :

- `draft_to_validate` ;
- `to_review` ;
- `extracted` ;
- `blocked` ;
- `human_review_required` ;
- `unextractable` ;
- `image_only` ;
- `contradicted` ;
- `deprecated`.

Les règles V1 actives viennent de `CLEAN_USABLE_RULESET_2026.md` et des règles atomiques propres
`R-DECISION-001`, `R-GREEKS-001` et `R-OPTIONS-001`, toutes encodées comme gates read-only. Les
216 candidats documentaires et les 365 blocs bruts ne sont ni importés ni promus.

Un statut documentaire ne devient jamais automatiquement un statut opérationnel. Les rapports
conservent le statut, l'URI, la date d'accès, la confiance, les règles passées/échouées et les veto.
