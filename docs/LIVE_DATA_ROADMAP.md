# Roadmap données live

Cette roadmap ne constitue pas une autorisation d’activation. Aucune connexion live
n’est activée par défaut.

1. Paramétrer le socket local TWS/IB Gateway (`host`, `port`, `clientId`) sans clé API,
   puis valider compte, entitlements, licences, coûts et droits de redistribution.
2. Connecter un port read-only injecté : découverte contrats, spot, chaîne, timestamps,
   bid/ask, volume, open interest et Greeks.
3. Tester fraîcheur, trous, reconnexion, rate limits, cache, cutoff et fail-closed.
4. Nettoyer la surface, exclure les quotes invalides, contrôler l’arbitrage et journaliser
   les calibrations.
5. Récupérer les quotes combo et comparer la quote BAG au synthétique jambe par jambe.
6. Ajouter commissions et marge what-if à un preview expirant et non transmissible.
7. Passer par une campagne paper avant toute revue commerciale.

Point d'arrêt au 16 septembre 2026 : les phases 2 et 4 existent désormais côté code et sont
testées hors ligne. Le provider qualifie le sous-jacent et les options, borne la chaîne, collecte
les champs de marché, applique cache/retry/pacing, construit une quote BAG read-only et convertit
le résultat vers le snapshot canonique. Une commande explicite de capture est disponible.

Cette implémentation n'a pas été connectée pendant ce checkpoint. La preuve réelle du 25 août
reste limitée au handshake IBKR Paper sur Oracle, au compte `DU` et à un snapshot de télémétrie
sans position TTWO. Elle ne valide pas le nouveau chemin chaîne/Greeks/OI/BAG. Entitlement et
licence restent des gates humains non confirmés ; la surface, le what-if et la campagne paper
restent à réaliser.

Les fallbacks synthétiques sont interdits pour un résultat promu. Les détails
spécifiques au broker sont dans [IBKR_OPRA_ROADMAP.md](IBKR_OPRA_ROADMAP.md).
