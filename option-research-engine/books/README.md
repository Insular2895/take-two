# books/ — Bibliothèque officielle

## Rôle
Recenser les ouvrages sources du moteur. Un livre = une fiche complète dans `fiches/`, créée à
partir de `templates/fiche_livre.md`. Les PDF ne sont jamais commités (droits d'auteur) ; seuls
les Markdown de travail transitent localement pendant le traitement.

## Contenu
- `fiches/` — une fiche par livre (`B-<AUTEUR>-<ANNEE>` → `b_natenberg_1994.md`).
- La bibliothèque initiale ci-dessous est un socle : elle est conçue pour accueillir plusieurs
  centaines de livres sans restructuration (ajout = une fiche, rien d'autre).

## Bibliothèque initiale (socle)
| ID | Titre | Catégorie principale |
|---|---|---|
| B-NATENBERG-1994 | Option Volatility and Pricing | OPTIONS / VOL |
| B-MCMILLAN-2012 | Options as a Strategic Investment | OPTIONS |
| B-HULL-2021 | Options, Futures, and Other Derivatives | OPTIONS / MC |
| B-SINCLAIR-2013 | Volatility Trading | VOL |
| B-SINCLAIR-2020 | Positional Option Trading | OPTIONS / PROBA |
| B-PASSARELLI-2012 | Trading Options Greeks | GREEKS |
| B-TALEB-1997 | Dynamic Hedging | GREEKS / RISK |
| B-VINCE-1992 | The Mathematics of Money Management | MM |
| B-THARP-2006 | Trade Your Way to Financial Freedom | TRADSYS / MM |
| B-DOUGLAS-2000 | Trading in the Zone | PSY |
| B-KAHNEMAN-2011 | Thinking, Fast and Slow | BEHAV / PSY |
| B-MAUBOUSSIN-2021 | Expectations Investing | VALUATION |
| B-GLASSERMAN-2003 | Monte Carlo Methods in Financial Engineering | MC |
| B-ARONSON-2006 | Evidence-Based Technical Analysis | PROBA / Backtesting |
| B-PARDO-2008 | The Evaluation and Optimization of Trading Strategies | TRADSYS / Backtesting |

## Format attendu
Fiche complète : auteur, année, catégorie, objectif, niveau de confiance, importance, modules
concernés, informations recherchées très précisément, **prompt Gemini spécifique au livre**
(jamais générique), format attendu, format de sortie, journal de traitement.

## Dépendances
`prompts/categories/` (base des prompts), `templates/fiche_livre.md`, `docs/01_methodologie_recherche.md`.
