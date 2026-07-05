# B-NATENBERG-1994 — Option Volatility and Pricing

## Auteur
Sheldon Natenberg

## Année
1994 (éd. révisée 2014)

## Catégorie
OPTIONS (principale), VOL, GREEKS

## Objectif
Fournir au moteur les fondations pratiques du pricing, de la volatilité et des Greeks du point de
vue d'un trader : seuils, arbitrages ITM/ATM/OTM, comportement des Greeks selon échéance et strike.

## Niveau de confiance
OPTIONS : 5 — VOL : 5 — GREEKS : 4. Référence absolue des desks d'options depuis 30 ans.

## Pourquoi ce livre est important
C'est le pont entre la théorie du pricing et la décision de trading. Il chiffre le comportement
des Greeks (Delta/Gamma/Theta/Vega) selon moneyness et maturité, exactement ce dont le moteur de
sélection a besoin.

## Modules concernés
sélection, strikes, échéances, simulation, scoring, maintenance, rolling.

## Informations recherchées (très précisément)
- Relations chiffrées Greeks × moneyness × maturité (chap. sur les Greeks et la sensibilité).
- Règles de choix entre options courtes et longues selon le régime de volatilité.
- Comportement de l'IV : structure par strike (skew) et par terme, implications d'achat.
- Spreads : quand une structure à plusieurs jambes domine un Call sec.
- Erreurs de traders débutants explicitement listées par l'auteur.

## Prompt Gemini spécifique
Tu extrais des règles de « Option Volatility and Pricing » (Natenberg). Base : prompt catégorie
OPTIONS + VOL. Spécialisations : (1) Natenberg raisonne en « theoretical edge » — convertis chaque
raisonnement d'edge en condition testable (IV vs volatilité prévue). (2) Dans les chapitres sur
les Greeks, extrais systématiquement les TABLEAUX chiffrés (Delta/Gamma/Theta/Vega par strike et
échéance) sous forme de règles de seuil. (3) Dans les chapitres sur les spreads, produis des
règles de la forme « SI condition de volatilité/skew ALORS structure X domine structure Y ».
(4) Ignore les développements sur les futures et les pits historiques. Sortie : uniquement le
format officiel des règles, avec chapitre et page.

## Format attendu (entrée)
Markdown par chapitre, marqueurs `[p. N]`.

## Format de sortie
Règles au format `rules/FORMAT_REGLE.md` exclusivement. Aucun résumé.

## Journal de traitement
- 2026-07-05 — OCR intégral et recherche ciblée terminés — 53 blocs, 59 candidates avec preuve
  vérifiée, 18 formulations `to_review`; tableaux/formules à contrôler visuellement.
