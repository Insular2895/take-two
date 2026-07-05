# Registre des conflits et transpositions

Date : 2026-07-05

Tous les éléments sont `conflict_open` ou `to_review`.

## C-001 — Delta comme probabilité

- Source : Natenberg et Passarelli utilisent le delta comme approximation pratique de probabilité
  dans certains contextes.
- Risque : transformer une approximation dépendante du modèle en probabilité calibrée.
- Traitement : conserver delta comme sensibilité ; si une probabilité est affichée, la calculer et
  la calibrer séparément.
- Statut : `to_review`.

## C-002 — IV supérieure à RV donc vente de volatilité

- Source : Passarelli discute les cas où IV et volatilité réalisée divergent.
- Risque : ignorer événements, prime de risque de volatilité, skew, gaps, coûts et risque de ruine.
- Traitement : en faire une hypothèse à tester, jamais une règle d'entrée autonome.
- Statut : `conflict_open`.

## C-003 — Delta-neutral présenté comme direction-neutral

- Source : les manuels définissent la neutralité instantanée par un delta net nul.
- Risque : gamma, vega, charm, gaps et rebalancement recréent immédiatement une exposition.
- Traitement : afficher horizon et scénarios de choc ; interdire le libellé « sans risque
  directionnel ».
- Statut : `to_review`.

## C-004 — Edge théorique contre coûts réels

- Source : Natenberg mesure un avantage théorique ; Grinold et Kahn traitent contraintes, turnover
  et coûts.
- Risque : un edge brut positif peut devenir négatif après bid-ask, commissions, impact et hedge.
- Traitement : exiger un edge net robuste dans plusieurs scénarios de coûts.
- Statut : `conflict_open`.

## C-005 — Structure complexe contre exécutabilité

- Source : McMillan décrit les avantages de spreads ; Natenberg souligne la difficulté des spreads
  à plusieurs côtés.
- Risque : optimiser le payoff théorique en dégradant fortement l'exécution.
- Traitement : comparer toute structure à une alternative plus simple avec cotations exécutables.
- Statut : `conflict_open`.

## C-006 — Deux définitions du risque

- Source : Grinold et Kahn utilisent volatilité/tracking error ; Klarman insiste sur la perte
  permanente et la marge de sécurité.
- Risque : confondre dispersion statistique et risque économique.
- Traitement : conserver deux familles de métriques : risque de marché/portefeuille et risque
  fondamental de perte permanente.
- Statut : `to_review`.

## C-007 — Psychologie transformée en automatisation

- Source : Douglas et les notes Duke portent sur le processus de décision.
- Risque : Gemini transforme des principes subjectifs en blocages arbitraires ou délais inventés.
- Traitement : limiter ces sources aux checklists et au journal jusqu'à définition mesurable.
- Statut : `to_review`.

## C-008 — Règles historiques devenues obsolètes

- Source : éditions anciennes de McMillan, Natenberg et autres.
- Risque : seuils d'exercice automatique, règles de marge, microstructure et produits modifiés.
- Traitement : vérifier chaque règle opérationnelle dans la documentation actuelle OCC/IBKR et dans
  le cadre réglementaire applicable avant codage.
- Statut : `conflict_open`.

## C-009 — Convention de signe des Greeks

- Source : la figure 6-24 de Natenberg affiche un theta négatif pour des options longues, alors que
  la figure 6-25 affiche des valeurs positives présentées comme taux de décroissance. La figure
  6-25 affiche aussi les deltas des puts comme des magnitudes positives, contrairement à la figure
  6-24.
- Risque : inverser le sens économique d'une exposition lors de l'import de données ou de la
  comparaison avec IBKR.
- Traitement : stocker explicitement convention, unité, horizon et fournisseur ; normaliser vers une
  convention interne unique avec tests.
- Résolution documentaire : la figure 6-26 établit les signes économiques des positions longues et
  courtes ; la figure 6-25 doit être interprétée comme présentation de magnitudes/taux.
- Statut : `resolved_documentary`; convention IBKR encore à vérifier.
