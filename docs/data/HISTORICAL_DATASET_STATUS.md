# État du dataset historique TTWO — phase C

Le dataset financier pré-OPRA reste `BLOCKED_BY_DATA`. Le dépôt contient maintenant
un contrat point-in-time strict, un audit local reproductible et un manifeste agrégé,
mais aucune donnée brute sous licence.

Inventaire privé constaté le 8 août 2026 :

- 616 clôtures ajustées TTWO (Alpaca/IEX), du 1er février 2024 au 17 juillet 2026 ;
- 1 998 enveloppes Market Data dont les hashes sont valides ;
- 46 413 lignes d'options, 3 036 symboles OCC, 250 dates de requête, calls et puts ;
- bid, ask, open interest, volume, sous-jacent et timestamps présents ;
- IV et Greeks fournisseur absents sur toutes les lignes ;
- macro, FX, calendrier, corporate actions, dividendes et événements officiels non
  intégrés au dataset gouverné.

Le statut `point_in_time=partial` ne signifie pas « validé ». Les timestamps des
extraits présents sont contrôlables, mais la couverture est incomplète et la licence
Alpaca reste `to_review`. Le fichier
`reports/pre_opra/data_inventory_2026-08-08.json` est un manifeste de métadonnées et
de statistiques agrégées ; il ne permet pas de reconstruire les observations brutes.

Une observation critique manquante n'est jamais imputée silencieusement. Une donnée
publiée ou disponible après le `decision_cutoff` est exclue et provoque un statut
fail-closed. Une valeur dérivée doit référencer ses observations sources ; une valeur
imputée exige une justification et reste visible comme telle.
