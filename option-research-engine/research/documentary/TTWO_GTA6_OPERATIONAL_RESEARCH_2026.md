# TTWO / GTA VI — research opérationnelle avant build

Date : 2026-07-08
Statut : `draft_to_validate`
Objet : compléter les données et règles nécessaires pour construire un futur outil de sélection de
structure optionnelle autour de Take-Two Interactive (`TTWO`) et du catalyseur `Grand Theft Auto VI`.

Ce document n'est pas une recommandation de trade. Il transforme le corpus documentaire en cahier des
charges opérationnel : quelles données collecter, quels contrôles appliquer, quelles stratégies
comparer, et quels points doivent bloquer le scoring tant que les données live ne sont pas disponibles.

## Réponse courte

On a assez de connaissance pour construire le **moteur read-only de recherche**.

On n'a pas encore assez pour décider d'un “trade parfait”, car ce trade dépendra de données live au
moment de l'analyse :

- prix TTWO ;
- option chain complète ;
- bid/ask par jambe ;
- IV par strike et échéance ;
- realized volatility récente ;
- open interest et volume ;
- marge IBKR ;
- commissions et slippage ;
- événements exacts entre entrée et expiration.

Le futur outil doit donc produire une **comparaison contrainte** :

```text
no-trade vs action TTWO vs call/put sec vs vertical spread vs calendar/diagonal vs structure bornée
```

Il ne doit jamais sélectionner une structure simplement parce qu'elle “ressemble” à une bonne idée de
livre.

## Contexte TTWO / GTA VI vérifié

### Faits actuels

- Take-Two Interactive est cotée au NASDAQ sous `TTWO`.
- Rockstar Games est un label de Take-Two.
- Le lancement annoncé de `Grand Theft Auto VI` est le **19 novembre 2026** sur PlayStation 5 et Xbox
  Series X|S.
- Les précommandes ont été annoncées comme ouvertes à partir du **25 juin 2026**.
- Take-Two a publié ses résultats FY2026 le **21 mai 2026** :
  - net bookings FY2026 : **6,72 Md$** ;
  - outlook initial FY2027 : **8,0 à 8,2 Md$** ;
  - le management lie explicitement le niveau record attendu de FY2027 au lancement de GTA VI.
- Snapshot marché utilisé pendant cette recherche : `TTWO` autour de **257,79 $** le
  **2026-07-08 09:56 UTC**. Ce prix doit être rafraîchi par l'outil, pas recopié comme input durable.

### Implication pour le trade

Le catalyseur GTA VI n'est pas un simple événement “earnings”. C'est une chaîne d'événements :

1. précommandes ;
2. communication marketing / trailers ;
3. résultats trimestriels et guidance ;
4. risque de délai ;
5. release ;
6. premières métriques commerciales ;
7. révisions analystes ;
8. potentiel `sell-the-news` ;
9. effet sur FY2027 puis FY2028.

Le moteur doit donc raisonner par **date et horizon**, pas seulement par direction.

## Hypothèse de travail

L'idée initiale peut être formulée ainsi :

```text
TTWO pourrait bénéficier d'un catalyseur majeur avec GTA VI, mais une partie de ce catalyseur est déjà
probablement intégrée dans le prix de l'action et dans les volatilités implicites. La bonne structure
optionnelle dépend donc du rapport entre :

- upside fondamental encore non pricé ;
- probabilité et timing du catalyseur ;
- coût de l'optionnalité ;
- liquidité ;
- risque de délai / IV crush / gap ;
- perte maximale acceptable.
```

Cette hypothèse reste `draft_to_validate`.

## Ce que le futur outil doit construire

### 1. Distribution prix / temps

But : estimer les chemins plausibles de TTWO jusqu'aux dates importantes.

Données minimales :

- prix live ;
- historiques journaliers et intraday ;
- realized volatility `10d`, `20d`, `30d`, `60d`, `90d`, `252d` ;
- distribution des gaps ;
- drawdowns historiques ;
- réaction historique aux earnings ;
- corrélation avec Nasdaq, SPY et panier gaming si disponible ;
- scénario fondamental : retard, lancement conforme, lancement supérieur aux attentes, sell-the-news.

Sorties :

- fourchette de prix par date clé ;
- probabilité par zone de prix ;
- expected move implicite par échéance optionnelle ;
- scénarios `bull`, `base`, `bear`, `delay`, `crash_gap`.

Statut si incomplet : `distribution_price_time_missing`.

### 2. IV actuelle vs historique

But : éviter de payer une option chère simplement parce que l'histoire est séduisante.

Données minimales :

- IV par expiration et strike ;
- IV ATM par échéance ;
- skew call/put ;
- term structure ;
- IV rank / percentile si historique disponible ;
- realized volatility comparable ;
- spread entre IV et RV ;
- IV autour des prochains événements.

Lecture :

- IV basse + catalyseur crédible : long option ou long spread peut être étudié.
- IV élevée + thèse directionnelle : vertical spread, stock ou structure financée peut être préférable.
- IV très élevée avant event : attention à l'IV crush même si la direction est correcte.

Statut si incomplet : `iv_surface_missing`.

### 3. Liquidité

But : bloquer les stratégies théoriquement belles mais inexécutables.

Données minimales par jambe :

- bid ;
- ask ;
- mid ;
- spread en dollars ;
- spread en % du mid ;
- volume ;
- open interest ;
- dernier trade et horodatage ;
- exchange ;
- taille disponible si accessible.

Veto possibles :

- bid/ask trop large ;
- open interest faible ;
- absence de bid sur jambe longue à la sortie ;
- multi-leg impossible à prix réaliste ;
- expiration longue trop illiquide.

Statut si incomplet : `liquidity_veto_or_unknown`.

### 4. Sizing

But : dimensionner par perte maximale et par scénario adverse, jamais par enthousiasme sur GTA VI.

Règles candidates :

- perte maximale par idée définie avant scoring ;
- stratégie à risque non borné interdite sans validation humaine ;
- taille réduite si événement binaire, délai possible ou bid/ask large ;
- pas de sizing Kelly sans backtest robuste ;
- réduire la taille si la sortie dépend d'une liquidité incertaine.

Statut si incomplet : `sizing_policy_missing`.

### 5. Invalidation

But : écrire avant l'entrée ce qui rend la thèse fausse ou moins bonne.

Exemples de règles :

- retard officiel de GTA VI ;
- changement négatif de guidance ;
- précommandes ou signaux de demande inférieurs aux attentes ;
- hausse d'IV rendant la structure trop chère avant entrée ;
- baisse d'IV ou du sous-jacent cassant la structure ;
- rupture d'un niveau de prix défini ;
- expiration devenue trop proche pour le scénario ;
- perte de liquidité.

Statut si incomplet : `invalidation_missing`.

### 6. Catalyseur

Dates à suivre :

- prochaines publications TTWO ;
- conférences et investor events ;
- date de lancement GTA VI : 2026-11-19 selon source officielle actuelle ;
- éventuels trailers / annonces Rockstar ;
- fenêtre de précommandes ;
- période de review / previews ;
- premières métriques de ventes ;
- résultats couvrant la période de lancement.

Le moteur doit stocker ces événements dans un `event_calendar` horodaté. Une stratégie dont
l'expiration tombe avant le catalyseur principal doit être explicitement justifiée.

Statut si incomplet : `event_calendar_missing`.

## Comparaison action vs option vs vertical spread

### Action TTWO

Avantages :

- pas de theta ;
- pas d'expiration ;
- exposition simple à la thèse GTA VI ;
- pas de bid/ask optionnel multi-jambes.

Limites :

- capital plus élevé ;
- downside intégral ;
- moins de convexité ;
- exposition au marché global et aux résultats hors GTA VI.

### Call sec

Avantages :

- convexité ;
- perte bornée à la prime ;
- utile si upside fort et timing suffisamment clair.

Limites :

- theta ;
- IV crush ;
- besoin d'avoir raison sur direction, amplitude et temps ;
- spread large sur longues échéances possible.

### Vertical call debit spread

Avantages :

- réduit le coût d'entrée ;
- définit la perte maximale ;
- moins sensible à payer une IV trop élevée que le call sec ;
- bon candidat si objectif de prix borné.

Limites :

- upside plafonné ;
- assignment possible sur jambe courte si equity américaine ;
- exécution multi-jambes ;
- pin risk proche du strike court.

### Règle de comparaison

Le moteur doit refuser de scorer un call sec sans afficher au minimum :

```text
stock equivalent exposure
call premium and breakeven
vertical spread alternative
max loss
required move
IV/RV context
liquidity score
exit plan
```

## Readiness par famille pour TTWO / GTA VI

| Famille | Utilité possible pour TTWO/GTA VI | Données bloquantes | Statut |
|---|---|---|---|
| Achat call/put directionnel | Expression directe d'une thèse haussière ou baissière liée à GTA VI. | IV live, distribution prix/temps, liquidité, expiration cohérente avec catalyseur. | `candidate_after_live_chain` |
| Bull/bear vertical spreads | Candidat central si direction claire mais IV chère ou perte à borner. | Bid/ask par jambe, net debit réaliste, assignment, marge, commissions. | `candidate_after_execution_check` |
| Calendar / diagonal | Utile si la term structure autour du lancement ou earnings est mal pricée. | Surface IV live, événement entre expirations, short-leg assignment, roll/close. | `to_review_with_event_calendar` |
| Butterfly / condor | Seulement si zone de prix cible explicite et liquidité suffisante. | Probabilité de finir dans la zone, pin risk, multi-leg slippage, OI. | `selective_only` |
| Ratio / backspread | Peut exprimer convexité, mais risque asymétrique et marge complexe. | Stress gap, risque non borné, permissions broker, validation humaine. | `human_validation_required` |
| Straddle / strangle | Long vol si expected move sous-estime GTA VI ; short vol très risqué. | IV/RV, IV crush, earnings, gap, hedge policy, marge. | `event_mode_required` |
| Gamma scalping | À réserver à paper/backtest avec données intraday. | Intraday, frais, hedge logs, latence, attribution P&L. | `paper_only` |
| Protective / collar | Pertinent seulement si portefeuille TTWO existant. | Position exacte, fiscalité, coût max, assignment, dividendes/borrow. | `requires_portfolio_context` |
| LEAPS | Possible substitut action si thèse longue GTA VI/FY2027. | Long-dated IV, bid/ask, delta drift, liquidité, plan de roll. | `candidate_after_long_chain` |
| Overlay value | Nécessaire pour relier GTA VI au prix de TTWO. | Filings actuels, reverse DCF, WACC, scénarios, probabilités. | `research_layer_required` |

## Données live à collecter par IBKR

### Contrat sous-jacent

- `conId` TTWO ;
- exchange ;
- currency ;
- trading hours ;
- corporate actions ;
- shortability / borrow si stratégie short stock ;
- positions existantes.

### Chaîne options

Pour chaque contrat :

- `conId` ;
- `localSymbol` ;
- expiration ;
- strike ;
- call/put ;
- style d'exercice ;
- multiplier ;
- deliverable ;
- tradingClass ;
- bid/ask/last ;
- bidSize/askSize si disponible ;
- volume ;
- open interest ;
- implied volatility ;
- delta/gamma/theta/vega/rho ;
- model price ;
- timestamp.

### Événements

- earnings ;
- ex-dividend si applicable ;
- corporate actions ;
- GTA VI release / précommandes / annonces Rockstar ;
- macro events si l'échéance est courte.

### Frais et contraintes

- commission par contrat ;
- exchange fees ;
- margin impact ;
- permissions options ;
- multi-leg order support ;
- régles d'exercice/assignment broker ;
- compte cash vs margin.

## Garde-fous spécifiques TTWO / GTA VI

### Aucun trade n'est `trade_ready` si :

- la date GTA VI n'est pas vérifiée dans le calendrier ;
- l'option expire avant le catalyseur sans justification ;
- le bid/ask n'est pas disponible ;
- le net debit/credit multi-leg n'est pas exécutable ;
- l'open interest est insuffisant ;
- la perte maximale n'est pas connue ;
- le scénario de retard n'est pas simulé ;
- l'IV crush n'est pas simulé ;
- la marge n'est pas connue ;
- la règle de sortie n'est pas écrite ;
- la validation humaine n'est pas explicite.

### Stratégies interdites par défaut

Ces stratégies doivent rester `blocked_by_policy` tant qu'il n'y a pas de validation humaine :

- naked short calls ;
- short straddle/strangle non couvert ;
- ratio spread avec risque non borné ;
- backspread mal borné ou financé par short options disproportionnées ;
- gamma scalping réel sans paper trading validé ;
- stratégie nécessitant short stock si borrow/shortability inconnus.

## Score minimal proposé

Le futur moteur peut produire un score seulement si les blocs suivants sont complets :

| Bloc | Question | Si manquant |
|---|---|---|
| `thesis_score` | Pourquoi TTWO devrait bouger, dans quel sens, à quelle date ? | `thesis_to_review` |
| `valuation_score` | Que semble déjà impliquer le prix actuel ? | `valuation_to_review` |
| `distribution_score` | Le move requis est-il plausible dans le temps restant ? | `distribution_missing` |
| `iv_score` | L'optionnalité est-elle chère ou bon marché vs histoire/RV ? | `iv_surface_missing` |
| `liquidity_score` | Peut-on entrer et sortir sans se faire manger par le spread ? | `liquidity_veto_or_unknown` |
| `execution_score` | Le prix net multi-leg est-il réaliste ? | `execution_unknown` |
| `risk_score` | Max loss, margin, gap, assignment, IV crush sont-ils traités ? | `risk_gate_failed` |
| `exit_score` | Close, roll, stop, take-profit et invalidation sont-ils écrits ? | `exit_plan_missing` |

## Structure du futur rapport généré par l'outil

Chaque idée TTWO doit sortir sous cette forme :

```text
1. Thèse immédiate
2. Source de la thèse
3. Date/horizon du catalyseur
4. Prix TTWO live
5. Distribution prix/temps
6. IV/RV et term structure
7. Structures comparées
8. Meilleure structure candidate
9. Pourquoi les autres sont rejetées
10. Max loss / max gain / breakeven / required move
11. Liquidité et prix exécutable
12. Assignment / dividend / margin / commissions
13. Plan d'entrée
14. Plan de sortie / roll / invalidation
15. Stress tests
16. Statut final : no_trade, research_candidate, paper_candidate, human_review_required
```

## Ce qu'il manque encore réellement

Le corpus documentaire est suffisant pour le design. Les manques restants ne sont plus des “pages de
livres”, mais des données de marché et de broker :

- option chain TTWO live ;
- IV historique de TTWO ;
- realized volatility calculée sur données propres ;
- bid/ask et OI par expiration autour de novembre 2026 et au-delà ;
- earnings calendar courant ;
- marge IBKR sur chaque structure ;
- commissions et fees exacts ;
- règles de shortability/borrow ;
- éventuelles options ajustées ;
- backtest/paper trading.

Conclusion : la prochaine étape de build doit être un **collecteur read-only IBKR** et non un moteur
d'ordre.

## Sources utilisées

- Take-Two Interactive, communiqué FY2026 / Q4 FY2026, 2026-05-21 :
  `https://www.take2games.com/ir/news/take-two-interactive-software-inc-reports-results-fourth-2`
- Take-Two Interactive / Rockstar Games, précommandes GTA VI, 2026-06-24 :
  `https://www.take2games.com/ir/news/rockstar-games-announces-pre-orders-grand-theft-auto-vi`
- Snapshot marché TTWO via outil finance, 2026-07-08 09:56 UTC.
- Corpus interne :
  - `STRATEGY_READINESS_MATRIX.md`
  - `CURRENTNESS_AUDIT_2026.md`
  - revues Natenberg, McMillan, Passarelli, Mauboussin.
