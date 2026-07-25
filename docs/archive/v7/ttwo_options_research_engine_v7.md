# Architecture - TTWO options accuracy engine V7

Statut : `source_backed_screen_grade_no_trade`

## Objectif

La V7 transforme le panel MarketData.app en protocole de recherche reproductible. Elle cherche a
mesurer une performance hors echantillon et son incertitude, puis bloque tout candidat qui ne
survit pas aux gates de couverture, rendement, risque, stabilite, multiple testing et holdout.
Elle reste strictement read-only.

## Flux

```text
sessions Alpaca + expirations actuelles + taux Treasury
        |
        v
observations non chevauchantes + embargo + train/test/holdout
        |
        v
chaine EOD de signal MarketData.app
        |
        +--> expiration cotee la plus proche du DTE cible
        +--> selection delta/liquidite sans information future
        |
        v
entree/sortie aux cotes executables + frais + slippage
        |
        v
KPI trade/variante + stress + intervalles + Deflated Sharpe
        |
        v
gates test puis holdout --> no_trade ou candidat bloque/eligible
        |
        v
rapport JSON/Markdown + dashboard portable
```

## Modules V7

- `accuracy.py` : generation des panels, splits purges, orchestration multi-horizon/DTE, scan de la
  chaine actuelle et synthese des variantes.
- `marketdata_panel.py` : selection de contrats, expiration dynamique, P&L par jambe, couts,
  stress, KPI par split et gates test/holdout.
- `research_statistics.py` : Wilson, bootstrap, volatilite, downside deviation, ratios, VaR/CVaR,
  skew/kurtosis et approximation Deflated Sharpe.
- `treasury_data.py` : telechargement/cache des courbes officielles et interpolation par maturite.
- `accuracy_dashboard.py` : datasets auditables, cartes KPI, graphiques, filtres, trades et jambes.
- `docs/sql/ttwo_v7_accuracy_dashboard_source.sql` : extraction documentaire de la source du
  dashboard canonique.

## Contrat de precision

La precision affichee est le taux de trades dont le P&L net est strictement positif. Elle est
toujours accompagnee d'un intervalle Wilson a 95 %. La moyenne et la mediane disposent
d'intervalles bootstrap deterministes. Aucun point estimate ne devient une probabilite predictive
calibree.

Une variante ne peut etre classee que si elle respecte les minima d'observations/couverture, le
rendement median, le drawdown, la pire perte, l'ecart train/test et le seuil Deflated Sharpe. Elle
doit ensuite passer un holdout reste hors du choix de variante. L'echec d'un seul gate maintient le
candidat en `blocked`; `no_trade` reste alors la reference.

## Premier run reel

- Fenetre fournisseur : 2025-07-21 au 2026-07-17.
- 8 panels, 40 variantes, 938 requetes logiques dont 511 servies par cache.
- Variante de recherche la mieux observee : long call, detention 5 seances, cible 150 DTE,
  profil delta 65/35.
- Test : 11 observations, taux de gain 54.5 % [28.0 %, 78.7 %], P&L total negatif, drawdown
  72.3 % et Deflated Sharpe sous le seuil.
- Holdout : 8 observations, mediane -14.79 % et drawdown 86.91 %.
- Decision mecanique : `no_trade`; zero variante validee et zero candidat actuel eligible.

## Dashboard

Le fichier `reports/ttwo_v7_accuracy_dashboard.html` est autonome. Il expose les variantes, la
distribution des rendements, la courbe du lead de recherche et les tables de candidats, trades et
jambes. Les filtres permettent de limiter par strategie, split, resultat gagnant/perdant et regime.
Sa validation automatique controle structure, sources, interactions et absence de debordement a
1440 et 390 pixels.

## Frontieres

1. Les cotes EOD ne sont pas un replay NBBO intraday ni une combo quote.
2. Un an d'historique ne traverse pas assez de regimes pour valider une strategie durable.
3. Les variantes reutilisent des dates : leurs trades ne sont pas tous independants.
4. Le bootstrap et le Deflated Sharpe restent des diagnostics approximatifs sur petit echantillon.
5. Les rendements sur prime ne representent ni sizing, marge, composition ni portefeuille reel.
6. Le candidat actuel est un objet d'audit; il ne peut autoriser ordre, taille ou recommandation.

Voir aussi [les limites connues](../known_limits.md) et
[la strategie de tests](../testing_strategy.md).
