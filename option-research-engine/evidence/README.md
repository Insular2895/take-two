# evidence/ — Dossiers de preuve

## Rôle

Ce dossier sert à conserver, pour chaque décision importante du futur moteur, le faisceau de preuves
qui justifie ou bloque cette décision.

Une décision peut être une règle activée, une structure d'option retenue, un seuil de scoring, une
hypothèse de marché, un choix de sizing, une règle de roll/close ou une intégration d'outil. Rien ne
doit passer de la recherche à l'usage opérationnel sans dossier de preuve.

Ce dossier versionné contient les preuves décisionnelles légères. Les médias de transcription
volumineux restent dans `evidence_packets/` local, ignoré par Git, et sont reliés par identifiants et
hashes plutôt que copiés dans le repository.

## Preuves de transcription PDF

La transcription V2 utilise une famille de statuts distincte du cycle de vie des règles :

| Statut élément | Sens |
|---|---|
| `machine_verified` | Extraction locale non critique et contrôles réussis |
| `machine_verified_with_visual_check` | Vérification Gemini concordante et contrôles réussis |
| `machine_reviewed` | Fallback Codex traçable et contrôles réussis |
| `needs_visual_review` | Ambiguïté non résolue |
| `human_verified` | Revue humaine documentée |
| `human_review_required` | Machine incapable de conclure |
| `blocked` | Désaccord ou contrôle critique en échec |
| `unextractable` | Source insuffisamment lisible |
| `image_only` | Figure conservée sans données numériques fiables |

Un élément PDF validé peut soutenir une règle `EXTRACTED`; il ne transforme jamais directement
cette règle en `VALIDATED`. Voir `../docs/07_transcription_pdf_technique_v2.md`.

## Statuts obligatoires

Chaque règle, source ou décision référencée dans un dossier de preuve doit utiliser l'un de ces
statuts :

| Statut | Sens | Utilisable par le futur moteur ? |
|---|---|---|
| `DRAFT` | idée, règle ou décision encore en formulation | Non |
| `EXTRACTED` | extrait d'une source, avec provenance, mais non encore validé | Non |
| `VALIDATED` | contrôlé par source fiable, cohérence interne, simulations ou validation humaine selon le cas | Oui, si les données live sont disponibles |
| `CONTRADICTED` | contredit par une source plus forte, une simulation ou une contrainte broker/réglementaire | Non |
| `DEPRECATED` | remplacé par une version plus récente ou rendu obsolète | Non |

Les statuts de blocage plus fins (`live_quotes_or_margin_missing`, `unbounded_risk_to_review`, etc.)
restent utiles dans `research/documentary/STRATEGY_READINESS_MATRIX.md`, mais ils ne remplacent pas
ces cinq statuts de cycle de vie.

## Contenu minimal d'un dossier de preuve

Chaque fichier de preuve doit répondre à ces questions :

1. Quelle décision est évaluée ?
2. Quel est son statut actuel ?
3. Quels livres, règles et sources externes la soutiennent ?
4. Quelles sources la contredisent ou la limitent ?
5. Quelles simulations favorables ont été faites ?
6. Quelles simulations défavorables ou stress tests ont été faits ?
7. Quelles données 2026/live restent nécessaires ?
8. Quelle validation humaine est requise avant usage ?

Le modèle officiel est `templates/decision_evidence.md`.

## Règles de gouvernance

- Une décision sans dossier `evidence/` reste `DRAFT` ou `EXTRACTED`.
- Une source open source ou un blog ne peut jamais valider seul une règle de trading.
- Les livres spécialisés peuvent valider une logique de structure, mais pas des données 2026 :
  settlement, marge, commissions, taxes, IV live, corporate actions, liquidité et règles broker
  doivent venir de sources actuelles.
- Une simulation favorable ne suffit pas : il faut aussi une simulation adverse ou un stress test.
- Une contradiction ouverte bloque l'usage automatique jusqu'à résolution documentée.
- IBKR peut préparer un ordre seulement après validation humaine explicite ; le dossier de preuve
  doit indiquer cette validation ou rester bloqué.

## Nom des fichiers

Format recommandé :

```text
evidence/<YYYY-MM-DD>_<decision_id>.md
```

Exemples :

- `2026-07-09_ttwo_gta6_vertical_vs_call.md`
- `2026-07-09_rule_gamma_scalping_activation.md`
- `2026-07-09_ibkr_order_preview_gate.md`
