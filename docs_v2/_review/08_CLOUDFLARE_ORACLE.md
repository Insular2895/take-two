# Cloudflare, Oracle et séparation des responsabilités

## Pourquoi deux environnements ?

Cloudflare fournit l’interface, l’authentification, D1 et les routes signées. IB Gateway exige une
session locale persistante ; elle vit donc sur Oracle A1. Le navigateur ne reçoit jamais un accès
direct au socket broker.

## Oracle A1

État documenté :

- Ubuntu ARM64 ;
- SSH limité, UFW et fail2ban ;
- VNC uniquement via tunnel SSH ;
- IB Gateway Paper sur loopback ;
- API officielle installée dans un virtualenv dédié ;
- publisher systemd read-only disponible.

Limites : la disponibilité Always Free n’est pas une garantie SRE et IB Gateway peut demander une
réauthentification périodique.

## Cloudflare Worker/D1

Le Worker :

- exige une identité Cloudflare Access ;
- vérifie les signatures HMAC, timestamp et nonce ;
- sépare credentials de télémétrie et bridge paper ;
- conserve une projection latest-only et un audit ;
- n’importe aucun SDK broker ;
- ne peut pas envoyer directement un ordre IBKR.

## Télémétrie

La télémétrie actuelle lit les positions TTWO déjà présentes, leur quote et le P&L broker. Elle
retire l’identifiant du compte. Un P&L manquant rend le total inconnu au lieu de produire un faux
zéro.

Le chemin local est testé. La preuve end-to-end encore attendue est :

```text
position TTWO paper réelle
 -> callback IBKR
 -> payload redacted
 -> signature dédiée
 -> Access
 -> Worker
 -> D1
 -> dashboard
```

Le premier snapshot réel documenté contenait zéro position TTWO et n’a pas été publié à
Cloudflare ; il ne prouve donc pas ce trajet complet.

Un vecteur HMAC partagé est désormais rejoué par le client Python et le vérificateur TypeScript.
Il prouve que le corps exact, le SHA-256, la chaîne canonique et la signature sont compatibles
entre les deux langages. Il ne prouve ni Cloudflare Access réel, ni le réseau Oracle, ni D1 distant,
ni l'affichage dashboard : ces preuves restent dans la liste end-to-end ci-dessus.

## Bridge paper

Les contrats, journal SQLite WAL, outbox, claim, heartbeat, HMAC, idempotence et kill switch sont
codés. Le runtime instancie toujours `DisabledGateway`. Les tests avec `FakeGateway` prouvent le
workflow du journal, pas un ordre IBKR.
