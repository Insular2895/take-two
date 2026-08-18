# Backtest walk-forward point-in-time

Le contrat `WalkForwardCase` impose :

- `decision_time <= entry_time < exit_time` ;
- calibration terminée strictement avant la décision ;
- donnée disponible au plus tard à la décision ;
- contrat, expiration et strike existants à cette date ;
- achats au ask, ventes au bid, commissions et slippage explicites ;
- quantités entières et oracle exclu du holdout.

Les splits `train`, `validation`, `test` et `holdout` sont distincts. Le holdout est
verrouillé et `final_holdout_used_for_tuning` vaut toujours `false`.

## Baselines obligatoires

`cash`, `underlying`, `long_call_atm`, `long_call_fixed_delta`,
`bull_call_spread_standard`, `random_admissible`, `oracle_hindsight`,
`model_candidate` et `NO_TRADE`.

L’oracle mesure le regret possible mais ne peut participer à un gate. Une baseline
absente est listée ; elle n’est pas simulée silencieusement.

## Commande

```bash
ttwo-options calibration evaluate \
  --walk-forward fixtures/v11/walk_forward.example.json
```

La fixture produit `FIXTURE_ONLY_NOT_VALIDATED`. Une preuve financière exige des
quotes historiques autorisées et réellement disponibles à chaque décision.
