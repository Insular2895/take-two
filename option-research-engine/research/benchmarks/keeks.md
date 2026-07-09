# REPO-KEEKS — Keeks

Nature : repository candidat pour money management.
Source GitHub repérée : <https://github.com/wdm0006/keeks>. Licence déclarée : MIT.
Langage principal : Python. Maturité : `to_audit`.
Étude ciblée : Kelly, bankroll, drawdown, allocation et sizing.

Statut d'intégration : `candidate_to_verify`.
Priorité : 4/5 — utile pour enrichir `money_management/`, pas pour le pricing options.

## 1. Ce que ce projet fait mieux que nous
Keeks semble pertinent pour formaliser l'allocation : Kelly, bankroll, drawdown et sizing. C'est
un complément naturel aux règles déjà présentes sur perte maximale, fraction de Kelly et
robustesse du sizing sous incertitude.

## 2. Ce qu'il ne fait pas
Keeks n'est pas un moteur d'options. Il ne couvre pas la structure des contrats, les Greeks, la
volatilité implicite/réalisée, la liquidité, l'exécution multi-jambes, l'early exercise, les
dividendes ou l'assignment. Sa logique ne doit donc jamais dimensionner une stratégie sans les
contraintes optionnelles et broker.

## 3. Ce que nous pouvons réutiliser
À étudier pour :

- les formules Kelly et Kelly fractionné ;
- la gestion de bankroll ;
- les limites de drawdown ;
- les plafonds de risque par trade et par scénario ;
- les méthodes de transformation d'un edge estimé en taille de position.

## 4. Ce que nous devons améliorer
Pour notre outil, le sizing doit partir de la perte maximale acceptable, puis être plafonné par
la liquidité, la marge, le risque de gap, le risque d'assignment, l'incertitude du modèle et la
validation humaine. Kelly ne peut être qu'un plafond indicatif, jamais une autorisation de taille.

## 5. Pourquoi notre architecture sera différente
Keeks peut inspirer le module `money_management/`. Notre architecture doit l'encadrer par un
contrat de risque optionnel : aucune allocation ne passe sans stress tests, coût exécutable,
budget de perte, garde-fous broker, journal de décision et mode `human_review_required` pour les
structures asymétriques ou non bornées.
