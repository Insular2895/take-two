# Revue visuelle — B-PASSARELLI-2012 — Studying Volatility Charts

Source : Dan Passarelli, *Trading Option Greeks*, 2e édition.

Section : Studying Volatility Charts.

Statut : `in_progress`

Date de revue : 2026-07-06.

Les images du livre ne sont pas versionnées. Cette fiche conserve les configurations IV/RV
contrôlées visuellement et leur usage pour le futur moteur de recherche options.

## Introduction du chapitre 14 — page imprimée 264

Passarelli présente les volatility charts comme un outil pour comparer :

- l'IV courante à son historique ;
- la RV courante à son historique ;
- les divergences et convergences entre IV et RV.

La ligne de RV répond à trois questions :

- les 30 derniers jours ont-ils été plus ou moins volatils que d'habitude ?
- quelle est la plage typique de RV du sous-jacent ?
- combien de volatilité le sous-jacent a-t-il historiquement connu autour d'événements récurrents ?

### Impact projet

Le moteur doit stocker les courbes IV et RV comme séries temporelles, pas seulement comme un snapshot
du jour. La décision doit comparer le niveau courant à son régime historique et aux événements.

## Figure 14.1 — pages imprimées 265–266

Titre : `Realized Volatility Rises, Implied Volatility Rises`.

### Configuration

RV et IV montent ensemble. Passarelli indique trois variantes possibles :

- IV monte plus vite que RV ;
- RV monte plus vite que IV ;
- les deux montent à peu près au même rythme.

### Interprétation

- Pattern souvent associé à des actifs très actifs en news.
- Si IV dépasse nettement RV, le marché price une volatilité future plus haute.
- Le gamma peut être utile si la RV converge vers l'IV, mais l'option devient chère en theta.
- Sans news attendue, l'excès d'IV peut devenir une opportunité short vol.
- Le texte souligne que ce type de situation est difficile : le trader peut avoir raison ou se faire
  broyer.

### Impact projet

Ne pas scorer automatiquement une hausse simultanée IV/RV comme achat de volatilité. Il faut
séparer :

- news/catalyseur attendu ;
- vitesse relative de l'IV et de la RV ;
- coût theta ;
- niveau historique de l'IV ;
- capacité du gamma scalping à couvrir le theta.

## Figure 14.2 — page imprimée 267

Titre : `Volatility Mesas`.

### Configuration

La RV peut former une `mesa` après un gros mouvement d'un jour :

- un jour de forte variation entre dans la fenêtre de calcul ;
- la RV 30 jours saute puis reste élevée pendant environ 30 jours ;
- lorsque ce jour sort de la fenêtre, la RV peut chuter brusquement.

### Interprétation

Une mesa de RV ne signifie pas nécessairement que toute la période de 30 jours a été volatile. Elle
peut être l'effet mécanique d'un seul gros mouvement qui reste dans la fenêtre.

### Impact projet

Le moteur doit distinguer :

- RV élevée par dispersion récurrente ;
- RV élevée par un seul outlier ;
- date de sortie de l'outlier de la fenêtre RV.

Sinon, il risque de surévaluer la volatilité réalisée durable.

## Figure 14.3 — pages imprimées 267–269

Titre : `Realized Volatility Rises, Implied Volatility Remains Constant`.

### Configuration

- IV reste élevée ou stable.
- RV monte tardivement.

### Interprétation

Le texte donne deux lectures :

- le marché options avait déjà anticipé un événement, ce qui explique une IV élevée avant la hausse
  de RV ;
- ou l'IV est trop haute et l'achat d'options trop précoce peut subir beaucoup de theta avant que la
  RV monte.

Passarelli note qu'acheter des options plusieurs mois trop tôt peut être douloureux, même si le
mouvement finit par arriver. Il note aussi qu'un vendeur de volatilité juste avant le gros mouvement
peut subir une forte perte.

### Impact projet

Le moteur doit mesurer le coût d'attente :

- theta jusqu'au catalyseur ;
- durée estimée avant réalisation ;
- risque de vendre vol trop proche du mouvement ;
- risque d'acheter vol trop tôt.

## Figure 14.4 — pages imprimées 269–270

Titre : `Realized Volatility Rises, Implied Volatility Falls`.

### Configuration

La RV monte pendant que l'IV baisse. Passarelli décrit deux exemples dans la même figure.

### Interprétation

Ce pattern peut indiquer une inefficience :

- RV commence à devenir plus chère que l'IV ;
- si IV est aussi basse historiquement, l'achat de volatilité peut devenir intéressant ;
- le gamma/theta ratio peut être favorable au gamma scalper.

Dans l'exemple de droite, Passarelli décrit un IV crush post-earnings :

- IV baisse fortement ;
- RV monte fortement en une journée ;
- le long volatility trader peut perdre sur vega mais compenser ou dépasser cette perte par gamma.

### Impact projet

Le moteur doit séparer deux cas :

- divergence exploitable sans événement ;
- IV crush post-event où vega et gamma agissent en sens opposés.

Il doit donc simuler simultanément :

- perte/gain vega ;
- gain/perte gamma ;
- theta ;
- timing de l'événement.

## Figure 14.5 — pages imprimées 270–271

Titre : `Realized Volatility Remains Constant, Implied Volatility Rises`.

### Configuration

- RV reste stable.
- IV monte.
- L'exemple montre une RV oscillant entre environ `20 %` et `24 %`, tandis que l'IV passe d'environ
  `24 %` à plus de `30 %`.

### Interprétation

Si aucune news ne justifie la hausse d'IV, le pattern peut signaler une opportunité de vente de
volatilité :

- objectif : profiter du theta ou d'une baisse de vega ;
- contrainte : ne pas perdre trop sur negative gamma ;
- hypothèse : IV doit finir par retomber et converger vers RV.

### Impact projet

Le moteur doit exiger une recherche de cause avant de vendre la volatilité :

- événement prévu ?
- news non encore intégrée ?
- changement de régime ?
- distorsion temporaire de demande options ?

Sans cause identifiable, le signal short vol devient plus plausible, mais reste à stresser contre
gap et hausse persistante d'IV.

## Figure 14.6 — page imprimée 272

Titre : `Realized Volatility Remains Constant, Implied Volatility Remains Constant`.

### Configuration

- IV et RV restent globalement dans une zone proche pendant plusieurs mois.
- L'exemple décrit une IV entre environ `15 %` et `20 %` de fin janvier à fin juillet.
- La RV reste dans les low teens.

### Interprétation Passarelli

- Environnement favorable aux vendeurs d'options lorsque l'IV reste au-dessus de la RV.
- Du point de vue gamma/theta, les odds favorisent les short-volatility traders.
- Les stratégies citées incluent vente de calls delta-neutre avec stock, time spreads et iron
  condors.

### Limites

- Le pattern n'est pas une garantie.
- Une stratégie delta-neutre peut échouer si le trader couvre mal ses deltas.
- Les time spreads et iron condors peuvent échouer si la volatilité monte ou si le sous-jacent trend
  dans une direction.
- Il faut regarder le graphique du prix du sous-jacent avec le graphique de volatilité.

## Figure 14.7 — page imprimée 273

Titre : `Realized Volatility Remains Constant, Implied Volatility Falls`.

### Configuration

- La RV reste globalement stable.
- L'IV tombe pour converger vers la RV.
- Passarelli décrit deux convergences classiques.

### Interprétation

- Les divergences importantes IV/RV peuvent se réduire par arbitrage.
- Si l'IV est très au-dessus de la RV, les acteurs rationnels peuvent vendre des options pour
  capturer l'edge gamma/theta.
- Cette vente fait baisser les prix d'options et donc l'IV.

### Impact projet

Le moteur peut détecter une compression possible de l'IV quand :

- IV très supérieure à RV ;
- absence de catalyseur évident ;
- liquidité suffisante ;
- prix du sous-jacent non directionnel.

Mais il doit refuser un signal automatique sans vérifier événement, tendance du sous-jacent et
risque de gap.

## Figure 14.8 — page imprimée 274

Titre : `Realized Volatility Falls, Implied Volatility Rises`.

### Configuration

- RV baisse.
- IV monte.
- Passarelli l'associe aux anticipations d'événements, notamment earnings ou décisions FDA.

### Interprétation

- L'incertitude future peut faire monter l'IV même si le prix réalisé devient calme.
- Le pattern peut précéder un événement directionnel important.
- Après l'événement, l'IV peut être écrasée et les vega/gamma peuvent se retourner contre le trader.

### Impact projet

Le moteur doit traiter ce pattern comme `event-risk`, pas comme simple anomalie IV/RV :

- détecter earnings/FDA/news ;
- mesurer échéance avant événement ;
- éviter d'interpréter RV basse comme sécurité ;
- stresser IV crush et gap directionnel.

## Figure 14.9 — pages imprimées 275–276

Titre : `Realized Volatility Falls, Implied Volatility Remains Constant`.

### Configuration

- RV baisse fortement.
- IV reste proche de son niveau précédent.
- Crossover visible autour du milieu de février dans l'exemple.

### Interprétation

- Une baisse de RV n'indique pas nécessairement un événement de volatilité.
- Elle peut refléter une période plus lente ou une contraction naturelle après une période active.
- Ce qui compte est la réaction du marché options à cette baisse.
- Si l'IV ne baisse pas alors que la RV tombe, les options peuvent devenir chères relativement au
  mouvement réalisé.

### Passage important

Passarelli indique que lorsque l'IV monte ou baisse, le trader doit chercher la cause. Le marché
options réagit à la volatilité du sous-jacent, pas l'inverse.

### Gamma scalping et seuils

Dans l'exemple, utiliser un écart-type quotidien dérivé de l'IV pour entrer des hedges aurait pu :

- couvrir trop tôt en janvier, quand la RV était supérieure à l'IV ;
- couvrir trop tard fin février, quand la RV était tombée sous l'IV.

Il suggère d'adapter les intervalles de hedge quand la volatilité réalisée change.

### Impact projet

Le futur moteur doit permettre des seuils de hedge dynamiques :

- seuil fondé sur IV ;
- seuil fondé sur RV récente ;
- seuil hybride ;
- contraction/extension du seuil selon le régime de volatilité.

## Figure 14.10 — pages imprimées 277–278

Titre : `Realized Volatility Falls, Implied Volatility Falls`.

### Configuration

- RV et IV baissent ensemble après une période de forte volatilité.
- Le texte associe ce pattern à la résolution d'une incertitude : procès, management, rumeur,
  spin-off, merger ou autre événement corporate.

### Interprétation

- Lorsque la cause de l'incertitude disparaît, RV et IV peuvent revenir vers une moyenne plus basse.
- Le problème est de savoir ce qu'est la volatilité normale après un changement fondamental.
- Si l'historique récent est peu représentatif, comparer avec d'autres sociétés du même secteur peut
  aider.

### Conclusion de section

Passarelli conclut que les vol charts sont des représentations graphiques de l'interaction entre RV
et IV. Les divergences et convergences aident le trader à comprendre si les options paraissent
chères ou bon marché, surtout en les comparant à l'historique courant et passé.

## Conclusions provisoires pour Take Two

1. IV et RV doivent être stockées comme deux séries distinctes.
2. L'écart IV/RV ne suffit pas : il faut interpréter le régime, le sous-jacent et les catalyseurs.
3. IV haute vs RV basse peut favoriser short vol, mais seulement si le risque événementiel et
   directionnel est maîtrisé.
4. RV basse avec IV montante signale souvent event-risk, pas nécessairement une opportunité simple.
5. Les seuils de gamma scalping doivent pouvoir s'adapter à la volatilité réalisée récente.
6. Les comparables sectoriels peuvent aider quand l'historique du titre est perturbé par un
   événement corporate.
7. Le moteur IBKR devra intégrer calendrier d'événements, historique IV/RV et chart du prix avant
   de scorer une stratégie volatilité.
