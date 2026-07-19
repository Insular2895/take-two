# Contrats de données TTWO options V1

Le schéma JSON complet est disponible par :

```bash
.venv/bin/ttwo-options schema > reports/ttwo_options_v1.schema.json
```

## Paquet d'entrée

`MarketDataBundle` contient :

- `UnderlyingSnapshot` : ticker, place, devise, spot, timestamp, fraîcheur, sources, événements et
  corporate actions ;
- `FundamentalSnapshot` : direction, thèse, catalyseur daté, invalidation, scénarios probabilisés,
  fraîcheur et sources ;
- `PortfolioState` : budget de perte **de recherche**, hypothèses de commissions/slippage, état de
  marge et permissions ;
- `OptionQuote[]` : contrat, bid/ask, tailles, volume, open interest, IV, Greeks fournisseur,
  timestamp, fraîcheur et provenance ;
- taux sans risque et volatilité annualisée avec fraîcheur/source propres, puis paramètres
  Monte-Carlo.

## Contrat option

`OptionContract` exige `con_id`, `local_symbol`, `trading_class`, exchange, devise, expiration,
strike, type, multiplicateur positif, deliverable, style d'exercice, cycle de règlement et état
d'ajustement. Un multiplicateur nul ou un deliverable vide échoue à la validation avant moteur.

## Fraîcheur et provenance

Toute donnée de marché, fondamentale, taux, volatilité ou coût/marge porte `as_of`, `accessed_at`,
`status`, `is_stale` et éventuellement un âge maximal. Le moteur recalcule l'âge au freeze time :
un élément déclaré `current` mais hors fenêtre est veto. Les éléments utilisés dans la décision
portent un `EvidenceReference` avec identifiant, type, URI, statut, date d'accès, confiance et
notes.

Seuls `validated` et `read_only_gate` autorisent le calcul de recherche. `draft_to_validate`,
`to_review`, `blocked`, `human_review_required`, `unextractable`, `image_only`, `contradicted` et
`deprecated` entraînent un veto lorsqu'ils sont décisionnels.

## HistoricalOptionQuote V4

Le champ `price_basis` separe trois preuves incompatibles :

- `nbbo` : quote bid/ask historique intraday horodatee ;
- `eod_bid_ask` : bid/ask de fin de session, sans replay du chemin intraday ;
- `option_bar_close_proxy` : close d'une barre de transactions utilise comme proxy.

Une quote EOD peut transporter `bid_size`, `ask_size`, `volume`, `open_interest` et
`underlying_price`. Ces champs restent optionnels pour conserver les fixtures historiques. Le
multiplicateur ne vient jamais de la quote et reste obligatoire dans la specification source.

## Sortie

`DecisionReport` conserve le paquet d'entrée, tous les candidats, leurs jambes, coûts, risques,
scénarios, règles, preuves, veto et score décomposé. `decision_posture` vaut uniquement
`read_only_research`.

## MarketDataPanelReport V5

Le panel walk-forward separe trois dates par observation : `signal_quote_date`,
`entry_quote_date` et `exit_quote_date`, avec l'invariant strict `signal < entry < exit`. Le contrat
selectionne sur le signal est recherche exactement aux dates d'entree et de sortie ; une jambe
absente, sans bid/ask positif ou produisant un credit non prevu est rejetee.

Chaque strategie conserve : symboles OCC, position, strike, delta locale, bid/ask, open interest,
volume, resultats normalises, couverture, raisons d'ineligibilite et rapport de backtest brut.
`ranked_strategy_ids` ne contient que les strategies ayant passe les seuils de preuve et les veto
de rendement/drawdown/perte/stabilite. `comparison_order` permet d'auditer les strategies bloquees
sans les presenter comme candidates eligibles. `order_capability` reste `forbidden`.
