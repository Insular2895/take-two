# Changelog documentaire

## 2026-07-28 - V11 Probabilistic Strategy Intelligence

Statut : `implemented_research_only_calibration_required`

Ajouts :

- couche modulaire au-dessus du rapport V10.1, sans remplacement du moteur de
  construction ni du contrôle américain QuantLib ;
- hub de données unifié avec provenance, déduplication et ports read-only SEC
  EDGAR, FRED, Take-Two RSS, Google Trends alpha, calendrier de marché et
  IBKR/OPRA ;
- mises à jour bayésiennes auditées avec faits canoniques, contradictions et
  plafonds par famille de sources ;
- 4 régimes croisés avec GBM, volatilité locale Dupire, Heston et
  Heston-plus-sauts, sorties path-dependent et métriques de queue ;
- covariance dynamique 20/60/252 jours, fenêtres événement/régime, shrinkage
  et correction PSD, sans invention des facteurs manquants ;
- optimisation exacte en contrats entiers sous budget, perte maximale,
  liquidité et cap de contrats, avec réserve cash et `NO_TRADE` explicites ;
- stress coûts/adverse/rupture/CVaR, maintien du statut contaminé V7–V9 et
  interdiction de promotion sans holdout neuf ni paper trading ;
- dossiers de position et avis explicables `conserver`, `surveiller`,
  `réduire`, `sortir` ou `thèse invalidée` ;
- previews IBKR verrouillées `transmit=false`, `what_if=true`,
  `order_capability=forbidden` et rejet des adaptateurs capables d’ordonner.
- 119 tests, Ruff, mypy strict, `pip check`, build wheel et contrôles des
  artefacts JSON/HTML passent.
- README transformé en spécification mathématique et décisionnelle complète :
  payoff, coûts, Black-Scholes/QuantLib, Greeks, scénarios, classements, Bayes,
  Dupire, covariance, SDE/Itô, Monte-Carlo, robustesse, optimisation,
  stress/promotion, monitoring, paramètres, limites et frontières réellement
  connectées.

Reste à valider :

- priors, likelihoods, régimes, Heston, sauts et surface locale sur données
  point-in-time source-backed ;
- campagne IBKR/OPRA réelle avec droits, fraîcheur, `conId`, livrables, quotes
  combo, commissions, marge et support what-if ;
- facteurs de covariance alignés, walk-forward imbriqué, holdout intact et
  paper trading ;
- toute évolution éventuelle de la frontière d’exécution, qui reste hors
  périmètre et soumise à validation explicite.

## 2026-07-19 - Budget EUR et horizons V9

Statut : `source_backed_budget_screen_no_trade`

Ajouts :

- contrainte dure de risque en euros sur les selections actuelles et chaque cas historique ;
- taux EUR/USD date et trace, avec reference BCE `1 EUR = 1.1435 USD` au 2026-07-17 ;
- comparaison `single_long` EUR 1 000 et `staged_three` EUR 310/245/445 ;
- quatre recettes de vertical call avec horizons, profit targets, stops et sorties temps distincts ;
- premiere table du dashboard dediee au budget, aux poches disponibles, au ticket lisible, au
  scenario de gain, aux preuves et aux motifs de blocage ;
- 69 tests, dont un veto historique explicite pour toute structure au-dessus de la poche EUR.

Resultat source-backed :

- derniere chaine EOD utilisee : 2026-07-16 ; echeance maximale cotee : 2027-03-19, 246 DTE ;
- `single_long` construit C250/C270 mars 2027, debit indicatif USD 1 050 et risque modelise
  USD 1 058.60, soit environ EUR 926, mais reste bloque faute de couverture, test et holdout ;
- `staged_three` ne construit ni la poche court terme ni la poche moyen terme sous les filtres de
  liquidite ; la poche longue C310/C320 consomme environ EUR 445 mais son test/holdout est negatif ;
- aucun candidat eligible et classement final `no_trade`.

## 2026-07-19 - Panel d'architectures et opportunites V8

Statut : `source_backed_screen_grade_no_trade`

Ajouts :

- registre de 21 architectures avec frontiere `backtested/catalog_only/risk_disabled` ;
- 13 structures optionnelles actives : longs, verticals, straddle/strangle, butterflies, iron
  condor, calendar/diagonal et LEAPS ;
- jambes et ratios explicites, selection delta ou moneyness, ailes et echeances avant/arriere ;
- sorties EOD path-dependent avec profit target, stop, sortie temps et motif auditable ;
- capital a risque des credits, regime momentum/volatilite, IV/RV et holdout reutilise bloque ;
- dashboard recentre sur opportunites actuelles, gagnants historiques et bibliotheque complete ;
- tickets IBKR lisibles en francais avec action, call/put, quantite, strike, echeance, ordre
  limite debit/credit, prix par action, cout par lot et scenario de gain ;
- 68 tests, Ruff, mypy strict, `pip check` et HTML portable valide a 1440/390 pixels.

Resultat source-backed :

- scan actuel MarketData.app au 2026-07-16, derniere seance autorisee par le plan ;
- 4 panels, 17 variantes configurees, 81 fenetres, 977 requetes logiques dont 975 cache hits au
  rerun final ;
- 13 candidats actuels bloques, zero eligible et classement `no_trade` ;
- lead observe long call 150 DTE/delta 55 : test n=11, taux de gain 54.5 % [28.0 %, 78.7 %],
  mediane +3.02 %, drawdown 89.49 % ; holdout mediane -15.09 % ;
- recette put spot+10/365 DTE/TP80 : selection rejetee si le strike s'ecarte de plus de cinq
  points de la cible ; aucune observation conforme ni contrat actuel assez proche dans ce run ;
- holdout V8 `reused_exploratory`, donc aucune promotion possible sans periode fraiche.

## 2026-07-19 - Validation empirique et dashboard V7

Statut : `source_backed_screen_grade_no_trade`

Ajouts :

- generation d'observations non chevauchantes, embargo et splits train/test/holdout ;
- expiration dynamique proche de 90, 150 ou 270 DTE et taux Treasury officiel interpole ;
- 8 panels, 40 variantes, trois profils delta et horizons de 5, 10, 20 et 40 seances ;
- intervalles Wilson/bootstrap, volatilite/downside, profit factor, VaR/CVaR, drawdown, stress et
  approximation Deflated Sharpe ;
- audit de chaque trade et de chaque jambe aux cotes EOD executables ;
- dashboard HTML portable filtre par strategie, sample, resultat et regime, valide a 1440 et 390
  pixels ;
- 63 tests offline, Ruff, mypy strict, `pip check` et aucune capacite d'ordre.

Resultat source-backed :

- dernier snapshot de marche : seance du 2026-07-17 ;
- `no_trade` reste l'unique reference classee ; aucune variante ni candidat actuel n'est valide ;
- meilleur profil suffisamment observe : long call, 5 seances, cible 150 DTE, delta 65 ;
- test : 11 cas, 54.5 % gagnants avec intervalle 95 % de 28.0 % a 78.7 %, mediane +5.47 %,
  moyenne -1.46 %, P&L total -607.30 dollars, CVaR 95 % -33.37 % et drawdown 72.30 % ;
- holdout : 8 cas, mediane -14.79 %, P&L total -2,564.40 dollars et drawdown 86.91 % ;
- candidat actuel correspondant `TTWO261218C00220000` bloque par risque, Deflated Sharpe et
  echec holdout ; il s'agit d'un lead de recherche, pas d'un trade a executer.

## 2026-07-19 - Panel MarketData.app walk-forward V6

Statut : `source_backed_screen_grade_no_trade`

Ajouts :

- selection delta/liquidite sur une chaine de signal anterieure a l'entree ;
- comparaison `no_trade`, long call/put et verticals debit bornes ;
- 6 observations train et 4 test sur expiration janvier 2027 ;
- bid/ask EOD reel, commissions, slippage, cache et provenance ;
- veto avant classement sur couverture, rendement median, drawdown, pire perte et stabilite ;
- 58 tests offline et aucune capacite d'ordre.

Resultat initial :

- `no_trade` seule strategie eligible ;
- long call meilleur comparatif optionnel, mais bloque par drawdown test `49.11 %` et pire perte
  `-41.60 %` ;
- puts et verticals bloques par rendement test negatif et/ou risque excessif ;
- dix observations restent insuffisantes pour une conclusion statistique durable.

## 2026-07-19 - Premier run Alpaca reel read-only V5

Statut : `source_backed_screen_grade`

Resultats :

- connexion read-only Alpaca validee sur TTWO via le feed actions IEX ;
- chaine options indicative reelle de 378 contrats exportee ;
- contrat `TTWO270115C00260000` confirme avec quote, IV et Greeks ;
- premier backtest source-backed passe sur les bars options historiques ;
- call janvier 2027 strike 260 negatif sur l'unique cas train et l'unique cas test ;
- calibration actions source-backed sur 615 seances : GBM et Merton heuristique calibres, Heston
  refuse pour preuve insuffisante ;
- tous les artefacts restent `screen_grade`, sans capacite d'ordre.

Limites :

- une seule observation par split ne permet aucune conclusion de strategie ;
- les closes de bars options sont des proxies, pas du NBBO historique ;
- le panel multi-dates et multi-structures reste a construire ;
- MarketData.app reste necessaire pour le bid/ask EOD historique.

## 2026-07-19 - Integration MarketData.app read-only V4

Statut : `implemented_credentials_required`

Ajouts :

- client HTTP strictement pricing-only et token limite au header `Authorization` ;
- chaines options historiques EOD avec bid/ask, tailles, volume, open interest et sous-jacent ;
- cache local atomique, cle par requete, empreinte SHA-256 et rejet des donnees corrompues ;
- recalcul local IV/Greeks avec le moteur americain QuantLib et hypotheses explicites ;
- conversion des quotes EOD en backtests train/test anti-look-ahead `screen_grade` ;
- multiplicateur de contrat obligatoire, provenance et capacite d'ordre `forbidden` ;
- fixture TTWO, guide d'utilisation et 54 tests offline.

Validation externe :

- smoke test reel passe sur le contrat public AAPL `AAPL260814C00335000` au 2026-07-17 ;
- aucune donnee TTWO n'a ete telechargee faute de token MarketData.app personnel ;
- les droits de redistribution ou d'usage commercial restent hors du perimetre valide.

## 2026-07-19 - Integration Alpaca read-only V3

Statut : `implemented_credentials_required`

Ajouts :

- SDK officiel `alpaca-py` et credentials exclusivement par variables d'environnement ;
- verification read-only et export de chaine options actuelle avec IV/Greeks ;
- export de bars actions reels vers calibration source-backed ;
- export de bars options reels vers backtest train/test anti-look-ahead ;
- distinction obligatoire `historical_nbbo` / `option_bar_close_proxy` ;
- proxy de close maintenu `screen_grade`, slippage non nul obligatoire ;
- 46 tests offline et aucune importation du client d'ordres Alpaca.

Blocage actuel :

- cles Alpaca absentes de l'environnement local ; aucun appel reel ni artefact source-backed n'a
  donc ete produit dans cette passe.

## 2026-07-19 - Moteur TTWO options research V2

Statut : `implemented_v2_screen_grade_to_validate`

Ajouts :

- pricing americain QuantLib avec dividendes discrets et benchmark europeen ;
- Greeks coherents par differences finies, prime d'exercice anticipe et drapeaux assignment/pin ;
- surface IV strike/expiration avec diagnostics d'extrapolation ;
- simulations GBM, Merton jump diffusion et Heston full-truncation ;
- attribution P&L par repricing spot/temps/IV/taux/couts ;
- calibration RV/jumps avec refus explicite de Heston sur preuve insuffisante ;
- backtest train/test bid/ask avec frais et controle look-ahead ;
- fixtures/rapports V2 et 41 tests offline.

Reste a valider :

- historiques reels TTWO/chaines options et surfaces reconstructibles ;
- calibration Heston et jumps sur donnees source-backed ;
- backtest hors echantillon reel, robustesse des seuils et score ;
- quotes combo, couts, marge et revue humaine broker.

## 2026-07-18 — Moteur TTWO options research V1

Statut : `implemented_read_only_to_validate`

Ajouts :

- package Python typé et CLI offline ;
- contrats de données, fixtures, pricing, coûts, Greeks et scénarios ;
- génération `no-trade`, action, call, put et verticals bornés ;
- veto explicables avant scoring et evidence/provenance par candidat ;
- rapports JSON/Markdown, journal de décision et tests automatisés ;
- frontière broker qui interdit submit/modify/cancel.

Restent à valider :

- données live et chaîne TTWO ;
- hypothèses fondamentales, dates événementielles et scénarios ;
- seuils de liquidité, pondération du score et coûts broker ;
- modèle américain/dividendes/assignment et paper validation humaine.

## 2026-07-14 — Transcription PDF technique V2

Statut : `draft_to_validate`

Ajouts :

- spécification PDF -> JSON/Markdown/preuves en trois niveaux ;
- schémas JSON Gemini et sidecar canonique ;
- prompt Gemini de vérification visuelle stricte ;
- plan d'implémentation par phases et gates ;
- golden set et protocole de tests ;
- statuts documentaires distincts des statuts de règles ;
- protection Git des PDF, secrets et médias de preuve lourds.

Décisions encore ouvertes :

- choix des moteurs de rendu, OCR, layout, tableaux et formules ;
- choix/version du modèle Gemini et budget par livre ;
- seuils de confiance après mesure sur le golden set ;
- politique de conservation locale des preuves ;
- implémentation dans le dépôt logiciel `/Users/insular/transcripts` après validation du présent
  contrat.
