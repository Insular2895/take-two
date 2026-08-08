# Validation finale pré-OPRA — phases A à L

Résultat immédiat : `BLOCKED_BY_DATA` et `NO_POSITION_RECOMMENDED`.

Les phases A–L sont implémentées, testées et livrées avec un commit atomique par phase.
La phase M n'a pas été démarrée. Le niveau de preuve reste `software_tested_only` : les
diagnostics réels close-only ne suffisent pas à démontrer une performance d'options.

À lire en priorité :

- dashboard statique : `reports/pre_opra/final_pre_opra_report_2026-08-08.html` ;
- rapport lisible : `reports/pre_opra/final_pre_opra_report_2026-08-08.md` ;
- rapport machine : `reports/pre_opra/final_pre_opra_report_2026-08-08.json` ;
- manifeste : `reports/pre_opra/run_manifest_2026-08-08.json` ;
- méthodologies : `docs/methodology/` ;
- audits, sources et livres : `docs/audits/` et `docs/research/`.

Les sorties manquantes restent `null`, `unavailable` ou `blocked`; aucune valeur
illustrative n'est promue en résultat TTWO. Le holdout est `UNOPENED`, les données
privées restent hors Git et la capacité d'ordre est `forbidden`.
