# Guide des fixtures

Toutes les fixtures sont synthetiques et deterministes :

- `ttwo_v1_fixture.json` conserve le contrat de compatibilite V1 ;
- `ttwo_v2_fixture.json` ajoute surface IV, pricing americain et trois modeles de simulation ;
- `ttwo_v2_calibration_fixture.json` valide les controles de calibration ;
- `ttwo_v2_backtest_fixture.json` valide bid/ask, couts, train/test et look-ahead.
- `alpaca_tt_options_backtest_spec.example.json` est une specification d'ingestion, pas un dataset ;
  ses symboles doivent etre confirmes via `alpaca-chain`.
- `marketdata_tt_options_backtest_spec.example.json` est une specification EOD, pas un dataset ;
  ses symboles OCC, multiplicateurs, taux et dividendes doivent etre verifies avant ingestion.
- `marketdata_tt_options_panel_v1.json` definit 10 observations walk-forward ; les quotes reelles
  sont telechargees depuis MarketData.app et restent hors Git.
- `experiments/legacy/v7/fixtures/marketdata_tt_options_accuracy_v7_generator.json`
  reproduit la campagne de precision V7.
- `experiments/legacy/v8/fixtures/marketdata_tt_options_opportunity_v8_generator.json`
  definit les familles V8, les quantites,
  profils delta/moneyness, echeances avant/arriere et politiques TP/SL/time ; il genere une spec,
  pas des prix de marche.
- `experiments/legacy/v9/fixtures/marketdata_tt_options_budget_v9_generator.json`
  ajoute les plans `single_long` et
  `staged_three`, leurs poches en EUR, le taux EUR/USD date et les recettes court/moyen/long.

Leurs valeurs de spot, chaine, volatilite, scenarios, probabilites, frais et marge ne sont ni live
ni executables.

Pour créer une fixture de validation :

1. copier la structure sans retirer les champs de provenance ;
2. remplacer chaque valeur instable et son timestamp depuis une source autorisée ;
3. distinguer faits source, hypothèses analyste et calculs dérivés dans `notes` ;
4. marquer toute donnée ambiguë `to_review` ou `draft_to_validate` ;
5. vérifier que les probabilités fondamentales totalisent exactement 1 ;
6. exécuter tests, rapport JSON, Markdown et journal ;
7. faire valider humainement les événements, contrats ajustés, dividendes et coûts.

Pour une fixture historique, `data_available_at` doit etre inferieur ou egal au timestamp de
decision. Le cutoff de calibration doit preceder strictement chaque entree de backtest. Une ligne
publiee tardivement doit etre exclue meme si sa date economique est anterieure.

Une fixture peut être `current` dans sa fenêtre de test tout en restant explicitement
`offline_fixture` et de confiance faible. Ce statut valide le contrat de test, pas le marché réel.

Le fixture de panel contient uniquement les dates, hypotheses, couts et seuils. Le taux `0.04`,
l'absence de dividende, le multiplicateur `100` et les veto de risque restent a valider. Son
resultat source-backed reste `screen_grade` et ne constitue pas une autorisation de trade.
