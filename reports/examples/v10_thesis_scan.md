# V10.1 Bullish Thesis Scanner

- Statut global : `watchlist`
- Ticker / direction : `TTWO` / bullish
- Spot de référence : `$230.00` au `2026-07-24T20:00:00+00:00`
- Budget : `€1,000.00` ; perte maximale : `€1,000.00`
- Catalyseur : `2026-11-19` + `45` jours
- Probabilités : `user_supplied`
- Capacité d'ordre : `forbidden`

> Recherche en lecture seule. Les candidats sont des constructions synthétiques à contrôler dans IBKR, pas des recommandations.

## Meilleures stratégies — Top 3 par profil

### Prudent

| Rang | Candidat | Structure | Score | Coût EUR | Perte max EUR | Meilleur gain modélisé EUR | Break-even | Statut |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | `cand-75984ebc6c766510` | Bull call spread 230/250 · 2027-03-19 | 73.58 | €770.79 | €770.79 | €978.22 | `[238.814]` | `watchlist` |
| 2 | `cand-119e6d7d30c47119` | Bull call spread 240/260 · 2027-03-19 | 73.55 | €683.34 | €683.34 | €1,065.68 | `[247.814]` | `watchlist` |
| 3 | `cand-b9aa8a0e0964eb88` | Bull call spread 220/240 · 2027-12-17 | 73.53 | €875.73 | €875.73 | €873.28 | `[230.014]` | `watchlist` |

### Balanced

| Rang | Candidat | Structure | Score | Coût EUR | Perte max EUR | Meilleur gain modélisé EUR | Break-even | Statut |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | `cand-5159edae09c7d168` | Long call 280 · 2027-03-19 | 66.23 | €595.28 | €595.28 | €8,187.21 | `[286.807]` | `watchlist` |
| 2 | `cand-a31726b9f88bb946` | Long call 260 · 2027-03-19 | 65.37 | €997.55 | €997.55 | €9,031.05 | `[271.407]` | `watchlist` |
| 3 | `cand-c15c8aa5445d3fe8` | Bull call spread 250/280 · 2027-03-19 | 65.23 | €718.32 | €718.32 | €1,905.20 | `[258.214]` | `watchlist` |

### Aggressive

| Rang | Candidat | Structure | Score | Coût EUR | Perte max EUR | Meilleur gain modélisé EUR | Break-even | Statut |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | `cand-4dfb14afde235e50` | Long call 300 · 2027-03-19 | 57.65 | €674.60 | €674.60 | €14,507.62 | `[303.857]` | `watchlist` |
| 2 | `cand-a31726b9f88bb946` | Long call 260 · 2027-03-19 | 57.47 | €997.55 | €997.55 | €9,031.05 | `[271.407]` | `watchlist` |
| 3 | `cand-13690dc64acaef11` | LEAPS call 360 · 2027-12-17 | 56.81 | €901.97 | €901.97 | €13,586.74 | `[365.157]` | `watchlist` |

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
- Perte max : `$781.40` / `€683.34` ; `68.33%` du budget
- Gain maximal contractuel : `1218.6`
- Meilleur gain parmi les scénarios modélisés : `$1,218.60` / `€1,065.68`
- Ratio gain/perte contractuel : `1.55950857` ; ratio modélisé : `1.5595`
- Break-even : `[247.814]`
- Tu perds tout ou partie de la mise si TTWO termine sous $247.81; à ou sous $240.00, la perte maximale est atteinte.
- Tu gagnes à l’échéance au-dessus de $247.81; le gain est plafonné à partir de $260.00.
- Greeks nets : delta `11.253`, gamma `0.015`, theta `-0.297`, vega `1.229`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00240000` | 240 | $17.60 | $18.40 | $18.00 | 100 |
| VENDRE | 1 | `TTWO270319C00260000` | 260 | $10.60 | $11.40 | $11.00 | 100 |

### Seuils de performance à l'échéance

> ×2 la mise = valeur finale égale à deux fois le coût total initial, soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie n'est ajouté.
- ×2 : Cours TTWO à l’échéance : $255.63
- ×3 : Impossible — gain plafonné par la structure.
- ×5 : Impossible — gain plafonné par la structure.

### P&L aux objectifs

| Spot | Catalyseur IV down | Catalyseur IV stable | Catalyseur IV up | Échéance |
|---:|---:|---:|---:|---:|
| $220.00 | $-354.28 / €-309.82 | $-282.32 / €-246.89 | $-234.92 / €-205.44 | $-781.40 / €-683.34 |
| $250.00 | $208.79 / €182.59 | $180.07 / €157.47 | $155.62 / €136.09 | $218.60 / €191.17 |
| $280.00 | $717.17 / €627.17 | $603.69 / €527.93 | $516.35 / €451.55 | $1,218.60 / €1,065.68 |
| $300.00 | $937.56 / €819.91 | $814.10 / €711.94 | $709.49 / €620.46 | $1,218.60 / €1,065.68 |
| $330.00 | $1,108.67 / €969.55 | $1,016.44 / €888.89 | $918.93 / €803.61 | $1,218.60 / €1,065.68 |
| $360.00 | $1,169.81 / €1,023.01 | $1,118.63 / €978.25 | $1,047.04 / €915.65 | $1,218.60 / €1,065.68 |

P&L espéré conditionnel aux probabilités utilisateur : `$653.42` / `€571.42` ; probabilité de résultat positif : `90.00%`.

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
- Perte max : `$1,031.40` / `€901.97` ; `90.20%` du budget
- Gain maximal contractuel : `Illimité théorique`
- Meilleur gain parmi les scénarios modélisés : `$15,536.44` / `€13,586.74`
- Ratio gain/perte contractuel : `non borné` ; ratio modélisé : `15.0634`
- Break-even : `[365.157]`
- Tu perds tout ou partie de la mise si TTWO termine sous $365.16; à ou sous $360.00, la prime peut être perdue intégralement.
- Tu gagnes à l’échéance si TTWO dépasse $365.16; le gain contractuel reste théoriquement illimité.
- Greeks nets : delta `49.896`, gamma `0.627`, theta `-7.246`, vega `172.733`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 2 | `TTWO271217C00360000` | 360 | $4.45 | $5.15 | $4.80 | 100 |

### Seuils de performance à l'échéance

> ×2 la mise = valeur finale égale à deux fois le coût total initial, soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie n'est ajouté.
- ×2 : Cours TTWO à l’échéance : $370.31
- ×3 : Cours TTWO à l’échéance : $375.47
- ×5 : Cours TTWO à l’échéance : $385.79

### P&L aux objectifs

| Spot | Catalyseur IV down | Catalyseur IV stable | Catalyseur IV up | Échéance |
|---:|---:|---:|---:|---:|
| $220.00 | $-496.53 / €-434.22 | $213.53 / €186.73 | $1,147.53 / €1,003.52 | $-1,031.40 / €-901.97 |
| $250.00 | $331.76 / €290.13 | $1,476.80 / €1,291.48 | $2,791.12 / €2,440.86 | $-1,031.40 / €-901.97 |
| $280.00 | $1,781.50 / €1,557.94 | $3,343.15 / €2,923.61 | $4,991.23 / €4,364.87 | $-1,031.40 / €-901.97 |
| $300.00 | $3,146.07 / €2,751.27 | $4,935.38 / €4,316.03 | $6,761.09 / €5,912.63 | $-1,031.40 / €-901.97 |
| $330.00 | $5,810.25 / €5,081.11 | $7,831.38 / €6,848.61 | $9,843.43 / €8,608.16 | $-1,031.40 / €-901.97 |
| $360.00 | $9,179.48 / €8,027.53 | $11,291.53 / €9,874.53 | $13,393.88 / €11,713.05 | $-1,031.40 / €-901.97 |

P&L espéré conditionnel aux probabilités utilisateur : `$5,158.58` / `€4,511.22` ; probabilité de résultat positif : `100.00%`.

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
- Perte max : `$771.40` / `€674.60` ; `67.46%` du budget
- Gain maximal contractuel : `Illimité théorique`
- Meilleur gain parmi les scénarios modélisés : `$16,589.47` / `€14,507.62`
- Ratio gain/perte contractuel : `non borné` ; ratio modélisé : `21.5057`
- Break-even : `[303.857]`
- Tu perds tout ou partie de la mise si TTWO termine sous $303.86; à ou sous $300.00, la prime peut être perdue intégralement.
- Tu gagnes à l’échéance si TTWO dépasse $303.86; le gain contractuel reste théoriquement illimité.
- Greeks nets : delta `49.745`, gamma `0.936`, theta `-9.970`, vega `117.703`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 2 | `TTWO270319C00300000` | 300 | $3.35 | $3.85 | $3.60 | 100 |

### Seuils de performance à l'échéance

> ×2 la mise = valeur finale égale à deux fois le coût total initial, soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie n'est ajouté.
- ×2 : Cours TTWO à l’échéance : $307.71
- ×3 : Cours TTWO à l’échéance : $311.57
- ×5 : Cours TTWO à l’échéance : $319.29

### P&L aux objectifs

| Spot | Catalyseur IV down | Catalyseur IV stable | Catalyseur IV up | Échéance |
|---:|---:|---:|---:|---:|
| $220.00 | $-650.76 / €-569.09 | $-418.15 / €-365.67 | $-64.22 / €-56.16 | $-771.40 / €-674.60 |
| $250.00 | $-58.32 / €-51.01 | $529.09 / €462.69 | $1,202.67 / €1,051.75 | $-771.40 / €-674.60 |
| $280.00 | $1,626.61 / €1,422.48 | $2,529.25 / €2,211.85 | $3,443.85 / €3,011.67 | $-771.40 / €-674.60 |
| $300.00 | $3,557.75 / €3,111.28 | $4,533.41 / €3,964.51 | $5,507.89 / €4,816.69 | $-771.40 / €-674.60 |
| $330.00 | $7,600.64 / €6,646.82 | $8,464.31 / €7,402.10 | $9,377.07 / €8,200.32 | $5,228.60 / €4,572.45 |
| $360.00 | $12,645.40 / €11,058.50 | $13,259.09 / €11,595.18 | $13,995.92 / €12,239.55 | $11,228.60 / €9,819.50 |

P&L espéré conditionnel aux probabilités utilisateur : `$5,131.80` / `€4,487.80` ; probabilité de résultat positif : `90.00%`.

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
- Perte max : `$680.70` / `€595.28` ; `59.53%` du budget
- Gain maximal contractuel : `Illimité théorique`
- Meilleur gain parmi les scénarios modélisés : `$9,362.07` / `€8,187.21`
- Ratio gain/perte contractuel : `non borné` ; ratio modélisé : `13.7536`
- Break-even : `[286.807]`
- Tu perds tout ou partie de la mise si TTWO termine sous $286.81; à ou sous $280.00, la prime peut être perdue intégralement.
- Tu gagnes à l’échéance si TTWO dépasse $286.81; le gain contractuel reste théoriquement illimité.
- Greeks nets : delta `32.961`, gamma `0.535`, theta `-5.783`, vega `67.238`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00280000` | 280 | $6.20 | $6.80 | $6.50 | 100 |

### Seuils de performance à l'échéance

> ×2 la mise = valeur finale égale à deux fois le coût total initial, soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie n'est ajouté.
- ×2 : Cours TTWO à l’échéance : $293.61
- ×3 : Cours TTWO à l’échéance : $300.42
- ×5 : Cours TTWO à l’échéance : $314.04

### P&L aux objectifs

| Spot | Catalyseur IV down | Catalyseur IV stable | Catalyseur IV up | Échéance |
|---:|---:|---:|---:|---:|
| $220.00 | $-525.26 / €-459.35 | $-335.76 / €-293.62 | $-92.70 / €-81.06 | $-680.70 / €-595.28 |
| $250.00 | $42.46 / €37.13 | $414.73 / €362.68 | $804.87 / €703.86 | $-680.70 / €-595.28 |
| $280.00 | $1,339.57 / €1,171.46 | $1,794.88 / €1,569.64 | $2,249.63 / €1,967.32 | $-680.70 / €-595.28 |
| $300.00 | $2,629.69 / €2,299.69 | $3,057.75 / €2,674.02 | $3,499.22 / €3,060.10 | $1,319.30 / €1,153.74 |
| $330.00 | $5,047.81 / €4,414.35 | $5,360.73 / €4,688.00 | $5,724.53 / €5,006.15 | $4,319.30 / €3,777.26 |
| $360.00 | $7,811.29 / €6,831.04 | $7,998.69 / €6,994.92 | $8,260.27 / €7,223.67 | $7,319.30 / €6,400.79 |

P&L espéré conditionnel aux probabilités utilisateur : `$3,271.11` / `€2,860.61` ; probabilité de résultat positif : `90.00%`.

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
- Perte max : `$881.40` / `€770.79` ; `77.08%` du budget
- Gain maximal contractuel : `1118.6`
- Meilleur gain parmi les scénarios modélisés : `$1,118.60` / `€978.22`
- Ratio gain/perte contractuel : `1.26911731` ; ratio modélisé : `1.2691`
- Break-even : `[238.814]`
- Tu perds tout ou partie de la mise si TTWO termine sous $238.81; à ou sous $230.00, la perte maximale est atteinte.
- Tu gagnes à l’échéance au-dessus de $238.81; le gain est plafonné à partir de $250.00.
- Greeks nets : delta `11.696`, gamma `-0.002`, theta `-0.070`, vega `-1.844`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00230000` | 230 | $21.60 | $22.40 | $22.00 | 100 |
| VENDRE | 1 | `TTWO270319C00250000` | 250 | $13.60 | $14.40 | $14.00 | 100 |

### Seuils de performance à l'échéance

> ×2 la mise = valeur finale égale à deux fois le coût total initial, soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie n'est ajouté.
- ×2 : Cours TTWO à l’échéance : $247.63
- ×3 : Impossible — gain plafonné par la structure.
- ×5 : Impossible — gain plafonné par la structure.

### P&L aux objectifs

| Spot | Catalyseur IV down | Catalyseur IV stable | Catalyseur IV up | Échéance |
|---:|---:|---:|---:|---:|
| $220.00 | $-294.46 / €-257.51 | $-246.44 / €-215.51 | $-217.96 / €-190.61 | $-881.40 / €-770.79 |
| $250.00 | $304.90 / €266.64 | $238.71 / €208.75 | $188.47 / €164.82 | $1,118.60 / €978.22 |
| $280.00 | $757.53 / €662.47 | $634.09 / €554.52 | $534.21 / €467.17 | $1,118.60 / €978.22 |
| $300.00 | $927.84 / €811.40 | $813.37 / €711.29 | $707.94 / €619.10 | $1,118.60 / €978.22 |
| $330.00 | $1,045.13 / €913.98 | $972.67 / €850.60 | $886.10 / €774.90 | $1,118.60 / €978.22 |
| $360.00 | $1,081.59 / €945.86 | $1,046.18 / €914.90 | $988.43 / €864.39 | $1,118.60 / €978.22 |

P&L espéré conditionnel aux probabilités utilisateur : `$652.11` / `€570.28` ; probabilité de résultat positif : `90.00%`.

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
- Perte max : `$1,140.70` / `€997.55` ; `99.76%` du budget
- Gain maximal contractuel : `Illimité théorique`
- Meilleur gain parmi les scénarios modélisés : `$10,327.00` / `€9,031.05`
- Ratio gain/perte contractuel : `non borné` ; ratio modélisé : `9.0532`
- Break-even : `[271.407]`
- Tu perds tout ou partie de la mise si TTWO termine sous $271.41; à ou sous $260.00, la prime peut être perdue intégralement.
- Tu gagnes à l’échéance si TTWO dépasse $271.41; le gain contractuel reste théoriquement illimité.
- Greeks nets : delta `42.098`, gamma `0.608`, theta `-6.223`, vega `72.669`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00260000` | 260 | $10.60 | $11.40 | $11.00 | 100 |

### Seuils de performance à l'échéance

> ×2 la mise = valeur finale égale à deux fois le coût total initial, soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie n'est ajouté.
- ×2 : Cours TTWO à l’échéance : $282.81
- ×3 : Cours TTWO à l’échéance : $294.22
- ×5 : Cours TTWO à l’échéance : $317.04

### P&L aux objectifs

| Spot | Catalyseur IV down | Catalyseur IV stable | Catalyseur IV up | Échéance |
|---:|---:|---:|---:|---:|
| $220.00 | $-797.63 / €-697.54 | $-534.91 / €-467.79 | $-238.74 / €-208.78 | $-1,140.70 / €-997.55 |
| $250.00 | $171.68 / €150.14 | $571.60 / €499.87 | $972.13 / €850.14 | $-1,140.70 / €-997.55 |
| $280.00 | $1,994.39 / €1,744.11 | $2,374.56 / €2,076.57 | $2,769.20 / €2,421.69 | $859.30 / €751.46 |
| $300.00 | $3,591.66 / €3,140.94 | $3,895.25 / €3,406.43 | $4,238.75 / €3,706.82 | $2,859.30 / €2,500.48 |
| $330.00 | $6,321.15 / €5,527.89 | $6,496.66 / €5,681.39 | $6,738.26 / €5,892.66 | $5,859.30 / €5,124.01 |
| $360.00 | $9,236.95 / €8,077.79 | $9,321.38 / €8,151.62 | $9,470.74 / €8,282.24 | $8,859.30 / €7,747.53 |

P&L espéré conditionnel aux probabilités utilisateur : `$3,983.75` / `€3,483.82` ; probabilité de résultat positif : `90.00%`.

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
- Perte max : `$1,001.40` / `€875.73` ; `87.57%` du budget
- Gain maximal contractuel : `998.6`
- Meilleur gain parmi les scénarios modélisés : `$998.60` / `€873.28`
- Ratio gain/perte contractuel : `0.99720391` ; ratio modélisé : `0.9972`
- Break-even : `[230.014]`
- Tu perds tout ou partie de la mise si TTWO termine sous $230.01; à ou sous $220.00, la perte maximale est atteinte.
- Tu gagnes à l’échéance au-dessus de $230.01; le gain est plafonné à partir de $240.00.
- Greeks nets : delta `8.382`, gamma `-0.046`, theta `0.138`, vega `-7.730`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO271217C00220000` | 220 | $41.50 | $42.50 | $42.00 | 100 |
| VENDRE | 1 | `TTWO271217C00240000` | 240 | $32.50 | $33.50 | $33.00 | 100 |

### Seuils de performance à l'échéance

> ×2 la mise = valeur finale égale à deux fois le coût total initial, soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie n'est ajouté.
- ×2 : Impossible — gain plafonné par la structure.
- ×3 : Impossible — gain plafonné par la structure.
- ×5 : Impossible — gain plafonné par la structure.

### P&L aux objectifs

| Spot | Catalyseur IV down | Catalyseur IV stable | Catalyseur IV up | Échéance |
|---:|---:|---:|---:|---:|
| $220.00 | $-149.72 / €-130.93 | $-174.99 / €-153.03 | $-200.28 / €-175.14 | $-1,001.40 / €-875.73 |
| $250.00 | $201.15 / €175.91 | $108.22 / €94.64 | $36.07 / €31.54 | $998.60 / €873.28 |
| $280.00 | $473.62 / €414.19 | $343.72 / €300.59 | $240.14 / €210.00 | $998.60 / €873.28 |
| $300.00 | $605.94 / €529.90 | $469.79 / €410.83 | $355.33 / €310.74 | $998.60 / €873.28 |
| $330.00 | $741.43 / €648.39 | $615.44 / €538.21 | $497.57 / €435.13 | $998.60 / €873.28 |
| $360.00 | $821.41 / €718.33 | $717.57 / €627.52 | $607.14 / €530.95 | $998.60 / €873.28 |

P&L espéré conditionnel aux probabilités utilisateur : `$392.16` / `€342.95` ; probabilité de résultat positif : `90.00%`.

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
- Perte max : `$821.40` / `€718.32` ; `71.83%` du budget
- Gain maximal contractuel : `2178.6`
- Meilleur gain parmi les scénarios modélisés : `$2,178.60` / `€1,905.20`
- Ratio gain/perte contractuel : `2.65230095` ; ratio modélisé : `2.6523`
- Break-even : `[258.214]`
- Tu perds tout ou partie de la mise si TTWO termine sous $258.21; à ou sous $250.00, la perte maximale est atteinte.
- Tu gagnes à l’échéance au-dessus de $258.21; le gain est plafonné à partir de $280.00.
- Greeks nets : delta `14.627`, gamma `0.077`, theta `-0.641`, vega `6.768`

### Jambes et cotations

| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |
|---|---:|---|---:|---:|---:|---:|---:|
| ACHETER | 1 | `TTWO270319C00250000` | 250 | $13.60 | $14.40 | $14.00 | 100 |
| VENDRE | 1 | `TTWO270319C00280000` | 280 | $6.20 | $6.80 | $6.50 | 100 |

### Seuils de performance à l'échéance

> ×2 la mise = valeur finale égale à deux fois le coût total initial, soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie n'est ajouté.
- ×2 : Cours TTWO à l’échéance : $266.43
- ×3 : Cours TTWO à l’échéance : $274.64
- ×5 : Impossible — gain plafonné par la structure.

### P&L aux objectifs

| Spot | Catalyseur IV down | Catalyseur IV stable | Catalyseur IV up | Échéance |
|---:|---:|---:|---:|---:|
| $220.00 | $-456.02 / €-398.80 | $-342.35 / €-299.39 | $-261.60 / €-228.77 | $-821.40 / €-718.32 |
| $250.00 | $214.07 / €187.20 | $237.07 / €207.32 | $241.78 / €211.44 | $-821.40 / €-718.32 |
| $280.00 | $1,004.63 / €878.56 | $876.80 / €766.77 | $776.95 / €679.45 | $2,178.60 / €1,905.20 |
| $300.00 | $1,434.37 / €1,254.37 | $1,247.10 / €1,090.60 | $1,097.85 / €960.08 | $2,178.60 / €1,905.20 |
| $330.00 | $1,845.94 / €1,614.29 | $1,657.63 / €1,449.61 | $1,484.38 / €1,298.10 | $2,178.60 / €1,905.20 |
| $360.00 | $2,036.11 / €1,780.60 | $1,903.25 / €1,664.41 | $1,751.83 / €1,531.99 | $2,178.60 / €1,905.20 |

P&L espéré conditionnel aux probabilités utilisateur : `$1,043.12` / `€912.22` ; probabilité de résultat positif : `90.00%`.

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
