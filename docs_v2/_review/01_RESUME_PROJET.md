# Résumé du projet

`DOCUMENTATION : ÉTAT DU DÉPÔT, PAS CONSEIL FINANCIER`

## Le produit

Le bot est un atelier de recherche sur les options de Take-Two (`TTWO`). Il prend une thèse, un
budget, des contraintes de risque et une chaîne d’options, puis construit plusieurs structures
réellement listées. Il ne choisit pas d’avance un strike gagnant.

Le résultat attendu n’est pas obligatoirement un trade. `WAIT`, `NO_TRADE` et
`BLOCKED_INSUFFICIENT_DATA` sont des sorties normales.

## Ce qu’il fait

- normalise les contrats et les quotes ;
- construit des structures à risque borné ;
- calcule primes, cash-flows, risque, coûts, Greeks et scénarios ;
- sépare mesure risque-neutre `Q` et probabilité réelle `P` ;
- bloque les modèles non calibrés pour les décisions ;
- compare par hard gates, Pareto puis score explicatif ;
- conserve provenance, configuration, hashes et limites ;
- produit des rapports JSON, Markdown et HTML autonomes ;
- prépare des previews IBKR non transmissibles.

## Ce qu’il ne fait pas

- il ne garantit pas la performance de TTWO ;
- il ne remplace pas une validation des données ou des droits OPRA ;
- il ne transmet pas d’ordre ;
- il ne transforme pas un backtest en vérité future ;
- il ne remplace pas une quote BAG par la somme des jambes sans le signaler ;
- il ne considère pas la marge, les commissions ou les fills inconnus comme nuls.

## État empirique actuel

Le rapport pré-OPRA a conclu :

- `PRE_OPRA_RESEARCH_COMPLETE` pour les travaux offline de cette campagne ;
- `NO_POSITION_RECOMMENDED` ;
- `ENGINE_NOT_PROVEN_SUPERIOR` ;
- holdout final `UNOPENED_UNPROVISIONED` ;
- walk-forward réel trop petit pour le minimum formel ;
- exécution `forbidden`.

Cela signifie que le logiciel est largement testable, mais que sa valeur financière prospective
n’est pas démontrée.

## Les trois systèmes à ne pas confondre

| Système | Rôle | Autorité |
|---|---|---|
| Moteur Python | Recherche, normalisation, modèles, décision et rapports | Aucune autorité d’ordre |
| Cloudflare Worker/D1 | Registre, interface, audit, monitoring et contrôle paper futur | Ne parle pas directement à IBKR |
| Oracle + IB Gateway | Session broker locale et pont sortant | Read-only aujourd’hui ; dispatch désactivé |

## Résultat visé avant le branchement final

Le résultat visé est un système « prêt à observer » : code complet, tests offline verts, commande
explicite de capture, documentation, gates fail-closed et aucun ordre. La validation réelle vient
ensuite et produit une preuve distincte ; elle ne réécrit pas rétroactivement les tests offline.

