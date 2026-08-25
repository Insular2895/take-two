# Contrat de configuration pré-OPRA v1

Le fichier `configs/pre_opra/v1/ttwo_research.yaml` regroupe les onze domaines de
configuration exigés pour une recherche reproductible. Le contrat Pydantic strict
correspondant est `take_two_options.config.contracts.PreOpraConfig`; son schéma JSON
est exporté dans `schemas/pre_opra_config.schema.json`.

Les valeurs financières ne sont pas des défauts universels. Chaque seuil ou coût
susceptible d'influencer le résultat est un `GovernedValue` comportant :

- la valeur brute ;
- son origine ;
- son statut (`sourced`, `calibrated`, `calibration_required` ou
  `draft_to_validate`) ;
- ses sources et sa justification.

Une valeur marquée `sourced` sans identifiant de source est refusée. Les probabilités
de scénario doivent être toutes absentes ou toutes présentes et sommer à un. Les
contraintes de capital, de devise et de cutoff sont vérifiées entre sections.

Les strikes et échéances restent issus de la chaîne réellement fournie. Les recettes
décrivent des relations entre jambes, jamais un symbole OCC, un strike ou une date
TTWO. Le fixture synthétique `XYZ` démontre que le noyau de génération, payoff,
risque, Pareto, validation numérique et reporting fonctionne sans branche TTWO.

Le contrat impose `preview_only=true` et `order_capability=forbidden`. Il ne connecte
aucun flux OPRA et ne crée aucun ordre.
