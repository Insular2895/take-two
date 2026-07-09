# Revue visuelle — B-MCMILLAN-2012 — Chapitre 10

Source : Lawrence G. McMillan, *Options as a Strategic Investment*, 5e édition.

Chapitre : 10 — The Butterfly Spread.

Statut : `in_progress`

Date de revue : 2026-07-06.

Périmètre reçu : chapitre complet, pages imprimées `200–209`.

## Construction et payoff — pages 200–202, tableaux 10-1 et 10-2, figure 10-1

Butterfly call standard :

- acheter `1` call au strike bas ;
- vendre `2` calls au strike médian ;
- acheter `1` call au strike haut ;
- même échéance et espacements identiques.

Formules :

- investissement net = débit net ;
- profit maximal = distance entre strikes − débit net ;
- break-even bas = strike bas + débit net ;
- break-even haut = strike haut − débit net.

Exemple `50/60/70` :

- débit `3` ;
- perte maximale `3` ;
- profit maximal `7` au strike médian `60` ;
- break-even `53` et `67`.

La structure est limitée en risque et en profit. Son maximum est obtenu précisément au strike des
deux calls vendus.

## Sélection du spread — pages 203–205

McMillan cherche :

- un débit aussi faible que possible ;
- un sous-jacent proche du strike médian à l'expiration ;
- un compromis entre neutralité et opinion directionnelle.

Il observe que les butterflies sont plus praticables sur :

- sous-jacents plus chers ou plus volatils ;
- chaînes dont les strikes sont suffisamment espacés ;
- marchés où le débit reste raisonnable après bid-ask et commissions.

Les commissions sur quatre jambes et l'exécution aux vrais bid/ask peuvent détruire le rendement
théorique.

## Butterfly asymétrique — pages 205–206

Un espacement asymétrique modifie le biais :

- davantage de bull spread que de bear spread crée un biais haussier ;
- davantage de bear spread crée un biais baissier.

Cette construction peut réduire le débit, voire produire un crédit, mais n'est plus neutre et peut
augmenter les exigences de marge lorsque les écarts entre strikes diffèrent.

## Follow-Up Action — pages 206–209, tableaux 10-3 et 10-4

Le butterfly est déjà borné, mais McMillan envisage une clôture anticipée :

- près du strike médian, pour protéger un profit non réalisé ;
- si l'exercice anticipé du call short devient probable ;
- lorsque les commissions restent proportionnées au profit disponible.

Il rappelle de ne pas sortir jambe par jambe au hasard. Une adaptation structurée est néanmoins
possible lorsqu'un mouvement important a presque maximisé l'un des deux spreads internes :

- après une forte baisse, fermer le bear spread profitable et conserver le bull spread ;
- après une forte hausse, fermer le bull spread profitable et conserver le bear spread.

Cette transformation augmente légèrement le risque, mais peut permettre de profiter d'un retour du
sous-jacent vers la zone centrale. Elle doit être évaluée comme une nouvelle position, avec son
nouveau coût et son nouveau payoff.

## Impact projet

Le moteur doit :

- reconstruire le butterfly comme bull spread + bear spread ;
- contrôler l'espacement réel des strikes ;
- intégrer bid-ask, quatre jambes, commissions et marge ;
- calculer le payoff après toute clôture partielle ;
- ne jamais qualifier automatiquement une structure asymétrique de neutre ;
- refuser un butterfly dont l'edge théorique disparaît après coûts d'exécution.
