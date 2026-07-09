# R-VOL-001 — Tester une marge d'erreur de volatilité

## Titre
Refuser un edge qui disparaît sous un faible choc de volatilité.

## Description
Une estimation ponctuelle de volatilité ne doit pas suffire à déclarer une stratégie attractive.
Natenberg illustre qu'une stratégie rentable à `15 %` mais perdante à `16 %` ne possède pas de
marge d'erreur réaliste. Ce point de pourcentage est un exemple du livre, pas un seuil universel.

## Condition
`edge_théorique > 0 ET volatilité_de_bascule_calculable = vrai`

## Variables nécessaires
`volatilité_estimée (%)`, `volatilité_de_bascule (%)`, `P&L par scénario (devise)`, `vega`,
`horizon (jours)`.

## Action
Calculer la distance entre volatilité estimée et volatilité de bascule, stresser plusieurs chocs
d'IV/RV et classer `to_review` toute stratégie dont l'edge ne résiste pas à la marge validée.

## Justification
La volatilité future est difficile à prévoir ; une stratégie robuste doit rester supportable lorsque
l'estimation est légèrement erronée.

## Risques
Une marge fixe peut être inadaptée selon le sous-jacent, l'horizon, le régime ou la convexité.

## Exceptions
Le seuil d'acceptation doit être calibré sur données actuelles ; le cas `15 %` contre `16 %` ne doit
pas être codé comme constante.

## Exemple
Une stratégie profitable à `15 %` mais déficitaire à `16 %` échoue le test illustratif de
robustesse du livre.

## Auteur
Sheldon Natenberg.

## Livre
`B-NATENBERG-1994` — *Option Volatility and Pricing*.

## Chapitre
4 — Volatility.

## Page
PDF p. 91, page imprimée 79.

## Niveau de confiance
3 — auteur crédible et mécanisme clair, mais marge opérationnelle à calibrer.

## Modules concernés
simulation, scoring, robustesse, alertes.

## Références croisées
`→ R-GREEKS-003`, `≠ C-002`.

## Tags
volatilité, stress test, marge d'erreur, robustesse.

## Revue 2026
Statut 2026 : `valide_comme_principe`, `non_active_sans_surface_iv_live_et_scenarios`.

Le principe reste actuel : une stratégie doit garder une marge d'erreur face à une mauvaise
estimation de volatilité. Le seuil ne peut pas venir d'un livre ou d'une constante globale. Il doit
être calibré par sous-jacent, expiration, skew, structure par terme, régime IV/RV, événements,
liquidité et historique récent.

Contrôle obligatoire avant scoring : surface IV par strike/expiry, IV rank/percentile, RV
multi-horizons, calendrier d'événements, stress de volatilité, taux par maturité et statut de
données non stale.

Sources 2026 : IBKR market data/options chain ; historique IV/RV fiable ; U.S. Treasury daily
yield curve ; calendrier earnings/events.

## Historique
- 2026-07-05 — EXTRAITE — Gemini, preuve retrouvée sur la page PDF.
- 2026-07-05 — NORMALISÉE — le point de pourcentage a été conservé comme exemple, pas comme seuil.
- 2026-07-06 — NORMALISÉE — figures 6-18 et 6-19, pages imprimées 114–115 ; effet de la
  volatilité sur la valeur contrôlé visuellement selon la moneyness.
- 2026-07-06 — NORMALISÉE — figures 6-20 et 6-21, pages imprimées 116–117 ; la sensibilité vega
  n'est pas constante hors ATM.
- 2026-07-06 — NORMALISÉE — chapitre 4, pages imprimées 52–79 ; IV, vol historique/forecast,
  annualisation, cohérence des mouvements observés et marge d'erreur contrôlées visuellement.
