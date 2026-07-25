# Limites connues - TTWO options engine V9

- Le budget V9 est une limite de risque modelise, pas une garantie de debit IBKR. Le combo live,
  le taux de change, les commissions, le slippage, le multiplicateur et le pouvoir d'achat du
  compte peuvent modifier le montant reel.
- Le plan `single_long` et les trois poches de `staged_three` sont des hypotheses de recherche.
  Une poche sans contrats conformes reste vide ; le moteur ne relache pas les filtres de spread ou
  d'open interest pour consommer artificiellement le budget.
- Le run V9 utilise le taux BCE du 2026-07-17, `1 EUR = 1.1435 USD`. Ce taux est une reference de
  conversion, pas le taux d'execution du courtier.
- La chaine actuelle s'arrete au 2027-03-19, soit 246 DTE au 2026-07-16. Le moteur ne peut donc pas
  construire aujourd'hui un trade a 365 DTE exact avec les contrats fournis.
- Le plan de sortie longue V9 teste TP +80 %, stop -50 % ou sortie apres 30 seances. Il ne mesure
  pas une detention passive jusqu'a l'echeance et son payoff a 246 jours ne doit pas etre confondu
  avec le P&L realise apres environ six semaines.

- Le catalogue V8 contient 21 architectures, mais seules 13 structures optionnelles autonomes a
  risque contractuellement borne sont backtestees. `catalog_only` ne signifie pas valide et
  `risk_disabled` ne peut pas etre active depuis le moteur.
- Un profit target ou stop est detecte a la premiere cote EOD complete selon la frequence declaree.
  Il ne prouve ni franchissement intraday, ni fill au seuil, ni execution combo simultanee.
- Le capital a risque des structures de credit repose sur le payoff terminal borne. Une liquidation
  anticipee jambe par jambe sur des spreads tres larges peut produire une marque executable pire que
  cette perte contractuelle ; ces anomalies restent visibles dans les stress et veto.
- Calendar et diagonal ferment toutes les jambes avant l'echeance courte, mais ne rejouent pas
  l'assignment americain, le roll, la term-structure intraday ou les combo fills.
- Les recettes LEAPS a 365 DTE choisissent l'echeance cotee la plus proche. Au scan du 2026-07-16,
  la plus lointaine disponible dans la chaine Alpaca fournie expirait le 2027-03-19, soit moins de
  365 jours. Le nom de recette exprime une cible, pas une maturite garantie.
- Le holdout V8 est `reused_exploratory` car les resultats V7 ont deja ete inspectes. Aucun statut
  `eligible` ne peut etre produit sans nouvelle periode fraiche verrouillee avant analyse.
- Le plan MarketData.app a refuse la seance du 2026-07-17 comme non totalement cloturee et a
  declare le 2026-07-16 comme derniere seance accessible. Le dashboard utilise cette date reelle.

- Les credentials restent hors depot. Des datasets reels Alpaca et MarketData.app ont ete produits
  localement le 2026-07-19, mais ils sont ignores par Git et ne constituent pas une validation de
  strategie.
- L'historique options Alpaca commence en fevrier 2024.
- Alpaca expose les bars/trades options historiques mais pas un endpoint de quotes/NBBO options
  historiques dans le SDK officiel utilise. Le close de barre reste un proxy d'execution.
- Le feed options `indicative` modifie les quotes et derive les trades ; OPRA requiert un abonnement.
- Le feed actions IEX ne couvre qu'IEX ; SIP requiert l'entitlement correspondant.
- MarketData.app Free Forever est limite a un an d'historique, 100 credits par jour, des donnees
  retardees de 24 heures et un usage personnel/non commercial. Le cache local doit respecter les
  conditions de conservation et de suppression du fournisseur.
- Les chaines MarketData.app apportent bid/ask EOD, tailles, volume et open interest, mais pas un
  replay NBBO intraday. Elles restent `screen_grade` sous `historical_eod_bid_ask`.
- Les IV/Greeks historiques MarketData.app etaient nuls dans les reponses publiques testees. Leur
  recalcul QuantLib depend du midpoint, du taux, des dividendes et de la grille numerique declares.
- MarketData.app ne remplace pas les contract details broker/OCC : multiplicateur et deliverable
  restent des entrees explicites, sans supposition automatique a 100.
- Le pricing americain QuantLib reste sensible aux hypotheses de taux, volatilite, dividendes et
  convergence de grille ; il ne reproduit pas une quote executable.
- L'exercice anticipe est price, mais assignment et pin risk restent des niveaux heuristiques sans
  probabilite historique.
- La surface IV V2 est statique et synthetique ; elle ne controle pas encore les arbitrages de
  calendrier/convexite et ne modelise pas un skew dynamique.
- Merton et Heston sont implementes et seedes, mais leurs parametres du fixture sont illustratifs.
- Le schema Heston full-truncation Euler porte une erreur de discretisation et n'est pas une
  calibration d'options Heston.
- L'attribution est un waterfall de repricing dont le resultat depend de l'ordre des facteurs ; le
  residuel est conserve.
- La calibration close-to-close fournit RV et une classification de jumps heuristique. Elle refuse
  volontairement Heston sans historique de surface/variance.
- Le backtest V7 utilise une seule annee accessible par le plan MarketData.app teste. Les variantes
  les mieux observees ont 28 observations train, 11 test et 8 holdout ; les horizons plus longs en
  ont beaucoup moins. Ce volume ne permet pas de couvrir plusieurs cycles de marche.
- Les observations d'une variante sont non chevauchantes et les splits ont un embargo, mais les
  variantes reutilisent certaines dates et certains contrats. Les 58 selections test gagnantes du
  dashboard ne sont donc pas 58 paris economiquement independants.
- La precision affichee est le taux de P&L net positif observe, avec intervalle Wilson a 95 %. Ce
  n'est ni une probabilite predictive calibree, ni une probabilite de succes du prochain trade.
- Les intervalles bootstrap de moyenne/mediane restent fragiles sous dependance temporelle, petits
  echantillons, changements de regime et selection de la meilleure variante.
- Le Deflated Sharpe est une approximation de diagnostic au pas de detention observe ; il ne
  remplace pas un test academique complet avec toutes les strategies essayees et leur covariance.
- Les rendements sont normalises par la prime/debit initial. Les courbes cumulatives sont additives
  a une unite de risque et ne representent pas un portefeuille taille, marge ou compose.
- La selection walk-forward utilise la chaine de signal precedente, mais les prix d'entree/sortie
  restent des bid/ask EOD et ne garantissent pas un fill intraday ou simultane sur un spread.
- Pas de combo quote broker, legging model, market impact ou slippage calibré.
- Frais, marge, borrow, permissions et taux sont fournis par fixture, pas vérifiés au broker.
- Pas de consensus, positionnement, short interest, données de portefeuille réel ou sizing réel.
- Les scénarios fondamentaux et probabilités de la fixture sont illustratifs.
- Le score est une comparaison de recherche à poids égaux ; il n'est ni calibre ni valide comme
  signal.
- Le run V7 du 2026-07-19 ne valide aucune variante. Le meilleur profil suffisamment observe a un
  taux de gain test de 54.5 % sur 11 cas, mais un P&L test total negatif, un holdout negatif, un
  drawdown excessif et une probabilite Deflated Sharpe tres inferieure au seuil.
- La couverture documentaire TTWO reste `draft_to_validate` pour toute décision de marché.
- Aucun ordre, recommandation, activation de risque non borné ou statut live n'est disponible.

Avant une éventuelle validation paper, il faut des donnees source-backed actuelles, un audit du
contrat, des scenarios evenementiels valides, un modele de couts/marge broker et un vrai backtest
hors echantillon. Une couche d'execution reelle resterait un projet separe avec
revue sécurité, conformité, observabilité, limites et kill switch.
