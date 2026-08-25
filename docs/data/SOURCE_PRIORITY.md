# Priorité et résolution des sources

Ordre général :

1. source officielle primaire ;
2. donnée de marché autorisée ;
3. fournisseur commercial réputé ;
4. valeur dérivée localement avec lignage ;
5. estimation explicite ;
6. hypothèse utilisateur explicite.

L'accès technique n'accorde pas automatiquement un droit d'usage, de conservation ou
de redistribution. Les données Market Data du cache restent privées : la politique du
fournisseur interdit la redistribution des données de ses offres self-service. Les
fichiers bruts ne sont donc jamais ajoutés au dépôt. Les conditions applicables au
compte Alpaca doivent être confirmées séparément avant d'élever son extrait au statut
`authorized_internal`.

Sources techniques vérifiées le 8 août 2026 :

- [Market Data — option chain historique](https://www.marketdata.app/docs/api/options/chain/) ;
- [Market Data — politique de redistribution](https://www.marketdata.app/docs/account/data-policies/data-redistribution/) ;
- [Alpaca — historique options et différence indicative/OPRA](https://docs.alpaca.markets/us/docs/historical-option-data) ;
- [Alpaca — historique de marché et abonnements](https://docs.alpaca.markets/us/docs/about-market-data-api) ;
- [SEC — API EDGAR](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

En cas de divergence, aucune valeur n'écrase silencieusement l'autre. Les observations
sont conservées avec `provider`, `source_id`, timestamps, unité et hash ; le conflit
est inscrit au manifeste. Une règle de résolution ne peut retenir une valeur qu'en
fonction de critères pré-enregistrés (autorité, disponibilité au cutoff, couverture,
qualité), jamais parce qu'elle améliore le résultat.
