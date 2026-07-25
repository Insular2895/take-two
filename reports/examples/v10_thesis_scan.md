# V10 Bullish Thesis Scanner

- Statut global : `watchlist`
- Ticker / direction : `TTWO` / bullish
- Spot de référence : `$230.00` au `2026-07-24T20:00:00+00:00`
- Budget : `€1,000.00` ; perte maximale : `€1,000.00`
- Catalyseur : `2026-11-19` + `45` jours
- Probabilités : `user_supplied`
- Capacité d'ordre : `forbidden`

> Recherche en lecture seule. Les candidats sont des constructions synthétiques à contrôler dans IBKR, pas des recommandations.

## Trois profils

### Prudent

| Rang | Candidat | Structure | Score | Coût EUR | Perte max USD | Statut |
|---:|---|---|---:|---:|---:|---|
| 1 | `cand-75984ebc6c766510` | Bull call spread 230/250 · 2027-03-19 | 73.58 | €770.79 | $881.40 | `watchlist` |
| 2 | `cand-119e6d7d30c47119` | Bull call spread 240/260 · 2027-03-19 | 73.55 | €683.34 | $781.40 | `watchlist` |
| 3 | `cand-b9aa8a0e0964eb88` | Bull call spread 220/240 · 2027-12-17 | 73.53 | €875.73 | $1,001.40 | `watchlist` |

### Balanced

| Rang | Candidat | Structure | Score | Coût EUR | Perte max USD | Statut |
|---:|---|---|---:|---:|---:|---|
| 1 | `cand-5159edae09c7d168` | Long call 280 · 2027-03-19 | 66.23 | €595.28 | $680.70 | `watchlist` |
| 2 | `cand-a31726b9f88bb946` | Long call 260 · 2027-03-19 | 65.37 | €997.55 | $1,140.70 | `watchlist` |
| 3 | `cand-c15c8aa5445d3fe8` | Bull call spread 250/280 · 2027-03-19 | 65.23 | €718.32 | $821.40 | `watchlist` |

### Aggressive

| Rang | Candidat | Structure | Score | Coût EUR | Perte max USD | Statut |
|---:|---|---|---:|---:|---:|---|
| 1 | `cand-4dfb14afde235e50` | Long call 300 · 2027-03-19 | 57.65 | €674.60 | $771.40 | `watchlist` |
| 2 | `cand-a31726b9f88bb946` | Long call 260 · 2027-03-19 | 57.47 | €997.55 | $1,140.70 | `watchlist` |
| 3 | `cand-13690dc64acaef11` | LEAPS call 360 · 2027-12-17 | 56.81 | €901.97 | $1,031.40 | `watchlist` |

## Filtrage auditable

- Quotes reçues : `22`
- Calls utilisables : `20`
- Combinaisons générées : `258`
- Candidats techniquement admissibles : `18`

| Motif | Nombre |
|---|---:|
| `BUDGET_EXCEEDED` | 188 |
| `COMBO_SPREAD_FAILED` | 57 |
| `LEG_SPREAD_TOO_WIDE` | 2 |
| `LIQUIDITY_FAILED` | 57 |
| `MAXIMUM_LOSS_EXCEEDED` | 188 |

## Bull call spread 240/260 · 2027-03-19

- ID : `cand-119e6d7d30c47119`
- Architecture : `bull_call_spread` ; maturité : `standard` ; DTE : `238`
- Combo : mid `$700.00` / `€612.16` ; débit prudent `$780.00` / `€682.12`
- Slippage / commissions : `$0.10` / `$1.30` ; `€0.09` / `€1.14`
- Coût total : `$781.40` / `€683.34`
- FX : `1.143500 USD/EUR`, `2026-07-17`, European Central Bank reference rate snapshot (configuration input)
- Perte max : `$781.40` / `€683.34` ; gain max contractuel : `1218.6`
- Break-even : `[247.814]`
- Greeks nets : delta `11.253`, gamma `0.015`, theta `-0.297`, vega `1.229`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00240000` | 240 | $17.60 | $18.40 | $18.00 | 100 |
| VENDRE | 1 | `TTWO270319C00260000` | 260 | $10.60 | $11.40 | $11.00 | 100 |

### P&L aux objectifs, date du catalyseur, IV stable

| Spot | P&L USD |
|---:|---:|
| $220.00 | $-282.32 |
| $250.00 | $180.07 |
| $280.00 | $603.69 |
| $300.00 | $814.10 |
| $330.00 | $1,016.44 |
| $360.00 | $1,118.63 |

P&L espéré utilisateur : `$653.42` ; probabilité de résultat positif : `90.00%`.

### Alertes

- `NON_EXECUTABLE_QUOTE_QUALITY:synthetic`
- `Synthetic fixture for deterministic tests and documentation only`

### Preview IBKR

- Type / ordre : `BAG` / `LMT` ; `mode=preview` ; `transmit=false` ; `what_if=true`
- Débit maximum indicatif : `$7.80` par action de combo
- Coût indicatif par lot : `$781.40` / `€683.34`
- Date de la quote : `2026-07-24T20:00:00+00:00`
- Message : vérifier la cotation combo live dans IBKR avant validation
- ACHETER `1` × `TTWO270319C00240000` CALL 240 2027-03-19 SMART
- VENDRE `1` × `TTWO270319C00260000` CALL 260 2027-03-19 SMART

## LEAPS call 360 · 2027-12-17

- ID : `cand-13690dc64acaef11`
- Architecture : `long_call` ; maturité : `leaps` ; DTE : `511`
- Combo : mid `$960.00` / `€839.53` ; débit prudent `$1,030.00` / `€900.74`
- Slippage / commissions : `$0.10` / `$1.30` ; `€0.09` / `€1.14`
- Coût total : `$1,031.40` / `€901.97`
- FX : `1.143500 USD/EUR`, `2026-07-17`, European Central Bank reference rate snapshot (configuration input)
- Perte max : `$1,031.40` / `€901.97` ; gain max contractuel : `illimité`
- Break-even : `[365.157]`
- Greeks nets : delta `49.896`, gamma `0.627`, theta `-7.246`, vega `172.733`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 2 | `TTWO271217C00360000` | 360 | $4.45 | $5.15 | $4.80 | 100 |

### P&L aux objectifs, date du catalyseur, IV stable

| Spot | P&L USD |
|---:|---:|
| $220.00 | $213.53 |
| $250.00 | $1,476.80 |
| $280.00 | $3,343.15 |
| $300.00 | $4,935.38 |
| $330.00 | $7,831.38 |
| $360.00 | $11,291.53 |

P&L espéré utilisateur : `$5,158.58` ; probabilité de résultat positif : `100.00%`.

### Alertes

- `NON_EXECUTABLE_QUOTE_QUALITY:synthetic`
- `Synthetic fixture for deterministic tests and documentation only`

### Preview IBKR

- Type / ordre : `OPT` / `LMT` ; `mode=preview` ; `transmit=false` ; `what_if=true`
- Débit maximum indicatif : `$5.15` par action de combo
- Coût indicatif par lot : `$515.70` / `€901.97`
- Date de la quote : `2026-07-24T20:00:00+00:00`
- Message : vérifier la cotation combo live dans IBKR avant validation
- ACHETER `2` × `TTWO271217C00360000` CALL 360 2027-12-17 SMART

## Long call 300 · 2027-03-19

- ID : `cand-4dfb14afde235e50`
- Architecture : `long_call` ; maturité : `standard` ; DTE : `238`
- Combo : mid `$720.00` / `€629.65` ; débit prudent `$770.00` / `€673.37`
- Slippage / commissions : `$0.10` / `$1.30` ; `€0.09` / `€1.14`
- Coût total : `$771.40` / `€674.60`
- FX : `1.143500 USD/EUR`, `2026-07-17`, European Central Bank reference rate snapshot (configuration input)
- Perte max : `$771.40` / `€674.60` ; gain max contractuel : `illimité`
- Break-even : `[303.857]`
- Greeks nets : delta `49.745`, gamma `0.936`, theta `-9.970`, vega `117.703`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 2 | `TTWO270319C00300000` | 300 | $3.35 | $3.85 | $3.60 | 100 |

### P&L aux objectifs, date du catalyseur, IV stable

| Spot | P&L USD |
|---:|---:|
| $220.00 | $-418.15 |
| $250.00 | $529.09 |
| $280.00 | $2,529.25 |
| $300.00 | $4,533.41 |
| $330.00 | $8,464.31 |
| $360.00 | $13,259.09 |

P&L espéré utilisateur : `$5,131.80` ; probabilité de résultat positif : `90.00%`.

### Alertes

- `NON_EXECUTABLE_QUOTE_QUALITY:synthetic`
- `Synthetic fixture for deterministic tests and documentation only`

### Preview IBKR

- Type / ordre : `OPT` / `LMT` ; `mode=preview` ; `transmit=false` ; `what_if=true`
- Débit maximum indicatif : `$3.85` par action de combo
- Coût indicatif par lot : `$385.70` / `€674.60`
- Date de la quote : `2026-07-24T20:00:00+00:00`
- Message : vérifier la cotation combo live dans IBKR avant validation
- ACHETER `2` × `TTWO270319C00300000` CALL 300 2027-03-19 SMART

## Long call 280 · 2027-03-19

- ID : `cand-5159edae09c7d168`
- Architecture : `long_call` ; maturité : `standard` ; DTE : `238`
- Combo : mid `$650.00` / `€568.43` ; débit prudent `$680.00` / `€594.67`
- Slippage / commissions : `$0.05` / `$0.65` ; `€0.04` / `€0.57`
- Coût total : `$680.70` / `€595.28`
- FX : `1.143500 USD/EUR`, `2026-07-17`, European Central Bank reference rate snapshot (configuration input)
- Perte max : `$680.70` / `€595.28` ; gain max contractuel : `illimité`
- Break-even : `[286.807]`
- Greeks nets : delta `32.961`, gamma `0.535`, theta `-5.783`, vega `67.238`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00280000` | 280 | $6.20 | $6.80 | $6.50 | 100 |

### P&L aux objectifs, date du catalyseur, IV stable

| Spot | P&L USD |
|---:|---:|
| $220.00 | $-335.76 |
| $250.00 | $414.73 |
| $280.00 | $1,794.88 |
| $300.00 | $3,057.75 |
| $330.00 | $5,360.73 |
| $360.00 | $7,998.69 |

P&L espéré utilisateur : `$3,271.11` ; probabilité de résultat positif : `90.00%`.

### Alertes

- `NON_EXECUTABLE_QUOTE_QUALITY:synthetic`
- `Synthetic fixture for deterministic tests and documentation only`

### Preview IBKR

- Type / ordre : `OPT` / `LMT` ; `mode=preview` ; `transmit=false` ; `what_if=true`
- Débit maximum indicatif : `$6.80` par action de combo
- Coût indicatif par lot : `$680.70` / `€595.28`
- Date de la quote : `2026-07-24T20:00:00+00:00`
- Message : vérifier la cotation combo live dans IBKR avant validation
- ACHETER `1` × `TTWO270319C00280000` CALL 280 2027-03-19 SMART

## Bull call spread 230/250 · 2027-03-19

- ID : `cand-75984ebc6c766510`
- Architecture : `bull_call_spread` ; maturité : `standard` ; DTE : `238`
- Combo : mid `$800.00` / `€699.61` ; débit prudent `$880.00` / `€769.57`
- Slippage / commissions : `$0.10` / `$1.30` ; `€0.09` / `€1.14`
- Coût total : `$881.40` / `€770.79`
- FX : `1.143500 USD/EUR`, `2026-07-17`, European Central Bank reference rate snapshot (configuration input)
- Perte max : `$881.40` / `€770.79` ; gain max contractuel : `1118.6`
- Break-even : `[238.814]`
- Greeks nets : delta `11.696`, gamma `-0.002`, theta `-0.070`, vega `-1.844`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00230000` | 230 | $21.60 | $22.40 | $22.00 | 100 |
| VENDRE | 1 | `TTWO270319C00250000` | 250 | $13.60 | $14.40 | $14.00 | 100 |

### P&L aux objectifs, date du catalyseur, IV stable

| Spot | P&L USD |
|---:|---:|
| $220.00 | $-246.44 |
| $250.00 | $238.71 |
| $280.00 | $634.09 |
| $300.00 | $813.37 |
| $330.00 | $972.67 |
| $360.00 | $1,046.18 |

P&L espéré utilisateur : `$652.11` ; probabilité de résultat positif : `90.00%`.

### Alertes

- `NON_EXECUTABLE_QUOTE_QUALITY:synthetic`
- `Synthetic fixture for deterministic tests and documentation only`

### Preview IBKR

- Type / ordre : `BAG` / `LMT` ; `mode=preview` ; `transmit=false` ; `what_if=true`
- Débit maximum indicatif : `$8.80` par action de combo
- Coût indicatif par lot : `$881.40` / `€770.79`
- Date de la quote : `2026-07-24T20:00:00+00:00`
- Message : vérifier la cotation combo live dans IBKR avant validation
- ACHETER `1` × `TTWO270319C00230000` CALL 230 2027-03-19 SMART
- VENDRE `1` × `TTWO270319C00250000` CALL 250 2027-03-19 SMART

## Long call 260 · 2027-03-19

- ID : `cand-a31726b9f88bb946`
- Architecture : `long_call` ; maturité : `standard` ; DTE : `238`
- Combo : mid `$1,100.00` / `€961.96` ; débit prudent `$1,140.00` / `€996.94`
- Slippage / commissions : `$0.05` / `$0.65` ; `€0.04` / `€0.57`
- Coût total : `$1,140.70` / `€997.55`
- FX : `1.143500 USD/EUR`, `2026-07-17`, European Central Bank reference rate snapshot (configuration input)
- Perte max : `$1,140.70` / `€997.55` ; gain max contractuel : `illimité`
- Break-even : `[271.407]`
- Greeks nets : delta `42.098`, gamma `0.608`, theta `-6.223`, vega `72.669`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00260000` | 260 | $10.60 | $11.40 | $11.00 | 100 |

### P&L aux objectifs, date du catalyseur, IV stable

| Spot | P&L USD |
|---:|---:|
| $220.00 | $-534.91 |
| $250.00 | $571.60 |
| $280.00 | $2,374.56 |
| $300.00 | $3,895.25 |
| $330.00 | $6,496.66 |
| $360.00 | $9,321.38 |

P&L espéré utilisateur : `$3,983.75` ; probabilité de résultat positif : `90.00%`.

### Alertes

- `NON_EXECUTABLE_QUOTE_QUALITY:synthetic`
- `Synthetic fixture for deterministic tests and documentation only`

### Preview IBKR

- Type / ordre : `OPT` / `LMT` ; `mode=preview` ; `transmit=false` ; `what_if=true`
- Débit maximum indicatif : `$11.40` par action de combo
- Coût indicatif par lot : `$1,140.70` / `€997.55`
- Date de la quote : `2026-07-24T20:00:00+00:00`
- Message : vérifier la cotation combo live dans IBKR avant validation
- ACHETER `1` × `TTWO270319C00260000` CALL 260 2027-03-19 SMART

## Bull call spread 220/240 · 2027-12-17

- ID : `cand-b9aa8a0e0964eb88`
- Architecture : `bull_call_spread` ; maturité : `standard` ; DTE : `511`
- Combo : mid `$900.00` / `€787.06` ; débit prudent `$1,000.00` / `€874.51`
- Slippage / commissions : `$0.10` / `$1.30` ; `€0.09` / `€1.14`
- Coût total : `$1,001.40` / `€875.73`
- FX : `1.143500 USD/EUR`, `2026-07-17`, European Central Bank reference rate snapshot (configuration input)
- Perte max : `$1,001.40` / `€875.73` ; gain max contractuel : `998.6`
- Break-even : `[230.014]`
- Greeks nets : delta `8.382`, gamma `-0.046`, theta `0.138`, vega `-7.730`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO271217C00220000` | 220 | $41.50 | $42.50 | $42.00 | 100 |
| VENDRE | 1 | `TTWO271217C00240000` | 240 | $32.50 | $33.50 | $33.00 | 100 |

### P&L aux objectifs, date du catalyseur, IV stable

| Spot | P&L USD |
|---:|---:|
| $220.00 | $-174.99 |
| $250.00 | $108.22 |
| $280.00 | $343.72 |
| $300.00 | $469.79 |
| $330.00 | $615.44 |
| $360.00 | $717.57 |

P&L espéré utilisateur : `$392.16` ; probabilité de résultat positif : `90.00%`.

### Alertes

- `NON_EXECUTABLE_QUOTE_QUALITY:synthetic`
- `Synthetic fixture for deterministic tests and documentation only`

### Preview IBKR

- Type / ordre : `BAG` / `LMT` ; `mode=preview` ; `transmit=false` ; `what_if=true`
- Débit maximum indicatif : `$10.00` par action de combo
- Coût indicatif par lot : `$1,001.40` / `€875.73`
- Date de la quote : `2026-07-24T20:00:00+00:00`
- Message : vérifier la cotation combo live dans IBKR avant validation
- ACHETER `1` × `TTWO271217C00220000` CALL 220 2027-12-17 SMART
- VENDRE `1` × `TTWO271217C00240000` CALL 240 2027-12-17 SMART

## Bull call spread 250/280 · 2027-03-19

- ID : `cand-c15c8aa5445d3fe8`
- Architecture : `bull_call_spread` ; maturité : `standard` ; DTE : `238`
- Combo : mid `$750.00` / `€655.88` ; débit prudent `$820.00` / `€717.10`
- Slippage / commissions : `$0.10` / `$1.30` ; `€0.09` / `€1.14`
- Coût total : `$821.40` / `€718.32`
- FX : `1.143500 USD/EUR`, `2026-07-17`, European Central Bank reference rate snapshot (configuration input)
- Perte max : `$821.40` / `€718.32` ; gain max contractuel : `2178.6`
- Break-even : `[258.214]`
- Greeks nets : delta `14.627`, gamma `0.077`, theta `-0.641`, vega `6.768`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00250000` | 250 | $13.60 | $14.40 | $14.00 | 100 |
| VENDRE | 1 | `TTWO270319C00280000` | 280 | $6.20 | $6.80 | $6.50 | 100 |

### P&L aux objectifs, date du catalyseur, IV stable

| Spot | P&L USD |
|---:|---:|
| $220.00 | $-342.35 |
| $250.00 | $237.07 |
| $280.00 | $876.80 |
| $300.00 | $1,247.10 |
| $330.00 | $1,657.63 |
| $360.00 | $1,903.25 |

P&L espéré utilisateur : `$1,043.12` ; probabilité de résultat positif : `90.00%`.

### Alertes

- `NON_EXECUTABLE_QUOTE_QUALITY:synthetic`
- `Synthetic fixture for deterministic tests and documentation only`

### Preview IBKR

- Type / ordre : `BAG` / `LMT` ; `mode=preview` ; `transmit=false` ; `what_if=true`
- Débit maximum indicatif : `$8.20` par action de combo
- Coût indicatif par lot : `$821.40` / `€718.32`
- Date de la quote : `2026-07-24T20:00:00+00:00`
- Message : vérifier la cotation combo live dans IBKR avant validation
- ACHETER `1` × `TTWO270319C00250000` CALL 250 2027-03-19 SMART
- VENDRE `1` × `TTWO270319C00280000` CALL 280 2027-03-19 SMART

## Historique de backtest — séparé de la simulation actuelle

- Statut : `weak_contaminated`
- Effet sur l'éligibilité : `warning_only`
- Confiance : `0.35`
- V7-V9 conservent NO_TRADE ou des variantes bloquées; ces résultats sont affichés séparément et ne sont pas réutilisés comme holdout vierge.
- Limite historique : Historique EOD jambe par jambe, pas de replay combo NBBO
- Limite historique : Holdouts V7-V9 déjà inspectés et donc contaminés
- Limite historique : Échantillon multi-régime insuffisant pour valider une thèse TTWO
- Artefact : `docs/archive/v9/ttwo_options_budget_engine_v9.md`
- Artefact : `validation/contaminated_holdouts/v7_v8_v9/manifest.json`

## Limites et hypothèses actuelles

- Les résultats historiques V9 étaient faibles/contaminés et abaissent la confiance à 0.35; ils ne bloquent pas automatiquement ce mode de thèse et ne constituent pas une validation.
- Une chaîne de jambes ne garantit pas une exécution combo simultanée.
- Les IV et Greeks sont des estimations de modèle, pas des cotations.
- Les dividendes, taux, FX, coûts et seuils de liquidité sont des entrées datées à revérifier.
- Les contrats au multiplicateur ou livrable non confirmés restent signalés et doivent être contrôlés dans IBKR.
- Aucune allocation V9 fixe n'est réutilisée dans ce scanner.
- Hypothèse : LEAPS call désigne une classe de maturité de long call, jamais une architecture distincte.
- Hypothèse : Le débit prudent utilise ask pour chaque achat et bid pour chaque vente.
- Hypothèse : Le moteur de scénario pré-échéance est le moteur américain QuantLib finite-difference partagé.
- Hypothèse : Les objectifs de cours viennent de l'utilisateur; le scanner n'invente aucune probabilité.

## Sources

- European Central Bank reference rate snapshot (configuration input)
- TTWO configured as non-dividend-paying; verify before live use
- US Treasury market proxy (configuration input)
- research/knowledge_items (compiled strategy recipes)
- synthetic-ttwo-chain-v10
- synthetic-ttwo-spot-v10
