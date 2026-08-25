# Execution quality score — `pre-opra-v2`

Échelle 0–100, plus haut = exécution estimée de meilleure qualité. Les entrées prévues
sont taux de passage des filtres historiques (20 %), coût/capital (25 %), jambes actives
(15 %), complétude bid/ask (15 %) et exécution live (25 %). Le dernier composant reste
`pending_opra`, soit 75 % de couverture pré-OPRA. La formule est validée mécaniquement,
mais les données historiques ne prouvent pas les fills. Le module reste read-only, sans
création ni transmission d'ordre.
