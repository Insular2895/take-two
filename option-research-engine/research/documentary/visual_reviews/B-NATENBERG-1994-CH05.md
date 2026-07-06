# Revue visuelle — B-NATENBERG-1994 — Chapitre 5

Source : Sheldon Natenberg, *Option Volatility & Pricing*, édition 1994.

Chapitre : 5 — Using an Option's Theoretical Value.

Statut : `in_progress`

Date de revue : 2026-07-06.

Les images du livre ne sont pas versionnées. Cette fiche conserve les structures, hypothèses,
valeurs utiles et limites contrôlées visuellement. Les conclusions restent documentaires : aucune
règle n'est active pour trading ou exécution IBKR.

## Objectif du chapitre — pages 81–82

Le chapitre teste si un trader peut transformer une différence entre valeur théorique et prix de
marché en profit réel.

Hypothèses de départ :

- le modèle représente correctement la distribution des prix ;
- la volatilité future est connue ;
- futures juin : `101.35` ;
- taux : `8 %` ;
- temps à expiration juin : `10 semaines`.

Pour le June 100 call :

- volatilité connue supposée : `18.3 %` ;
- valeur théorique : `3.88` ;
- prix de marché : `3.25` ;
- edge brut : `0.63` par option.

### Impact projet

Le moteur ne doit pas s'arrêter à `théorique - prix`. Ce différentiel ne devient exploitable qu'à
travers une position maintenue, des hedges, des coûts et des contraintes de marché.

## Delta hedge initial — pages 82–84

Le chapitre rappelle trois conventions utiles :

- delta call entre `0` et `1.00`, souvent présenté entre `0` et `100` ;
- delta de l'option change avec les conditions de marché ;
- delta du sous-jacent = `1.00`, ou `100` selon la convention du livre.

Exemple :

```text
Acheter 100 June 100 calls, delta 57  => +5700 deltas
Vendre 57 June futures, delta 100     => -5700 deltas
Delta net                             => 0
```

Le hedge est présenté comme neutre à la direction seulement dans une petite plage.

### Recalcul après changement de marché

Une semaine plus tard :

- futures juin : `102.26` ;
- temps restant : `9 semaines` ;
- volatilité : `18.3 %` ;
- nouveau delta du call : `62`.

Position avant ajustement :

```text
Long 100 calls, delta 62   => +6200
Short 57 futures, delta 100 => -5700
Delta net                  => +500
```

Pour redevenir delta neutre, l'exemple vend `5` futures supplémentaires :

```text
Long 100 calls, delta 62   => +6200
Short 62 futures, delta 100 => -6200
Delta net                  => 0
```

### Procédure documentaire

Le chapitre résume la procédure :

1. acheter les options sous-évaluées ou vendre les options surévaluées ;
2. établir un hedge delta-neutre contre le sous-jacent ;
3. ajuster le hedge à intervalles réguliers pour rester delta-neutre.

### Impact projet

Le futur outil devra représenter un trade d'option comme une position dynamique :

- entrée option ;
- hedge initial ;
- recalcul des deltas ;
- politique d'ajustement ;
- coûts et cash flows.

## Figure 5-1 — hedge futures hebdomadaire, pages 85–86

La figure suit l'achat de calls et les ajustements futures hebdomadaires jusqu'à expiration.

### Données clés transcrites

| Semaine | Futures | Delta call | Delta position | Ajustement futures | Variation |
|---:|---:|---:|---:|---|---:|
| 0 | 101.35 | 57 | 0 | 0 | 0 |
| 1 | 102.26 | 62 | +500 | sell 5 | -51.87 |
| 2 | 99.07 | 46 | -1600 | buy 16 | +197.78 |
| 3 | 100.39 | 53 | +700 | sell 7 | -60.72 |
| 4 | 100.76 | 56 | +300 | sell 3 | -19.61 |
| 5 | 103.59 | 74 | +1800 | sell 18 | -158.48 |
| 6 | 99.26 | 45 | -2900 | buy 29 | +320.42 |
| 7 | 98.28 | 35 | -1000 | buy 10 | +44.10 |
| 8 | 99.98 | 50 | +1500 | sell 15 | -59.50 |
| 9 | 103.78 | 93 | +4300 | sell 43 | -190.00 |
| 10 | 102.54 | — | — | buy 36 | — |

Le texte explique que les ajustements forcent à vendre le sous-jacent quand le delta devient positif
et à acheter quand il devient négatif. Dans cet exemple, cela produit un gain d'ajustement.

### Résultat P&L

Composants :

| Composant | P&L |
|---|---:|
| Original hedge | -138.83 |
| Ajustements | +205.27 |
| Coût de portage option | -4.99 |
| Variation costs | +1.36 |
| Total | +62.81 |

Edge théorique initial :

```text
100 × (3.88 - 3.25) = +63.00
```

Le résultat réalisé `+62.81` est proche de l'edge théorique, sous les hypothèses du modèle.

### Impact projet

Le calcul d'edge doit être décomposé :

- option P&L ;
- hedge initial ;
- ajustements ;
- coûts de portage ;
- variation margin ;
- intérêts sur cash flows ;
- commissions/slippage à ajouter dans le monde réel.

## Marché frictionless vs réalité — pages 87–88

Le chapitre explicite les hypothèses frictionless :

1. achat/vente libre du sous-jacent ;
2. emprunt/prêt au même taux pour tous ;
3. coûts de transaction nuls ;
4. pas de taxes.

Il rappelle ensuite que les marchés réels violent ces hypothèses :

- marchés futures parfois locked limit ;
- taux d'emprunt/prêt différents ;
- coûts de transaction ;
- taxes ;
- coûts d'ajustements.

Le texte insiste : ajuster plus souvent réduit la malchance à court terme, mais augmente les coûts.
Les professionnels et les particuliers peuvent donc choisir des fréquences d'ajustement différentes.

### Impact projet

Le futur outil doit simuler plusieurs politiques de hedge :

- ajustement fréquent ;
- ajustement moins fréquent ;
- seuil de delta ;
- coûts par ajustement ;
- cash funding ;
- faisabilité de hedge selon la liquidité.

## IV, break-even volatility et sortie anticipée — pages 89–90

Le chapitre compare la volatilité future supposée et l'IV au prix d'entrée.

Exemple :

- call acheté à `3.25` ;
- IV au trade price : `14.6 %`;
- volatilité future supposée : `18.3 %`;
- valeur modèle à `18.3 %` : `3.88`;
- profit théorique attendu : `0.63` par option, soit `63.00` pour `100` options.

Si l'IV se réévalue immédiatement de `14.6 %` à `18.3 %`, le trader peut potentiellement clôturer
rapidement et capturer l'edge. Mais le texte indique que les réévaluations rapides d'IV sont
l'exception ; l'IV peut aussi bouger contre la position.

### Enseignement

- L'IV favorable permet parfois de réaliser plus vite l'edge.
- L'absence de réévaluation favorable oblige à maintenir et ajuster.
- Une perte mark-to-market initiale ne signifie pas nécessairement que le trade est mauvais si la
  thèse de volatilité reste valide.
- Plus la position est détenue longtemps, plus les erreurs d'inputs peuvent compter.

### Impact projet

Le moteur doit distinguer :

- edge de convergence immédiate d'IV ;
- edge réalisé par hedge dynamique jusqu'à expiration ;
- risque de mark-to-market défavorable ;
- horizon pendant lequel l'hypothèse reste défendable.

## Figure 5-2 — hedge stock options, pages 90–92

Deuxième exemple, sur action :

- stock price : `48 1/2` ;
- taux : `8 %` ;
- temps à expiration mars : `10 semaines` ;
- dividende attendu : `0.50` dans `40` jours ;
- volatilité future supposée : `32.4 %`;
- March 50 call : valeur théorique `2.17`, delta `46`;
- prix marché : `3.00`, IV `42.2 %`.

Comme le call est surévalué, l'exemple vend des calls et achète des actions :

```text
Sell 100 March 50 calls
Buy 4600 shares
```

### Résultat P&L

La figure et le texte décomposent :

| Composant | P&L |
|---|---:|
| Original hedge | +24,075 |
| Ajustements | -13,425 |
| Interest on hedge | -2,962.63 |
| Interest on adjustments | -814.34 |
| Dividends | +1,400 |
| Interest on dividends | +9.21 |
| Total | +8,282.24 |

Edge théorique :

```text
100 × (300 - 217) = +8,300
```

Le résultat réalisé est proche de l'edge théorique sous les hypothèses du modèle.

### Impact projet

Pour options sur actions, le moteur doit intégrer :

- dividendes ;
- coût de financement du stock ;
- intérêt sur ajustements ;
- cash flows d'achat/vente d'actions ;
- multiplicateur ;
- contraintes de short sale.

## Contraintes de short sale et réplication — page 93

Le texte signale qu'une position théorique peut être difficile à hedger si la vente à découvert est
contrainte. Historiquement, l'exemple discute l'uptick rule et le fait que certains courtiers ne
paient pas l'intégralité de l'intérêt sur le produit d'une vente short.

### Réplication dynamique

Conclusion du chapitre :

- avec les bonnes conditions de marché connues, les cash flows d'une option peuvent être répliqués
  par un processus d'ajustement dans le sous-jacent ;
- selon le modèle, à expiration, le cash flow total du hedge dynamique doit égaler la valeur de
  l'option ;
- si l'option est achetée sous sa valeur théorique ou vendue au-dessus, la différence entre prix et
  valeur théorique devient le profit attendu, sous hypothèses.

### Impact projet

Le futur outil doit tester si la réplication est réalisable :

- sous-jacent tradable ;
- short sale possible ;
- taux de financement réaliste ;
- coût d'ajustement ;
- taxes et contraintes de compte ;
- liquidité suffisante pendant la vie du trade.

## Conclusions provisoires pour Take Two

1. Le theoretical edge est une promesse conditionnelle, pas un profit garanti.
2. Une option mal pricée doit être évaluée avec son hedge et ses ajustements.
3. La neutralité delta est locale et doit être recalculée.
4. La fréquence de hedge change le compromis malchance/costs.
5. Les coûts de financement, variation margin, dividendes et taxes peuvent manger l'edge.
6. Une réévaluation favorable d'IV peut permettre une sortie anticipée, mais n'est pas garantie.
7. Une perte mark-to-market n'invalide pas automatiquement une thèse si les hypothèses restent
   cohérentes.
8. Une stratégie non hedgeable ou trop coûteuse à ajuster ne doit pas être considérée comme
   exploitable.
9. Le futur script IBKR doit simuler le trade comme une trajectoire de cash flows, pas comme un
   simple écart `fair value - price`.

## Prochaine source attendue

Passarelli, chapitre 13 — `Trading Realized Volatility` :

- gamma scalping ;
- realised volatility vs implied volatility ;
- P&L des hedges ;
- relation long gamma, theta et coûts.
