# Mauboussin & Rappaport — *Expectations Investing* — revue documentaire

Date : 2026-07-06
Statut : `to_review`
Source : `B-MAUBOUSSIN-RAPPAPORT-2001` — édition 2001, PDF local complet.

## Réponse courte

Le livre est exploitable pour la partie **sélection du sous-jacent et thèse d'investissement** du
futur outil, mais il ne suffit pas à lui seul pour déclencher une stratégie options.

Son apport principal est de forcer le moteur à partir du prix de marché pour retrouver les attentes
déjà incluses dans le cours, puis à demander : “quel scénario différent du consensus justifie le
trade ?”

## Concepts utiles pour le projet

### 1. Reverse DCF / attentes implicites

Mauboussin et Rappaport recommandent de ne pas commencer par une prévision arbitraire. Le bon
réflexe est de partir du prix actuel et de remonter aux attentes implicites : croissance, marges,
investissement, coût du capital et durée de l'avantage concurrentiel.

Usage futur :

- éviter de choisir un call uniquement parce que l'IV semble attractive ;
- vérifier si le sous-jacent porte déjà des attentes très optimistes ou pessimistes ;
- détecter les dossiers où une surprise raisonnable peut déplacer fortement le prix.

### 2. Carte de création de valeur

Formule et structure contrôlées visuellement :

```text
Operating profit = Sales × Operating margin
Cash taxes = Operating profit × Cash tax rate
NOPAT = Operating profit - Cash taxes
Free cash flow = NOPAT - Investment
```

La valeur de l'entreprise vient ensuite de la somme actualisée des flux libres, du coût du capital,
de la période de prévision et de la valeur résiduelle.

Usage futur :

- relier les scénarios action à des drivers mesurables ;
- demander au moteur de stocker les hypothèses utilisées ;
- éviter les thèses vagues du type “la société est bonne”.

### 3. Valeur résiduelle et période de prévision implicite

Formules contrôlées :

```text
PV of perpetuity = Annual cash flow / Required rate of return
Perpetuity residual value = NOPAT / Cost of capital
Inflation-adjusted perpetuity = NOPAT × (1 + inflation) / (Cost of capital - inflation)
```

La période de prévision implicite mesure combien d'années de création de valeur le marché semble
déjà payer.

Usage futur :

- repérer les sous-jacents où le marché exige une exécution parfaite ;
- pondérer les calls longs/LEAPS par le risque de duration des attentes ;
- distinguer “bon business” et “bon prix”.

### 4. Scénarios et espérance de valeur

Le livre utilise une logique d'espérance :

```text
Expected value = Σ(probability × scenario value)
```

Usage futur :

- toute stratégie option doit être rattachée à au moins un scénario prix/temps/volatilité ;
- le moteur doit comparer le payoff net à une distribution de scénarios, pas à un seul objectif ;
- les probabilités restent `to_review` tant qu'elles ne viennent pas d'un protocole validé.

### 5. Signaux corporate

Le livre est utile pour interpréter :

- acquisitions : `value change = PV of synergies - acquisition premium` ;
- rachats d'actions : intéressants seulement si le titre est sous sa valeur attendue et si aucun
  meilleur usage du capital n'existe ;
- rémunération en actions : à traiter comme dilution/coût économique, avec règles comptables à jour.

## Ce qui est stable en 2026

- La logique DCF / NOPAT / FCF / coût du capital reste valide.
- Le raisonnement “prix → attentes implicites → scénario différenciant” reste central.
- Les scénarios probabilisés restent utiles pour relier valorisation et options.
- Les buybacks doivent toujours être jugés à partir de prix vs valeur, coût d'opportunité et dilution.

## Ce qui n'est plus à utiliser tel quel

- Les exemples de taux, primes de risque, multiples, fiscalité et sources de données datent de 2001.
- La comptabilité des stock-options a évolué : utiliser ASC 718 / SAB Topic 14, pas les discussions
  anciennes comme règle opérationnelle.
- Les rachats d'actions doivent intégrer le contexte réglementaire et fiscal actuel, notamment la
  taxe d'accise américaine sur certains buybacks.
- L'édition traitée est celle de 2001, pas la révision 2021.

## Règles candidates à conserver

- `R-VALUATION-001` — commencer par les attentes implicites du prix.
- `R-VALUATION-002` — traduire une thèse en drivers : croissance, marge, investissement, coût du
  capital, durée.
- `R-VALUATION-003` — comparer la valeur attendue pondérée à la valeur de marché.
- `R-CORP-001` — analyser M&A, buybacks et dilution comme changements d'espérance de valeur.

Ces règles restent `documentary_to_review`. Elles ne sont pas actives.

## Impact sur le futur outil

Le moteur options devra avoir une couche `valuation / thesis` avant la couche `option_chain` :

1. prix actuel et attentes implicites ;
2. scénario différenciant ;
3. catalyseur et horizon ;
4. probabilité / incertitude ;
5. traduction en distribution prix/temps/volatilité ;
6. seulement ensuite, choix de structure optionnelle.
